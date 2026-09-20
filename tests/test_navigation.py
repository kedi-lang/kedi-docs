"""Navigation ownership and published route/fragment compatibility."""

import json
import re
import sys
import tomllib
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_docs import _collect_pages, _page_title  # noqa: E402


class Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        value = dict(attrs).get("id")
        if value:
            self.ids.add(value)


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.nav = tomllib.loads((ROOT / "zensical.toml").read_text())["project"]["nav"]
        legacy = json.loads((ROOT / "tests/fixtures/legacy-routes.json").read_text())
        self.legacy = {route.removeprefix("/docs"): anchors for route, anchors in legacy.items()}

    def test_every_source_has_one_owner(self):
        sources = []

        def walk(items):
            self.assertTrue(items, "Navigation groups must not be empty")
            for item in items:
                if isinstance(item, str):
                    sources.append(item)
                else:
                    for value in item.values():
                        walk(value if isinstance(value, list) else [value])

        walk(self.nav)
        self.assertEqual(len(sources), len(set(sources)))
        actual = {p.relative_to(ROOT / "docs").as_posix() for p in (ROOT / "docs").rglob("*.md")}
        self.assertEqual(set(sources), actual)
        routes = {
            "/"
            if source == "index.md"
            else "/" + (source[:-8] if source.endswith("index.md") else source[:-3] + "/")
            for source in sources
        }
        self.assertTrue(set(self.legacy).issubset(routes))

    def test_machine_index_keeps_full_ancestry(self):
        pages = _collect_pages(self.nav, ROOT / "docs")
        sections = {p.source.relative_to(ROOT / "docs").as_posix(): p.section for p in pages}
        self.assertEqual(
            sections["agent-adapters/typesafe.md"], "Models and Integrations / Decision Models"
        )
        self.assertEqual(
            sections["python-interop/python-blocks.md"], "Language Reference / Python Interop"
        )
        self.assertEqual(sections["tooling/terminal-bench.md"], "Benchmarks / Terminal-Bench 2.1")

    def test_heading_attributes_are_not_titles(self):
        self.assertEqual(_page_title(ROOT / "docs/core-language/index.md"), "Language Reference")

    def test_overview_exports_use_descriptive_titles(self):
        pages = _collect_pages(self.nav, ROOT / "docs")
        titles = {p.source.name: p.title for p in pages}
        self.assertEqual(titles["subagents.md"], "Subagents")
        self.assertEqual(titles["codemode.md"], "CodeMode")

    def test_language_has_one_reading_order(self):
        source = (ROOT / "docs/core-language/index.md").read_text()
        self.assertNotIn("Read the section in this order:", source)
        self.assertEqual(source.count("## In This Section"), 1)

    def test_skill_examples_use_the_dedicated_directive(self):
        for page in (ROOT / "docs").rglob("*.md"):
            with self.subTest(page=page):
                source = page.read_text()
                self.assertIsNone(re.search(r">\s*use:\s*`?skills\b", source))
                self.assertNotIn("reserved name `skills`", source)

    def test_tutorial_downloads_are_published_verbatim(self):
        for extension in ("py", "kedi"):
            relative = Path(f"assets/examples/reviewed_evidence.{extension}")
            self.assertEqual(
                (ROOT / "site" / relative).read_bytes(), (ROOT / "docs" / relative).read_bytes()
            )

    def test_published_routes_and_old_fragments_survive(self):
        self.assertTrue(
            (ROOT / "site/index.html").exists(), "Build docs before publication validation"
        )
        for route, anchors in self.legacy.items():
            with self.subTest(route=route):
                page = ROOT / "site" / route.removeprefix("/") / "index.html"
                self.assertTrue(page.exists())
                parser = Ids()
                parser.feed(page.read_text())
                self.assertFalse(set(anchors) - parser.ids, set(anchors) - parser.ids)


if __name__ == "__main__":
    unittest.main()
