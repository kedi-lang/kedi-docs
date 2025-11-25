# Installation

Getting started with Kedi is straightforward. It's a Python package that you can install in minutes.

---

## Requirements

| Requirement | Version                     |
| ----------- | --------------------------- |
| Python      | 3.10+                       |
| pip         | latest                      |
| LLM API Key | OpenAI / Anthropic / Ollama |

---

## Installation Methods

=== "uv (Recommended)"

    ```bash
    uv add kedi
    ```

=== "pip"

    ```bash
    pip install kedi
    ```

=== "From Source"

    ```bash
    git clone https://github.com/kedi-lang/kedi.git
    cd kedi
    pip install -e .
    ```

---

## Verify Installation

```bash
kedi --version
```

Expected output:

```
kedi 0.1.0
```

---

## Configuration

### LLM Provider Setup

Kedi supports multiple LLM providers. Configure via environment variables or a `.env` file:

=== "OpenAI"

    ```bash title=".env"
    OPENAI_API_KEY=sk-...
    OPENAI_MODEL=gpt-4o
    ```

=== "Anthropic"

    ```bash title=".env"
    ANTHROPIC_API_KEY=sk-ant-...
    ANTHROPIC_MODEL=claude-sonnet-4-20250514
    ```

=== "Ollama (Local)"

    ```bash title=".env"
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL=llama3
    ```

### Environment Priority

1. Environment variables (highest priority)
2. `.env` file in current directory
3. `.env` file in home directory
4. Default values

---

## Editor Support

### VS Code Extension

Install the Kedi VS Code extension for syntax highlighting:

1. Open VS Code
2. Go to Extensions (`Cmd+Shift+X`)
3. Search for "Kedi"
4. Click Install

!!! tip "Syntax Highlighting"
    The VS Code extension provides syntax highlighting, error detection, and code snippets for `.kedi` files.

---

## Troubleshooting

!!! warning "Common Issues"
    **Python version too old:**
    ```bash
    python --version  # Must be 3.10+
    ```
    
    **Missing API key:**
    ```bash
    export OPENAI_API_KEY="your-key-here"
    ```

---

## Next Steps

[:material-rocket-launch: Write Your First Program](hello-world.md){ .md-button .md-button--primary }
