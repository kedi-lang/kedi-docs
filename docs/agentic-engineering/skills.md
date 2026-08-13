# Skills

Skills are scoped instruction documents loaded on demand through two read-only
tools. Kedi does not inject every skill into every prompt.

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
> skills: enabled

>> Use a relevant project skill if one applies, then return [answer: str].
= <answer>
```

The compact directive registers `list_skills` and `read_skill`. Disable an
inherited policy with `> skills: disabled`.

Profiles can carry the same setting:

```kedi
> profile: maintainer:
    > adapter: pydantic
    > skills: enabled
```

The expanded form configures discovery:

```kedi
> skills:
    enabled: true
    cwd: workspace
    max_skills: 40
    include_registry: true
    include_all: false
    exclude_paths: `["~/.agents/skills"]`
```

`enabled` is required in the expanded form. `cwd` changes the base of the
project-local source and resolves relative to the Kedi program. `max_skills`
accepts 1 through 100. `include_registry` controls the Kedi registry source.
`include_all: false` selects the first source containing a valid skill;
`include_all: true` merges every source. `exclude_paths` accepts an inline
Python list and may exclude a source root or individual skill directory.

## Source Priority

Kedi checks sources in this order:

1. `$KEDI_HOME/registry/skills`, normally `~/.kedi/registry/skills`;
2. `<cwd>/.agents/skills`;
3. `~/.agents/skills`.

Merged names are deterministic. If sources define the same skill name,
`read_skill` uses the highest-priority copy. Set `include_registry: false` to
skip only the registry source.

## Discovery Tools

`list_skills(all: bool = false, limit: int = 20) -> list[str]` returns valid
skill identifiers in deterministic sorted order. `limit` must be a positive
integer no greater than 100 and is additionally bounded by `max_skills`.
Source merging is configured by `include_all`; the `all` tool argument remains
accepted for API compatibility.

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

## Install Into the Kedi Registry

Install a one-file skill from a local directory or GitHub repository:

```bash
kedi skills add --path ~/my-skill
kedi skills add --repo owner/skill-repository
```

The source must have `SKILL.md` at its root. Kedi copies only that file into
`~/.kedi/registry/skills/<name>/SKILL.md`. GitHub input uses the
`OWNER/REPOSITORY` form, performs a credential-free shallow checkout, and
records the checked-out revision. Installation is user-scoped and never writes
into the project.

## Resolution and Security Checks

Kedi rejects invalid names, absolute/traversal attempts, symlink escapes,
missing/non-file targets, non-UTF-8 content, and files larger than 256 KiB.

`list_skills` omits entries that fail validation rather than advertising
unreadable content. `read_skill` reports the specific failure when explicitly
requested.

These checks protect skill-file resolution. Skill content is still trusted
instruction text and may attempt to influence agent behavior. Review project
and installed skills, and keep approvals/tool boundaries active.

## When to Use Skills

Use a skill for repeatable operational guidance that should be selected at task
time: release procedures, code-review policy, migration checklists, or domain
workflows. Put unconditional behavior in `> system:` and executable typed
operations in tools instead.

Skills do not grant capabilities. A skill may instruct use of a tool, but the
profile must separately expose that tool and its approval policy.
