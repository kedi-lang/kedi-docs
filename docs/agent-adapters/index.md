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

## Structured Output

`>> ... [field]` requires structured output. Pydantic, DSPy, LangChain, Claude,
and Codex support it. Generic ACP currently does not; use raw capture:

```kedi
>> Return a plain-text [answer: str] for the question.
```

Structured output is validated again at adapter boundaries where supported.

## Tools and MCP

Pydantic, LangChain, Claude, DSPy, and Codex accept Kedi tools. Pydantic,
LangChain, and Claude accept stdio/SSE/HTTP MCP. DSPy accepts stdio MCP only.
Codex currently rejects Kedi MCP declarations, although Codex itself retains
its harness-native tools. Generic ACP receives neither Kedi tools nor MCP
servers from this adapter.

## Subagent Support

Pydantic, LangChain, Claude, and Codex support foreground/background children.
DSPy supports blocking children only. Generic ACP is not subagent-capable.

## Choose a Backend

- Choose Pydantic for the broadest typed Python integration.
- Choose LangChain for LangChain models, middleware, and tool ecosystems.
- Choose DSPy for signatures, ReAct, and GEPA workflows.
- Choose Claude or Codex when a coding-agent harness and its native tools are
  part of the task.
- Choose ACP only when driving an existing stdio ACP agent as a text harness.

Consult the [capability matrix](../reference/capability-matrix.md) before
building a portable profile.
