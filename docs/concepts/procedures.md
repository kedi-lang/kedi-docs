# Procedures

Procedures are the building blocks of Kedi applications. They encapsulate logic, LLM prompts, and Python code.

## Definition

A procedure is defined using the `@` symbol, followed by the name, arguments, and return type.

```python
@procedure_name(arg1: type, arg2: type) -> return_type:
    # Body of the procedure
    = return_value
```

!!! info "Default Type"
    If you omit the type for an argument or return value, it defaults to `str`.

## The Main Procedure

Every Kedi program has an implicit "main" procedure. The top-level code is part of this main procedure.

The return value of the main procedure is defined by the `=` token at the beginning of a line.

```python
# This is the main procedure
= Done
```

## Procedure Body

A procedure body can contain:

1.  **Template Strings**: Natural language prompts for LLMs.
2.  **Python Expressions**: Logic and data manipulation.
3.  **Return Statement**: The final result.

### Example: LLM Interaction

```python
@get_capital(country: str) -> str:
    What is the [capital] of <country>?
    = <capital>
```

In this example:

1.  The text between the definition and the return statement is the **prompt**.
2.  `<country>` injects the argument.
3.  `[capital]` captures the LLM's output into a variable.
4.  `= <capital>` returns the captured value.

!!! warning "One Line = One Agent Run"
    In Kedi, **every line in a procedure body is treated as a separate template string**, triggering a separate LLM run.

    If you want to write a long prompt across multiple lines but execute it as a **single** LLM call, you must use the backslash `\` character for line continuation.

    **Incorrect (Two separate runs):**
    ```python
    You are a helpful geography assistant.
    What is the [capital] of <country>?
    ```
    *(This runs the agent twice. First it processes "You are...", then it processes "What is..." separately.)*

    **Correct (One single run):**
    ```python
    You are a helpful geography assistant. \
    What is the [capital] of <country>?
    ```
    *(The backslash merges these lines into a single prompt, running the agent only once.)*

    Always ensure your output field `[...]` is embedded naturally within the sentence.

## Nested Procedures

Procedures can be nested. Inner procedures have access to the scope of outer procedures.

```python
@outer():
    @inner():
        = I am inner
    = <inner()>
```
