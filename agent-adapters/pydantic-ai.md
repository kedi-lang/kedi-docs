# Pydantic AI

## Installation

Pydantic AI is a core Kedi dependency:

```bash
uv add kedi
```

Provider credentials and optional provider packages follow Pydantic AI's model
requirements.

## Model Names

Select the adapter and a Pydantic-style or LiteLLM-style model:

```kedi
> adapter: pydantic
> model: openai:gpt-4o-mini
```

Strings using `vendor/model` are normalized to Pydantic's model naming form.
An existing Pydantic AI `Model` may be passed to `PydanticAdapter` directly.

## Model Settings

Supported settings are `max_tokens`, `temperature`, `top_p`, `timeout`,
`parallel_tool_calls`, `tool_choice`, `seed`, `presence_penalty`,
`frequency_penalty`, `logit_bias`, `stop_sequences`, `extra_headers`,
`thinking`, `service_tier`, and `extra_body`.

```kedi
> settings:
    temperature: 0.2
    max_tokens: 2048
    parallel_tool_calls: true
```

`max` reasoning effort maps to Pydantic AI's `xhigh`.

## Structured Outputs

Kedi builds a dynamic Pydantic model from each output field:

```kedi
~Finding(severity: str, message: str)

>> Inspect <code> and return [findings: list[Finding]].
```

Field descriptions from `Annotated[T, "description"]` are preserved. Pydantic
AI produces and validates the result before Kedi publishes captured fields.

## Python and Procedure Tools

Python `@kedi.tool` functions and Kedi procedures selected by `> use:` become
native Pydantic AI tools for one lexical run. Registration is context-local,
so tools do not leak between concurrent calls.

## MCP Toolsets

All Kedi MCP transports are mapped to Pydantic AI toolsets:

- stdio with command, args, and env;
- SSE with URL and headers;
- streamable HTTP with URL and headers.

Application and MCP toolsets are approval-required before execution.

## Approval Integration

Pydantic's deferred-tool capability is used to resolve Kedi approval requests.
Read-only calls pass automatically; mutating and sensitive calls flow through
the active static/dynamic policy. Edited arguments are supplied as Pydantic
tool overrides after validation.

Nested subagent policies form a ceiling: a child cannot widen a parent's
restriction.

## Foreground and Background Subagents

Pydantic supports both modes and native conversation resume. Usage limits are
translated to Pydantic AI request, tool-call, and token limits. Child tool,
MCP, skills, model, and instruction scopes remain isolated.

## Usage and Retry Behavior

Pydantic run usage is reported to Kedi's subagent budget observer. The adapter
tracks requests, tool calls, and input/output/total tokens.

`subagent_failure_policy="fail_closed"` is the default. `"recover"` exposes a
sanitized child error to the parent instead of failing the parent run.

