# Run and Parse Commands

## Run a Source File

```bash
kedi program.kedi
```

Kedi loads imports, optimized prompts, generates missing `> auto:` procedures,
compiles, and runs the top-level program.

## Run Inline Source

```bash
kedi -c '= Hello from Kedi'
```

Inline source supports direct run or `--parse`, but not `--test`, `--eval`, or
`--optimize`, because those workflows need file-backed artifacts.

## Pass Program Arguments

Unknown `--name value` options after the source become `args.name`:

```bash
kedi greet.kedi --name Ada --verbose
```

Values are strings; flags are `True`; missing names read as `None`. Hyphens
normalize to underscores. First occurrence wins when an option repeats.
Non-option positional extras are ignored.

## Parse Without Execution

All are supported:

```bash
kedi -p program.kedi
kedi program.kedi --parse
kedi -p -c '@greet(name: str):'
```

A successful parse prints `Parsed successfully.` and performs no model call or
program execution.

## `kedi parse`

```bash
kedi parse program.kedi
```

This is an alternate parse-only form. It requires one source path.

## Select an Adapter or Agent

The CLI option is historically named `--adapter` and accepts all built-ins:

```bash
kedi program.kedi --adapter pydantic
kedi program.kedi --adapter codex
```

Inside source, use the semantically strict `> adapter:` for Pydantic/DSPy/
LangChain and `> agent:` for Claude/Codex/ACP.

## Select a Model

```bash
kedi program.kedi \
  --adapter pydantic \
  --adapter-model openai:gpt-4o-mini
```

Environment equivalents are `KEDI_ADAPTER` and `KEDI_ADAPTER_MODEL`. Lexical
source directives and profiles can override CLI defaults.

## ACP Commands

ACP commands must be embedded explicitly in source using multiline `> agent:`
syntax, or supplied through `ACPAdapter(command=...)` in Python. The CLI does
not accept a global ACP command because one process-level value cannot describe
multiple ACP profiles.

## Exit Codes and Rendered Errors

Successful runs return zero. Source read, parse, execution, validation,
codegen, optimizer, and package errors return nonzero. Parse diagnostics include
source location and excerpts; execution errors include hydrated Kedi/Python
trace context when available. The frame model and embedded-Python mapping are
documented in [Errors, Frames, and Tracebacks](../runtime/errors-and-debugging.md).
