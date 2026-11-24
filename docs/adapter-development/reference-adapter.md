# Reference Adapter

Every page in this section extends one adapter, `ChatAdapter`, that connects
Kedi to a chat backend with tool calling and JSON Schema output. The code on
these pages is complete: the documentation test suite assembles the
`python title="..."` blocks into modules and runs them through real Kedi
programs.

The adapter is about 170 lines. It implements:

| Protocol or attribute | Defined in | Section |
|---|---|---|
| `kind`, `shortname`, `capabilities` | `kedi.agent_adapter.AgentAdapter` | [Overview](index.md) |
| `invoke`, `invoke_sync`, `produce`, `produce_sync` | `kedi.agent_adapter.AgentAdapter` | [Calls](#calls) |
| `default_model`, `profile_override` | `kedi.agent_adapter.meta.SupportsProfileOverride` | [Profiles](#profiles) |
| `tool_scope`, `register_tool` | `kedi.agent_adapter.SupportsToolRegistration` | [Tools](#tools) |

Later pages add subagents, conversations, and the other optional protocols to
the same class.

## The Backend

The backend stands in for your provider SDK. It receives one rendered request
and returns one reply: text, a decoded JSON value, or tool calls.

```python title="backend.py"
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Reply:
    text: str | None = None
    data: Any = None
    tool_calls: tuple[ToolCall, ...] = ()
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class BackendRequest:
    model: str
    system: str | None
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] = field(default_factory=list)
    output_schema: dict[str, Any] | None = None


class Backend(Protocol):
    async def complete(self, request: BackendRequest) -> Reply: ...
```

A real backend translates `BackendRequest` into its provider call: `system`
becomes the system message, `messages` the conversation, `tools` the
provider's tool declarations, and `output_schema` its structured-output or
response-format option.

## The Adapter

```python title="chat_adapter.py"
from __future__ import annotations

import inspect
import json
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from pydantic import TypeAdapter
from pydantic_core import to_jsonable_python

from kedi.agent_adapter import AdapterCapabilities, AgentAdapterKind, ToolSpec
from kedi.agent_adapter.execution import run_sync
from kedi.agent_adapter.invocation import InvocationUsage, report_invocation
from kedi.agent_adapter.output_schema import build_output_model
from kedi.agent_profile import AgentProfile, AgentProfileOverrideUnsupported

from backend import Backend, BackendRequest, Reply, ToolCall


class ChatAdapter:
    kind: AgentAdapterKind = "agent-framework"
    shortname = "chat"
    capabilities = AdapterCapabilities(
        supports_structured_output=True,
        supports_tool_registration=True,
        supports_artifacts=True,
        supports_profile_override=True,
        supports_model_override=True,
        supports_effort=False,
        supports_settings=False,
        supports_mcp=False,
    )

    def __init__(self, backend: Backend, *, model: str, max_steps: int = 8) -> None:
        self._backend = backend
        self._model = model
        self._max_steps = max_steps
        self._profiles: ContextVar[tuple[AgentProfile, ...]] = ContextVar(
            f"chat_profiles_{id(self)}", default=()
        )
        self._tools: ContextVar[tuple[ToolSpec, ...]] = ContextVar(
            f"chat_tools_{id(self)}", default=()
        )
```

The `ContextVar`s give every concurrent call, thread, and subagent its own
profile stack and tool set. Kedi runs template blocks in parallel and children
in background tasks, so state stored on `self` would leak between them.

### Profiles

```python title="chat_adapter.py"
    def default_model(self) -> str | None:
        return self._model

    @property
    def active_profile(self) -> AgentProfile:
        stack = self._profiles.get()
        return stack[-1] if stack else AgentProfile.empty()

    @contextmanager
    def profile_override(self, profile: AgentProfile) -> Generator[None, None, None]:
        unsupported = [
            name
            for name, present in (
                ("effort", profile.effort is not None),
                ("settings", bool(profile.settings)),
                ("mcp", bool(profile.mcp_servers)),
            )
            if present
        ]
        if unsupported:
            raise AgentProfileOverrideUnsupported(
                f"{self.shortname} does not support profile fields: {', '.join(unsupported)}"
            )
        token = self._profiles.set((*self._profiles.get(), profile))
        try:
            yield
        finally:
            self._profiles.reset(token)
```

Kedi enters `profile_override(profile)` around every call. Once an adapter
implements it, Kedi no longer rejects profile fields on the adapter's behalf,
so the adapter must refuse what it cannot honor. `profile.system` needs no
handling here: Kedi already renders it into `instructions`.

### Tools

```python title="chat_adapter.py"
    @contextmanager
    def tool_scope(self, tools: Sequence[object] = ()) -> Generator[None, None, None]:
        token = self._tools.set(tuple(tool for tool in tools if isinstance(tool, ToolSpec)))
        try:
            yield
        finally:
            self._tools.reset(token)

    def register_tool(self, tool: ToolSpec) -> None:
        self._tools.set((*self._tools.get(), tool))

    async def _execute(self, tools: dict[str, ToolSpec], call: ToolCall) -> str:
        tool = tools.get(call.name)
        if tool is None:
            return json.dumps({"ok": False, "error": f"Unknown tool {call.name!r}"})
        try:
            result = tool.fn(**call.arguments)
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:  # the model sees the failure and may recover
            return json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        return json.dumps({"ok": True, "result": to_jsonable_python(result, fallback=str)})

    @staticmethod
    def _declaration(tool: ToolSpec) -> dict[str, Any]:
        return {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.json_schema or {"type": "object", "properties": {}},
        }
```

`tool.fn` is already wrapped by Kedi. Calling it applies approval policy,
required-tool tracking, artifact admission, and telemetry; a denied call raises
`ToolApprovalDenied` like any other tool failure. Some Kedi tools are
coroutines (subagent delegation is one), so always await an awaitable result.

### Calls

```python title="chat_adapter.py"
    async def _run(
        self,
        *,
        prompt: str,
        instructions: str | None,
        output_schema: dict[str, Any] | None,
        history: Sequence[dict[str, Any]] = (),
        max_requests: int | None = None,
    ) -> tuple[Reply, list[dict[str, Any]]]:
        messages = [*history, {"role": "user", "content": prompt}]
        tools = {tool.name: tool for tool in self._tools.get()}
        steps = self._max_steps if max_requests is None else min(self._max_steps, max_requests)
        for _ in range(steps):
            reply = await self._backend.complete(
                BackendRequest(
                    model=self.active_profile.model or self._model,
                    system=instructions,
                    messages=list(messages),
                    tools=[self._declaration(tool) for tool in tools.values()],
                    output_schema=output_schema,
                )
            )
            report_invocation(
                InvocationUsage(
                    requests=1,
                    tool_calls=len(reply.tool_calls),
                    input_tokens=reply.input_tokens,
                    output_tokens=reply.output_tokens,
                    total_tokens=reply.input_tokens + reply.output_tokens,
                )
            )
            if not reply.tool_calls:
                content = reply.text if output_schema is None else json.dumps(reply.data)
                messages.append({"role": "assistant", "content": content})
                return reply, messages
            messages.append(
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"id": call.id, "name": call.name, "arguments": call.arguments}
                        for call in reply.tool_calls
                    ],
                }
            )
            for call in reply.tool_calls:
                content = await self._execute(tools, call)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": content})
        raise RuntimeError(f"{self.shortname} stopped after {steps} model requests")

    async def invoke(self, *, prompt: str, instructions: str | None = None, **_: Any) -> str:
        reply, _messages = await self._run(
            prompt=prompt, instructions=instructions, output_schema=None
        )
        if reply.text is None:
            raise RuntimeError("The backend returned no text")
        return reply.text

    async def produce(
        self,
        *,
        template: str,
        output_schema: dict[str, Any] | None = None,
        output_type: Any = None,
        instructions: str | None = None,
        **_: Any,
    ) -> Any:
        if output_schema is not None:
            schema = build_output_model(output_schema).model_json_schema()
        else:
            schema = TypeAdapter(output_type).json_schema()
        reply, _messages = await self._run(
            prompt=template, instructions=instructions, output_schema=schema
        )
        return reply.data

    def invoke_sync(self, **kwargs: Any) -> str:
        return run_sync(self.invoke(**kwargs))

    def produce_sync(self, **kwargs: Any) -> Any:
        return run_sync(self.produce(**kwargs))
```

The rules that matter:

- **One loop.** The synchronous entry points use `run_sync` from
  `kedi.agent_adapter.execution`, never `asyncio.run`. Kedi runs all
  overlapping model work on one shared event loop, and background subagents
  started by a tool call keep running on it after the call returns. A private
  loop would close under them. See [Concurrency](../runtime/concurrency.md).
- **Kedi's text, unchanged.** `instructions` is the system message, the prompt
  is the user message, and the JSON Schema comes from `build_output_model`, so
  the field descriptions Kedi adds reach the model.
- **Usage after every request.** `report_invocation` feeds subagent usage
  limits, request-size reservations, telemetry, and checkpoint usage events.
  A subagent limit that is exceeded raises from inside `report_invocation`;
  let that exception propagate. Run budgets (`> budget:`) need one more call
  before each request; see [Budgets and Usage](budgets.md).
- **Kedi validates.** `produce` returns the decoded value. Kedi checks it
  against the requested type, converts it, and fails the call if a field is
  missing.

## Running It

```python title="run_chat.py"
import asyncio
from collections.abc import Callable

from kedi.lang import compile_program, parse_program

from backend import BackendRequest, Reply
from chat_adapter import ChatAdapter


class ScriptedBackend:
    """A test backend: each request is answered by a function of that request."""

    def __init__(self, answer: Callable[[BackendRequest], Reply]) -> None:
        self.answer = answer
        self.requests: list[BackendRequest] = []

    async def complete(self, request: BackendRequest) -> Reply:
        self.requests.append(request)
        return self.answer(request)


def run(source: str, backend: ScriptedBackend) -> object:
    runtime = compile_program(parse_program(source), adapter=ChatAdapter(backend, model="m1"))
    try:
        return runtime.run_main()
    finally:
        asyncio.run(runtime.aclose())
```

`runtime.aclose()` releases the runtime's resources after the run; it is not
model work, so `asyncio.run` is correct there.

A template capture with a tool:

```python title="run_chat.py"
from backend import ToolCall

SOURCE = """
@population(city: str) -> int:
  ###
  Return the population of a city.
  ###
  > tool:
    risk: read_only
  = `2_100_000`

> use: population
>> Paris has [count: int] inhabitants.
= `count`
"""


def answer(request: BackendRequest) -> Reply:
    tool_results = [m for m in request.messages if m["role"] == "tool"]
    if not tool_results:
        return Reply(tool_calls=(ToolCall("c1", "population", {"city": "Paris"}),))
    return Reply(data={"count": 2_100_000})


backend = ScriptedBackend(answer)
assert run(SOURCE, backend) == 2_100_000
first = backend.requests[0]
assert first.model == "m1"
assert "<TemplateInstructions>" in (first.system or "")
assert first.output_schema is not None and "count" in first.output_schema["properties"]
assert "population" in {tool["name"] for tool in first.tools}
```
