"""Regression tests for kedi-lang/kedi#215 (kedi-docs findings).

Every test fails on the base commit (b0bce7f) and passes with the fix.
Kedi-stable reference commit: ee9093c.
"""

import ast
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "scripts"))
from build_docs import _page_summary  # noqa: E402


def _read(relative: str) -> str:
    return (DOCS / relative).read_text(encoding="utf-8")


class CodemodeTests(unittest.TestCase):
    def test_codemode_import_is_valid(self):
        """P0-1: CodeModeSettings is not importable from kedi.agent_adapter."""
        text = _read("agentic-engineering/codemode.md")
        self.assertNotIn("from kedi.agent_adapter import CodeModeSettings", text)
        self.assertIn("CodeModeSettings", text)
        # The documented import location must actually provide the symbol.
        from kedi import CodeModeSettings  # noqa: F401

    def test_codemode_python_blocks_parse(self):
        """P2-4: every ```python block in codemode.md is valid Python."""
        text = _read("agentic-engineering/codemode.md")
        blocks = re.findall(r"```python\n(.*?)```", text, re.S)
        self.assertTrue(blocks)
        for block in blocks:
            with self.subTest(block=block.splitlines()[0][:60]):
                ast.parse(block)


class CliAndEnvTests(unittest.TestCase):
    def test_no_adapter_a2a(self):
        """P0-2: --adapter does not list a2a; A2A is served via `kedi a2a`."""
        text = _read("reference/cli.md")
        row = next(line for line in text.splitlines() if "--adapter NAME" in line)
        self.assertNotIn("a2a", row)
        self.assertIn("kedi a2a serve", text)

    def test_python_api_dotenv_behavior_is_explicit(self):
        """Configuration loads dotenv; low-level adapter construction does not."""
        text = _read("reference/environment-variables.md")
        self.assertIn("default configuration does not either", " ".join(text.split()))
        self.assertIn("`kedi.configure()` and the `kedi` CLI load", text)
        self.assertIn("dotenv.load_dotenv()", text)

    def test_registry_url_documented(self):
        """P0-5: the public registry and KEDI_REGISTRY_URL are documented."""
        text = _read("reference/environment-variables.md")
        self.assertIn("KEDI_REGISTRY_URL", text)
        self.assertIn("https://registry.kedi-lang.org", text)
        self.assertNotIn("until the public registry exists", text)

    def test_a2a_prompt_only_hooks_in_matrix(self):
        """P0-6: the matrix says A2A, like ACP, exposes only user_prompt_submit."""
        text = _read("reference/capability-matrix.md")
        line = next(line for line in text.splitlines() if "only `user_prompt_submit`" in line)
        self.assertIn("A2A", line)
        self.assertIn("ACP", line)

    def test_cli_and_env_reference_gaps(self):
        """P1-2: explain/audit/debug --stdio/--state-dir and env vars are covered."""
        cli = _read("reference/cli.md")
        for token in ("kedi explain", "kedi audit", "kedi debug --stdio", "--state-dir"):
            self.assertIn(token, cli)
        env = _read("reference/environment-variables.md")
        for token in ("KEDI_A2A_STATE_DIR", "NO_COLOR"):
            self.assertIn(token, env)


class DirectivesTests(unittest.TestCase):
    def test_directives_gaps(self):
        """P1-1: budget/capability/defer/hooks/artifacts fields are listed."""
        text = _read("reference/directives.md")
        for token in (
            "> budget:",
            "> capability:",
            "> defer:",
            "post_tool_result_failure",
            "exclude_tools",
        ):
            self.assertIn(token, text)
        self.assertIn("enabled", text)
        lines = text.splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("`> hooks:` fields"))
        hooks = " ".join(lines[index : index + 3])
        self.assertIn("post_tool_result_failure", hooks)
        self.assertIn("enabled", hooks)


class InstallationTests(unittest.TestCase):
    def test_no_separate_pydantic_ai_slim_openai(self):
        """P0-4: 0.1.5 does not need a separate pydantic-ai-slim[openai] install."""
        text = _read("getting-started/installation.md")
        self.assertNotIn("also need `pydantic-ai-slim[openai]`", text)
        self.assertIn("no separate install", text)

    def test_install_extras(self):
        """P1-4: snapshots/terminal-bench/a2a/a2a-persistence extras are listed."""
        text = _read("getting-started/installation.md")
        for extra in ("snapshots", "terminal-bench", "a2a", "a2a-persistence"):
            self.assertIn(f"kedi[{extra}]", text)


class CapabilityMatrixTests(unittest.TestCase):
    FIELDS = (
        "supports_artifacts",
        "supports_native_artifacts",
        "supports_stateful_history",
        "supports_history_replay",
        "supports_native_compaction",
        "supports_request_budget",
        "supports_tool_attempt_budget",
    )

    def test_sync_script_covers_all_fields(self):
        """P1-3: the 7 AdapterCapabilities fields are in sync_capability_matrix.py."""
        script = (ROOT / "scripts" / "sync_capability_matrix.py").read_text()
        for field in self.FIELDS:
            self.assertIn(field, script)

    def test_matrix_covers_all_fields(self):
        """P1-3: the 7 fields are rows in the generated matrix."""
        text = _read("reference/capability-matrix.md")
        for field in self.FIELDS:
            label = field.removeprefix("supports_").replace("_", " ")
            self.assertIn(label, text.lower())

    def test_matrix_matches_adapter_metadata(self):
        """P1-3: `sync_capability_matrix.py --check` passes against installed kedi."""
        try:
            import kedi  # noqa: F401
        except ImportError:
            self.skipTest("kedi is not installed")
        result = subprocess.run(
            [sys.executable, "scripts/sync_capability_matrix.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class AdapterSettingsTests(unittest.TestCase):
    @staticmethod
    def _setting_keys():
        import kedi

        settings = Path(kedi.__file__).resolve().parent / "agent_profile" / "settings.py"
        tree = ast.parse(settings.read_text(encoding="utf-8"))
        keys = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name = node.target.id
                if name.endswith("_SETTING_KEYS") and isinstance(node.value, ast.Call):
                    keys[name] = sorted(
                        elt.value
                        for elt in node.value.args[0].elts
                        if isinstance(elt, ast.Constant)
                    )
        return keys

    def test_pydantic_ai_settings_complete(self):
        """P1-5: pydantic-ai.md documents all 22 settings (19 + 3 runtime)."""
        try:
            keys = self._setting_keys()
        except ImportError:
            self.skipTest("kedi is not installed")
        expected = sorted(
            set(keys["PYDANTIC_MODEL_SETTING_KEYS"]) | set(keys["KEDI_RUNTIME_SETTING_KEYS"])
        )
        text = _read("agent-adapters/pydantic-ai.md")
        missing = [key for key in expected if key not in text]
        self.assertEqual(missing, [], f"missing settings: {missing}")

    def test_langchain_settings_complete(self):
        """P1-5: langchain.md documents all 37 settings (34 + 3 runtime)."""
        try:
            keys = self._setting_keys()
        except ImportError:
            self.skipTest("kedi is not installed")
        expected = sorted(
            set(keys["LANGCHAIN_MODEL_SETTING_KEYS"]) | set(keys["KEDI_RUNTIME_SETTING_KEYS"])
        )
        text = _read("agent-adapters/langchain.md")
        missing = [key for key in expected if key not in text]
        self.assertEqual(missing, [], f"missing settings: {missing}")

    def test_settings_tables_are_generated(self):
        """P1-5: the generated settings tables match the sync script output."""
        try:
            import kedi  # noqa: F401
        except ImportError:
            self.skipTest("kedi is not installed")
        result = subprocess.run(
            [sys.executable, "scripts/sync_adapter_settings.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class BuildDocsTests(unittest.TestCase):
    def test_page_summary_four_backtick_fence(self):
        """P2-1: _page_summary keeps fence tracking inside ```` blocks."""
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.md"
            page.write_text(
                "# Title\n\n````kedi\n```\n```\n```\n````\n\nReal first paragraph here.\n",
                encoding="utf-8",
            )
            self.assertEqual(_page_summary(page), "Real first paragraph here.")


class StandaloneCheckoutTests(unittest.TestCase):
    def test_mock_adapter_is_vendored(self):
        """P2-2: a standalone checkout has its own mock_adapter."""
        self.assertTrue((ROOT / "tests" / "mock_adapter.py").exists())
        for name in ("test_manual_contracts.py", "test_validation_examples.py"):
            text = (ROOT / "tests" / name).read_text(encoding="utf-8")
            self.assertIn('ROOT / "tests"', text)
            self.assertNotIn('sys.path.insert(0, str(KEDI_SOURCE / "tests"))', text)

    def test_standalone_import(self):
        """P2-2: the contract tests import without a surrounding kedi checkout."""
        try:
            import kedi  # noqa: F401
        except ImportError:
            self.skipTest("kedi is not installed")
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "kedi-docs"
            shutil.copytree(
                ROOT,
                copy,
                ignore=shutil.ignore_patterns(".git", "site", "__pycache__", ".kedi-source"),
            )
            env = dict(**{k: v for k, v in __import__("os").environ.items()})
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.path.insert(0, 'tests'); sys.path.insert(0, 'scripts');"
                    " import test_manual_contracts, test_validation_examples",
                ],
                cwd=copy,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class StaleVersionTests(unittest.TestCase):
    def test_no_stale_versions(self):
        """Pages name current releases and the compatible published editor stack."""
        self.assertNotIn("0.1.4", _read("tooling/repl.md"))
        self.assertNotIn("0.1.4", _read("tooling/terminal-bench.md"))
        self.assertNotIn("0.3.0 package", _read("agent-adapters/typesafe.md"))
        for page in ("tooling/vscode.md", "tooling/zed.md"):
            text = _read(page)
            self.assertNotIn("kedi==0.1.4", text)
            self.assertNotIn("tree-sitter-kedi==0.4.6", text)
            self.assertIn("kedi==0.1.5", text)
            self.assertIn("tree-sitter-kedi==0.4.7", text)
            self.assertIn("kedi-debugger==0.1.1", text)
            self.assertNotIn("tree-sitter-kedi==0.4.9", text)


class BuiltInModulesTests(unittest.TestCase):
    def test_built_in_modules_links_exports(self):
        """P2-5: the built-in modules page names the wordle/filesystem exports."""
        text = _read("modules-and-packaging/built-in-modules.md")
        for token in ("WordleSetup", "readonlyfs", "read_text_file", "filesystem.md"):
            self.assertIn(token, text)
        self.assertIn("example-modules.md", text)


if __name__ == "__main__":
    unittest.main()
