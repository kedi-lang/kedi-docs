"""Parse-check Kedi code fences in the documentation."""

from __future__ import annotations

import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from kedi.lang import parse_program  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
OPENING_FENCE = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,})(?P<info>.*)$")


@dataclass(frozen=True)
class KediFence:
    markdown_path: Path
    markdown_line: int
    source_path: str
    source: str


def _fence_options(info: str) -> tuple[bool, str | None]:
    parts = shlex.split(info.strip())
    if not parts or parts[0] != "kedi":
        return False, None

    source_path: str | None = None
    for option in parts[1:]:
        if option == "no-parse":
            return True, None
        if option.startswith("file="):
            source_path = option.removeprefix("file=")
            if not source_path:
                raise ValueError("A Kedi fence's file= option cannot be empty")
            continue
        raise ValueError(f"Unknown Kedi fence option: {option!r}")
    return False, source_path


def _default_source_path(markdown_path: Path, source: str, line: int) -> str:
    if any(row.lstrip().startswith("> package:") for row in source.splitlines()):
        return "package.kedi"
    relative = markdown_path.relative_to(DOCS_DIR).with_suffix("")
    return f"<docs:{relative.as_posix()}:{line}>"


def _kedi_fences(markdown_path: Path) -> list[KediFence]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    fences: list[KediFence] = []
    index = 0

    while index < len(lines):
        match = OPENING_FENCE.match(lines[index])
        if match is None:
            index += 1
            continue

        info = match.group("info")
        try:
            skip, configured_path = _fence_options(info)
        except ValueError as exc:
            relative = markdown_path.relative_to(ROOT)
            raise ValueError(f"{relative}:{index + 1}: {exc}") from exc

        fence = match.group("fence")
        closing = re.compile(rf"^ {{0,3}}`{{{len(fence)},}}[ \t]*$")
        end = index + 1
        while end < len(lines) and closing.match(lines[end]) is None:
            end += 1
        if end == len(lines):
            relative = markdown_path.relative_to(ROOT)
            raise ValueError(f"{relative}:{index + 1}: unclosed Markdown fence")

        if info.strip().split(maxsplit=1)[:1] == ["kedi"] and not skip:
            source = "\n".join(lines[index + 1 : end]) + "\n"
            source_path = configured_path or _default_source_path(
                markdown_path,
                source,
                index + 2,
            )
            fences.append(
                KediFence(
                    markdown_path=markdown_path,
                    markdown_line=index + 2,
                    source_path=source_path,
                    source=source,
                )
            )
        index = end + 1

    return fences


def main() -> None:
    fences: list[KediFence] = []
    failures: list[str] = []

    for markdown_path in sorted(DOCS_DIR.rglob("*.md")):
        try:
            fences.extend(_kedi_fences(markdown_path))
        except ValueError as exc:
            failures.append(str(exc))

    for fence in fences:
        try:
            parse_program(fence.source, source_path=fence.source_path)
        except Exception as exc:
            relative = fence.markdown_path.relative_to(ROOT)
            failures.append(
                f"{relative}:{fence.markdown_line} (parsed as {fence.source_path}): {exc}"
            )

    if failures:
        print("Kedi documentation example validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"\n- {failure}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Parsed {len(fences)} Kedi documentation fences successfully")


if __name__ == "__main__":
    main()
