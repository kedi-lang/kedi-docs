# CLI Reference

Kedi provides a command-line interface for running Kedi programs. This page covers all available options.

---

## Basic Usage

```bash
kedi <file.kedi> [options]
```

Running a Kedi file executes the program directly:

```bash
# Run a program
kedi my_program.kedi

# Run with specific adapter
kedi my_program.kedi --adapter pydantic

# Run with tests
kedi my_program.kedi --test
```

---

## Options

### `--adapter`

Choose the LLM adapter to use for execution.

| Value | Description |
|-------|-------------|
| `pydantic` | Use PydanticAI adapter (default) |
| `dspy` | Use DSPy adapter |

```bash
kedi program.kedi --adapter pydantic
kedi program.kedi --adapter dspy
```

---

### `--adapter-model`

Specify the model to use with the selected adapter.

**Format:** `provider:model_name`

```bash
# OpenAI models
kedi program.kedi --adapter-model openai:gpt-4o
kedi program.kedi --adapter-model openai:gpt-4o-mini

# Anthropic models
kedi program.kedi --adapter-model anthropic:claude-3-5-sonnet-latest

# Groq models
kedi program.kedi --adapter-model groq:llama-3.1-70b-versatile

# Google models
kedi program.kedi --adapter-model google:gemini-1.5-pro

# Ollama (local models)
kedi program.kedi --adapter-model ollama:llama3
```

**Default:** `groq:qwen/qwen3-32b`

!!! tip "Provider-specific API Keys"
    Each provider requires its own API key set as an environment variable:
    
    - OpenAI: `OPENAI_API_KEY`
    - Anthropic: `ANTHROPIC_API_KEY`
    - Groq: `GROQ_API_KEY`
    - Google: `GOOGLE_API_KEY`

---

### `--test`

Run test blocks (`@test:`) defined in the Kedi program.

```bash
kedi program.kedi --test
```

**Example test block:**

```python title="example.kedi"
@get_capital(country) -> str:
    The capital of <country> is [capital].
    = `capital`

@test: get_capital:
    > case: france:
        `assert get_capital("France") == "Paris"`
    
    > case: japan:
        `assert get_capital("Japan") == "Tokyo"`
```

---

### `--eval`

Run evaluation metrics (`@eval:`) defined in the Kedi program.

```bash
kedi program.kedi --eval
```

**Example eval block:**

```python title="example.kedi"
@summarize(text) -> str:
    Summarize this text: <text>. Provide a concise [summary].
    = `summary`

@eval: summarize:
    > metric: compression_ratio:
        = ```
        original = "This is a very long text..."
        summary = summarize(original)
        ratio = len(summary) / len(original)
        return (1.0 - ratio, f"Compressed to {ratio:.1%}")
        ```
```

---

### `--codegen-agent`

Specify the agent to use for AI-generated procedures (procedures with `>` specification).

| Value | Description |
|-------|-------------|
| `pydantic_ai` | Use PydanticAI for code generation (default) |
| `mock` | Use mock agent for testing |

```bash
kedi program.kedi --codegen-agent pydantic_ai
```

---

### `--codegen-model`

Specify the model to use for code generation.

```bash
kedi program.kedi --codegen-model openai:gpt-4o
kedi program.kedi --codegen-model anthropic:claude-3-5-sonnet-latest
```

**Default:** `openai:gpt-4o`

!!! info "Codegen vs Runtime Models"
    The `--codegen-model` is used only for generating procedure implementations from specifications (`>`). The `--adapter-model` is used for all runtime LLM calls.

---

### `--codegen-retries`

Number of retry attempts for code generation if tests fail.

```bash
kedi program.kedi --codegen-retries 10
```

**Default:** `5`

---

### `--no-cache`

Disable caching for AI-generated procedures. By default, generated procedures are cached in `<filename>.cache.kedi`.

```bash
# Force regeneration of all AI procedures
kedi program.kedi --no-cache
```

---

## Environment Variables

Kedi respects the following environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | API key for OpenAI models |
| `ANTHROPIC_API_KEY` | API key for Anthropic models |
| `GROQ_API_KEY` | API key for Groq models |
| `GOOGLE_API_KEY` | API key for Google models |
| `KEDI_ADAPTER` | Default adapter (overridden by `--adapter`) |
| `KEDI_ADAPTER_MODEL` | Default model (overridden by `--adapter-model`) |
| `KEDI_CODEGEN_AGENT` | Default codegen agent |
| `KEDI_CODEGEN_MODEL` | Default codegen model |
| `KEDI_CODEGEN_RETRIES` | Default codegen retries |

**Example:**

```bash
export OPENAI_API_KEY="sk-..."
export GROQ_API_KEY="gsk_..."
export KEDI_ADAPTER="pydantic"
export KEDI_ADAPTER_MODEL="openai:gpt-4o"

kedi my_program.kedi
```

---

## Complete Examples

### Simple Execution

```bash
# Run a basic program
kedi hello.kedi
```

### Production Setup

```bash
# Run with OpenAI GPT-4 for runtime and code generation
kedi app.kedi \
    --adapter pydantic \
    --adapter-model openai:gpt-4o \
    --codegen-model openai:gpt-4o \
    --codegen-retries 10
```

### Development Setup

```bash
# Run with fast Groq model and no cache for iteration
kedi app.kedi \
    --adapter pydantic \
    --adapter-model groq:llama-3.1-70b-versatile \
    --no-cache
```

### Running Tests

```bash
# Run program with tests
kedi app.kedi --test
```

### Running Evaluations

```bash
# Run program with evaluations
kedi app.kedi --eval
```

### Using DSPy

```bash
# Run with DSPy adapter
kedi app.kedi \
    --adapter dspy \
    --adapter-model openai:gpt-4o-mini
```

### Local Models with Ollama

```bash
# Run with local Ollama model
kedi app.kedi --adapter-model ollama:llama3
```

---

## Output and Logging

Kedi outputs the final result of your program to stdout. Debug information and logs are written to stderr.

```bash
# Capture output to file
kedi program.kedi > output.txt

# Separate stdout and stderr
kedi program.kedi > output.txt 2> debug.log
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | Runtime error or test failure |

---

## Troubleshooting

### Common Issues

!!! warning "API Key Not Found"
    ```
    Error: No API key found for provider 'openai'
    ```
    
    **Solution:** Set the appropriate environment variable:
    ```bash
    export OPENAI_API_KEY="your-key-here"
    ```

!!! warning "Model Not Available"
    ```
    Error: Model 'gpt-5' not found
    ```
    
    **Solution:** Check the model name and ensure it's available for your provider.

!!! warning "Cache File Issues"
    If you're seeing stale generated procedures:
    ```bash
    # Delete cache and regenerate
    rm program.cache.kedi
    kedi program.kedi
    
    # Or use --no-cache
    kedi program.kedi --no-cache
    ```

---

## See Also

- [Agent Adapters](../adapters/index.md) — Learn about PydanticAI and DSPy adapters
- [Code Generation](../concepts/codegen.md) — How AI-generated procedures work
- [Procedures](../concepts/procedures.md) — Writing procedures and test blocks
