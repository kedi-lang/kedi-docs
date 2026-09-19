"""Run the manual's validation examples without external models."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from kedi.app import run_evals_cli
from kedi.tests_runner import run_evals, run_tests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
KEDI_SOURCE = ROOT / ".kedi-source" if (ROOT / ".kedi-source").is_dir() else ROOT.parent
sys.path.insert(0, str(KEDI_SOURCE / "tests"))
from mock_adapter import MockAdapter  # noqa: E402
from validate_kedi_examples import _kedi_fences  # noqa: E402


def examples(page):
    return [f.source for f in _kedi_fences(ROOT / "docs/evals-and-optimization" / page)]


class ValidationExampleTests(unittest.TestCase):
    def test_all_test_block_examples(self):
        for source in examples("test-blocks.md"):
            with self.subTest(source=source.splitlines()[0]):
                results = run_tests(source, adapter=MockAdapter())
                self.assertTrue(results)
                for suite in results:
                    for case in suite.cases:
                        self.assertTrue(case.success, case.error)

    def test_dataset_examples_execute(self):
        for source in examples("datasets-and-metrics.md"):
            if "@eval:" not in source or ">>" in source:
                continue
            with self.subTest(source=source.splitlines()[0]):
                metric = run_evals(source, adapter=MockAdapter())[0].metrics[0]
                self.assertEqual(metric.score, 1.0, metric.feedback)
                self.assertNotIn("error:", metric.feedback or "")

    def test_workflow_and_regression(self):
        source = examples("validation-workflow.md")[0]
        self.assertTrue(all(c.success for s in run_tests(source) for c in s.cases))
        self.assertEqual(run_evals(source)[0].metrics[0].score, 1.0)
        broken = source.replace(".split()", '.split(" ")')
        self.assertFalse(run_tests(broken)[0].cases[0].success)
        self.assertEqual(run_evals(broken)[0].metrics[0].score, 0.5)

    def test_row_error_continues_and_bad_dataset_fails(self):
        source = examples("validation-workflow.md")[1]
        metric = run_evals(source)[0].metrics[0]
        self.assertAlmostEqual(metric.score, 2 / 3)
        self.assertIn("error:", metric.feedback)
        with self.assertRaises(RuntimeError):
            run_evals(source.replace("[2, 0, 4]", "42"))

    def test_empty_test_data_does_not_fall_back_to_training(self):
        source = examples("validation-workflow.md")[0]
        source = source.replace(
            '[("  Release   Notes ", {"label": "release-notes"}), ("", {"label": ""})]',
            "[]",
        )
        metric = run_evals(source)[0].metrics[0]
        self.assertEqual(metric.score, 0.0)
        self.assertEqual(metric.feedback, "no examples")

    def test_scalar_pair_is_not_an_expected_binding(self):
        source = examples("datasets-and-metrics.md")[0]
        source = source.replace('{"count": 2}', "2").replace('{"count": 3}', "3")
        metric = run_evals(source)[0].metrics[0]
        self.assertEqual(metric.score, 0.0)
        self.assertIn("error:", metric.feedback)

    def test_eval_exit_status_is_not_a_quality_gate(self):
        source = examples("validation-workflow.md")[0].replace(".split()", '.split(" ")')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labels.kedi"
            path.write_text(source)
            with patch("kedi.app._build_runtime_adapter", return_value=MockAdapter()):
                status, output = run_evals_cli(str(path))
            self.assertEqual(status, 0)
            self.assertIn("0.5000", output)

    def test_optimized_prefix_preserves_template(self):
        source = next(s for s in examples("prompt-optimization.md") if "@eval:" in s)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owner.kedi"
            path.write_text(source)
            artifact = path.with_suffix(".kedi.optimized.json")
            artifact.write_text(
                json.dumps({"extract_owner": {"owner": "Use explicit ownership evidence."}})
            )
            adapter = MockAdapter()
            run_evals(str(path), adapter=adapter)
            self.assertEqual(len(adapter.request_calls), 1)
            self.assertIn("Use explicit ownership evidence.", adapter.request_calls[0])
            self.assertIn("owner", adapter.request_calls[0])
            self.assertIn("Owner: Ada", adapter.request_calls[0])
            artifact.write_text("not json")
            with self.assertRaises(Exception):
                run_evals(str(path), adapter=MockAdapter())
