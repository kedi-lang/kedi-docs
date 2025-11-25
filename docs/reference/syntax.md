# Syntax Reference

A complete reference to all Kedi syntax elements.

## Grammar Overview

```
program     ::= statement*
statement   ::= procedure | type_def | assignment | template | python_block | comment
```

## Procedures

```
procedure   ::= "@" name "(" params ")" "->" return_type ":" body
params      ::= (param ("," param)*)?
param       ::= name (":" type)?
return_type ::= type
body        ::= (indent statement)+
```

**Examples:**

```python
# Basic procedure
@greet(name: str) -> str:
    Hello, <name>!
    = <name>

# Typed parameters
@calculate(x: int, y: int) -> int:
    Sum of <x> and <y> is [sum].
    = <sum>

# Default parameters (not yet supported)
@greet(name: str, greeting: str) -> str:
    <greeting>, <name>!
    = <greeting>
```

## Type Definitions

```
type_def    ::= "~" name "(" fields ")"
fields      ::= field ("," field)*
field       ::= name (":" type)?
```

**Examples:**

```python
# Simple type
~Person(name: str, age: int)

# Complex type
~Company(name: str, employees: list, revenue: float)
```

## Templates

```
template    ::= text (substitution | output)*
substitution ::= "<" name ">"
output      ::= "[" name "]"
```

**Examples:**

```python
# Substitution: insert variable value
Hello, <name>!

# Output: capture LLM output
What is the [capital] of <country>?

# Combined
Tell me a [fact] about <topic>.
```

## Python Blocks

````
python_block ::= "```python" python_code "```"
````

**Examples:**

````python
@compute(data: list) -> float:
    Calculate the [value] from <data>.

```python
import statistics
result = statistics.mean(<data>)
\```

    The mean is [result].
    = <result>
````

## Assignments

```
assignment  ::= "=" value | "=" "<" procedure_call ">"
```

**Examples:**

```python
# Direct return
= <result>

# Procedure call return
= <greet(Alice)>
```

## Comments

```
comment     ::= "#" text (until end of line)
```

**Examples:**

```python
# This is a comment
@greet(name: str) -> str:  # Inline comment
    Hello!
```

## Escape Sequences

| Sequence | Meaning               |
| -------- | --------------------- |
| `\<`     | Literal `<`           |
| `\>`     | Literal `>`           |
| `\[`     | Literal `[`           |
| `\]`     | Literal `]`           |
| `\=`     | Literal `=`           |
| `\@`     | Literal `@`           |
| `\,`     | Literal `,` (in args) |
| `\\`     | Literal `\`           |
| `\#`     | Literal `#`           |
| `\~`     | Literal `~`           |
| `` \` `` | Literal `` ` ``       |
| `\(`     | Literal `(`           |
| `\)`     | Literal `)`           |
| `\t`     | Tab                   |
| `\n`     | Newline               |
| `\s`     | Space                 |

## Line Continuation

Use `\` at end of line to continue to next line as single template:

```python
@analyze(topic: str) -> str:
    You are an expert. \
    Analyze <topic>. \
    Provide [analysis].
    = <analysis>
```

## Type System

### Built-in Types

| Type    | Description       |
| ------- | ----------------- |
| `str`   | Text string       |
| `int`   | Integer           |
| `float` | Floating-point    |
| `bool`  | Boolean           |
| `list`  | List/Array        |
| `dict`  | Dictionary        |
| `code`  | Executable Python |

### Custom Types

```python
~MyType(field1: type, field2: type)
```

Custom types are converted to Pydantic models automatically.

## File Structure

A typical Kedi file:

```python
# Type definitions (top)
~Person(name: str, age: int)

# Procedures
@create_person(name: str, age: int) -> Person:
    Create a [person] with name <name> and age <age>.

@greet(person: Person) -> str:
    Hello [greeting] to <person.name>!
    = <greeting>

# Main execution (bottom)
person = <create_person(Alice, 30)>
= <greet(<person>)>
```
