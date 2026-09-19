# Tools and `> use:`

`> use:` either exposes a callable as an agent tool, applies a profile, or
enables the reserved project-skill surface. Resolution depends on its form.

## Expose a Procedure

```kedi
@lookup_release(version: str) -> str:
  ###
  Return release notes for one exact version.
  ###
  = `release_index[version]`

> use: lookup_release

>> Find release 1.4.0 and return [answer: str] summarizing it.
= <answer>
```

Kedi converts the procedure signature and docstring into a tool name,
description, JSON argument schema, and validated callable. Custom Kedi types
become nested schemas. Defaults remain optional arguments.

Write useful procedure docstrings before exposing a tool. The model must know
what the tool does, what its arguments mean, and what result it returns.

## Single-Line Resolution

For `> use: name`, Kedi resolves in this order:

1. a visible Kedi procedure;
2. a visible Python callable;
3. a profile;
4. the reserved name `skills`.

A procedure or callable therefore wins over a profile with the same name.
Avoid collisions even though the resolution is deterministic.

Backtick names are accepted for syntax symmetry:

```kedi
> use: `lookup_release`
```

They still resolve a name; this is not an arbitrary tool expression.

## Multiline Tool Lists

The block form always lists tools and never applies profiles:

```kedi
> use:
    lookup_release
    search_changelog
```

Every entry must resolve to a Kedi procedure or Python callable. Use this form
when a scope intentionally exposes several tools.

## Python Callables

A callable introduced by the prelude, imports, Python API, or configured
environment can be registered:

````kedi
```
def current_time(*, timezone: str) -> str:
    """Return the current time for one IANA timezone."""
    ...
```

> use: current_time
````

Python tool functions are invoked with keyword arguments. Complete annotations
and a docstring produce the best schema. Variadic or weakly typed signatures
reduce validation and model reliability.

## Tool Results

Tools return their native procedure or Python value. Framework adapters encode
that value into their tool-result protocol. A model-facing tool should return a
small, serializable object or text with enough context to interpret it.

Do not return open file handles, generators, process objects, or enormous
payloads. Use custom types or dictionaries for structured results and include
error context by raising a precise exception rather than returning an ambiguous
sentinel.

## Registration Scope

Tool frames are lexical:

```kedi
@outer_tool(query: str) -> str:
  = outer

> use: outer_tool

@inner() -> str:
  @outer_tool(query: str) -> str:
    = inner
  > use: outer_tool
>> Use the available tool and return [answer: str].
  = <answer>
```

The inner registration shadows only inside `inner`; leaving the procedure
restores the outer binding.

Profiles imported from modules retain their private bound tool implementations.
An unbound later registration with the same name deliberately restores normal
caller-scope lookup.

## Risk and Approval

Custom Kedi procedures and Python tools default to `mutating`. The Python API
can mark a tool `read_only`, `mutating`, or `sensitive`, and can attach an
argument-aware resolver that only elevates risk. Every risky invocation is
processed through the active approval policy before execution.

See [Approvals](approvals.md) for defaults and edited-argument validation.

## Adapter Support

Dynamic tool registration requires backend support. Framework adapters commonly
support Kedi tools; a harness may own a closed native tool surface and be unable
to accept external functions. The LSP reports a capability warning and the
adapter must not silently imply the tool is available.

Test each production profile with its actual backend. A syntactically valid
`> use:` is not evidence that every adapter can register it.
