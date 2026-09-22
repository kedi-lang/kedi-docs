"""Execute published examples and guard P3-P7 documentation contracts offline."""

import ast
import asyncio
import contextlib
import inspect
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import kedi
from kedi.errors import KediExecutionError
from kedi.lang import compile_program, parse_program
from kedi.package_registry import install_package

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kedi_examples import _kedi_fences  # noqa: E402

KEDI_SOURCE = ROOT / ".kedi-source" if (ROOT / ".kedi-source").is_dir() else ROOT.parent
sys.path.insert(0, str(KEDI_SOURCE / "tests"))
from mock_adapter import MockAdapter  # noqa: E402


class WorkflowAdapter(MockAdapter):
    shortname = "pydantic"

    def __init__(self, supported):
        super().__init__()
        self.supported = supported

    def produce_sync(self, **kwargs):
        result = super().produce_sync(**kwargs)
        if "supported" in result:
            result["supported"] = self.supported
        return result


def snippets(page):
    return [f.source for f in _kedi_fences(ROOT / "docs" / page)]


def run(source, **kwargs):
    runtime = compile_program(parse_program(source), **kwargs)
    try:
        return runtime.run_main()
    finally:
        asyncio.run(runtime.aclose())


class ManualContractTests(unittest.TestCase):
    def tearDown(self):
        kedi.reset_config()
        kedi.clear_cache()

    def test_scope_examples_execute(self):
        examples = snippets("core-language/scopes-and-bindings.md")
        self.assertEqual(run(examples[0]), ("pending", 1))
        self.assertIs(run(examples[1]), True)
        with self.assertRaises(KediExecutionError) as caught:
            run(examples[0].replace("= `(status, visits)`", "= `scratch`"))
        self.assertIn("scratch", str(caught.exception))

    def test_last_return_and_defaults(self):
        examples = snippets("core-language/parameters-and-returns.md")
        last = next(s for s in examples if "@last_value" in s)
        default = next(s for s in examples if "@format_count" in s)
        self.assertEqual(run(last), 2)
        self.assertEqual(run(default), "3 items")

    def test_nested_loop_map(self):
        source = next(s for s in snippets("core-language/loops-and-map.md") if "[squares:" in s)
        self.assertEqual(run(source), [[1, 4], [9, 16]])

    def test_constraints_preserved(self):
        source = next(s for s in snippets("core-language/types.md") if "Rating = Annotated" in s)
        self.assertEqual(run(source), 1.5)
        with self.assertRaises(KediExecutionError) as caught:
            run(source.replace("`1.5`", "`3.0`"))
        self.assertIn("does not match annotated type", str(caught.exception))

    def test_python_block_example_is_not_a_prelude(self):
        source = next(
            s
            for s in snippets("python-interop/prelude-globals-and-scope.md")
            if 'temporary = "not persistent"' in s
        )
        self.assertIsNone(run(source))
        with self.assertRaises(KediExecutionError) as caught:
            run(source + "\n= `temporary`\n")
        self.assertIn("temporary", str(caught.exception))

    def test_python_snippets_and_query_docstrings_parse(self):
        pages = list((ROOT / "docs/python-api").glob("*.md"))
        for page in pages:
            for index, source in enumerate(
                re.findall(r"```python\n(.*?)\n```", page.read_text(), re.S)
            ):
                with self.subTest(page=page.name, snippet=index):
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            continue
                        doc = ast.get_docstring(node)
                        if doc and doc.startswith("kedi\n"):
                            # Parsing cleans indentation, so check the displayed source too.
                            expression = node.body[0]
                            lines = source.splitlines()
                            for line in lines[expression.lineno : expression.end_lineno - 1]:
                                if line.strip():
                                    self.assertGreaterEqual(
                                        len(line) - len(line.lstrip()),
                                        expression.col_offset,
                                        f"Misaligned query docstring in {page.name}: {line!r}",
                                    )
                            body = doc.split("\n", 1)[1]
                            wrapped = "@example():\n" + "\n".join(
                                "    " + line for line in body.splitlines()
                            )
                            parse_program(wrapped)

    def test_embedding_example_runs_and_closes(self):
        page = (ROOT / "docs/python-api/embedding.md").read_text()
        source = re.findall(r"```python\n(.*?)\n```", page, re.S)[0]
        namespace = {}
        exec(compile(source, "embedding.md", "exec"), namespace)

    def test_jev_workflow_routes_both_outcomes(self):
        source = snippets("agent-adapters/jev-workflow.md")[0]
        for supported in (True, False):
            with self.subTest(supported=supported):
                adapter = WorkflowAdapter(supported)
                result = run(source, adapter=adapter)
                expected = (
                    "Draft for human review: reply-value"
                    if supported
                    else "Manual review required; do not send the draft."
                )
                self.assertEqual(result, expected)
                self.assertEqual(
                    adapter.model_calls,
                    [
                        "openai:gpt-5.6-luna",
                        "typesafe/jev-latest",
                    ],
                )
                self.assertEqual(adapter.settings_calls[1]["typesafe_threshold"], 0.9)
                self.assertIn("reply-value", adapter.request_calls[1])
                self.assertEqual(len(adapter.request_calls), 2)

    def test_default_executor_example(self):
        page = (ROOT / "docs/python-api/executors.md").read_text()
        source = re.findall(r"```python\n(.*?)\n```", page, re.S)[1]
        exec(compile(source, "executors.md", "exec"), {})

    def test_public_export_inventory_is_exact(self):
        page = (ROOT / "docs/python-api/public-exports.md").read_text()
        documented = set()
        for line in page.splitlines():
            if line.startswith("| `"):
                documented.update(re.findall(r"`([^`]+)`", line.split("|")[1]))
        self.assertEqual(documented, set(kedi.__all__))

    def test_configuration_parameter_inventory(self):
        common = {
            "model",
            "adapter",
            "agent",
            "system",
            "effort",
            "settings",
            "tools",
            "env",
            "mcp_servers",
            "approval",
            "hooks",
            "skills",
            "artifacts",
            "conversation",
        }
        execution = {"parallel", "max_workers", "loop_iteration_limit", "adapter_kwargs"}
        additions = {
            "configure": execution,
            "context": execution,
            "query": {"fn", "cache", "requires"},
            "bind": {"file", "cache", "reload", "requires"},
            "interactive": execution
            | {
                "executor",
                "engine",
                "cwd",
                "subagent_max_depth",
                "subagent_max_concurrency",
                "subagent_timeout_seconds",
                "subagent_usage_limits",
                "subagent_state_path",
            },
        }
        reference = (ROOT / "docs/python-api/public-parameters.md").read_text()
        for name, extra in additions.items():
            with self.subTest(name=name):
                self.assertEqual(
                    set(inspect.signature(getattr(kedi, name)).parameters), common | extra
                )
                for parameter in common | extra:
                    self.assertIn(parameter, reference)

    def test_local_package_tutorial(self):
        examples = snippets("modules-and-packaging/local-package.md")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "release_labels"
            source = package / "src/release_labels"
            source.mkdir(parents=True)
            (package / "package.kedi").write_text(examples[0])
            (source / "formatting.kedi").write_text(examples[1])
            (source / "main.kedi").write_text(examples[2])
            with patch.dict(os.environ, {"KEDI_HOME": str(root / "home")}):
                install_package(package / "package.kedi")
                consumer = root / "consumer.kedi"
                runtime = compile_program(parse_program(examples[3], source_path=str(consumer)))
                try:
                    self.assertEqual(runtime.run_main(), "Kedi v0.4.0")
                finally:
                    asyncio.run(runtime.aclose())
                self.assertTrue(
                    (root / "home/registry/release_labels/.kedi-install.json").is_file()
                )

    def test_filesystem_bounded_read_example(self):
        source = next(s for s in snippets("modules-and-packaging/filesystem.md") if "[head]" in s)
        with tempfile.TemporaryDirectory() as temporary, contextlib.chdir(temporary):
            Path("application.log").write_text("a" * 2000 + "b" * 2000 + "not in the two pages")
            with patch.dict(os.environ, {"KEDI_WORKSPACE_POLICY": "strict"}):
                self.assertEqual(run(source), "a" * 2000 + "\n" + "b" * 2000)


if __name__ == "__main__":
    unittest.main()
