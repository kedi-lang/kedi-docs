"""Exercise CLI and incremental examples published in the tooling chapter."""

import sys
import unittest
from pathlib import Path

from click.testing import CliRunner

import kedi
from kedi.cli import main
from kedi.errors import KediExecutionError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_kedi_examples import _kedi_fences  # noqa: E402


class ToolingExampleTests(unittest.TestCase):
    def test_documented_parse_and_inline_commands(self):
        runner = CliRunner()
        for args, expected in [
            (["-c", "= Hello from Kedi"], "Hello from Kedi"),
            (["-p", "-c", "= Hello from Kedi"], "Parsed successfully."),
        ]:
            with self.subTest(args=args):
                result = runner.invoke(main, args)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn(expected, result.output)

    def test_documented_program_arguments(self):
        source = _kedi_fences(ROOT / "docs/tooling/run-and-parse.md")[0].source
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("greet.kedi").write_text(source)
            result = runner.invoke(main, ["greet.kedi", "--name", "Ada", "--verbose"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Hello, Ada. Verbose output is enabled.", result.output)

    def test_notebook_cells_require_execution_order(self):
        cells = [f.source for f in _kedi_fences(ROOT / "docs/tooling/notebook.md")]
        self.assertEqual(len(cells), 2)
        with kedi.interactive() as session:
            with self.assertRaises(KediExecutionError):
                session.execute(cells[1])
            session.execute(cells[0])
            self.assertEqual(session.execute(cells[1]), 38)
            self.assertEqual(session.execute(cells[1]), 38)

    def test_cli_default_inventory(self):
        defaults = {p.name: p.default for p in main.params}
        self.assertEqual(defaults["adapter"], "pydantic")
        self.assertEqual(defaults["adapter_model"], "groq:qwen/qwen3-32b")
        self.assertEqual(defaults["optimizer"], "mock")
        self.assertEqual(defaults["optimizer_max_metric_calls"], 100)
        self.assertEqual(defaults["codegen_retries"], 5)
