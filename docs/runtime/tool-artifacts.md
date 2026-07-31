# Tool Artifacts

Tool Artifacts is Kedi's bounded large-value transport. It prevents large tool
results and generated fields from being copied into model context while
preserving the original typed value for Kedi and embedded Python.

Artifacts are enabled by default. They are part of the normal agent execution
contract, not an optional persistence API: values that remain small continue to
flow inline, while qualifying values are represented to the model by compact,
session-scoped references.

## Normative Model

Tool Artifacts separates one logical value into three representations:

1. **Native value**: the original `str`, `bytes`, list, Pydantic model,
   dataclass, or other Python object used by Kedi and Python.
2. **Stored payload**: the serialized or process-local value owned by one
   `ArtifactManager` and one artifact session.
3. **Model-visible reference**: a bounded `ArtifactRef` containing metadata,
   summary, preview, size, expiry, and instructions for retrieving content.

These representations have different consumers and must not be conflated:

| Consumer | Representation |
| --- | --- |
| Kedi return block, embedded Python, `run_main()` | Original native value |
| A later model call receiving an artifact-backed substitution | `ArtifactRef` |
| `read_artifact` and `run_artifact_code` | Bounded views of the stored payload |
| Portable conversation history | References and bounded read results |

The core invariant is:

> Artifact conversion may change how a value crosses the model boundary, but
> it must not change the value observed by Kedi or Python.

Consequently, `ArtifactRef[T]` is a model transport type. It does not replace
`T` in ordinary application code.

## Runtime Architecture

One artifact-enabled execution is composed of the following parts:

| Component | Responsibility |
| --- | --- |
| `ArtifactPolicy` | Lexically scoped admission, storage, quota, and expiry configuration |
| `ArtifactManager` | Session ownership, admission, deduplication, reads, leases, release, and cleanup |
| `ArtifactStore` | Memory or file-backed payload storage |
| `ArtifactHandle[T]` | Lazy internal binding that resolves to the native `T` |
| `ArtifactRef[T]` | Compact model-visible metadata |
| Artifact management tools | Search, bounded read, code-based reduction, and release |
| `ArtifactHistory` | Append-only lifecycle events for portable history and telemetry |

The manager belongs to an explicit artifact session. A normal stateless Kedi
run creates a session for that run. A Python `session()` keeps one manager and
conversation state across multiple calls.

The management tools and artifact instructions are installed as a stable
contract from the first artifact-enabled model call. They are not injected only
after the first large result. Keeping the prefix stable avoids invalidating
provider prompt caches when an artifact first appears later in a run.

## End-to-End Dataflow

### Generated fields

Each generated field is validated against its declared Kedi type before
artifact admission. Fields are measured independently; one large field can
become an artifact while sibling fields remain inline.

```text
model output
  -> structured-output validation
  -> serialize and measure each field
  -> inline value OR ArtifactHandle[T]
  -> bind into KediEnv
```

### Tool results

A tool result enters artifact admission only after the tool was approved,
executed, and return-validated:

```text
tool request
  -> approval
  -> tool execution
  -> return validation
  -> serialize and measure
  -> inline result OR ArtifactHandle[T]
  -> model receives inline result OR ArtifactRef[T]
```

An `ArtifactRef` returned from a tool means the source tool already completed.
The model must inspect the reference instead of repeating the source operation.

### Native reads

Kedi stores an `ArtifactHandle[T]` internally. When Kedi or embedded Python
reads that binding, the handle asks its session manager for the original value:

```kedi
> artifacts:
    threshold: 1b

>> A detailed explanation of Kedi is [report].

# `report` resolves to the complete native string here.
= `report.upper()`
```

The same rule applies to `run_main()`, `@kedi.query`, and `@kedi.bind`: their
callers receive the native result, not artifact metadata.

### Model substitutions

The model boundary is deliberately different. A later template that receives
an artifact-backed value sees only its compact reference:

```kedi
>> A detailed release report is [report].
>> The conclusion in <report> is [conclusion].
```

The second call can use `read_artifact` or `run_artifact_code` to retrieve only
the evidence required to fill `conclusion`. The full report is not implicitly
copied into the second prompt.

## Admission Algorithm

Materialized values are serialized once to determine their logical type,
media type, byte size, summary, preview, persistence support, and optional
content digest.

For generated fields and ordinary values, admission is equivalent to:

```text
if artifacts are disabled:
    return native value
if serialized size < threshold:
    return native value
return stored ArtifactHandle
```

Tool results have an additional hard context-safety limit of 100,000 bytes:

```text
if artifacts are enabled and (
    serialized size >= threshold OR serialized size > 100,000 bytes
):
    return stored ArtifactHandle
if serialized size <= 100,000 bytes:
    return native value
raise ToolOutputTooLargeError
```

This means increasing `threshold` above 100 KB does not authorize a tool to
insert a larger payload into model history. With artifacts enabled, that result
is still artifacted. With artifacts explicitly disabled, it is rejected before
history insertion.

Artifact admission is deterministic for a given serialized payload and policy.
An identical active payload in the same store is deduplicated by digest before
quota enforcement and reuses the existing reference.

## Configuration and Lexical Scope

```kedi
> artifacts:
    enabled: true
    store: memory
    threshold: 100kb
    ttl: 1h
    idle_ttl: none
    preview_chars: 1200
    read_max_chars: 4000
    session_quota: 256mb
    max_artifacts: 128
    cleanup_interval: 1m
```

The directive is valid at top level, inside a procedure, and inside a profile.
Its policy is lexical and source ordered: it affects subsequent calls in the
current scope. A nested policy overlays only the fields it specifies. Setting
`enabled: false` explicitly disables inherited artifact handling in that scope.

```kedi
> profile: compact:
    > adapter: pydantic
    > artifacts:
        threshold: 64kb

@short_answer() -> str:
    > artifacts:
        enabled: false
    >> A short greeting is [answer].
    = `answer`
```

### Policy reference

| Field | Default | Constraint | Meaning |
| --- | --- | --- | --- |
| `enabled` | `true` | Boolean | Enables artifact admission and management tools |
| `store` | `memory` | `memory` or `file` | Payload store for newly admitted values |
| `path` | `.kedi/artifacts` | String or `Path` | Root directory for the file store |
| `threshold` | `100kb` | Non-negative byte size | Minimum serialized size for ordinary artifact conversion |
| `ttl` | `1h` | Positive duration | Absolute lifetime from creation |
| `idle_ttl` | `none` | `none` or positive duration | Optional lifetime since last successful access |
| `preview_chars` | `1200` | Positive integer | Maximum preview length in `ArtifactRef` |
| `read_max_chars` | `4000` | Positive integer | Per-read upper bound, including code-mode reads |
| `session_quota` | `256mb` | Positive byte size | Maximum active payload bytes in one session |
| `max_artifacts` | `128` | Positive integer | Maximum active records in one session |
| `cleanup_interval` | `1m` | Positive duration | Maximum interval between expiry checks |

Byte sizes accept `b`, `kb`, `mb`, `gb`, `kib`, `mib`, and `gib`. Decimal units
use powers of 1,000; binary units use powers of 1,024. Durations accept `ms`,
`s`, `m`, `h`, and `d`. Runtime values may use inline Python:

```kedi
> artifacts:
    threshold: `args.artifact_threshold`
    ttl: `timedelta(minutes=30)`
```

## Reference Contract

`ArtifactRef[T]` is immutable and contains:

| Field | Meaning |
| --- | --- |
| `ref_id` | Session-scoped identifier such as `tool_call_result_1` |
| `logical_type` | Fully qualified native type name |
| `media_type` | Stored projection type, such as JSON or UTF-8 text |
| `summary` | Bounded structural description, not a model-generated replacement |
| `preview` | Bounded prefix preview; it may be incomplete |
| `size_bytes` | Canonical serialized payload size |
| `char_count` | Character count when meaningful; `null` for binary or opaque values |
| `created_at` | UTC creation timestamp |
| `expires_at` | Fixed-TTL UTC deadline |
| `sensitive` | Sensitivity marker for policy and observability consumers |
| `usage_hint` | Stable routing guidance for reading, code reduction, and release |

Reference IDs are ordered per artifact kind within a session:

- `tool_call_result_N` for tool results
- `template_output_N` for generated fields
- `artifact_code_result_N` for derived code-mode results
- `artifact_N` for other sources

The ID is a handle, not globally unique storage identity. Access is authorized
by the owning artifact session; a different session cannot read the payload.

The preview is explicitly non-authoritative. A model must not treat a truncated
preview as the complete source or invent missing content from it.

## Management Tools

Artifact-enabled adapters receive four runtime-owned tools. Their schemas and
instructions remain stable across turns.

### `search_artifacts`

```text
search_artifacts(query: str | None = None, limit: int = 20)
```

Searches active reference metadata without opening payloads. Search covers the
reference ID, logical type, media type, summary, and source. Results are newest
first, include status and timestamps, and are capped at 100 items.

Use this when the required reference is not already present in the current
context. Do not search before reading a known reference.

### `read_artifact`

```text
read_artifact(
    ref_id: str,
    max_chars: int = -1,
    offset: int = 0,
    offset_from: "start" | "end" = "start",
    path: str | None = None,
    pattern: str | None = None,
    max_matches: int = 20,
)
```

This is the preferred operation for a known literal, one JSON field, the head
or tail of a value, or another bounded inspection.

- `max_chars=-1` selects `read_max_chars`; it never means unlimited.
- A positive `max_chars` is clamped to `read_max_chars`.
- `offset_from="start"` pages forward from the beginning.
- `offset_from="end"` addresses a tail-relative window without reversing text.
- `path` is an RFC 6901 JSON Pointer into structured JSON content.
- `pattern` performs bounded literal substring search and returns match
  contexts instead of an `ArtifactChunk`.
- Pattern search cannot be combined with `offset`, `offset_from="end"`, or
  `path`.

An `ArtifactChunk` returns `content`, the requested `offset`, an optional
`next_offset`, `complete`, `media_type`, `path`, and `offset_from`. Callers must
use `complete` and `next_offset`; the absence of more text must not be inferred
from chunk length alone.

### `run_artifact_code`

```text
run_artifact_code(code: str, artifact_refs: list[str])
```

Runs bounded Python over an explicit reference allowlist. Use it for filtering,
aggregation, joins, ranking, cross-artifact comparison, and any operation where
returning pages to the model would cost more context than returning the reduced
answer.

The sandbox exposes:

```python
artifact_metadata(ref_id)
read_artifact(ref_id, offset=0, offset_from="start", max_chars=-1)
find_artifact(ref_id, pattern, max_matches=20, context_chars=120)
iter_artifact(ref_id, chunk_chars=4000)
get_artifact(ref_id)
```

`get_artifact` is limited to small values. Large values must be processed with
bounded reads, literal search, or iteration. The final Python expression is the
semantic result; captured stdout is diagnostic output.

The execution cannot import modules or access host files, environment
variables, the network, models, adapters, tools, or subagents. It can access
only references listed in `artifact_refs`. Host calls, total bytes read,
materialization, stdout, execution time, memory, recursion, result size, result
depth, and result node count are bounded.

The default runtime limits are:

| Limit | Default |
| --- | ---: |
| Duration | 5 seconds |
| Memory | 64 MB |
| Recursion depth | 100 |
| Allowed references | 32 |
| Host calls | 256 |
| Characters per host read | 64,000 |
| Cumulative bytes read | 32 MB |
| `get_artifact` materialization | 256 KB |
| Captured stdout | 16 KB |
| Result size | 8 MB |
| Result depth | 64 |
| Result nodes | 100,000 |

The result is admitted under the active artifact policy. A small reduction is
returned inline. A reduction at or above the threshold becomes a new
`artifact_code_result_N` with provenance linking its source references and a
hash of the executed code. The derived artifact remains valid if its source
artifacts are later released.

Choose a threshold larger than the expected reduced result. An unnecessarily
low threshold can recursively artifact a useful small reduction and force an
extra model turn to read it.

### `release_artifact`

```text
release_artifact(ref_id: str)
```

Releases payload storage and quota after the agent has consumed all evidence it
will need from that reference. Release is mutating and follows the active
approval policy. It is idempotent: releasing an already released artifact
returns `already_released=true`.

Release does not delete or rewrite prior conversation messages. Later access to
the payload fails with `ArtifactReleasedError`.

## Agent Routing Contract

The runtime instructs artifact-aware agents to follow this decision table:

| Need | Operation |
| --- | --- |
| Known literal, one bounded range, head, tail, or one JSON path | `read_artifact` |
| Locate a literal in one artifact | `read_artifact(pattern=...)` |
| Locate an artifact whose reference is unknown | `search_artifacts` |
| Filter, aggregate, rank, join, or compare one or more artifacts | `run_artifact_code` |
| Payload is no longer needed | `release_artifact` |

The agent must not repeat a source tool after receiving its artifact reference.
It must not page an entire large payload through `read_artifact` when a bounded
code reduction can produce the answer. Conversely, it should not invoke the
code sandbox for a single known literal or one small bounded read.

This routing is the source of the context reduction: the model sees compact
references and small semantic results rather than every byte touched by the
runtime.

## Explicit Streaming

Artifact admission protects model context even for ordinary materialized tool
results, but it cannot undo producer memory already allocated by user code. A
tool that constructs a 500 MB string has already paid for that allocation before
Kedi can measure it.

Tools that need bounded producer memory must opt into `ArtifactStream`:

```python
from collections.abc import Iterator

import kedi


def chunks() -> Iterator[str]:
    with open("application.log", encoding="utf-8") as stream:
        while chunk := stream.read(64 * 1024):
            yield chunk


@kedi.tool
def read_application_log() -> kedi.ArtifactStream[str]:
    return kedi.ArtifactStream.text(chunks())
```

`ArtifactStream.text`, `ArtifactStream.bytes`, and
`ArtifactStream.json_items` accept synchronous or asynchronous sources. Kedi
does not infer stream semantics from arbitrary iterables or generators; the
explicit wrapper makes single-use ownership and failure behavior unambiguous.

The stream pipeline is:

```text
producer chunks
  -> incremental canonical encoder
  -> threshold buffer
  -> transactional store writer after threshold crossing
  -> compact reference
```

Before the threshold is crossed, Kedi buffers only enough content to decide
whether the result stays inline. Once crossed, the buffer and later chunks are
written incrementally. Session quota is reserved and grown as chunks arrive.
Failure, cancellation, invalid chunk type, or quota rejection aborts the writer,
releases reservations, closes the source, and exposes no partial artifact.

If a stream completes below the threshold, Kedi reconstructs its declared
native value. If artifacts are disabled, a stream may stay inline only up to
the 100,000-byte hard tool-result limit.

The bundled `filesystem.read_text_file` and skill `read_skill` tools use
`ArtifactStream` automatically during adapter tool calls. Their direct
Kedi/Python call contract remains `str`; the incremental transport is an
internal execution detail and does not alter their schema. Small bounded tools
such as directory and artifact metadata listing remain materialized. Sandbox
and subagent results are artifact-admitted after completion because their
underlying engines do not expose incremental result chunks.

## Serialization and Stores

### Canonical serialization

Kedi supports four payload classes:

| Value | Codec | Media type | Persistence |
| --- | --- | --- | :---: |
| `str` | UTF-8 text | `text/plain; charset=utf-8` | yes |
| `bytes` | raw bytes | `application/octet-stream` | yes |
| JSON-compatible values, Pydantic models, dataclasses | canonical JSON | `application/json` | yes |
| Other Python objects | opaque process-local object | `application/x-python-object` | memory only |

Serializable mutable values are snapshotted when admitted. JSON encoding is
canonical and records bounded RFC 6901 pointer ranges so file-backed path reads
can avoid materializing the complete document. Opaque objects use a safe type
preview, have no content digest, and cannot enter the file store.

Kedi never uses pickle and never imports an arbitrary class while loading an
artifact.

### Memory store

The memory store preserves native Python values, including opaque objects. It
reduces model context, but it is not resident-memory offload: the process still
owns the full value until release, expiry, or manager close.

### File store

The file store persists supported text, bytes, and JSON projections and does
not retain an unbounded native-value cache. Reads and literal searches operate
on the persisted projection. Paths are confined to the configured root,
symlink escapes are rejected, and payload and metadata writes are atomic.

File records are restored only for their owning session. Expired records are
not revived. A value that cannot be represented safely by a supported codec
raises `ArtifactSerializationError` instead of falling back to unsafe
persistence.

## Quotas, Expiry, and Concurrency

Admission checks both active artifact count and active payload bytes. Streaming
writes reserve count and bytes transactionally, so concurrent producers cannot
individually pass a stale quota check and overcommit the session.

The fixed TTL is measured from creation and never moves. `idle_ttl` is measured
from the last successful leased access. An artifact expires at the earlier of
the two deadlines.

Reads acquire a lease. If release or expiry occurs during an active read, the
record enters `pending_release` or `expired`, the current reader may finish, and
the payload is deleted when the final lease closes. New reads fail immediately.

Artifact states are:

```text
active -> pending_release -> released
active ------------------> released
active ------------------> expired
pending_release ----------> expired
```

Cleanup is both lazy and background-driven. Runtime operations perform an
expiry check when the configured interval has elapsed, and one process-level
cleanup service tracks active managers. Kedi does not create one cleanup thread
per runtime.

Closing the manager unregisters cleanup, closes stores and code-runtime pools,
and releases in-process accounting. An application must not reuse a closed
session.

## History and Cache Stability

`ArtifactHistory` is a thread-safe, append-only lifecycle log with monotonically
increasing sequence numbers. It records tool calls, tool results, artifact
creation, bounded reads, release, and expiry. Portable conversation history
contains references and bounded tool results, never the original large payload.

Within one cache epoch, artifact lifecycle operations never delete, reorder, or
rewrite earlier model messages. Releasing or expiring a payload therefore does
not invalidate an already cached provider prefix. The old reference remains in
history, but later attempts to dereference it receive the precise released or
expired error.

Provider-native checkpoints follow the same rule: release and expiry do not
mutate their existing prefix. Conversation compaction is a separate explicit
operation that starts a new cache epoch; artifact lifecycle does not perform
hidden history compaction.

Kedi remains stateless by default. Use an explicit Python
[`session()`](../python-api/artifacts-and-sessions.md) when separate calls must
share model history and artifact ownership.

## Failure Semantics

Artifact failures are explicit and do not silently expose the full payload:

| Error | Meaning |
| --- | --- |
| `ArtifactPolicyError` | Invalid field, unit, store, duration, or bound |
| `ArtifactSerializationError` | Value cannot be represented by the selected store |
| `ArtifactQuotaExceededError` | Count or byte quota would be exceeded |
| `ToolOutputTooLargeError` | Artifacts are disabled and a tool result exceeds 100,000 bytes |
| `ArtifactAccessError` | Reference is unknown or belongs to another session |
| `ArtifactReleasedError` | Payload was explicitly released or is pending release |
| `ArtifactExpiredError` | TTL or idle TTL elapsed |
| `ArtifactStreamError` | Stream kind, chunk, reuse, or transactional consumption failed |
| `ArtifactCodeAccessError` | Code attempted to access a ref outside its allowlist |
| `ArtifactCodeBudgetError` | Code exceeded a host-call, read, materialization, or result bound |
| `ArtifactCodeError` | Sandboxed artifact computation failed |

Quota failure occurs before publishing a reference. Stream failure aborts the
transaction. Code-mode failure does not create a derived artifact. None of
these errors include the rejected raw payload in their message or telemetry.

## Adapter Contract

Artifact-aware adapters receive the same compact metadata, stable system
instructions, and management-tool schemas. Stateful continuation is a separate
capability:

| Adapter | Compact artifacts | Stateful history |
| --- | :---: | :---: |
| Pydantic AI | yes | yes |
| Claude Agent SDK | yes | yes |
| Codex App Server | yes | no |
| LangChain | yes | no |
| DSPy | yes | no |
| WebGPU | yes | no |
| ACP | no | no |

An adapter without artifact support fails capability validation instead of
silently copying the original payload into context. An adapter may support
artifacts within one run without supporting continuation across calls.

## Security and Observability

Artifact metadata, summaries, bounded previews, read sizes, lifecycle states,
and code-mode provenance may appear in telemetry. Raw payloads are not attached
to artifact lifecycle spans. Code provenance contains a code hash and source
references, not an unrestricted payload copy.

Artifact storage is not a secret-management boundary. Sensitive data still
requires a suitable file-store root, TTL, approval policy, process isolation,
and telemetry configuration. The `sensitive` marker is metadata for policy and
observability consumers; it does not encrypt the payload.

## Operational Guidance

- Keep artifacts enabled for agentic programs. Disabling them does not permit
  unbounded tool context; it converts oversized results into hard failures.
- Set `threshold` above the expected size of useful reductions so
  `run_artifact_code` can return them inline.
- Use `ArtifactStream` for producer-memory control. Ordinary artifact admission
  controls model context, not the allocation already made inside a tool.
- Prefer `read_artifact` for one bounded fact and `run_artifact_code` for data
  reduction. Paging an entire payload through the model defeats the design.
- Release payloads only after the needed evidence and derived values have been
  obtained. Release frees quota but intentionally leaves history immutable.
- Use the file store when process memory offload or restart persistence matters;
  use the memory store when native opaque Python values are required.

Explicitly setting `enabled: false` removes artifact references and management
tools from that scope. A tool result over the hard inline limit still fails
before model history insertion.
