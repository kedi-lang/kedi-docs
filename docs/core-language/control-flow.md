# Control Flow

Kedi supports deterministic and model-classified branches, conditional loops,
and sequential iterable loops. A trailing `:` after an inline Python condition
selects deterministic execution. Without that trailing colon, the header is a
Kedi template claim classified by the active agent adapter.

## Conditional Branches

```kedi
[score: int] = `72`

> if: `score >= 60`:
  [result] = passed
> else:
  [result] = failed

= <result>
```

The condition is evaluated exactly once. Its result must have exact Python
type `bool`; values that are merely truthy or falsey are rejected. The closing
`:` after the embedded Python expression is required. Kedi runs only the
selected body, so Python statements, procedure definitions, and model calls in
the other body have no effect.

`> else:` is optional. Kedi has no `elif` form; nest another `> if:` when a
second condition is needed:

```kedi
> if: `score >= 90`:
  [grade] = A
> else:
  > if: `score >= 75`:
    [grade] = B
  > else:
    [grade] = C
```

Writes from the selected body remain visible afterward. Agent-profile
directives inside that body are lexical and do not affect statements after the
branch. A return inside a selected body participates in Kedi's existing
last-return behavior; it is not a Python-style early return.

## Template Conditions

```kedi
[city] = Ankara
[minimum_population: int] = `5_000_000`

> if: <city> has more than `minimum_population` residents
  [result] = major city
> else:
  [result] = smaller city

= <result>
```

A template condition has no trailing `:`. Plain text, `<name>` substitutions,
procedure calls, and inline Python values use normal Kedi rendering semantics.
`[output]` fields are rejected because a condition does not create a binding.

Kedi asks the active adapter for an annotated `bool` with this request:

```text
Return true only if the following claim can be established as true from the available context; otherwise return false.
Claim: {rendered claim}
```

The call uses the active profile's model, system instructions, settings, tools,
MCP servers, history, caching, limits, retries, cancellation, streaming, and
telemetry. A claim that cannot be established must be classified as `false`.
No internal classification result is added to the Kedi environment.

The trailing colon distinguishes a deterministic condition from a claim even
when both contain one inline Python segment:

```kedi
> if: `is_ready`:
  [kind] = deterministic

> if: `is_ready`
  [kind] = model-classified
```

## Conditional Loops

```kedi
[remaining: int] = `3`

> loop: `remaining > 0`:
  `remaining -= 1`

= `remaining`
```

The exact-`bool` condition is evaluated before every iteration. A false first
result executes no body, while writes from a completed body are visible to the
next condition.

Template conditional loops use the same claim syntax and re-render the claim
before every iteration:

```kedi
> loop: <work> remains unfinished
  >> Continue the unfinished work.
```

Conditional loops allow 10,000 completed iterations by default. If their
condition is still true, Kedi raises `LoopIterationLimitError` before starting
the next body. Nested loops have independent counters. Python callers can set a
positive `loop_iteration_limit` through `compile_program()`, `configure()`,
`context()`, or `interactive()`.

## Sequential Loops

```kedi
[items: list[int]] = `[1, 2, 3, 4, 5]`
[total: int] = `0`

> loop [n]: `items`:
  `total += n`

= `total`
```

The expression is evaluated once and must return an `Iterable`. Kedi traverses
it sequentially in its native order without materializing it or adding implicit
parallelism. Lists, tuples, dictionaries, strings, generators, ranges, and
custom iterables therefore retain their normal iteration behavior.

The binder receives each yielded value without coercion and is visible to every
statement and nested block in the current iteration. Its lifetime is restricted
to the loop:

```kedi
[n: int] = `99`
[values: list[int]] = `[]`

> loop [n]: `range(3)`:
  `values.append(n)`

= `(values, n)`
```

This returns `([0, 1, 2], 99)`. Kedi restores an existing binding or removes a
new one in `finally`, including when the loop is empty, raises, or is
cancelled. Nested loops may shadow the same binder safely. Writes to other
values remain visible after each iteration and after the loop.
