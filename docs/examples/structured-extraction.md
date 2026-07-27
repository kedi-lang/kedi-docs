# Structured Extraction

This example extracts one reusable native object rather than parsing JSON text
after a model call.

## Complete Program

```kedi
> adapter: pydantic
> model: groq:qwen/qwen3-32b
> system: Extract only facts stated in the incident report.

~Owner(
  name: Annotated[str, "Person or team responsible for follow-up"],
  email: Email | None
)

~Incident(
  title: str,
  severity: Literal["low", "medium", "high", "critical"],
  owner: Owner | None,
  affected_services: list[str],
  customer_visible: bool
)

@extract_incident(report: str) -> Incident:
  >> Read this incident report:
  <report>
  Return one normalized [incident: Incident].
  = `incident`

[report: str] = Payment retries failed in checkout. The Payments team owns the follow-up.
[incident: Incident] = `extract_incident(report)`

= `incident.model_dump_json(indent=2)`
```

The adjacent lines after `>>` are newline-joined into one model request. Do not
insert a blank line inside that block: it can terminate template continuation.
`[incident: Incident]` creates a structured output schema and validates the
response; it is not an instruction to return an arbitrary JSON string.

## Native Return Versus Rendering

Inside `extract_incident`, this return preserves the Pydantic model:

```kedi
= `incident`
```

This alternative returns text:

```kedi
= <incident>
```

Use the native form when another procedure, Python caller, metric, or tool needs
to inspect fields. Render only at a presentation boundary.

## Multiple Captures

For a local result that is not reused as one domain object, separate fields are
often simpler:

```kedi
@classify(message: str) -> tuple[str, bool]:
  >> Classify <message>.
  Return [category: Literal["question", "request", "incident"]]
  and whether it is [urgent: bool].
  = `(category, urgent)`
```

All fields in one block are filled by one model call and become visible only
after that call completes. A continuation line in the same block cannot
substitute a field captured earlier in that block.

## Dynamic Python Type

Use a backtick annotation only when the type genuinely comes from Python:

````kedi
```
from typing import Literal

CurrentRegion = Literal["eu", "us", "apac"]
```

@extract_region(text: str) -> `CurrentRegion`:
  >> Identify [region: `CurrentRegion`] in <text>.
  = `region`
````

For Kedi custom types and built-ins, direct annotations are clearer. Provider
schema support can be narrower than Python's type system; consult the selected
[adapter](../agent-adapters/index.md) before using URL, regex, or complex union
types.

## Validate Deterministic Constraints in Python

Do not ask the model to calculate facts your program can enforce:

```kedi
@bounded_confidence(raw: float) -> float:
  = `max(0.0, min(1.0, raw))`
```

Model schemas validate shape and type. Cross-field business invariants still
belong in deterministic code, tests, or a Pydantic validator supplied through
Python.
