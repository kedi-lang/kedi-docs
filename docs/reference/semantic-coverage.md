# Semantic Coverage Map

This page owns the documentation coverage checklist for Kedi's public semantics.
Each item must be explained in a focused guide and represented in the compact
reference where applicable. It is a maintenance contract, not a substitute for
those explanations.

## Program Structure

- Source order, indentation, lexical scope, comments, and command-line arguments
- Single-file and multi-file execution

## Prompt Execution

- `>>` templates and multiline template blocks
- `<<` raw model invokes
- Variable, procedure, nested-call, and Python substitutions
- Structured outputs and native returns

## Values and Types

- Output fields, assignments, field descriptions, and multiple outputs
- Built-in, inline Python, generic, and custom types
- Runtime type validation and native-versus-rendered values

## Procedures

- Parameters, defaults, positional and named arguments
- Return annotations, direct returns, Python returns, and continuations
- Lexical closures and procedure-local scope

## Python Interop

- Inline expressions, multiline blocks, value-returning blocks, and side effects
- Prelude execution, Python globals, rebinding, and source-mapped exceptions

## Modules and Packaging

- Relative, nested, bundled, and installed module resolution
- Built-in errors, dependency checks, filesystem profiles, sandboxing, and examples
- Explicit, star, selective, and transitive exports
- Source-order collisions and one-time initialization
- Package metadata, local install, registry add, GitHub sources, and receipts
- Python compatibility, dependency metadata, path containment, and package security

## Agentic Engineering

- Framework adapters and agent harnesses
- Model, reasoning effort, system instructions, settings, and profiles
- Merge rules, precedence, validation, and capability metadata

## Tools, MCP, and Skills

- Procedure and Python tools, tool schemas, risks, and lexical registration
- Static and dynamic approvals, argument edits, and sensitive files
- Stdio, SSE, HTTP, and streamable HTTP MCP transports
- Project-local skills, listing, reading, validation, and on-demand loading

## Subagents

- Direct-child graphs, forward references, cycle checks, and descendant budgets
- Foreground and background runs, status, wait, cancellation, and continuation
- Structured final schemas, summaries, result validation, and conversation limits
- Restart persistence, interrupted runs, isolation, and adapter capabilities

## Runtime

- Parse, compile, and execute phases
- Dataflow dependencies, sequential execution, parallel execution, and snapshots
- Promise forcing, failure draining, thread safety, and adaptive job management
- Parse, response, codegen, and optimization caches
- Large-value artifact conversion, native lazy resolution, and compact model refs
- Memory/file stores, TTL, quotas, bounded reads, release, and history compaction
- Structured diagnostics, source maps, and debug exporters

## Testing, Evaluation, and Generation

- `@test:` blocks
- `@eval:` suites, training data, test data, metrics, expected values, and feedback
- `> optimize:` spans, GEPA configuration, budgets, checkpoints, and artifacts
- `> auto:` procedure generation, generated tests, retries, and codegen cache

## Python API

- `query`, `bind`, `configure`, `context`, and `reset_config`
- Type, tool, and approval decorators
- MCP, skills, environment precedence, backend overrides, and dynamic output types
- Artifact policy, conversation state, and explicit sync/async sessions
- Parallel contexts, promises, cache helpers, runtime objects, and executors

## Tooling and Integrations

- Run, command, parse, test, eval, optimize, install, and add CLI surfaces
- Environment variables and generated artifacts
- Pydantic AI, DSPy, LangChain, custom adapters, Codex, Claude, and ACP
- Language server, VS Code, Zed, browser, and playground execution

## Reference Maintenance Rules

- Every new parser construct updates Syntax and Directive indexes.
- Every new CLI option or Kedi-owned environment variable updates its reference.
- Every public `kedi` export updates the Python API inventory.
- Every adapter capability change updates both its adapter page and matrix.
- Every generated artifact and failure mode updates troubleshooting.
- Every executable snippet remains parser- or Python-AST-checked.
