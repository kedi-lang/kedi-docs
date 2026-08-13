# Capability Matrix

Capabilities are declared contracts, not feature guesses. Kedi validates the
active profile against them and fails when a required surface is unavailable.

The tables between the generated markers come directly from the built-in
adapters' `AdapterCapabilities`. Run
`python scripts/sync_capability_matrix.py` after changing adapter metadata.
Every built-in adapter also implements raw text invocation because `invoke` is
part of the base adapter protocol rather than an optional capability.

<!-- BEGIN GENERATED ADAPTER CAPABILITIES -->
## Framework Adapters

| Capability | Pydantic AI | DSPy | LangChain |
| --- | :---: | :---: | :---: |
| Structured output | yes | yes | yes |
| Kedi tool registration | yes | yes | yes |
| Kedi-declared MCP | yes | yes | yes |
| Profile override | yes | yes | yes |
| Model override | yes | yes | yes |
| Effort | yes | yes | yes |
| Settings | yes | yes | yes |
| Code mode | no | no | no |
| Native approvals | yes | no | yes |
| Dynamic native approval handler | yes | no | yes |
| Foreground subagents | yes | yes | yes |
| Background subagents | yes | no | yes |
| Semantic stream events | yes | no | yes |

## Agent Harnesses

| Capability | Claude Agent SDK | Codex App Server | ACP |
| --- | :---: | :---: | :---: |
| Structured output | yes | yes | no |
| Kedi tool registration | yes | yes | no |
| Kedi-declared MCP | yes | no | no |
| Profile override | yes | yes | yes |
| Model override | yes | yes | no |
| Effort | yes | yes | no |
| Settings | yes | yes | yes |
| Code mode | no | no | no |
| Native approvals | yes | yes | no |
| Dynamic native approval handler | yes | no | no |
| Foreground subagents | yes | yes | no |
| Background subagents | yes | yes | no |
| Semantic stream events | yes | yes | yes |
<!-- END GENERATED ADAPTER CAPABILITIES -->

ACP is intentionally a raw-text harness. It starts a fresh ACP session for each
Kedi invocation and consumes text chunks. Structured captures, Kedi tools, MCP
projection, model selection, effort, and subagents are rejected rather than
simulated.

“Native approvals” means the adapter can project Kedi's policy into its own
tool loop. Kedi still performs argument validation and risk classification
around registered tools. Transport modes, provider support, and other
adapter-specific constraints are not represented by the boolean capability
metadata; consult the corresponding [adapter page](../agent-adapters/index.md).

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
| `stream_events` | Completed semantic commentary/final messages and run lifecycle events |

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
