# Kedi

Kedi is a typed language and Python API for building LLM programs whose prompts,
dataflow, structured outputs, tools, tests, and agent configuration live in one
readable source format.

## What Kedi Is

Kedi sits between application code and model or agent frameworks. A `.kedi`
program can:

- render prompts from runtime values;
- capture model output into typed fields;
- compose reusable procedures;
- run Python expressions and blocks when deterministic code is the right tool;
- expose procedures and Python callables as agent tools;
- configure models, MCP servers, skills, approvals, and subagents;
- define tests, datasets, metrics, prompt optimization, and generated procedures.

Kedi is not a model provider. Model calls are routed through an **agent
framework adapter** such as Pydantic AI, DSPy, or LangChain, or an **agent
harness adapter** such as Codex, Claude, or an ACP agent.

## Why Typed LLM Programs

Prompts are useful for fuzzy transformations; Python is useful for deterministic
logic. Kedi keeps both in one dataflow without pretending they are the same
thing.

```kedi
~Ticket(category: str, urgency: int)

@classify(message: str) -> Ticket:
  >> Classify this support message: <message>
  Return [ticket: Ticket].
  = `ticket`
```

`<message>` is a substitution: Kedi renders an existing value into the prompt.
`[ticket: Ticket]` is an output capture: the adapter asks the model for a value
matching the generated schema. ``= `ticket` `` returns the native `Ticket`
object. Writing `= <ticket>` instead would stringify it.

Use output capture whenever a model result participates in the program's
dataflow, including plain text. A `str` capture still gives the adapter an
explicit output contract:

```kedi
@summarize(message: str) -> str:
  >> Summarize <message> as [summary: str] in two sentences.
  = <summary>
```

Raw capture is an escape hatch for deliberately unstructured text, not the
default form of a Kedi model call.

## Choose a Starting Point

- New to Kedi: begin with [Start with Kedi](getting-started/index.md).
- Learning the DSL: use the [Core Language](core-language/index.md) guide.
- Embedding Kedi in Python: use the [Python API](python-api/index.md).
- Building tool-using or delegated agents: use
  [Agentic Engineering](agentic-engineering/index.md).
- Looking up exact syntax or behavior: use the [Reference](reference/index.md).

## Core Language, Python API, and Agent Adapters

The same runtime semantics are available through two authoring surfaces:

- `.kedi` files are best for workflows where prompts, types, procedures, tests,
  and profiles should be visible together.
- `@kedi.query` and `@kedi.bind` are best when Python owns the public function
  signature and Kedi provides the implementation.

Adapters are boundary implementations, not alternative Kedi dialects. The
language semantics stay stable, while capability validation reports whether a
selected backend supports structured output, tools, MCP, approvals, or
subagents.

## Documentation Conventions

Code blocks marked `kedi` are Kedi source. Backticks have two different roles:

- single backticks, such as `` `items` ``, evaluate a Python expression;
- triple backtick blocks execute multiline Python.

The documentation distinguishes:

- **substitution** (`<value>`), which reads and renders a value;
- **output capture** (`[value: Type]`), which asks the model to produce a value;
- **native return** (``= `value` ``), which preserves the Python object;
- **rendered return** (`= <value>`), which returns text.

Those choices are called out in examples because replacing one with another can
change types, validation, or whether a model response is retained.
