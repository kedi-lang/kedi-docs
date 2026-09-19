# Control Flow

Kedi supports deterministic and model-classified branches, conditional loops,
and sequential iterable loops. A trailing `:` after an inline Python condition
selects deterministic execution. Without that trailing colon, the header is a
Kedi template claim classified by the active agent adapter.

## Conditional Branches

```kedi
[score: int] = `72`
[result] = pending

> if: `score >= 60`:
  [result] := passed
> else:
  [result] := failed

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
[grade] = unknown

> if: `score >= 90`:
  [grade] := A
> else:
  > if: `score >= 75`:
    [grade] := B
  > else:
    [grade] := C
```

Each selected body owns a child value scope. A Kedi `=` initialization remains
inside that branch, while `:=` or embedded Python may update a binding already
owned by a containing scope. New Python-only names never become Kedi bindings.
Agent-profile directives inside the body are also lexical. A return inside a
selected body participates in Kedi's existing last-return behavior; it is not
a Python-style early return.

## Template Conditions

```kedi
[city] = Ankara
[minimum_population: int] = `5_000_000`
[result] = unknown

> if: <city> has more than `minimum_population` residents
  [result] := major city
> else:
  [result] := smaller city

= <result>
```

A template condition has no trailing `:`. Plain text, `<name>` substitutions,
procedure calls, and inline Python values use normal Kedi rendering semantics.
`[output]` fields are rejected because a condition does not create a binding.

Kedi evaluates the rendered claim using the current agent profile and its
available context. A claim that cannot be established is treated as `false`.
The evaluation does not create a Kedi binding.

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
result executes no body. Every body execution receives a fresh child scope.
State needed by the next condition must update an existing outer binding with
`:=` or owner-aware Python write-back; new body-local declarations disappear
after that iteration.

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
custom iterables therefore retain their normal iteration behavior. If the
iterator exposes `close()`, Kedi calls it after normal traversal and on an
early exit caused by a loop-body failure.

The binder receives each yielded value without coercion and is visible to every
statement and nested block in the current iteration. Every iteration owns a
fresh child scope, so its binder and local declarations cannot leak into or
overwrite another iteration. The binder's lifetime is restricted to the loop:

```kedi
[n: int] = `99`
[values: list[int]] = `[]`

> loop [n]: `range(3)`:
  `values.append(n)`

= `(values, n)`
```

This returns `([0, 1, 2], 99)`. Each iteration binder belongs to a fresh child
scope, so the outer `n` is never overwritten and the iteration binding is
discarded when that scope ends. Nested loops may shadow the same binder safely.
Outer values change only through `:=`, owner-aware Python write-back, or
mutation of an outer object.

## Map Continuations

One sibling `> map:` clause may immediately follow an iterable loop:

```kedi
[selected: list[str]] = `[]`

> loop [candidate]: `candidates`:
  >> Decide whether <candidate> qualifies as [qualified: bool] and extract [email].
> map:
  > if: `qualified`:
    `selected.append(email)`

= `selected`
```

This is a deferred continuation stage, not Python's collection-producing
`map()`. Kedi first traverses the iterable and starts every loop-body job. It
then schedules one continuation for each retained iteration scope. Each map
execution sees only its own binder, declarations, and model outputs plus the
containing scopes.

The configured execution engine controls concurrency. Sequential execution
preserves source order; a parallel engine may finish independent records out of
order. Kedi joins and drains the entire stage before continuing after the loop,
then surfaces the first failure.

Parallel map continuations may overlap. Source-order side effects and atomic
read-modify-write operations are not implied: shared aggregates must use
operations or synchronization appropriate for the active execution engine.

The first version accepts one map stage on an immediately preceding
binder-based loop. It has no binder and creates no implicit output collection.
Orphan maps, maps attached to conditional loops, and chained maps are parse
errors.
