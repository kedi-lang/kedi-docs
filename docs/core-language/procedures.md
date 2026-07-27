# Procedures

Procedures package Kedi statements into typed, reusable callables. They are also
the unit exposed to tools, tests, evals, optimization, generated code, and the
Python API.

## Define and Call a Procedure

Declare a procedure with `@name(parameters):` and indent its body:

```kedi
@greet(name: str) -> str:
  = Hello, <name>.

= <greet(Ada)>
```

The name must be a valid Python identifier. The body can contain assignments,
templates, Python blocks, directives, nested types, nested procedures, and a
return. Call it with `<greet(Ada)>` in rendered Kedi text or `greet("Ada")` in a
Python expression.

## Procedure Bodies and Returns

Statements execute in source order. A return statement starts with `=`:

```kedi
@summarize(text: str) -> str:
  >> Summarize <text> as [summary: str].
  = <summary>
```

Execution stops at the first reached return. If an untyped procedure reaches the
end without a value, it returns an empty string. For non-string behavior, add an
explicit return annotation and return a native value.

Keep deterministic transformation in Python and model judgement in `>>`
templates. A procedure may combine both, but its name and return type should
still describe one coherent operation.

## Local Variables

Parameters and assignments belong to the procedure invocation:

```kedi
[prefix] = global

@format(value: str) -> str:
  [prefix] = local
  [result] = <prefix>: <value>
  = <result>

= <format(item)> / <prefix>
```

The procedure returns `"local: item"` while the top-level `prefix` remains
`"global"`. New local names do not leak to callers.

Parameters are read-only bindings for lexical assignment purposes. Reuse a new
local name when deriving from a parameter rather than treating the parameter as
shared mutable state.

## Calling Other Procedures

Procedures can form pipelines:

```kedi
@normalize(value: str) -> str:
  = `value.strip().lower()`

@classify(value: str) -> str:
  >> Classify <value> as [category: str].
  = <category>

@process(value: str) -> str:
  [normalized: str] = <normalize(<value>)>
  = <classify(<normalized>)>
```

A sole call on an assignment right-hand side preserves the called procedure's
native return type. Text around the call renders the assignment as `str`.

## Nested Procedures

A procedure can declare helpers visible only during that invocation:

```kedi
@invoice_total(lines: list[float]) -> float:
  @subtotal(values: list[float]) -> float:
    = `sum(values)`

  = `round(subtotal(lines), 2)`
```

The nested `subtotal` is not visible after `invoice_total` returns. A nested
definition shadows an outer procedure with the same name only inside its
lexical scope.

Use nested procedures for helpers that are meaningful only to one operation or
that need to capture invocation state. Use a top-level procedure when several
features should call it or when it should be exported, tested, optimized, or
exposed as a tool independently.

## Lexical Closures

Nested procedures capture the surrounding invocation and observe the latest
outer value:

```kedi
@make_report(title: str) -> str:
  [state] = draft
  @render() -> str:
    = <title>: <state>
  [state] = approved
  = <render()>
```

The result is `"title [approved]"`, not `"title [draft]"`. Closure lookup walks
the current local scope, outer procedure scopes, imports, and top-level globals.
A nested parameter shadows a captured name.

Assignments made through nested lexical scopes can update a captured Kedi
binding. This is different from Python block rules, where rebinding from a
nested Python function requires `global`.

## Recursion

Compiled procedures are ordinary callable values and can be called from Python,
including recursively:

```kedi
@factorial(n: int) -> int:
  = `1 if n <= 1 else n * factorial(n - 1)`

= `factorial(5)`
```

Use recursion only when it improves the domain model. Iteration in a Python
block is usually clearer for large collections and avoids Python's recursion
limit. Model-calling recursion can also multiply cost and latency; bound it
explicitly.

## Procedure Documentation

Place a `###` block first in the body to define the procedure docstring:

```kedi
@lookup_order(order_id: str) -> str:
  ###
  Return the canonical status for one order.

  Args:
    order_id: External order identifier.
  ###
  = pending
```

Kedi surfaces this text in editor hover, generated Python stubs, procedure JSON
schemas, and tool descriptions. A block comment after another statement remains
a comment and does not become the procedure docstring.

Document externally visible procedures and every procedure exposed with
`> tool:`. Include semantic constraints that types cannot express; do not
duplicate the signature verbatim.

## Failure Behavior

Calling a procedure fails when arguments are missing or excessive, a native
value violates a parameter annotation, the body raises, or the return violates
its annotation. Kedi retains source spans across nested calls so the reported
failure points back to the relevant `.kedi` statement.
