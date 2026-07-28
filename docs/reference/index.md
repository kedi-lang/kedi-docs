# Reference

This section is the compact, searchable inventory of Kedi's public language,
runtime, Python, adapter, and tooling contracts. The conceptual sections linked
from each table provide examples and rationale.

## Language

- [Syntax Index](syntax.md) lists every statement form and delimiter.
- [Directive Index](directives.md) lists every top-level, procedure, profile,
  test, eval, optimization, and package directive.
- [Package Manifest](package-manifest.md) defines `package.kedi`.

## Runtime and Integration

- [CLI Reference](cli.md) covers invocation, options, program arguments, and
  exit behavior.
- [Environment Variables](environment-variables.md) records Kedi-owned and
  provider-owned configuration.
- [Python API](python-api.md) inventories decorators, contexts, promises,
  runtime helpers, approvals, MCP, and debugging.
- [Capability Matrix](capability-matrix.md) distinguishes framework and harness
  feature support.

## Failure and Coverage

- [Diagnostics and Troubleshooting](diagnostics-and-troubleshooting.md) maps
  symptoms to violated contracts.
- [Semantic Coverage Map](semantic-coverage.md) is the completeness checklist
  for the documentation set.

The reference describes public behavior. Internal modules not exported from
`kedi` may change without preserving compatibility.

## Terminology

- **Template call** is the Kedi-level `>>` operation. It may request structured
  output fields or discard a raw response when no fields are present.
- **Raw invoke** is `[name] << prompt`, which retains the model's complete text
  response as a string.
- **Adapter invocation** is the runtime call through Kedi's `AgentAdapter`
  protocol.
- **Provider request** is the outbound model or harness request made by an
  adapter. One Kedi operation may require multiple provider requests when tools
  or agent loops are involved.
