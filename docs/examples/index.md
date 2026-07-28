# Examples

These examples combine Kedi features into reviewable programs. Read the focused
language pages first when you need a complete rule rather than a guided
scenario.

## Choose an Example

| Example | Main concepts | Requires model calls |
| --- | --- | --- |
| [Structured Extraction](structured-extraction.md) | custom types, typed captures, native returns | yes |
| [Tools and Approvals](tools-and-approvals.md) | Kedi and Python tools, risk, argument editing | yes |
| [Agent Delegation](agent-delegation.md) | profiles, structured children, background lifecycle | yes |
| [Evaluation and Optimization](evaluation-and-optimization.md) | datasets, metrics, `> optimize:`, GEPA | yes |
| [Modules and Packaging](modules-and-packaging.md) | exports, selective imports, `package.kedi` | no |
| [Complete Program](complete-program.md) | a compact end-to-end application | yes |

## Runnable Conventions

Unless a page shows a directory tree, save its complete listing as
`program.kedi` and run:

```bash
kedi program.kedi
```

The examples use `groq:qwen/qwen3-32b` to make backend selection explicit.
Replace it with a model configured for your environment. Provider credentials
are read by the selected adapter; never place API keys in a `.kedi` source file.

## Syntax Used in Examples

- `<value>` substitutes an existing value into prompt or return text.
- `<`python_expression`>` evaluates Python and renders its result as text.
- `[field: Type]` in a `>>` block asks the model for a typed output.
- `[name: Type] = expression` performs a deterministic assignment.
- `= `python_expression`` returns the native Python value.
- `[text] << prompt` captures the raw model text; bare `<<` is not an operator.

These distinctions matter. Use a typed output when a model must infer a value,
Python when the answer is deterministic, and a native Python return when the
caller should receive an object rather than its string representation.

## Verification

The documentation build validates Markdown structure and links, but it does not
currently parse every Kedi fence. Some listings are fragments, while package
manifests and module examples require the source path shown by their directory
tree. Parser validity also does not prove that a provider supports every schema
or capability. Parse complete listings in their documented file context, then
run model-facing examples against the same adapter and model intended for
production.
