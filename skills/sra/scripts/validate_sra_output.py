#!/usr/bin/env python3
"""Validate SRA method-fidelity evidence without duplicating runtime allocation."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime_bootstrap import activate_runtime

activate_runtime(__file__)

from _runtime.core.io import load_json
from _runtime.core.report import Finding, finding, print_shape_report
from _runtime.core.shape import non_empty_string, require_object
from _runtime.fidelity.core import MOVE_FIELDS, MOVE_STATUSES
from sra_domain import (
    AUTHORIZATION_HORIZONS,
    FIDELITY_SCHEMA,
    FINAL_DECISION_SCHEMA,
    FINALIZATION_STATUSES,
    LITE_AUTHORIZATION_HORIZONS,
    RECONCILIATION_OUTCOMES,
    finalization_status_for_outcome,
)

METHOD = "SRA"
REPORT_TITLE = "SRA Method-Fidelity & Evidence Risk Report"
ENTRY_OUTCOMES = {"direct", "lite", "full", "blocked"}
TERMINAL_STATES = FINALIZATION_STATUSES - {"pending"}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
BASE_MOVES = (
    "candidate_horizon_probe",
    "priority_order",
    "resource_contention",
    "evidence_bounded_necessity",
    "contraction",
    "replenishment",
    "meaningful_tranche",
    "switching_vs_sunk_cost",
    "authorization_horizon",
    "defer_stop_or_reserve",
    "rerank_trigger",
    "mode_boundary",
    "claim_ceiling",
)
FULL_MOVES = (
    "minimum_sufficient_bundle",
    "resource_vector",
    "feasibility_and_dominance",
    "reserve_capacity",
)
RUNTIME_REF_FIELDS = (
    "schema_version",
    "artifact_path",
    "artifact_hash",
    "mode",
    "allocation_outcome",
    "finalization_status",
    "authorization_horizon",
)


def _missing_field(path: str) -> Finding:
    return finding("block", "missing-field", f"missing field: {path}", path)


def _invalid_field(path: str, expected: str) -> Finding:
    return finding("block", "invalid-field", f"{path} must be {expected}", path)


def _unsupported_enum(path: str, value: Any, allowed: set[str]) -> Finding:
    allowed_text = ", ".join(sorted(allowed))
    return finding(
        "block",
        "unsupported-enum",
        f"{path} unsupported: {value!r}; expected one of: {allowed_text}",
        path,
    )


def _require_non_empty_string(
    findings: list[Finding],
    data: dict[str, Any],
    field_name: str,
    path: str,
) -> None:
    if field_name not in data:
        findings.append(_missing_field(path))
    elif not non_empty_string(data.get(field_name)):
        findings.append(_invalid_field(path, "a non-empty string"))


def _validate_exit(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    _require_non_empty_string(
        findings,
        data,
        "plain_language_conclusion",
        "plain_language_conclusion",
    )
    _require_non_empty_string(findings, data, "exit_reason", "exit_reason")
    if "transfer_to" in data and not isinstance(data.get("transfer_to"), str):
        findings.append(_invalid_field("transfer_to", "a string"))
    return findings


def _validate_move(findings: list[Finding], move_name: str, move: Any) -> None:
    path = f"required_judgment_moves.{move_name}"
    if not isinstance(move, dict):
        findings.append(_invalid_field(path, "an object"))
        return
    for field_name in MOVE_FIELDS:
        _require_non_empty_string(findings, move, field_name, f"{path}.{field_name}")
    status = move.get("status")
    if isinstance(status, str) and status not in MOVE_STATUSES:
        findings.append(
            _unsupported_enum(f"{path}.status", status, set(MOVE_STATUSES))
        )


def _validate_moves(data: dict[str, Any], entry_outcome: str) -> list[Finding]:
    findings: list[Finding] = []
    moves = data.get("required_judgment_moves")
    if moves is None:
        return [_missing_field("required_judgment_moves")]
    if not isinstance(moves, dict):
        return [_invalid_field("required_judgment_moves", "an object")]
    required = BASE_MOVES + (FULL_MOVES if entry_outcome == "full" else ())
    for move_name in required:
        if move_name not in moves:
            findings.append(
                finding(
                    "block",
                    "missing-judgment-move",
                    f"missing required judgment move: {move_name}",
                    move_name,
                )
            )
        else:
            _validate_move(findings, move_name, moves.get(move_name))
    return findings


def _validate_runtime_decision_ref(
    data: dict[str, Any], entry_outcome: str
) -> list[Finding]:
    findings: list[Finding] = []
    ref = data.get("runtime_decision_ref")
    if ref is None:
        return [_missing_field("runtime_decision_ref")]
    if not isinstance(ref, dict):
        return [_invalid_field("runtime_decision_ref", "an object")]
    for field_name in RUNTIME_REF_FIELDS:
        if field_name not in ref:
            findings.append(_missing_field(f"runtime_decision_ref.{field_name}"))

    if ref.get("schema_version") != FINAL_DECISION_SCHEMA:
        findings.append(
            _invalid_field(
                "runtime_decision_ref.schema_version",
                f"the canonical runtime schema {FINAL_DECISION_SCHEMA}",
            )
        )
    _require_non_empty_string(
        findings,
        ref,
        "artifact_path",
        "runtime_decision_ref.artifact_path",
    )
    artifact_hash = ref.get("artifact_hash")
    if not isinstance(artifact_hash, str) or not SHA256_RE.fullmatch(artifact_hash):
        findings.append(
            _invalid_field(
                "runtime_decision_ref.artifact_hash",
                "a lowercase sha256:<64 hex> digest",
            )
        )

    mode = ref.get("mode")
    if mode not in {"lite", "full"}:
        findings.append(
            _unsupported_enum("runtime_decision_ref.mode", mode, {"lite", "full"})
        )
    elif mode != entry_outcome:
        findings.append(
            finding(
                "block",
                "mode-mismatch",
                "runtime_decision_ref.mode must match entry_outcome",
                "runtime_decision_ref.mode",
            )
        )

    outcome = ref.get("allocation_outcome")
    if outcome not in RECONCILIATION_OUTCOMES:
        findings.append(
            _unsupported_enum(
                "runtime_decision_ref.allocation_outcome",
                outcome,
                set(RECONCILIATION_OUTCOMES),
            )
        )
    finalization = ref.get("finalization_status")
    if finalization not in TERMINAL_STATES:
        findings.append(
            _unsupported_enum(
                "runtime_decision_ref.finalization_status",
                finalization,
                TERMINAL_STATES,
            )
        )
    if outcome in RECONCILIATION_OUTCOMES:
        expected = finalization_status_for_outcome(str(outcome))
        if finalization != expected:
            findings.append(
                finding(
                    "block",
                    "inconsistent-finalization",
                    "runtime_decision_ref.finalization_status must match allocation_outcome",
                    "runtime_decision_ref.finalization_status",
                )
            )

    horizon = ref.get("authorization_horizon")
    allowed_horizons = (
        set(LITE_AUTHORIZATION_HORIZONS)
        if entry_outcome == "lite"
        else set(AUTHORIZATION_HORIZONS)
    )
    if horizon not in allowed_horizons:
        findings.append(
            _unsupported_enum(
                "runtime_decision_ref.authorization_horizon",
                horizon,
                allowed_horizons,
            )
        )
    return findings


def validate_sra_output(data: Any) -> list[Finding]:
    root_findings = require_object(
        data, "SRA method-fidelity output must be an object"
    )
    if root_findings:
        return root_findings
    findings: list[Finding] = []
    if data.get("schema_version") != FIDELITY_SCHEMA:
        findings.append(
            finding(
                "block",
                "invalid-schema-version",
                f"schema_version must be {FIDELITY_SCHEMA}",
            )
        )
    if data.get("method") != METHOD:
        findings.append(
            finding("block", "invalid-method", f"method must be {METHOD}")
        )
    entry_outcome = data.get("entry_outcome")
    if not isinstance(entry_outcome, str):
        findings.append(_invalid_field("entry_outcome", "a string"))
        return findings
    if entry_outcome not in ENTRY_OUTCOMES:
        findings.append(
            _unsupported_enum("entry_outcome", entry_outcome, ENTRY_OUTCOMES)
        )
        return findings
    if entry_outcome in {"direct", "blocked"}:
        findings.extend(_validate_exit(data))
        return findings
    _require_non_empty_string(
        findings,
        data,
        "plain_language_conclusion",
        "plain_language_conclusion",
    )
    findings.extend(_validate_runtime_decision_ref(data, entry_outcome))
    findings.extend(_validate_moves(data, entry_outcome))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate SRA method-fidelity evidence without duplicating the canonical "
            "runtime allocation contract."
        )
    )
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    try:
        data = load_json(path, error_factory=ValueError)
    except ValueError as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 1
    findings = validate_sra_output(data)
    accepted_exit = ""
    if isinstance(data, dict) and data.get("entry_outcome") in {"direct", "blocked"}:
        accepted_exit = str(data.get("entry_outcome"))
    print_shape_report(
        title=REPORT_TITLE,
        path=path,
        findings=findings,
        truth_boundary=(
            "priority quality, semantic ROI, necessity truth, allocation correctness, "
            "or the referenced runtime artifact contents"
        ),
        accepted_exit=accepted_exit,
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
