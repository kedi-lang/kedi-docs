# Interactive Execution

Interactive execution evaluates complete Kedi fragments against one persistent,
process-local runtime. It is useful for terminal exploration, notebooks,
debuggers, and hosts that need to submit code incrementally without replaying
earlier cells.

Kedi exposes the same execution model through two surfaces:

- `kedi.interactive()` creates a session for Python hosts.
- `kedi --idle` starts a terminal REPL backed by that session.

Normal file execution is unchanged. Interactive execution is an additional
surface, not a replacement for `compile_program(...).run_main()`.

## Python API

Create sessions with `kedi.interactive()` and execute one complete fragment at
a time:

```python
import kedi


with kedi.interactive() as session:
    session.execute("[base: int] = `40`")
    session.execute(
        """
@add_two() -> int:
    = `base + 2`
""".strip()
    )
    assert session.execute("= `add_two()`") == 42
```

The second and third fragments can read declarations and values created by the
first fragment. Values, procedures, types, imports, profiles, directives,
conversation state, and artifacts remain available until the session closes.
Earlier fragments are neither concatenated nor executed again.

### Results

`InteractiveSession.execute()` uses the same native-value boundary as
`KediRuntime.run_main()`:

- a native return such as ``= `value` `` returns the underlying Python value;
- a rendered return such as `= <value>` returns rendered text;
- a fragment without a top-level return returns `None`.

This distinction means an `int` remains an `int`; interactive execution does
not implicitly stringify results.

### Source Identity and Imports

Every fragment gets a unique source name such as `<interactive:1>`. That name
appears in parse diagnostics and Kedi stack traces. A host can supply a more
useful identity:

```python
with kedi.interactive(cwd="examples/cells") as session:
    result = session.execute(
        "> import: helpers\n= `answer`",
        source_name="answer.kedi",
    )
```

A real `source_name` becomes the base for relative imports. Synthetic names use
the session's `cwd`, which defaults to the process working directory. Source
names must be unique within a session so diagnostics cannot ambiguously refer
to two fragments.

### Configuration

`kedi.interactive()` accepts the same model, adapter or agent, system prompt,
effort, settings, tools, environment, MCP, approval, skills, artifacts,
conversation, and parallel-execution inputs as the other high-level Python API
surfaces. It also accepts an executor, execution engine, `cwd`, and subagent
limits.

Configuration is resolved when the session is created. The session owns the
runtime assembled from that configuration; later calls to `kedi.configure()` do
not rebuild an existing session.

### Durable Snapshots

`kedi.dump_session(session, path)` writes a pickle-free snapshot only when the
complete logical session can be restored without replaying executable cells.
Restore it with `kedi.load_session(path)`. The corresponding
`InteractiveSession.dump()` and `InteractiveSession.load()` methods expose the
same operations:

```python
from pathlib import Path

import kedi


snapshot = Path("work.kedi-state")
with kedi.interactive() as session:
    session.execute("[base: int] = `40`")
    session.execute(
        """
@add_two() -> int:
    = `base + 2`
""".strip()
    )
    kedi.dump_session(session, snapshot)

with kedi.load_session(snapshot) as session:
    assert session.execute("= `add_two()`") == 42
```

The operation is strict and all-or-nothing. Kedi validates all fragments,
environment values, active profile state, conversation state, and artifacts
before publishing the file. `SessionDumpError` reports every unsupported
boundary found during preflight. It never silently removes a binding, and an
existing destination remains untouched when validation fails. Successful
writes use a mode-`0600` temporary file, `fsync`, and atomic replacement.

The snapshot value codec preserves scalar values, bytes, complex and decimal
numbers, UUIDs, dates and times, paths, regular expressions, standard
containers with typed keys, and source-backed Kedi type instances. Kedi stores
fragment sources and digests so procedures, types, profiles, tracebacks, and
source identities can be rebuilt before native values are installed. The
document integrity hash, format version, and Kedi version are checked on load.

Kedi rejects state that cannot be restored with equivalent semantics:

- arbitrary Python callables, generators, open resources, concurrency
  primitives, tasks/futures, classes, and unknown object instances;
- shared or cyclic mutable object graphs;
- dynamic approval handlers, process-bound tool/profile bindings, active
  artifacts, conversation turns, or adapter-native continuation state;
- imports, inline Python preludes, executable type defaults, and runtime-scoped
  declarations that would require old code to run during load.

Adapters and executors are not serialized. Supply them when the restored
session needs those infrastructure dependencies:

```python
session = kedi.load_session(
    "work.kedi-state",
    adapter=adapter,
    executor=executor,
)
```

`load_session()` accepts a keyword-only `session_type=` factory and defaults
to `InteractiveSession`. An `InteractiveSession` subclass can be supplied when
the restored object needs application-specific behavior.

Loading compiles source-backed declarations but never re-executes prior
assignments, templates, tools, LLM requests, filesystem writes, or other
top-level side effects.

### Lifecycle and Failure Semantics

Use the context manager form when possible. `close()` is idempotent and releases
session-owned resources. Executing after close, closing during execution, or
starting concurrent or re-entrant `execute()` calls raises an error.

The execution model is synchronous and non-transactional. If a fragment fails:

- it is not retried automatically;
- state committed before the failure remains visible;
- completed external side effects are not rolled back;
- the source-aware exception identifies the failed fragment.

Interactive fragments reject package metadata, export directives, and
`@test`/`@eval` suites. Those constructs describe complete files, packages, or
validation surfaces rather than one incremental cell.

## Terminal REPL

Start the terminal frontend without a source file:

```console
$ kedi --idle
 /\_/\
( o.o )
 > ^ <
Kedi 0.4.0 on darwin
Type "help" for interactive help, ":show" to inspect a value, ":dump" to save, or ":exit" to leave.
+++ [base: int] = `40`
+++ @add_two() -> int:
...     = `base + 2`
...
+++ :show `add_two()`
42
+++
```

`+++` is the primary prompt. `...` indicates that the current fragment needs
more input. The REPL enters continuation mode for:

- a block header ending in `:`;
- an open parenthesis, bracket, or brace;
- an open inline-Python expression or Python fence;
- an explicit line continuation ending in `\`.

Press Tab to insert indentation at the continuation prompt. Submit an empty
continuation line to execute the buffered fragment exactly once. A complete
single-line fragment executes immediately.

### Inspecting Values

`:show <expression>` is a terminal-only meta command. It is not valid Kedi
source and cannot appear in a `.kedi` file.

The command evaluates any expression accepted on the right-hand side of a Kedi
return. For example:

```console
+++ :show <name>
'rendered value'
+++ :show `items[0]`
42
```

The first form uses Kedi rendering; the second preserves and displays the native
value with `repr()`. This provides top-level inspection without making bare
top-level substitutions legal in normal Kedi programs.

### Commands, History, and Exit

The terminal understands these commands:

| Input | Behavior |
| --- | --- |
| `help` or `help()` | Show concise interactive help |
| `:show <expression>` | Evaluate and print one value |
| `:dump` | Save the complete restorable session and print its resume command |
| `:exit` | Close the session |
| `Ctrl+C` | Exit silently, including during active execution |
| `Ctrl+D` | Close the session at the input prompt |

Python's `exit()` and `quit()` have no special terminal meaning. `:exit` is the
only textual exit command.

The first `:dump` writes an atomic snapshot under `~/.kedi/sessions`; later
dumps in the same REPL update the same file. Kedi prints the exact resume
command after every successful dump:

```console
To resume session, run -- kedi --idle --load <session_path>
```

Use `--record` to dump automatically before `:exit`, `Ctrl+C`, `Ctrl+D`, or a
`SystemExit` raised by inline Python. Recording happens before session resources
close and preserves the `SystemExit` status. `--load` restores a snapshot and
continues recording changes to that same path:

```bash
kedi --idle --record
kedi --idle --load ~/.kedi/sessions/idle-20260826T120000-ab12cd34.kedi-state
```

Readline history is stored in `~/.kedi_history`. Set `KEDI_HISTORY` to use a
different path:

```bash
KEDI_HISTORY="$HOME/.local/state/kedi/history" kedi --idle
```

Adapter selection remains available:

```bash
kedi --idle --adapter pydantic --adapter-model openai:gpt-4o-mini
```

Interactive mode does not accept a source file, `-c/--command`, program
arguments, `--parse`, `--test`, `--eval`, or `--optimize`.
`--record` and `--load` require `--idle`.

## Choosing a Surface

Use `kedi --idle` for direct terminal exploration. Use `kedi.interactive()` when
an editor, notebook, debugger, or application owns input, output, source names,
and lifecycle. Use ordinary file execution when a complete program should be
repeatable from source as one unit.
