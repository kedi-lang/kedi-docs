# Creating Custom Adapters

Learn how to build custom adapters to integrate Kedi with any LLM framework or provider.

---

## The AgentAdapter Protocol

All Kedi adapters must implement the `AgentAdapter` protocol:

```python
from typing import Any, Protocol, TypeVar

T = TypeVar("T")

class AgentAdapter(Protocol[T]):
    """Protocol that all Kedi adapters must implement."""
    
    async def produce(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ) -> T:
        """
        Async method to produce structured output from an LLM.
        
        Args:
            template: The prompt template (may include [field] placeholders)
            output_schema: Dict mapping field names to Python types
            **kwargs: Additional provider-specific arguments
            
        Returns:
            An object with attributes matching output_schema keys
        """
        ...
    
    def produce_sync(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ) -> T:
        """
        Synchronous version of produce().
        
        Typically wraps the async version with asyncio.run().
        """
        ...
```

---

## Basic Implementation

Here's a minimal adapter implementation:

```python
import asyncio
from pydantic import create_model
from typing import Any

class MyAdapter:
    """A custom Kedi adapter."""
    
    def __init__(self, model: str = "my-default-model"):
        self.model = model
    
    def _build_output_model(self, output_schema: dict[str, type]):
        """Create a Pydantic model for validation."""
        return create_model(
            "Output",
            **{k: (v, ...) for k, v in output_schema.items()}
        )
    
    async def produce(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ):
        """Generate structured output from the LLM."""
        # 1. Build output model for validation
        OutputModel = self._build_output_model(output_schema)
        
        # 2. Call your LLM (implement _call_llm)
        raw_response = await self._call_llm(template, output_schema)
        
        # 3. Parse and validate response
        return OutputModel(**raw_response)
    
    def produce_sync(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ):
        """Sync wrapper for produce()."""
        return asyncio.run(self.produce(template, output_schema, **kwargs))
    
    async def _call_llm(
        self,
        template: str,
        output_schema: dict[str, type]
    ) -> dict:
        """Your LLM API call logic goes here."""
        # Implement your LLM call
        # Return a dict with keys matching output_schema
        raise NotImplementedError
```

---

## Complete Example: OpenAI Adapter

Here's a full adapter using the OpenAI API directly:

```python
import asyncio
import json
from typing import Any
from pydantic import create_model
from openai import AsyncOpenAI

class OpenAIDirectAdapter:
    """Direct OpenAI API adapter for Kedi."""
    
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.client = AsyncOpenAI()
    
    def _build_output_model(self, output_schema: dict[str, type]):
        """Create a Pydantic model from the output schema."""
        return create_model(
            "DynamicOutput",
            **{k: (v, ...) for k, v in output_schema.items()}
        )
    
    def _build_json_schema(self, output_schema: dict[str, type]) -> dict:
        """Convert Python types to JSON schema for OpenAI."""
        type_map = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
        }
        
        properties = {}
        for name, pytype in output_schema.items():
            origin = getattr(pytype, "__origin__", None)
            
            if origin is list:
                item_type = pytype.__args__[0]
                properties[name] = {
                    "type": "array",
                    "items": type_map.get(item_type, {"type": "string"})
                }
            else:
                properties[name] = type_map.get(pytype, {"type": "string"})
        
        return {
            "type": "object",
            "properties": properties,
            "required": list(output_schema.keys())
        }
    
    async def produce(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ):
        """Call OpenAI and return structured output."""
        OutputModel = self._build_output_model(output_schema)
        json_schema = self._build_json_schema(output_schema)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": f"{template}\n\nRespond with JSON matching this schema:\n{json.dumps(json_schema, indent=2)}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        return OutputModel(**data)
    
    def produce_sync(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ):
        """Sync wrapper."""
        return asyncio.run(self.produce(template, output_schema, **kwargs))
```

---

## Example: Ollama Adapter

Adapter for local models using Ollama:

```python
import asyncio
import json
import httpx
from pydantic import create_model
from typing import Any

class OllamaAdapter:
    """Adapter for local Ollama models."""
    
    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url
    
    def _build_output_model(self, output_schema: dict[str, type]):
        return create_model(
            "Output",
            **{k: (v, ...) for k, v in output_schema.items()}
        )
    
    async def produce(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ):
        OutputModel = self._build_output_model(output_schema)
        
        # Build prompt with JSON instruction
        fields = ", ".join(output_schema.keys())
        prompt = f"""{template}

Respond with ONLY a valid JSON object with these fields: {fields}
No additional text before or after the JSON."""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["response"]
            
            # Parse JSON from response
            parsed = json.loads(content)
            return OutputModel(**parsed)
    
    def produce_sync(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ):
        return asyncio.run(self.produce(template, output_schema, **kwargs))
```

---

## Example: Mock Adapter for Testing

Useful for unit tests:

```python
import asyncio
from pydantic import create_model
from typing import Any, Dict

class MockAdapter:
    """Mock adapter for testing Kedi programs."""
    
    def __init__(self, responses: Dict[str, dict] = None):
        """
        Args:
            responses: Dict mapping template substrings to response dicts
        """
        self.responses = responses or {}
        self.calls = []  # Track all calls for assertions
    
    def _build_output_model(self, output_schema: dict[str, type]):
        return create_model(
            "Output",
            **{k: (v, ...) for k, v in output_schema.items()}
        )
    
    def add_response(self, template_contains: str, response: dict):
        """Add a mock response for templates containing the given string."""
        self.responses[template_contains] = response
    
    async def produce(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ):
        # Track the call
        self.calls.append({
            "template": template,
            "output_schema": output_schema,
            "kwargs": kwargs
        })
        
        OutputModel = self._build_output_model(output_schema)
        
        # Find matching response
        for key, response in self.responses.items():
            if key in template:
                return OutputModel(**response)
        
        # Default: generate placeholder values
        defaults = {}
        for name, pytype in output_schema.items():
            if pytype == str:
                defaults[name] = f"mock_{name}"
            elif pytype == int:
                defaults[name] = 42
            elif pytype == float:
                defaults[name] = 3.14
            elif pytype == bool:
                defaults[name] = True
            elif getattr(pytype, "__origin__", None) is list:
                defaults[name] = []
            else:
                defaults[name] = f"mock_{name}"
        
        return OutputModel(**defaults)
    
    def produce_sync(
        self,
        template: str,
        output_schema: dict[str, type],
        **kwargs: Any
    ):
        return asyncio.run(self.produce(template, output_schema, **kwargs))
```

**Usage in tests:**

```python
def test_kedi_program():
    adapter = MockAdapter()
    adapter.add_response("capital of France", {"capital": "Paris"})
    adapter.add_response("population", {"population": 67000000})
    
    runtime = KediRuntime(adapter=adapter)
    # ... run your program
    
    # Assert calls were made
    assert len(adapter.calls) == 2
    assert "capital" in adapter.calls[0]["output_schema"]
```

---

## Using Your Custom Adapter

### With KediRuntime

```python
from kedi.core import KediRuntime

adapter = MyAdapter(model="my-model")
runtime = KediRuntime(adapter=adapter)

# Run a program
result = runtime.run_main()
```

### Registering Globally

To use your adapter from the CLI, you can register it:

```python
# In your package's __init__.py or a plugin file
from kedi.agent_adapter import register_adapter
from my_package import MyAdapter

register_adapter("my-adapter", MyAdapter)
```

Then use:

```bash
kedi program.kedi --adapter my-adapter
```

---

## Best Practices

!!! tip "Use Pydantic for Validation"
    Always use `pydantic.create_model()` to build your output types. This ensures consistent validation across all adapters.

!!! tip "Handle Type Conversion"
    LLMs return strings. Convert types appropriately:
    
    ```python
    def _convert_value(self, value: Any, expected_type: type) -> Any:
        if expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        elif expected_type == bool:
            return value.lower() in ("true", "yes", "1")
        return value
    ```

!!! tip "Implement Retries"
    LLMs can fail or return invalid JSON. Add retry logic:
    
    ```python
    import tenacity
    
    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(min=1, max=10)
    )
    async def produce(self, ...):
        ...
    ```

!!! tip "Add Logging"
    Log requests and responses for debugging:
    
    ```python
    import logging
    
    logger = logging.getLogger(__name__)
    
    async def produce(self, template, output_schema, **kwargs):
        logger.debug(f"Calling LLM with template: {template[:100]}...")
        result = await self._call_llm(...)
        logger.debug(f"LLM returned: {result}")
        return result
    ```

---

## Type Handling Reference

Common Python types and their handling:

| Python Type | JSON Schema | Notes |
|-------------|-------------|-------|
| `str` | `{"type": "string"}` | Default type |
| `int` | `{"type": "integer"}` | Parse from string |
| `float` | `{"type": "number"}` | Parse from string |
| `bool` | `{"type": "boolean"}` | Handle "true"/"false" |
| `list[str]` | `{"type": "array", "items": {"type": "string"}}` | Nested arrays |
| `dict[str, Any]` | `{"type": "object"}` | Free-form objects |
| Custom Model | Full JSON schema | Use `model.model_json_schema()` |

---

## See Also

- [AgentAdapter Overview](index.md) — Understanding the adapter system
- [PydanticAdapter](pydantic.md) — Reference implementation
- [DSPyAdapter](dspy.md) — Alternative implementation
- [Python Interop](../concepts/python-interop.md) — Using adapters in Python
