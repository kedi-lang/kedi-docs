# ACP Agents

## Stdio Agent Commands

The generic ACP adapter launches an Agent Client Protocol process and speaks
newline-delimited JSON-RPC over stdio:

```kedi
> agent:
    acp: npx @zed-industries/codex-acp
```

Command strings are shell-split without invoking a shell. Python may pass a
sequence to avoid quoting ambiguity.

## Inline and Multiline Agent Directives

Inline selection uses a separately configured command:

```kedi
> agent: acp
```

Multiline selection binds the command in the profile. The command may be plain
text or a Python expression returning a string or sequence.

## `KEDI_ACP_AGENT_COMMAND`

If no directive/Python command is set, Kedi reads:

```bash
export KEDI_ACP_AGENT_COMMAND='npx @zed-industries/codex-acp'
kedi program.kedi --adapter acp
```

The CLI's `--acp-command` sets the same process environment value. Resolution
order is profile command, adapter constructor command, then environment.

## Working Directory and Environment

```kedi
> settings:
    cwd: /workspace/project
    env: `{"MODE": "review"}`
    timeout: 300
```

Clients are reused by `(command, cwd, env)` and each prompt opens a fresh ACP
session. Stdio process cwd and `session/new.cwd` receive the configured cwd.

## Timeouts

`timeout` is the prompt request timeout and must be a positive number.
`request_timeout` on `ACPAdapter` governs protocol requests by default.
Disconnect errors include the last 40 stderr lines for diagnosis.

## Model Selection

Generic ACP model selection is not currently mapped. `> model:` and
`> effort:` are unsupported capability overrides. Configure the child ACP
agent's own default model through its command/environment.

## Prompt and Structured Results

ACP supports raw text only:

```kedi
> agent: acp
>> Inspect the repository and return [answer: str] summarizing the risk.
= `answer`
```

Kedi concatenates `agent_message_chunk` text updates. Structured `>>` output
raises `NotImplementedError`; no prompting shim fabricates a schema.

## ACP Capability Mapping

Kedi sends protocol initialization, `session/new` with cwd and an empty
`mcpServers` list, `session/prompt`, streamed updates, then `session/close`.
Each call is independent.

## Current Limits

- no structured output;
- no Kedi tool registration;
- no Kedi MCP projection;
- no model or effort override;
- no Kedi subagents;
- only text `agent_message_chunk` updates are collected.
