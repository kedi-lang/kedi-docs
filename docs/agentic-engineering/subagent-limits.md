# Limits, Isolation and Safety

Delegation has several independent bounds. Increasing one does not increase
the others, and a profile cannot remove a runtime safety ceiling.

## Resource Limits

| Boundary | Default | Upper bound / behavior |
| --- | ---: | --- |
| Descendant starts per profile invocation (`max_agents`) | 100 when omitted | At most 100; oversized explicit budgets are rejected. |
| Active children (`subagent_max_concurrency`) | 4 | Clamped to 32; a full slot set rejects a new start rather than silently queueing it. |
| Child depth (`subagent_max_depth`) | 5 | Clamped to 5. |
| Child deadline (`subagent_timeout_seconds`) | 120 seconds | Positive values capped at 600; `None` disables this deadline. |
| Model requests per child | 8 | Capped at 50. |
| Tool calls per child | 16 | Capped at 100. |
| Input/output/total token limits | Unset | Each configured limit is capped at 1,000,000. |
| Completed turns per child conversation | 8 | Includes the initial run. |

The model/tool/token limits are configured through `SubagentUsageLimits`, not
`> settings: max_tokens`. The latter is a model-generation setting and does not
replace the whole-child budget. See [Python Embedding](subagent-python.md).

## What Consumes a Start

Repeated calls to one child count separately. Once admitted, failed and
cancelled work still consumes its start. A request rejected before admission
does not. Nested descendants consume the immediate parent's budget and every
active ancestor's budget.

For a parent with `max_agents: 3`, three completed calls exhaust the budget just
as three failed calls do. `max_agents` is not a concurrency setting: sequential
calls can exhaust it. Active concurrency is also bounded across root
invocations sharing the runtime, not just within one parent's prompt.

## Isolated Child Configuration

A child uses its own model, instructions, tools, MCP, skills, settings, and
direct-child list. It does not inherit the parent's conversation or local
variables. Put required data in the task or expose a deliberate read tool in
the child profile. Only directly declared children are callable; forward
references work, but unknown children and cyclic graphs fail.

This is agent-context isolation, not a Python security sandbox. Tools still
execute trusted host code and may share resources explicitly provided by the
embedding application.

## Host Safety Ceilings

Descendants can narrow inherited host permissions, not widen them:

- A child's `cwd` must stay within the parent's working-directory boundary.
- A relative child path resolves beneath that boundary.
- Sandbox order is `read-only` < `workspace-write` < `danger-full-access`.
- An ancestor deny cannot be replaced by a child allow.
- Parent argument edits are reclassified and checked under child policy.

An escaping working directory, invalid sandbox name, widened sandbox, or
conflicting permission decision fails before the protected operation. The
approval boundary does not intercept arbitrary I/O inside embedded Python.

## Failure Is Not an Empty Result

Depth, concurrency, start-budget, usage, and deadline failures are explicit.
Adapters must honor the usage contract rather than silently accept a limit they
cannot enforce. A parent should report missing evidence or recover within its
remaining budget, never reinterpret an exception as a negative/positive finding.

For waiting, observation, and cancellation behavior, see
[Foreground and Background Runs](subagent-lifecycle.md).
