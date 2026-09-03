#!/usr/bin/env python3
"""Validate SRA fidelity output shape without judging priority correctness."""

from __future__ import annotations

import argparse
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


SCHEMA_VERSION = "sra-fidelity-v0.1"
METHOD = "SRA"
REPORT_TITLE = "SRA Shape & Evidence Risk Report"
ENTRY_OUTCOMES = {"direct", "lite", "full", "blocked"}
LITE_ACTIONS = {"continue", "switch", "maintain", "defer", "stop", "reserve"}
ALLOCATION_OUTCOMES = {"allocate", "conditional", "infeasible", "blocked"}
FULL_ACTIONS = ALLOCATION_OUTCOMES
ALLOCATION_ACTIONS = LITE_ACTIONS | FULL_ACTIONS
AUTHORIZATION_HORIZONS = {"one_action", "one_tranche", "until_named_checkpoint"}
ALLOCATION_SCOPES = {"problem_portfolio", "execution_portfolio"}
BUNDLE_STATUSES = {"feasible", "infeasible", "dominated", "conditional"}
RESERVE_STATUSES = {"reserved", "none"}
FRAME_FIELDS = (
    "parent_objective",
    "target_threshold",
    "time_window",
    "risk_floor",
    "decision_owner",
    "contested_resource",
    "evidence_ceiling",
)
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
LITE_DECISION_FIELDS = (
    "considered_candidates",
    "current_floor",
    "next_tranche",
    "investment_ceiling",
    "authorization_horizon",
    "displaced_work",
    "rerank_trigger",
)
FULL_DECISION_FIELDS = (
    "allocation_outcome",
    "allocation_scope",
    "contested_resources",
    "dominant_constraint",
    "candidate_bundles",
    "contraction_findings",
    "replenishment_findings",
    "selected_main_allocation",
    "necessary_support",
    "minimum_maintenance",
    "explicit_defer",
    "explicit_stop",
    "reserved_capacity",
    "next_tranche",
    "authorization_boundary",
    "decision_lifetime",
    "rerank_triggers",
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
    findings: list[Finding], data: dict[str, Any], field_name: str, path: str
) -> None:
    if field_name not in data:
        findings.append(_missing_field(path))
    elif not non_empty_string(data.get(field_name)):
        findings.append(_invalid_field(path, "a non-empty string"))


def _require_list(
    findings: list[Finding],
    data: dict[str, Any],
    field_name: str,
    path: str,
    *,
    non_empty: bool = False,
) -> None:
    if field_name not in data:
        findings.append(_missing_field(path))
        return
    value = data.get(field_name)
    if not isinstance(value, list):
        findings.append(_invalid_field(path, "a list"))
    elif non_empty and not value:
        findings.append(_invalid_field(path, "a non-empty list"))


def _validate_exit(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    _require_non_empty_string(
        findings, data, "plain_language_conclusion", "plain_language_conclusion"
    )
    _require_non_empty_string(findings, data, "exit_reason", "exit_reason")
    if "transfer_to" in data and not isinstance(data.get("transfer_to"), str):
        findings.append(_invalid_field("transfer_to", "a string"))
    return findings


def _validate_frame(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    frame = data.get("allocation_frame")
    if frame is None:
        return [_missing_field("allocation_frame")]
    if not isinstance(frame, dict):
        return [_invalid_field("allocation_frame", "an object")]
    for field_name in FRAME_FIELDS:
        _require_non_empty_string(
            findings,
            frame,
            field_name,
            f"allocation_frame.{field_name}",
        )
    return findings


def _validate_move(
    findings: list[Finding], move_name: str, move: Any
) -> None:
    if not isinstance(move, dict):
        findings.append(_invalid_field(f"required_judgment_moves.{move_name}", "an object"))
        return
    for field_name in MOVE_FIELDS:
        _require_non_empty_string(
            findings,
            move,
            field_name,
            f"required_judgment_moves.{move_name}.{field_name}",
        )
    status = move.get("status")
    if isinstance(status, str) and status not in MOVE_STATUSES:
        findings.append(
            _unsupported_enum(
                f"required_judgment_moves.{move_name}.status",
                status,
                set(MOVE_STATUSES),
            )
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
            continue
        _validate_move(findings, move_name, moves.get(move_name))
    return findings


def _validate_lite(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    action = data.get("allocation_action")
    if isinstance(action, str) and action not in LITE_ACTIONS:
        findings.append(_unsupported_enum("allocation_action", action, LITE_ACTIONS))

    decision = data.get("lite_decision")
    if decision is None:
        return [_missing_field("lite_decision")]
    if not isinstance(decision, dict):
        return [_invalid_field("lite_decision", "an object")]

    for field_name in LITE_DECISION_FIELDS:
        if field_name not in decision:
            findings.append(_missing_field(f"lite_decision.{field_name}"))
    for field_name in (
        "current_floor",
        "next_tranche",
        "investment_ceiling",
        "rerank_trigger",
    ):
        if field_name in decision and not non_empty_string(decision.get(field_name)):
            findings.append(
                _invalid_field(f"lite_decision.{field_name}", "a non-empty string")
            )

    candidates = decision.get("considered_candidates")
    if "considered_candidates" in decision:
        if not isinstance(candidates, list):
            findings.append(
                _invalid_field("lite_decision.considered_candidates", "a list")
            )
        else:
            if not 2 <= len(candidates) <= 4:
                findings.append(
                    _invalid_field(
                        "lite_decision.considered_candidates",
                        "a list of two to four non-empty strings",
                    )
                )
            for index, candidate in enumerate(candidates):
                if not non_empty_string(candidate):
                    findings.append(
                        _invalid_field(
                            f"lite_decision.considered_candidates[{index}]",
                            "a non-empty string",
                        )
                    )

    horizon = decision.get("authorization_horizon")
    if "authorization_horizon" in decision:
        if not isinstance(horizon, str):
            findings.append(
                _invalid_field("lite_decision.authorization_horizon", "a string")
            )
        elif horizon not in AUTHORIZATION_HORIZONS:
            findings.append(
                _unsupported_enum(
                    "lite_decision.authorization_horizon",
                    horizon,
                    AUTHORIZATION_HORIZONS,
                )
            )

    if "displaced_work" in decision and not isinstance(
        decision.get("displaced_work"), list
    ):
        findings.append(_invalid_field("lite_decision.displaced_work", "a list"))
    return findings


def _validate_reserve(findings: list[Finding], value: Any) -> None:
    if not isinstance(value, dict):
        findings.append(_invalid_field("full_decision.reserved_capacity", "an object"))
        return
    for field_name in ("status", "reason", "release_trigger", "review_time"):
        _require_non_empty_string(
            findings,
            value,
            field_name,
            f"full_decision.reserved_capacity.{field_name}",
        )
    status = value.get("status")
    if isinstance(status, str) and status not in RESERVE_STATUSES:
        findings.append(
            _unsupported_enum(
                "full_decision.reserved_capacity.status", status, RESERVE_STATUSES
            )
        )


def _validate_full(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    action = data.get("allocation_action")
    if isinstance(action, str) and action not in FULL_ACTIONS:
        findings.append(_unsupported_enum("allocation_action", action, FULL_ACTIONS))

    decision = data.get("full_decision")
    if decision is None:
        return [_missing_field("full_decision")]
    if not isinstance(decision, dict):
        return [_invalid_field("full_decision", "an object")]

    for field_name in FULL_DECISION_FIELDS:
        if field_name not in decision:
            findings.append(_missing_field(f"full_decision.{field_name}"))

    outcome = decision.get("allocation_outcome")
    if "allocation_outcome" in decision:
        if not isinstance(outcome, str):
            findings.append(_invalid_field("full_decision.allocation_outcome", "a string"))
        elif outcome not in ALLOCATION_OUTCOMES:
            findings.append(
                _unsupported_enum(
                    "full_decision.allocation_outcome", outcome, ALLOCATION_OUTCOMES
                )
            )
        elif isinstance(action, str) and action in FULL_ACTIONS and action != outcome:
            findings.append(
                finding(
                    "block",
                    "inconsistent-allocation-result",
                    "allocation_action must match full_decision.allocation_outcome",
                    "allocation_action",
                )
            )

    scope = decision.get("allocation_scope")
    if "allocation_scope" in decision:
        if not isinstance(scope, str):
            findings.append(_invalid_field("full_decision.allocation_scope", "a string"))
        elif scope not in ALLOCATION_SCOPES:
            findings.append(
                _unsupported_enum(
                    "full_decision.allocation_scope", scope, ALLOCATION_SCOPES
                )
            )

    for field_name in (
        "dominant_constraint",
        "selected_main_allocation",
        "next_tranche",
        "authorization_boundary",
        "decision_lifetime",
    ):
        if field_name in decision and not non_empty_string(decision.get(field_name)):
            findings.append(
                _invalid_field(f"full_decision.{field_name}", "a non-empty string")
            )

    for field_name in (
        "contested_resources",
        "candidate_bundles",
        "contraction_findings",
        "replenishment_findings",
        "rerank_triggers",
    ):
        _require_list(
            findings,
            decision,
            field_name,
            f"full_decision.{field_name}",
            non_empty=True,
        )

    bundles = decision.get("candidate_bundles")
    if isinstance(bundles, list):
        for index, bundle in enumerate(bundles):
            path = f"full_decision.candidate_bundles[{index}]"
            if not isinstance(bundle, dict):
                findings.append(_invalid_field(path, "an object"))
                continue
            _require_non_empty_string(findings, bundle, "bundle_id", f"{path}.bundle_id")
            status = bundle.get("status")
            if "status" not in bundle:
                findings.append(_missing_field(f"{path}.status"))
            elif not isinstance(status, str):
                findings.append(_invalid_field(f"{path}.status", "a string"))
            elif status not in BUNDLE_STATUSES:
                findings.append(
                    _unsupported_enum(f"{path}.status", status, BUNDLE_STATUSES)
                )

    for field_name in (
        "necessary_support",
        "minimum_maintenance",
        "explicit_defer",
        "explicit_stop",
    ):
        _require_list(
            findings,
            decision,
            field_name,
            f"full_decision.{field_name}",
        )

    if "reserved_capacity" in decision:
        _validate_reserve(findings, decision.get("reserved_capacity"))
    return findings


def validate_sra_output(data: Any) -> list[Finding]:
    root_findings = require_object(data, "SRA fidelity output must be an object")
    if root_findings:
        return root_findings

    findings: list[Finding] = []
    if data.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            finding(
                "block",
                "invalid-schema-version",
                f"schema_version must be {SCHEMA_VERSION}",
            )
        )
    if data.get("method") != METHOD:
        findings.append(finding("block", "invalid-method", f"method must be {METHOD}"))

    entry_outcome = data.get("entry_outcome")
    if not isinstance(entry_outcome, str):
        findings.append(_invalid_field("entry_outcome", "a string"))
        return findings
    if entry_outcome not in ENTRY_OUTCOMES:
        findings.append(_unsupported_enum("entry_outcome", entry_outcome, ENTRY_OUTCOMES))
        return findings

    if entry_outcome in {"direct", "blocked"}:
        findings.extend(_validate_exit(data))
        return findings

    _require_non_empty_string(
        findings, data, "plain_language_conclusion", "plain_language_conclusion"
    )
    action = data.get("allocation_action")
    if not isinstance(action, str):
        findings.append(_invalid_field("allocation_action", "a string"))
    elif action not in ALLOCATION_ACTIONS:
        findings.append(
            _unsupported_enum("allocation_action", action, ALLOCATION_ACTIONS)
        )

    findings.extend(_validate_frame(data))
    findings.extend(_validate_moves(data, entry_outcome))
    if entry_outcome == "lite":
        findings.extend(_validate_lite(data))
    else:
        findings.extend(_validate_full(data))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate SRA fidelity output shape without judging priority correctness."
    )
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = load_json(path)
    findings = validate_sra_output(data)
    accepted_exit = ""
    if isinstance(data, dict) and data.get("entry_outcome") in {"direct", "blocked"}:
        accepted_exit = str(data.get("entry_outcome"))
    print_shape_report(
        title=REPORT_TITLE,
        path=path,
        findings=findings,
        truth_boundary="priority quality, semantic ROI, necessity truth, or allocation correctness",
        accepted_exit=accepted_exit,
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
