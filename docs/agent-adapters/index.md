# Agent Adapters

Adapters translate Kedi's uniform prompt contract into a model framework or an
agent harness. Selection is explicit because those backends have materially
different capabilities.

## Agent Framework Adapters

Use `> adapter:` or Python `adapter=`:

| Shortname | Backend |
| --- | --- |
| `pydantic` | Pydantic AI |
| `dspy` | DSPy |
| `langchain` | LangChain agents |

Framework adapters accept Kedi-defined tools and structured output directly.

## Agent Harness Adapters

Use `> agent:` or Python `agent=`:

| Shortname | Backend |
| --- | --- |
| `claude` | Claude Agent SDK |
| `codex` | Codex App Server |
| `acp` | Generic stdio ACP agent |

Harnesses are full agent processes with their own tools, sessions, sandboxing,
and permission models. Kedi maps what each protocol actually supports.

## Shared Adapter Contract

Every adapter provides async and sync paths for:

- `produce(...)`: a template plus structured output schema;
- `invoke(...)`: a raw prompt returning text.

It also declares `kind`, `shortname`, and `AdapterCapabilities`. Optional
protocols add profile overrides, tool registration, approvals, and subagents.

## Capability Negotiation

The [capability matrix](../reference/capability-matrix.md) is generated from
the built-in adapters' declared metadata and is the canonical support table.
Kedi checks required capabilities rather than silently emulating a missing
surface. For example, `>> ... [field]` requires structured output; a text-only
adapter must use raw capture instead:

```kedi
[answer] << Answer the question in plain text.
```

Transport modes, provider restrictions, native harness tools, and lifecycle
details are adapter-specific and remain documented on each adapter page.

## Choose a Backend

- Choose Pydantic for the broadest typed Python integration.
- Choose LangChain for LangChain models, middleware, and tool ecosystems.
- Choose DSPy for signatures, ReAct, and GEPA workflows.
- Choose Claude or Codex when a coding-agent harness and its native tools are
  part of the task.
- Choose ACP only when driving an existing stdio ACP agent as a text harness.
