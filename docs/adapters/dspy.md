# DSPyAdapter

The `DSPyAdapter` integrates [DSPy](https://dspy.ai/) with Kedi, enabling prompt optimization, few-shot learning, and modular LLM programming.

---

## Overview

DSPy is a framework for algorithmically optimizing LLM prompts and weights. The DSPyAdapter brings these capabilities to Kedi:

- **Signature-based prompting** — Define inputs and outputs declaratively
- **Modular pipelines** — Compose complex LLM workflows
- **Prompt optimization** — Automatically improve prompts with optimizers
- **Few-shot learning** — Include examples to improve performance

---

## Usage

### Command Line

```bash
# Use DSPy adapter
kedi program.kedi --adapter dspy

# With specific model
kedi program.kedi --adapter dspy --adapter-model openai:gpt-4o
```

### Python API

```python
from kedi.agent_adapter import DSPyAdapter
from kedi.core import KediRuntime

# Create adapter
adapter = DSPyAdapter(model="openai:gpt-4o")

# Use with runtime
runtime = KediRuntime(adapter=adapter)

# Or use directly
result = adapter.produce_sync(
    template="What is the capital of France? [capital]",
    output_schema={"capital": str}
)
print(result.capital)  # "Paris"
```

---

## How It Works

### 1. Dynamic Signature Creation

DSPy uses "Signatures" to define input/output contracts. The adapter creates these dynamically:

```python title="example.kedi"
The capital of <country> is [capital].
```

This generates a DSPy Signature:

```python
import dspy

class DynamicSignature(dspy.Signature):
    """Generated signature for Kedi outputs."""
    capital: str = dspy.OutputField()
```

### 2. Predict Module

The adapter uses `dspy.Predict` to execute the signature:

```python
predictor = dspy.Predict(DynamicSignature)
result = predictor(prompt=template)
```

### 3. Response Extraction

Output fields are extracted and returned as an object with matching attributes.

---

## Supported Models

DSPyAdapter supports all models available through DSPy's LM interface:

### OpenAI

```bash
kedi program.kedi --adapter dspy --adapter-model openai:gpt-4o
kedi program.kedi --adapter dspy --adapter-model openai:gpt-4o-mini
```

### Anthropic

```bash
kedi program.kedi --adapter dspy --adapter-model anthropic:claude-3-5-sonnet-latest
kedi program.kedi --adapter dspy --adapter-model anthropic:claude-3-haiku-20240307
```

### Groq

```bash
kedi program.kedi --adapter dspy --adapter-model groq:llama-3.1-70b-versatile
kedi program.kedi --adapter dspy --adapter-model groq:mixtral-8x7b-32768
```

### Local Models

```bash
kedi program.kedi --adapter dspy --adapter-model ollama:llama3
```

---

## DSPy Features in Kedi

### Modular Composition

DSPy excels at composing multiple LLM calls. In Kedi:

```python title="pipeline.kedi"
@extract_entities(text) -> list[str]:
    Extract named entities from: <text>
    Entities: [entities: list[str]]
    = `entities`

@classify_sentiment(text) -> str:
    Classify sentiment of: <text>
    Sentiment: [sentiment]
    = `sentiment`

@analyze(text) -> str:
    [entities: list[str]] = `extract_entities(text)`
    [sentiment] = `classify_sentiment(text)`
    = `f"Entities: {entities}, Sentiment: {sentiment}"`
```

### Chain of Thought

DSPy supports Chain-of-Thought reasoning:

```python title="reasoning.kedi"
@solve_math(problem) -> str:
    Let's solve this step by step.
    Problem: <problem>
    
    [reasoning]
    
    Therefore, the answer is [answer].
    = `answer`
```

---

## When to Use DSPy

!!! success "Good Use Cases"
    - **Research & Experimentation** — Testing different prompting strategies
    - **Prompt Optimization** — When you want to improve prompts automatically
    - **Few-Shot Learning** — When examples improve performance
    - **Complex Pipelines** — Multi-step LLM workflows
    - **Retrieval-Augmented Generation** — Integrating with retrievers

!!! warning "Consider PydanticAdapter Instead"
    - **Production APIs** — PydanticAdapter has better type validation
    - **Simple Structured Outputs** — PydanticAI is more straightforward
    - **JSON Schema Outputs** — PydanticAI handles this natively

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
```

### DSPy Settings

The adapter configures DSPy settings automatically:

```python
import dspy

# This happens internally when you create DSPyAdapter
lm = dspy.LM("openai:gpt-4o")
dspy.settings.configure(lm=lm)
```

---

## Advanced Usage

### Custom DSPy Modules

You can extend the adapter with custom DSPy modules:

```python
import dspy
from kedi.agent_adapter import DSPyAdapter

class ChainOfThought(dspy.Module):
    def __init__(self, signature):
        super().__init__()
        self.cot = dspy.ChainOfThought(signature)
    
    def forward(self, **kwargs):
        return self.cot(**kwargs)

# Use in custom adapter
class CoTAdapter(DSPyAdapter):
    def type_builder(self, output_schema):
        signature = super().type_builder(output_schema)
        return ChainOfThought(signature)
```

### Integration with DSPy Retrievers

```python
import dspy

class RAGAdapter(DSPyAdapter):
    def __init__(self, model, retriever):
        super().__init__(model)
        self.retriever = retriever
    
    async def produce(self, template, output_schema, **kwargs):
        # Retrieve context
        context = self.retriever(template)
        
        # Augment template
        augmented = f"Context: {context}\n\n{template}"
        
        return await super().produce(augmented, output_schema, **kwargs)
```

---

## Comparison with PydanticAdapter

| Feature | PydanticAdapter | DSPyAdapter |
|---------|----------------|-------------|
| Type Validation | ✅ Strong (Pydantic) | ⚠️ Basic |
| Structured Output | ✅ Native JSON | ⚠️ Text parsing |
| Prompt Optimization | ❌ | ✅ DSPy optimizers |
| Few-Shot Learning | ⚠️ Manual | ✅ Built-in |
| Chain of Thought | ⚠️ Manual | ✅ Native |
| Production Ready | ✅ | ⚠️ Research-focused |
| Async Support | ✅ Native | ⚠️ Wrapped |

---

## Troubleshooting

!!! warning "Import Errors"
    ```
    ModuleNotFoundError: No module named 'dspy'
    ```
    
    **Solution:** Install DSPy:
    ```bash
    pip install dspy-ai
    ```

!!! warning "Model Not Configured"
    ```
    Error: No LM configured in DSPy settings
    ```
    
    **Solution:** The adapter should configure this automatically. Check your model string format:
    ```bash
    kedi program.kedi --adapter dspy --adapter-model openai:gpt-4o
    ```

---

## See Also

- [AgentAdapter Overview](index.md) — Understanding the adapter system
- [PydanticAdapter](pydantic.md) — Production-focused adapter
- [Custom Adapters](custom.md) — Building your own adapter
- [DSPy Documentation](https://dspy.ai/) — Official DSPy docs
