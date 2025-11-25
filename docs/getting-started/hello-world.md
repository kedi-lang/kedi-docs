# Your First Kedi Program

Let's write a simple program to understand the basic syntax of Kedi.

---

## The "Hello World"

Create a file named `hello.kedi`:

```python title="hello.kedi"
[name: str] = `input('Enter your name: ')`

= Hello, <name>! Welcome to the Kedi cookbook!
```

### Running the Program

=== "CLI"

    ```bash
    kedi hello.kedi
    ```

=== "Python Module"

    ```bash
    python -m kedi hello.kedi
    ```

### Line-by-Line Breakdown

```python
[name: str] = `input('Enter your name: ')`
```

| Part          | Meaning                               |
| ------------- | ------------------------------------- |
| `[name: str]` | Declare variable `name` of type `str` |
| `=`           | Assignment operator                   |
| `` `...` ``   | Python code block (executed inline)   |

```python
= Hello, <name>! Welcome to the Kedi cookbook!
```

| Part     | Meaning                        |
| -------- | ------------------------------ |
| `=`      | Return statement               |
| `<name>` | Substitute the value of `name` |

---

## Adding an LLM Call

Now let's make it interesting by adding an LLM-generated greeting:

```python title="hello_ai.kedi"
@greet(name: str) -> str:
    Create a warm and friendly [greeting] for <name>.
    = <greeting>

[user] = `input('Your name: ')`
= <greet(<user>)>
```

This time:

1. The `@greet` procedure sends a prompt to the LLM
2. The LLM generates a personalized greeting
3. The output is captured in `[greeting]` and returned

---

## Defining Procedures

Procedures are the building blocks of Kedi programs:

```python title="hello_proc.kedi"
@say_hello(name: str) -> str:
    = Hello, <name>.

[user] = Mert
= <say_hello(<user>)>
```

### Procedure Anatomy

```
@say_hello(name: str) -> str:
│    │      │     │     │    │
│    │      │     │     │    └─ Colon starts body
│    │      │     │     └────── Return type
│    │      │     └──────────── Parameter type
│    │      └────────────────── Parameter name
│    └───────────────────────── Procedure name
└────────────────────────────── @ prefix (required)
```

---

## Next Steps

Now that you understand the basics:

- [:material-function-variant: Learn about Procedures](../concepts/procedures.md) - Master procedure definitions
- [:material-code-tags: Variables & Types](../concepts/variables-and-types.md) - Explore the type system
- [:material-robot: LLM Integration](../concepts/llm-integration.md) - Deep dive into LLM calls
