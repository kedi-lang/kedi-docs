from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from kedi_highlight import fence, highlight  # noqa: E402


class KediHighlightTests(unittest.TestCase):
    def test_tokens_follow_the_grammar(self) -> None:
        html = highlight(
            "@solve(problem: str) -> str:\n"
            "  > evolve: planner:\n"
            "    >> Plan <problem>. [plan]\n"
            "  [count: int] << Count <plan>.\n"
            '  = `str(count) + "!"`'
        )

        self.assertIn('<span class="nf">solve</span>', html)
        self.assertIn('<span class="nv">problem</span>: <span class="nc">str</span>', html)
        self.assertIn('<span class="k">evolve</span>', html)
        self.assertIn('<span class="nl">planner</span>', html)
        self.assertIn('<span class="o">&lt;</span><span class="nv">plan</span>', html)
        self.assertIn('<span class="nv">count</span>: <span class="nc">int</span>', html)
        self.assertIn('<span class="s">"!"</span>', html)

    def test_columns_count_utf16_units(self) -> None:
        html = highlight(">> 🐈 Merhaba <name>.")

        self.assertIn('<span class="o">&lt;</span><span class="nv">name</span>', html)

    def test_source_text_is_escaped(self) -> None:
        html = highlight(">> Use <a> & <b>.\n= `a & b`")

        self.assertNotIn(" & ", html)
        self.assertEqual(html.count("&amp;"), 2)

    def test_fence_keeps_the_block_attributes(self) -> None:
        html = fence(
            "= <x>",
            "kedi",
            "kedi",
            {},
            None,
            classes=["wide"],
            id_value="example",
            attrs={"title": "main.kedi"},
        )

        self.assertTrue(
            html.startswith('<pre id="example" class="kedi wide" title="main.kedi"><code>')
        )
        self.assertTrue(html.endswith("</code></pre>"))


if __name__ == "__main__":
    unittest.main()
