# Concurrency

Kedi is sequential by default. Parallel execution is opt-in and accelerates
independent model templates without changing source syntax or expected results.

## Sequential Default

Every `>>` or `<<` call blocks until the adapter returns:

```kedi
>> Produce [first: str].
>> Produce [second: str].
```

This is easiest to debug and is appropriate when latency is unimportant, the
adapter is not thread-safe, or calls have external ordering effects.

## Enable Parallel Execution

Environment:

```console
$ KEDI_PARALLEL=1 kedi program.kedi
```

Accepted truthy values are `1`, `true`, `yes`, and `on`; false values are `0`,
`false`, `no`, `off`, or unset. A positive integer sets the worker count.
Invalid values are rejected rather than guessed.

Python:

```python
import kedi

kedi.configure(parallel=True)

with kedi.parallel(max_workers=4):
    run_workflow()
```

Use the public form appropriate to the application. `max_workers` must be a
positive bound.

## Automatic Dependencies

There is no parallel operator. The runtime follows value dependencies:

```kedi
>> Extract [service: str] from <incident>.
>> Find [owner: str] for <service>.

>> Extract [region: str] from <incident>.
>> Find [runbook: str] for <region>.
```

The service and region calls can start together. Each downstream call begins as
soon as its own input resolves, so the two chains pipeline independently.

## Promises and Forcing

Template outputs are represented internally as opaque promises until a value is
needed. Normal Kedi code does not observe them. A bare Python read or
`globals()["name"]` forces the value.

Advanced non-forcing operations such as `globals().get("name")`,
`globals().items()`, `globals().values()`, and `dict(globals())` can expose the
raw promise for forwarding. Resolve it with `kedi.force(value)`.

Using an unresolved promise as an ordinary value raises `KediPromiseLeak`
instead of silently stringifying, indexing, comparing, or serializing the wrong
object. Application logic should not catch and normalize this exception; it
indicates an interpreter/advanced-integration error.

## Snapshot Semantics

When a template is scheduled, Kedi snapshots its value environment by value. A
later assignment on the main thread cannot alter that call's inputs.

Sequential and parallel results must be identical. Parallel mode is not a
consistency option and must not be used to create races intentionally.

## Failure Draining

Every scheduled template runs, including one whose output is never consumed.
Before a scope returns or propagates another failure, Kedi drains its work. The
first model failure is raised; additional concurrent failures are logged.

This prevents silent background exceptions and resource leaks. It also means a
fire-and-forget `>>` still has cost and can fail.

## Adapter Thread Safety

Parallel execution may call an adapter's synchronous production path from
several worker threads. Built-in adapters are designed for this contract. A
custom adapter must be thread-safe or serialize its own critical section.

Agent/tool calls must also keep invocation scopes isolated. Do not store
request-specific mutable state on a shared adapter without synchronization.

## Shared Pools

Thread pools are process-global and cached by worker count. The first request
for one size creates that pool; later runs using the same size reuse it. Select
a small bound based on provider rate limits and workload, not CPU count alone.

## Adaptive Job Manager

`JobManagerEngine` is an advanced opt-in engine that adds AIMD concurrency,
transient-error retries with exponential backoff and jitter, and a circuit
breaker. It is not selected by the public `parallel()` helper.

Construct it explicitly through `compile_program(engine=...)` when operating a
rate-limited backend and when retry semantics are acceptable. Do not enable
automatic retries for non-idempotent external effects without a deduplication
strategy.
