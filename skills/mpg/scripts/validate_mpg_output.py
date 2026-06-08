#!/usr/bin/env python3
"""Validate MPG fidelity output shape.

This script checks required path-carrying judgment moves. It does not decide whether
the mainline or action posture is semantically correct.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mpg-fidelity-v0.1"
METHOD_NAME = "MPG"

APPLICABILITY = {"applicable", "not_applicable", "transfer", "challenge_premise"}
MOVE_STATUSES = {"addressed", "not_applicable", "transfer", "challenge_premise"}
ACTION_POSTURES = {
    "commit",
    "stage",
    "hedge",
    "wait",
    "switch_vehicle",
    "probe",
    "hold",
    "exit",
    "transfer",
    "unclear",
}

REQUIRED_MOVES = (
    "qualified_mainline",
    "carrier_vehicle_separation",
    "counter_force_map",
    "exposure_budget",
    "optionality_design",
    "trigger_conditions",
    "mainline_challenge",
    "aqm_boundary",
)

MOVE_FIELDS = (
    "status",
    "finding",
    "failure_criteria_response",
    "evidence_surface",
)


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    judgment_move: str = ""


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_exit(data: dict[str, Any], findings: list[Finding]) -> None:
    for field in ("plain_language_conclusion", "exit_reason"):
        if not non_empty_string(data.get(field)):
            findings.append(Finding("block", "missing-field", f"missing field: {field}"))
    if "transfer_to" in data and not isinstance(data["transfer_to"], str):
        findings.append(Finding("risk", "invalid-field", "transfer_to must be a string"))


def validate_applicable(data: dict[str, Any], findings: list[Finding]) -> None:
    for field in ("plain_language_conclusion", "action_posture", "required_judgment_moves"):
        if field not in data:
            findings.append(Finding("block", "missing-field", f"missing field: {field}"))

    posture = data.get("action_posture")
    if isinstance(posture, str):
        if posture not in ACTION_POSTURES:
            allowed = ", ".join(sorted(ACTION_POSTURES))
            findings.append(
                Finding(
                    "block",
                    "unsupported-enum",
                    f"action_posture unsupported: {posture!r}; expected one of: {allowed}",
                )
            )
    elif "action_posture" in data:
        findings.append(Finding("block", "invalid-field", "action_posture must be a string"))

    moves = data.get("required_judgment_moves")
    if not isinstance(moves, dict):
        if "required_judgment_moves" in data:
            findings.append(Finding("block", "invalid-field", "required_judgment_moves must be an object"))
        return

    for move_name in REQUIRED_MOVES:
        move = moves.get(move_name)
        if move is None:
            findings.append(
                Finding(
                    "block",
                    "missing-judgment-move",
                    f"missing required judgment move: {move_name}",
                    move_name,
                )
            )
            continue
        if not isinstance(move, dict):
            findings.append(Finding("block", "invalid-move", f"{move_name} must be an object", move_name))
            continue
        for field in MOVE_FIELDS:
            value = move.get(field)
            if not non_empty_string(value):
                findings.append(
                    Finding("block", "empty-move-field", f"{move_name}.{field} is empty", move_name)
                )
        status = move.get("status")
        if isinstance(status, str) and status not in MOVE_STATUSES:
            allowed = ", ".join(sorted(MOVE_STATUSES))
            findings.append(
                Finding(
                    "block",
                    "unsupported-enum",
                    f"{move_name}.status unsupported: {status!r}; expected one of: {allowed}",
                    move_name,
                )
            )


def validate(data: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(data, dict):
        return [Finding("block", "invalid-root", "MPG fidelity output must be an object")]
    if data.get("schema_version") != SCHEMA_VERSION:
        findings.append(Finding("block", "invalid-schema-version", f"schema_version must be {SCHEMA_VERSION}"))
    if data.get("method") != METHOD_NAME:
        findings.append(Finding("block", "invalid-method", f"method must be {METHOD_NAME}"))

    applicability = data.get("applicability")
    if applicability not in APPLICABILITY:
        allowed = ", ".join(sorted(APPLICABILITY))
        findings.append(
            Finding("block", "unsupported-enum", f"applicability unsupported: {applicability!r}; expected one of: {allowed}")
        )
        return findings

    if applicability == "applicable":
        validate_applicable(data, findings)
    else:
        validate_exit(data, findings)
    return findings


def print_report(path: Path, data: Any, findings: list[Finding]) -> None:
    print("MPG Shape & Evidence Risk Report")
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
    print("Reminder: agentic audit remains required; this report does not validate mainline truth.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MPG fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = validate(data)
    print_report(path, data, findings)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
