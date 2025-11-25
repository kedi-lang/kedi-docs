````markdown
# Python API Reference

This page documents Kedi's Python API for programmatic usage.

---

## KediRuntime

The main class for executing Kedi programs from Python.

### Basic Usage

```python
from kedi.core import KediRuntime

# Create runtime with default adapter
runtime = KediRuntime()

# Load and run a program
runtime.load_file("my_program.kedi")
result = runtime.run_main()
```

### Constructor

```python
KediRuntime(
    adapter: AgentAdapter | None = None,
    codegen_agent: str = "pydantic_ai",
    codegen_model: str = "openai:gpt-4o",
    codegen_retries: int = 5,
    cache: bool = True
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `adapter` | `AgentAdapter \| None` | LLM adapter instance. Uses PydanticAdapter if None. |
| `codegen_agent` | `str` | Agent for AI-generated procedures. |
| `codegen_model` | `str` | Model for code generation. |
| `codegen_retries` | `int` | Retry attempts for code generation. |
| `cache` | `bool` | Enable/disable caching for generated procedures. |

### Methods

#### `load_file(path: str) -> None`

Load a Kedi program from a file.

```python
runtime.load_file("program.kedi")
```

#### `load_source(source: str) -> None`

Load a Kedi program from a string.

```python
source = """
@greet(name):
    Hello, <name>! Welcome to [greeting].
    = `greeting`
"""
runtime.load_source(source)
```

#### `run_main() -> Any`

Execute the program and return the final result.

```python
result = runtime.run_main()
print(result)
```

#### `run_tests() -> TestResults`

Run all `@test:` blocks in the program.

```python
results = runtime.run_tests()
print(f"Passed: {results.passed}, Failed: {results.failed}")
```

#### `run_evals() -> EvalResults`

Run all `@eval:` blocks in the program.

```python
results = runtime.run_evals()
for metric in results.metrics:
    print(f"{metric.name}: {metric.score}")
```

#### `call_procedure(name: str, **kwargs) -> Any`

Call a specific procedure by name.

```python
capital = runtime.call_procedure("get_capital", country="France")
```

---

## AgentAdapter Protocol

All LLM adapters must implement this protocol.

```python
from typing import Any, Protocol, TypeVar

T = TypeVar("T")

class AgentAdapter(Protocol[T]):
    async def produce(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ) -> T:
        """Generate structured output from an LLM."""
        ...
    
    def produce_sync(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ) -> T:
        """Synchronous version of produce()."""
        ...
```

### Using Built-in Adapters

```python
from kedi.agent_adapter import PydanticAdapter, DSPyAdapter

# PydanticAI adapter
pydantic_adapter = PydanticAdapter(model="openai:gpt-4o")

# DSPy adapter
dspy_adapter = DSPyAdapter(model="openai:gpt-4o")

# Use with runtime
runtime = KediRuntime(adapter=pydantic_adapter)
```

---

## Custom Types

Define and use custom Kedi types from Python.

### Defining Types

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    email: str

# Register with runtime
runtime.register_type("Person", Person)
```

### Using in Kedi

```python
# The Person type is now available
@create_user(name, age: int, email) -> Person:
    Create a new user [person: Person] with name <name>, age <age>, and email <email>.
    = `person`
```

---

## Complete Example

```python
from kedi.core import KediRuntime
from kedi.agent_adapter import PydanticAdapter

# Create adapter with specific model
adapter = PydanticAdapter(model="openai:gpt-4o")

# Create runtime
runtime = KediRuntime(
    adapter=adapter,
    codegen_model="openai:gpt-4o",
    codegen_retries=10
)

# Load program
runtime.load_file("research_assistant.kedi")

# Run main program
report = runtime.run_main()
print(report)

# Or call specific procedure
summary = runtime.call_procedure("summarize", text="Long text here...")
print(summary)

# Run tests
test_results = runtime.run_tests()
if test_results.failed > 0:
    print(f"⚠️ {test_results.failed} tests failed")
    for failure in test_results.failures:
        print(f"  - {failure.name}: {failure.message}")
```

---

## Error Handling

```python
from kedi.core import KediRuntime, KediError, KediSyntaxError, KediRuntimeError

try:
    runtime = KediRuntime()
    runtime.load_file("program.kedi")
    result = runtime.run_main()
except KediSyntaxError as e:
    print(f"Syntax error at line {e.line}: {e.message}")
except KediRuntimeError as e:
    print(f"Runtime error: {e.message}")
except KediError as e:
    print(f"Kedi error: {e}")
```

---

## Async Usage

For async applications, use the async methods directly:

```python
import asyncio
from kedi.core import KediRuntime
from kedi.agent_adapter import PydanticAdapter

async def main():
    adapter = PydanticAdapter(model="openai:gpt-4o")
    runtime = KediRuntime(adapter=adapter)
    runtime.load_file("program.kedi")
    
    # Async execution
    result = await runtime.run_main_async()
    print(result)

asyncio.run(main())
```

---

## See Also

- [CLI Reference](cli.md) — Command-line usage
- [Agent Adapters](../adapters/index.md) — Adapter documentation
- [Custom Adapters](../adapters/custom.md) — Building custom adapters
- [Python Interop](../concepts/python-interop.md) — Using Python in Kedi

````
