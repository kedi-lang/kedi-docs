# Prompt Optimization

## Mark an `> optimize:` Span

An optimize span is an executable template block inside a procedure:

```kedi
@extract_owner(ticket: str) -> str:
  > optimize: owner_extraction:
    >> Read the ticket below.
    Ticket: <ticket>
    Return the responsible person's name: [owner]
  = `owner`
```

The whole indented body is newline-joined and sent in **one model call**. Values
captured as `[owner]` become available only after that call finishes.

## Named Prompt Spans

The span name is a stable artifact key. In
`program.kedi.optimized.json`, prompts are stored as:

```json
{
  "extract_owner": {
    "owner_extraction": "Optimized instruction prefix..."
  }
}
```

Choose names that describe the prompt's job. Renaming a span disconnects it
from the old artifact entry.

## Explicit and Legacy Block Forms

Both forms below are valid and have identical single-call behavior.

Explicit form:

```kedi
@extract(document: str) -> str:
  > optimize: fields:
    >> Read <document>.
    Return [title] and [author].
  = `<title> + " by " + <author>`
```

Legacy bare-line form:

```kedi
@extract(document: str) -> str:
  > optimize: fields:
    Read <document>.
    Return [title] and [author].
  = `<title> + " by " + <author>`
```

The leading `>>` is optional **only inside `> optimize:` and `> auto:` bodies**.
Bare template text at top level or in an ordinary procedure is a parse error.
The bare form is not a sequence of separate prompts; all lines still form one
template call.

Substitutions and captures work exactly as they do in `>>` blocks:

- `<document>` reads and renders an existing value.
- `<helper(document)>` renders a procedure call result.
- `<`expression`>` renders a Python expression.
- `[title]` captures a string.
- `[items: list[str]]` requests and captures a typed value.

## Multiple Spans

A procedure may contain multiple independently named spans:

```kedi
@solve(problem: str) -> int:
  > optimize: parse:
    >> Parse <problem> into [left: int], [right: int], and [operation].
  > optimize: calculate:
    >> Calculate <left> <operation> <right>: [answer: int]
  = `answer`
```

They execute in procedure order. Because they are separate model calls, the
second span can substitute fields produced by the first. GEPA optimizes spans
one at a time and stores one prefix per span.

## Required Eval Suites

Every optimized procedure needs:

1. a same-named `@eval:` suite;
2. at least one `> data:` dataset;
3. at least one metric;
4. a metric dataset name that refers to training data.

```kedi
@extract_owner(ticket: str) -> str:
  > optimize: owner:
    Find the owner in <ticket>: [owner]
  = `owner`

@eval: extract_owner:
  > data: tickets:
    = `[("Owner: Ada", {"owner": "Ada"})]`
  > metric: exact(tickets):
    = `extract_owner(tickets) == expected["owner"]`
```

Kedi validates these requirements before constructing model-backed optimizer
services, so configuration errors fail before expensive optimization begins.

## Training Data

The optimizer uses the first declared training dataset for a procedure. Use
explicit `(input, expected)` rows. For multi-parameter procedures, the input is
a tuple ordered like the procedure signature:

```kedi
= `[(("left text", "right text"), {"same": False})]`
```

Metrics should return stable scores and useful feedback. An optimizer can only
improve what the dataset and metric expose.

## Validation Data

A `> test_data:` block with the same name becomes the optimizer's validation
set. If GEPA has no test set, it uses the first quarter of training examples
when at least four training examples exist; otherwise it validates on the full
training set.

`--optimizer-max-validation-examples N` truncates an explicit test set for
baseline validation. It does not truncate the training set.

## Optimized Output Artifacts

Run optimization independently:

```bash
kedi program.kedi --optimize --optimizer gepa
```

Or optimize and then report eval results in the same command:

```bash
kedi program.kedi --optimize --optimizer gepa --eval
```

Kedi stores only an optimized **prefix**. It preserves the original source
template, including output fields and type annotations, and prepends the prefix
at runtime. This prevents an optimizer from becoming the owner of the output
schema.

File-backed execution, tests, and evals load `program.kedi.optimized.json`
automatically. A missing file means “use the source prompt.” A malformed file
is an execution error; Kedi never silently falls back from corrupt optimized
state.

## Fresh Optimization Runs

GEPA normally seeds from prior optimized prompts and resumes per-span
checkpoints. Start from the source template only with:

```bash
kedi program.kedi --optimize --optimizer gepa --optimizer-fresh
```

`--optimizer-fresh` deletes:

- `program.kedi.optimized.json`;
- `program.kedi.optimized_scores.json`;
- `program.kedi.gepa/`.

It is unrelated to `--no-cache`, which controls generated `> auto:`
implementations.
