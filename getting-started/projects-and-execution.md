# Projects and Execution

## Single-File Programs

A `.kedi` file can contain top-level values, types, procedures, profiles, tests,
evals, and the final executable statements. Single-file programs are a good fit
when the public surface is small and all prompts share one lifecycle.

## Multi-File Projects

Split reusable procedures, types, values, and profiles into modules. Imports are
relative to the importing file first, then fall back to bundled modules and the
local Kedi package registry.

```text
project/
├── main.kedi
├── profiles.kedi
└── services/
    └── classify.kedi
```

```kedi
> import: services/classify:
  classify_ticket
```

Only explicitly exported names are visible to importers.

## Entry Points

The source passed to `kedi` is the root program:

```bash
kedi main.kedi
```

Modules are initialized as the root program is compiled. A package entry point
is the `main.kedi` inside the source directory declared by `package.kedi`.

## Source Loading Order

Kedi loads the root source, imported modules, optional generated
`*.cache.kedi` implementations, and optimized prompt artifacts through a source
map. Imports are initialized at most once per root compilation, including
diamond import graphs.

Bindings still obey source order. A later declaration or import can replace a
name introduced earlier, even when the binding kind changes.

## Runtime Environment

The runtime environment contains Kedi values, procedure frames, prelude names,
registered Python tools and types, configured environment values, and the
reserved CLI argument object. Python blocks see existing Kedi variables as
globals.

Do not use the runtime environment as a general mutable global store. Prefer
procedure parameters and returns for explicit dataflow; reserve prelude and
configured `env` for shared dependencies or types.

## Backend and Model Selection

The CLI defaults to the Pydantic adapter and a configured default model. Override
them explicitly:

```bash
kedi main.kedi \
  --adapter pydantic \
  --adapter-model groq:qwen/qwen3-32b
```

Source directives and profiles can override CLI defaults in lexical scope. A
single scope cannot select both a framework adapter and an agent harness.

## Generated and Cached Artifacts

Depending on the features used, Kedi may create:

- `source.cache.kedi` for AI-generated procedure implementations;
- optimized prompt JSON and score artifacts;
- optimizer checkpoint directories;
- in-memory parse and response cache entries;
- an optional owner-only subagent state file configured by Python callers.

Generated artifacts are implementation inputs, not source-of-truth replacements
for the original procedure signatures, tests, eval datasets, or prompt spans.
