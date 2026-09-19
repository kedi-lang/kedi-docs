# Profiles

Profiles are named, reusable agent-state fragments. They make backend,
instructions, tools, approval, and delegation reviewable as one unit.

## Define a Profile

```kedi
> profile: reviewer:
    ###
    Reviews one change against repository evidence.
    ###
    > adapter: pydantic
    > model: groq:qwen/qwen3-32b
    > effort: medium
    > system: Cite the evidence used for every finding.
    > settings:
        temperature: 0.1
```

A profile body may contain `> adapter:`, `> agent:`, `> model:`, `> effort:`,
`> approval:`, `> system:`, `> settings:`, `> mcp:`, `> use:`,
`> subagent:`, `> max_agents:`, and `> workflow:`.

## Profile Documentation

When a `###` block is the first profile member, it becomes the profile
docstring. The LSP shows it in hover and subagent tool descriptions. A later
block remains an ordinary comment.

Document what task the profile owns, what evidence it should return, and any
important limitation. Child-agent descriptions depend on this text.

## Apply a Profile

Single-line `> use:` applies a profile when no procedure with that name exists:

```kedi
> use: reviewer

>> Review of the current change: [review: str].
= <review>
```

If a procedure and profile share a name, the procedure wins and is registered
as a tool. Avoid such collisions.

## Merge Rules

Applying a profile merges it into active state:

- scalar members such as backend, model, effort, system, approval,
  `max_agents`, and workflow mode replace earlier values when specified;
- settings merge by key;
- tools and subagents merge by name, with later bindings taking precedence;
- MCP servers append in order;
- omitted members inherit from the active state.

Direct directives after profile application can override profile members:

```kedi
> use: reviewer
> effort: high
```

The result uses the reviewer's backend, model, instructions, and settings with
high effort.

## Export and Import Profiles

Profiles are module values and can be explicitly exported:

```kedi
> profile: reviewer:
    > adapter: pydantic
    > model: groq:qwen/qwen3-32b

> export:
  reviewer
```

Imported profiles retain private tool and child-profile bindings needed by
their contract without flattening those dependencies into the importer's
procedure namespace. This lets a package expose a profile facade while keeping
helpers private.

## Forward References and Validation

A profile can name a child profile declared later. Kedi resolves the complete
profile graph and rejects unknown children and cycles.

Within one profile, framework and harness selection remain mutually exclusive.
Invalid backend kinds, duplicate or unknown members, invalid settings,
nonpositive `max_agents`, missing tools, and unsupported required capabilities
produce diagnostics or compile-time errors.

## Child Profiles

```kedi
> profile: coordinator:
    > adapter: pydantic
    > subagent: researcher
    > max_agents: 3
    > workflow: dynamic

> profile: researcher:
    > adapter: pydantic
    > system: Investigate one self-contained question.
```

Only directly listed children can be delegated to. `max_agents` bounds the
descendant work started by one parent invocation. Workflow mode defaults to
`delegate`; `dynamic` exposes one sandboxed Python orchestration tool. See
[Subagents](subagents.md) for lifecycle and safety rules.

## Choosing Profile Boundaries

Create a profile when a task needs a stable combination of behavior and
capabilities. Do not create one merely to alias a model string. Profiles should
be narrow enough that their tools, approvals, and child relationships can be
reviewed as a coherent security boundary.
