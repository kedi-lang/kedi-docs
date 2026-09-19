# Zed

## Install the Extension

Open **Zed → Extensions**, search for **Kedi**, and install it. For local
development choose **Install Dev Extension** and select the `kedi-zed`
directory, not the grammar repository.

## File Recognition

The bundled language config registers `.kedi` as **Kedi**, with `#` line
comments, `###` block comments, bracket pairs, and Kedi indentation behavior.

## Tree-sitter Grammar

The extension pins `tree-sitter-kedi` to the revision in `extension.toml`.
Registry installs build/use the packaged extension. Local dev installs require
Rust via `rustup` and the declared `wasm32-wasip1` target.

## Syntax Highlighting

Tree-sitter queries provide highlights, outlines, brackets, indentation, and
Python injection. Recommended:

```json
{
  "languages": {
    "Kedi": {
      "formatter": "language_server",
      "format_on_save": "on",
      "semantic_tokens": "combined"
    }
  }
}
```

## Language Server Setup

Resolution order is configured `lsp.kedi-lsp.binary.path`, workspace `.venv`/
`venv` executable, `kedi-lsp` on `PATH`, then `python -m kedi.lsp.server`.

```json
{
  "lsp": {
    "kedi-lsp": {
      "binary": {
        "path": "/path/to/python",
        "arguments": ["-m", "kedi.lsp.server"]
      }
    }
  }
}
```

The extension also starts an embedded-Python proxy and auto-installs Pyright
through Zed's npm support. Python query docstrings use a separate virtualizer
server.

## Tasks and Commands

Kedi execution remains a normal terminal/task command such as
`kedi program.kedi`; the extension focuses on language services and snippets.

## Extension Updates

Registry updates follow the published extension version. A dev extension uses
the selected local checkout and may leave ignored WASM/grammar build artifacts.

## Troubleshooting

If **Kedi** is absent from language selection, verify the extension installed
and `languages/kedi/config.toml` is present. If files are recognized but LSP
features fail, configure a Python environment that can import `kedi`.

The manifest requests broad `process:exec` because it may launch a configured
binary, workspace executable, Python fallback, Node, and Pyright proxy. Users
may narrow Zed's granted capability locally.

