"""Run native task and budget guides without network calls or provider credentials."""

import asyncio
import contextlib
import io
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import kedi
from kedi.agent_adapter import PydanticAdapter
from kedi.lang import compile_program, parse_program
from pydantic_ai.models.test import TestModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kedi_examples import _kedi_fences  # noqa: E402


class ReviewAdapter(PydanticAdapter):
    def __init__(self):
        super().__init__(TestModel())
        self.calls = []

    async def produce(self, template, **kwargs):
        self.calls.append(template)
        if kwargs.get("output_schema") is not None:
            return SimpleNamespace(action="Add integration coverage")
        if "[verification:" in template:
            result = {"verification": "Integration tests"}
        elif "[issue:" in template:
            result = {
                "issue": "Unverified integration",
                "recommendation": "Add integration coverage",
            }
        else:
            result = {"recommendation": "Add integration coverage"}
        return {"task_summary": "Reviewed the supplied evidence.", "final_result": result}


def python_snippets(page):
    return re.findall(r"```python\n(.*?)\n```", (ROOT / "docs" / page).read_text(), re.S)


def local_source(page):
    source = _kedi_fences(ROOT / "docs" / page)[0].source
    # Substitute only model selection; execute the published program unchanged.
    return "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("> model:")
    )


class OrchestrationExampleTests(unittest.TestCase):
    def tearDown(self):
        kedi.reset_config()
        kedi.clear_cache()

    def test_native_tasks_materialize_typed_child_outputs(self):
        source = local_source("agentic-engineering/subagent-tasks.md")
        adapter = ReviewAdapter()
        runtime = compile_program(parse_program(source), adapter=adapter)
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                self.assertEqual(runtime.run_main(), "Integration tests")
            self.assertEqual(output.getvalue(), "Add integration coverage\n")
            self.assertEqual(len(adapter.calls), 2)
            self.assertTrue(all("export endpoint" in prompt for prompt in adapter.calls))
        finally:
            asyncio.run(runtime.aclose())

    def test_task_group_joins_processing_before_following_statement(self):
        source = local_source("agentic-engineering/subagent-processing.md")
        adapter = ReviewAdapter()
        runtime = compile_program(parse_program(source), adapter=adapter)
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                self.assertIsNone(runtime.run_main())
            self.assertEqual(len(adapter.calls), 3)
            self.assertEqual(
                output.getvalue().splitlines(),
                [
                    "Add integration coverage",
                    "Add integration coverage",
                    "Both reviews and their processing have finished.",
                ],
            )
        finally:
            asyncio.run(runtime.aclose())

    def test_budget_guide_stops_the_second_model_request(self):
        source = python_snippets("runtime/run-budgets.md")[0]
        namespace = {}
        exec(compile(source, "run-budgets.md", "exec"), namespace)
        self.assertEqual(len(namespace["calls"]), 1)

    def test_explain_example_inspects_without_invocation(self):
        source = python_snippets("tooling/run-and-parse.md")[0]
        namespace = {}
        exec(compile(source, "run-and-parse.md", "exec"), namespace)
        self.assertEqual(len(namespace["report"].calls), 1)

    def test_new_guides_have_navigation_entries(self):
        nav = (ROOT / "zensical.toml").read_text()
        for page in ("agentic-engineering/subagent-tasks.md", "runtime/run-budgets.md"):
            self.assertIn(page, nav)

    def test_history_python_examples_are_valid_python(self):
        for source in python_snippets("runtime/history.md"):
            compile(source, "history.md", "exec")
