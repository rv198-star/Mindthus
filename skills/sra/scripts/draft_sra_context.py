#!/usr/bin/env python3
"""Assemble a canonical SRA input draft; never allocate or prepare an execution run.

The caller/Agent supplies sourced semantics. Only identifiers and inert structural
defaults are generated. Missing goals, quantities, projections, evidence timestamps,
and dependency knowledge remain missing. No NLP or priority inference lives here.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from sra_domain import EXTENDED_INPUT_SCHEMA
from sra_io import SraRuntimeError, load_json
from sra_policy import PROPORTIONATE_POLICY
from sra_criteria import FIELDS as CRITERION_FIELDS, criterion_hash
from sra_runtime_core import validate_context_input

DRAFT_SCHEMA = "sra.context-draft.v1"


def draft_context(partial: Any, *, run_id: str | None = None) -> dict[str, Any]:
    if not isinstance(partial, dict):
        raise SraRuntimeError("intake requires a structured context object supplied by the caller")
    draft = copy.deepcopy(partial)
    draft.setdefault("schema_version", EXTENDED_INPUT_SCHEMA)
    if run_id is not None:
        if draft.get("run_id") not in (None, run_id):
            raise SraRuntimeError("explicit run_id conflicts with the supplied draft")
        draft["run_id"] = run_id
    draft.setdefault("run_id", "sra-" + uuid4().hex[:16])
    for key in ("mode", "view_plan", "coverage_review"):
        draft.setdefault(key, "auto")
    for key in ("escalation_signals", "contamination_signals", "coverage_signals",
                "assumptions", "evidence", "context_items", "source_inventory", "known_omissions"):
        draft.setdefault(key, [])
    draft.setdefault("overrides", {})
    draft.setdefault("state_context", {})
    if draft["schema_version"] == EXTENDED_INPUT_SCHEMA:
        draft.setdefault("execution_policy", {
            "version": PROPORTIONATE_POLICY,
            "risk_level": "unknown",
            "assessment_basis": "Risk has not been assessed; retain conservative calibration.",
        })
    candidates = draft.get("candidates", [])
    for index, candidate in enumerate(candidates if isinstance(candidates, list) else []):
        if not isinstance(candidate, dict):
            continue
        candidate.setdefault("candidate_id", f"C-{index + 1:02d}")
        for key in ("evidence_refs", "assumption_refs", "unlocks", "substitutes_for"):
            candidate.setdefault(key, [])
        # [] asserts that no prerequisite is declared; the compiler cannot invent that.
        candidate.setdefault("depends_on", None)
    catalog = draft.get("completion_criteria")
    if isinstance(catalog, dict) and isinstance(catalog.get("items"), list):
        for criterion in catalog["items"]:
            if isinstance(criterion, dict) and set(criterion) == CRITERION_FIELDS - {"content_hash"}:
                criterion["content_hash"] = criterion_hash(criterion)
    allowed = {"schema_version", "run_id", "decision_question", "mode", "view_plan", "coverage_review",
               "execution_policy", "overrides", "escalation_signals", "contamination_signals", "coverage_signals",
               "allocation_frame", "active_candidate_id", "candidates", "evidence", "assumptions", "context_items",
               "state_context", "source_inventory", "known_omissions", "completion_criteria", "rerank_lineage"}
    try:
        findings = ["intake contains unsupported or judgment fields: " + ", ".join(sorted(set(draft) - allowed))] if set(draft) - allowed else validate_context_input(draft)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        findings = [f"incomplete or malformed draft: {exc}"]
    return {
        "schema_version": DRAFT_SCHEMA,
        "status": "ready_for_prepare" if not findings else "needs_input",
        "draft": draft,
        "findings": findings,
        "authority": "draft_only",
        "claim_ceiling": "Shape readiness is not factual truth, priority, permission or allocation.",
        "next_action": (
            "Review the sourced input, then explicitly run prepare_sra_run.py on the draft."
            if not findings else "Resolve only missing inputs that can affect this allocation; do not invent them."
        ),
    }


def write_draft(path: Path, draft: dict[str, Any]) -> None:
    """Exclusive output prevents using intake to overwrite raw input or authority."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(draft, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="New canonical draft file, never an existing run file.")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    try:
        report = draft_context(load_json(args.input), run_id=args.run_id)
        if args.output:
            write_draft(args.output, report["draft"])
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "ready_for_prepare" else 2
    except (SraRuntimeError, OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
