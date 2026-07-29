# Tool Artifacts

Tool artifacts keep large generated fields and tool results out of model
context while preserving their original native value for Kedi and Python.
They are opt-in and scoped like other agent configuration.

## Enable Artifacts

```kedi no-parse
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
Its policy is lexical: it affects subsequent calls in the current scope.
`enabled: false` disables an inherited policy.

```kedi no-parse
> profile: compact:
    > adapter: pydantic
    > artifacts:
        enabled: true
        threshold: 64kb

@short_answer() -> str:
    > artifacts:
        enabled: false
    >> A short greeting is [answer].
    = `answer`
```

## Policy Reference

| Field | Default | Meaning |
| --- | --- | --- |
| `enabled` | `false` | Convert qualifying values into artifacts |
| `store` | `memory` | `memory` or persistent bounded `file` storage |
| `path` | `.kedi/artifacts` | Root used by the file store |
| `threshold` | `100kb` | Minimum serialized size for conversion |
| `ttl` | `1h` | Fixed lifetime from creation |
| `idle_ttl` | `none` | Optional lifetime from the last successful read |
| `preview_chars` | `1200` | Maximum preview exposed to the model |
| `read_max_chars` | `4000` | Maximum content returned by one read |
| `session_quota` | `256mb` | Maximum active payload bytes per session |
| `max_artifacts` | `128` | Maximum active records per session |
| `cleanup_interval` | `1m` | Lazy and background expiry-check interval |

Byte sizes accept `b`, `kb`, `mb`, `gb`, `kib`, `mib`, and `gib`. Durations
accept `ms`, `s`, `m`, `h`, and `d`. Runtime values may use inline Python:

```kedi no-parse
> artifacts:
    enabled: true
    threshold: `args.artifact_threshold`
    ttl: `timedelta(minutes=30)`
```

## Native Values, Compact Context

Artifact conversion happens after normal type validation. Every generated
field is measured independently. A successful tool result is measured after
approval and execution:

```text
approval -> tool call -> validation -> artifact store -> compact reference
```

Kedi stores an internal lazy handle in its environment. Native Kedi and Python
reads resolve the handle and receive the original typed value:

```kedi no-parse
> artifacts:
    enabled: true
    threshold: 1b

>> A detailed explanation of Kedi is [report].

# The return block receives the complete string.
= `report.upper()`
```

Model substitutions behave differently. Passing `<report>` to another model
call sends a compact `ArtifactRef`, not the full payload:

```kedi
>> A detailed release report is [report].
>> The conclusion in <report> is [conclusion].
```

The reference contains an ID, logical and media types, bounded summary and
preview, size, timestamps, and sensitivity metadata. The model is instructed
to read hidden content before relying on it. A reference returned from a source
tool means that source tool already succeeded; the agent should read the
reference rather than repeat the source operation.

Values returned by `run_main()`, `@kedi.query`, and `@kedi.bind` remain their
original native values.

## Artifact Tools

Enabling artifacts registers three management tools:

- `search_artifacts(query=None, limit=20)` searches active metadata without
  opening payloads.
- `read_artifact(ref_id, max_chars=-1, offset=0, path=None)` reads a bounded
  chunk. `offset` paginates content and `path` is an RFC 6901 JSON Pointer for
  structured values. `-1` selects the configured limit; it is not unlimited.
- `invalidate_artifact(ref_id)` releases an artifact and compacts portable
  history linked to it.

Search and read are read-only operations. Invalidation is mutating and follows
the active approval policy. Management-tool results are never artifacted again.

## Storage and Security

The memory store accepts JSON-compatible values and process-local opaque Python
objects. Serializable mutable values are snapshotted. Opaque values remain
live process-local objects and cannot be persisted.

The file store persists supported text, bytes, JSON, Pydantic, and dataclass
snapshots. It never uses pickle or imports arbitrary classes while loading.
Paths are confined to the configured root, symlink escapes are rejected, and
payload and metadata writes are atomic.

Each reference belongs to one artifact session. Other sessions cannot read it.
Fixed TTL never moves; idle TTL refreshes only after a successful access.
Invalidation is idempotent. An active leased read may finish while release is
pending, but later reads fail with a released or expired error.

Expiry runs lazily and through one process-level cleanup service. Kedi does not
create one cleanup thread per runtime.

## History and Invalidation

Portable conversation history stores compact refs and bounded read chunks, not
the original payload. Invalidating or expiring a ref removes obsolete chunks
while preserving valid tool-call/result structure and leaves a metadata-only
tombstone.

Provider-native checkpoints may still retain earlier content. Kedi marks such
checkpoints stale and rotates or replays compact portable history when the
adapter supports continuation. Invalidation does not claim to erase content
already retained by a remote provider.

Kedi remains stateless by default. Use an explicit Python
[`session()`](../python-api/artifacts-and-sessions.md) when separate calls must
share conversation history and artifact ownership.

## Adapter Support

Artifact-aware adapters receive the same compact reference and bounded
management-tool schemas. Stateful continuation is a separate capability:

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
silently exposing the full value. An adapter may still use artifacts inside one
run without supporting resumed history across calls.

Artifact metadata, summaries, and bounded chunks may appear in telemetry. Raw
payloads are not attached to artifact events. Sensitive data still requires an
appropriate store root, TTL, approval policy, and telemetry configuration.
