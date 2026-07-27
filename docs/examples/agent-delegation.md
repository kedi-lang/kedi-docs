# Agent Delegation

Subagents are explicit direct-child profiles. They are appropriate when a
coordinator needs an isolated conversation, tool set, model, or safety policy;
they are unnecessary for deterministic helper procedures.

## Foreground Structured Delegation

```kedi
> profile: researcher:
    ###
    Investigate one focused question and distinguish evidence from inference.
    ###
    > adapter: pydantic
    > model: groq:qwen/qwen3-32b
    > system: Return concise evidence and identify uncertainty.

> profile: coordinator:
    ###
    Split a request only when independent research is useful.
    ###
    > adapter: pydantic
    > model: groq:qwen/qwen3-32b
    > subagent: researcher
    > max_agents: 2

> use: coordinator

~ResearchAnswer(claim: str, confidence: float, evidence: list[str])

>> Ask researcher for a structured result, then return
[answer: ResearchAnswer].
= `answer`
```

Kedi gives `coordinator` a `delegate_task` tool. The model supplies
`subagent="researcher"`, a self-contained `task`, and optionally a
`final_schema`. The runtime validates structured child output before returning
it as `final_result`.

The child cannot see the parent's prompt or local Kedi values. Its task must
include the objective, necessary input, constraints, and expected evidence.

## Result Contract

A completed delegation returns:

| Field | Meaning |
| --- | --- |
| `run_id` | Stable handle for status, wait, cancellation, or continuation |
| `subagent` | Selected direct child |
| `task_summary` | Validated summary of the child turn |
| `final_result` | Schema-conforming payload, or `None` for text-only work |

Only children listed with `> subagent:` are selectable. Unknown children,
cycles, and budget exhaustion fail explicitly.

## Background Lifecycle

Pydantic, Claude, Codex, and LangChain coordinators can ask for
`background=True`. They then receive these additional tools:

```text
subagent_status(run_id)
wait_subagent(run_id, timeout=...)
cancel_subagent(run_id)
```

The parent must call `wait_subagent` before consuming the result or returning a
final answer. Merely checking status or cancelling does not count as successful
observation. Unobserved background work causes the parent to fail closed.

DSPy supports foreground delegation only. ACP does not expose the child
execution seam.

## Continue a Child Conversation

`continue_subagent(run_id, task, final_schema=None, background=False)` starts a
new run in the same bounded child conversation. Only the owner may continue it,
only the latest completed run is eligible, and a conversation is limited to
eight completed turns.

Use continuation when the next task depends on the child's prior context. Start
a fresh `delegate_task` for independent work; this avoids accidental context
coupling.

## Safety and Persistence

Children receive isolated profiles and may narrow, never widen, inherited
working-directory, sandbox, and approval ceilings. A declared
`> max_agents: N` bounds descendant starts for one parent invocation; the hard
runtime ceiling is 100.

Python embedders can persist terminal run state with
`compile_program(..., subagent_state_path=...)` or
`KediRuntime(..., subagent_state_path=...)`. Completed results and valid
continuations survive restart. In-flight records become failed after restart;
Kedi does not pretend to resume a request whose process ownership was lost.
