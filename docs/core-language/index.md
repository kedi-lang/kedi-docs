# Core Language

## Program Anatomy

A Kedi program is an ordered sequence of declarations and executable
statements. The public language surface includes:

- imports, exports, and package metadata;
- custom types and procedures;
- template and raw model calls;
- assignments and returns;
- embedded Python;
- model, profile, tool, MCP, skill, and subagent directives;
- test, eval, optimization, and generated-procedure blocks.

Indentation defines scope. There is no brace-delimited alternative.

## Prompt and Native Execution

Kedi uses explicit syntax for the model boundary:

```kedi
>> Extract [count: int] action items from <notes>.
```

This performs a model call and captures `count`. By contrast:

```kedi
[count: int] = `len(notes.splitlines())`
```

is deterministic Python assignment and does not contact a model. Use a template
when the transformation needs model judgement; use Python when the answer is
deterministic and locally computable.

## Dataflow at a Glance

Angle brackets read values; square brackets introduce or assign values:

```kedi
[topic] = API compatibility
>> Explain <topic> and return [summary: str].
= <summary>
```

`<topic>` is an R-value substitution. `[summary: str]` is an L-value output
capture. The same bracket syntax can appear on the left of `=` for native
assignment, where no model is involved.

## Types and Structured Results

Types can annotate outputs, assignments, parameters, returns, and custom type
fields. Kedi resolves built-in names, Python type expressions, and custom types,
then validates values at runtime. Adapters receive structured schemas when they
support them.

## Procedures and Scope

Procedures create reusable lexical scopes:

```kedi
@normalize(value: str, lower: bool = `True`) -> str:
  = `value.strip().lower() if lower else value.strip()`
```

Parameters and local assignments do not leak to callers. Top-level agent state
is captured by following procedures; directives inside a procedure affect only
the remainder of that procedure's lexical block.

## Complete Language Map

Read the section in this order:

1. [Source Structure](source-structure.md)
2. [Templates and Invokes](templates-and-invokes.md)
3. [Substitutions and Calls](substitutions-and-calls.md)
4. [Outputs and Assignments](outputs-and-assignments.md)
5. [Procedures](procedures.md)
6. [Parameters and Returns](parameters-and-returns.md)
7. [Types](types.md)
8. [Multiline Syntax and Escaping](multiline-and-escaping.md)

Modules, agent directives, tests, and Python embedding are documented in their
own sections because each has independent scoping and runtime rules.
