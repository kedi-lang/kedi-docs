# Approvals, MCP, and Skills

## `@kedi.approval`

Decorate a handler to install it as the current Python API configuration's
default dynamic policy:

```python
import kedi


@kedi.approval
def review_call(request: kedi.ApprovalRequest) -> kedi.ApprovalDecision:
    if request.tool_name == "write_report":
        return kedi.ApprovalDecision.edit(
            {**request.arguments, "path": "reports/latest.md"},
            reason="confine writes to the report path",
        )
    return kedi.ApprovalDecision.deny(reason="tool is outside this workflow")
```

The decorator returns the original handler, so it can also be passed explicitly
to `context`, `query`, or `bind`.

## Approval Policies

The `approval=` parameter accepts:

```python
kedi.configure(approval="allow")
kedi.configure(approval="deny")
kedi.configure(approval=kedi.ApprovalPolicy.allow())
kedi.configure(approval=kedi.ApprovalPolicy.dynamic(review_call))
```

Only `"allow"` and `"deny"` are valid strings. With no policy, mutating and
sensitive tools are denied. Read-only tools are always allowed, even under a
static deny policy.

## Dynamic Approval Handlers

Handlers may be synchronous or asynchronous:

```python
async def approve_from_service(
    request: kedi.ApprovalRequest,
) -> kedi.ApprovalDecision:
    allowed = await policy_service.check(request.tool_name, request.arguments)
    if allowed:
        return kedi.ApprovalDecision.allow(reason="approved by policy service")
    return kedi.ApprovalDecision.deny(reason="rejected by policy service")
```

An async handler requires an async-capable tool path when an event loop is
already running. Returning any object other than `ApprovalDecision` is an
invalid decision error.

## Approval Requests and Decisions

`ApprovalRequest` is frozen and contains:

| Field | Meaning |
| --- | --- |
| `tool_name` | Registered tool name |
| `arguments` | Deep-copied, read-only argument mapping |
| `risk` | `read_only`, `mutating`, or `sensitive` |
| `adapter_shortname` | Active adapter when known |
| `description` | Tool description when known |
| `metadata` | Optional deep-copied adapter/runtime metadata |

Return one explicit decision:

```python
kedi.ApprovalDecision.allow(reason="safe for this task")
kedi.ApprovalDecision.deny(reason="outside allowed scope")
kedi.ApprovalDecision.edit(
    {"path": "reports/output.md", "content": "approved content"},
    reason="rewrote destination",
)
```

Only `edit` may contain replacement arguments. Edited arguments are
revalidated and reclassified before execution; an edit is not a bypass around
tool schemas or risk policy.

## `McpServerSpec`

Import the typed specification from `kedi`:

```python
from kedi import McpServerSpec
```

For stdio:

```python
filesystem_mcp = McpServerSpec(
    transport="stdio",
    command="npx",
    args=("-y", "@modelcontextprotocol/server-filesystem", "/workspace"),
    env={"LOG_LEVEL": "warning"},
).normalized()
```

For streamable HTTP:

```python
docs_mcp = McpServerSpec(
    transport="http",
    url="http://127.0.0.1:8000/mcp",
    headers={"Authorization": "Bearer token"},
).normalized()
```

For SSE, use `transport="sse"` and `url=...`. The Python dataclass accepts the
canonical values `stdio`, `http`, and `sse`; DSL spelling
`streamable-http` normalizes to `http`.

Calling `.normalized()` is recommended when constructing specs directly. It
validates that stdio has a command, remote transports have a URL, and clears
fields that do not apply to the selected transport.

## Configure MCP Servers

Pass a sequence at any configuration scope:

```python
kedi.configure(mcp_servers=[docs_mcp])

with kedi.context(mcp_servers=[filesystem_mcp]):
    result = investigate("...")
```

Context and per-callable MCP servers append to inherited servers; they do not
replace or deduplicate them. Adapter capability differs: unsupported adapters
must fail or report the capability limitation rather than silently emulate an
MCP server.

MCP servers are external code or services. Stdio commands run with the host
process's authority, and remote headers may carry credentials.

## Enable Skills

Enable project-local skills explicitly:

```python
kedi.configure(skills=True)
```

or for one callable:

```python
@kedi.query(skills=True)
def solve(task: str) -> str:
    """kedi
>> Use an applicable project skill to solve <task>. Return [answer: str].
    = `answer`
    """
    ...
```

Kedi looks under `.agents/skills` relative to the active working directory and
exposes two read-only tools:

- `list_skills(all=False, limit=20)`;
- `read_skill(name)`.

Enabling skills does not preload every `SKILL.md`; the agent discovers and
reads only relevant entries.

## Per-Callable Overrides

```python
@kedi.query(
    approval=review_call,
    mcp_servers=[docs_mcp],
    skills=True,
)
def investigate(question: str) -> str:
    """kedi
>> Investigate <question> and return [answer: str].
    = `answer`
    """
    ...
```

An explicit per-callable approval overrides inherited approval for that
callable. `skills=False` can disable inherited skills. MCP servers append
because their merge model is additive.

## Scope Precedence

For profile values, effective precedence is:

1. defaults from `configure()`;
2. active nested `context()` scopes;
3. `query()` or `bind()` decorator overrides;
4. lexical DSL directives and selected named profiles.

Later explicit values win. Settings maps merge by key, tool names merge with
later definitions taking ownership, and MCP server lists append. Approval and
skills replace when explicitly provided.
