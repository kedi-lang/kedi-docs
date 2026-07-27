# Caching, Runtime, and Executors

## Inspect Cache State

```python
info = kedi.cache_info()
print(info.parse_entries)
print(info.response_entries)
```

`CacheInfo` is a frozen dataclass with counts for the process-memory parse and
response caches. It does not report codegen, optimized prompt, GEPA checkpoint,
or adapter-provider caches.

## Clear Caches

```python
kedi.clear_cache()
```

This clears parsed programs and completed response entries. It also advances a
cache generation: a request already in flight may finish for its current
callers, but it cannot repopulate the newly cleared cache.

Response caching is opt-in per `query` or `bind` with `cache=True`. Parse
caching is always source-hash based. Concurrent identical response misses
coalesce; failed calls are never stored. A recursive same-thread request for
the same cache key raises instead of deadlocking.

## `KediRuntime`

`KediRuntime` is the compiled execution container:

```python
from kedi import KediRuntime
```

Most applications should use `query` or `bind`. Use the runtime directly when
building an embedding, custom compiler flow, executor integration, or engine.

Important public methods include:

- `run_main()` to execute the compiled top-level program and return a forced
  result;
- `set_initial_globals(mapping)` to seed runtime values before execution;
- `procedure` and `main` decorators for low-level program construction;
- `m(expressions)` and `invoke(expressions, capture=...)` inside an active Kedi
  procedure context;
- `drain()` to await every scheduled job;
- `current_trace_frames()` and `build_execution_error(...)` for diagnostics.

## Compile Programs

Parse and compile explicitly:

```python
from kedi.lang import compile_program, parse_program

source = """
@greet(name: str) -> str:
  = Hello, <name>

= <greet(World)>
"""

program = parse_program(source, source_path="<memory>")
runtime = compile_program(program)
result = runtime.run_main()
```

A model adapter is optional only when the program never executes a template or
raw invoke. For model-backed programs, pass an `AgentAdapter`.

## Runtime Input, Output, and Context

Seed native values:

```python
program = parse_program("= `customer_id`")
runtime = compile_program(
    program,
    runtime_globals={"customer_id": "cus_123"},
)
assert runtime.run_main() == "cus_123"
```

`compile_program(...)` accepts:

- `adapter`;
- `executor`;
- `runtime_globals`;
- `engine`;
- `default_agent_profile`;
- subagent depth, concurrency, timeout, usage limits, and state path.

The runtime owns procedure/global environments and uses `ContextVar` for the
current invocation, trace stack, and subagent stack.

## Low-Level Expressions

The root package exports constructors used with `runtime.m(...)`:

```python
from kedi import c, i, o

expressions = [
    "Find the capital of ",
    i("country"),
    ": ",
    o("capital", str),
]
```

`i(name)` reads an input, `o(name, type)` declares an output, and
`c(procedure, *args)` invokes a Kedi procedure. `runtime.m(...)` and
`runtime.invoke(...)` require an active procedure environment; calling them
arbitrarily outside Kedi execution raises.

## Custom Executors

Implement the `Executor` protocol from `kedi`:

```python
from typing import Any, Callable
from kedi import Executor, ExecutorDebugExporter, KediRuntime


class RestrictedExecutor:
    def set_debug_exporter(
        self, exporter: ExecutorDebugExporter | None
    ) -> None: ...

    def evaluate_inline(
        self, rt: KediRuntime, code: str, local_env: dict[str, Any]
    ) -> Any: ...

    def execute_block(
        self, rt: KediRuntime, code: str, local_env: dict[str, Any]
    ) -> Any: ...

    def execute_side_effects(
        self,
        rt: KediRuntime,
        code: str,
        env_map: dict[str, Any],
        *,
        kedi_line_offset: int = 0,
    ) -> None: ...

    def execute_prelude(
        self, rt: KediRuntime, code: str
    ) -> dict[str, Any]: ...

    def create_dynamic_function(
        self,
        name: str,
        params: list[str],
        body: Callable[..., Any],
        defaults: dict[str, Any] | None = None,
    ) -> Callable[..., Any]: ...

    def evaluate_type_expression(
        self, rt: KediRuntime, code: str, env: dict[str, Any]
    ) -> Any: ...
```

The protocol is runtime-checkable. A custom executor must preserve Kedi's
environment and return semantics, not merely evaluate isolated strings.

## Default Executor

`DefaultExecutor` uses Python `eval` and `exec`:

```python
from kedi import DefaultExecutor

runtime = compile_program(program, executor=DefaultExecutor())
```

It is **not sandboxed**. Embedded Python has the host process's authority,
imports, filesystem access, network access, and credentials. Use a specialized
executor and operating-system isolation for untrusted Kedi source.

## Debug Exporters

Attach a Markdown event exporter:

```python
from kedi import DefaultExecutor, MarkdownDebugExporter

executor = DefaultExecutor(
    debug_exporter=MarkdownDebugExporter("runtime-debug.md")
)
runtime = compile_program(program, executor=executor)
```

Events include executor step, code, inputs, local environment, outputs, and
errors. Sanitization makes values printable; it does **not redact secrets**.
Debug exports can contain prompts, credentials, user data, and tool results.
Store and share them accordingly.

`default_debug_export_path("program.kedi")` creates a timestamped path in the
current working directory.

## Subagent State Persistence

Low-level compilation can configure subagents:

```python
runtime = compile_program(
    program,
    adapter=adapter,
    subagent_max_depth=5,
    subagent_max_concurrency=4,
    subagent_timeout_seconds=120.0,
    subagent_usage_limits=limits,
    subagent_state_path=".kedi/subagents.json",
)
```

The state file belongs to the subagent coordinator and is separate from
response, codegen, and optimization caches. Pending or running work restored
after process loss is marked interrupted rather than falsely reported as
completed.

