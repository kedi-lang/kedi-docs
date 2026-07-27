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

