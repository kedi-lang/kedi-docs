"""Offline checks for the shared domain and legacy documentation routes."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from assemble_site import assemble, redirect_page
from build_docs import Page, _copy_markdown_and_add_alternates


class PublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "homepage"
        self.docs = self.root / "docs"
        self.output = self.root / "output"
        self.write(self.home, "index.html", "Homepage")
        self.write(self.home, "assets/cat.webp", "cat")
        self.write(self.home, "examples/inventory.json", "{}")
        for route in (
            "index.html",
            "404.html",
            "tooling/notebook/index.html",
            "examples/index.html",
        ):
            self.write(self.docs, route, "<head></head><body>Docs</body>")
        self.write(self.docs, "tooling/notebook.md", "# Notebook")
        self.write(self.docs, "assets/main.js", "docs assets")
        self.write(self.docs, "llms.txt", "https://kedi-lang.org/docs/tooling/notebook.md")
        self.write(self.docs, "llms-full.txt", "# Kedi")
        self.write(self.docs, "sitemap.xml", "<urlset />")

    @staticmethod
    def write(root: Path, name: str, content: str) -> None:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def build(self) -> int:
        return assemble(
            self.home, self.docs, self.output, {"homepage": "a", "docs": "b", "kedi": "c"}
        )

    def test_homepage_docs_assets_and_legacy_routes(self) -> None:
        self.assertEqual(self.build(), 2)
        self.assertEqual((self.output / "index.html").read_text(), "Homepage")
        self.assertIn("Docs", (self.output / "docs/index.html").read_text())
        self.assertEqual((self.output / "assets/cat.webp").read_text(), "cat")
        self.assertEqual((self.output / "docs/assets/main.js").read_text(), "docs assets")
        self.assertEqual((self.output / "examples/inventory.json").read_text(), "{}")
        redirect = (self.output / "tooling/notebook/index.html").read_text()
        self.assertIn('content="0;url=/docs/tooling/notebook/"', redirect)
        self.assertIn("location.search + location.hash", redirect)
        self.assertNotIn("location.replace", (self.output / "404.html").read_text())
        self.assertEqual((self.output / "tooling/notebook.md").read_text(), "# Notebook")
        self.assertEqual(
            (self.output / "llms.txt").read_bytes(), (self.output / "docs/llms.txt").read_bytes()
        )
        self.assertEqual(json.loads((self.output / "deployment.json").read_text())["homepage"], "a")
        sitemap = ElementTree.fromstring((self.output / "sitemap.xml").read_text())
        self.assertEqual(
            [node.text for node in sitemap.iter() if node.tag.endswith("}loc")],
            [
                "https://kedi-lang.org/homepage-sitemap.xml",
                "https://kedi-lang.org/docs/sitemap.xml",
            ],
        )
        self.assertTrue((self.output / ".nojekyll").exists())

    def test_rebuild_removes_stale_files(self) -> None:
        self.build()
        self.write(self.output, "stale.txt", "old")
        self.build()
        self.assertFalse((self.output / "stale.txt").exists())

    def test_route_collision_is_rejected(self) -> None:
        self.write(self.home, "tooling/notebook/index.html", "Collision")
        with self.assertRaisesRegex(ValueError, "collides"):
            self.build()

    def test_reserved_docs_and_social_covers_are_rejected(self) -> None:
        for name in ("docs/index.html", "assets/kedi-cover.png", "assets/social/banner.png"):
            with self.subTest(name=name):
                self.write(self.home, name, "not allowed")
                with self.assertRaises(ValueError):
                    self.build()
                (self.home / name).unlink()
                if name.startswith(("docs/", "assets/social/")):
                    (self.home / name).parent.rmdir()

    def test_missing_build_and_overlapping_paths_are_rejected(self) -> None:
        for output in (self.home, self.home / "nested", self.root):
            with self.assertRaisesRegex(ValueError, "overlap"):
                assemble(self.home, self.docs, output, {})
        (self.docs / "index.html").unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.build()

    def test_redirect_target_is_escaped(self) -> None:
        self.assertIn("a&amp;b", redirect_page("/docs/a&b/"))

    def test_copy_markdown_alternate_uses_docs_base(self) -> None:
        source = self.root / "source"
        self.write(source, "tooling/notebook.md", "# Notebook")
        self.write(source, "index.md", "# Home")
        pages = [
            Page("Tooling", "Notebook", source / "tooling/notebook.md"),
            Page("", "Home", source / "index.md"),
        ]
        _copy_markdown_and_add_alternates(pages, source, self.docs, "https://kedi-lang.org/docs/")
        document = (self.docs / "tooling/notebook/index.html").read_text()
        self.assertIn('href="https://kedi-lang.org/docs/tooling/notebook.md"', document)
        self.assertIn(
            'href="https://kedi-lang.org/docs/index.md"', (self.docs / "index.html").read_text()
        )
        _copy_markdown_and_add_alternates(pages, source, self.docs, "https://kedi-lang.org/docs/")
        self.assertEqual(
            (self.docs / "tooling/notebook/index.html").read_text().count('rel="alternate"'), 1
        )


if __name__ == "__main__":
    unittest.main()
