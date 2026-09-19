# TypeSafe Jev

Jev evaluates claims, selects finite options, and scores described rubrics. It is
not a free-form text generator. Kedi exposes it through the Pydantic AI and
LangChain adapters using the optional `kedi-typesafe` package.

## Installation

For a published compatible release:

```sh
uv add 'kedi[typesafe]'
# For LangChain, also install the classifier integration:
uv add 'kedi[langchain,typesafe]' 'kedi-typesafe[langchain]'
```

The current `typesafe` and `codex-model`/`terminal-bench` extras pin incompatible
Pydantic AI release lines. Install them in separate environments; uv rejects the
unsupported combined selections explicitly.

Set `TYPESAFE_API_KEY` in the environment. The extended API described here requires
`kedi-typesafe` 0.2.1, which includes the decision evidence used by Kedi bindings.

## Claims and Thresholds

```kedi
> adapter: pydantic
> model: typesafe/jev-latest
> settings:
  typesafe_threshold: 0.9

> if: Ankara is the capital of Turkey
  = established
> else:
  = not established
```

Replace `pydantic` with `langchain` to use the other adapter. The default decision
rule is **probability > 0.85**; equality is false. Explicit request/profile settings
override the model constructor threshold without changing the shared model.
Thresholds must be finite numbers in [0, 1], not strings or booleans.

This threshold applies to boolean outputs and individual multi-label memberships.
It does not threshold raw probabilities, categorical choices, or rubric scores.
A provider probability is not a guarantee of empirical accuracy.

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
>> Reference: Ankara. Answer: Ankara. Assessment: [assessment: Assessment].
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

## Decision Evidence in Kedi

Jev-backed output bindings retain their decision evidence without changing the
normal output type:

````kedi
```
from kedi import decision_info
```
> adapter: pydantic
> model: typesafe/jev-latest

[ticket] = I was charged twice for the same invoice.
>> Does <ticket> describe a duplicate charge? [duplicate_charge: bool]

`print(decision_info("duplicate_charge").probability)`
`print(decision_info("duplicate_charge").threshold)`

[ticket] := I was charged only once.
`print(decision_info("duplicate_charge").matches_inputs(ticket=ticket))`
````

The helper resolves the nearest lexical binding. For an interactive session,
`session.decision_info("duplicate_charge")` inspects a top-level binding without
executing another fragment. Unknown names raise `NameError`; values without Jev
evidence return `None`.

Evidence includes the provider/model, source location, Noul probability, the
threshold used for boolean conversion, and Choice/Score confidence and
distributions when the provider supplied them. Noul does not gain an invented
confidence value. Multiple fields produced by one template share one call record
while retaining field-specific evidence. For a nested or multilabel output,
`answers` contains each matching child path separately; Kedi never merges several
Noul answers into one probability.

`state_fingerprint`, `criteria_fingerprint`, `config_fingerprint`, and
`request_fingerprint` identify the evaluated provider state, resolved criteria,
decision configuration, and their combined request. These are one-way identities,
not recoverable prompt copies.

`matches_inputs(**values)` performs a local fingerprint comparison over the
explicit `<name>` inputs. It makes no model or tool call and does not claim that
history or external state is unchanged. Reassigning an input leaves the historical
record intact, so this check can report `False`. Reassigning the output removes the
record from that current binding. Kedi does not automatically re-evaluate a
decision or apply a new threshold.

Decision records participate in strict interactive-session dump/load. They contain
versioned fingerprints, not recoverable copies of the original input text. A
fingerprint is an identity check, not anonymization; do not publish snapshots that
may contain sensitive provider evidence.

## Python API

```python
from typing import Annotated
from pydantic import BaseModel
from pydantic_ai import Agent
from kedi_typesafe import Probability, TypeSafeModel

class Assessment(BaseModel):
    supported: bool
    probability: Probability

async def assess():
    async with TypeSafeModel(threshold=0.9) as model:
        result = await Agent(model, output_type=Assessment).run(
            "Reference: Ankara is Turkey's capital. Claim: Turkey's capital is Ankara."
        )
        return result.output
```

LangChain uses `kedi_typesafe.integrations.langchain.TypeSafeChatModel` and
`with_structured_output(Assessment, include_raw=True)`. Raw results expose decision
evidence, provider probabilities/confidence when available, and usage. Evidence is
metadata, not an additional generated output field. Streaming exposes the completed
assessment; it does not simulate token-by-token Jev generation.

Reuse model instances for warm connections. Close owned models using their context
manager or `aclose`; caller-supplied clients remain caller-owned. Configure transport
timeout on the constructor. Unsupported generation settings are rejected.

## Capture Decisions from Python Calls

`kedi.capture_decisions()` collects the completed template decisions produced by
`@kedi.query` and `@kedi.bind` calls without changing their return types:

```python
import kedi

@kedi.query(adapter="pydantic", model="typesafe/jev-latest")
def review(ticket: str) -> bool:
    """kedi
    >> Does <ticket> describe a duplicate charge? [duplicate: bool]
    = `duplicate`
    """

with kedi.capture_decisions() as run:
    duplicate = review("I was charged twice for the same invoice.")

for decision in run.decisions:
    print(decision.field_path, decision.probability, decision.threshold)
```

`decisions` is a tuple of immutable `DecisionInfo` views, one per output binding,
in call completion order. Multiple fields share their `call_id`. These historical
snapshots remain accessible after the function returns. Nested capture scopes
also contribute to their enclosing scope; separate concurrent scopes are isolated.
Use regular `with` around `await` calls and await desired work before exiting.
Exit does not wait for pending work; the capture stops accepting records.

Capturing makes no additional model calls. Response-cache hits, failed calls, and
outputs without provider evidence do not create decision records. Successfully
completed decisions remain available if a later call raises. This captures typed
template outputs, not implicit control-flow claims or arbitrary SDK calls.

## Explicit Tool Routing

Both framework integrations support opt-in selection of registered tools. Jev may
select a zero-argument tool for framework execution. A tool requiring arguments
produces a `ToolCallProposed` exception for an explicit argument-producing handler;
it does not invent arguments or silently delegate to an LLM.

Tool selection has its own `typesafe_tool_call_threshold` (default 0.6, inclusive).
It is not the claim threshold. Selection is not authorization: retain Kedi hooks,
approval policy, and framework execution limits. Review or fallback behavior must
be explicitly written by the application.

## Migration from 0.1

The extended integration defaults to strict `> 0.85`, rather than the old 0.5
threshold. Set an explicit threshold when migrating an existing decision policy.
Do not assume an unwrapped upstream model enforces this policy: Kedi rejects that
model for claims when the policy cannot be enforced.

The package pins the upstream integration versions because it extends schema and
decision behavior at tested framework boundaries. Upgrade those pins together with
the compatibility tests, not independently.
