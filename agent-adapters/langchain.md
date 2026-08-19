# LangChain

## Installation

Kedi includes LangChain, OpenAI/OpenRouter integrations, and MCP adapters:

```bash
uv add kedi
```

Other providers may require their own LangChain integration package.

## Chat Models

```kedi
> adapter: langchain
> model: openai:gpt-4o-mini
```

String models are passed through `langchain.chat_models.init_chat_model`.
An existing chat model object may be supplied directly to `LangChainAdapter`.
A missing model fails when the adapter first runs.

## Model Settings

Kedi supports common constructor/runtime fields including `temperature`,
`max_tokens`, `timeout`, `max_retries`, sampling penalties, `tool_choice`,
`parallel_tool_calls`, callbacks, metadata/tags, streaming controls,
OpenAI-compatible endpoint fields, and `reasoning`/`reasoning_effort`.

For `openrouter:` model names, effort is written to
`reasoning={"effort": ...}`; other models receive `reasoning_effort`.

## Structured Outputs

Kedi builds a Pydantic output model and calls `create_agent` with a response
format. It reads LangChain's `structured_response` field and fails if the agent
does not provide one.

Subagent JSON Schema uses LangChain `ToolStrategy`, preserving the child
schema rather than inventing a Kedi output format.

## Tool Binding

Kedi tools become `StructuredTool` instances with JSON argument schemas.
Sync and async functions retain the correct invocation path. Kedi's approval
middleware guards projected tools and preserves tool metadata.

## MCP Tools

`MultiServerMCPClient` maps:

- Kedi stdio to LangChain `stdio`;
- Kedi SSE to `sse`;
- Kedi HTTP to `streamable_http`.

MCP tools are added to each agent run. External MCP tools are treated as
mutating by default and upgraded to sensitive when arguments target dotenv
secret files.

## CodeMode

`> codemode: enabled` replaces LangChain's model-facing application tools with
`search_tools`, `get_tool_schema`, and `execute_code`. Scoped Kedi tools and
`MultiServerMCPClient` tools enter one run-scoped catalog. Nested calls retain
Kedi argument validation and inline approval; the direct-call approval
middleware does not approve the three controls a second time.

LangChain receives Monty and boundary failures as failed tool results, allowing
the model to correct a snippet without terminating the complete agent run. See
[CodeMode](../agentic-engineering/codemode.md) for the shared contract.

## Subagent Lifecycle

LangChain supports foreground/background child runs. Request limits map to a
LangGraph recursion limit of `request_limit * 2 + 1`. Usage metadata from
messages is reported to Kedi's budget observer.

## Capability Limits

Backend-specific settings still depend on the selected chat model. Native
approval middleware covers tools represented in the LangChain agent; it cannot
grant capabilities the provider itself does not expose.
