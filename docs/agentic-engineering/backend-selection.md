# Backend Selection

Kedi separates framework adapters from agent harnesses because they expose
different execution and capability contracts.

## Frameworks with `> adapter:`

```kedi
> adapter: pydantic
> model: groq:qwen/qwen3-32b

>> Summary of <document>: [summary: str].
```

Built-in framework shortnames are `pydantic`, `dspy`, and `langchain`.
Frameworks are appropriate when Kedi owns structured prompting and registers
typed tools through the framework's model interface.

## Harnesses with `> agent:`

```kedi
> agent: codex
> model: gpt-5
> settings:
    cwd: .
    sandbox: workspace-write

>> Inspect the repository and return [answer: str] explaining the failing test.
= <answer>
```

Built-in harness shortnames are `claude`, `codex`, and `acp`. Harnesses are
appropriate when the underlying agent owns its tool loop, repository context,
or protocol session.

## Literal and Dynamic Selection

Literal names are validated by the parser/LSP and runtime:

```kedi
> adapter: langchain
```

Use a backtick expression only when selection is genuinely dynamic:

````kedi
```
selected_backend = "pydantic"
```

> adapter: `selected_backend`
````

Dynamic selection postpones validation and reduces static diagnostics. Prefer a
literal or profile in production source.

## ACP Commands

Select ACP using an explicit command:

```kedi
> agent:
    acp: `["uv", "run", "my-acp-agent"]`
```

The command can be plain text or a Python expression evaluating to a string or
sequence of strings. The structured form binds the command to the `acp` harness.

This short form reads the command from process configuration:

```kedi
> agent: acp
```

When no command is embedded, Kedi uses `KEDI_ACP_AGENT_COMMAND`. The CLI
`--acp-command` option sets the same environment value for that process. A
missing command is an initialization error, not a no-op.

## CLI and Environment Defaults

If source does not select a backend, Python configuration or CLI defaults can
provide one. The Python API loads `.env` and recognizes:

| Variable | Meaning |
| --- | --- |
| `KEDI_ADAPTER` | Framework adapter shortname |
| `KEDI_AGENT` | Harness shortname |
| `KEDI_ADAPTER_MODEL` | Model for either selected backend |
| `KEDI_ACP_AGENT_COMMAND` | Default ACP stdio command |

`KEDI_ADAPTER` and `KEDI_AGENT` are mutually exclusive.

## Selection Precedence

For a model call, selection priority is:

1. a direct directive in the current lexical scope;
2. a profile applied in that scope;
3. Python/CLI default agent profile;
4. environment-based default selection.

Nested scopes may choose another backend and restore the outer selection when
they exit.

## Invalid Combinations

A single lexical scope cannot mix `> adapter:` and `> agent:`. Kedi also rejects
a framework name in `> agent:`, a harness name in `> adapter:`, conflicting
environment defaults, a dynamic value with the wrong type, and an adapter
instance whose declared kind does not match the selected API.

Switch in a nested procedure or define separate profiles instead of creating an
ambiguous mixed scope.
