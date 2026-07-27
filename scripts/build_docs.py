"""Build the documentation and publish its machine-readable Markdown surface."""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "zensical.toml"


@dataclass(frozen=True)
class Page:
    section: str
    title: str
    source: Path


def _page_title(source: Path) -> str:
    for line in source.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError(f"Missing H1 in {source.relative_to(ROOT)}")


def _page_summary(source: Path) -> str:
    lines = source.read_text(encoding="utf-8").splitlines()
    paragraph: list[str] = []
    seen_h1 = False
    in_fence = False

    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("# "):
            seen_h1 = True
            continue
        if not seen_h1:
            continue
        if not line.strip():
            if paragraph:
                break
            continue
        if line.startswith(("#", "-", "*", "|", "!!!", "???", ">")):
            if paragraph:
                break
            continue
        paragraph.append(line.strip())

    summary = " ".join(paragraph)
    summary = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", summary)
    summary = summary.replace("`", "")
    return summary


def _collect_pages(nav: list[object], docs_dir: Path) -> list[Page]:
    pages: list[Page] = []
    seen: set[Path] = set()

    def visit(items: list[object], section: str) -> None:
        for item in items:
            if isinstance(item, str):
                source = docs_dir / item
                if source not in seen:
                    pages.append(Page(section, _page_title(source), source))
                    seen.add(source)
                continue
            if not isinstance(item, dict) or len(item) != 1:
                raise ValueError(f"Unsupported navigation item: {item!r}")
            label, value = next(iter(item.items()))
            if isinstance(value, str):
                source = docs_dir / value
                if source not in seen:
                    pages.append(Page(section, str(label), source))
                    seen.add(source)
            elif isinstance(value, list):
                visit(value, str(label))
            else:
                raise ValueError(f"Unsupported navigation value: {value!r}")

    visit(nav, "Overview")
    return pages


def _markdown_url(site_url: str, source: Path, docs_dir: Path) -> str:
    relative = source.relative_to(docs_dir).as_posix()
    return urljoin(site_url.rstrip("/") + "/", relative)


def _html_path(source: Path, docs_dir: Path, site_dir: Path) -> Path:
    relative = source.relative_to(docs_dir)
    if relative.name == "index.md":
        return site_dir / relative.with_suffix(".html")
    return site_dir / relative.with_suffix("") / "index.html"


def _copy_markdown_and_add_alternates(
    pages: list[Page],
    docs_dir: Path,
    site_dir: Path,
    site_url: str,
) -> None:
    for page in pages:
        relative = page.source.relative_to(docs_dir)
        destination = site_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(page.source, destination)

        html_path = _html_path(page.source, docs_dir, site_dir)
        document = html_path.read_text(encoding="utf-8")
        markdown_url = "/" + relative.as_posix()
        alternate = (
            f'<link rel="alternate" type="text/markdown" '
            f'href="{html.escape(markdown_url, quote=True)}">\n'
        )
        if alternate not in document:
            document = document.replace("</head>", f"  {alternate}</head>", 1)
            html_path.write_text(document, encoding="utf-8")


def _write_llms_index(
    pages: list[Page],
    docs_dir: Path,
    site_dir: Path,
    site_name: str,
    description: str,
    site_url: str,
) -> None:
    lines = [
        f"# {site_name}",
        "",
        f"> {description}",
        "",
        "Typed reference documentation for the Kedi language and Python API.",
    ]
    current_section = ""
    for page in pages:
        if page.section != current_section:
            current_section = page.section
            lines.extend(["", f"## {current_section}", ""])
        url = _markdown_url(site_url, page.source, docs_dir)
        summary = _page_summary(page.source)
        suffix = f": {summary}" if summary else ""
        lines.append(f"- [{page.title}]({url}){suffix}")
    lines.append("")
    (site_dir / "llms.txt").write_text("\n".join(lines), encoding="utf-8")


def _write_llms_full(
    pages: list[Page],
    docs_dir: Path,
    site_dir: Path,
    site_name: str,
    description: str,
    site_url: str,
) -> None:
    sections = [
        f"# {site_name} Documentation",
        "",
        f"> {description}",
        "",
        f"Canonical documentation: {site_url}",
    ]
    for page in pages:
        url = _markdown_url(site_url, page.source, docs_dir)
        source = page.source.read_text(encoding="utf-8").rstrip()
        sections.extend(
            [
                "",
                "---",
                "",
                f"Source: {url}",
                "",
                source,
            ]
        )
    sections.append("")
    (site_dir / "llms-full.txt").write_text("\n".join(sections), encoding="utf-8")


def generate_machine_readable_docs() -> None:
    config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))["project"]
    docs_dir = ROOT / config.get("docs_dir", "docs")
    site_dir = ROOT / config.get("site_dir", "site")
    site_url = config["site_url"]
    pages = _collect_pages(config["nav"], docs_dir)

    _copy_markdown_and_add_alternates(pages, docs_dir, site_dir, site_url)
    _write_llms_index(
        pages,
        docs_dir,
        site_dir,
        config["site_name"],
        config.get("site_description", ""),
        site_url,
    )
    _write_llms_full(
        pages,
        docs_dir,
        site_dir,
        config["site_name"],
        config.get("site_description", ""),
        site_url,
    )
    print(f"Generated Markdown endpoints and LLM indexes for {len(pages)} pages")


def main() -> None:
    arguments = sys.argv[1:] or ["--clean", "--strict"]
    subprocess.run(["zensical", "build", *arguments], cwd=ROOT, check=True)
    generate_machine_readable_docs()


if __name__ == "__main__":
    main()
