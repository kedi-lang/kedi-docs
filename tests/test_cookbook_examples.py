"""Run cookbook listings through real runtime boundaries with local model fixtures."""

import asyncio
import contextlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai.messages import ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel

from kedi.agent_adapter import PydanticAdapter
from kedi.errors import KediExecutionError
from kedi.lang import compile_program, parse_program
from kedi.package_registry import install_package
from kedi.tests_runner import run_evals, run_tests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kedi_examples import _kedi_fences  # noqa: E402


def snippets(name):
    return [f.source for f in _kedi_fences(ROOT / "docs/examples" / name)]


def local_source(name):
    # Substitute the provider, not the program's tools, profiles, or output schemas.
    return "\n".join(
        line for line in snippets(name)[0].splitlines() if not line.lstrip().startswith("> model:")
    )


def returned(messages, name):
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in reversed(message.parts):
                if isinstance(part, ToolReturnPart) and part.tool_name == name:
                    return part.content
    return None


def output(info, values):
    return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, values)])


def execute(source, **kwargs):
    runtime = compile_program(parse_program(source), **kwargs)
    try:
        return runtime.run_main()
    finally:
        asyncio.run(runtime.aclose())


class CookbookTests(unittest.TestCase):
    def test_incident_main_invokes_profile_tool(self):
        calls = []

        def respond(messages, info):
            calls.append(info)
            self.assertIn("lookup_incident", {t.name for t in info.function_tools})
            evidence = returned(messages, "lookup_incident")
            if evidence is None:
                return ModelResponse(parts=[ToolCallPart("lookup_incident", {"incident_id": 42})])
            self.assertEqual(evidence, "Checkout requests time out. Payments owns mitigation.")
            return output(
                info,
                {
                    "incident": {
                        "id": 42,
                        "title": "Checkout timeout",
                        "owner": "Payments",
                        "severity": "high",
                    }
                },
            )

        source = local_source("complete-program.md")
        result = execute(
            source,
            adapter=PydanticAdapter(FunctionModel(respond)),
            runtime_globals={"args": SimpleNamespace(incident_id="42")},
        )
        self.assertEqual(result, "#42 [high] Checkout timeout - Payments")
        self.assertEqual(len(calls), 2)
        cases = run_tests(source)[0].cases
        self.assertTrue(all(case.success for case in cases))

    def test_structured_extraction_preserves_native_object(self):
        def respond(messages, info):
            return output(
                info,
                {
                    "incident": {
                        "title": "Payment retries",
                        "severity": "high",
                        "owner": {"name": "Payments", "email": None},
                        "affected_services": ["checkout"],
                        "customer_visible": True,
                    }
                },
            )

        result = execute(
            local_source("structured-extraction.md"),
            adapter=PydanticAdapter(FunctionModel(respond)),
        )
        incident = json.loads(result)
        self.assertEqual(incident["owner"], {"name": "Payments", "email": None})
        self.assertIs(incident["customer_visible"], True)

    def test_approval_edits_path_before_real_write(self):
        def respond(messages, info):
            evidence = returned(messages, "lookup_incident")
            if evidence is None:
                return ModelResponse(parts=[ToolCallPart("lookup_incident", {"incident_id": 42})])
            self.assertEqual(evidence["severity"], "high")
            saved = returned(messages, "write_report")
            if saved is None:
                return ModelResponse(
                    parts=[
                        ToolCallPart(
                            "write_report",
                            {
                                "path": "unapproved.md",
                                "content": "Incident 42: high checkout latency.",
                            },
                        )
                    ]
                )
            self.assertEqual(saved, "reports/incident-42.md")
            return output(info, {"saved_path": saved})

        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            result = execute(
                local_source("tools-and-approvals.md"),
                adapter=PydanticAdapter(FunctionModel(respond)),
            )
            self.assertEqual(Path(result).read_text(), "Incident 42: high checkout latency.")
            self.assertFalse(Path("unapproved.md").exists())

    def test_invalid_extraction_is_not_rendered_as_success(self):
        def respond(messages, info):
            return output(
                info,
                {
                    "incident": {
                        "title": "Payment retries",
                        "severity": "invented-severity",
                        "owner": None,
                        "affected_services": [],
                        "customer_visible": True,
                    }
                },
            )

        with self.assertLogs("kedi", level="ERROR"), self.assertRaises(KediExecutionError):
            execute(
                local_source("structured-extraction.md"),
                adapter=PydanticAdapter(FunctionModel(respond), retries=0),
            )

    def test_typed_child_is_consumed(self):
        child_results = []
        payload = {
            "claim": "Migration failure blocks release",
            "confidence": 0.9,
            "evidence": ["migration check failed"],
        }

        def respond(messages, info):
            if "delegate_task" not in {t.name for t in info.function_tools}:
                child_results.append(payload)
                return output(info, {"task_summary": "Release blocked", "final_result": payload})
            child = returned(messages, "delegate_task")
            if child is None:
                return ModelResponse(
                    parts=[
                        ToolCallPart(
                            "delegate_task",
                            {
                                "subagent": "researcher",
                                "task": "Parser passed, migration failed; both must pass. Explain the blocker.",
                            },
                        )
                    ]
                )
            self.assertEqual(child["final_result"], payload)
            return output(info, {"answer": child["final_result"]})

        answer = execute(
            local_source("agent-delegation.md"), adapter=PydanticAdapter(FunctionModel(respond))
        )
        self.assertEqual(answer.model_dump(), payload)
        self.assertEqual(len(child_results), 1)

    def test_eval_uses_validation_rows(self):
        calls = []

        def respond(messages, info):
            rendered = str(messages)
            calls.append(rendered)
            owner = "Payments" if "payment intents" in rendered else "Search"
            return output(info, {"owner": owner})

        results = run_evals(
            local_source("evaluation-and-optimization.md"),
            adapter=PydanticAdapter(FunctionModel(respond)),
        )
        self.assertEqual(results[0].metrics[0].score, 1.0)
        self.assertEqual(len(calls), 2)
        self.assertTrue(any("New documents" in call for call in calls))

    def test_catalog_package_installs_and_executes(self):
        examples = snippets("modules-and-packaging.md")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "catalog"
            source = package / "src/catalog"
            source.mkdir(parents=True)
            (source / "main.kedi").write_text(examples[0])
            (source / "formatting.kedi").write_text(examples[1])
            (package / "package.kedi").write_text(examples[2])
            with patch.dict(os.environ, {"KEDI_HOME": str(root / "home")}):
                install_package(package / "package.kedi")
                consumer = root / "consumer/report.kedi"
                runtime = compile_program(parse_program(examples[3], source_path=str(consumer)))
                try:
                    self.assertEqual(runtime.run_main(), "$165.50")
                finally:
                    asyncio.run(runtime.aclose())
