# Conversation History

History retains successful turns. It is not response memoization: a new prompt still invokes the model.

## Stateful Conversation History

Kedi model calls are stateless by default. Enable history in a lexical scope
when later template or raw-invoke blocks must receive complete successful turns
from earlier calls:

```kedi
> history: enabled

>> Remember [project_name].
>> A concise tagline for <project_name> is [tagline].

= <tagline>
```

History is valid at top level, in procedures, and in profiles. A nested
`> history: disabled` scope neither reads nor mutates enabled outer history.
Failed and cancelled calls do not commit partial turns.

Prompt hooks run before a turn enters history. When `user_prompt_submit` edits a
prompt, transport, budgeting, telemetry, cache identity, and history all use the
same edited content. A successful prompt/result pair, native continuation,
cleanup ownership, and cache-epoch effect commit atomically. Parallel calls
sharing one conversation run these complete transactions in source order;
separate conversation sessions remain independent.

History is partitioned by concrete adapter and compatible model, settings, MCP,
and tool-contract lane. Each lane keeps its native or portable message sequence,
tool lifecycle, and stable cache identity. Changing an incompatible input starts
a fresh native continuation rather than replaying the previous checkpoint.
Kedi does not translate private provider messages between frameworks, and tool
calls/results remain native causal messages rather than being flattened into a
user prompt. Artifact release and expiry do not delete or reorder existing
messages, so a cached prefix remains append-only within its cache epoch.

## User-Defined History Processing

`PydanticAdapter` and `LangChainAdapter` accept an optional
`history_processor=` callback when an application needs deterministic retention,
redaction, or its own summarization policy. It runs before every logical model
request, including later requests in a tool loop, and receives detached native
messages plus validated editing groups:

```python
from typing import TypeVar

from kedi.agent_adapter import (
    HistoryProcessorContext,
    LangChainAdapter,
    PydanticAdapter,
)

MessageT = TypeVar("MessageT")


def keep_recent_cycles(ctx: HistoryProcessorContext[MessageT]) -> list[MessageT]:
    editable = [group for group in ctx.groups if group.closed and not group.protected]
    retained = {group.group_id for group in editable[-4:]}
    retained.update(group.group_id for group in ctx.groups if group.protected)
    return [
        message
        for group in ctx.groups
        if group.group_id in retained
        for message in ctx.messages[group.entry_start : group.entry_end]
    ]


pydantic_adapter = PydanticAdapter(history_processor=keep_recent_cycles)
langchain_adapter = LangChainAdapter(history_processor=keep_recent_cycles)
```

For an executable tool-loop example using a deterministic `FunctionModel`, see
[examples/history_processor.py](https://github.com/kedi-lang/kedi/blob/stable/examples/history_processor.py).
From the repository checkout, run `uv run python examples/history_processor.py`;
it needs no API key and makes no network requests.

The callback may be synchronous or asynchronous. Synchronous callbacks run in a
worker thread rather than blocking the adapter event loop. It must return a
non-empty sequence in the owning framework's native message type. Returning the
input or an equivalent fresh sequence is a no-op. Do not slice an arbitrary last
`N` messages: a boundary can split a tool call from its result. `ctx.groups`
exposes the atomic ranges that can be selected safely.

Leaving `history_processor=None` disables this work. An enabled no-op still
copies and inspects messages; it preserves history and continuation rather than
eliminating processing overhead. Native message classes and typed tool payloads
are deep-copied, so the callback must not depend on sharing object identity with
the caller. Serialized dictionaries are not accepted in place of native messages.

The frozen context also provides `adapter_shortname`, `model_id`, one-based
`request_index`, `cache_epoch`, a conservative `estimated_tokens` value, and
per-entry metadata. It does not expose the complete wire request: system
instructions, tool schemas, routing, approvals, and model settings remain owned
by the adapter.

### Editing Boundaries

`group.entry_start` and `group.entry_end` are half-open indices into
`ctx.messages`. Groups cover complete user/assistant cycles, including their
tool exchanges. Keep or replace an eligible group as a whole. Redacting one
message while retaining the rest of its original group is rejected; replace
the entire eligible group with native text summary messages instead.

Use `group.closed`, `group.protected`, and `group.protected_reasons` to decide
what is editable. Retained groups may be reordered within the same protected
boundaries, but their internal message order must remain intact. Keep the last
request message exactly, and preserve system messages, checkpoints, unfinished
work, and provider-required records. A signed reasoning block can therefore
protect its entire group.

This conservative grouping does not expose individual completed tool exchanges
inside an ongoing user cycle for arbitrary editing. Use `history_archive=` for
the existing exact archival of long tool loops. Combining it with this callback
does not allow the callback to remove the resulting checkpoints.

Kedi clones the callback input and accepted result. Before transport it rejects
orphan tool results, partial lifecycle groups, an altered current request,
fabricated provider/checkpoint records, and removal of pending or signed native
state. Callback errors propagate; Kedi never silently sends the old history.

`HistoryProcessingError` wraps callback/copy failures;
`HistoryProcessingValidationError` identifies invalid edits. Cancellation
propagates normally. A running synchronous callback's worker thread cannot be
forcibly stopped: its late result is discarded, but application-owned side
effects still need their own cancellation policy. Callback state shared between
concurrent runs is also the application's responsibility. Kedi keeps its request
counters and pending transport resets separate, including nested native runs on
the same adapter. Calling that same configured adapter recursively from inside
the processor raises an error; use a separate processor-free model for a summary.

### Persistence and Continuation

An accepted edit replaces Pydantic AI's native run history or LangChain's
durable graph state, so later tool steps and successful future turns see it.
Stale response-ID continuation is disabled before an incompatible request and
the conversation's cache generation is staged atomically. Failure or cancellation
does not commit the edit. When `history_archive=` is also enabled, exact archival
runs first and the callback sees the checkpointed native history.

Each actual rewrite stages a generation; two rewrites in one run can advance
it twice. Requests without another rewrite reuse the current generation, and
successful commit does not advance it again. An old server-owned conversation
ID remains disabled on later turns of the same Kedi conversation lane: otherwise
the server could reintroduce removed history. Automatic response-ID continuation
may resume from a response produced after the edit; a fixed old response ID is
not reused. Caller-owned model settings are not mutated.

These cross-turn guarantees require Kedi's conversation state. With native
Pydantic `message_history=` alone, carry forward `result.all_messages()` and
appropriate model settings yourself. Do not append `new_messages()` to the old
unprocessed list, because that would restore the history you removed.

A separately supplied Pydantic `ProcessHistory` capability is rejected when
`history_processor` is configured. Compose the policies in one callback instead.
Other capabilities must also respect these message boundaries.

This is a Python adapter API. It does not add a second DSL compaction mode.
