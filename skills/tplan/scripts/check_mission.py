#!/usr/bin/env python3
"""Validate a tplan Mission runtime state.

This checks runtime shape and reports historical reference/closure inconsistencies.
It does not judge Mission value or semantic correctness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tplan_runtime import (
    TplanError,
    _mission_completion_findings,
    _validate_trace_evidence_references,
    read_mission,
    read_outcome_attribution_snapshot,
    runtime_provenance_report,
    validate_execution_trace,
    validate_mission,
    validate_mission_directory_identity,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a tplan Mission runtime state.")
    parser.add_argument("mission_dir", help="Mission directory containing mission.json.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mission_dir = Path(args.mission_dir)
    runtime_report = None
    integrity_warnings = []
    try:
        read_mission(mission_dir)  # Preserve the check command's pending-recovery behavior.
        snapshot = read_outcome_attribution_snapshot(mission_dir)
        mission, trace, events = snapshot["mission"], snapshot["trace"], snapshot["events"]
        errors = validate_mission(mission)
        errors.extend(validate_mission_directory_identity(mission, mission_dir))
        errors.extend(validate_execution_trace(mission, trace))
        if not errors:
            integrity_warnings.extend(_validate_trace_evidence_references(trace, events))
            if mission["mission"]["status"] == "completed":
                integrity_warnings.extend(_mission_completion_findings(mission, events))
        runtime_report = runtime_provenance_report(mission)
        if runtime_report["severity"] == "error":
            errors.extend(
                f"{item['code']}: {item['message']}"
                for item in runtime_report["diagnostics"]
            )
    except (OSError, json.JSONDecodeError, TplanError) as exc:
        errors = [str(exc)]

    if errors:
        print("mission_check: failed")
        for error in errors:
            print(f"- {error}")
        print("script_result: runtime shape issues found; agentic judgment is still required after remediation")
        return 1

    print("mission_check: ok")
    for warning in integrity_warnings:
        print(f"integrity_warning: {warning}")
    if runtime_report is not None and runtime_report["severity"] == "warning":
        for item in runtime_report["diagnostics"]:
            print(f"runtime_warning: {item['code']}: {item['message']}")
    print("script_result: no runtime schema violations detected; agentic judgment is still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
