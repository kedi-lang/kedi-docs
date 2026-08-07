# Built-In Modules

Kedi ships a small set of ordinary `.kedi` modules. They use the same explicit
exports, profiles, Python interop, tool metadata, and resolution rules as project
modules.

## Resolution and Shadowing

Import a bundled module by name:

```kedi
> import: filesystem:
  readonlyfs
  read_text_file
```

A sibling `filesystem.kedi` takes precedence over the bundled module. Use this
deliberately; an accidental same-name file changes the imported API.

## `errors`

The `errors` module exports `ModuleNotInstalledError`:

````kedi
> import: errors

```
raise ModuleNotInstalledError("httpx", required_by="HTTP reports")
```
````

The exception subclasses `ModuleNotFoundError` and formats singular or plural
missing package names. Use it when a feature has a clear optional Python
dependency.

## `require`

`require` exports a Python-callable helper:

````kedi
> import: require

```
require(["httpx", "pydantic"], required_by="Remote reports")
```
````

It checks import availability with Python's module discovery and returns `True`
when all names are present. Missing modules raise `ModuleNotInstalledError`.
It does not install packages or validate their versions.

## `filesystem`

The `filesystem` module exports:

| Name | Behavior |
| --- | --- |
| `read_text_file` | Read one UTF-8 file |
| `write_text_file` | Replace/create one UTF-8 file |
| `apply_patch` | Add, append, or exact-once replace text |
| `path_exists` | Check file or directory existence |
| `list_directory` | Return sorted direct child names |
| `create_directory` | Create a directory tree |
| `get_file_info` | Return basic path metadata |
| `filesystem` | Read/write agent profile |
| `readonlyfs` | Read-only agent profile |

```kedi
> import: filesystem

@load_readme() -> str:
  = `read_text_file("README.md")`
```

Paths resolve against the process working directory captured when the module
initializes. Every resolved path must remain beneath that root. `..`, absolute
paths, and symlinks cannot escape it.

`read_text_file` refuses files larger than 1,000,000 bytes.
`list_directory` refuses directories with more than 1,000 direct entries.
These are bounded agent-tool operations, not general bulk filesystem APIs.

Files named `.env` or beginning `.env.` are treated as secrets.
`read_text_file(path)` refuses them unless `secret_files=True`. In agent tool
use, that argument changes the call's risk classification so approval can be
required. Secret opt-in is not an authorization boundary by itself; the host
approval policy still decides.

`apply_patch("add", ...)` refuses an existing file. `update` requires a nonempty
`old_text` that occurs exactly once. `append` adds content. Prefer `apply_patch`
over whole-file writes for auditable agent edits.

The public profiles intentionally omit destructive deletion tools. `readonlyfs`
registers reads and metadata only; `filesystem` adds writes, patching, and
directory creation.

## `sandbox`

The optional `sandbox` module exports `execute_code` and a `sandbox` profile:

```kedi
> import: sandbox

[result: Any] = `execute_code("sum(values)", {"values": [1, 2, 3]})`
```

It requires the Python package `pydantic_monty`. Importing the module checks that
dependency immediately. `execute_code(code, inputs, fail_fast=True)` executes
with Monty and returns the native final result; the backtick expression preserves
that value. With `fail_fast=False`, an execution failure is returned as text.

This sandbox is for intentionally constrained generated code. It is not the
execution mechanism for ordinary Kedi Python blocks, which use the configured
Kedi executor.

## `this` and Example Modules

`this` is a bundled demonstration/easter-egg module whose import executes its
encoded output. It is not an application API.

Bundled examples such as `wordle` demonstrate profiles and tools and may require
optional packages. Treat them as examples rather than stable general-purpose
stdlib contracts. Production modules should import only the explicit built-in
surface they need.
