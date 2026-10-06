# Artifact Admission and Configuration

Choose which values enter storage and how much context each preview or read may expose. These are byte and character limits, not provider token budgets.

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
    query_artifacts: disabled
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
| `query_artifacts` | `disabled` | `enabled` or `disabled` | Exposes bounded lexical retrieval for known artifacts |
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
