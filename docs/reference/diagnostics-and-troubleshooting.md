# Diagnostics and Troubleshooting

Kedi distinguishes parse, compile, capability, execution, validation, and
external-backend failures. Preserve the rendered source location and original
exception when reporting a problem.

## Language and Type Errors

| Symptom | Likely contract | Fix |
| --- | --- | --- |
| Template text must start with `>>` | Bare prompt outside optimize/auto | Add one `>>` at block start |
| Inline Python expression cannot be empty | Backtick delimiters were split/malformed | Keep expression on one line or use a fence |
| Unexpected indentation/dedent | Body indentation is inconsistent | Use one indentation width and align fences |
| Unknown directive | Misspelled or misplaced `>` directive | Use the [Directive Index](directives.md) |
| Unknown type | Type not defined/imported before use | Move declaration/import earlier |
| Output validation failure | Provider value does not satisfy resolved type | Simplify schema/prompt or correct provider |
| Promise leak | Internal/embedding code concretely used unresolved promise | Route dependency or call `force()` at consumption |

A blank line can terminate an adjacent multiline template even though it does
not close the lexical procedure. Start a new `>>` after the blank.

## Imports and Packages

| Symptom | Check |
| --- | --- |
| Imported name missing | Module has explicit export and selective name matches |
| Module not found | Relative path, bundled module, then installed registry |
| Manifest rejected | Exact `package.kedi` name and metadata-only contents |
| Python incompatible | Closed `python@...` range includes installer |
| Dependency invalid | Every entry parses as PEP 508 |
| Source-tree escape | No absolute path, `..`, symlink escape, or pattern |
| Registry package unavailable | Configure mock root or use explicit GitHub source |

Package install does not install Python dependencies. A valid receipt also does
not make imported Python safe.

## Backend and Capability Errors

| Symptom | Check |
| --- | --- |
| Framework/harness mismatch | Use `> adapter:` for frameworks, `> agent:` for harnesses |
| ACP command missing | Set multiline ACP command, CLI `--acp-command`, or environment variable |
| Structured output unsupported | Choose a structured adapter or use raw `[text] <<` |
| Tools/MCP/subagents unsupported | Consult [Capability Matrix](capability-matrix.md) |
| Model setting ignored/rejected | Use a key supported by the active adapter |
| Provider authentication fails | Provider-specific API key and endpoint |
| Codex schema rejected | Replace unsupported URL/regex formats with described strings |

Do not treat successful parsing as adapter validation. Test the exact profile
with its production model and optional dependencies installed.

## Tools and Approvals

- A missing policy denies mutating and sensitive calls; read-only remains
  allowed.
- A dynamic handler must return `ApprovalDecision`, not a string or mapping.
- An edit must provide the complete argument mapping and is revalidated.
- `.env` reads need explicit secret-file intent plus sensitive approval.
- Approval only wraps registered tools, not arbitrary embedded Python.
- Tool retries retry exceptions and may repeat side effects; make retryable
  mutating tools idempotent.

## MCP

For stdio, verify command, arguments, working directory, inherited environment,
server dependencies, and that stdout is reserved for protocol traffic. For
remote transports, verify normalized transport, URL, headers, TLS/network
reachability, and server protocol version.

`streamable-http` is DSL input syntax normalized to `http`. Direct
`McpServerSpec` construction should call `.normalized()`.

## Subagents

| Failure | Meaning |
| --- | --- |
| Unknown child | Child is not a direct declared profile |
| Cycle detected | Profile delegation graph is recursive |
| Budget exhausted | `max_agents` or hard descendant cap reached |
| Background unsupported | Adapter only supports foreground children |
| Unobserved run | Parent returned without successful `wait_subagent` |
| Cannot continue | Run not latest/completed/owned or turn limit reached |
| Interrupted after restart | In-flight work cannot be resumed safely |
| Child safety violation | Child widened cwd, sandbox, or approval ceiling |

## Tests, Evals, and Optimization

- Test exceptions fail that case while later cases continue.
- Eval data loader errors abort; metric-row errors score `0.0` with feedback.
- `--eval` reports matching test data or training fallback, not both.
- Every optimized procedure needs a same-named eval, training data, and metric.
- Corrupt `.optimized.json` fails loudly; remove/fix it rather than expecting
  fallback.
- `--optimizer-fresh` resets GEPA artifacts; `--no-cache` controls auto-codegen.

## Editor and Site

If Kedi is absent from language selection, verify the VS Code/Zed extension,
file association, language-server executable, and editor logs. If highlighting
works but diagnostics do not, check LSP command resolution separately.

For documentation failures, run the strict Zensical build. Broken nav entries,
relative links, malformed nested fences, and duplicate anchors should be fixed
at source rather than suppressed.
