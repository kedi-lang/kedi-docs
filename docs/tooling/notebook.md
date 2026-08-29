# Local Notebook

Kedi Notebook is a local browser interface over `InteractiveSession`. It keeps
definitions, values, imports, profiles, conversation state, and artifacts
available across cells without concatenating or replaying earlier source.

## Install and Start

Install the optional browser package, then serve the notebook:

```bash
python -m pip install kedi-notebook
kedi notebook
```

The server listens on `127.0.0.1:8788` and opens
`http://127.0.0.1:8788/notebook/`. It is a localhost development tool, not a
multi-user hosted service.

The standalone entry point has the same behavior:

```bash
kedi-notebook
```

Install and start the published package in one command when `uv` is available:

```bash
uvx --from kedi-notebook kedi-notebook
```

Use `--host`, `--port`, `--cwd`, and `--no-open` to control serving. The working
directory is the base for relative Kedi imports and ordinary host filesystem
operations.

## Browser and Host Python

Browser execution through Pyodide 3.14 is selected by default. Embedded Python
runs in one persistent Web Worker, so Python values created by an earlier cell
remain available to later cells.

The worker starts loading when the notebook page opens. Runtime startup is
therefore paid during initial page load rather than deferred to the first cell.
The ready worker, imported modules, and browser-installed packages are reused
until the runtime is reset or the page is closed.

The local server also discovers compatible host Python installations. Select
one from the runtime menu when code should use packages installed in that
environment. Add or prioritize an exact executable while starting the server:

```bash
kedi notebook --python /opt/homebrew/bin/python3.11
kedi notebook --python ~/.pyenv/versions/3.12.4/bin/python --port 8899
```

`--python` is repeatable. In host mode the Kedi session stays in the notebook
server while embedded Python operations are sent to a persistent worker started
by the selected executable. Host execution is not sandboxed: it has the same
permissions and import paths as that Python process.

The runtime cannot be changed after the first Kedi cell runs. Start a new
runtime session before choosing another interpreter.

## Cell Semantics

Kedi cells execute in source order. A cell number represents the cell's current
position in the notebook, not its execution count. Rerunning a cell leaves that
number unchanged; adding, moving, or deleting cells recomputes affected
positions. A successful cell keeps its source editor and displays its output
directly below the source. It can be edited and run again; each rerun is a new
incremental execution against the current runtime state. The notebook does not
append an empty cell after execution. New cells are created only with an Add
cell control. Markdown cells render locally and never enter the Kedi runtime.

A cell whose first non-whitespace character is `!` is a terminal cell. You can
also create one explicitly from the cell type menu. Every non-empty line in a
multi-command terminal cell must begin with `!`.

In host mode, commands run in the notebook working directory. `!python` and
`!pip` always use the interpreter selected in the runtime menu. Other commands
run through the local shell, with the same permissions as the notebook server.
Standard output and standard error are streamed into the cell output while the
command is running. The terminal source remains editable and rerunnable after
the command finishes.

Browser mode has no operating-system shell. It supports:

- `!pip install <package>` and `!uv add <package>` through `micropip`;
- `!pip list`;
- `!echo <text>`;
- `!pwd`.

Browser `!uv add` is an installation convenience: it changes the live Pyodide
environment but does not edit `pyproject.toml`, lock files, or host project
state. Installed packages are immediately importable by later Kedi cells in
the same runtime session.

Notebook execution is intentionally non-transactional. State and external side
effects completed before an error remain visible after the cell fails. Running
any Kedi or terminal cell again creates a new execution attempt; Kedi does not
roll the session back or retry the source automatically.

Starting a new runtime clears live execution state and marks Kedi and terminal
source cells as unexecuted. Opening a notebook file also loads source only.
There is no hidden replay and no automatic run-all operation.

## Notebook Files

The Save command downloads a `.kedinb` JSON document containing the title,
cell kinds, and cell source. It does not serialize the Python worker or claim
that external side effects are reproducible. Opening the file restores cells as
unexecuted drafts.

Use `InteractiveSession.dump()` and `load()` from the Python API when a strict,
portable runtime snapshot is required. Snapshot creation rejects state it
cannot restore without replay.

## Editing

The active Kedi cell uses Monaco with Tree-sitter Kedi highlighting, embedded
Python highlighting, runtime diagnostics, and Kedi/Pyright hover. Press
`Shift+Enter` to run the active cell. Completed cells remain flat and readable;
only the current draft is presented as an editor surface.

The interface supports light and dark themes and keeps notebook drafts in local
browser storage between page reloads. Local draft recovery restores source, not
the previous runtime process.
