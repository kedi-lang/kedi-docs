# Caching

Kedi has several independent reuse mechanisms. Enabling one does not enable the
others.

Tool artifacts are not a cache: they replace large model-visible values with
bounded references while retaining the native value for the current artifact
session. See [Tool Artifacts](tool-artifacts.md).

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

History is partitioned by adapter. Each adapter lane keeps its native or
portable message sequence, tool lifecycle, and stable cache identity. Switching
adapters resumes that adapter's lane rather than translating private provider
messages. Artifact release and expiry do not delete or reorder existing
messages, so a cached prefix remains append-only within its cache epoch.

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

## Python API Parse Cache

`@kedi.query` and `@kedi.bind` cache parsed programs automatically. The key is:

- API kind (`query` or `bind`);
- source path when applicable;
- SHA-256 of the exact Kedi source.

Identical source is parsed once in the process. A changed hash creates a new
entry. `bind(..., reload=True)` rereads its file and therefore detects source
changes; without reload, the file content is captured when decorated.

This cache avoids parser work only. It never reuses model answers.

## Response Cache

Response caching is opt-in per Python query or binding:

```python
import kedi


@kedi.query(cache=True)
def summarize(topic: str) -> str:
    """kedi
    >> One-sentence summary of <topic>: [summary: str].
    = <summary>
    """
```

The cache key includes source identity/hash, callable identity, arguments,
configured and local environment, resolved backend identity, adapter kwargs,
model/profile state, approval identity, MCP servers, skills, and tool names.
A model, instruction, setting, tool, argument, or env change therefore creates
a fresh entry.

Values are represented stably so incidental object memory addresses do not
split otherwise equivalent calls.

## Concurrent First Calls

Concurrent callers for the same missing key coalesce into one producer flight.
Waiters receive the same result or producer exception. A failed producer writes
no response entry and releases waiters.

Recursive acquisition of the same key by its owner is rejected rather than
deadlocking. Clearing caches advances a generation so an older in-flight result
can finish its waiters but cannot repopulate the freshly cleared cache.

## Result Isolation

Kedi deep-copies stored and returned cached results when possible. Mutating one
returned list, dict, Pydantic model, or dataclass does not corrupt the shared
entry for later callers.

For exotic non-copyable objects such as locks, connections, or open handles,
Kedi falls back to returning by reference. Such values are poor cache results;
prefer serializable immutable data.

## Inspect and Clear

```python
import kedi

info = kedi.cache_info()
print(info.parse_entries, info.response_entries)

kedi.clear_cache()
```

`clear_cache()` clears both Python API caches for the current process. These
caches are in memory and do not survive process restart.

## Code Generation Cache

AI-generated `> auto:` procedures use a sibling `.cache.kedi` file. Each
generated procedure occupies a comment-delimited block keyed by procedure name,
so regenerating one does not overwrite other generated implementations.

The cache is merged with source for compilation and tests. Writes are atomic.
Failed generation removes only that procedure's block. CLI `--no-cache`
disables reuse and removes generated temporary cache content after the run.

Treat `.cache.kedi` as generated executable Kedi/Python source. Review it when
shipping generated implementations and do not confuse it with model-response
memoization.

## Optimized Prompt Artifacts

Optimization writes a sibling `.optimized.json` mapping procedure and optimize
span names to prompt prefixes. Program/test loading injects valid prefixes into
the matching spans while preserving the original seed template.

Missing artifacts mean no optimization. Invalid JSON or invalid shape fails
loudly; Kedi does not silently run the base prompt when a present artifact is
corrupt. Stale span names are diagnosed during loading.

See [Evals and Optimization](../evals-and-optimization/index.md) for generation
and validation rules.

## Privacy and Staleness

Response keys may derive from argument and environment representations, and
cached values may contain model output. The current cache is process-local, but
do not pass secrets to a long-lived shared process without an application-level
data policy.

Caching assumes the modeled operation is stable for the key. Disable it for
time-sensitive answers, changing external state, nondeterministic tool results,
or side-effecting workflows.
