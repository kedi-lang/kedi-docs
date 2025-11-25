# PydanticAdapter

The `PydanticAdapter` is Kedi's default adapter, built on [PydanticAI](https://ai.pydantic.dev/). It provides robust type validation and structured outputs using Pydantic models.

---

## Overview

The PydanticAdapter leverages PydanticAI's `Agent` class to:

- Generate structured JSON outputs from LLMs
- Validate responses against Pydantic models
- Support multiple model providers (OpenAI, Anthropic, Groq, etc.)
- Handle async/sync execution seamlessly

---

## Usage

### Command Line

```bash
# Use PydanticAdapter (default)
kedi program.kedi --adapter pydantic

# With specific model
kedi program.kedi --adapter pydantic --adapter-model openai:gpt-4o
```

### Python API

```python
from kedi.agent_adapter import PydanticAdapter
from kedi.core import KediRuntime

# Create adapter
adapter = PydanticAdapter(model="openai:gpt-4o")

# Use with runtime
runtime = KediRuntime(adapter=adapter)

# Or use directly
result = adapter.produce_sync(
    template="List 3 colors: [colors: list[str]]",
    output_schema={"colors": list[str]}
)
print(result.colors)  # ["red", "blue", "green"]
```

---

## How It Works

### 1. Dynamic Model Creation

When you define outputs in Kedi, the adapter creates a dynamic Pydantic model:

```python title="example.kedi"
[name: str], [age: int], and [hobbies: list[str]] describe the person.
```

This generates:

```python
from pydantic import BaseModel, create_model

OutputModel = create_model(
    "DynamicOutput",
    name=(str, ...),
    age=(int, ...),
    hobbies=(list[str], ...)
)
```

### 2. Agent Execution

The adapter uses PydanticAI's `Agent.run()` with `output_type`:

```python
from pydantic_ai import Agent

agent = Agent(model="openai:gpt-4o")
result = await agent.run(
    prompt,
    output_type=OutputModel
)
```

### 3. Response Validation

PydanticAI ensures the LLM response matches the expected types, retrying if necessary.

---

## Supported Models

PydanticAdapter supports all models available through PydanticAI:

### OpenAI

```bash
kedi program.kedi --adapter-model openai:gpt-4o
kedi program.kedi --adapter-model openai:gpt-4o-mini
kedi program.kedi --adapter-model openai:gpt-3.5-turbo
```

### Anthropic

```bash
kedi program.kedi --adapter-model anthropic:claude-3-5-sonnet-latest
kedi program.kedi --adapter-model anthropic:claude-3-haiku-20240307
kedi program.kedi --adapter-model anthropic:claude-3-opus-20240229
```

### Groq

```bash
kedi program.kedi --adapter-model groq:llama-3.1-70b-versatile
kedi program.kedi --adapter-model groq:llama-3.1-8b-instant
kedi program.kedi --adapter-model groq:mixtral-8x7b-32768
```

### Google

```bash
kedi program.kedi --adapter-model google:gemini-1.5-pro
kedi program.kedi --adapter-model google:gemini-1.5-flash
```

### Ollama (Local)

```bash
kedi program.kedi --adapter-model ollama:llama3
kedi program.kedi --adapter-model ollama:mistral
kedi program.kedi --adapter-model ollama:codellama
```

---

## Type Support

PydanticAdapter supports all Python types that Pydantic can validate:

### Basic Types

```python
[name: str]           # String
[count: int]          # Integer
[score: float]        # Float
[active: bool]        # Boolean
```

### Collection Types

```python
[items: list[str]]           # List of strings
[numbers: list[int]]         # List of integers
[mapping: dict[str, int]]    # Dictionary
[unique: set[str]]           # Set
```

### Optional Types

```python
[nickname: str | None]       # Optional string
[age: int | None]            # Optional integer
```

### Custom Types

```python
~Person(name, age: int, email)
[user: Person]               # Custom Pydantic model
[team: list[Person]]         # List of custom models
```

---

## Configuration

### Environment Variables

```bash
# Required for OpenAI
export OPENAI_API_KEY="sk-..."

# Required for Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Required for Groq
export GROQ_API_KEY="gsk_..."

# Required for Google
export GOOGLE_API_KEY="..."
```

### Default Model

The default model is `groq:qwen/qwen3-32b`. Override with:

```bash
kedi program.kedi --adapter-model openai:gpt-4o
```

---

## Error Handling

PydanticAdapter handles common errors gracefully:

### Validation Errors

If the LLM returns invalid data, Pydantic raises a validation error:

```
ValidationError: 1 validation error for DynamicOutput
age
  value is not a valid integer (type=type_error.integer)
```

### API Errors

API errors (rate limits, auth failures) are propagated with helpful messages:

```
AuthenticationError: Invalid API key for provider 'openai'
```

---

## Best Practices

!!! tip "Use Specific Types"
    Be specific with types to get better LLM outputs:
    
    ```python
    # Good - specific type
    [cities: list[str]]
    
    # Less good - generic
    [cities]  # Defaults to str
    ```

!!! tip "Validate with Custom Types"
    Use custom types for complex structured data:
    
    ```python
    ~Address(street, city, country, postal_code)
    ~Person(name, age: int, address: Address)
    
    [person: Person]  # Fully validated nested structure
    ```

!!! tip "Handle Optional Fields"
    Use union types for optional fields:
    
    ```python
    [nickname: str | None]  # May be null
    ```

---

## See Also

- [AgentAdapter Overview](index.md) — Understanding the adapter system
- [DSPyAdapter](dspy.md) — Alternative adapter using DSPy
- [Custom Adapters](custom.md) — Building your own adapter
- [Variables & Types](../concepts/variables-and-types.md) — Kedi's type system
