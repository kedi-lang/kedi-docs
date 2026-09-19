# Terminal REPL

The terminal submits complete fragments to an incremental runtime. For embedding, persistence restrictions, and failures, see [Incremental Execution](../runtime/interactive-execution.md).

## Terminal REPL

Start the terminal frontend without a source file:

```console
$ kedi --idle
 /\_/\
( o.o )
 > ^ <
Kedi 0.4.0 on darwin
Type "help" for interactive help, ":show" to inspect a value, ":multiline" for a multiline fragment, ":dump" to save, or ":exit" to leave.
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

### Explicit Multiline Input

Use `:multiline` when you want to compose a complete fragment before any part
of it executes:

```console
+++ :multiline
... [values: list[int]] = `[1, 2, 3]`
... > loop [value]: `values`:
...   `print(value)`
...
1
2
3
+++
```

Enter creates a new line. Press Enter again on the new empty line to submit the
fragment. Kedi keeps the editor open while the source has an open block,
delimiter, inline expression, or Python fence. `Alt+Enter` forces submission,
which is useful when you want the parser to diagnose incomplete source.

The multiline editor is one-shot: execution or an error returns to the normal
`+++` prompt. Terminal meta commands are recognized only at the primary prompt;
text such as `:exit` inside the editor is treated as Kedi source. The complete
fragment is executed once, so earlier lines cannot partially change session
state before submission. Terminal copy and paste preserves pasted newlines,
indentation, and blank lines without submitting the fragment. Press Enter twice
after pasting to execute it.

### Syntax Highlighting

Enable live Kedi and embedded-Python highlighting explicitly:

```bash
kedi --idle --highlight
```

Highlighting changes terminal presentation only. It does not start the Kedi
language server or add diagnostics, completion, or hover. Very large fragments
fall back to plain input to keep editing responsive. Highlighted input uses the
same `~/.kedi_history` file as ordinary and multiline input.

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
| `:multiline` | Compose and submit one complete multiline fragment |
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
kedi --idle --adapter pydantic --adapter-model openai:gpt-5.6-luna
```

Interactive mode does not accept a source file, `-c/--command`, program
arguments, `--parse`, `--test`, `--eval`, or `--optimize`.
`--record`, `--load`, and `--highlight` require `--idle`.
