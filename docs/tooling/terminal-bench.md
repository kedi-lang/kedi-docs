# Terminal-Bench 2.1

Kedi can run as an official Harbor custom agent for Terminal-Bench 2.1. The
integration owns the Kedi harness, terminal tools, non-interactive approval
policy, history, artifacts, and durable Kedi records. Harbor continues to own
the dataset, task containers, resource limits, timeouts, graders, task lock,
and job resume lifecycle.

## Install

Harbor requires Python 3.12 or newer:

```bash
python3.12 -m pip install 'kedi[terminal-bench]'
```

`KediAgent` installs the Pydantic AI provider runtime inside each task container,
separate from Harbor's host environment. During local development, passing a
wheel built from the exact Kedi commit is the most reproducible path.

## Freeze a Run

Build Kedi, then create the immutable manifest before observing benchmark
results:

```bash
uv build
kedi-terminal-bench manifest \
  --output runs/pilot.json \
  --harbor-revision 389bd4f8ce796ef4a97de4b62675021e262c8e76 \
  --model openrouter/openai/gpt-5.6-luna \
  --effort high \
  --kedi-wheel dist/kedi-0.4.0-py3-none-any.whl \
  --timeout-multiplier 1 \
  --agent-timeout-multiplier 1 \
  --verifier-timeout-multiplier 1 \
  --max-retries 0 \
  --task task-a \
  --task task-b
```

The manifest records:

- Terminal-Bench and Harbor versions;
- Harbor and Kedi revisions plus Kedi dirty state and the wheel SHA-256 or
  published package specification;
- adapter, model, effort, and non-secret model settings;
- exact task names, attempts, concurrency, environment, all Harbor timeout
  multipliers, and retry policy;
- history, provider prefix-cache placement, artifacts, compaction, and terminal
  limits.

Credential-like model setting keys and token values are rejected. Credentials
must be supplied through Harbor's provider environment.

Writing materially different settings to an existing manifest path is refused.
Its content digest excludes only the creation timestamp.

Agent setup and environment-build timeout multipliers are available alongside
the general, agent, and verifier controls. When retries are enabled, repeat
`--retry-include` and `--retry-exclude` to freeze the eligible Harbor exception
classes. `--retry-all-exceptions` explicitly clears Harbor's default exclusion
list.

## Run

Run the manifest with the recorded wheel:

```bash
kedi-terminal-bench run runs/pilot.json \
  --kedi-wheel dist/kedi-0.4.0-py3-none-any.whl \
  --jobs-dir runs/jobs \
  --job-name pilot-1
```

Use `--dry-run` to inspect the exact Harbor command without starting a job. If
the job directory and name are omitted, Kedi uses `./jobs` and a deterministic
name derived from the manifest digest.

Before a real job starts, Kedi checks that the selected `harbor` executable
reports the manifest's pinned Harbor version. A dry run only renders the
command and deliberately skips this executable check.

Kedi copies the manifest to `kedi-manifest.json` inside the Harbor job. Harbor's
generated `lock.json` records resolved task hashes, image digests, resources,
and grader inputs. Preserve both files with any reported result.

Resume an interrupted job through Harbor's native resume path:

```bash
kedi-terminal-bench resume runs/jobs/pilot-1
```

## Task Runtime

The benchmark profile is deliberately neutral to individual tasks. It tells the
agent to inspect before editing, ground effects in tool results, use exact argv
unless shell syntax is required, run focused verification, and stop when the
task is verified or no safe progress remains.

The task-container tool surface includes:

- sandbox-rooted filesystem reads, writes, directory creation, and structured
  patches;
- foreground argv and explicit Bash execution;
- background process start, status, bounded output reads, stdin, and stop;
- full capped process logs transported through Tool Artifacts;
- a verification state that becomes stale after later mutations.

Every process belongs to the trial session. Timeout, cancellation, output-limit
termination, and normal teardown terminate remaining process groups. Provider
credentials are stripped from terminal subprocess environments. Binary output
is exposed as base64 by bounded reads; text previews retain head, tail,
truncation state, byte counts, and the complete capped log path.

Benchmark approval never opens an interactive prompt. Read-only operations and
declared mutations inside the isolated task container are allowed. Sensitive
requests and tools outside the explicit benchmark allowlist are denied.

## History and Artifacts

Stateful history and file-backed artifacts are enabled by default. Large tool
results remain available without placing their complete payload into every
model request. Stateful history also applies Kedi's provider-native prefix-cache
placement where the selected provider supports it.

Use `--no-history` or `--no-artifacts` when preparing controlled comparisons.
Disabling history also disables Kedi-managed prefix-cache placement. Native
compaction is opt-in:

```bash
kedi-terminal-bench manifest \
  --output runs/compacted.json \
  --harbor-revision 389bd4f8ce796ef4a97de4b62675021e262c8e76 \
  --model openrouter/openai/gpt-5.6-luna \
  --task task-a \
  --compaction-mode native \
  --compaction-threshold 100000
```

The fixed profile does not enable subagents or dynamic workflows. Those
capabilities require separate experiments before they can become benchmark
defaults.

## Evidence and Failures

Each trial preserves:

- `kedi-result.json` with state, phase, policy, verification, and usage;
- `terminal-events.jsonl` with process lifecycle and verification changes;
- bounded command records and complete capped terminal stream files;
- file-backed artifact payloads;
- redacted error and cleanup diagnostics.

Terminal states distinguish completion, agent failure, integration failure,
timeout, and cancellation. The failure phase distinguishes setup, agent
execution, and teardown. Kedi usage and cache counters are projected into
Harbor's `AgentContext` after Harbor syncs the task-container logs to the host.

The integration does not include benchmark solutions or produce a score by
itself. Official graders remain the only source of task correctness.
