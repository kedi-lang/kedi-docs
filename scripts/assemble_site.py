"""Combine the homepage and /docs into the single GitHub Pages publication."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path
from urllib.parse import quote

ORIGIN = "https://kedi-lang.org"


def redirect_page(target: str) -> str:
    escaped = html.escape(target, quote=True)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Documentation moved - Kedi</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{ORIGIN}{escaped}">
<meta http-equiv="refresh" content="0;url={escaped}">
<script>location.replace({json.dumps(target)} + location.search + location.hash);</script>
</head><body><p>The documentation has moved to <a href="{escaped}">{escaped}</a>.</p></body></html>
"""


def assemble(homepage: Path, docs: Path, output: Path, revisions: dict[str, str]) -> int:
    homepage, docs, output = (path.resolve() for path in (homepage, docs, output))
    for source in (homepage, docs):
        if source == output or source in output.parents or output in source.parents:
            raise ValueError("Output must not overlap a source directory")
        if not (source / "index.html").is_file():
            raise ValueError(f"Missing built index.html: {source}")
    if (homepage / "docs").exists():
        raise ValueError("The homepage must not own the reserved /docs route")
    for path in homepage.rglob("*"):
        relative = path.relative_to(homepage)
        if "kedi-cover" in path.name.lower() or relative.parts[:2] == ("assets", "social"):
            raise ValueError(f"Social cover is not a website asset: {relative}")

    # Build the entire tree before publishing; neither repository deploys alone.
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(homepage, output)
    shutil.copytree(docs, output / "docs")

    redirects = 0
    for page in sorted(docs.rglob("*.html")):
        relative = page.relative_to(docs)
        if relative.as_posix() in {"index.html", "404.html"}:
            continue
        destination = output / relative
        if destination.exists():
            raise ValueError(f"Homepage collides with a legacy docs route: {relative}")
        route = relative.as_posix()
        if route.endswith("index.html"):
            route = route.removesuffix("index.html")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(redirect_page("/docs/" + quote(route, safe="/")), encoding="utf-8")
        redirects += 1

    # Raw Markdown and LLM indexes keep working for clients that do not run JS.
    for page in [*docs.rglob("*.md"), docs / "llms.txt", docs / "llms-full.txt"]:
        if page.is_file():
            destination = output / page.relative_to(docs)
            if destination.exists():
                raise ValueError(f"Homepage collides with a raw docs endpoint: {destination}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(page, destination)

    (output / "404.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Page not found - Kedi</title></head><body>"
        '<h1>Page not found</h1><p><a href="/">Kedi home</a> '
        '| <a href="/docs/">Documentation</a></p></body></html>\n',
        encoding="utf-8",
    )
    (output / "CNAME").write_text("kedi-lang.org\n", encoding="utf-8")
    (output / ".nojekyll").touch()
    (output / "deployment.json").write_text(
        json.dumps(revisions, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (output / "homepage-sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{ORIGIN}/</loc></url></urlset>\n",
        encoding="utf-8",
    )
    (output / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<sitemap><loc>{ORIGIN}/homepage-sitemap.xml</loc></sitemap>"
        f"<sitemap><loc>{ORIGIN}/docs/sitemap.xml</loc></sitemap></sitemapindex>\n",
        encoding="utf-8",
    )
    (output / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n", encoding="utf-8"
    )
    return redirects


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--homepage", type=Path, required=True)
    parser.add_argument("--docs", type=Path, default=Path("site"))
    parser.add_argument("--output", type=Path, default=Path("public-site"))
    parser.add_argument("--homepage-sha", required=True)
    parser.add_argument("--docs-sha", required=True)
    parser.add_argument("--kedi-sha", required=True)
    args = parser.parse_args()
    count = assemble(
        args.homepage,
        args.docs,
        args.output,
        {
            "homepage": args.homepage_sha,
            "docs": args.docs_sha,
            "kedi": args.kedi_sha,
        },
    )
    print(f"Assembled homepage, /docs, and {count} legacy redirects in {args.output}")


if __name__ == "__main__":
    main()
