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

## CodeMode

Use `> codemode: enabled` to replace application tool schemas with Kedi's
`search_tools`, `get_tool_schema`, and `execute_code` controls:

```kedi
> adapter: pydantic
> codemode: enabled
```

The outer capability wraps constructor, caller, scoped Kedi, and local MCP
toolsets together. Nested calls retain validation, approval, required-tool,
telemetry, cancellation, and artifact behavior. Provider-native MCP and
external deferred approval are rejected while CodeMode is active. See
[CodeMode](../agentic-engineering/codemode.md) for the complete contract.

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

## Native Tool Artifacts

When artifacts are enabled, constructor tools, caller-provided tools, and local
MCP toolsets cross Kedi's artifact-admission boundary before Pydantic AI commits
their successful results to message history. Large values therefore become the
same compact `ArtifactRef` objects used by Kedi-defined tools.

Admission preserves Pydantic AI's native `tool_call_id`, validation, retries,
approval flow, and streaming result handling. Failed tool results remain native
errors, and a tool already wrapped by Kedi is not admitted twice. The exact
returned ref ID must be used with `read_artifact`; IDs must not be predicted.

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

Unless `retries` is supplied explicitly, `PydanticAdapter` allows three
bounded retries for correctable tool-call failures. The output-validation
retry budget remains Pydantic AI's default. An explicit integer or
`AgentRetries` value overrides Kedi's tool retry default.

`subagent_failure_policy="fail_closed"` is the default. `"recover"` exposes a
sanitized child error to the parent instead of failing the parent run.

## Codex Responses Connections

`codex_responses_model()` builds a Codex-authenticated Pydantic model. HTTP is
the default. The optional WebSocket path requires a helper build containing
the `websocket` extra; the published `codex-auth-helper==1.6.1` alone does not
include these local transport additions.

```python
from kedi import codex_responses_model
from kedi.agent_adapter import PydanticAdapter

model = codex_responses_model(
    "gpt-5.6-luna",
    adapter="pydantic",
    connection="websocket",
    fallback="error",
)
adapter = PydanticAdapter(model)

async def review():
    async with adapter.responses_session():
        first = await adapter.run("The current release is amber. Acknowledge it.")
        second = await adapter.run(
            "Which release is current?",
            message_history=first.all_messages(),
        )
    return second.output
```

An ordinary adapter run keeps its connection across model/tool turns. The
explicit session above also retains it across sequential adapter calls.
It owns the connection, not the history: supply native message history as
shown or use Kedi's normal stateful-history surface. Concurrent child tasks
remain isolated, and exit, errors, and cancellation clean up the connection.

Updated helper builds scope a separate routing turn to every adapter run. HTTP
and WebSocket echo the first server-provided `x-codex-turn-state` within its tool
loop, but discard it before the next run, even on a shared connection. Kedi does
not put this opaque value in history or transport metrics. Prompt-cache keys and
native history remain unchanged; provider cache hits are not guaranteed.

Auth recovery reloads same-account credentials after an explicit 401, then allows
one refresh if necessary. Account changes require a new client; permanent auth
failures and exhausted 401s do not trigger HTTP fallback. Same-file refresh locking
is in-process only. Older helper builds work without the new turn-state feature.

Append-only requests can transmit only their new suffix. History edits or
changed request settings reset continuation. If the socket is already known
to be closed before the next request, a new connection receives full history.
Changing handshake headers also replaces the connection.

With helper 1.8.0, non-streaming model requests recover
transient WebSocket send/receive failures by discarding incomplete output and
rebuilding full history on a new connection. Completed local tools are not rerun
by recovery. The client `max_retries` controls reconnects (default two), with
bounded backoff. `fallback="http"` permits HTTP after retries are exhausted, as
well as initial-handshake fallback. The model can still choose another tool
call, and lost provider work may incur unreported cost.

Raw client calls and exposed streams are not replayed; cancellation, permanent
auth/permission failures and provider-hosted tools also prevent response replay.
Install the pinned helper with `uv add 'kedi[codex-model]'`. Stream consumers can stop on
`response.completed` without discarding the completed response; stopping before
completion abandons it. The closing handshake has a 250 ms timeout, separate
from generation and tool execution.

Connection reuse can improve provider cache reads, but does not guarantee a
particular hit rate or lower latency. Cached input is part of total input,
not an additional token count.
