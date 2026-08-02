# Directive Index

## Agent Configuration

| Directive | Scope and contract |
| --- | --- |
| `> adapter: pydantic` | Select framework adapter: `pydantic`, `dspy`, or `langchain` |
| `> agent: codex` | Select harness: `claude`, `codex`, or `acp` |
| `> agent:` / `acp: command` | Select ACP and embed its stdio command |
| `> model: value` | Set plain or Python-evaluated model identifier |
| `> effort: level` | Set `minimal`, `low`, `medium`, `high`, `xhigh`, or `max` |
| `> system: text` | Replace active instructions; block form joins lines |
| `> settings:` | Merge adapter settings by key |
| `> artifacts:` | Configure scoped large-value storage and compact references |
| `> approval: allow`, `deny`, or handler | Set lexical tool approval policy |
| `> mcp:` | Append one MCP server specification |
| `> use: name` | Register a tool, apply a profile, or enable `skills` |
| `> use:` | Register an indented list of procedure/Python tools |

Framework and harness selection are mutually exclusive in one state. Literal
names are statically validated; backtick expressions defer validation to
runtime. Adapter settings unsupported by the selected backend are filtered or
rejected according to that adapter's contract.

`> artifacts:` fields are `enabled`, `store`, `path`, `threshold`, `ttl`,
`idle_ttl`, `preview_chars`, `read_max_chars`, `session_quota`,
`max_artifacts`, and `cleanup_interval`. The policy is lexical and enabled by
default. See [Tool Artifacts](../runtime/tool-artifacts.md).

`> mcp:` fields:

```kedi
> mcp:
    name: project_docs
    transport: stdio
    command: uv
    args: `["run", "docs-server"]`
    env: `{"LOG_LEVEL": "warning"}`
    cwd: .
```

Network transports use `url` instead of `command`/`args`. Valid normalized
transports are documented in [MCP Servers](../agentic-engineering/mcp.md).

## Profiles and Delegation

| Directive | Contract |
| --- | --- |
| `> profile: name:` | Define a reusable agent state |
| `> subagent: child` | Permit one direct child profile |
| `> max_agents: N` | Bound descendant starts for one invocation |
| `> workflow: delegate\|dynamic` | Select direct or sandboxed dynamic child orchestration |

A profile body may contain adapter or agent selection, model, effort, system,
settings, approval, MCP, tools, child profiles, and descendant budget. Scalar
members replace earlier values, settings merge by key, tools/children merge by
name, and MCP servers append.

`> subagent:`, `> max_agents:`, and `> workflow:` are profile members rather
than arbitrary runtime spawn commands. `delegate` is the default. `dynamic`
requires at least one direct child and exposes `run_workflow` instead of the
delegation lifecycle tools. Forward child references are valid; unknown
children, cycles, nonpositive budgets, duplicate workflow modes, and
unsupported adapter capabilities fail.

## Modules and Packages

| Directive | Contract |
| --- | --- |
| `> import: module/path` | Import all explicitly exported names |
| `> import: module/path:` | Import only listed exported names |
| `> export:` | Export listed top-level procedures, types, values, or profiles |
| `> export: *` | Export all public names not starting with `_` |
| `> package: name:` | Declare metadata in `package.kedi` only |

Imports are relative to their source file before bundled and installed-package
fallbacks. Selective imports bind names directly, not under a namespace.
Modules without an export directive expose nothing.

`> package:` supports `author`, `contact`, `version`, `source`, `python`,
`license`, and one `python_dependencies:` list. The manifest must contain no
executable statements.

## Tests and Evaluation

| Directive | Parent | Contract |
| --- | --- | --- |
| `> case: name:` | `@test:` | One Python assertion block |
| `> data: name:` | `@eval:` | Training/fallback-eval iterable |
| `> test_data: name:` | `@eval:` | Matching held-out iterable |
| `> metric: name(dataset):` | `@eval:` | One score function for the suite |

Cases run in source order and failures do not stop later cases. Eval suites
allow one metric. `--eval` prefers same-named test data, while optimization
always trains on data and validates with matching test data.

## Optimization and Generation

```kedi
@classify(text: str) -> str:
  > optimize: classification_prompt:
    Classify <text> as [label].
  = `label`

@generated_slug(value: str) -> str:
  > auto:
    Implement deterministic slug generation for <value>.
```

`> optimize: span_name:` owns one model template whose optimized artifact key is
the containing procedure plus span name. Every optimized procedure needs a
same-named eval suite with training data and a metric.

`> auto:` requests generated procedure implementation and tests. Codegen
uses a separate agent/model configuration and stores generated source in
`program.cache.kedi`.

Both directive bodies accept explicit `>>` or legacy bare template lines. The
entire body remains one newline-joined model call; the old syntax does not imply
one request per line.

## Placement and Capture

Agent directives at top level are captured by procedures defined afterward.
Directives in a procedure affect subsequent calls in that invocation and are
restored on exit. Profile application follows the same lexical rule.

Unknown directives, invalid placement, duplicate singleton members, malformed
blocks, or wrong directive kinds are errors rather than ignored configuration.
