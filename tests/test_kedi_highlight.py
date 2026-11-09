from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

from kedi.idle_input import KEDI_IDLE_STYLE

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from kedi_highlight import _CLASSES, fence, highlight  # noqa: E402

STYLESHEETS = ROOT / "docs" / "stylesheets"
SCHEMES = {"light": '[data-md-color-scheme="default"]', "dark": '[data-md-color-scheme="slate"]'}


def _block(css: str, selector: str) -> str:
    return re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)[1]


def _variables(css: str, selector: str, prefix: str) -> dict[str, str]:
    return dict(re.findall(rf"--{prefix}([\w-]+):\s*(#[0-9a-f]{{6}})", _block(css, selector)))


def _luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    light, dark = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class KediHighlightTests(unittest.TestCase):
    def test_tokens_follow_the_grammar(self) -> None:
        html = highlight(
            "@solve(problem: str) -> str:\n"
            "  > evolve: planner:\n"
            "    >> Plan <problem>. [plan]\n"
            "  [count: int] << Count <plan>.\n"
            '  = `str(count) + "!"`'
        )

        self.assertIn('<span class="kt-function">solve</span>', html)
        self.assertIn(
            '<span class="kt-parameter">problem</span>: <span class="kt-type">str</span>', html
        )
        self.assertIn('<span class="kt-keyword">evolve</span>', html)
        self.assertIn('<span class="kt-constant">planner</span>', html)
        self.assertIn(
            '<span class="kt-operator">&lt;</span><span class="kt-variable">plan</span>', html
        )
        self.assertIn(
            '<span class="kt-variable">count</span>: <span class="kt-type">int</span>', html
        )
        self.assertIn('<span class="kt-string">"!"</span>', html)

    def test_columns_count_utf16_units(self) -> None:
        html = highlight(">> 🐈 Merhaba <name>.")

        self.assertIn(
            '<span class="kt-operator">&lt;</span><span class="kt-variable">name</span>', html
        )

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


class KediPaletteTests(unittest.TestCase):
    """Kedi fences keep the REPL's roles apart in both color schemes."""

    css = (STYLESHEETS / "kedi-highlight.css").read_text()
    manual = (STYLESHEETS / "manual.css").read_text()
    repl = {
        name.removeprefix("kedi."): style.split()[0] for name, style in KEDI_IDLE_STYLE.style_rules
    }

    def palette(self, scheme: str) -> dict[str, str]:
        return _variables(self.css, SCHEMES[scheme], "kedi-token-")

    def test_every_role_has_a_rule_and_a_color_in_both_schemes(self) -> None:
        roles = {name.removeprefix("kt-") for name in _CLASSES.values()}
        for role in roles:
            self.assertIn(f"pre.kedi .kt-{role} {{\n  color: var(--kedi-token-{role});", self.css)
        for scheme in SCHEMES:
            self.assertEqual(set(self.palette(scheme)), roles, scheme)

    def test_roles_the_repl_tells_apart_have_different_colors(self) -> None:
        for scheme in SCHEMES:
            palette = self.palette(scheme)
            for first in palette:
                for second in palette:
                    if self.repl[first] != self.repl[second]:
                        self.assertNotEqual(
                            palette[first], palette[second], (scheme, first, second)
                        )

    def test_dark_scheme_uses_the_repl_colors(self) -> None:
        dark = self.palette("dark")
        # The REPL's comment color is too dim on the site's code background.
        self.assertEqual(
            {role: color for role, color in dark.items() if role != "comment"},
            {role: color for role, color in self.repl.items() if role != "comment"},
        )

    def test_every_color_is_readable_on_the_code_background(self) -> None:
        for scheme in SCHEMES:
            background = _variables(self.manual, SCHEMES[scheme], "md-code-")["bg-color"]
            for role, color in self.palette(scheme).items():
                self.assertGreaterEqual(_contrast(color, background), 4.5, (scheme, role))


if __name__ == "__main__":
    unittest.main()
