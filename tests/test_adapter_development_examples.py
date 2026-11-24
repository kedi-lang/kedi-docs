"""Run the Python published in the Adapter Development section.

Every ``python title="name.py"`` fence in ``docs/adapter-development`` belongs to the module
named by its title. Fences with the same title are concatenated in page order, so a page can
explain one class in several blocks. Each ``run_*.py`` module is a scenario: it is executed in a
fresh interpreter with the assembled modules importable, and fails through its assertions.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION = ROOT / "docs" / "adapter-development"
FENCE = re.compile(
    r'^```python[ \t]+title="(?P<title>[^"]+\.py)"[ \t]*\n(?P<body>.*?)^```[ \t]*$',
    re.MULTILINE | re.DOTALL,
)


def section_modules() -> dict[str, str]:
    """Return the assembled source of every titled module in the section."""

    sources: dict[str, list[str]] = defaultdict(list)
    owners: dict[str, Path] = {}
    for page in sorted(SECTION.glob("*.md")):
        for match in FENCE.finditer(page.read_text(encoding="utf-8")):
            title = match.group("title")
            owner = owners.setdefault(title, page)
            if owner != page:
                raise AssertionError(f"{title} is defined in both {owner.name} and {page.name}")
            sources[title].append(match.group("body"))
    return {title: "\n".join(parts) for title, parts in sources.items()}


class AdapterDevelopmentExampleTests(unittest.TestCase):
    def test_section_publishes_scenarios(self) -> None:
        modules = section_modules()
        self.assertIn("chat_adapter.py", modules)
        self.assertTrue(any(name.startswith("run_") for name in modules))

    def test_published_scenarios_run(self) -> None:
        modules = section_modules()
        with tempfile.TemporaryDirectory() as directory:
            for name, source in modules.items():
                Path(directory, name).write_text(source, encoding="utf-8")
            for name in sorted(name for name in modules if name.startswith("run_")):
                with self.subTest(scenario=name):
                    result = subprocess.run(
                        [sys.executable, "-I", "-c", _runner(name)],
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        timeout=180,
                        env={**os.environ, "PYTHONPATH": directory},
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


def _runner(name: str) -> str:
    # -I drops the script directory and PYTHONPATH; put the assembled modules back explicitly.
    return (
        "import os, runpy, sys\n"
        "sys.path.insert(0, os.getcwd())\n"
        f"runpy.run_path({name!r}, run_name='__main__')\n"
    )


if __name__ == "__main__":
    unittest.main()
