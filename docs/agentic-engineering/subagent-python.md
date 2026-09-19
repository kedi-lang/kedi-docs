# Embedding Subagent Programs in Python

The language declares the profile graph. Python supplies the adapter, host
tools, global values, resource limits, and runtime lifetime. It does not need
to reach into the coordinator or call an invented `kedi.subagent()` function.

## Compile, Execute, Close

This complete embedding uses a profile-only program with a raw text result.
Configure provider credentials before running it:

```python
import asyncio

from kedi import SubagentUsageLimits
from kedi.agent_adapter import PydanticAdapter
from kedi.lang import compile_program, parse_program

source = """
> profile: reviewer:
    > adapter: pydantic
    > system: Identify what the supplied evidence does not establish.

> profile: coordinator:
    > adapter: pydantic
    > subagent: reviewer
    > max_agents: 2

> use: coordinator
[answer] << Ask reviewer to assess: unit tests passed but integration tests were not run. Summarize uncertainty.
= <answer>
"""

limits = SubagentUsageLimits(
    request_limit=4,
    tool_calls_limit=6,
    input_tokens_limit=20000,
    output_tokens_limit=2000,
    total_tokens_limit=22000,
)
runtime = compile_program(
    parse_program(source),
    adapter=PydanticAdapter("openai:gpt-5.6-luna"),
    subagent_max_depth=2,
    subagent_max_concurrency=2,
    subagent_timeout_seconds=60,
    subagent_usage_limits=limits,
    subagent_state_path=".kedi-subagent-state.json",
)
try:
    print(runtime.run_main())
finally:
    asyncio.run(runtime.aclose())
```

This is a synchronous script. In an asynchronous application, keep execution
and cleanup under that application's lifetime; do not call `asyncio.run` inside
an already running event loop. The same subagent configuration is accepted by
`KediRuntime` and the public `kedi.context(...)` runtime context.

Input/total token budgets can require pre-request token counting from the model
integration. If the selected model cannot provide it, the child fails rather
than pretending that the limit was enforced. The local documentation fixture
implements token counting explicitly; a bare Pydantic `FunctionModel` does not.

The state path is optional. Exclude it from version control because task text,
results, and adapter continuation state may be sensitive. See
[Persistence](subagent-continuations.md).

## Inspect a Child From Its Tool

`current_subagent_execution()` returns a `SubagentExecutionContext` inside a
child execution, or `None` outside it. Its public fields are `run_id`, `profile`,
and `conversation_id`. It is task-local, so concurrent children do not share one
global "current child" value.

```python
from kedi import current_subagent_execution, tool

@tool(risk="read_only")
def execution_identity() -> dict[str, str]:
    """Return the identity of the child currently inspecting evidence."""
    child = current_subagent_execution()
    if child is None:
        raise RuntimeError("This tool requires a child invocation")
    return {
        "run_id": child.run_id,
        "conversation_id": child.conversation_id,
        "profile": child.profile.name or "",
    }
```

Pass this callable in `runtime_globals` and expose it with `> use:` in the
child's profile. Registration does not invoke it. The
[reviewed evidence example](reviewed-evidence.md) demonstrates a real child tool
using this API and verifies its identity against the delegation result.

## Keep the Surfaces Separate

| Surface | Intended caller |
| --- | --- |
| Profile directives | Kedi source declares permissions and graph structure. |
| `delegate_task`, lifecycle tools, `run_workflow` | The parent model through its advertised tools. |
| `compile_program`, `KediRuntime`, `kedi.context` | The embedding application. |
| `SubagentUsageLimits`, execution context helper | Application configuration and child-aware tools. |

The coordinator's underscored runtime methods are implementation details, not
an application API. A parent task's final text is not a substitute for observing
its required child outcomes and host effects.
