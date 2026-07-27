# Errors and Debugging

Kedi separates parse diagnostics, structural/type failures, execution traces,
and backend errors so the reported location stays near the violated contract.

## Parse Diagnostics

Malformed syntax produces `KediParseError` with one or more diagnostics:

```text
Kedi parse error:

  File "workflow.kedi", line 4, column 3
  ...
  ^

Kedi error: ParseError
  unexpected source at top level
```

Use `kedi parse workflow.kedi` for parse/validation without a model call.
The LSP exposes the same source-aware diagnostics while editing.

## Structural and Type Errors

After syntax, Kedi validates duplicate declarations, imports/exports, profile
graphs, directives, package manifests, type names, default ordering, and known
adapter capabilities. These failures prevent invalid execution state.

Runtime type errors preserve the violated boundary: parameter, return, output,
assignment, custom field, or edited tool argument. Values are not silently
coerced to make the error disappear.

## Execution Errors

Runtime exceptions are wrapped as `KediExecutionError` with Kedi frames such as
top-level program, procedure, template, assignment, return, Python block, and
type expression. Specialized subclasses also behave as Python `TypeError`,
`ValueError`, `KeyError`, or `NameError` where appropriate.

The original exception remains available to Python callers. CLI rendering shows
the concise Kedi stack instead of exposing internal virtual filenames.

## Embedded Python Mapping

Every inline expression and fenced block receives a unique virtual Python
filename. Kedi records its origin and maps `SyntaxError` and traceback lines
back to the real `.kedi` file, procedure, block, Kedi line, Python line, source
snippet, and caret.

Nested embedded-Python calls can show both call and error snippets. Do not catch
an exception merely to regain a source location; uncaught propagation preserves
the richer Kedi trace.

## Source Maps and Companion Files

Source loading retains each physical document. Errors in imported modules,
generated cache blocks, optimization/test companions, and merged source can
point to their actual file instead of a concatenated virtual line.

When source is compiled from memory, pass a meaningful `source_path` or source
map through the Python API to improve relative imports and diagnostics.

## Adapter and Capability Errors

Backend selection, credentials, model availability, unsupported schema formats,
tool/MCP capability gaps, protocol failures, approval denials, and provider
errors surface at the adapter boundary. Kedi does not convert these into empty
outputs.

Differentiate a capability diagnostic from a provider outage: the first means
the profile contract cannot be represented; the second means a valid request
failed operationally.

## Executor Debug Events

Executors can emit `ExecutorDebugEvent` records with UTC timestamp, executor,
step, event name, and sanitized payload fields such as code, inputs,
environment, arguments, result, output, and error.

Attach a `MarkdownDebugExporter` from Python:

```python
from kedi import MarkdownDebugExporter
from kedi.executors import DefaultExecutor

exporter = MarkdownDebugExporter("runtime-debug.md")
executor = DefaultExecutor(debug_exporter=exporter)
```

When no path is supplied, the default name is
`<normalized-name>_debug_export_<UTC timestamp>.md` in the current directory.

“Sanitized” here means values are converted to representable forms; it is not
secret redaction. Debug exports may contain prompts, code, env values, tool
arguments, and outputs. Store them securely, inspect before sharing, and delete
when no longer needed.

## Optimization Debugging

`KEDI_DEBUG_OPTIMIZED=1` prints optimized-prompt loading and injection details
to stderr. Use it for stale/missing `.optimized.json` diagnosis, not as a
general runtime trace switch.

## Concurrent Failures

Parallel execution drains already-scheduled calls. The first failure is raised;
additional concurrent failures are logged so they are not silently lost. When
debugging, reproduce in sequential mode for simpler timing, but treat any
sequential/parallel result difference as a runtime bug.

## Debugging Order

1. Run `kedi parse`.
2. Resolve LSP structural and capability diagnostics.
3. Run sequentially and inspect the Kedi stack.
4. Verify the active profile/model/tool surface.
5. Enable a scoped executor debug export only if the trace is insufficient.
6. Re-enable parallelism and validate equivalence.
