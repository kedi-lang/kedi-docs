"""Keep published historical metrics consistent with the sanitized task projection."""

import copy
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_benchmark_records import percentile, summarize  # noqa: E402

DATA = json.loads((ROOT / "docs/assets/benchmarks/terminal-bench-89x1-metrics.json").read_text())


class BenchmarkMetricsTests(unittest.TestCase):
    def test_projection_summaries_recompute(self):
        for run in DATA["runs"].values():
            self.assertEqual(summarize(run["tasks"]), run["summary"])
            self.assertRegex(run["archive_sha256"], r"^[0-9a-f]{64}$")

    def test_published_totals_and_denominators(self):
        page = (ROOT / "docs/tooling/terminal-bench-results.md").read_text()
        for name, cost, scored in [("pydantic", 4.93781512, 89), ("langchain", 5.05064428, 88)]:
            summary = DATA["runs"][name]["summary"]
            self.assertEqual(summary["solved"], 68)
            self.assertEqual(summary["scored"], scored)
            self.assertAlmostEqual(summary["totals"]["cost_usd"], cost, places=8)
            self.assertIn(f"${cost:.8f}", page)
            self.assertIn(f"${cost / 89:.8f}", page)
            self.assertIn(f"${cost / 68:.8f}", page)
            self.assertIn(f"{summary['cache_read_ratio'] * 100:.2f}%", page)
            for metric in [
                "input_tokens",
                "cache_tokens",
                "output_tokens",
                "requests",
                "tool_calls",
            ]:
                self.assertIn(f"{summary['totals'][metric]:,}", page)

    def test_unscored_task_is_not_fabricated_zero_reward(self):
        rows = DATA["runs"]["langchain"]["tasks"]
        unscored = [row for row in rows if row["reward"] is None]
        self.assertEqual(len(unscored), 1)
        self.assertEqual(unscored[0]["task"], "model-extraction-relu-logits")
        self.assertEqual(unscored[0]["exception_type"], "VerifierTimeoutError")
        self.assertEqual(summarize(rows)["score"], 68 / 89)

    def test_matched_task_identity_and_outcomes(self):
        a, b = (
            {r["task"]: r["reward"] for r in DATA["runs"][name]["tasks"]}
            for name in ("pydantic", "langchain")
        )
        self.assertEqual(set(a), set(b))
        self.assertEqual(sum(a[t] == b[t] == 1 for t in a), 62)
        self.assertEqual(sum(a[t] == 1 and b[t] != 1 for t in a), 6)
        self.assertEqual(sum(b[t] == 1 and a[t] != 1 for t in a), 6)

    def test_duplicate_tasks_and_invalid_rewards_rejected(self):
        rows = copy.deepcopy(DATA["runs"]["pydantic"]["tasks"])
        rows[0]["task"] = rows[1]["task"]
        with self.assertRaisesRegex(ValueError, "unique"):
            summarize(rows)
        rows = copy.deepcopy(DATA["runs"]["pydantic"]["tasks"])
        rows[0]["reward"] = 0.5
        with self.assertRaisesRegex(ValueError, "Non-binary"):
            summarize(rows)

    def test_interpolation_and_counter_definitions(self):
        self.assertAlmostEqual(percentile([0, 10], 0.95), 9.5)
        for name, count in [("pydantic", 3849), ("langchain", 3867)]:
            rows = DATA["runs"][name]["tasks"]
            self.assertEqual(sum(r["emitted_tool_call_parts"] for r in rows), count)
            self.assertLess(max(r["max_request_input_tokens"] for r in rows), 272000)

    def test_projection_has_only_allowlisted_fields(self):
        allowed = {
            "task",
            "batch",
            "reward",
            "exception_type",
            "input_tokens",
            "cache_tokens",
            "output_tokens",
            "requests",
            "tool_calls",
            "emitted_tool_call_parts",
            "cost_usd",
            "started_at",
            "finished_at",
            "duration_seconds",
            "max_request_input_tokens",
        }
        for run in DATA["runs"].values():
            for row in run["tasks"]:
                self.assertEqual(set(row), allowed)
                self.assertTrue(re.fullmatch(r"[a-z0-9][a-z0-9.-]*", row["task"]))
                self.assertGreaterEqual(row["input_tokens"], row["cache_tokens"])
