"""Shared shape engine for Method Fidelity Harness validators.

The Shape & Evidence Risk Report exposes review risks and does not validate semantic truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


APPLICABILITY = {"applicable", "not_applicable", "transfer", "challenge_premise"}
MOVE_STATUSES = {"addressed", "not_applicable", "transfer", "challenge_premise"}
MOVE_FIELDS = (
    "status",
    "finding",
    "failure_criteria_response",
    "evidence_surface",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    judgment_move: str = ""


@dataclass(frozen=True)
class FidelitySpec:
    schema_version: str
    method: str
    report_title: str
    required_moves: tuple[str, ...]
    action_postures: frozenset[str]
    truth_boundary: str = "semantic truth"


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finding(severity: str, code: str, message: str, judgment_move: str = "") -> Finding:
    return Finding(severity, code, message, judgment_move)


def _validate_exit(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for field in ("plain_language_conclusion", "exit_reason"):
        if not non_empty_string(data.get(field)):
            findings.append(_finding("block", "missing-field", f"missing field: {field}"))
    if "transfer_to" in data and not isinstance(data["transfer_to"], str):
        findings.append(_finding("risk", "invalid-field", "transfer_to must be a string"))
    return findings


def _validate_applicable(data: dict[str, Any], spec: FidelitySpec) -> list[Finding]:
    findings: list[Finding] = []
    for field in ("plain_language_conclusion", "action_posture", "required_judgment_moves"):
        if field not in data:
            findings.append(_finding("block", "missing-field", f"missing field: {field}"))

    posture = data.get("action_posture")
    if isinstance(posture, str):
        if posture not in spec.action_postures:
            allowed = ", ".join(sorted(spec.action_postures))
            findings.append(
                _finding(
                    "block",
                    "unsupported-enum",
                    f"action_posture unsupported: {posture!r}; expected one of: {allowed}",
                )
            )
    elif "action_posture" in data:
        findings.append(_finding("block", "invalid-field", "action_posture must be a string"))

    moves = data.get("required_judgment_moves")
    if not isinstance(moves, dict):
        if "required_judgment_moves" in data:
            findings.append(_finding("block", "invalid-field", "required_judgment_moves must be an object"))
        return findings

    for move_name in spec.required_moves:
        move = moves.get(move_name)
        if move is None:
            findings.append(
                _finding(
                    "block",
                    "missing-judgment-move",
                    f"missing required judgment move: {move_name}",
                    move_name,
                )
            )
            continue
        if not isinstance(move, dict):
            findings.append(_finding("block", "invalid-move", f"{move_name} must be an object", move_name))
            continue
        for field in MOVE_FIELDS:
            value = move.get(field)
            if not non_empty_string(value):
                findings.append(
                    _finding("block", "empty-move-field", f"{move_name}.{field} is empty", move_name)
                )
        status = move.get("status")
        if isinstance(status, str) and status not in MOVE_STATUSES:
            allowed = ", ".join(sorted(MOVE_STATUSES))
            findings.append(
                _finding(
                    "block",
                    "unsupported-enum",
                    f"{move_name}.status unsupported: {status!r}; expected one of: {allowed}",
                    move_name,
                )
            )
    return findings


def validate_fidelity_output(data: Any, spec: FidelitySpec) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(data, dict):
        return [_finding("block", "invalid-root", f"{spec.method} fidelity output must be an object")]

    if data.get("schema_version") != spec.schema_version:
        findings.append(_finding("block", "invalid-schema-version", f"schema_version must be {spec.schema_version}"))
    if data.get("method") != spec.method:
        findings.append(_finding("block", "invalid-method", f"method must be {spec.method}"))

    applicability = data.get("applicability")
    if applicability not in APPLICABILITY:
        allowed = ", ".join(sorted(APPLICABILITY))
        findings.append(
            _finding(
                "block",
                "unsupported-enum",
                f"applicability unsupported: {applicability!r}; expected one of: {allowed}",
            )
        )
        return findings

    if applicability == "applicable":
        findings.extend(_validate_applicable(data, spec))
    else:
        findings.extend(_validate_exit(data))
    return findings


def print_text_report(path: Path, data: Any, findings: list[Finding], spec: FidelitySpec) -> None:
    print(spec.report_title)
    print(f"Path: {path}")
    print()
    if isinstance(data, dict) and data.get("applicability") in {"not_applicable", "transfer", "challenge_premise"}:
        print(f"method exit accepted: {data.get('applicability')}")
        print()

    if not findings:
        print("No shape or evidence risks detected.")
    else:
        for finding in findings:
            move = f" [{finding.judgment_move}]" if finding.judgment_move else ""
            print(f"- {finding.severity.upper()} [{finding.code}]{move}: {finding.message}")

    print()
    print(f"Reminder: agentic audit remains required; this report does not validate {spec.truth_boundary}.")
