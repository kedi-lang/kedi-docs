"""Public embedding and CodeMode examples, using local model fixtures."""

import asyncio
import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import RequestUsage

from kedi.agent_adapter import PydanticAdapter
from kedi.lang import compile_program, parse_program
from test_reviewed_evidence import returned

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kedi_examples import _kedi_fences  # noqa: E402


class OrchestrationExamplesTests(unittest.TestCase):
    def test_procedure_tool_example_uses_its_fixture(self):
        page = ROOT / "docs/agentic-engineering/tools-and-use.md"
        source = _kedi_fences(page)[0].source
        tool_calls = []

        def respond(messages, info):
            notes = returned(messages, "lookup_release")
            if notes is None:
                tool_calls.append("lookup_release")
                return ModelResponse(parts=[ToolCallPart("lookup_release", {"version": "1.4.0"})])
            return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {"answer": notes})])

        runtime = compile_program(
            parse_program(source), adapter=PydanticAdapter(FunctionModel(respond))
        )
        try:
            self.assertEqual(
                runtime.run_main(), "Adds typed child results and fixes cancellation cleanup."
            )
        finally:
            asyncio.run(runtime.aclose())
        self.assertEqual(tool_calls, ["lookup_release"])

    def test_python_embedding_uses_public_configuration_and_persistence(self):
        page = (ROOT / "docs/agentic-engineering/subagent-python.md").read_text()
        snippet = re.findall(r"```python\n(.*?)\n```", page, re.S)[0]
        observed = []

        def respond(messages, info):
            names = {tool.name for tool in info.function_tools}
            if "delegate_task" not in names:
                observed.append("child")
                return ModelResponse(parts=[TextPart("Integration tests were not run.")])
            result = returned(messages, "delegate_task")
            if result is None:
                return ModelResponse(
                    parts=[
                        ToolCallPart(
                            "delegate_task",
                            {
                                "subagent": "reviewer",
                                "task": "Unit tests passed; integration tests were not run.",
                            },
                        )
                    ]
                )
            self.assertIsNone(result["final_result"])
            return ModelResponse(parts=[TextPart(result["task_summary"])])

        counts = []

        class CountingFunctionModel(FunctionModel):
            async def count_tokens(self, messages, model_settings, model_request_parameters):
                counts.append(len(messages))
                return RequestUsage(input_tokens=1)

        adapter = PydanticAdapter(CountingFunctionModel(respond))
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            with (
                patch("kedi.agent_adapter.PydanticAdapter", return_value=adapter),
                contextlib.redirect_stdout(io.StringIO()) as output,
            ):
                exec(compile(snippet, "subagent-python.md", "exec"), {})
            self.assertTrue(Path(".kedi-subagent-state.json").is_file())
            self.assertIn("Integration tests were not run.", output.getvalue())
        self.assertEqual(observed, ["child"])
        self.assertTrue(counts)

    def test_codemode_fixture_discovers_hydrates_and_executes(self):
        page = ROOT / "docs/agentic-engineering/codemode.md"
        source = next(f.source for f in _kedi_fences(page) if "def load_counts" in f.source)
        steps = []

        def respond(messages, info):
            names = {tool.name for tool in info.function_tools}
            self.assertNotIn("load_counts", names)
            self.assertTrue({"search_tools", "get_tool_schema", "execute_code"}.issubset(names))
            if returned(messages, "search_tools") is None:
                steps.append("discover")
                return ModelResponse(parts=[ToolCallPart("search_tools", {"query": "load_counts"})])
            if returned(messages, "get_tool_schema") is None:
                steps.append("hydrate")
                return ModelResponse(
                    parts=[ToolCallPart("get_tool_schema", {"tool_names": ["load_counts"]})]
                )
            if returned(messages, "execute_code") is None:
                steps.append("execute")
                return ModelResponse(
                    parts=[
                        ToolCallPart(
                            "execute_code", {"code": "values = await load_counts()\nsum(values)"}
                        )
                    ]
                )
            result = returned(messages, "execute_code")
            self.assertIn("10", str(result))
            return ModelResponse(parts=[TextPart("10")])

        runtime = compile_program(
            parse_program(source), adapter=PydanticAdapter(FunctionModel(respond))
        )
        try:
            self.assertEqual(runtime.run_main(), "10")
        finally:
            asyncio.run(runtime.aclose())
        self.assertEqual(steps, ["discover", "hydrate", "execute"])


if __name__ == "__main__":
    unittest.main()
