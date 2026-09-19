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

The core distribution includes the Pydantic AI adapter. Other adapters,
provider SDKs, and runtime surfaces are installed only when selected:

```bash
uv add "kedi[claude]"
uv add "kedi[codex-model]"
uv add "kedi[dspy]"
uv add "kedi[groq]"
uv add "kedi[langchain]"
uv add "kedi[langchain-aws]"
uv add "kedi[playground]"
```

`dspy` installs the DSPy adapter and optimization instrumentation. `langchain`
installs the LangChain adapter's common OpenAI, OpenRouter, and MCP
integrations; add `langchain-aws` only for Bedrock. `groq` installs the provider
SDK used by Groq-backed Pydantic AI models. `claude` and `codex-model` install
their corresponding SDK bridges, while `playground` adds browser server
dependencies. Codex, Claude, and ACP harnesses may also require an executable,
authentication, or explicit command configuration.

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
