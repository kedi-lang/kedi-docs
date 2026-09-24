# Subagents

Subagents let a profile delegate bounded, isolated work to explicitly declared
children. The parent chooses a task; the child runs with its own configuration
and returns evidence or a typed result. It is not an implicit ability to spawn
any profile or inspect the parent's local variables.

## Declare Direct Children

```kedi
> profile: investigator:
    ###
    Inspect supplied test evidence and identify what remains unverified.
    ###
    > adapter: pydantic
    > system: Separate observed results from missing evidence.

> profile: coordinator:
    > adapter: pydantic
    > subagent: investigator
    > max_agents: 3

> use: coordinator
[answer] << Ask investigator to assess: unit tests passed; integration tests were not run. Summarize release uncertainty.
= <answer>
```

Supply a model through the CLI or Python embedding. The parent sees
`delegate_task` with a child-name argument restricted to `investigator`.
The main program actually invokes the coordinator, but the model still chooses
whether to use its tool; configuration alone is not proof of delegation.

Forward profile references are valid. Unknown children and cycles are rejected.
For a graph A -> B -> C, A may call B but cannot call C unless A also lists C
directly. The first block comment in each profile supplies its description.

## Choose an Orchestration Mode

The default `> workflow: delegate` gives the model delegation and supported
lifecycle tools. `> workflow: dynamic` instead gives it `run_workflow(code)`
and exposes the direct children as async functions inside a sandbox.

Use delegate mode for one child result at a time. Use
[Dynamic Workflows](dynamic-workflows.md) for generated dependencies and fan-out.
Both modes preserve the same child boundaries, budgets, and approval ceilings.

## Start a Child in Kedi Code

Use native `> task` when the program, rather than the parent model, decides to
delegate. The header names one direct child and opens exactly one `>>` template
block. It starts the child immediately; `> await` waits at its own statement.

```kedi
> profile: reviewer:
    > adapter: pydantic
    > system: Review only the supplied change.

> profile: coordinator:
    > adapter: pydantic
    > subagent: reviewer

> use: coordinator

> task [review_job]: reviewer:
    >> The main issue in <change> is [issue: str].
    The recommended fix is [recommendation: str].

> await [review]: review_job
> show: `review.output.recommendation`
```

The two capture fields form a validated child output model. They do not create
parent-scope variables and do not invoke the parent model. The child receives
only the rendered task text, with its explicit `<change>` input. The child
profile must not also declare `> output:` when the task has captures. Without
captures, the child profile's output type applies; without either schema,
`review.output` is `None` and text is in `review.task_summary`.

You may start several tasks before awaiting any of them. `> await: review_job`
waits and propagates errors without binding a result. Repeated awaits observe
the same run. Unawaited work is cancelled and fails the enclosing invocation.
See [Foreground and Background Runs](subagent-lifecycle.md) and
[Python Embedding](subagent-python.md).

## Child Isolation

A child receives its own profile, not the parent's conversation, local values,
or tools. Include the objective, relevant data, constraints, and expected result
in `task`. See [Limits, Isolation and Safety](subagent-limits.md).

## `delegate_task`

The model-facing arguments are `subagent`, `task`, optional `final_schema`,
and `background` where supported. A successful foreground result contains
`run_id`, `subagent`, `task_summary`, and `final_result`.

A profile's `> output: Type` supplies the default result schema; an explicit
`final_schema` overrides it. With neither, `task_summary` carries text and
`final_result` is null. Read [Typed Child Results](subagent-results.md) for
schemas, validation, and examples.

## Budgets and Usage Limits

Total descendant starts, concurrent children, depth, per-child usage, and
deadlines are separate limits. Failed admitted starts still consume budget.
[Limits and Safety](subagent-limits.md#resource-limits) gives defaults, caps,
and the behavior of each boundary.

## Foreground and Background

Foreground calls wait for a completed result. Background calls return a handle
and require later observation. See
[Foreground and Background Runs](subagent-lifecycle.md) for exact tool results,
caller wait timeouts, cancellation, and cleanup.

## Fail-Closed Observation

A background handle is not evidence that work succeeded. Under fail-closed
policy, unresolved delegated work prevents the parent from completing as
though it had succeeded. Status inspection is not successful result observation.
See [Observe Before Returning](subagent-lifecycle.md#observe-before-returning).

## Continue a Conversation

`continue_subagent` starts a new run in the same bounded conversation. Only
the latest completed run can be continued, by its owning profile. See
[Continuations and Persistence](subagent-continuations.md).

## Safety Ceiling

Child working directories, sandboxes, and approvals cannot widen inherited
host permissions. This is distinct from the child's isolated prompt/tool
configuration. See [Host Safety Ceilings](subagent-limits.md#host-safety-ceilings).

## Restart Persistence

Persistence can restore completed results and bounded continuation state.
Interrupted live requests restore as failures, not resumed provider work.
See [Continuations and Persistence](subagent-continuations.md#opt-into-restart-persistence).

## Adapter Support

Pydantic AI, LangChain, Claude Agent SDK, Codex App Server, and DSPy support
child execution. Background lifecycle requires asynchronous ownership and is
not available through DSPy's bridge. Unsupported capabilities fail explicitly;
consult the [capability matrix](../reference/capability-matrix.md).

## Reading Path

1. [Typed Child Results](subagent-results.md): define what the parent consumes.
2. [Foreground and Background Runs](subagent-lifecycle.md): own and observe work.
3. [Limits, Isolation and Safety](subagent-limits.md): bound resources and authority.
4. [Continuations and Persistence](subagent-continuations.md): refine and restore.
5. [Dynamic Workflows](dynamic-workflows.md): compose child calls in code.
6. [Python Embedding](subagent-python.md): configure, inspect, and close a runtime.
7. [Reviewed Evidence Workflow](reviewed-evidence.md): execute the complete path.

The model-facing tools and native task statements use the same coordinator.
Python callers can use `runtime.subagents(parent="coordinator")`; coordinator
internals are not required application APIs.
