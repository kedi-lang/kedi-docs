# Escaping & Line Continuation

Kedi uses special characters for its syntax. When you need to use these characters literally, you must escape them with a backslash `\`.

## Escapable Characters

| Escape   | Result  | Use Case                         |
| -------- | ------- | -------------------------------- |
| `\<`     | `<`     | Literal less-than in text        |
| `\>`     | `>`     | Literal greater-than in text     |
| `\[`     | `[`     | Literal bracket in text          |
| `\]`     | `]`     | Literal bracket in text          |
| `\=`     | `=`     | Literal equals sign              |
| `\@`     | `@`     | Literal at sign                  |
| `\,`     | `,`     | Comma inside procedure arguments |
| `\\`     | `\`     | Literal backslash                |
| `\#`     | `#`     | Literal hash (not a comment)     |
| `\~`     | `~`     | Literal tilde                    |
| `` \` `` | `` ` `` | Literal backtick                 |
| `\(`     | `(`     | Literal parenthesis              |
| `\)`     | `)`     | Literal parenthesis              |
| `\t`     | Tab     | Tab character                    |
| `\n`     | Newline | Newline character                |
| `\s`     | Space   | Preserved space                  |

## Line Continuation

!!! warning "Critical Rule"
    In Kedi, **every line is a separate template string**, which means each line triggers a separate LLM call. To write multi-line prompts that execute as a **single** LLM call, use the backslash `\` at the end of each line.

### Example: Multi-line Prompt

```python
@analyze(topic: str) -> str:
    You are an expert analyst. \
    Analyze <topic> from multiple perspectives: economic, social, and political. \
    Provide your [analysis] in a structured format.
    = <analysis>
```

This is equivalent to a single-line prompt:

```
You are an expert analyst. Analyze {topic} from multiple perspectives: economic, social, and political. Provide your {analysis} in a structured format.
```

### Common Mistake

```python
# WRONG: Two separate LLM calls
@bad_example(topic: str) -> str:
    You are an expert.
    What is your [opinion] on <topic>?
    = <opinion>

# CORRECT: Single LLM call
@good_example(topic: str) -> str:
    You are an expert. \
    What is your [opinion] on <topic>?
    = <opinion>
```

## Escaping Commas in Arguments

When passing arguments that contain commas, escape them with `\,`:

```python
@format(text: str) -> str:
    = Formatted: <text>

# Pass "alpha, beta, gamma" as a single argument
= <format(alpha\, beta\, gamma)>
```

## Whitespace Preservation

Regular whitespace at the start and end of lines is trimmed. To preserve whitespace, use escape sequences:

```python
# Leading tab and trailing newline are preserved
= \tIndented text\n
```
