# CodeMode

CodeMode reduces the model-facing cost of large tool catalogs and intermediate
tool outputs. Instead of sending every application tool schema to the model,
Kedi exposes three stable control tools and keeps selected tool execution inside
a bounded Monty sandbox.

CodeMode is disabled by default and implemented for Pydantic AI, LangChain,
Claude Agent SDK, and Codex App Server. All four adapters expose the same three
controls and use the same catalog, Monty subset, limits, approval composition,
and artifact boundary. DSPy intentionally remains unsupported.

## Enable CodeMode

Enable it in the current lexical scope:

```kedi
> adapter: pydantic
> codemode: enabled
```

The directive is valid at top level, in a profile, and in a procedure. Disable
an inherited or adapter-constructor policy with `> codemode: disabled`.

The expanded form enables CodeMode and configures its limits. `enabled`
defaults to `true` when omitted:

```kedi
> codemode:
    default_search_limit: 10
    max_search_limit: 50
    max_hydrated_tools: 32
    max_nested_calls: 48
    max_concurrent_calls: 8
    max_tool_result_bytes: 256000
    max_total_tool_result_bytes: 1000000
    request_timeout: 60
```

`> codemode:` is Kedi-owned and is never forwarded as provider model
configuration. `> settings:` does not accept a `codemode` field.

The equivalent Python API is available on every supported adapter:

```python
from kedi.agent_adapter import LangChainAdapter, PydanticAdapter

adapter = PydanticAdapter(model, codemode=True)
langchain_adapter = LangChainAdapter(chat_model, codemode=True)
```

## Model-Facing Tools

The model sees three CodeMode controls instead of the ordinary application tool
schemas.

### `search_tools`

```python
search_tools(
    *,
    query: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
)
```

The result contains only `tool_names` and `next_cursor`. Omitting `query`
returns the next deterministic alphabetical page. Supplying a query performs a
bounded name search; it does not return descriptions or schemas. The cursor is
opaque and bound to the current catalog snapshot, query, page size, and offset.
A changed tool catalog makes old cursors stale.

### `get_tool_schema`

```python
get_tool_schema(*, tool_names: list[str])
```

Names must exactly match values returned by `search_tools`. The result includes
the description, input JSON Schema, output schema when available, sequential
constraint, and the callable name used by Monty. Successfully resolved tools
are added to the current run's hydrated allowlist. Unknown, duplicate, or
ambiguous names fail explicitly.

### `execute_code`

```python
execute_code(*, code: str, restart: bool = False)
```

Only hydrated tools exist in the sandbox. Tool functions are async and accept
keyword arguments:

```python
records = await list_records(project="kedi")
active = [record for record in records if record["active"]]
len(active)
```

Independent calls may run concurrently:

```python
import asyncio

users, projects = await asyncio.gather(
    list_users(team="runtime"),
    list_projects(owner="kedi-lang"),
)
{"users": len(users), "projects": len(projects)}
```

A sequential tool runs exclusively relative to the other nested calls in that
snippet. Merely hydrating it does not serialize unrelated independent calls.
`restart=True` resets variables in the current run's sandbox without affecting
another run. Variables and successful tool results persist between
`execute_code` calls in the same run; reuse them instead of repeating completed
host calls.

When Monty code fails, `execute_code` returns the captured standard output and
traceback message separately:

```json
{
  "output": "loaded 3 rows",
  "error": "AttributeError: 'list' object has no attribute 'get'"
}
```

`output` contains only text printed before the failure, while `error` contains
only the sandbox error. Variables assigned before the failure remain available
to the next cell, so the model can inspect the checkpoint and continue without
repeating successful host calls. Application-tool failures, approval denials,
and Kedi execution limits remain failed tool calls rather than successful
sandbox results.

## Supported Sandbox Subset

The shared CodeMode instruction teaches the verified Monty subset:

- scalar, list, tuple, dictionary, and string literals;
- indexing and read-only slicing;
- arithmetic, comparisons, boolean expressions, and f-strings;
- `if`/`elif`/`else`, `for`, `while`, `break`, and `continue`;
- `range`, `enumerate`, `zip`, comprehensions, sorting, filtering, grouping,
  joining, and aggregation;
- small helper functions;
- `asyncio.gather` for independent hydrated tool calls.

Read mapping values with `mapping[key]`. Monty does not expose mapping methods
such as `mapping.get(...)`.

CodeMode does not provide host filesystem, environment, process, unrestricted
network, third-party package, `eval`, or `exec` access. It is not general
CPython execution.

## Tool Semantics

Nested calls use the adapter's fully assembled application tools through one
Kedi-owned invocation bridge. Kedi therefore retains:

- schema and callable validation;
- `argument_validator` canonicalization;
- static and dynamic risk resolution;
- approval allow, deny, and edit behavior;
- edit revalidation;
- `required_before_output` tracking;
- nested tool telemetry and cancellation;
- sequential constraints and local MCP session ownership.

CodeMode requires Kedi-owned inline approval. A deferred decision cannot safely
suspend and replay half of a snippet. Pydantic therefore rejects
`approval_resolution="external"` while CodeMode is active; other adapters apply
the same inline policy ownership to nested calls.

## MCP Tools

MCP support follows the adapter's interceptable local tool path:

| Adapter | CodeMode MCP behavior |
| --- | --- |
| Pydantic AI | Local `MCPToolset` tools join the catalog; provider-native MCP is rejected. |
| LangChain | `MultiServerMCPClient` tools join the catalog. |
| Claude Agent SDK | Kedi-declared stdio, SSE, and HTTP MCP tools are materialized locally and join the catalog. |
| Codex App Server | Kedi MCP declarations remain unsupported by the adapter. |

Kedi preserves each exact exposed MCP tool name and schema. Duplicate names
from multiple sources are configuration errors. A provider-native path is not
accepted when it would let the model call an application tool outside
`execute_code`.

Claude and Codex keep their harness-native filesystem, search, shell, and other
control-plane tools available. Those controls are not application tools and do
not enter the CodeMode catalog.

## Artifact Boundary

Tool results called inside Monty are not admitted to model history one by one.
They remain bounded, JSON-compatible sandbox values while code filters, joins,
or aggregates them. Only the final `execute_code` result passes through Kedi's
normal artifact policy:

- a compact derived result remains inline;
- a large final result becomes an `ArtifactRef`;
- oversized individual or aggregate nested results fail explicitly;
- artifact-store read helpers are not exposed inside `execute_code`.

Use `run_artifact_code` when the source values are already artifact references.
CodeMode and artifact code have separate responsibilities.

## Lifecycle and Limits

Every agent run receives an isolated catalog, hydration set, Monty process
checkout, and variable state. Kedi closes the session and cancels active host
callbacks on normal completion, errors, cancellation, and early close.

The runtime bounds search pages, discovery payload bytes, hydrated tools, code
characters, nested call count, nested concurrency, individual result bytes,
aggregate result bytes, captured output, and execution time. Invalid cursors,
unhydrated calls, non-JSON nested values, denials, and budget failures are
model-correctable errors rather than silent fallbacks.

| Setting | Default | Meaning |
| --- | ---: | --- |
| `default_search_limit` | `10` | Tool names returned when `search_tools` omits `limit`. |
| `max_search_limit` | `50` | Maximum accepted search page size. |
| `max_hydrated_tools` | `64` | Exact schemas that may be hydrated in one run. |
| `max_discovery_result_bytes` | `256000` | Serialized bound for search and schema results. |
| `max_code_chars` | `20000` | Maximum source length for one snippet. |
| `max_nested_calls` | `64` | Host tool calls allowed in one execution. |
| `max_concurrent_calls` | `8` | Concurrent host tool calls allowed in one execution. |
| `max_tool_result_bytes` | `256000` | Serialized bound for one nested result. |
| `max_total_tool_result_bytes` | `1000000` | Aggregate nested-result bound per execution. |
| `max_print_bytes` | `256000` | Captured standard-output bound. |
| `request_timeout` | `60` | Timeout in seconds for one nested host tool call. |

CodeMode telemetry records payload-free `search tools`, `get tool schema`, and
`execute code` spans. It records counts, byte totals, restart state, duration,
and outcome without recording query text, code, arguments, or tool results.

## Native Pydantic Capability

Use the public capability directly for a single native Pydantic run:

```python
from kedi.agent_adapter import PydanticCodeModeCapability

result = adapter.run_sync(
    "Use CodeMode for this task.",
    capabilities=[PydanticCodeModeCapability()],
)
```

The capability is outermost around the fully assembled Pydantic application
toolset. It is a native Pydantic convenience; LangChain, Claude Agent SDK, and
Codex use adapter projections over the same Kedi CodeMode core.
