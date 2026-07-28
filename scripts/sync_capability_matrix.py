"""Generate the built-in adapter capability tables from Kedi metadata."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from kedi.agent_adapter import (
    ACPAdapter,
    ClaudeAdapter,
    CodexAdapter,
    DSPyAdapter,
    LangChainAdapter,
    PydanticAdapter,
)  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs" / "reference" / "capability-matrix.md"
START_MARKER = "<!-- BEGIN GENERATED ADAPTER CAPABILITIES -->"
END_MARKER = "<!-- END GENERATED ADAPTER CAPABILITIES -->"

ADAPTERS = (
    ("Pydantic AI", PydanticAdapter),
    ("DSPy", DSPyAdapter),
    ("LangChain", LangChainAdapter),
    ("Claude Agent SDK", ClaudeAdapter),
    ("Codex App Server", CodexAdapter),
    ("ACP", ACPAdapter),
)
CAPABILITIES = (
    ("Structured output", "supports_structured_output"),
    ("Kedi tool registration", "supports_tool_registration"),
    ("Kedi-declared MCP", "supports_mcp"),
    ("Profile override", "supports_profile_override"),
    ("Model override", "supports_model_override"),
    ("Effort", "supports_effort"),
    ("Settings", "supports_settings"),
    ("Code mode", "supports_codemode"),
    ("Native approvals", "supports_native_approvals"),
    ("Dynamic native approval handler", "supports_native_approval_handler"),
    ("Foreground subagents", "supports_subagents"),
    ("Background subagents", "supports_background_subagents"),
)


def _availability(value: bool | None) -> str:
    return "yes" if value is True else "no"


def _table(adapters: tuple[tuple[str, type[Any]], ...]) -> str:
    headings = ["Capability", *(name for name, _ in adapters)]
    lines = [
        "| " + " | ".join(headings) + " |",
        "| --- | " + " | ".join(":---:" for _ in adapters) + " |",
    ]
    for label, attribute in CAPABILITIES:
        values = (
            _availability(getattr(adapter.capabilities, attribute)) for _, adapter in adapters
        )
        lines.append("| " + " | ".join((label, *values)) + " |")
    return "\n".join(lines)


def _generated_section() -> str:
    frameworks = tuple(adapter for adapter in ADAPTERS if adapter[1].kind == "agent-framework")
    harnesses = tuple(adapter for adapter in ADAPTERS if adapter[1].kind == "agent-harness")
    return "\n".join(
        (
            START_MARKER,
            "## Framework Adapters",
            "",
            _table(frameworks),
            "",
            "## Agent Harnesses",
            "",
            _table(harnesses),
            END_MARKER,
        )
    )


def _updated_document(document: str) -> str:
    if document.count(START_MARKER) != 1 or document.count(END_MARKER) != 1:
        raise ValueError(
            f"{MATRIX_PATH.relative_to(ROOT)} must contain exactly one generated section"
        )
    before, remainder = document.split(START_MARKER, maxsplit=1)
    _, after = remainder.split(END_MARKER, maxsplit=1)
    return before + _generated_section() + after


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed matrix differs from adapter metadata",
    )
    args = parser.parse_args()

    document = MATRIX_PATH.read_text(encoding="utf-8")
    updated = _updated_document(document)
    if args.check:
        if updated != document:
            raise SystemExit(
                "Adapter capability matrix is stale; run python scripts/sync_capability_matrix.py"
            )
        print("Adapter capability matrix matches Kedi metadata")
        return

    MATRIX_PATH.write_text(updated, encoding="utf-8")
    print(f"Updated {MATRIX_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
