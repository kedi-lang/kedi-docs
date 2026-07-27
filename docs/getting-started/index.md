# Start with Kedi

## What You Will Build

The first workflow accepts a topic from the command line, asks a model for a
short structured brief, and returns the captured text:

```kedi
@brief(topic: str) -> str:
  >> Explain <topic> to a software engineer.
  Keep the answer to two sentences and return [summary: str].
  = <summary>

= <brief(`args.topic`)>
```

This is intentionally small, but it demonstrates the main execution model:

1. `args.topic` is passed to `brief` as a native Python string.
2. `<topic>` substitutes that runtime value into the prompt.
3. `[summary: str]` captures one typed field from the model response.
4. `= <summary>` returns its rendered text.

## Prerequisites

- Python 3.10 or newer;
- a Kedi installation;
- credentials required by the selected model provider;
- optionally, an agent harness installation when using Codex, Claude, or ACP.

Parsing does not contact a provider. Use it to validate syntax before setting up
credentials.

## The Smallest Useful Program

For a fixed prompt with one result, capture the output explicitly:

```kedi
>> Explain why idempotency matters as [answer: str] in one paragraph.
= <answer>
```

The typed field keeps the response and makes its contract visible to the
adapter. A plain template without an output field does **not** keep the response:

```kedi
>> Explain why idempotency matters in one paragraph.
```

That form is appropriate only when the call's side effects or trace matter and
the text is intentionally discarded. It is usually the wrong choice for a
user-facing answer.

## Run, Parse, and Validate

Save the first example as `brief.kedi`, then parse it:

```bash
kedi parse brief.kedi
```

Run it with an application argument:

```bash
kedi brief.kedi --topic "distributed locks"
```

Unknown CLI options after the source file are normalized into the reserved
`args` object. For example, `--dry-run` becomes `args.dry_run`. The `args`
binding cannot be reassigned from Kedi or embedded Python.

You can also parse inline source:

```bash
kedi -p -c "@broken("
```

Parse-only mode checks syntax and structural rules. Compilation and execution
can additionally fail on type resolution, backend capability validation,
provider errors, or approval decisions.

## Where to Go Next

- [First Program](first-program.md) expands the example and compares structured
  capture with raw capture.
- [Projects and Execution](projects-and-execution.md) explains source loading,
  adapters, and generated artifacts.
- [Templates and Invokes](../core-language/templates-and-invokes.md) defines
  the exact `>>` and `<<` semantics.
- [Outputs and Assignments](../core-language/outputs-and-assignments.md)
  explains when brackets capture model output and when they assign native data.
