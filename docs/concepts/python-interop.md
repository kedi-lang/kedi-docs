# Python Interop

Kedi is designed to work seamlessly with Python. You can execute Python code directly within your Kedi files.

## Inline Expressions

Use backticks `` `...` `` to evaluate a Python expression inline.

```python
[current_year: int] = `2025`
[next_year: int] = `current_year + 1`
```

You can also use them in template strings:

```python
The result is <`10 * 5`>.
```

## Multiline Blocks

For more complex logic, use triple backticks `...`.

````python
[fib_sequence: list[int]] = ```
a, b = 0, 1
result = []
for _ in range(10):
    result.append(a)
    a, b = b, a + b
return result
```
````

## Preamble (Imports)

You can place Python imports and helper functions at the top of your file (or anywhere, really, but top is best practice).

````python
```
import math
import random

def calculate_area(radius):
    return math.pi * radius * radius
```

[area] = `calculate_area(5)`
= Area is <area>
````

## Calling Kedi from Python

You can also call compiled Kedi procedures from within the Python blocks.

````python
@get_name() -> str:
    = Kedi

[message] = ```
name = get_name()
return f"Hello from Python, {name}!"
```
= <message>
````
