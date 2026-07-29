# Configuration and Context

## Configure Process Defaults

`kedi.configure(...)` creates a new default configuration in the current
context:

```python
import kedi

kedi.configure(
    adapter="pydantic",
    model="openai:gpt-4o-mini",
    system="Prefer precise, source-grounded answers.",
    effort="low",
    settings={"temperature": 0.2},
    tools=[search_docs],
    env={"audience": "maintainers"},
    approval="deny",
    skills=False,
    artifacts=False,
    parallel=False,
    max_workers=8,
)
```

Calling `configure()` again rebuilds defaults; it does not merge with the
previous `configure()` call. Pass the complete intended default configuration.

## Temporary Context Overrides

`kedi.context(...)` merges onto the currently active configuration and restores
it afterward:

```python
with kedi.context(
    model="openai:gpt-4.1",
    system="Perform a deeper review.",
    effort="high",
):
    result = review("...")
```

Nested contexts merge in order. Later settings and environment keys override
earlier keys. Tools merge by registered name. MCP server sequences append.
Artifact mappings overlay inherited policy fields. `artifacts=False` disables
an inherited policy. Conversation state changes only when an explicit
`conversation=` is supplied.

## Sync and Async Context Managers

The same object supports both forms:

```python
with kedi.context(model="openai:gpt-4o-mini"):
    sync_result = summarize("...")
```

```python
async with kedi.context(model="openai:gpt-4o-mini"):
    async_result = await summarize_async("...")
```

Configuration uses `ContextVar`, so an async task inherits the context present
when it is created. A context does not globally reconfigure unrelated task
contexts.

## Framework and Harness Selection

Use `adapter=` for frameworks:

```python
kedi.configure(adapter="pydantic")
kedi.configure(adapter="dspy")
kedi.configure(adapter="langchain")
```

Use `agent=` for process-backed harnesses:

```python
kedi.configure(agent="claude")
kedi.configure(agent="codex")
kedi.configure(agent="acp")
```

Passing both is an error. Passing a harness name through `adapter=` or a
framework name through `agent=` also fails with a corrective message.
`AdapterLike` instances must expose `kind` and `shortname` metadata consistent
with the parameter used.

## Models, Instructions, Effort, and Settings

These profile fields merge from configuration, context, callable decorator,
and DSL directives:

```python
with kedi.context(
    model="openai:gpt-4.1",
    system="Answer for an expert reader.",
    effort="high",
    settings={
        "temperature": 0.1,
        "max_tokens": 2048,
    },
):
    result = explain("promise pipelining")
```

Settings are backend-specific. Unsupported profile overrides fail or produce a
documented capability warning according to the selected adapter; Kedi does not
pretend every backend supports every field.

Extra keyword arguments accepted by `configure()` and `context()` are adapter
construction arguments, not profile `settings`. `query()` and `bind()` expose
only their declared parameters and do not accept arbitrary adapter kwargs.

## Runtime Environment Precedence

The final runtime map is assembled in this order, with later entries winning:

1. configured tools, then query/bind-local tools;
2. bound Python call arguments;
3. auto-injected `@kedi.type` classes;
4. `kedi.configure(env=...)`;
5. active `kedi.context(env=...)` and query/bind-local `env`.

This means local environment values can intentionally replace caller
arguments:

```python
with kedi.context(env={"audience": "security reviewers"}):
    explain(topic="approvals", audience="beginners")
```

Inside Kedi, `audience` is `"security reviewers"`.

Tool names are protected separately: a function parameter that collides with a
registered tool raises `KediExecutionError`.

## `.env` and Environment Selection

`configure()` calls `dotenv.load_dotenv()` before resolving default backend
selection. Existing process environment values are not overwritten by the
default dotenv behavior.

When no explicit selection is passed:

- `KEDI_AGENT` selects an agent harness;
- otherwise `KEDI_ADAPTER` selects a framework, defaulting to `pydantic`;
- `KEDI_ADAPTER_MODEL` supplies the model.

`KEDI_AGENT` and `KEDI_ADAPTER` are mutually exclusive. `context()` does not
reload `.env`; it starts from active configuration.

## Reset Configuration

Reset the current context to Kedi's built-in defaults:

```python
kedi.reset_config()
```

The default selection metadata is the Pydantic framework with no explicit
model. Registered `@kedi.type` classes remain registered, and in-memory caches
remain intact. Use `kedi.clear_cache()` separately.

## Artifacts and Conversation State

```python
import kedi

kedi.configure(
    artifacts={"enabled": True, "threshold": "100kb", "ttl": "1h"},
)

with kedi.session() as conversation:
    first = create_report()
    second = review_report()
```

Artifacts keep large values out of model context and are enabled by default. A
session is opt-in and allows separate calls to share portable history and
artifact ownership. See [Artifacts and Sessions](artifacts-and-sessions.md).

## Invalid Combinations

Configuration fails early for:

- `adapter=` and `agent=` together;
- unknown adapter or harness names;
- an instance with missing or mismatched `kind`/`shortname`;
- both `KEDI_AGENT` and `KEDI_ADAPTER`;
- invalid approval values;
- invalid backend-specific options when the adapter is built or used.

Prefer explicit selection in production entry points. Environment selection is
useful for deployment overrides but makes the active backend less visible in
code.
