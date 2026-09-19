"""Execute the downloadable tutorial through the real Kedi/Pydantic boundary."""

import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel

from kedi import ApprovalDecision, current_subagent_execution, observe_agent_events
from kedi.agent_adapter import PydanticAdapter
from kedi.errors import KediExecutionError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kedi_examples import _kedi_fences  # noqa: E402

EXAMPLE = ROOT / "docs/assets/examples/reviewed_evidence.py"
SOURCE = EXAMPLE.with_suffix(".kedi")


def returned(messages, name):
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in reversed(message.parts):
                if isinstance(part, ToolReturnPart) and part.tool_name == name:
                    return part.content
    return None


class ReviewedEvidenceTests(unittest.TestCase):
    def test_download_matches_manual(self):
        page = ROOT / "docs/agentic-engineering/reviewed-evidence.md"
        self.assertEqual(_kedi_fences(page)[0].source.strip(), SOURCE.read_text().strip())

    def run_tutorial(self, *, dynamic=False, deny=False, invalid_child=False):
        calls = []
        events = []
        stream_events = []
        children = []
        parent_results = []
        namespace = runpy.run_path(str(EXAMPLE))
        original_read_text = Path.read_text

        def read_source(path, *args, **kwargs):
            text = original_read_text(path, *args, **kwargs)
            if dynamic and path == SOURCE:
                return text.replace(
                    "    > subagent: reviewer\n",
                    "    > subagent: reviewer\n    > workflow: dynamic\n",
                )
            return text

        def respond(messages, info):
            names = {tool.name for tool in info.function_tools}
            calls.append(names)
            if "read_evidence" in names:
                self.assertNotIn("write_report", names)
                self.assertNotIn("delegate_task", names)
                evidence = returned(messages, "read_evidence")
                if evidence is None:
                    return ModelResponse(
                        parts=[
                            ToolCallPart(
                                "read_evidence", {"suite": "parser"}, tool_call_id="evidence-call"
                            )
                        ]
                    )
                self.assertEqual(evidence["failures"], ["unicode_identifier"])
                result = {
                    "failures": evidence["failures"],
                    "may_release": False if not invalid_child else "not-a-boolean",
                }
                children.append(result)
                return ModelResponse(
                    parts=[
                        ToolCallPart(
                            info.output_tools[0].name,
                            {"task_summary": "One failing parser test.", "final_result": result},
                        )
                    ]
                )

            self.assertIn("write_report", names)
            self.assertNotIn("read_evidence", names)
            orchestration = "run_workflow" if dynamic else "delegate_task"
            self.assertIn(orchestration, names)
            review = returned(messages, orchestration)
            if review is None:
                arguments = (
                    {
                        "code": 'review = await reviewer(task="Inspect suite parser using read_evidence.")\nreview'
                    }
                    if dynamic
                    else {
                        "subagent": "reviewer",
                        "task": "Inspect suite parser using read_evidence.",
                    }
                )
                return ModelResponse(parts=[ToolCallPart(orchestration, arguments)])
            if invalid_child:
                return ModelResponse(parts=[TextPart("Unable to obtain valid evidence.")])
            parent_results.append(review)
            written = returned(messages, "write_report")
            if written is not None:
                return ModelResponse(parts=[TextPart(str(written))])
            payload = review["final_result"]
            self.assertIs(payload["may_release"], False)
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "write_report",
                        {
                            "path": "requested.txt",
                            "text": f"Release: {payload['may_release']}; failures: {', '.join(payload['failures'])}",
                        },
                    )
                ]
            )

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(Path, "read_text", read_source),
            observe_agent_events(stream_events.append),
        ):
            adapter = PydanticAdapter(FunctionModel(respond), retries=0, hook_handler=events.append)
            if deny:
                with patch.object(
                    ApprovalDecision, "edit", return_value=ApprovalDecision.deny(reason="test deny")
                ):
                    result = namespace["run_review"](adapter, directory)
                self.assertFalse((Path(directory) / "review.txt").exists())
                self.assertEqual(result["writes"], [])
                self.assertEqual(len(result["approvals"]), 1)
                self.assertTrue(children)
                return
            if invalid_child:
                with (
                    self.assertLogs("kedi", level="ERROR"),
                    self.assertRaises(KediExecutionError) as raised,
                ):
                    namespace["run_review"](adapter, directory)
                self.assertRegex(str(raised.exception), "(?i)validat|retries|delegat|child")
                self.assertFalse((Path(directory) / "review.txt").exists())
                self.assertTrue(children)
                return
            result = namespace["run_review"](adapter, directory)
            self.assertEqual(len(result["writes"]), 1)
            self.assertEqual(len(result["approvals"]), 1)
            self.assertEqual(result["approvals"][0].arguments["path"], "requested.txt")
            self.assertEqual(result["receipt"], str(Path(directory).resolve() / "review.txt"))
            self.assertEqual(
                (Path(directory) / "review.txt").read_text(), result["writes"][0]["text"]
            )
            self.assertIn("unicode_identifier", result["writes"][0]["text"])
            self.assertEqual(len(result["observations"]), 1)
            run_id, profile, conversation_id = result["observations"][0]
            self.assertEqual(profile, "reviewer")
            self.assertEqual(run_id, parent_results[0]["run_id"])
            self.assertTrue(conversation_id)
            reads = [
                event
                for event in events
                if event.event == "post_tool_use" and event.tool_name == "read_evidence"
            ]
            self.assertEqual(len(reads), 1)
            self.assertEqual(reads[0].run_id, run_id)
            self.assertEqual(reads[0].tool_call_id, "evidence-call")
            self.assertEqual(reads[0].arguments["suite"], "parser")
            self.assertIsNotNone(reads[0].parent_run_id)
            self.assertIsNone(current_subagent_execution())

    def test_delegate_workflow(self):
        self.run_tutorial()

    def test_dynamic_workflow(self):
        self.run_tutorial(dynamic=True)

    def test_denied_write_has_no_effect(self):
        self.run_tutorial(deny=True)

    def test_invalid_child_result_cannot_write(self):
        self.run_tutorial(invalid_child=True)


if __name__ == "__main__":
    unittest.main()
