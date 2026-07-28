# Python API

The Python API embeds Kedi programs in typed Python callables. It preserves the
same template, substitution, output, profile, tool, MCP, approval, skills, and
runtime semantics as `.kedi` files.

## Embed Kedi in Python

Use `@kedi.query` for a short program in a docstring:

```python
import kedi


@kedi.query
def summarize(text: str) -> str:
    """kedi
>> One-sentence summary of <text>: [summary: str].
    = `summary`
    """
    ...


print(summarize("Kedi combines LLM templates with Python."))
```

Use `@kedi.bind` when the implementation belongs in a separate `.kedi` file:

```python
@kedi.bind(file="summarize.kedi")
def summarize(text: str) -> str:
    ...
```

In both forms, Python owns the callable signature and Kedi owns execution. The
stub body is never called.

## Decorator-Based Programs

The API exposes four decorators:

| Decorator | Role |
| --- | --- |
| `@kedi.query` | Compile a Kedi procedure body from the function docstring |
| `@kedi.bind(file=...)` | Run a complete file-backed Kedi program |
| `@kedi.type` | Register a Python class for Kedi type resolution |
| `@kedi.tool` | Add tool metadata and optional retry behavior to a callable |

`@kedi.approval` registers a default dynamic approval handler in the current
Python API context.

## Global and Scoped Configuration

`kedi.configure(...)` replaces process-context defaults for subsequent calls:

```python
kedi.configure(
    adapter="pydantic",
    model="openai:gpt-4o-mini",
    system="Answer with evidence.",
)
```

`kedi.context(...)` temporarily merges overrides:

```python
with kedi.context(model="openai:gpt-4.1"):
    result = summarize("...")
```

Use `async with` in asynchronous code. Configuration is held in a
`ContextVar`, so scoped overrides follow async task context rather than a
single mutable process-global stack.

## Registered Types and Tools

```python
from pydantic import BaseModel


@kedi.type
class Finding(BaseModel):
    severity: str
    message: str


@kedi.tool(risk="read_only")
def search_docs(query: str) -> list[str]:
    """Search the local documentation index."""
    return []
```

Registering a tool makes it available to the runtime environment. The Kedi
program must still opt into it with `> use: search_docs`.

## Runtime Control

Independent template calls are sequential by default:

```python
with kedi.parallel(max_workers=4):
    result = summarize("...")
```

`kedi.cache_info()` and `kedi.clear_cache()` inspect and clear the in-memory
parse and response caches. `kedi.force(value)` explicitly resolves a low-level
`KediPromise`; ordinary query results are resolved before they return.

## Public API Map

Common imports come from the package root:

```python
from kedi import (
    ApprovalDecision,
    ApprovalPolicy,
    ApprovalRequest,
    CacheInfo,
    KediPromise,
    KediPromiseLeak,
    KediRuntime,
    McpServerSpec,
    bind,
    cache_info,
    clear_cache,
    configure,
    context,
    force,
    parallel,
    query,
    reset_config,
    tool,
    type,
)
```

Compiler entry points are in `kedi.lang`:

```python
from kedi.lang import compile_program, parse_program
```

Executor protocols and the default implementation are also re-exported from
`kedi`; specialized engine and playground executor classes live in their
respective submodules.
