# Provider Prefix Caching

Provider prompt caching reuses computation for a matching request prefix. It
does not skip a model invocation and is independent of Kedi's response cache.

## What Kedi Preserves

Within a compatible conversation lane, request assembly retains the order of
successful native messages and their tool-call/result relationships. Artifact
tools are present from the first artifact-enabled request. Releasing a payload
does not remove its old reference from history.

Changing a tool schema, model, settings, instructions, or enabled capabilities
can change the request prefix or continuation lane. Compaction establishes a
new cache epoch. These are not equivalent to appending a user message to an
otherwise identical request.

## What Kedi Cannot Guarantee

An unchanged prefix is necessary for reuse, not a promise of a cache hit.
Provider routing, minimum eligible prefix lengths, retention, and provider
implementation determine whether computation is reused. A cache key is a
routing hint, not a cache reservation. HTTP and WebSocket are transports;
neither guarantees a particular cache-read percentage.

## Measure Requests, Not Just Runs

Compare the same model, request sequence, tools, settings, and input sizes.
Record per-request input tokens and cached input tokens. The aggregate read
ratio is total cached input divided by total input, not an unweighted average
of request percentages. Include the cold first request explicitly, or label a
warm-only measurement as such.

A high ratio alone does not establish efficiency: repeatedly sending an
unnecessary large context can increase both cached tokens and total work.
Report uncached input, cached input, output, request count, task success, and
latency separately. Missing cache counters are unknown, not measured zero.

See [History](history.md), [Compaction](compaction.md), and [Application
Caches](caching.md) for the separate ownership and lifecycle rules.
