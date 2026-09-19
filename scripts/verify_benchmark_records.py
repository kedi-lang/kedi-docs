"""Derive a content-free metrics projection from frozen Harbor evidence archives.

Never extracts archive members or executes benchmark subjects. Run with the
documented genai-prices version to preserve the historical price interpretation.
"""

import argparse
import hashlib
import json
import math
import tarfile
from datetime import datetime
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path, PurePosixPath


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def summarize(rows):
    names = [row["task"] for row in rows]
    if len(rows) != 89 or len(set(names)) != 89:
        raise ValueError("Expected exactly 89 unique tasks")
    if any(row["reward"] not in (None, 0, 1) for row in rows):
        raise ValueError("Non-binary reward")
    keys = (
        "input_tokens",
        "cache_tokens",
        "output_tokens",
        "requests",
        "tool_calls",
        "cost_usd",
        "duration_seconds",
    )
    totals = {key: sum(row[key] for row in rows) for key in keys}
    solved = sum(row["reward"] == 1 for row in rows)
    return {
        "tasks": len(rows),
        "solved": solved,
        "score": solved / len(rows),
        "scored": sum(row["reward"] is not None for row in rows),
        "totals": totals,
        "cache_read_ratio": totals["cache_tokens"] / totals["input_tokens"],
        "cost_per_task_usd": totals["cost_usd"] / len(rows),
        "cost_per_solved_task_usd": totals["cost_usd"] / solved if solved else None,
        "wall_seconds": (
            max(datetime.fromisoformat(row["finished_at"]) for row in rows)
            - min(datetime.fromisoformat(row["started_at"]) for row in rows)
        ).total_seconds(),
        "max_request_input_tokens": max(row["max_request_input_tokens"] for row in rows),
        "distributions": {
            key: {
                "p50": percentile([row[key] for row in rows], 0.5),
                "mean": totals[key] / len(rows),
                "p90": percentile([row[key] for row in rows], 0.9),
                "p95": percentile([row[key] for row in rows], 0.95),
                "max": max(row[key] for row in rows),
            }
            for key in keys
        },
    }


def read_archive(path):
    from genai_prices import Usage, calc_price

    results, requests, runtime_results = {}, {}, {}
    with tarfile.open(path) as archive:
        for member in archive:
            parts = PurePosixPath(member.name).parts
            if not member.isfile() or len(parts) < 4 or parts[0] != "jobs":
                continue
            identity = parts[1:3]
            if len(parts) == 4 and parts[-1] == "result.json":
                if identity in results:
                    raise ValueError("Duplicate result member")
                results[identity] = json.load(archive.extractfile(member))
            elif parts[3:] == ("agent", "model-requests.jsonl"):
                if identity in requests:
                    raise ValueError("Duplicate request evidence member")
                requests[identity] = [
                    json.loads(line) for line in archive.extractfile(member) if line.strip()
                ]
            elif parts[3:] == ("agent", "kedi-result.json"):
                runtime_results[identity] = json.load(archive.extractfile(member))
    rows = []
    for identity, result in sorted(results.items()):
        completed = [r for r in requests[identity] if r["event"] == "model_request_completed"]
        if not completed:
            raise ValueError("Task has no completed request evidence")
        usage = [r["response"]["usage"] for r in completed]
        cost = Decimal(0)
        for request, tokens in zip(completed, usage):
            if not 0 <= tokens["cache_read_tokens"] <= tokens["input_tokens"]:
                raise ValueError("Invalid cache accounting")
            cost += calc_price(
                Usage(
                    input_tokens=tokens["input_tokens"],
                    output_tokens=tokens["output_tokens"],
                    cache_read_tokens=tokens["cache_read_tokens"],
                    cache_write_tokens=tokens.get("cache_write_tokens", 0),
                ),
                "gpt-5.6-luna",
                provider_id="openai",
                genai_request_timestamp=datetime.fromisoformat(request["recorded_at"]),
            ).total_price
        row = {
            "task": result["task_name"].removeprefix("terminal-bench/"),
            "batch": "standard81-c2" if "standard81-c2" in identity[0] else "high-memory8-c1",
            "reward": (result.get("verifier_result") or {}).get("rewards", {}).get("reward"),
            "exception_type": (result.get("exception_info") or {}).get("exception_type"),
            "input_tokens": sum(u["input_tokens"] for u in usage),
            "cache_tokens": sum(u["cache_read_tokens"] for u in usage),
            "output_tokens": sum(u["output_tokens"] for u in usage),
            "requests": len(completed),
            "tool_calls": runtime_results[identity]["usage"]["tool_calls"],
            "emitted_tool_call_parts": sum(
                p.get("kind") == "tool-call" for r in completed for p in r["response"]["parts"]
            ),
            "cost_usd": float(cost),
            "started_at": result["started_at"],
            "finished_at": result["finished_at"],
            "duration_seconds": (
                datetime.fromisoformat(result["finished_at"])
                - datetime.fromisoformat(result["started_at"])
            ).total_seconds(),
            "max_request_input_tokens": max(u["input_tokens"] for u in usage),
        }
        agent = result["agent_result"]
        for field, harbor_field in [
            ("input_tokens", "n_input_tokens"),
            ("cache_tokens", "n_cache_tokens"),
            ("output_tokens", "n_output_tokens"),
        ]:
            if row[field] != agent[harbor_field]:
                raise ValueError(f"Usage mismatch for {row['task']}: {field}")
        rows.append(row)
    summary = summarize(rows)
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"archive_sha256": digest, "summary": summary, "tasks": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pydantic", required=True, type=Path)
    parser.add_argument("--langchain", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    runs = {name: read_archive(getattr(args, name)) for name in ("pydantic", "langchain")}
    if {r["task"] for r in runs["pydantic"]["tasks"]} != {
        r["task"] for r in runs["langchain"]["tasks"]
    }:
        raise ValueError("Task sets differ")
    data = {
        "pricing_package": f"genai-prices=={version('genai-prices')}",
        "model": "gpt-5.6-luna",
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({name: run["summary"] for name, run in runs.items()}, indent=2))


if __name__ == "__main__":
    main()
