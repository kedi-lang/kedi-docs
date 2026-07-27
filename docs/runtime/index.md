# Runtime

The runtime turns Kedi source into a validated program, compiles declarations
and scopes, executes deterministic statements, and crosses the model boundary
only at explicit template or raw-invoke statements.

## Parse, Compile, Execute

1. Source loading merges the main file and supported companion artifacts while
   retaining a source map.
2. Parsing builds a structured program and reports syntax diagnostics.
3. Structural validation resolves directives, modules, declarations, and
   profile graphs.
4. Compilation creates runtime types, procedures, environments, and adapter
   state.
5. Execution evaluates top-level statements and the resulting dataflow.

`kedi parse` stops after parsing/validation. Normal `kedi file.kedi` continues
through compilation and execution.

## Value Environments

The runtime separates imports, prelude names, top-level values, procedure
frames, and lexical closures while presenting one predictable lookup model to
Kedi expressions. Native Python values stay native until a rendered text
boundary converts them to strings.

## Adapter Invocation

`>>` with output fields produces a typed schema call. `[name] << ...` produces
raw response text. `>>` without output fields still invokes the adapter and
discards its response. Assignments and Python expressions do not call a model.

## Execution Engines

Sequential execution is the default. Parallel mode schedules independent model
templates concurrently and discovers dependencies from value reads. Both modes
must produce identical values and failures.

## Caches and Artifacts

The Python API has in-memory parse and optional response caches. AI-generated
procedures use `.cache.kedi`; prompt optimization uses `.optimized.json`.
These are separate systems and are documented in [Caching](caching.md).

## Diagnostics

Parse errors include file, line, column, source snippet, and message. Runtime
errors carry Kedi procedure/statement frames and remapped embedded-Python
locations. Capability and adapter errors fail at the narrowest boundary that
can identify the unmet contract.
