# VS Code

## Install the Extension

Install **Kedi-Lang** (`dyigitpolat.kedi-vscode`) and the Microsoft Python
extension. VS Code 1.85 or newer is required.

## File Recognition

The extension registers `.kedi` as language ID `kedi` with aliases `Kedi` and
`kedi`.

## Syntax Highlighting

Semantic tokens from `kedi-lsp` highlight Kedi structure. Embedded fenced and
backtick Python regions are forwarded to Python tooling. Kedi query docstrings
inside `.py` files can also receive experimental semantic tokens.

## Language Server Setup

Resolution prefers:

1. workspace `.venv/bin/kedi-lsp` (or Windows equivalent);
2. interpreter selected by the Python extension;
3. explicit `kedi.lsp.pythonPath`;
4. `kedi.lsp.serverCommand` on `PATH`.

Use **Kedi: Restart Language Server** after changing environments.

## Completion and Hover

Kedi completion, hover, definitions, references, rename, outline, signature
help, inlay hints, formatting, and diagnostics come from `kedi-lsp`. Embedded
Python hover/definition/references come from Pylance/Pyright forwarding.

## Diagnostics

Open **Output → Kedi Language Server** for client/server failures. Set
`kedi.lsp.trace.server` to `messages` or `verbose` for protocol tracing.

## Extension Settings

```json
{
  "kedi.lsp.usePythonExtension": true,
  "kedi.embeddedPython.enable": true,
  "kedi.embeddedKediInPython.enable": true,
  "kedi.embeddedKediInPython.experimentalSemanticTokens": true
}
```

Set `kedi.lsp.usePythonExtension` false and `kedi.lsp.pythonPath` explicitly
when the selected environment cannot import Kedi.

## Troubleshooting

Confirm the selected interpreter runs `python -m kedi.lsp.server`. Reload the
window after installing Kedi into a new environment. Pylance shadow documents
are stored in extension storage, outside the workspace, and may be deleted;
the extension regenerates them.

