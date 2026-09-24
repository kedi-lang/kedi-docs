# Language Server

## Start `kedi-lsp`

```bash
kedi-lsp
```

Equivalent fallback:

```bash
python -m kedi.lsp.server
```

The server uses stdio and is normally started by an editor extension.

Running it in a terminal waits for LSP protocol messages; it is not an
interactive Kedi prompt. Use `kedi --idle` for that. The selected Python
environment must have Kedi installed, independently of the editor extension.

## Parsing and Diagnostics

Documents are reparsed on open/change; diagnostics clear on close. Reports
cover grammar, duplicate declarations/import entries, unresolved imports,
invalid profile graphs/settings/types, and semantic directive errors.

## Type Diagnostics

The LSP resolves built-in, custom, imported, nested, generic, union, and
`Annotated` type expressions. It reports invalid type positions and schema
formats that the selected adapter cannot carry.

## Adapter Capability Diagnostics

Selection state is tracked lexically. Unsupported structured output is an
error. Unsupported tool/MCP/profile capabilities are reported at the relevant
directive. Diagnostics use adapter metadata, not a hard-coded backend guess.
An active `> history:` processor declaration, including an external callable,
receives a non-blocking prefix-cache warning at its declaration. Adding
`processor_condition` does not remove that warning. A statically disabled
``processor: `None` `` does not warn, and the warning is not repeated at every
model call. The LSP also completes and explains `processor_condition`.

## Completion

Completion covers directives, procedures, values, types, profiles, imports,
settings, tools, and scoped names. Suggestions respect source position and
imported module surfaces.

## Hover Documentation

Hover shows procedure/type/profile signatures, fields, docstrings, variables,
directives, and imported symbols. Procedure/profile leading block comments are
surfaced as documentation.

## Definition and References

Go-to-definition and references work across declarations, calls,
substitutions, types, profiles, and module imports. Rename is available for
supported Kedi symbols and produces a workspace edit.

## Module Surfaces

The server reads exported sibling/bundled/installed modules, honors selective
imports and `> export: *`, and does not expose private non-exported names.

## Python Virtual Documents

Embedded Python fences/backticks are transformed into scope-aware virtual
Python documents with Kedi procedures, values, and types represented as Python.
Editor proxies use these maps for Python hover/definition/references.

Python files with query docstrings whose first cleaned line is `kedi` receive
Kedi diagnostics, hover, definition, references, and semantic tokens inside
the docstring.

The server also provides semantic tokens, document symbols, formatting,
signature help on `(` and `,`, and inlay hints.

## What Diagnostics Do Not Prove

Editor validation is not execution. A clean document does not prove a provider
is authenticated, tools are available, a model claim is true, or a program's
side effects are safe. Use deterministic tests and model-backed evals for their
respective contracts. Python virtual documents are an analysis projection,
not a second copy of the running program or a sandbox.
