#!/usr/bin/env python3
"""Deterministic A/B simulation for tplan continuation authorization."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCENARIO = {
    "mission": "Validate a late PhaseX rerun before spending another expensive same-path generation pass.",
    "late_defect": (
        "Near the end of the run, red-team evidence still contains placeholder/sample anchors, "
        "so the evidence shape must be classified before another broad rerun is trusted."
    ),
    "candidate_expensive_action": "continue_same_path",
    "authorized_recovery_action": "targeted_fix",
}


def script_path(source_root: Path, name: str) -> Path:
    return source_root / "skills" / "tplan" / "scripts" / name


def run_step(name: str, args: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    return {
        "name": name,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_events(mission_dir: Path) -> list[dict[str, Any]]:
    path = mission_dir / "evidence.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def continuation_authorization_surface(source_root: Path) -> bool:
    runtime = script_path(source_root, "tplan_runtime.py")
    if not runtime.exists():
        return False
    text = runtime.read_text(encoding="utf-8")
    return (
        "CONTINUATION_AUTHORIZATION_FIELDS" in text
        and "_validate_continuation_authorization" in text
        and "continuation_authorization" in text
    )


def authorization_latency(blocked: bool, final_allowed_action: str) -> dict[str, Any]:
    return {
        "loop_model": (
            "continuation_authorization_blocks_ungated_same_path"
            if blocked
            else "pre_authorization_plain_same_path_continuation"
        ),
        "expensive_same_path_continue_attempts_before_gate": 0 if blocked else 1,
        "steps_until_first_authorization_gate": 1 if blocked else 2,
        "invalid_evidence_claims": 0,
        "blocked_action": "expensive_same_path_continue" if blocked else None,
        "final_allowed_action": final_allowed_action,
        "events": [
            {
                "step": 1,
                "candidate_action": "expensive_same_path_continue",
                "runtime_gate": "continuation_authorization_required" if blocked else "none",
                "allowed": not blocked,
                "reason": (
                    "The new runtime rejects the expensive same-path continuation until the "
                    "late evidence-shape defect is classified."
                    if blocked
                    else "The old runtime has no continuation authorization field, so the same "
                    "Mission-facing continue payload can be applied."
                ),
            },
            {
                "step": 1 if blocked else 2,
                "candidate_action": final_allowed_action,
                "runtime_gate": "continuation_authorization.authorized_action" if blocked else "plain_judgment",
                "allowed": True,
                "reason": (
                    "The explicit authorization record allows a targeted fix instead of blind rerun."
                    if blocked
                    else "Plain judgment may eventually redirect, but only after the ungated continuation candidate."
                ),
            },
        ],
    }


def create_tasks_file(output_dir: Path) -> Path:
    tasks_path = output_dir / "tasks.json"
    write_json(
        tasks_path,
        [
            {
                "id": "T1",
                "title": "Validate PhaseX evidence shape before another large rerun",
                "role": "success-critical",
                "mission_contribution": (
                    "Prevents placeholder/sample evidence from authorizing another expensive same-path rerun."
                ),
                "acceptance_evidence": ["A1", "A2", "A3", "A4"],
            }
        ],
    )
    return tasks_path


def base_continue_decision() -> dict[str, Any]:
    return {
        "recommendation": "continue",
        "rationale": (
            "Continue the PhaseX same-path validation work after late placeholder/sample "
            "red-team anchor defects were discovered."
        ),
        "confidence": 70,
        "evidence_links": [],
        "proposed_mutations": [],
        "requires_human": False,
        "mission_alignment": (
            "Another broad PhaseX continuation could address A1-A4, but late placeholder/sample "
            "anchors make the expected evidence delta uncertain."
        ),
        "path_assessment": {
            "marginal_roi": "weak",
            "path_role": "one_of_many",
            "evidence_delta": "unclear",
        },
    }


def continuation_authorization() -> dict[str, Any]:
    return {
        "trigger_reasons": ["second_large_rerun", "post_generation_defect"],
        "evidence_shape_lint": "fail",
        "defect_classification": "acceptance_blocking",
        "expected_evidence_delta": "new_evidence_expected",
        "authorized_action": "targeted_fix",
    }


def authorized_continue_decision() -> dict[str, Any]:
    decision = base_continue_decision()
    decision["continuation_authorization"] = continuation_authorization()
    return decision


def invalid_authorization_decision() -> dict[str, Any]:
    decision = authorized_continue_decision()
    decision["continuation_authorization"]["defect_classification"] = "minor_bug"
    return decision


def invalid_source_report(source_root: Path, output_dir: Path, missing: list[str]) -> dict[str, Any]:
    report = {
        "scenario": SCENARIO,
        "source_root": str(source_root),
        "runtime_profile": "invalid_continuation_authorization_source",
        "ungated_continue_allowed": False,
        "mechanical_score": 0,
        "limitations": [f"missing script: {name}" for name in missing],
    }
    write_json(output_dir / "simulation_result.json", report)
    return report


def run_report(source_root: Path, output_dir: Path) -> dict[str, Any]:
    scripts = {
        name: script_path(source_root, name)
        for name in (
            "init_mission.py",
            "apply_decision.py",
            "check_mission.py",
        )
    }
    missing = [name for name, path in scripts.items() if not path.exists()]
    if missing:
        return invalid_source_report(source_root, output_dir, missing)

    mission_dir = output_dir / "mission"
    tasks_path = create_tasks_file(output_dir)
    steps: dict[str, dict[str, Any]] = {}

    def run(name: str, args: list[str]) -> None:
        steps[name] = run_step(name, args, source_root)

    run(
        "init_mission",
        [
            sys.executable,
            str(scripts["init_mission.py"]),
            "--dir",
            str(mission_dir),
            "--mission-id",
            "phasex-continuation-authorization",
            "--title",
            "PhaseX continuation authorization decision",
            "--objective",
            "Decide whether another expensive PhaseX same-path continuation is authorized after late evidence-shape defects.",
            "--acceptance-evidence",
            "A1:Late placeholder/sample evidence anchors are detected before rerun.",
            "--acceptance-evidence",
            "A2:The defect is classified as acceptance-blocking, batchable detail, or non-blocking.",
            "--acceptance-evidence",
            "A3:The next action is justified by expected evidence delta, not sunk cost.",
            "--acceptance-evidence",
            "A4:An expensive same-path continuation is not applied without explicit authorization.",
            "--task-json",
            str(tasks_path),
            "--human-in-loop",
            "0",
            "--risk-tolerance",
            "45",
            "--resource-sufficiency",
            "35",
        ],
    )

    missing_auth_decision = output_dir / "decision_missing_continuation_authorization.json"
    write_json(missing_auth_decision, base_continue_decision())
    run(
        "apply_missing_continuation_authorization",
        [
            sys.executable,
            str(scripts["apply_decision.py"]),
            str(mission_dir),
            "--decision",
            str(missing_auth_decision),
        ],
    )

    surface_exists = continuation_authorization_surface(source_root)
    missing_blocked = (
        steps["apply_missing_continuation_authorization"]["returncode"] != 0
        and steps["apply_missing_continuation_authorization"]["stderr"]
        == "decision missing field: continuation_authorization"
    )
    ungated_allowed = steps["apply_missing_continuation_authorization"]["returncode"] == 0

    runtime_profile = (
        "continuation_authorization" if surface_exists else "pre_continuation_authorization"
    )
    final_allowed_action = "continue_same_path"
    authorization = None

    if surface_exists:
        valid_decision = output_dir / "decision_with_continuation_authorization.json"
        authorization = continuation_authorization()
        write_json(valid_decision, authorized_continue_decision())
        run(
            "apply_valid_continuation_authorization",
            [
                sys.executable,
                str(scripts["apply_decision.py"]),
                str(mission_dir),
                "--decision",
                str(valid_decision),
            ],
        )

        invalid_decision = output_dir / "decision_with_invalid_continuation_authorization.json"
        write_json(invalid_decision, invalid_authorization_decision())
        run(
            "apply_invalid_continuation_authorization",
            [
                sys.executable,
                str(scripts["apply_decision.py"]),
                str(mission_dir),
                "--decision",
                str(invalid_decision),
            ],
        )
        final_allowed_action = authorization["authorized_action"]

    run("check_mission", [sys.executable, str(scripts["check_mission.py"]), str(mission_dir)])

    events = read_events(mission_dir)
    event_types = [event.get("event_type") for event in events]
    valid_allowed = (
        surface_exists
        and steps.get("apply_valid_continuation_authorization", {}).get("returncode") == 0
    )
    invalid_enum_blocked = (
        surface_exists
        and steps.get("apply_invalid_continuation_authorization", {}).get("returncode") != 0
        and steps.get("apply_invalid_continuation_authorization", {})
        .get("stderr", "")
        .startswith("continuation_authorization defect_classification unsupported")
    )
    runtime_text = script_path(source_root, "tplan_runtime.py").read_text(encoding="utf-8")
    enum_surface = all(
        phrase in runtime_text
        for phrase in ("evidence_shape_lint", "defect_classification", "authorized_action")
    )
    mechanical_checks = [
        surface_exists,
        missing_blocked,
        valid_allowed,
        invalid_enum_blocked,
        "decision_applied" in event_types,
        authorization is not None and authorization["authorized_action"] == "targeted_fix",
    ]

    report = {
        "scenario": SCENARIO,
        "source_root": str(source_root),
        "runtime_profile": runtime_profile,
        "ungated_continue_allowed": ungated_allowed,
        "mechanical_score": sum(1 for item in mechanical_checks if item) if surface_exists else 0,
        "enum_surface_present": enum_surface,
        "continuation_authorization": authorization,
        "authorization_latency": authorization_latency(missing_blocked, final_allowed_action),
        "event_types": event_types,
        "steps": steps,
        "limitations": []
        if surface_exists
        else [
            "continuation_authorization field unavailable",
            "evidence_shape_lint unavailable",
            "defect_classification unavailable",
            "authorized_action unavailable",
        ],
    }
    write_json(output_dir / "simulation_result.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run continuation authorization A/B simulation.")
    parser.add_argument("--source-root", required=True, help="Repository/source snapshot root.")
    parser.add_argument("--output-dir", required=True, help="Directory for simulation artifacts.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report = run_report(source_root, output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
