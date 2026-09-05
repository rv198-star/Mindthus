#!/usr/bin/env python3
"""Create a fresh allocation draft from explicit refreshed context and a checked parent.

Parent conclusions are references only. Nothing is copied from the parent decision
into the new allocation context. This command neither modifies a run nor executes work.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from draft_sra_context import draft_context, write_draft
from sra_domain import RERANK_LINEAGE_SCHEMA, EXTENDED_INPUT_SCHEMA
from sra_io import load_json, SraRuntimeError
from sra_runtime import run_check
from sra_serialization import digest_data


def rerank_draft(parent_dir: Path, refreshed_context: Any, *, run_id: str, reason: str) -> dict[str, Any]:
    if not isinstance(reason, str) or not reason.strip():
        raise SraRuntimeError("rerank requires an explicit change or reconsideration reason")
    if not isinstance(refreshed_context, dict):
        raise SraRuntimeError("rerank requires caller-supplied refreshed decision context")
    if refreshed_context.get("schema_version") not in (None, EXTENDED_INPUT_SCHEMA):
        raise SraRuntimeError("rerank needs refreshed v0.4 input; legacy parent input is not silently migrated")
    final = load_json(parent_dir / "final-decision.json")
    raw = load_json(parent_dir / "raw-input.json")
    report = run_check(parent_dir)
    if report["status"] != "ok":
        raise SraRuntimeError("parent integrity check failed; rerank cannot bless damaged authority")
    if (digest_data(final) != digest_data(load_json(parent_dir / "final-decision.json"))
            or digest_data(raw) != digest_data(load_json(parent_dir / "raw-input.json"))):
        raise SraRuntimeError("parent changed during rerank assessment; read a fresh snapshot")
    if run_id == raw["run_id"]:
        raise SraRuntimeError("rerank must use a new run_id")
    if "rerank_lineage" in refreshed_context:
        raise SraRuntimeError("supply refreshed context without inherited lineage metadata")
    result = draft_context(refreshed_context, run_id=run_id)
    result["draft"]["rerank_lineage"] = {
        "schema_version": RERANK_LINEAGE_SCHEMA,
        "parent_run_id": raw["run_id"],
        "parent_raw_input_hash": digest_data(raw),
        "parent_decision_hash": digest_data(final),
        "reason": reason,
    }
    result["reassessment_required"] = [
        "current capacity and window", "evidence freshness and current commitments",
        "candidate set and dependencies", "risk and authority", "any changed completion criteria",
    ]
    result["claim_ceiling"] = (
        "The parent was integrity-checked when this draft was created. The link is not "
        "inherited permission or a freshness proof; current facts and decisions require new assessment."
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path, help="Explicit refreshed context; no parent auto-fill.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.output and args.output.resolve().is_relative_to(args.parent.resolve()):
            raise SraRuntimeError("rerank output must be outside the immutable parent run")
        result = rerank_draft(args.parent, load_json(args.input), run_id=args.run_id, reason=args.reason)
        if args.output:
            write_draft(args.output, result["draft"])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "ready_for_prepare" else 2
    except (SraRuntimeError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
