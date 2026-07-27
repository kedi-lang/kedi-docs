# Capability Matrix

Capabilities are declared contracts, not feature guesses. Kedi validates the
active profile against them and fails when a required surface is unavailable.

## Framework Adapters

| Capability | Pydantic AI | DSPy | LangChain |
| --- | :---: | :---: | :---: |
| Raw text invocation | yes | yes | yes |
| Structured output | yes | yes | yes |
| Kedi tool registration | yes | yes | yes |
| MCP | stdio, SSE, HTTP | stdio | stdio, SSE, HTTP |
| Model override | yes | yes | yes |
| Effort and settings | yes | yes | yes |
| Native approvals | yes | no | yes |
| Dynamic native approval handler | yes | no | yes |
| Foreground subagents | yes | yes | yes |
| Background subagents | yes | no | yes |

“Native approvals” means the adapter can project Kedi's policy into its
framework tool loop. Kedi still performs its own argument validation and risk
classification around registered tools.

## Agent Harnesses

| Capability | Claude Agent SDK | Codex App Server | ACP |
| --- | :---: | :---: | :---: |
| Raw text invocation | yes | yes | yes |
| Structured output | yes | yes | no |
| Kedi tool registration | yes | yes | no |
| Kedi-declared MCP | yes | no | no |
| Model override | yes | yes | no |
| Effort | yes | yes | no |
| Settings | yes | yes | limited |
| Native approvals | yes | yes | no |
| Dynamic native approval handler | yes | no | no |
| Foreground subagents | yes | yes | no |
| Background subagents | yes | yes | no |

ACP is intentionally a raw-text harness. It starts a fresh ACP session for each
Kedi invocation and consumes text chunks. Structured captures, Kedi tools, MCP
projection, model selection, effort, and subagents are rejected rather than
simulated.

## Structured Schema Notes

Framework support still depends on the selected provider/model. Codex accepts
string schema formats `date`, `date-time`, `duration`, `email`, and `time`; it
rejects Kedi output schemas requiring `Regex`, `HttpUrl`, or `FileUrl`. Claude
accepts the documented built-in formats. Validate the exact production model,
not only the adapter.

## Capability Meanings

| Capability | Required by |
| --- | --- |
| `structured_output` | Any `>>` block containing output fields |
| `tool_registration` | `> use:` of a procedure or Python callable |
| `mcp` | One or more `> mcp:` servers |
| `profile_override` | Lexical/profile state changes |
| `model_override` | Explicit `> model:` |
| `effort` | Explicit `> effort:` |
| `settings` | Nonempty `> settings:` |
| `codemode` | Custom adapter code-execution mode when explicitly exposed |
| `native_approvals` | Adapter-owned risky tool loop |
| `native_approval_handler` | Dynamic handler projected natively |
| `subagents` | `> subagent:` |
| `background_subagents` | Background lifecycle tools |

Raw invokes with no structured fields can run on a text-only adapter. A profile
may be syntactically valid but capability-invalid for its selected backend;
that mismatch is an error before Kedi pretends the feature is active.

`codemode` is reserved in the adapter capability protocol for extensions that
replace ordinary tool exchange with an explicit code-execution surface. No
built-in adapter currently advertises it, and Kedi does not infer it from
ordinary tool registration.

## Custom Adapters

A custom `AgentAdapter` declares `kind`, `shortname`, and
`AdapterCapabilities`, then implements async/sync structured production and raw
invocation. Set an unsupported capability to false/`None`; never advertise a
surface and silently ignore it. See [Custom Adapters](../agent-adapters/custom-adapters.md).
