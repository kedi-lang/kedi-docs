# Evaluation and Optimization

This example improves one extraction prompt with supervised examples and a
metric that returns both a score and actionable feedback.

## Complete Program

```kedi
> adapter: pydantic
> model: groq:qwen/qwen3-32b

@extract_owner(ticket: str) -> str:
  > optimize: owner_prompt:
    Read the support ticket below.
    Ticket: <ticket>
    Return only the team that owns the next action: [owner]
  = `owner`

@eval: extract_owner:
  > data: tickets:
    = ```
    return [
      ("Payments: retries fail after authorization", {"owner": "Payments"}),
      ("Search indexing is twelve hours behind", {"owner": "Search"}),
      ("Identity reports invalid refresh tokens", {"owner": "Identity"}),
    ]
    ```

  > test_data: tickets:
    = ```
    return [
      ("Checkout cannot create payment intents", {"owner": "Payments"}),
      ("New documents do not appear in results", {"owner": "Search"}),
    ]
    ```

  > metric: exact_owner(tickets):
    = ```
    actual = extract_owner(tickets).strip().casefold()
    wanted = expected["owner"].casefold()
    if actual == wanted:
        return 1.0, None
    return 0.0, f"returned {actual!r}; expected {wanted!r}"
    ```

= `extract_owner("Identity: sessions expire immediately after login")`
```

The bare prompt lines inside `> optimize:` are intentional. They are legacy
template syntax accepted only inside `> optimize:` and `> auto:` bodies. They
are newline-joined into **one model call**, exactly like:

```kedi
@extract_owner_explicit(ticket: str) -> str:
  > optimize: owner_prompt:
    >> Read the support ticket below.
    Ticket: <ticket>
    Return only the team that owns the next action: [owner]
  = `owner`
```

Do not add `>>` to each continuation line. Bare template lines outside these
two special directives are parse errors.

## Run Tests and Evals

```bash
kedi program.kedi --eval
```

Normal evaluation uses matching `test_data` when present; otherwise it falls
back to `data`. It reports one selected score, not separate training and test
scores.

## Run GEPA

```bash
kedi program.kedi \
  --optimize \
  --optimizer gepa \
  --optimizer-max-metric-calls 30 \
  --eval
```

GEPA trains on `data`, validates against matching `test_data`, and stores only
an optimized prefix. The source prompt and its output schema remain
authoritative.

Generated files are:

- `program.kedi.optimized.json` for selected prompt prefixes;
- `program.kedi.optimized_scores.json` for score metadata;
- `program.kedi.gepa/` for per-span checkpoints.

Use `--optimizer-fresh` to remove these optimization artifacts before a new
GEPA run. `--no-cache` instead controls generated `> auto:` code and does not
reset optimizer state.

## Dataset Shape

Explicit `(input, expected_dict)` rows are the least ambiguous format across
evaluation and optimization. For a procedure with multiple parameters, use
`((arg1, arg2), expected_dict)`. Metrics should be deterministic, stable, and
cheap compared with the model call; vague feedback gives the optimizer little
usable evidence.
