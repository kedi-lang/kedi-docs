"""Check the complete built manual, not just representative navigation pages."""

import json
import re
import sys
import tomllib
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_docs import _collect_pages, _html_path  # noqa: E402
from validate_kedi_examples import _kedi_fences  # noqa: E402


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = set()
        self.links = []
        self.canonical = []
        self.markdown = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs["href"])
        if tag == "link" and attrs.get("type") == "text/markdown":
            self.markdown.append(attrs["href"])


class ReleaseSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = ROOT / "site"
        cls.docs = ROOT / "docs"
        config = tomllib.loads((ROOT / "zensical.toml").read_text())["project"]
        cls.origin = config["site_url"].rstrip("/") + "/"
        cls.pages = _collect_pages(config["nav"], cls.docs)
        cls.html = {
            _html_path(p.source, cls.docs, cls.site): Document(
                _html_path(p.source, cls.docs, cls.site).read_text()
            )
            for p in cls.pages
        }

    def test_all_internal_page_links_and_fragments_resolve(self):
        failures = []
        for path, document in self.html.items():
            current = urljoin(self.origin, path.relative_to(self.site).as_posix())
            for link in document.links:
                target = urlsplit(urljoin(current, link))
                if target.netloc != urlsplit(self.origin).netloc:
                    continue
                if not target.path.startswith("/docs/"):
                    continue  # Homepage and compatibility routes have separate tests.
                destination = self.site / unquote(target.path.removeprefix("/docs/"))
                if destination.is_dir():
                    destination /= "index.html"
                if not destination.is_file():
                    failures.append((path.relative_to(self.site).as_posix(), link, "missing file"))
                elif target.fragment and destination in self.html:
                    if unquote(target.fragment) not in self.html[destination].ids:
                        failures.append(
                            (path.relative_to(self.site).as_posix(), link, "missing anchor")
                        )
        self.assertEqual(failures, [])

    def test_canonical_markdown_sitemap_and_llm_exports_agree(self):
        sitemap = ET.parse(self.site / "sitemap.xml")
        locations = [node.text for node in sitemap.findall(".//{*}loc")]
        expected = set()
        index = (self.site / "llms.txt").read_text()
        full = (self.site / "llms-full.txt").read_text()
        for page in self.pages:
            relative = page.source.relative_to(self.docs).as_posix()
            route = relative[:-8] if relative.endswith("index.md") else relative[:-3] + "/"
            canonical = urljoin(self.origin, route)
            markdown = urljoin(self.origin, relative)
            expected.add(canonical)
            document = self.html[_html_path(page.source, self.docs, self.site)]
            with self.subTest(page=relative):
                self.assertEqual(document.canonical, [canonical])
                self.assertEqual(document.markdown, [markdown])
                self.assertEqual((self.site / relative).read_bytes(), page.source.read_bytes())
                self.assertEqual(index.count(f"]({markdown})"), 1)
                self.assertEqual(full.count(f"Source: {markdown}\n"), 1)
                self.assertIn(page.source.read_text().rstrip(), full)
        self.assertEqual(set(locations), expected)
        self.assertEqual(len(locations), len(expected))

    def test_search_and_downloads_cover_current_sources(self):
        search = json.loads((self.site / "search.json").read_text())
        roots = {entry["location"].split("#", 1)[0] for entry in search["items"]}
        for page in self.pages:
            relative = page.source.relative_to(self.docs).as_posix()
            route = relative[:-8] if relative.endswith("index.md") else relative[:-3] + "/"
            self.assertIn(route, roots)
        for source in (self.docs / "assets").rglob("*"):
            if source.is_file():
                self.assertEqual(
                    (self.site / source.relative_to(self.docs)).read_bytes(), source.read_bytes()
                )

    def test_new_optimize_examples_use_explicit_templates(self):
        for page in self.docs.rglob("*.md"):
            for fence in _kedi_fences(page):
                lines = fence.source.splitlines()
                for index, line in enumerate(lines):
                    if re.match(r"\s*> optimize:", line):
                        body = next(value.strip() for value in lines[index + 1 :] if value.strip())
                        self.assertTrue(body.startswith(">>"), f"{page}: {body}")

    def test_brand_logo_is_transparent_vector_art(self):
        config = tomllib.loads((ROOT / "zensical.toml").read_text())["project"]
        logo = self.docs / config["theme"]["logo"]
        self.assertEqual(logo.suffix, ".svg")
        root = ET.parse(logo).getroot()
        self.assertEqual(root.attrib["viewBox"], "0 0 1692 1096")
        tags = {node.tag.rsplit("}", 1)[-1] for node in root.iter()}
        self.assertEqual(tags, {"svg", "path"})
        self.assertNotIn("data:image", logo.read_text())

    def test_no_obsolete_general_example_models_or_personal_paths(self):
        forbidden = re.compile(
            r"google-gla:gemini-2\.5-flash|openai:gpt-4(?:o|-)|"
            r"/Users/[^/\s]+/|/home/mert/|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"
        )
        for page in self.docs.rglob("*.md"):
            self.assertIsNone(forbidden.search(page.read_text()), str(page))
