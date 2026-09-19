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
