# Backend Selection

Kedi separates framework adapters from agent harnesses because they expose
different execution and capability contracts.

## Frameworks with `> adapter:`

```kedi
> adapter: pydantic
> model: openai:gpt-5.6-luna

>> A summary of <document> is [summary: str].
```

Built-in framework shortnames are `pydantic`, `dspy`, and `langchain`.
Frameworks are appropriate when Kedi owns structured prompting and registers
typed tools through the framework's model interface.

## Harnesses with `> agent:`

```kedi
> agent: codex
> model: gpt-5.6-luna
> settings:
    cwd: .
    sandbox: workspace-write

>> The repository evidence suggests that [answer: str].
= <answer>
```

Built-in harness shortnames are `claude`, `codex`, `acp`, and `a2a`. Harnesses are
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

## Required Capabilities

Make nonnegotiable backend behavior explicit with `> requires:`:

```kedi
> adapter: langchain
> requires:
    structured_output
    tool_registration
    history_replay
```

Literal selections receive source-located LSP errors when the adapter cannot
meet the contract. Dynamic selections are checked at runtime before model I/O.
Requirements accumulate through lexical scope and applied profiles; an inner
scope cannot erase an outer obligation. See
[Scoping and Capabilities](scoping-and-capabilities.md#explicit-requirements).

## ACP Commands

Select ACP using an explicit command:

```kedi
> agent: acp:
    command: `["uv", "run", "my-acp-agent"]`
```

The command can be plain text or a Python expression evaluating to a string or
sequence of strings. The connection body binds the command to the `acp` harness.

ACP commands are always explicit. Use `> agent: acp:` syntax or construct
`ACPAdapter(command=...)` in Python. Plain `> agent: acp`, CLI command options,
and environment command fallbacks are unsupported.

## A2A Endpoints

Bind a remote A2A harness to its endpoint and credential reference:

```kedi
> agent: a2a:
    endpoint: https://agents.example.com
    auth:
        scheme: bearer
        token_env: RESEARCH_AGENT_TOKEN
```

The remote process owns its model and tool loop, so local `> model:`, `> effort:`,
`> settings:`, `> mcp:`, and tool registration are not forwarded. Generic peers
support raw text; Kedi-served peers can negotiate typed captures. See
[A2A Cloud Agents](../agent-adapters/a2a.md).

## CLI and Environment Defaults

If source does not select a backend, Python configuration or CLI defaults can
provide one. The Python API loads `.env` and recognizes:

| Variable | Meaning |
| --- | --- |
| `KEDI_ADAPTER` | Framework adapter shortname |
| `KEDI_AGENT` | Harness shortname |
| `KEDI_ADAPTER_MODEL` | Model for either selected backend |

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
