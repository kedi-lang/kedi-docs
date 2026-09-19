"""Execute manual examples without provider calls or credentials."""

import sys
import unittest
from pathlib import Path

from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from kedi.agent_adapter import PydanticAdapter
from kedi.agent_profile import AgentProfile
from kedi.lang import compile_program, parse_program

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kedi_examples import _kedi_fences  # noqa: E402


def example(page, marker):
    matches = [
        fence.source
        for fence in _kedi_fences(ROOT / "docs/agentic-engineering" / page)
        if marker in fence.source
    ]
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one example for {page}: {marker}")
    return matches[0]


class ProfileContractTests(unittest.TestCase):
    def execute(self, source):
        calls = []

        def respond(messages, info):
            calls.append(info)
            return ModelResponse(
                parts=[ToolCallPart(info.output_tools[0].name, {"answer": "verified"})]
            )

        runtime = compile_program(
            parse_program(source), adapter=PydanticAdapter(FunctionModel(respond))
        )
        try:
            result = runtime.run_main()
        finally:
            runtime.artifacts.close()
        return result, calls

    def test_profile_application_does_not_invoke_model(self):
        source = example("scoping-and-capabilities.md", "> profile: concise:")
        _, calls = self.execute(source)
        self.assertEqual(calls, [])

    def test_last_profile_application_replaces_system(self):
        source = example("scoping-and-capabilities.md", "> profile: concise:")
        result, calls = self.execute(source + "\n>> Answer [answer: str].\n= <answer>\n")
        self.assertEqual(result, "verified")
        self.assertEqual(len(calls), 1)
        self.assertIn("Return one sentence.", calls[0].instructions)
        self.assertNotIn("Return a paragraph.", calls[0].instructions)

    def test_later_directive_replaces_profile_system(self):
        source = example("scoping-and-capabilities.md", "> profile: concise:")
        source += "\n> system: Return a paragraph.\n>> Answer [answer: str].\n= <answer>\n"
        result, calls = self.execute(source)
        self.assertEqual(result, "verified")
        self.assertIn("Return a paragraph.", calls[0].instructions)
        self.assertNotIn("Return one sentence.", calls[0].instructions)

    def test_procedure_retains_outer_settings_and_overrides_timeout(self):
        source = example("instructions-and-settings.md", "@patient_call()")
        result, calls = self.execute(source + "\n= <patient_call()>\n")
        self.assertEqual(result, "verified")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].model_settings["temperature"], 0.2)
        self.assertEqual(calls[0].model_settings["timeout"], 120)

    def test_merge_is_shallow_and_tool_names_are_ordered(self):
        left = AgentProfile(
            settings={"temperature": 0.2, "extra_body": {"left": 1}},
            tools=("first", "second"),
        )
        right = AgentProfile(settings={"extra_body": {"right": 2}}, tools=("first",))
        merged = left.merge(right)
        self.assertEqual(merged.settings, {"temperature": 0.2, "extra_body": {"right": 2}})
        self.assertEqual(merged.tools, ("second", "first"))
        self.assertEqual(merged.merge(AgentProfile(tools=())).tools, merged.tools)
        self.assertEqual(left.tools, ("first", "second"))


if __name__ == "__main__":
    unittest.main()
