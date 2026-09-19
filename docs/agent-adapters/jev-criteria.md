# Jev Criteria and Output Types

Describe finite choices, binary evidence, probabilities, and ordered score levels. Import metadata through Python aliases; the Kedi type grammar does not gain arbitrary function calls.

## Typed Criteria

````kedi
```
from typing import Annotated
from kedi.typesafe import Probability, Rubric

Correctness = Annotated[
    Probability,
    "Does the answer agree with the reference?",
]
Quality = Annotated[
    float,
    "Assess the answer against the reference",
    Rubric(["Incorrect", "Partly correct", "Fully correct"]),
]
```
> adapter: pydantic
> model: typesafe/jev-latest

~Assessment(
  correctness: `Correctness`,
  quality: `Quality`
)
>> The reference is Ankara and the answer is Ankara. The assessment is [assessment: Assessment].
= `assessment`
````

`Probability` is a finite float between 0 and 1. A rubric with N ordered levels
produces a score between 0 and N-1; float scores retain their fractional part.
Integer rubric outputs round to the nearest level, with ties rounded upward.
Rubric bounds are automatically included and validated; no separate range is needed.

`ChoiceCriteria` supplies descriptions for each exact `Literal`/enum option.
`BooleanCriteria(true=..., false=...)` supplies descriptions for positive and negative
evidence. Import these from `kedi.typesafe` in the Python prelude and use them in
Python `Annotated` aliases. This does not add function calls to native type syntax.
Importing `kedi.typesafe` without the optional package fails with installation advice;
ordinary `import kedi` does not load Jev.


## Outputs and Limitations

- Nested required objects are reconstructed after evaluation.
- Lists of finite string choices are multi-label decisions, in declaration order.
- Nullable finite choices include an explicit no-match option.
- Email, phone, regex, and custom extractors produce finite candidates locally;
  Jev chooses among them. These are extraction, not arbitrary text generation.
- Nullable extraction without candidates returns `None` without a provider request.
- General unconstrained strings, free-form invokes, arbitrary numeric extraction,
  media input, recursive schemas, and arbitrary arrays are unsupported.
- Independent fields share one request. Dependent decisions need separate calls.
- Unsupported schemas and malformed provider output raise errors; they are not
  silently converted to false, repaired, or sent to another model.
