# Local Notebook

Kedi Notebook is a local browser interface over `InteractiveSession`. It keeps
definitions, values, imports, profiles, conversation state, and artifacts
available across cells without concatenating or replaying earlier source.

## Install and Start

From a Kedi source checkout, resolve the optional browser package and start the
notebook in one command:

```bash
uv run --extra notebook kedi notebook
```

The notebook is currently a local-build surface. This command uses the checked
out Kedi source and `notebook` submodule rather than a published distribution.

The server listens on `127.0.0.1:8788` and opens
`http://127.0.0.1:8788/notebook/`. It is a localhost development tool, not a
multi-user hosted service.

The standalone entry point has the same behavior:

```bash
kedi-notebook
```

Use `--host`, `--port`, `--cwd`, and `--no-open` to control serving. The working
directory is the base for relative Kedi imports and ordinary host filesystem
operations.

Loopback serving needs no credentials. Binding another interface requires an
explicit access token:

```bash
kedi notebook --host 0.0.0.0 --token "$KEDI_NOTEBOOK_TOKEN"
```

The token is required by every notebook API and browser bridge request. The
server also rejects cross-origin API requests. This protects the host Python
and shell execution surface; it does not turn the notebook into a multi-user
service.

The server loads `.env` from `--cwd` at startup without overriding existing
process values. Use **Secret Manager** in the top bar for model names,
credentials, and other environment values that should not enter notebook
source. Values may be entered individually or imported from an explicit
`.env` path; relative paths resolve from `--cwd`. They are stored in
`~/.kedi/notebook/secrets.json` with user-only permissions, and the browser
receives only configured variable names. Updating a value resets the active
runtime so later cells inherit the new environment.

## Browser and Host Python

Browser execution through Pyodide 3.14 is selected by default. Embedded Python
runs in one persistent Web Worker, so Python values created by an earlier cell
remain available to later cells.

The worker starts loading when the notebook page opens. Runtime startup is
therefore paid during initial page load rather than deferred to the first cell.
The ready worker, imported modules, and browser-installed packages are reused
until the runtime is reset or the page is closed. Core Pyodide, Python standard
library, Micropip, and Pydantic files are shipped in the notebook wheel; this
startup does not require a Pyodide CDN. Packages installed later can still need
network access.

The local server also discovers compatible host Python installations. Select
one from the runtime menu when code should use packages installed in that
environment. Add or prioritize an exact executable while starting the server:

```bash
kedi notebook --python /opt/homebrew/bin/python3.11
kedi notebook --python ~/.pyenv/versions/3.12.4/bin/python --port 8899
```

`--python` is repeatable. The selected executable is a base interpreter, not an
environment that Kedi modifies directly. On first use, the notebook creates a
project-specific virtual environment under `~/.kedi/notebook/venvs`, installs
the active Kedi checkout and its dependencies, and starts the persistent worker
from that environment. Its stable `kedi-notebook-py...` name is derived from the
base interpreter and working directory, so later server runs reuse it. Set
`KEDI_NOTEBOOK_ENV_HOME` to choose another environment root. Host execution is
not sandboxed and has the notebook server process's filesystem permissions.

After selecting a host runtime, use the package action beside the runtime menu
to inspect installed distributions or install newline-separated Python
requirements. Pip output streams in the dialog. These packages persist in the
managed environment and are available to both Kedi cells and host terminal
cells. The selected base interpreter remains unchanged.

The runtime cannot be changed after the first Kedi cell runs. Start a new
runtime session before choosing another interpreter.

Use the square interrupt action while a Kedi or terminal cell is running. The
active worker is terminated and replaced, so the cell remains editable and
rerunnable while its previous live state is discarded. Host execution is also
limited to 120 seconds. Sessions with no activity expire after 30 minutes.

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
`!pip` always use the managed notebook environment. Other commands
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
source cells as unexecuted. There is no hidden replay and no automatic run-all
operation.

## Notebook Files

The Save command offers two `.kedinb` modes:

- **Just notebook** stores the title, cell layout, kinds, and source. Opening it
  restores unexecuted drafts.
- **Save progress** also stores retained outputs/results and a strict,
  pickle-free `InteractiveSession` snapshot containing the current KediEnv.
  Opening it restores that logical session when the next cell runs.

Neither mode includes Secret Manager or process environment values. A progress
save also does not serialize the Python worker or claim that external side
effects are reproducible. If live Kedi state cannot be represented without
changing its semantics, Save progress fails instead of writing a partial
snapshot.

Opening or creating a document asks before replacing unsaved work. Notebook
files are limited to 5 MB and 1,000 cells. Individual cell source is limited to
1 MB, and retained inline output is limited to 200,000 characters with an
explicit truncation marker.

`InteractiveSession.dump()` and `load()` expose the same strict snapshot
boundary to Python callers. Snapshot creation rejects state it cannot restore
without replay.

## Editing

The active Kedi cell uses Monaco with Tree-sitter Kedi highlighting, embedded
Python highlighting, live Kedi and Pyright diagnostics, runtime diagnostics,
Kedi/Pyright completion, hover, references, rename, signature help, and
definition navigation. A rename that reaches into an earlier executed cell is
rejected instead of applying only the active-cell edits. If Monaco cannot load, the
notebook keeps editing available with a plain multiline fallback. Completed
cells remain editable and display output below their source.

Markdown cells safely render headings, paragraph groups, ordered and unordered
lists, fenced code, blockquotes, emphasis, links, and separators. Raw HTML is
not rendered.

Keyboard commands:

- `Shift+Enter`: run the active cell;
- `Ctrl/Cmd+S`: download the notebook;
- `Ctrl/Cmd+Enter`: insert after the active cell;
- `Ctrl/Cmd+Shift+Enter`: append a cell;
- `Ctrl/Cmd+Backspace`: delete the active cell;
- `Ctrl/Cmd+ArrowUp` or `Ctrl/Cmd+ArrowDown`: move the active cell.

All visible cells remain editable; changing focus does not collapse them or
replace highlighted source with plaintext. The eye action explicitly hides a
cell and persists that state in drafts and notebook files. The interface uses a
single dark notebook theme and keeps source/layout drafts in local browser
storage between reloads. Local draft recovery does not restore runtime state.

Monaco currently uses pinned jsDelivr assets. The default Pyodide runtime and
its startup packages are vendored with Kedi Notebook. Host execution remains
available through the fallback editor when Monaco cannot load.
