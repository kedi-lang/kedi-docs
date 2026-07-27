# Skills

Skills are project-local instruction documents loaded on demand through two
read-only tools. Kedi does not inject every skill into every prompt.

## Layout

```text
.agents/
  skills/
    release-review/
      SKILL.md
    incident-triage/
      SKILL.md
```

Each skill is exactly one UTF-8 `SKILL.md` under one skill-name directory.
Skill names start with an alphanumeric character and may contain letters,
digits, `_`, and `-`.

## Enable Skills

```kedi
> use: skills

>> Use a relevant project skill if one applies, then return [answer: str].
= <answer>
```

This single-line reserved form registers `list_skills` and `read_skill`.
The multiline form is always a procedure-tool list and therefore does not
enable skills.

Profiles can carry the same setting:

```kedi
> profile: maintainer:
    > adapter: pydantic
    > use: skills
```

## Discovery Tools

`list_skills(all: bool = false, limit: int = 20) -> list[str]` returns valid
skill identifiers in deterministic sorted order. `limit` must be a positive
integer no greater than 100. `all` is reserved for future source selection and
currently uses the same project-local root.

`read_skill(skill_name: str) -> str` returns the exact UTF-8 file content for
one valid listed skill.

Both tools are `read_only`, so the default approval policy allows them.

## On-Demand Loading

Enabling skills adds compact instructions telling the agent to:

1. call `list_skills` when reusable guidance may help;
2. call `read_skill` for a listed relevant name;
3. follow it only for the current task;
4. never claim to have read a skill whose contents were not returned.

The model does not know a skill's body until it reads that skill. This avoids
filling every context with unrelated instructions and makes skill usage visible
in the tool trace.

## Root and Security Checks

The default root is `.agents/skills` beneath the current working directory.
Kedi rejects invalid names, absolute/traversal attempts, symlink escapes,
missing/non-file targets, non-UTF-8 content, and files larger than 256 KiB.

`list_skills` omits entries that fail validation rather than advertising
unreadable content. `read_skill` reports the specific failure when explicitly
requested.

These checks protect skill-file resolution. Skill content is still trusted
instruction text and may attempt to influence agent behavior. Review project
skills and keep approvals/tool boundaries active.

## When to Use Skills

Use a skill for repeatable operational guidance that should be selected at task
time: release procedures, code-review policy, migration checklists, or domain
workflows. Put unconditional behavior in `> system:` and executable typed
operations in tools instead.

Skills do not grant capabilities. A skill may instruct use of a tool, but the
profile must separately expose that tool and its approval policy.
