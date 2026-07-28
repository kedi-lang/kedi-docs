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

## Deploy

Pushes to `main` run `.github/workflows/docs.yml`. The workflow builds the site
with the pinned dependency in `requirements-docs.txt` and publishes `site/` to
the `gh-pages` branch. GitHub Pages serves that branch at
<https://kedi-lang.org/>.

The repository secret `KEDI_REPOSITORY_TOKEN` must contain a fine-grained
GitHub token with read-only `Contents` access to the private
`kedi-lang/kedi` repository. The workflow checks out its `stable` branch and
installs Kedi from that local checkout.

The workflow can also be started manually from **Actions → Documentation → Run
workflow**.
