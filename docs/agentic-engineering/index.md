# Agentic Engineering

Kedi treats model execution as scoped agent configuration rather than a global
string. A scope can select a framework or harness, model, reasoning effort,
instructions, settings, tools, MCP servers, skills, approvals, and child agents.

## Framework Adapters and Agent Harnesses

Framework adapters embed Kedi's prompt and tool contracts in an agent framework:

- `pydantic`
- `dspy`
- `langchain`

Agent harnesses drive a complete external coding/agent runtime:

- `claude`
- `codex`
- `acp`

Select the first group with `> adapter:` and the second with `> agent:`. These
are mutually exclusive backend kinds, not interchangeable aliases.

## Active Agent State

Directives update immutable agent state for following calls in the lexical
scope:

```kedi
> adapter: pydantic
> model: groq:qwen/qwen3-32b
> effort: low
> system: Use tools only when they improve factual accuracy.
```

Top-level state is captured by following procedures. A procedure-body override
applies only to later calls in that invocation. When the scope exits, Kedi
restores the previous state.

## Profiles

Profiles name reusable state:

```kedi
> profile: reviewer:
    > adapter: pydantic
    > model: groq:qwen/qwen3-32b
    > system: Review evidence before making a claim.

> use: reviewer
```

Profiles can be exported, imported, merged with later directives, and exposed
as direct child subagents.

## Capability Surfaces

- Procedures become typed tools through `> use:`.
- `> mcp:` attaches external MCP tools.
- `> skills:` exposes scoped registry, project, and user skill discovery.
- `> approval:` controls risky tool calls.
- `> subagent:` adds bounded delegation tools to a profile.
- semantic stream events expose completed commentary and final messages to
  terminals, UIs, and orchestration code without changing adapter results.

Each surface is capability-checked against the selected backend. Unsupported
structured output is an execution error. Tools and MCP currently produce
forward-compatible editor warnings where an adapter may gain support later.

## Design Rule

Define the narrowest agent surface that can perform the task. Give profiles
specific instructions, only required tools, bounded child agents, and the least
permissive approval and sandbox settings. A broader model is not a substitute
for a clear contract.

Read this section in order:

1. [Backend Selection](backend-selection.md)
2. [Models and Reasoning](models-and-reasoning.md)
3. [Instructions and Settings](instructions-and-settings.md)
4. [Profiles](profiles.md)
5. [Tools and `> use:`](tools-and-use.md)
6. [Approvals](approvals.md)
7. [MCP Servers](mcp.md)
8. [Skills](skills.md)
9. [Subagents](subagents.md)
10. [Stream Events](stream-events.md)
11. [Scoping and Capabilities](scoping-and-capabilities.md)
