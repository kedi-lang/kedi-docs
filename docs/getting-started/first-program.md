# Your First Kedi Program

## Create a `.kedi` File

Create `review.kedi`:

```kedi
~Review(decision: Literal["approve", "revise"], summary: str)

@review_change(title: str, diff_summary: str) -> Review:
  >> Review the change titled <title>.
  The diff summary is: <diff_summary>
  Return [review: Review].
  = `review`

= `review_change(args.title, args.diff_summary).model_dump_json()`
```

Run it:

```bash
kedi review.kedi \
  --title "Reject unsafe paths" \
  --diff-summary "Adds containment checks before file access"
```

## Add Inputs

`title` and `diff_summary` are typed procedure parameters. The final call uses
a single-backtick Python expression:

```kedi
[review: Review] = `review_change(args.title, args.diff_summary)`
```

This passes native strings and preserves the native `Review` return. An angle
call renders its result to text, so it is appropriate for procedures returning
`str`, not for carrying a `Review` object through the dataflow.

## Write a Template

The two continuation rows after `>>` are joined with newlines and sent as one
model request:

```kedi
>> Review the change titled <title>.
The diff summary is: <diff_summary>
Return [review: Review].
```

`<title>` and `<diff_summary>` are substitutions. They read existing values;
they do not ask the model to generate anything. Use substitutions for runtime
facts, user input, prior procedure results, or deterministic Python values.

## Capture a Typed Output

`[review: Review]` is an output capture. The selected adapter receives a schema
derived from the Kedi type and must return a matching object. Capture output
when downstream logic needs typed fields or when the response must be validated.

Kedi also exposes raw capture for deliberately unstructured provider text:

```kedi
@review_change(title: str, diff_summary: str) -> str:
  [review] << Review <title>: <diff_summary>
  = <review>
```

Do not put output fields inside a raw `<<` prompt. Raw captures always produce a
string; types other than `str` are rejected. Prefer the typed version above for
normal application dataflow, including typed `str` results.

## Return the Result

Inside the typed version, ``= `review` `` returns the native `Review` model.
The top-level expression serializes it deliberately:

```kedi
= `review_change(args.title, args.diff_summary).model_dump_json()`
```

Use a native return when Python or another Kedi procedure needs the object. Use
a rendered return when the program's final output is text.

## Pass Command-Line Arguments

Application flags belong after the Kedi source:

```bash
kedi review.kedi --title "Update parser" --diff-summary "Adds package syntax"
```

Dashed names become underscore attributes, so `--diff-summary` is available as
`args.diff_summary`. Flags without values become booleans. Kedi's own options,
such as `--adapter` and `--test`, are parsed by the CLI rather than exposed as
application arguments.

## Parse Before Running

```bash
kedi parse review.kedi
```

Parsing catches malformed syntax, duplicate selective imports, invalid
directives, and other structural errors. It cannot prove that provider
credentials exist or that a runtime-computed type is valid. Those checks happen
during compilation or execution.
