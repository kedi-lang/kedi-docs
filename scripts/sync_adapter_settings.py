"""Generate the adapter model-settings tables from Kedi metadata.

Reads the setting-key sets from ``kedi.agent_profile.settings`` (the
installed kedi package, or ``.kedi-source`` / ``$KEDI_SOURCE`` in a source
checkout) and rewrites the tables between the generated markers in the
Pydantic AI and LangChain adapter pages. Descriptions live here because
``settings.py`` only declares key names.

Usage:
    python scripts/sync_adapter_settings.py [--check]
"""

from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

START_MARKER = "<!-- BEGIN GENERATED MODEL SETTINGS -->"
END_MARKER = "<!-- END GENERATED MODEL SETTINGS -->"

# Short descriptions of each setting key. Standard model parameters follow
# their usual provider meaning; Kedi-owned keys follow the Kedi DSL/code.
DESCRIPTIONS = {
    "api_key": "Provider API key used when constructing the chat model.",
    "base_url": "Base URL for an OpenAI-compatible endpoint.",
    "callbacks": "LangChain callbacks attached to model calls.",
    "configurable_fields": "Fields exposed as LangChain configurable fields.",
    "configurable_prefix": "Prefix applied to configurable field names.",
    "context_limit": "Model context window in tokens for Kedi's request ceiling; default 200,000.",
    "decision_boolean_threshold": "Probability above which a boolean decision counts as true.",
    "decision_tool_call_threshold": "Probability above which a hand-off tool is selected.",
    "disable_streaming": "Disable streaming globally or during tool calls.",
    "extra_body": "Extra fields merged into the provider request body.",
    "extra_headers": "Extra HTTP headers sent with provider requests.",
    "frequency_penalty": "Penalty scaled by how often a token already appeared.",
    "logit_bias": "Per-token logit adjustments.",
    "max_retries": "Maximum retries for failed model calls.",
    "max_tokens": "Maximum tokens in the model response.",
    "media_limit": "Largest media value, in bytes, a request may attach; default 20 MB cap.",
    "metadata": "Metadata attached to model calls.",
    "model_kwargs": "Extra keyword arguments passed to the chat model.",
    "organization": "Provider organization identifier.",
    "parallel_tool_calls": "Whether the model may call several tools in one turn.",
    "presence_penalty": "Penalty for repeating tokens already present.",
    "rate_limiter": "Rate limiter applied to model calls.",
    "request_retries": "Retries for transient provider request failures; does not replay tools or entire runs.",
    "reasoning": 'Reasoning configuration mapping (for example `{"effort": "high"}`).',
    "reasoning_effort": "Reasoning effort level for models without a reasoning mapping.",
    "response_cache": "Enable provider response caching for identical requests.",
    "response_cache_ttl": "Cache time-to-live in seconds for cached responses.",
    "seed": "Seed for deterministic sampling where the provider supports it.",
    "service_tier": "Provider service tier (`auto`, `default`, `flex`, `priority`).",
    "stop": "Stop strings for the chat model.",
    "stop_sequences": "Sequences that stop generation.",
    "stream_usage": "Include token usage in streamed responses.",
    "streaming": "Enable streaming responses.",
    "tags": "Tags attached to model calls.",
    "temperature": "Sampling temperature; higher values are more random.",
    "thinking": "Thinking budget (`minimal`, `low`, `medium`, `high`, `xhigh`) or boolean.",
    "timeout": "Request timeout in seconds.",
    "tool_choice": "Tool selection policy (`none`, `auto`, `required`).",
    "tool_reason": "Opts into an optional `reason` string on tool calls.",
    "top_p": "Nucleus sampling cutoff.",
}

PAGES = (
    ("docs/agent-adapters/pydantic-ai.md", "PYDANTIC_MODEL_SETTING_KEYS"),
    ("docs/agent-adapters/langchain.md", "LANGCHAIN_MODEL_SETTING_KEYS"),
)


def _settings_source() -> Path:
    candidates = []
    try:
        import kedi  # noqa: PLC0415

        candidates.append(Path(kedi.__file__).resolve().parent)
    except ImportError:
        pass
    for base in (os.environ.get("KEDI_SOURCE"), str(ROOT / ".kedi-source")):
        if base:
            candidates.append(Path(base) / "src" / "kedi")
    for base in candidates:
        source = base / "agent_profile" / "settings.py"
        if source.is_file():
            return source
    raise SystemExit(
        "Cannot find kedi settings.py: install kedi, check out .kedi-source, "
        "or set KEDI_SOURCE to a kedi checkout."
    )


def _setting_keys(source: Path) -> dict[str, set[str]]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    keys: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            if name.endswith("_SETTING_KEYS") and isinstance(node.value, ast.Call):
                keys[name] = {
                    elt.value for elt in node.value.args[0].elts if isinstance(elt, ast.Constant)
                }
    return keys


def _table(keys: set[str]) -> str:
    lines = [
        START_MARKER,
        "",
        "| Setting | Meaning |",
        "| --- | --- |",
    ]
    for key in sorted(keys):
        description = DESCRIPTIONS.get(key)
        if description is None:
            raise SystemExit(f"No description for setting {key!r}; add one to DESCRIPTIONS")
        lines.append(f"| `{key}` | {description} |")
    lines.extend(["", END_MARKER])
    return "\n".join(lines)


def _updated_document(document: str, table: str, relative: str) -> str:
    if document.count(START_MARKER) != 1 or document.count(END_MARKER) != 1:
        raise ValueError(f"{relative} must contain exactly one generated settings table")
    before, remainder = document.split(START_MARKER, maxsplit=1)
    _, after = remainder.split(END_MARKER, maxsplit=1)
    return before + table + after


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when a table is stale")
    args = parser.parse_args()

    keys = _setting_keys(_settings_source())
    runtime = keys["KEDI_RUNTIME_SETTING_KEYS"]
    stale: list[str] = []
    for relative, name in PAGES:
        path = ROOT / relative
        document = path.read_text(encoding="utf-8")
        updated = _updated_document(document, _table(keys[name] | runtime), relative)
        if updated == document:
            continue
        if args.check:
            stale.append(relative)
            continue
        path.write_text(updated, encoding="utf-8")
        print(f"Updated {relative}")
    if stale:
        raise SystemExit(
            "Adapter settings tables are stale; run python scripts/sync_adapter_settings.py: "
            + ", ".join(stale)
        )
    if args.check:
        print("Adapter settings tables match Kedi metadata")


if __name__ == "__main__":
    main()
