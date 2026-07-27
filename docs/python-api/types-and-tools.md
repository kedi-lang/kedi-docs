# Types and Tools

## Register Types with `@kedi.type`

`@kedi.type` makes Python classes usable in Kedi output annotations and Python
expressions:

```python
import kedi


@kedi.type
class Finding:
    severity: str
    message: str
```

Bare classes are converted to standard dataclasses. The decorated name is
rebound to the resulting class.

## Pydantic Models

Existing Pydantic models are retained:

```python
from pydantic import BaseModel, Field


@kedi.type
class Review(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    summary: str


@kedi.query
def review(text: str) -> Review:
    """kedi
    >> Review <text> and return [result: Review].
    = `result`
    """
    ...
```

The selected adapter receives the Pydantic schema. Validation is performed by
the adapter/model integration when producing the typed output.

## Pydantic Dataclasses

Pydantic dataclasses are recognized without reconversion:

```python
from pydantic.dataclasses import dataclass


@kedi.type
@dataclass
class Entity:
    name: str
    confidence: float
```

Place `@kedi.type` above `@dataclass` so it receives the finished Pydantic
dataclass.

## Standard Dataclasses

Standard dataclasses are also retained:

```python
from dataclasses import dataclass


@kedi.type
@dataclass
class Coordinate:
    latitude: float
    longitude: float
```

Whether an adapter can produce a particular dataclass schema depends on that
adapter's structured-output support.

## Bare Class Conversion

For a simple record, no explicit dataclass decorator is required:

```python
@kedi.type
class Label:
    name: str
    confidence: float = 1.0
```

Kedi applies `dataclasses.dataclass`. Methods and supported dataclass defaults
remain available. Classes that require custom metaclass behavior should be
defined explicitly rather than relying on conversion.

## Automatic Type Injection

`inject=True` is the default. The type is injected only for query/bind
callables defined in the same Python module:

```python
@kedi.type
class Result:
    value: str
```

Disable implicit injection:

```python
@kedi.type(inject=False)
class InternalResult:
    value: str


@kedi.query(env={"InternalResult": InternalResult})
def extract(text: str) -> InternalResult:
    """kedi
    >> Extract [result: InternalResult] from <text>.
    = `result`
    """
    ...
```

Configured and local `env` values override auto-injected type names. This can
be useful for dynamic schemas but should be deliberate.

## Register Tools with `@kedi.tool`

The tool decorator preserves a callable while attaching adapter metadata:

```python
@kedi.tool
def lookup_order(order_id: str) -> dict[str, object]:
    """Return public status information for one order."""
    return {"id": order_id, "status": "queued"}
```

Register it through `configure`, `context`, `query`, or `bind`, then opt in
inside Kedi:

```python
@kedi.query(tools=[lookup_order])
def answer(question: str) -> str:
    """kedi
    > use: lookup_order
>> Use the order lookup when needed. Return [answer: str] for <question>.
    = `answer`
    """
    ...
```

Decoration alone does not make the tool globally available.

## Names, Descriptions, and Retries

Override metadata and retry transient callable errors:

```python
@kedi.tool(
    name="search_docs",
    description="Search approved project documentation.",
    retries=2,
    risk="read_only",
)
def search_index(query: str) -> list[str]:
    return index.search(query)
```

The registered name defaults to `__name__`; description defaults to the
docstring. `retries=2` means at most three total attempts. Retries catch normal
`Exception` failures for both sync and async callables; they do not retry
`BaseException` subclasses. Negative retry counts are invalid.

## Tool Risk Metadata

Every tool is classified as:

- `read_only`;
- `mutating`;
- `sensitive`.

Custom tools default to `mutating`. Mark a tool `read_only` only if it cannot
change external or local state and cannot expose sensitive data:

```python
@kedi.tool(risk="sensitive")
def read_secret(name: str) -> str:
    ...
```

Risk participates in approval. Read-only calls are automatically allowed;
mutating and sensitive calls require an allow policy or dynamic decision.

## Tool Argument Shadowing

The runtime environment cannot safely contain a function argument and a tool
under the same registered name:

```python
@kedi.tool(name="search")
def search_docs(query: str) -> list[str]:
    return []


@kedi.query(tools=[search_docs])
def answer(search: str) -> str:
    """kedi
    = <search>
    """
    ...
```

Calling `answer(...)` raises `KediExecutionError`. Rename either the parameter
or the tool. Kedi rejects the collision rather than allowing input to shadow a
callable capability.
