# Kedi Programming Language

The Kedi documentation site is built with Zensical.

## Develop

```bash
uv tool run zensical serve
```

## Validate

Install Kedi from the source version the documentation targets, then run:

```bash
python scripts/validate_kedi_examples.py
python scripts/sync_capability_matrix.py --check
uv tool run --from zensical==0.0.51 python scripts/build_docs.py
```

The first command parser-checks Kedi fences with their declared source
filename. The second prevents the committed adapter table from drifting from
`AdapterCapabilities`. The generated static site is written to `site/`; the
build also publishes each source page as Markdown and it creates `site/llms.txt`
plus `site/llms-full.txt`.

## Manual Theme

The custom theme lives in `overrides/`, `docs/stylesheets/manual.css`, and
`docs/javascripts/manual.js`. It retains Zensical's search, palette switching,
instant navigation, Markdown rendering, and publication paths. The sidebar
and homepage directory both use the full `nav` in `zensical.toml`; adding a
section does not require a second menu definition. The `manual-directory`
comment in the homepage source is the insertion point for that directory.

The light and dark palettes share locally hosted Geist and Geist Mono fonts
(license in `docs/assets/fonts/`). The logo and pixel illustration are shared
with the homepage. Code examples remain static, with syntax highlighting and
source-only copying; the illustrative output on the index is not an execution
result. No playground or model calls are loaded by the theme.

After assembling `public-site/` using the command below, browser checks run with:

```sh
npm ci
npx playwright install chrome
npm run test:browser
```

The tests cover light/dark themes, mobile/tablet/desktop layouts, long reference
tables, the complete navigation, keyboard access, persistent expanded groups,
source/Markdown copying, and reading with JavaScript disabled. Screenshots and
failure traces are written to the ignored `test-results/` directory. The
deployment workflow runs these checks before publishing.

## Deploy

Pushes to `main` run `.github/workflows/docs.yml`. The workflow builds the docs
with the pinned dependency in `requirements-docs.txt`, checks out an exact
`kedi-lang/homepage` revision, and builds and browser-tests that site as well.
`scripts/assemble_site.py` combines the homepage at `/`, documentation at
`/docs/`, and compatibility routes into `public-site/`. Only this combined tree
is published to `gh-pages`. GitHub Pages keeps its existing custom domain and
branch settings; `/docs/` is a directory, not a second Pages configuration.

Old HTML documentation URLs redirect to `/docs/`, retaining query strings and
anchors with JavaScript and providing a meta-refresh/link fallback. GitHub Pages
serves these as static HTML, not server-side HTTP 301 redirects. The root page
is never redirected. Unknown URLs show a 404 with home/documentation links;
missing `/docs/` paths are not redirected recursively. Raw Markdown and LLM
indexes remain at their old addresses for non-browser consumers. Canonical URLs,
search, Markdown copy links, and sitemaps use the new documentation base.
The builder also scopes Zensical 0.0.51's language-alternate lookup to links with
`hreflang`: Markdown alternates must not be probed as separate sites with their
own sitemap. The patched JS bundle receives a new content hash for cache safety.

The workflow checks homepage `main` every 15 minutes and skips publication when
both source revisions match `deployment.json` on `gh-pages`. GitHub can delay
scheduled workflows; use a manual dispatch for an immediate homepage release.
No deployment token needs to be shared with the homepage repository. Social
cover images are excluded and rejected by the combined-site builder.

To check the publication locally, build the homepage first and run:

```sh
python scripts/build_docs.py
python -m unittest discover -s tests -v
python scripts/assemble_site.py --homepage ../website/dist \
  --homepage-sha "$(git -C ../website rev-parse HEAD)" \
  --docs-sha "$(git rev-parse HEAD)" --kedi-sha "$(git -C .. rev-parse HEAD)"
python -m http.server 8789 --directory public-site
```

Rollback: revert the homepage or documentation source commit and dispatch the
workflow again. `deployment.json` records the three source revisions; the domain
and Pages configuration do not need to change.

The repository secret `KEDI_REPOSITORY_TOKEN` must contain a fine-grained
GitHub token with read-only `Contents` access to the private
`kedi-lang/kedi` and `kedi-lang/tree-sitter-kedi` repositories. The workflow
checks out Kedi's `stable` branch, resolves its pinned `tree-sitter-kedi`
submodule revision, and installs both packages from those local checkouts.

The workflow can also be started manually from **Actions → Documentation → Run
workflow**.
