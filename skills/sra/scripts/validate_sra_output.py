#!/usr/bin/env python3
"""Validate SRA fidelity output shape and canonical sequence markers.

The validator checks structure only. It cannot decide whether a target is correct,
a bundle is truly feasible, or an allocation has the highest semantic value.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


THIS_FILE = Path(__file__).resolve()
sys.path.insert(0, str(THIS_FILE.parents[2]))

from runtime_bootstrap import activate_runtime

activate_runtime(THIS_FILE)

from _runtime.core.io import load_json
from _runtime.core.report import Finding, finding
from _runtime.core.shape import non_empty_string
from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output


SPEC = FidelitySpec(
    schema_version="sra-fidelity-v0.1",
    method="SRA",
    report_title="SRA Shape & Evidence Risk Report",
    required_moves=(
        "allocation_frame",
        "candidate_horizon",
        "bundle_hypotheses",
        "contraction",
        "floor_bundle_selection",
        "replenishment",
        "allocation_lanes",
        "authorization_and_rerank",
        "evidence_boundary",
    ),
    action_postures=frozenset(
        {
            "allocate",
            "conditional",
            "infeasible",
            "blocked",
            "unclear",
        }
    ),
    truth_boundary="allocation semantic truth",
)

_OUTCOMES = {"allocate", "conditional", "infeasible", "blocked"}
_REPLENISHMENT_STATUSES = {"selected", "conditional", "not_available"}
_LANE_FIELDS = (
    "main_allocation",
    "necessary_support",
    "maintenance",
    "reserve",
    "defer",
    "stop",
)
_FRAME_TEXT_FIELDS = (
    "parent_objective",
    "target_threshold",
    "time_window",
    "risk_floor",
    "decision_owner",
)
_CANDIDATE_TEXT_FIELDS = (
    "candidate_id",
    "objective_contribution",
)


def _require_non_empty_text(
    findings: list[Finding],
    data: dict[str, Any],
    field: str,
    *,
    subject: str,
) -> None:
    if not non_empty_string(data.get(field)):
        findings.append(
            finding(
                "block",
                "missing-or-empty-field",
                f"{subject}.{field} must be a non-empty string",
                subject,
            )
        )


def _require_list(
    findings: list[Finding],
    data: dict[str, Any],
    field: str,
    *,
    subject: str,
    non_empty: bool = False,
) -> list[Any] | None:
    value = data.get(field)
    if not isinstance(value, list):
        findings.append(
            finding(
                "block",
                "invalid-field",
                f"{subject}.{field} must be a list",
                subject,
            )
        )
        return None
    if non_empty and not value:
        findings.append(
            finding(
                "block",
                "empty-field",
                f"{subject}.{field} must not be empty",
                subject,
            )
        )
    return value


def _validate_allocation_frame(trace: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    frame = trace.get("allocation_frame")
    if not isinstance(frame, dict):
        return [
            finding(
                "block",
                "missing-allocation-frame",
                "allocation_trace.allocation_frame must be an object",
                "allocation_frame",
            )
        ]

    for field in _FRAME_TEXT_FIELDS:
        _require_non_empty_text(findings, frame, field, subject="allocation_frame")
    _require_list(
        findings,
        frame,
        "contested_resources",
        subject="allocation_frame",
        non_empty=True,
    )
    return findings


def _validate_candidate_horizon(trace: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    candidates = _require_list(
        findings,
        trace,
        "candidate_horizon",
        subject="allocation_trace",
        non_empty=True,
    )
    if candidates is None:
        return findings
    if len(candidates) < 2:
        findings.append(
            finding(
                "block",
                "insufficient-candidate-horizon",
                "allocation_trace.candidate_horizon must contain at least two competing candidates or postures",
                "candidate_horizon",
            )
        )

    candidate_ids: set[str] = set()
    for index, candidate in enumerate(candidates):
        subject = f"candidate_horizon[{index}]"
        if not isinstance(candidate, dict):
            findings.append(
                finding(
                    "block",
                    "invalid-candidate",
                    f"{subject} must be an object",
                    "candidate_horizon",
                )
            )
            continue
        for field in _CANDIDATE_TEXT_FIELDS:
            _require_non_empty_text(findings, candidate, field, subject=subject)
        resource_vector = candidate.get("resource_demand_vector")
        if not isinstance(resource_vector, dict) or not resource_vector:
            findings.append(
                finding(
                    "block",
                    "invalid-resource-vector",
                    f"{subject}.resource_demand_vector must be a non-empty object",
                    "candidate_horizon",
                )
            )
        candidate_id = candidate.get("candidate_id")
        if non_empty_string(candidate_id):
            if candidate_id in candidate_ids:
                findings.append(
                    finding(
                        "block",
                        "duplicate-candidate-id",
                        f"duplicate candidate_id: {candidate_id}",
                        "candidate_horizon",
                    )
                )
            candidate_ids.add(candidate_id)
    return findings


def _validate_bundle_hypotheses(trace: dict[str, Any], outcome: str) -> list[Finding]:
    findings: list[Finding] = []
    hypotheses = _require_list(
        findings,
        trace,
        "bundle_hypotheses",
        subject="allocation_trace",
        non_empty=outcome != "blocked",
    )
    if hypotheses is None:
        return findings

    for index, bundle in enumerate(hypotheses):
        subject = f"bundle_hypotheses[{index}]"
        if not isinstance(bundle, dict):
            findings.append(
                finding(
                    "block",
                    "invalid-bundle-hypothesis",
                    f"{subject} must be an object",
                    "bundle_hypotheses",
                )
            )
            continue
        for field in ("bundle_id", "target_reaching_basis"):
            _require_non_empty_text(findings, bundle, field, subject=subject)
        _require_list(findings, bundle, "components", subject=subject, non_empty=True)
        label = bundle.get("label")
        if isinstance(label, str) and "minimum" in label.lower():
            findings.append(
                finding(
                    "block",
                    "predeclared-minimum-bundle",
                    f"{subject}.label must not declare a minimum before contraction",
                    "bundle_hypotheses",
                )
            )
    return findings


def _validate_contraction(trace: dict[str, Any], outcome: str) -> list[Finding]:
    findings: list[Finding] = []
    contraction = trace.get("contraction")
    if not isinstance(contraction, dict):
        return [
            finding(
                "block",
                "missing-contraction",
                "allocation_trace.contraction must be an object; every applicable SRA run executes contraction",
                "contraction",
            )
        ]

    if contraction.get("target_held_constant") is not True:
        findings.append(
            finding(
                "block",
                "target-not-held-constant",
                "contraction.target_held_constant must be true",
                "contraction",
            )
        )
    if contraction.get("floor_bundle_basis") != "post_contraction":
        findings.append(
            finding(
                "block",
                "invalid-floor-bundle-basis",
                "contraction.floor_bundle_basis must be 'post_contraction'; minimum cannot be declared before contraction",
                "contraction",
            )
        )

    _require_list(
        findings,
        contraction,
        "tested_changes",
        subject="contraction",
        non_empty=outcome != "blocked",
    )
    floor_bundle = _require_list(
        findings,
        contraction,
        "floor_bundle",
        subject="contraction",
        non_empty=outcome in {"allocate", "conditional"},
    )

    if outcome in {"allocate", "conditional"}:
        _require_non_empty_text(findings, contraction, "first_break_point", subject="contraction")
    elif outcome == "infeasible":
        if floor_bundle:
            findings.append(
                finding(
                    "block",
                    "infeasible-with-floor-bundle",
                    "an infeasible outcome must not retain a non-empty contraction.floor_bundle",
                    "contraction",
                )
            )
        _require_non_empty_text(findings, contraction, "infeasibility_reason", subject="contraction")
    return findings


def _validate_qualification(trace: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    selection = trace.get("qualification_and_selection")
    if not isinstance(selection, dict):
        return [
            finding(
                "block",
                "missing-qualification-selection",
                "allocation_trace.qualification_and_selection must be an object",
                "qualification_and_selection",
            )
        ]
    for field in ("qualification_result", "selection_reason"):
        _require_non_empty_text(findings, selection, field, subject="qualification_and_selection")
    return findings


def _validate_replenishment(trace: dict[str, Any], outcome: str) -> list[Finding]:
    findings: list[Finding] = []
    replenishment = trace.get("replenishment")
    if not isinstance(replenishment, dict):
        return [
            finding(
                "block",
                "missing-replenishment",
                "allocation_trace.replenishment must be an object; every applicable SRA run records a replenishment result",
                "replenishment",
            )
        ]

    status = replenishment.get("status")
    if status not in _REPLENISHMENT_STATUSES:
        findings.append(
            finding(
                "block",
                "unsupported-enum",
                "replenishment.status must be 'selected', 'conditional', or 'not_available'",
                "replenishment",
            )
        )
    expected_statuses = {
        "allocate": {"selected"},
        "conditional": {"conditional", "selected"},
        "infeasible": {"not_available"},
        "blocked": {"not_available", "conditional"},
    }
    if status in _REPLENISHMENT_STATUSES and status not in expected_statuses[outcome]:
        findings.append(
            finding(
                "block",
                "outcome-replenishment-mismatch",
                f"replenishment.status {status!r} is inconsistent with outcome {outcome!r}",
                "replenishment",
            )
        )

    _require_list(
        findings,
        replenishment,
        "options_considered",
        subject="replenishment",
        non_empty=outcome in {"allocate", "conditional"},
    )
    for field in ("selected_next_tranche", "selection_reason"):
        _require_non_empty_text(findings, replenishment, field, subject="replenishment")
    return findings


def _validate_allocation_lanes(trace: dict[str, Any], outcome: str) -> list[Finding]:
    findings: list[Finding] = []
    lanes = trace.get("allocation_lanes")
    if not isinstance(lanes, dict):
        return [
            finding(
                "block",
                "missing-allocation-lanes",
                "allocation_trace.allocation_lanes must be an object",
                "allocation_lanes",
            )
        ]

    lane_values: dict[str, list[Any] | None] = {}
    for field in _LANE_FIELDS:
        lane_values[field] = _require_list(
            findings,
            lanes,
            field,
            subject="allocation_lanes",
        )
    if outcome in {"allocate", "conditional"} and lane_values.get("main_allocation") == []:
        findings.append(
            finding(
                "block",
                "empty-main-allocation",
                "allocation_lanes.main_allocation must not be empty for allocate or conditional outcomes",
                "allocation_lanes",
            )
        )
    return findings


def _validate_authorization(trace: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for field in ("investment_ceiling", "authorization_horizon", "evidence_ceiling"):
        _require_non_empty_text(findings, trace, field, subject="allocation_trace")
    _require_list(
        findings,
        trace,
        "reranking_triggers",
        subject="allocation_trace",
        non_empty=True,
    )
    return findings


def _validate_allocation_trace(data: Any) -> list[Finding]:
    if not isinstance(data, dict) or data.get("applicability") != "applicable":
        return []

    trace = data.get("allocation_trace")
    if not isinstance(trace, dict):
        return [
            finding(
                "block",
                "missing-allocation-trace",
                "allocation_trace is required for an applicable SRA run",
                "allocation_trace",
            )
        ]

    findings: list[Finding] = []
    outcome = trace.get("outcome")
    if outcome not in _OUTCOMES:
        findings.append(
            finding(
                "block",
                "unsupported-enum",
                "allocation_trace.outcome must be allocate, conditional, infeasible, or blocked",
                "allocation_trace",
            )
        )
        return findings

    if data.get("action_posture") != outcome:
        findings.append(
            finding(
                "block",
                "outcome-posture-mismatch",
                "action_posture must match allocation_trace.outcome",
                "allocation_trace",
            )
        )

    findings.extend(_validate_allocation_frame(trace))
    findings.extend(_validate_candidate_horizon(trace))
    findings.extend(_validate_bundle_hypotheses(trace, outcome))
    findings.extend(_validate_contraction(trace, outcome))
    findings.extend(_validate_qualification(trace))
    findings.extend(_validate_replenishment(trace, outcome))
    findings.extend(_validate_allocation_lanes(trace, outcome))
    findings.extend(_validate_authorization(trace))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SRA fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = load_json(path)
    findings = validate_fidelity_output(data, SPEC)
    findings.extend(_validate_allocation_trace(data))
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
