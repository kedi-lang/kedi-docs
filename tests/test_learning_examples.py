"""Verify the learning path in isolated projects without provider requests."""

import asyncio
import json
import sys
import unittest
from importlib.metadata import metadata
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner
from packaging.requirements import Requirement
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from kedi.agent_adapter import PydanticAdapter
from kedi.cli import main
from kedi.lang import compile_program, parse_program

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kedi_examples import _kedi_fences  # noqa: E402


def snippets(page):
    return [f.source for f in _kedi_fences(ROOT / "docs/getting-started" / page)]


class LearningExamplesTests(unittest.TestCase):
    def execute_model_program(self, source, payload, args):
        calls = []

        def respond(messages, info):
            calls.append(messages)
            return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, payload)])

        source = "\n".join(line for line in source.splitlines() if not line.startswith("> model:"))
        runtime = compile_program(
            parse_program(source),
            adapter=PydanticAdapter(FunctionModel(respond)),
            runtime_globals={"args": SimpleNamespace(**args)},
        )
        try:
            value = runtime.run_main()
        finally:
            asyncio.run(runtime.aclose())
        self.assertEqual(len(calls), 1)
        return value

    def test_installation_cli_smoke_and_intentional_parse_error(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            for args in (["--help"], ["-p", "-c", "= ready"], ["-c", "= ready"]):
                result = runner.invoke(main, args)
                self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(result.output.strip(), "ready")
            self.assertNotEqual(runner.invoke(main, ["-p", "-c", "@broken("]).exit_code, 0)

    def test_first_deterministic_program(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("label.kedi").write_text(snippets("first-program.md")[0])
            result = runner.invoke(main, ["label.kedi", "--title", "  Release   Notes  "])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(result.output.strip(), "release-notes")

    def test_review_keeps_native_object_until_json_boundary(self):
        payload = {"decision": "revise", "summary": "Check traversal tests."}
        result = self.execute_model_program(
            snippets("first-program.md")[1],
            {"review": payload},
            {"title": "Reject unsafe paths", "diff_summary": "Adds containment checks"},
        )
        self.assertEqual(json.loads(result), payload)

    def test_review_branch_uses_one_model_call_for_either_outcome(self):
        examples = snippets("first-program.md")
        branch = next(source for source in examples if "[next_step:" in source)
        source = examples[1].replace(
            "= `review_change(args.title, args.diff_summary).model_dump_json()`",
            branch,
        )
        for decision, expected in [
            ("approve", "Queue for human review"),
            ("revise", "Request another revision"),
        ]:
            with self.subTest(decision=decision):
                result = self.execute_model_program(
                    source,
                    {"review": {"decision": decision, "summary": "Check tests."}},
                    {"title": "Parser", "diff_summary": "New parser checks"},
                )
                self.assertEqual(result, f"{expected}: Check tests.")

    def test_overview_brief_program(self):
        result = self.execute_model_program(
            snippets("index.md")[0],
            {"summary": "Locks coordinate work."},
            {"topic": "distributed locks"},
        )
        self.assertEqual(result, "Locks coordinate work.")

    def test_two_file_project_resolves_from_parent_directory(self):
        examples = snippets("projects-and-execution.md")
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("project").mkdir()
            Path("project/labels.kedi").write_text(examples[0])
            Path("project/main.kedi").write_text(examples[1])
            result = runner.invoke(main, ["project/main.kedi", "--title", "Release Notes"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(result.output.strip(), "release-notes")

    def test_provider_extra_matches_installed_sdk_contract(self):
        package = metadata("pydantic-ai-slim")
        self.assertIn("openai", package.get_all("Provides-Extra"))
        requirements = [Requirement(value) for value in package.get_all("Requires-Dist")]
        self.assertTrue(
            any(
                requirement.name == "openai"
                and requirement.marker is not None
                and requirement.marker.evaluate({"extra": "openai"})
                for requirement in requirements
            )
        )
