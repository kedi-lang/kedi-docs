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
and manual directory both use the full `nav` in `zensical.toml`; adding a
section does not require a second menu definition. The `manual-directory`
comment in the manual index is the insertion point for that directory.

The light and dark palettes share locally hosted Geist and Geist Mono fonts
(license in `docs/assets/fonts/`). Code examples remain static, with syntax highlighting and
source-only copying; the illustrative output on the index is not an execution
result. No playground or model calls are loaded by the theme.

After building `site/`, browser checks run with:

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

Pushes to `main` run `.github/workflows/docs.yml`. The workflow validates the
manual against Kedi's `stable` branch and its pinned tree-sitter revision,
builds and browser-tests the documentation, then publishes `site/` to
`https://docs.kedi-lang.org` through GitHub Pages. The homepage is built and
published independently from `kedi-lang/homepage`.

Canonical URLs, search, Markdown copy links, sitemaps, and LLM exports all use
the documentation domain root. The homepage owns compatibility redirects from
legacy `https://kedi-lang.org/docs/...` links and preserves their path, query,
and fragment.

To check the publication locally, run:

```sh
python scripts/build_docs.py
python -m unittest discover -s tests -v
npm run test:browser
```

Rollback: revert the documentation source commit and dispatch the workflow
again. Homepage releases do not rebuild or republish documentation.

The repository secret `KEDI_REPOSITORY_TOKEN` must contain a fine-grained
GitHub token with read-only `Contents` access to the private
`kedi-lang/kedi` and `kedi-lang/tree-sitter-kedi` repositories. The workflow
checks out Kedi's `stable` branch, resolves its pinned `tree-sitter-kedi`
submodule revision, and installs both packages from those local checkouts.

The workflow can also be started manually from **Actions → Documentation → Run
workflow**.
