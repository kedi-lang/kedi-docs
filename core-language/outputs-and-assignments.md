# Outputs and Assignments

Square brackets are write syntax in Kedi. In a `>>` template they declare
fields the model must produce; on the left of `=` they assign deterministic
values. Neither form is the same as `<name>`, which reads a value.

## Output Fields as L-Values

An output field embedded in a template is an L-value:

```kedi
>> Incident severity: [severity: str]. Summary: [summary: str].
= <severity>: <summary>
```

Kedi builds a structured output schema, asks the active adapter to fill it, and
stores each field in the current environment. Output names must be valid Python
identifiers: they start with a letter or underscore and contain only letters,
digits, and underscores.

Use model outputs for semantic extraction or generation. Do not use them for
values that Python can determine exactly.

## Simple and Typed Outputs

An untyped output defaults to `str`:

```kedi
>> Concise headline: [headline].
```

A typed output asks the adapter for a native value and validates it:

```kedi
>> Priority: [priority: int]. Owners: [owners: list[str]]. Blocked: [blocked: bool].
```

Kedi does not merely include the annotation in the prompt. It resolves the type,
creates the provider schema, and validates the returned value. Unsupported
provider schema formats fail before a model call where the adapter can detect
them.

## Inline Python Output Types

Wrap a type expression in backticks when the type comes from runtime Python
state:

````kedi
```
from typing import Literal
Priority = Literal["low", "medium", "high"]
```

>> Ticket priority: [priority: `Priority`].
````

For ordinary built-in or custom Kedi types, prefer the direct form
`[priority: Priority]`. Runtime expressions are useful for types created by a
prelude, import, or factory, but they make static tooling less certain.

## Field Description Metadata

Use `Annotated[T, "description"]` to explain a field to the model while keeping
`T` as its runtime type:

```kedi
>> Country code: [code: Annotated[str, "Uppercase ISO 3166-1 alpha-2 country code"]].
```

The description becomes JSON Schema metadata for adapters that expose schemas.
The second argument must be a single-line string literal. `Annotated[T]` is
accepted as `T` but triggers an editor warning because it carries no
description. Additional metadata is ignored.

Use descriptions for constraints the base type cannot express clearly. Do not
repeat obvious information such as `Annotated[int, "An integer"]`.

## Multiple Outputs and Reassignment

One template can fill several fields:

```kedi
>> Release version: [version: str].
Release date: [date: date].
Changes: [changes: list[str]].
```

All continuation lines in that `>>` block belong to one model request and one
combined schema. A later output or assignment with the same name replaces the
value in the current scope:

```kedi
[status] = draft
>> Document status after review: [status: str].
= <status>
```

Reassignment is intentional but can obscure dataflow. Prefer a new name such as
`reviewed_status` when both values matter.

## Native Assignments

Assignment does not contact a model:

```kedi
[title] = Release <version>
[attempts: int] = `2 + 1`
[copy] = <title>
```

The right-hand side has two evaluation modes:

- A sole native Python segment preserves its native result.
- A sole procedure call preserves that procedure's native result.
- Mixed literal text and substitutions render to `str`.

This distinction matters:

```kedi
[native: int] = `40 + 2`
[rendered] = Answer: <`40 + 2`>
```

`native` is the integer `42`; `rendered` is the string `"Answer: 42"`.

## Typed Assignments

A typed assignment validates the resulting value without coercing it:

```kedi
[ports: list[int]] = `[8000, 8001]`
[enabled: bool] = `True`
```

`[count: int] = five` fails instead of converting text. If parsing user text is
required, do it explicitly in Python:

```kedi
[raw_count] = 5
[count: int] = `int(raw_count)`
```

## Assignment from a Python Block

Use a fenced block when computing a value requires statements:

````kedi
[durations: list[int]] = `[14, 8, 21]`
[p95: int] = ```
ordered = sorted(durations)
index = round(0.95 * (len(ordered) - 1))
return ordered[index]
```

= p95\=<p95>
````

The block must execute `return` to supply the assignment value. New helper names
inside the block remain local; the assigned result is the supported way to
surface one of them.

## Output Capture versus Raw Capture

Use `>>` output fields when you need typed or multiple structured values:

```kedi
>> Detected language: [language: str]. Confidence: [confidence: float].
```

Use raw capture when the complete model response should remain an unstructured
string:

```kedi
[explanation] << Explain why the build failed in one paragraph.
```

Raw capture accepts no embedded output fields and no type other than optional
`str`. A plain `>>` request with no output fields runs the model and discards
its response.

## Resolution and Validation Errors

Kedi rejects duplicate output names within an invalid schema, malformed
identifiers, unknown types, values that do not match assignments, and adapter
schemas the active backend cannot represent. Type validation is strict: a
numeric-looking string is still a string.

Choose annotations that match the wire capability of the selected adapter. For
example, a descriptive `Annotated[str, "..."]` can be more portable than a
provider-specific URL or regex format.
