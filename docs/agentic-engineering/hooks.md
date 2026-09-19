# Agent Lifecycle Hooks

Hooks let application code observe or govern agent boundaries without moving
that policy into model instructions. They are synchronous with the boundary:
the run waits for each handler before it continues.

## Events

| Event | Boundary | May edit | May deny |
| --- | --- | :---: | :---: |
| `user_prompt_submit` | Immediately before the prompt enters the adapter | yes | yes |
| `pre_tool_use` | After argument canonicalization and before approval/execution | yes | yes |
| `post_tool_use` | After one successful tool execution | no | no |
| `post_tool_use_failure` | After one failed tool execution | no | no |

A denied prompt is never transported to the model. A denied tool call does not
execute and does not produce a post-failure event. Denial is policy behavior,
not a tool execution failure.

Each executed tool call emits `pre_tool_use` and exactly one terminal event:
`post_tool_use` on success or `post_tool_use_failure` on failure.

## Kedi Configuration

Handlers are ordinary Python callables available to the Kedi environment:

````kedi
```
from pathlib import Path

from kedi import PreToolUseDecision, UserPromptSubmitDecision

audit_events = []

def redact_prompt(event):
    return UserPromptSubmitDecision.edit(
        event.content.replace("customer@example.com", "[email]")
    )

def constrain_report_path(event):
    if event.tool_name != "write_report":
        return None
    filename = Path(event.arguments["path"]).name
    return PreToolUseDecision.edit(
        {**event.arguments, "path": str(Path("reports") / filename)}
    )

def observe_tool(event):
    audit_events.append((event.event, event.tool_name, event.tool_call_id))
```

> hooks:
    user_prompt_submit: `redact_prompt`
    pre_tool_use: `constrain_report_path`
    post_tool_use: `observe_tool`
    post_tool_use_failure: `observe_tool`
````

A field may evaluate to one callable or a sequence of callables. Use the short
form to control inherited lexical/profile handlers:

```kedi
> hooks: disabled
```

`disabled` does not unregister handlers attached directly to an adapter
instance. The expanded form enables the handlers it declares.

The directive is valid at top level, inside a procedure, and inside a profile.
Top-level hooks are captured by following procedures according to normal source
order.

## Decisions

Prompt handlers return `None` or `UserPromptSubmitDecision`:

```python
from kedi import UserPromptSubmitDecision

UserPromptSubmitDecision.continue_()
UserPromptSubmitDecision.edit("replacement prompt")
UserPromptSubmitDecision.deny("prompt violates application policy")
```

Pre-tool handlers return `None` or `PreToolUseDecision`:

```python
from kedi import PreToolUseDecision

PreToolUseDecision.continue_()
PreToolUseDecision.edit({"path": "reports/output.md"})
PreToolUseDecision.deny("writes are disabled in this run")
```

`None` means continue. Only `edit` may carry replacement content or arguments,
and only `deny` may carry a denial reason. Invalid combinations fail before the
boundary continues. Post-success and post-failure handlers are observers and
must return `None`.

Edited tool arguments are revalidated before approval and execution. A handler
cannot bypass a tool signature, argument validator, risk resolver, secret-file
classification, or approval policy by editing the request.

## Event Data

Every event contains:

| Field | Meaning |
| --- | --- |
| `event` | Stable event name |
| `run_id` | Identity of the current agent run |
| `sequence` | Monotonic event sequence within that run |
| `adapter_shortname` | Active adapter |
| `parent_run_id` | Parent run for delegated work, when present |
| `agent_name` | Active agent identity, when present |
| `profile_name` | Active profile identity, when present |

Tool events additionally contain `tool_call_id`, logical `tool_name`, optional
`native_tool_name`, `origin`, immutable `arguments`, optional `description`, and
immutable `metadata`. `origin` is one of `kedi`, `mcp`, `adapter_native`, or
`provider_builtin`.

`PostToolUseEvent.result` contains the native successful result.
`PostToolUseFailureEvent` contains `error_type`, `error_message`, the original
exception when the adapter exposes it, `duration_seconds` when the execution
boundary can measure it, and an `interrupted` flag for cancellation or process
interruption. It is emitted only after tool execution starts; hook and approval
denials are not tool-execution failures. Payload values are available to the
handler but omitted from event representations and default telemetry.

## Ordering and Errors

Handlers execute serially in this order:

1. adapter constructor `hook_handler=`;
2. adapter event-specific handlers registered with `adapter.on(...)`;
3. lexical/profile handlers in merge and source order.

An edit becomes the input seen by the next handler. A denial short-circuits the
remaining chain. A raised exception becomes `HookExecutionError`; cancellation
propagates and drains the active handler. Sync boundaries accept sync handlers.
Use an adapter's async API when a handler itself is async.

Hook dispatch is suspended while a handler runs. Agent work started by a hook
does not recursively invoke the same active chain.

## Python API

Register one handler for one or several events:

```python
import kedi

audit_events = []

@kedi.on(("post_tool_use", "post_tool_use_failure"))
def audit_terminal_event(event):
    audit_events.append((event.run_id, event.tool_call_id, event.event))
```

`kedi.configure()`, `kedi.context()`, `@kedi.query`, and `@kedi.bind` accept a
`hooks=` mapping. Adapter instances expose `@adapter.on(...)`, and supported
adapter constructors accept one catch-all `hook_handler=` callable.

## Profiles and Subagents

Profile-local hooks belong to that profile. A child profile runs its own local
handlers. Direct top-level/procedure hook directives and Python API
registrations are enforcement policy and propagate to descendants. A parent's
profile-local handler is not copied into an unrelated child profile.

Child events use the child `run_id` and identify the child agent/profile.
`parent_run_id` links to a parent when a parent run context is available; it
may be `None` without that context. Do not use its absence alone to classify
a tool as a top-level call. Stream observation provides run lifecycle context
for UIs that need a complete parent/child activity tree.

## Persistence

Interactive session dumps never pickle hook handlers. Kedi records only an
importable module and qualified name. A top-level function from an importable
module can be restored; lambdas, local functions, closures, bound methods, and
`__main__` handlers make the dump fail explicitly. Nothing is silently omitted.

## Adapter Support

| Adapter | Prompt | Pre tool | Post tool | Tool failure | Tool origins |
| --- | :---: | :---: | :---: | :---: | --- |
| Pydantic AI | yes | yes | yes | yes | Kedi, MCP, adapter-native |
| LangChain | yes | yes | yes | yes | Kedi, MCP, adapter-native |
| Claude Agent SDK | yes | yes | yes | yes | Kedi, MCP, provider built-ins |
| Codex App Server | yes | yes | yes | yes | Kedi projected tools |
| WebGPU | yes | yes | yes | yes | Kedi, MCP |
| ACP | yes | no | no | no | none |
| DSPy | no | no | no | no | none |

Kedi validates support per event. A configuration that requests an unsupported
event fails before model transport and is reported by the LSP. Dynamic adapter
selection defers that check to runtime.

## Security and Telemetry

Hooks execute trusted Python and can inspect prompt, argument, result, and error
payloads. Keep audit sinks bounded and redact before forwarding data to another
system. A post hook cannot undo an effect that already succeeded.

The in-memory lists above are small examples, not durable audit logs. A failing
post hook may make the run fail after the tool has already performed its effect;
re-running that tool can duplicate the effect. Keep policy in pre-hooks and
approval, and use [Stream Events](stream-events.md) for non-blocking UI progress.

Kedi emits one telemetry span for a nonempty hook chain and records event name,
handler count, adapter, origin, outcome, edit/deny status, duration, failures,
and timeouts. Prompt text, arguments, tool result, error message, metadata, and
handler return values are not captured by default.
