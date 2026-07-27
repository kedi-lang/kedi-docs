# Kedi Documentation

The Kedi documentation site is built with Zensical.

## Develop

```bash
uv tool run zensical serve
```

## Validate

```bash
uv tool run --from zensical==0.0.51 python scripts/build_docs.py
```

The generated static site is written to `site/`. The build also publishes each
source page as Markdown and creates `site/llms.txt` plus
`site/llms-full.txt`.

## Deploy

Pushes to `main` run `.github/workflows/docs.yml`. The workflow builds the site
with the pinned dependency in `requirements-docs.txt` and publishes `site/` to
the `gh-pages` branch. GitHub Pages serves that branch at
<https://kedi-lang.org/>.

The workflow can also be started manually from **Actions → Documentation → Run
workflow**.
