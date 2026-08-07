# Complete Program

This compact application combines typed extraction, deterministic Python,
procedure tools, profiles, command-line input, tests, and evals without hiding
the boundaries between them.

## `incident_report.kedi`

````kedi
```
INCIDENTS = {
    42: "Checkout requests time out. Payments owns mitigation.",
    77: "Search results are stale. Search owns reindexing.",
}
```

~Incident(
  id: int,
  title: str,
  owner: str,
  severity: Literal["low", "medium", "high", "critical"]
)

@lookup_incident(incident_id: int) -> str:
  ###
  Return the source report for one incident identifier.
  ###
  = `INCIDENTS[incident_id]`

@extract_incident(incident_id: int, report: str) -> Incident:
  >> Report <report> describes [incident: Incident].
  Its identifier is <incident_id>.
  = `incident`

@format_incident(incident: Incident) -> str:
  = `f"#{incident.id} [{incident.severity}] {incident.title} - {incident.owner}"`

> profile: analyst:
    > adapter: pydantic
    > model: groq:qwen/qwen3-32b
    > system: Use tools for source data. Never invent an incident.
    > use: lookup_incident
    > approval: allow

@answer_request(request: str) -> str:
  > use: analyst
  >> Answer <request>. Use lookup_incident when an identifier is present.
  Return [answer: str].
  = <answer>

@test: format_incident:
  > case: formats_all_fields:
    ```
    incident = Incident(id=1, title="Latency", owner="Platform", severity="high")
    assert format_incident(incident) == "#1 [high] Latency - Platform"
    ```

[incident_id: int] = `int(args.incident_id)`
[source: str] = `lookup_incident(incident_id)`
[incident: Incident] = `extract_incident(incident_id, source)`

= `format_incident(incident)`

@eval: extract_incident:
  > data: reports:
    = ```
    return [
      ((42, INCIDENTS[42]), {"owner": "Payments"}),
      ((77, INCIDENTS[77]), {"owner": "Search"}),
    ]
    ```
  > metric: owner_accuracy(reports):
    = `extract_incident(*reports).owner == expected["owner"]`
````

Run incident 42:

```bash
kedi incident_report.kedi --incident-id 42
```

Unknown CLI options become fields on the reserved `args` binding; hyphens are
normalized to underscores. The first repeated option wins.

## Why Each Boundary Is Explicit

- `lookup_incident` is deterministic and should not be a model call.
- `extract_incident` uses a typed capture because understanding prose requires
  a model.
- `= `incident`` returns the native custom type.
- `format_incident` renders only at the final presentation boundary.
- The profile captures a stable adapter, model, instructions, tool, and policy.
- The test checks deterministic formatting without spending model tokens.
- The eval scores semantic extraction with explicit expected data.

The top-level assignment passes native values through Python expressions.
Writing `<incident>` inside a prompt would intentionally serialize it for the
model instead.

## Verification Commands

```bash
kedi incident_report.kedi --parse
kedi incident_report.kedi --test
kedi incident_report.kedi --eval
```

`--test` and `--eval` are validation modes; they do not continue into ordinary
top-level execution. Keep deterministic tests separate from model-backed evals
so failures identify the correct layer.
