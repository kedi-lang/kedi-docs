# Subagents

Subagents let one profile delegate bounded, isolated work to explicitly declared
child profiles. Delegation is a typed tool surface, not an implicit ability to
spawn any profile.

## Declare Direct Children

```kedi
> profile: researcher:
    ###
    Investigate one focused question and report evidence.
    ###
    > adapter: pydantic
    > model: groq:qwen/qwen3-32b
    > system: Distinguish observed facts from inference.

> profile: coordinator:
    > adapter: pydantic
    > subagent: researcher
    > max_agents: 3

> use: coordinator
>> Delegate research when needed and synthesize [answer: str].
= <answer>
```

`coordinator` receives a `delegate_task` tool whose `subagent` argument permits
only `researcher`. Forward profile references are valid. Unknown children and
cycles in the delegation graph are rejected.

## Choose an Orchestration Mode

Profiles default to delegated orchestration. These two forms are equivalent:

```kedi
> profile: coordinator:
    > adapter: pydantic
    > subagent: researcher
```

```kedi
> profile: coordinator:
    > adapter: pydantic
    > subagent: researcher
    > workflow: delegate
```

Delegate mode exposes `delegate_task` and the lifecycle tools documented
below. The parent model regains control after each foreground child call.

Dynamic mode replaces those parent-facing orchestration tools with one
sequential `run_workflow(code: str)` tool:

```kedi
> profile: reviewer:
    ###
    Identify contradictions in supplied evidence.
    ###
    > adapter: pydantic

> profile: coordinator:
    > adapter: pydantic
    > subagent: researcher
    > subagent: reviewer
    > workflow: dynamic
    > max_agents: 8
```

The parent generates a restricted Python program. Direct child profiles become
documented async functions inside that program:

```python
import asyncio

research, review = await asyncio.gather(
    researcher(task="Collect evidence for the claim."),
    reviewer(task="Find contradictions in the supplied evidence."),
)
{
    "evidence": research["task_summary"],
    "review": review["task_summary"],
}
```

Each function accepts a required keyword-only `task` and optional
`final_schema`. Its dictionary result always contains `run_id`, `subagent`,
`task_summary`, and `final_result`. The workflow's final expression is returned
to the parent; bounded `print()` output is included only as diagnostic output.
Use ordinary `await` for dependent work and `asyncio.gather` for independent
fan-out.

The code executes in Monty. It cannot access host Python objects, adapters,
credentials, environment variables, files, network, processes, clocks, or
arbitrary imports. Child calls still run through Kedi's normal coordinator, so
both modes share profile isolation, safety ceilings, approvals, cwd, usage
accounting, concurrency, cancellation, and ancestor budgets.

Type and syntax checking precede child execution. A failed child becomes a
sanitized `RuntimeError` that workflow code may catch. Successful identical
calls are retained in a bounded retry-salvage table, allowing a corrected
workflow to reuse already-paid results. Budget exhaustion is terminal rather
than retryable. Canceling the workflow cancels and joins all pending children.
Dynamic workflows cannot nest, and only JSON-safe values cross the sandbox
boundary.

## Child Isolation

Every delegate call starts a fresh child conversation. The child receives its
own profile model, instructions, tools, MCP servers, skills, approval policy,
settings, and direct children. Parent tools and local variables do not leak.

The `task` must therefore be self-contained: include objective, relevant input,
constraints, and expected evidence. Do not assume the child can inspect the
parent's prompt or Kedi scope.

## `delegate_task`

The generated tool accepts:

| Argument | Meaning |
| --- | --- |
| `subagent` | One directly declared child profile |
| `task` | Self-contained instruction |
| `final_schema` | Optional JSON Schema for structured final output |
| `background` | Start without blocking when supported |

Without `final_schema`, Kedi calls the child's raw text invocation seam. With a
schema, Kedi asks for `task_summary` plus a schema-conforming result and
validates the returned object again.

Completed results contain `run_id`, `subagent`, `task_summary`, and
`final_result`. For text runs, the summary carries the child text and
`final_result` is `None`; structured runs place the validated payload in
`final_result`.

## Budgets and Usage Limits

`> max_agents: N` limits descendant starts for one profile invocation. Repeated
calls count separately. Failed and cancelled starts consume budget; requests
rejected before a start do not. A nested start consumes the immediate parent's
budget and every active ancestor budget.

Kedi imposes a hard ceiling of 100 descendant starts per invocation even if a
larger profile value is requested.

Per-child adapter-neutral defaults allow 8 model requests and 16 tool calls.
Runtime configuration can set input, output, and total token limits. Hard caps
are 50 requests, 100 tool calls, and 1,000,000 tokens per configured token
limit. Adapters must report/enforce their usage contract or fail rather than
silently exceed it.

## Foreground and Background

Foreground delegation blocks until the child completes and returns its result.
Use it when the parent cannot continue without the result.

With `background=True`, supported adapters immediately return a run handle.
Pydantic, Claude, Codex, and LangChain expose:

- `subagent_status(run_id)`
- `wait_subagent(run_id, timeout=...)`
- `cancel_subagent(run_id)`

`wait_subagent` may be called repeatedly for a completed result. Cancellation is
idempotent: only the first request changes state. Runtime timeout starts when
the child starts, not when the parent begins waiting.

DSPy supports blocking delegation only because its synchronous tool bridge does
not guarantee lifecycle calls on the same event loop.

## Fail-Closed Observation

A parent using fail-closed lifecycle semantics cannot return while background
work remains unobserved. It must successfully recover the result with
`wait_subagent`; merely checking status or issuing cancellation is not a
successful result observation.

Timeout, cancellation, unknown run IDs, child exceptions, invalid structured
results, unobserved work, and exhausted budgets surface as explicit failures.
Live tasks are process-local, and old terminal handles may expire after bounded
retention.

## Continue a Conversation

`continue_subagent(run_id, task, final_schema=None, background=False)` creates a
new run in the same bounded child conversation. Only the latest completed run
can be continued, the caller must own that conversation, and a conversation can
contain at most eight completed turns.

Kedi uses native provider resume state when an adapter supports it. Otherwise
it supplies bounded, previously validated turn results. Continuation does not
allow a different parent to take ownership.

## Safety Ceiling

Descendants may narrow but never widen inherited host safety:

- child `cwd` must remain inside the parent working-directory boundary;
- sandbox order is `read-only` < `workspace-write` <
  `danger-full-access`;
- a child may select the same or narrower sandbox, never a broader one;
- every ancestor approval policy remains a ceiling;
- parent edits are reclassified and checked by child policies.

A relative child `cwd` resolves beneath the parent. Invalid sandbox values,
escaping paths, and a child allow that conflicts with an ancestor deny are
rejected.

## Restart Persistence

Python callers can opt in with `compile_program(..., subagent_state_path=...)`
or `KediRuntime(..., subagent_state_path=...)`. Kedi atomically stores versioned
JSON containing terminal runs, validated results, bounded turns, and
JSON-serializable native resume state. The file and temporary replacement use
owner-only permissions.

After restart, completed results and valid continuations can be restored.
Pending or running records become failed with `InterruptedError`; Kedi does not
claim to resume an in-flight provider request. Invalid versions, malformed
records, unknown statuses, and non-serializable state fail loudly.

## Adapter Support

Pydantic AI, Claude Agent SDK, Codex App Server, LangChain, and DSPy support the
core child-execution seam. Background lifecycle is available where the adapter
can preserve asynchronous ownership. An unsupported adapter fails capability
validation instead of ignoring `> subagent:`.
