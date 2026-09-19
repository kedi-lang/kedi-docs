# Terminal-Bench 2.1 Results

This page reports two complete, single-trial Terminal-Bench 2.1 engineering
runs. Every one of the 89 tasks was attempted once in each run. The runs use
the same frozen Kedi harness, model, prompt, task set, resource split, timeout,
and sandbox provider; the adapter is the subject difference.

These are not official leaderboard submissions. A single trial per task is not
a stable pass-rate estimate, and both runs include an unreleased,
infrastructure-only QEMU repair described under [Limitations](#limitations).

## Aggregate Results

| Metric | Pydantic AI adapter | LangChain adapter |
| --- | ---: | ---: |
| Official Harbor reward | 68/89 (76.40%) | 68/89 (76.40%) |
| Total model cost | $4.93781512 | $5.05064428 |
| Cost per attempted task | $0.05548107 | $0.05674881 |
| Cost per solved task | $0.07261493 | $0.07427418 |
| Input tokens | 119,974,598 | 106,890,221 |
| Cache-read input tokens | 113,355,776 | 100,099,584 |
| Cache-read ratio | 94.48% | 93.65% |
| Uncached input tokens | 6,618,822 | 6,790,637 |
| Output tokens | 1,122,446 | 1,408,771 |
| Model requests | 3,121 | 3,061 |
| Tool calls | 3,800 | 3,867 |
| Observed wall span | 7.88 h | 9.53 h |
| Sum of task durations | 14.12 h | 17.22 h |

Both adapters solved 62 of the same tasks. Each adapter additionally solved six
tasks that the other run missed. Equal aggregate reward therefore does not mean
identical task outcomes. These one-trial differences must not be interpreted as
causal adapter-quality claims.

The Wilson 95% interval for either 68/89 single-trial proportion is
66.61%-84.02%. It describes uncertainty around these observations; it is not a
five-trial Terminal-Bench leaderboard estimate.

## Per-Task Distributions

P50 is the median. Percentiles use linear interpolation over the 89 per-task
observations.

### Pydantic AI

| Metric | P50 | Mean | P90 | P95 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cost (USD) | $0.02364 | $0.05548 | $0.14343 | $0.19746 | $0.58565 |
| Duration (s) | 335.7 | 571.0 | 1,269.7 | 1,786.6 | 4,018.4 |
| Input tokens | 267,611 | 1,348,029 | 3,564,265 | 5,068,932 | 22,352,464 |
| Output tokens | 8,429 | 12,611 | 35,364 | 43,794 | 60,956 |
| Model requests | 21 | 35.1 | 81.0 | 100.0 | 217 |
| Tool calls | 30 | 42.7 | 86.6 | 131.8 | 245 |

### LangChain

| Metric | P50 | Mean | P90 | P95 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cost (USD) | $0.03189 | $0.05675 | $0.13264 | $0.15467 | $0.43384 |
| Duration (s) | 362.4 | 696.7 | 1,177.1 | 1,523.7 | 7,484.7 |
| Input tokens | 328,160 | 1,201,014 | 2,856,952 | 4,784,921 | 16,930,847 |
| Output tokens | 9,355 | 15,829 | 31,895 | 37,952 | 164,835 |
| Model requests | 22 | 34.4 | 69.2 | 91.0 | 161 |
| Tool calls | 33 | 43.4 | 94.0 | 103.6 | 172 |

Wall span is elapsed time from the first trial start to the final trial finish.
The sum of task durations counts concurrently running tasks separately. The
LangChain wall-time difference is an observed end-to-end result and is not, by
itself, evidence that Kedi adds adapter-specific latency; model trajectories,
task outcomes, framework execution, and remote infrastructure are not isolated
by these single runs.

## Batch Breakdown

| Adapter | Batch | Tasks | Solved | Score | Cost | Cache-read ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Pydantic AI | Standard C2 | 81 | 62 | 76.54% | $4.43934284 | 94.66% |
| Pydantic AI | High-memory C1 | 8 | 6 | 75.00% | $0.49847228 | 92.77% |
| LangChain | Standard C2 | 81 | 64 | 79.01% | $4.55293688 | 93.63% |
| LangChain | High-memory C1 | 8 | 4 | 50.00% | $0.49770740 | 93.82% |

## Frozen Configuration

The shared configuration was:

- model `codex/gpt-5.6-luna`, high reasoning effort;
- Kedi 0.4.0 and `codex-auth-helper` 1.8.0;
- WebSocket-first Codex Responses transport with HTTP recovery fallback;
- history and Tool Artifacts enabled, CodeMode and compaction disabled;
- Logfire disabled;
- one attempt per task, no automatic trial retries, and a six-hour agent
  timeout;
- 81 standard tasks at concurrency 2, followed by 8 high-memory tasks at
  concurrency 1;
- Daytona task sandboxes and Harbor 0.22.0;
- Terminal-Bench 2.1 plus `evalstate/terminal-bench-2-1` commit
  `75f5a2e66b2dfd9d7eba3065a9d919c1f9da5c5e` for the two QEMU tasks.

The Pydantic AI runtime used `pydantic-ai-slim==2.36.0`. The LangChain runtime
used `langchain==1.3.18`, `langchain-core==1.6.1`,
`langchain-openai==1.6.0`, `langchain-openrouter==0.2.8`,
`langchain-mcp-adapters==0.3.2`, `langgraph==1.2.11`, and
`langsmith==0.8.18`. Both task runtimes used OpenAI 3.8.0 and WebSockets
15.0.1.

The exact Pydantic manifest, sanitized Harbor evidence, and one immutable
89-run Autobench record are published in the
[Kedi benchmarks repository](https://github.com/kedi-lang/benchmarks/tree/main/terminal-bench-2-1/2026-09-12-codex-luna-high-daytona-full-89x1).
The frozen LangChain experiment contract has digest
`7f361e9c5687dc2f461b24ca33982ce66ce5718098b64ef9c0b08f8dc7c9a95a`.

## Cost Method

Costs use `genai-prices==0.1.4` with the OpenAI `gpt-5.6-luna` price record and
are calculated per completed model request from uncached input, cache-read
input, and output tokens. The Pydantic total equals the runtime-reported total.
The LangChain Harbor records contain complete request usage but no provider
cost field, so the same request-level price calculation supplies its reported
cost. Cloud sandbox cost is excluded.

## Limitations

- Each task has one trial. Model behavior is stochastic, so neither accuracy
  nor adapter deltas should be generalized without repeated matched trials.
- The QEMU tasks use an unreleased infrastructure repair. Their rewards remain
  in the engineering aggregate, which makes these runs ineligible for direct
  official leaderboard submission.
- The historical Kedi wheels were built from fully hashed, dirty source trees.
  Source and wheel hashes are retained, but credentials and private wheels are
  not published.
- Terminal-Bench measures the complete model, harness, tools, adapter, and
  sandbox system. It does not isolate the value of Kedi's language constructs.

