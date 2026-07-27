# Installation

## Supported Python Versions

Kedi requires Python 3.10 or newer. The package metadata currently supports
Python 3.10 through 3.14.

## Install with uv

For an application project:

```bash
uv add kedi
```

Run Kedi inside the project environment:

```bash
uv run kedi --help
uv run kedi-lsp
```

For a temporary CLI invocation without adding a project dependency, use
`uvx kedi`. Pin a version in automation so CI and local behavior do not drift.

## Install with pip

Kedi can also be installed into an activated virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install kedi
```

Use `uv` for the repository's contributor workflow. The `pip` path is intended
for consumers whose environments are managed by another tool.

## Optional Backend Dependencies

The core distribution includes the Pydantic AI, DSPy, and LangChain adapter
dependencies. Some harness or runtime surfaces need additional packages:

```bash
uv add "kedi[claude]"
uv add "kedi[playground]"
```

The `claude` extra installs the Claude Agent SDK. The `playground` extra adds
the browser/playground server dependencies. Codex and ACP connect to external
agent processes and may require their own executable, authentication, or
command configuration.

## Verify the CLI

```bash
kedi --help
kedi -p -c "= ready"
```

The second command parses inline Kedi without contacting a model. If
`kedi-lsp` is on `PATH`, editor integrations can start the language server.

## Upgrade Kedi

With uv:

```bash
uv lock --upgrade-package kedi
uv sync
```

Review release notes before upgrading a production workflow. Kedi programs may
also depend on provider SDK behavior, agent harness versions, and installed
Kedi packages.
