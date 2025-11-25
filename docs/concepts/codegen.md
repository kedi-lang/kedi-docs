# Code Generation

Kedi supports AI-generated procedures that are automatically implemented based on a specification. This powerful feature allows you to define *what* a procedure should do, and let the AI figure out *how*.

---

## AI-Generated Procedures

Define a procedure signature with a specification line starting with `>`:

```python
@summarize(texts: list[str]) -> str:
    > Takes a list of text documents and produces a concise summary \
    that preserves key information while reducing length by 80%
```

The `>` line is the **codegen prompt** — a natural language description of what the procedure should do.

---

## How It Works

When Kedi encounters a procedure with a `>` specification:

1. **Generate Test Cases** — The system creates test cases based on the specification
2. **Implement Procedure** — An AI agent generates the procedure implementation
3. **Run Tests** — The generated code is tested against the test cases
4. **Iterate** — If tests fail, the AI refines the implementation
5. **Cache** — Successful implementations are cached in `<filename>.cache.kedi`

---

## Syntax

```python
@procedure_name(param1: type, param2: type) -> return_type:
    > Natural language description of what the procedure should do. \
    Include details about expected behavior, edge cases, and output format.
```

!!! warning "Use Line Continuation"
    Like all template strings in Kedi, the `>` specification should be on a single logical line. Use `\` for multi-line specifications.

---

## Examples

### Text Processing

```python
@extract_keywords(text: str, max_count: int) -> list[str]:
    > Extract the most important keywords from the text. \
    Return at most max_count keywords, ordered by relevance. \
    Exclude common stop words and focus on domain-specific terms.
```

### Data Transformation

```python
@normalize_phone(phone: str, country_code: str) -> str:
    > Normalize a phone number to international format. \
    Handle various input formats like (555) 123-4567 or 555.123.4567. \
    Prepend the country code if not already present.
```

### Complex Analysis

```python
~SentimentResult(score: float, label: str, confidence: float)

@analyze_sentiment(text: str) -> SentimentResult:
    > Analyze the sentiment of the given text. \
    Return a score from -1.0 (negative) to 1.0 (positive), \
    a label (positive/negative/neutral), and confidence (0.0-1.0).
```

---

## Caching

Generated implementations are cached to avoid regeneration:

- Cache file: `<source>.cache.kedi`
- Contains the generated Python code for each procedure
- Loaded automatically on subsequent runs

### Bypassing Cache

```bash
# Force regeneration
kedi program.kedi --no-cache
```

---

## Configuration

Control code generation via CLI options:

| Option | Description | Default |
|--------|-------------|---------|
| `--codegen-agent` | Agent for code generation | `pydantic_ai` |
| `--codegen-model` | Model for code generation | `openai:gpt-4o` |
| `--codegen-retries` | Retry attempts if tests fail | `5` |
| `--no-cache` | Disable cache | `false` |

```bash
kedi program.kedi --codegen-model openai:gpt-4o --codegen-retries 10
```

---

## Best Practices

!!! tip "Be Specific"
    Provide detailed specifications with examples of expected behavior:
    
    ```python
    @format_currency(amount: float, currency: str) -> str:
        > Format a number as currency string. \
        Examples: (1234.5, "USD") -> "$1,234.50", \
        (1000, "EUR") -> "€1,000.00". \
        Use appropriate currency symbols and thousand separators.
    ```

!!! tip "Define Edge Cases"
    Mention how edge cases should be handled:
    
    ```python
    @parse_date(text: str) -> str:
        > Parse a date from natural language text and return ISO format. \
        Handle inputs like "tomorrow", "next Monday", "Jan 15". \
        Return empty string if no valid date found.
    ```

!!! tip "Use Types"
    Leverage custom types for complex return values:
    
    ```python
    ~ParsedEmail(subject: str, sender: str, date: str, body: str, attachments: list[str])
    
    @parse_email(raw_email: str) -> ParsedEmail:
        > Parse a raw email string into structured components. \
        Extract subject, sender, date, body text, and attachment filenames.
    ```

---

## See Also

- [CLI Reference](../reference/cli.md) — Codegen CLI options
- [Procedures](procedures.md) — Procedure fundamentals
- [Agent Adapters](../adapters/index.md) — How adapters work
