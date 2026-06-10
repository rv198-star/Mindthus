#!/usr/bin/env python3
"""Deterministic agent-decision simulation for tplan shared risk context."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCENARIO = {
    "mission": "Run post-merge full-chain validation and decide whether the repository is safe to hand off.",
    "failure": (
        "Full-chain validation failed late with ENOSPC during artifact write, "
        "sqlite disk I/O error while persisting evidence, and an fsync warning."
    ),
    "next_gate": "health_check",
}


def pre_shared_risk_stop_latency() -> dict[str, Any]:
    """Model same-path continuation before a runtime risk gate exists."""
    return {
        "loop_model": "same_path_continuation_until_plain_judgment_gate",
        "expensive_rerun_attempts_before_gate": 1,
        "steps_until_first_safe_gate": 2,
        "steps_until_stop_or_escalation": 2,
        "invalid_evidence_claims": 0,
        "blocked_action": None,
        "final_allowed_action": "health_check",
        "events": [
            {
                "step": 1,
                "candidate_action": "expensive_full_chain_rerun",
                "runtime_gate": "none",
                "allowed": True,
                "reason": "Old runtime has no shared risk gate, so the simulator can only rely on plain judgment.",
            },
            {
                "step": 2,
                "candidate_action": "health_check",
                "runtime_gate": "plain_judgment",
                "allowed": True,
                "reason": "Plain judgment eventually chooses health_check after one costly continuation candidate.",
            },
        ],
    }


def shared_risk_stop_latency(blocked: bool) -> dict[str, Any]:
    """Model same-path continuation after the runtime risk gate exists."""
    return {
        "loop_model": "active_shared_risk_blocks_ungated_continuation",
        "expensive_rerun_attempts_before_gate": 0 if blocked else 1,
        "steps_until_first_safe_gate": 1,
        "steps_until_stop_or_escalation": 1,
        "invalid_evidence_claims": 0,
        "blocked_action": "expensive_full_chain_rerun" if blocked else None,
        "final_allowed_action": "health_check",
        "events": [
            {
                "step": 1,
                "candidate_action": "expensive_full_chain_rerun",
                "runtime_gate": "risk_assessment_required",
                "allowed": not blocked,
                "reason": (
                    "Active shared risk requires risk_assessment before high-impact continuation; "
                    "the ungated rerun candidate is rejected."
                ),
            },
            {
                "step": 1,
                "candidate_action": "health_check",
                "runtime_gate": "risk_assessment.next_gate",
                "allowed": True,
                "reason": "risk_assessment sets next_gate=health_check before another full-chain rerun.",
            },
        ],
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_events(mission_dir: Path) -> list[dict[str, Any]]:
    path = mission_dir / "evidence.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pre_shared_risk_report(source_root: Path, output_dir: Path) -> dict[str, Any]:
    report = {
        "scenario": SCENARIO,
        "source_root": str(source_root),
        "runtime_profile": "pre_shared_risk",
        "can_publish_shared_risk": False,
        "mechanical_score": 0,
        "scripted_agent_score": 4,
        "next_gate": "health_check",
        "stop_latency": pre_shared_risk_stop_latency(),
        "limitations": [
            "record_risk_context.py missing",
            "mission.shared_context.risk_signals unavailable",
            "risk_context_update unavailable",
            "risk_assessment gate unavailable",
        ],
        "simulated_decision": {
            "classification": "invalid_environment_evidence",
            "recommendation": "health_check_before_expensive_rerun",
            "risk_assessment": None,
        },
    }
    write_json(output_dir / "simulation_result.json", report)
    return report


def create_tasks_file(output_dir: Path) -> Path:
    tasks_path = output_dir / "tasks.json"
    write_json(
        tasks_path,
        [
            {
                "id": "T1",
                "title": "Classify failed validation evidence",
                "role": "success-critical",
                "mission_contribution": (
                    "Classifies the failed validation result and prevents unsafe handoff claims."
                ),
                "acceptance_evidence": ["A1", "A2", "A3", "A4"],
            },
            {
                "id": "T2",
                "title": "Run constrained health gate before expensive rerun",
                "role": "success-critical",
                "mission_contribution": (
                    "Checks whether the shared environment can produce valid evidence before another full-chain rerun."
                ),
                "acceptance_evidence": ["A2", "A3", "A4"],
            },
        ],
    )
    return tasks_path


def base_decision_payload() -> dict[str, Any]:
    return {
        "recommendation": "switch",
        "rationale": (
            "Switch to the cheap health gate before another expensive full-chain rerun "
            "because current validation evidence may be invalid."
        ),
        "confidence": 80,
        "evidence_links": [],
        "proposed_mutations": [{"type": "set_active_task", "task_id": "T2"}],
        "requires_human": False,
        "mission_alignment": (
            "A health gate advances A2-A4 by checking whether future validation evidence "
            "can be trusted before claiming handoff safety."
        ),
        "path_assessment": {
            "marginal_roi": "weak",
            "path_role": "one_of_many",
            "evidence_delta": "unclear",
        },
    }


def shared_risk_report(source_root: Path, output_dir: Path) -> dict[str, Any]:
    scripts = {
        name: script_path(source_root, name)
        for name in (
            "init_mission.py",
            "record_risk_context.py",
            "make_decision_packet.py",
            "apply_decision.py",
            "check_mission.py",
        )
    }
    missing = [name for name, path in scripts.items() if not path.exists()]
    if missing:
        return {
            "scenario": SCENARIO,
            "source_root": str(source_root),
            "runtime_profile": "invalid_shared_risk_source",
            "can_publish_shared_risk": False,
            "mechanical_score": 0,
            "scripted_agent_score": 0,
            "limitations": [f"missing script: {name}" for name in missing],
        }

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
            "post-merge-full-chain-validation",
            "--title",
            "Post-merge full-chain validation handoff decision",
            "--objective",
            "Classify validation evidence and decide whether handoff is safe without invalid environment evidence.",
            "--acceptance-evidence",
            "A1:Full-chain validation command is identified.",
            "--acceptance-evidence",
            "A2:The validation result is classified as repository failure, environment failure, or invalid evidence.",
            "--acceptance-evidence",
            "A3:The next action is justified by Mission value, not elapsed time or sunk cost.",
            "--acceptance-evidence",
            "A4:Handoff safety is not claimed unless evidence is valid or the remaining gap is explicitly blocked.",
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
    run(
        "record_risk_context",
        [
            sys.executable,
            str(scripts["record_risk_context.py"]),
            str(mission_dir),
            "record",
            "--task-id",
            "T1",
            "--scope",
            "shared_environment",
            "--signal",
            "validation_persistence_unreliable_after_enospc_sqlite_fsync",
            "--severity",
            "high",
            "--confidence",
            "high",
            "--affected-surface",
            "validation_artifacts",
            "--affected-surface",
            "evidence_persistence",
            "--value-effect",
            "Another expensive full-chain rerun may produce invalid evidence until storage/sqlite health is checked.",
            "--recommended-gate",
            "health_check",
            "--recovery-condition",
            "Storage fsync and sqlite commit/readback smoke checks pass before rerun.",
        ],
    )
    packet_path = output_dir / "decision_packet.json"
    run(
        "make_decision_packet",
        [
            sys.executable,
            str(scripts["make_decision_packet.py"]),
            str(mission_dir),
            "--hook",
            "selection",
            "--output",
            str(packet_path),
        ],
    )

    missing_risk_decision = output_dir / "decision_missing_risk_assessment.json"
    write_json(missing_risk_decision, base_decision_payload())
    run(
        "apply_missing_risk_assessment",
        [
            sys.executable,
            str(scripts["apply_decision.py"]),
            str(mission_dir),
            "--decision",
            str(missing_risk_decision),
        ],
    )

    risk_assessment = {
        "shared_context_used": ["R1"],
        "invalid_evidence_risk": "high",
        "failure_risk": "high",
        "risk_adjusted_value": "weak",
        "next_gate": "health_check",
    }
    valid_decision = base_decision_payload()
    valid_decision["risk_assessment"] = risk_assessment
    valid_decision_path = output_dir / "decision_with_risk_assessment.json"
    write_json(valid_decision_path, valid_decision)
    run(
        "apply_valid_risk_assessment",
        [
            sys.executable,
            str(scripts["apply_decision.py"]),
            str(mission_dir),
            "--decision",
            str(valid_decision_path),
        ],
    )
    run(
        "resolve_risk_context",
        [
            sys.executable,
            str(scripts["record_risk_context.py"]),
            str(mission_dir),
            "resolve",
            "--task-id",
            "T1",
            "--risk-id",
            "R1",
            "--status",
            "resolved",
            "--summary",
            "Scripted simulation recovery condition acknowledged.",
            "--recovery-note",
            "Storage fsync and sqlite commit/readback smoke checks are required before rerun.",
        ],
    )
    run("check_mission", [sys.executable, str(scripts["check_mission.py"]), str(mission_dir)])

    mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
    events = read_events(mission_dir)
    packet = json.loads(packet_path.read_text(encoding="utf-8")) if packet_path.exists() else {}
    event_types = [event.get("event_type") for event in events]

    mechanical_checks = [
        steps["record_risk_context"]["returncode"] == 0,
        bool(mission.get("shared_context", {}).get("risk_signals")),
        "risk_context_update" in event_types,
        bool(packet.get("shared_context", {}).get("active_risk_signals")),
        steps["apply_missing_risk_assessment"]["returncode"] != 0
        and steps["apply_missing_risk_assessment"]["stderr"] == "decision missing field: risk_assessment",
        steps["apply_valid_risk_assessment"]["returncode"] == 0,
        risk_assessment["risk_adjusted_value"] in {"weak", "negative", "unclear"},
        "risk_context_recovery" in event_types,
    ]
    agent_checks = [
        True,  # classifies failed run as invalid environment evidence
        True,  # avoids repository-regression diagnosis by default
        mechanical_checks[0],  # publishes Mission-level shared risk
        True,  # consumes shared context rather than raw task logs
        mechanical_checks[4] and mechanical_checks[5],  # uses risk_assessment gate
        risk_assessment["invalid_evidence_risk"] == "high",
        risk_assessment["failure_risk"] == "high",
        risk_assessment["risk_adjusted_value"] == "weak",
        risk_assessment["next_gate"] == "health_check",
        True,  # does not claim handoff safety from invalid evidence
    ]
    missing_risk_blocked = (
        steps["apply_missing_risk_assessment"]["returncode"] != 0
        and steps["apply_missing_risk_assessment"]["stderr"] == "decision missing field: risk_assessment"
    )

    return {
        "scenario": SCENARIO,
        "source_root": str(source_root),
        "runtime_profile": "shared_risk",
        "can_publish_shared_risk": True,
        "mechanical_score": sum(1 for item in mechanical_checks if item),
        "scripted_agent_score": sum(1 for item in agent_checks if item),
        "risk_assessment": risk_assessment,
        "stop_latency": shared_risk_stop_latency(missing_risk_blocked),
        "event_types": event_types,
        "packet_shared_context": packet.get("shared_context"),
        "risk_signals": mission.get("shared_context", {}).get("risk_signals", []),
        "steps": steps,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic shared-risk agent simulation.")
    parser.add_argument("--source-root", required=True, help="Repository/source snapshot root.")
    parser.add_argument("--output-dir", required=True, help="Directory for simulation artifacts.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not script_path(source_root, "record_risk_context.py").exists():
        report = pre_shared_risk_report(source_root, output_dir)
    else:
        report = shared_risk_report(source_root, output_dir)
        write_json(output_dir / "simulation_result.json", report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
