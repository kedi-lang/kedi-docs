# Troubleshooting

This guide covers common issues you might encounter when working with Kedi.

## Installation Issues

### Package Not Found

```
ERROR: No matching distribution found for kedi
```

**Solution:** Ensure you're using Python 3.10 or higher:

```bash
python --version
pip install --upgrade pip
pip install kedi
```

### Missing Dependencies

```
ModuleNotFoundError: No module named 'pydantic'
```

**Solution:** Install with all dependencies:

```bash
pip install "kedi[all]"
```

## Runtime Errors

### LLM Configuration Missing

```
KeyError: 'OPENAI_API_KEY'
```

**Solution:** Set your API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

### Type Validation Failed

```
ValidationError: Type mismatch for 'count': expected 'int', got 'str'
```

**Solution:** Ensure your procedure return type matches:

```python
# Wrong: LLM returns string by default
@get_count() -> int:
    Give me a [number].  # May return "5" as string

# Correct: Kedi will coerce to int if valid
@get_count() -> int:
    Give me a [number] as digits only.
```

## Syntax Errors

### Unclosed Bracket/Angle

```
SyntaxError: Unclosed bracket in template
```

**Solution:** Use escape sequences for literal brackets:

```python
# Wrong
Show list[0] value

# Correct
Show list\[0\] value
```

### Missing Line Continuation

```
UnexpectedMultipleCallsError: Multiple LLM calls detected
```

**Solution:** Use `\` for multi-line prompts:

```python
# Wrong: Two LLM calls
@example() -> str:
    Line one
    Line two with [answer]
    = <answer>

# Correct: One LLM call
@example() -> str:
    Line one \
    Line two with [answer]
    = <answer>
```

## Common Mistakes

### Output Field as Instruction

!!! danger "Wrong Pattern"
    ```python
    # WRONG: Instruction-style output
    @get_capital(country: str) -> str:
        What is the capital of <country>? Write your answer in [capital]
        = <capital>
    ```

!!! success "Correct Pattern"
    ```python
    # CORRECT: Natural embedding
    @get_capital(country: str) -> str:
        What is the [capital] of <country>?
    ```

### Forgetting Return Statement

```python
# Wrong: No return
@greet(name: str) -> str:
    Hello, <name>!

# Correct: With return
@greet(name: str) -> str:
    Hello [greeting] to <name>!
    = <greeting>
```

## Debug Tips

### Verbose Mode

Run with debug output:

```bash
kedi script.kedi --verbose
```

### Print Intermediate Values

````python
@debug_example(x: str) -> str:
    Step 1: [step1]

```python
print("Step 1 result:", <step1>)
\```

    Step 2 using <step1>: [step2]
    = <step2>
````

## Getting Help

- **GitHub Issues:** [Report bugs](https://github.com/your-repo/kedi/issues)
- **Documentation:** Check the [concepts](../concepts/procedures.md) section
- **Examples:** See the [examples](../examples/trip-planner.md) for working code
