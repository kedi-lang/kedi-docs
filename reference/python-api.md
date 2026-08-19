# Python API Reference

All stable high-level names below are imported from `kedi`.

## Public Selection Types

- `FrameworkAdapterName` is
  `Literal["pydantic", "dspy", "langchain"]`.
- `AgentName` is `Literal["claude", "codex", "acp"]`.
- `AdapterLike` is `AgentAdapter[Any] | LazyAdapter`.
- `ApprovalMode` is `Literal["allow", "deny"]`.
- `ApprovalHandler` is a sync or async callable from `ApprovalRequest` to
  `ApprovalDecision`.

These aliases make extension signatures precise. Pass framework names through
`adapter=` and harness names through `agent=`.

## Query and Bind

```python
import kedi


@kedi.query(
    model=...,
    adapter=...,
    agent=...,
    system=...,
    effort=...,
    settings=...,
    tools=(),
    env=...,
    mcp_servers=(),
    approval=...,
    skills=...,
    artifacts=...,
    conversation=...,
    cache=False,
)
def function(value: str) -> str: ...
```

The function docstring starts with `kedi` and contains a procedure **body**, not
a full top-level program. The Python stub body is never executed. A normal
function produces a sync wrapper; an async function produces an async wrapper
that offloads blocking adapter work.

```python
import kedi


@kedi.bind(
    file="workflow.kedi",
    reload=False,
    cache=False,
    # same backend/profile arguments as query
)
def function(value: str) -> str: ...
```

`bind` resolves the path relative to the decorated function's source file,
loads a complete Kedi program, passes call arguments as runtime globals, and
runs top-level main. `reload=True` reparses when invoked; `cache=True` enables
the response cache. The Python return annotation informs static typing but the
Kedi return remains the runtime authority.

## Configuration

`configure(...)` accepts `model`, mutually exclusive `adapter`/`agent`,
`system`, `effort`, `settings`, `tools`, `env`, `mcp_servers`, `approval`,
`skills`, `artifacts`, `conversation`, `parallel`, `max_workers`, and
adapter-specific keyword arguments.
Each call rebuilds defaults; it does not merge with a previous `configure`.

`context(...)` accepts the same values and merges them over current
configuration for sync or async `with`, restoring the previous ContextVar state
on exit. `parallel(max_workers=8)` is shorthand for a parallel context.
`reset_config()` restores library defaults.

Effective environment precedence is configured/local tools, call arguments,
automatically registered types, configure environment, then progressively local
context/query/bind environment. Name collisions in tool arguments fail rather
than silently selecting one source.

## Tool and Type Decorators

```python
import kedi


@kedi.tool(
    name=None,
    description=None,
    retries=0,
    risk="mutating",
)
def tool_name(value: str) -> object: ...
```

Risk is `read_only`, `mutating`, or `sensitive`. Retries must be nonnegative and
produce `retries + 1` total attempts. Sync and async functions are preserved;
only `Exception` subclasses are retried.

`@kedi.type` converts an ordinary class to a dataclass or preserves an existing
Pydantic/dataclass surface. `inject=True` registers it by name for query
annotations in the defining module; `inject=False` removes that implicit
registration while the class can still be supplied through `env`.

## Artifacts and Sessions

`ArtifactPolicy` validates memory/file storage, size threshold, TTL, bounded
preview/read limits, quota, record count, and cleanup interval. `artifacts=`
accepts a policy, mapping, boolean, or `None` on `configure`, `context`,
`query`, and `bind`.

`session(state=None)` is a synchronous and asynchronous context manager. It
creates or activates a `ConversationState` so calls can share portable model
history and artifact ownership. Kedi remains stateless by default.

Public artifact models are `ArtifactRef`, `ArtifactChunk`,
`ArtifactSearchResult`, `ArtifactReleaseResult`, and `ArtifactHandle`. See
[Artifacts and Sessions](../python-api/artifacts-and-sessions.md).

## Interactive Execution

`interactive(...) -> InteractiveSession` creates a synchronous, process-local
incremental runtime. `InteractiveSession.execute(source, *, source_name=None)`
parses and executes one complete fragment exactly once while retaining earlier
values, declarations, imports, conversation state, and artifacts. It returns
the same native result as `KediRuntime.run_main()`. `close()` is idempotent;
the session is also a context manager.

See [Interactive Execution](../runtime/interactive-execution.md) for supported
configuration, source identity, failure semantics, restrictions, and the
`kedi --idle` frontend.

## Approvals

`@kedi.approval` installs a sync or async handler in current configuration and
returns the same callable. Policies are `ApprovalPolicy.allow()`,
`ApprovalPolicy.deny()`, `ApprovalPolicy.dynamic(handler)`, or the strings
`"allow"`/`"deny"`.

`ApprovalRequest` fields are `tool_name`, immutable deep-copied `arguments`,
`risk`, `adapter_shortname`, `description`, and immutable optional `metadata`.
Handlers return:

```python
kedi.ApprovalDecision.allow(reason=None)
kedi.ApprovalDecision.deny(reason=None)
kedi.ApprovalDecision.edit(arguments, reason=None)
```

Only edit may carry replacement arguments. Edited calls are reclassified and
validated before execution.

## MCP

```python
kedi.McpServerSpec(
    transport="stdio",
    command="server",
    args=(),
    env=None,
    url=None,
    headers=None,
).normalized()
```

Canonical transports are `stdio`, `sse`, and `http`. Stdio requires `command`;
remote transports require `url`. Normalization removes fields inapplicable to
the selected transport. MCP lists append across configuration scopes.

## Cache and Concurrency

`cache_info()` returns frozen `CacheInfo(parse_entries, response_entries)`.
`clear_cache()` clears parse/completed-response caches and advances generation
so stale in-flight calls cannot repopulate them.

`KediPromise.resolve()` returns the concrete value; `.map(fn)` derives without a
worker slot. `force(value)` resolves only a Kedi promise. Concrete use of an
unresolved promise raises `KediPromiseLeak`; `repr()` is non-forcing.

## Low-Level Runtime

`KediRuntime` is the compiled container. Common operations are `run_main()`,
`set_initial_globals(mapping)`, `drain()`, procedure/main decorators,
`m(expressions)`, `invoke(expressions, capture=...)`, trace inspection, and
execution-error construction.

`i(name)`, `o(name, pytype=None)`, and `c(procedure, *args)` construct low-level
input, output, and call expressions for `KediRuntime.m()`.

`Executor` is the runtime-checkable embedded-Python protocol; `DefaultExecutor`
uses host `eval`/`exec` and is not sandboxed. `MarkdownDebugExporter` records
code and values but does not redact secrets.

See the [Python API guide](../python-api/index.md) for complete examples and
scope behavior.
