# Evals and Optimization

Kedi separates four related jobs: deterministic tests, dataset-driven
evaluation, prompt optimization, and AI-generated procedure implementations.
They use some of the same procedures and Python environment, but they do not
have the same purpose or lifecycle.

## Tests, Evals, and Optimizers

| Surface | Purpose | Model calls |
| --- | --- | --- |
| `@test:` | Assert concrete behavior and regressions | Only those made by the tested procedure |
| `@eval:` | Score behavior over a dataset | Usually one procedure run per dataset row |
| `> optimize:` | Mark prompt spans that an optimizer may rewrite | Many candidate and metric calls |
| `> auto:` | Generate tests and an implementation for a procedure | Test-generation and implementation attempts |

Use tests for invariants that must always pass. Use evals for graded qualities
such as relevance, extraction accuracy, or style adherence. Optimize only after
the eval metric represents the behavior you actually want.

## Deterministic Validation

Tests are Python assertions grouped under a procedure name:

```kedi
@slugify(title: str) -> str:
  = `title.strip().lower().replace(" ", "-")`

@test: slugify:
  > case: trims_and_joins:
    ```
    assert slugify("  Kedi Reference  ") == "kedi-reference"
    ```
```

`kedi program.kedi --test` exits nonzero if any case fails. Test blocks do not
add runtime behavior to a normal program execution.

## Dataset-Driven Evaluation

An eval suite declares data and one metric:

```kedi
@classify(text: str) -> str:
  >> Classify <text> as positive or negative: [label]
  = `label`

@eval: classify:
  > data: examples:
    = `[("excellent", "positive"), ("awful", "negative")]`
  > metric: accuracy(examples):
    = `classify(examples) == expected`
```

The dataset name becomes the metric's input binding. For conventional
`(input, expected)` rows, `expected` is also available.

## Prompt Optimization

`> optimize: name:` marks only the prompt span to evolve; it does not replace
the procedure signature, surrounding computation, output schema, or metric.

```kedi
@extract_priority(ticket: str) -> str:
  > optimize: classify_priority:
    >> Read this support ticket: <ticket>
    Return its priority as low, medium, or high: [priority]
  = `priority`
```

Optimization requires a matching `@eval: extract_priority` suite with training
data. The generated instruction is stored beside the source and loaded on
later file-backed runs.

## Generated Implementations

`> auto:` asks the code-generation agent to implement a procedure from its
typed signature and natural-language contract:

```kedi
@deduplicate(items: list[str]) -> list[str]:
  > auto:
    Preserve first-seen order while removing duplicate strings.
```

Kedi generates tests first, then an implementation, and accepts the generated
code only after it parses and the generated tests pass.

## Artifacts and Reproducibility

Kedi writes generated state next to the source file:

| Artifact | Meaning |
| --- | --- |
| `program.cache.kedi` | Generated tests and implementations for `> auto:` procedures |
| `program.kedi.optimized.json` | Optimized instruction prefixes by procedure and span |
| `program.kedi.optimized_scores.json` | Last recorded training score by procedure |
| `program.kedi.gepa/` | Per-span GEPA resume checkpoints |

These artifacts serve different systems. `--no-cache` controls the codegen
cache only. `--optimizer-fresh` clears optimization output and GEPA checkpoints.

## Choose the Right Surface

- Use `@test:` when a Boolean assertion can define correctness exactly.
- Use `@eval:` when quality is continuous, subjective, or dataset-dependent.
- Use `> optimize:` when the procedure is structurally correct but its prompt
  can improve.
- Use `> auto:` when the procedure should be implemented as generated Python,
  not as an LLM prompt at runtime.
