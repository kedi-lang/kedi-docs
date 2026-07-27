# Scoping and Capabilities

Agent state follows lexical source scope. Capability metadata determines whether
the selected adapter can honor the resulting contract.

## Lexical Agent State

```kedi
> adapter: pydantic
> model: default-model

@quick(text: str) -> str:
  > effort: low
  >> Summarize <text> as [summary: str].
  = <summary>
```

The effort override exists only inside `quick`; the outer adapter and model are
inherited. On return, the prior state is restored.

## Top-Level Capture

Top-level directives are captured by procedures declared after them. A later
top-level change does not retroactively change a previously declared procedure:

```kedi
> model: first-model

@first() -> str:
  >> Return a brief [answer: str].
  = <answer>

> model: second-model

@second() -> str:
  >> Return a brief [answer: str].
  = <answer>
```

This source-order rule also applies to tools, MCP, instructions, and profiles.

## Precedence

For each member, effective state is formed from:

1. CLI/Python default profile;
2. captured outer lexical state;
3. profiles applied in the current scope;
4. direct directives in the current scope.

Later direct declarations win for scalar fields. Collection members follow
their documented merge rules.

## Tool Frames

Tool registration is block-scoped. Inner registrations can shadow an outer tool
with the same name; leaving the block restores the previous binding. A procedure
tool receives its schema from that procedure's signature and docstring.

The same profile used in two scopes does not make mutable tool state global.
Each invocation materializes its active tool surface.

## Capability Metadata

Adapters advertise kind and capabilities such as:

- structured outputs;
- dynamic Kedi/Python tools;
- MCP servers;
- skills;
- subagent foreground or background execution;
- approval mediation.

The parser and LSP combine literal backend selection with this metadata. Dynamic
backend expressions defer some checks to runtime.

## Errors versus Warnings

Structured output is central to `>>` output capture. If the selected adapter
does not support it, the LSP reports an error and execution raises rather than
falling back to manual JSON prompting.

Tool and MCP support is currently reported as a capability warning for adapters
that cannot register them, allowing the same source to become valid when the
adapter gains support. Do not ignore the warning in production: the intended
capability is not active.

Subagent delegation and other required runtime seams fail explicitly when the
adapter lacks child execution. Kedi never pretends that delegated work ran.

## Adapter Switching

Nested scopes may switch to another framework or harness:

```kedi
> adapter: pydantic

@repository_task(task: str) -> str:
  > agent: codex
>> Complete this repository task: <task>. Return [answer: str].
  = <answer>
```

The nested scope is a new selection boundary. A single scope still cannot mix
both kinds.

## Production Guidance

Treat every capability warning as an unmet contract, test literal profiles with
their production adapter, and keep dynamic backend selection at application
boundaries. Static profiles give the LSP enough information to detect schema,
tool, and transport mismatches before a paid model call.
