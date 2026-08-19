# Tooling

Kedi ships one CLI, an LSP server, editor integrations, package commands, and
low-level browser/playground bridges.

## Command-Line Interface

```bash
kedi program.kedi
kedi -c '= hello'
kedi parse program.kedi
kedi program.kedi --test
kedi program.kedi --eval
```

The CLI loads `.env`, renders source-aware parse/execution errors, and exits
nonzero on failure.

## Language Server

`kedi-lsp` provides diagnostics, semantic tokens, completion, hover,
definition/references, rename, formatting, symbols, signature help, and inlay
hints. It also understands Kedi query docstrings in Python.

## Editor Extensions

VS Code and Zed extensions recognize `.kedi`, package highlighting/snippets,
start `kedi-lsp`, and forward embedded Python regions to Python tooling.

## Browser Execution

`PlaygroundExecutor` moves embedded Python execution through a synchronous
worker bridge. `PyodideExecutor` is its browser-oriented alias/subclass.
`WebGPUAdapter` can route model requests to a browser-hosted model bridge.

## Package Tooling

`kedi install` installs a local `package.kedi`. `kedi add` installs a named
registry package or an explicit credential-free GitHub source.

## Validation Workflows

Use parse-only checks first, deterministic tests second, evals for measured
quality, and optimization only after metrics are trustworthy.

