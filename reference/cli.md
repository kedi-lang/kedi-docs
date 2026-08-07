# CLI Reference

## Invocation

```text
kedi SOURCE [OPTIONS] [PROGRAM_OPTIONS]
kedi -c SOURCE_TEXT [OPTIONS] [PROGRAM_OPTIONS]
kedi --idle [RUNTIME_BACKEND_OPTIONS]
kedi parse SOURCE
kedi SOURCE --parse
kedi install [PACKAGE.KEDI]
kedi add PACKAGE_NAME
kedi add git+https://github.com/OWNER/REPOSITORY.git
```

Use `kedi --help`, `kedi install --help`, or `kedi add --help` for the relevant
usage surface.

`-c/--command` supports direct execution and `--parse` only. It cannot be
combined with tests, evals, or optimization because those modes require a
source-file identity and adjacent artifacts.

## Runtime Backend Options

| Option | Default | Meaning |
| --- | --- | --- |
| `--adapter NAME` | `pydantic` | `pydantic`, `dspy`, `langchain`, `claude`, `codex`, or `acp` |
| `--adapter-model MODEL` | `groq:qwen/qwen3-32b` | Default model identifier |
| `--acp-command COMMAND` | unset | ACP stdio command; sets process-local `KEDI_ACP_AGENT_COMMAND` |

The historical option name is `--adapter`, but it accepts both framework
adapters and harnesses. In Kedi source and the Python API, `adapter` and `agent`
remain separate type-safe concepts.

## Interactive Mode

`kedi --idle` starts a process-local incremental session. It uses `+++` for a
new fragment and `...` for continuation input. Enter an empty continuation line
to execute a buffered multiline fragment. `:show <expression>` inspects a
value, `help` displays command help, and `:exit`, `Ctrl+C`, or `Ctrl+D` closes
the session.

Interactive mode accepts `--adapter` and `--adapter-model`. It rejects a source
file, `-c/--command`, program arguments, `--parse`, `--test`, `--eval`, and
`--optimize`. See [Interactive Execution](../runtime/interactive-execution.md)
for state persistence, native results, imports, history, and complete terminal
behavior.

## Validation and Generation Options

| Option | Meaning |
| --- | --- |
| `--test` | Run all `@test:` cases and stop |
| `--eval` | Run all `@eval:` suites and stop |
| `--optimize` | Optimize every eligible `> optimize:` span before continuing |
| `--no-cache` | Disable/remove `> auto:` codegen cache for this command |
| `--quiet` | Suppress codegen and GEPA progress |
| `-p`, `--parse` | Parse source without compiling or executing |

If both `--test` and `--eval` are given, tests run and return first. Avoid the
ambiguous combination and invoke each validation mode separately.

## Code Generation Options

| Option | Default |
| --- | --- |
| `--codegen-agent` | `pydantic_ai` |
| `--codegen-model` | `openrouter/minimax/minimax-m2.7` |
| `--codegen-retries` | `5` |

The alternate codegen agent is `mock`, intended for deterministic tests.
Retries count generation stages. Generated implementations are cached beside
the source as `SOURCE.cache.kedi`.

## Optimizer Options

| Option | Default | Meaning |
| --- | --- | --- |
| `--optimizer` | `mock` | `mock` or `gepa` |
| `--optimizer-model` | `openrouter/minimax/minimax-m2.7` | GEPA main model |
| `--optimizer-reflection-model` | same | GEPA reflection model |
| `--optimizer-max-metric-calls` | `100` | Optimization evaluation budget |
| `--optimizer-model-max-tokens` | `8000` | Main-model output limit |
| `--optimizer-reflection-model-max-tokens` | `32000` | Reflection output limit |
| `--optimizer-reflection-minibatch-size` | `3` | Examples before reflection |
| `--optimizer-max-validation-examples` | all | Explicit validation-set cap |
| `--optimizer-fresh` | false | Delete prior optimized state/checkpoints |

`--optimize` does not imply GEPA; the CLI default optimizer is `mock`.
`--optimizer-fresh` removes `.optimized.json`, `.optimized_scores.json`, and
`.gepa/` artifacts. It does not control codegen cache.

## Program Arguments

Unrecognized options after the source are parsed into the reserved `args`
binding:

```bash
kedi report.kedi --incident-id 42 --dry-run
```

```kedi
[incident_id: int] = `int(args.incident_id)`
[dry_run: bool] = `args.dry_run is True`
```

Hyphens normalize to underscores. `--key value` stores a string; a flag without
a value stores `True`. The first duplicate option wins. Non-option extra tokens
are ignored. Missing attributes read as `None`.

## Package Commands

`kedi install` accepts zero or one manifest path and defaults to
`./package.kedi`. `kedi add` accepts exactly one registry name or credential-free
GitHub `git+https` URL. Package subcommands reject ordinary runtime options.

## Exit and Output

Success exits `0`. Parse, compile, execution, validation, codegen, optimization,
package, and usage failures exit nonzero and render source-aware diagnostics
when available. Test mode exits `1` when any case fails; eval mode exits nonzero
for suite/configuration failures.

Ordinary top-level return values are written to stdout. Diagnostics and failed
operation details use stderr. `--quiet` does not hide final results or errors.
