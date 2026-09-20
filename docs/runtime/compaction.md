# Conversation Compaction

Compaction changes retained conversation state. Configure it independently from artifact storage and Python response caching.

## Native Compaction

Compaction belongs to history because it changes the conversation lifecycle and
cache epoch. Configure it with the expanded history form:

```kedi
> history:
    enabled: true
    compaction_mode: native
    compaction_threshold: `100_000`
```

`enabled` is required. `compaction_mode: native` delegates compaction to a
verified provider path. `compaction_threshold` is an optional positive
input-token count; omission uses the integration's default. Current native paths are:

- Pydantic AI `OpenAIResponsesModel` with `OpenAICompaction`;
- Pydantic AI `AnthropicModel` with `AnthropicCompaction`;
- LangChain OpenAI chat models with `context_management`;
- LangChain Anthropic chat models with context management and the required
  compaction beta.

Unsupported adapters and models fail before model I/O. Kedi never silently
changes `native` into an application summarizer. Disable an inherited policy
without disabling history by setting `compaction_mode: disabled`:

```kedi
> history:
    enabled: true
    compaction_mode: disabled
```

`compaction_threshold` cannot accompany `compaction_mode: disabled`. A provider
compaction checkpoint seals the current cache epoch. Kedi rotates the lane's
opaque cache identity once and keeps the compacted provider messages as the
first state of the new epoch. Replaying that checkpoint does not rotate it again.

Kedi includes an adapter-neutral deterministic history processor, lifecycle
grouping, protected-boundary planner, and transactional checkpoint validation
foundation. A Kedi-owned semantic summarizer is intentionally not public yet;
it is tracked in [kedi-lang/kedi#80](https://github.com/kedi-lang/kedi/issues/80).

## Application-Owned Processing

`history_processor=` is separate from native compaction. It lets Python
applications implement deterministic retention, redaction, or summarization
over framework-native messages. With `history_archive=`, exact archival runs
first and the custom processor receives the resulting checkpointed history.
Kedi validates atomic tool lifecycles and protected provider state before an
accepted edit replaces durable history.

See [User-Defined History Processing](history.md#user-defined-history-processing)
for the callback contract and a whole-group selection example.
