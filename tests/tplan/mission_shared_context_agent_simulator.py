#!/usr/bin/env python3
"""Deterministic acceptance simulation for tplan Mission shared context memory."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCENARIO = {
    "mission": "Resume an interrupted validation Mission without relying on chat history.",
    "interruption": "The first runtime recorded a shared environment risk, then stopped before handoff.",
    "fresh_start_decisions": [
        "continue matching Mission",
        "reject conflicting same mission id",
        "create new Mission with old memory as source_contexts",
    ],
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_events(mission_dir: Path) -> list[dict[str, Any]]:
    path = mission_dir / "evidence.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_step(name: str, args: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    return {
        "name": name,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def script_path(source_root: Path, name: str) -> Path:
    return source_root / "skills" / "tplan" / "scripts" / name


def pre_mission_shared_context_report(source_root: Path, output_dir: Path, missing: list[str]) -> dict[str, Any]:
    report = {
        "scenario": SCENARIO,
        "source_root": str(source_root),
        "runtime_profile": "pre_mission_shared_context",
        "can_load_mission_memory": False,
        "mechanical_score": 0,
        "scripted_agent_score": 2,
        "limitations": missing
        or [
            "preflight_mission.py missing",
            "project-level Mission shared context unavailable",
        ],
        "expected_failure_modes": [
            "fresh agent may rely on chat history",
            "same mission id conflict may silently continue",
            "source contexts may be treated as inherited authority",
        ],
    }
    write_json(output_dir / "simulation_result.json", report)
    return report


def create_tasks_file(output_dir: Path, acceptance_ids: list[str]) -> Path:
    tasks_path = output_dir / "tasks.json"
    write_json(
        tasks_path,
        [
            {
                "id": "T1",
                "title": "Preserve Mission memory",
                "role": "success-critical",
                "mission_contribution": "Keeps Mission identity and recovery context available.",
                "acceptance_evidence": acceptance_ids,
            }
        ],
    )
    return tasks_path


def parse_step_json(step: dict[str, Any]) -> dict[str, Any]:
    if step["returncode"] != 0:
        raise RuntimeError(f"{step['name']} failed: {step['stderr']}")
    return json.loads(step["stdout"])


def mission_shared_context_report(source_root: Path, output_dir: Path) -> dict[str, Any]:
    scripts = {
        name: script_path(source_root, name)
        for name in (
            "init_mission.py",
            "preflight_mission.py",
            "record_risk_context.py",
        )
    }
    missing = [f"{name} missing" for name, path in scripts.items() if not path.exists()]
    if missing:
        if "preflight_mission.py missing" not in missing:
            missing.append("preflight_mission.py missing")
        if "project-level Mission shared context unavailable" not in missing:
            missing.append("project-level Mission shared context unavailable")
        return pre_mission_shared_context_report(source_root, output_dir, missing)

    project_root = output_dir / "project"
    interrupted_dir = output_dir / "interrupted_mission"
    new_dir = output_dir / "new_mission"
    interrupted_tasks = create_tasks_file(output_dir / "interrupted_tasks", ["A1", "A2"])
    new_tasks = create_tasks_file(output_dir / "new_tasks", ["A1"])
    steps: dict[str, dict[str, Any]] = {}

    def run(name: str, args: list[str]) -> None:
        steps[name] = run_step(name, args, source_root)

    run(
        "init_interrupted_mission",
        [
            sys.executable,
            str(scripts["init_mission.py"]),
            "--dir",
            str(interrupted_dir),
            "--project-root",
            str(project_root),
            "--mission-id",
            "interrupted-validation",
            "--title",
            "Interrupted validation Mission",
            "--objective",
            "Validate repository handoff after interrupted run.",
            "--acceptance-evidence",
            "A1:Mission memory is available to a fresh agent.",
            "--acceptance-evidence",
            "A2:Shared environment risk is visible before the next action.",
            "--task-json",
            str(interrupted_tasks),
        ],
    )
    run(
        "record_shared_risk",
        [
            sys.executable,
            str(scripts["record_risk_context.py"]),
            str(interrupted_dir),
            "record",
            "--task-id",
            "T1",
            "--scope",
            "shared_environment",
            "--signal",
            "fsync_unreliable",
            "--severity",
            "high",
            "--confidence",
            "high",
            "--affected-surface",
            "generation",
            "--value-effect",
            "Expensive reruns may produce invalid evidence.",
            "--recommended-gate",
            "environment_health_gate",
            "--recovery-condition",
            "dd fsync and sqlite commit smoke pass",
        ],
    )
    run(
        "preflight_matching",
        [
            sys.executable,
            str(scripts["preflight_mission.py"]),
            "--project-root",
            str(project_root),
            "--mission-id",
            "interrupted-validation",
            "--objective",
            "Validate repository handoff after interrupted run.",
            "--acceptance-evidence",
            "A1:Mission memory is available to a fresh agent.",
            "--acceptance-evidence",
            "A2:Shared environment risk is visible before the next action.",
            "--json",
        ],
    )
    run(
        "preflight_conflict",
        [
            sys.executable,
            str(scripts["preflight_mission.py"]),
            "--project-root",
            str(project_root),
            "--mission-id",
            "interrupted-validation",
            "--objective",
            "Redesign a different validation system.",
            "--acceptance-evidence",
            "A1:Mission memory is available to a fresh agent.",
            "--acceptance-evidence",
            "A2:Shared environment risk is visible before the next action.",
            "--json",
        ],
    )
    run(
        "init_new_with_source_context",
        [
            sys.executable,
            str(scripts["init_mission.py"]),
            "--dir",
            str(new_dir),
            "--project-root",
            str(project_root),
            "--source-context",
            "interrupted-validation",
            "--mission-id",
            "new-validation-hardening",
            "--title",
            "New validation hardening Mission",
            "--objective",
            "Use old memory as background while owning new acceptance.",
            "--acceptance-evidence",
            "A1:New Mission owns new acceptance evidence.",
            "--task-json",
            str(new_tasks),
        ],
    )

    matching = parse_step_json(steps["preflight_matching"])
    conflict = parse_step_json(steps["preflight_conflict"])
    new_mission = read_json(new_dir / "mission.json")
    context_file = project_root / ".tplan" / "shared_contexts" / "tplan_mission_shared_context-interrupted-validation.md"
    markdown = context_file.read_text(encoding="utf-8") if context_file.exists() else ""
    event_types = [event.get("event_type") for event in read_events(interrupted_dir)]
    new_acceptance_ids = [item.get("id") for item in new_mission["mission"]["acceptance_evidence"]]
    source_contexts = new_mission.get("shared_context", {}).get("source_contexts", [])

    checks = {
        "context_file_exists": context_file.exists(),
        "matching_continuation": matching.get("action") == "continue_existing",
        "conflict_blocks_silent_continue": conflict.get("action") == "needs_agentic_selection",
        "source_contexts_recorded": source_contexts == ["interrupted-validation"],
        "new_acceptance_not_inherited": new_acceptance_ids == ["A1"],
        "risk_visible_in_markdown": "R1: fsync_unreliable (high, active)" in markdown,
    }
    mechanical_score = sum(1 for passed in checks.values() if passed)
    scripted_agent_checks = {
        "identifies_previous_mission": "interrupted-validation" in markdown,
        "objective_without_chat": "Validate repository handoff after interrupted run." in markdown,
        "sees_active_risk": checks["risk_visible_in_markdown"],
        "refuses_conflicting_continue": checks["conflict_blocks_silent_continue"],
        "source_context_is_background": checks["source_contexts_recorded"],
        "new_identity_preserved": new_mission["mission"]["id"] == "new-validation-hardening",
    }
    scripted_agent_score = sum(1 for passed in scripted_agent_checks.values() if passed)

    report = {
        "scenario": SCENARIO,
        "source_root": str(source_root),
        "runtime_profile": "mission_shared_context",
        "can_load_mission_memory": True,
        "mechanical_score": mechanical_score,
        "scripted_agent_score": scripted_agent_score,
        "checks": checks,
        "scripted_agent_checks": scripted_agent_checks,
        "preflight": {
            "matching_action": matching.get("action"),
            "conflict_action": conflict.get("action"),
            "conflict_fields": conflict.get("conflicts", []),
        },
        "lineage": {
            "source_contexts": source_contexts,
            "new_acceptance_evidence": new_acceptance_ids,
        },
        "event_types": event_types,
        "shared_context_markdown": markdown,
        "steps": steps,
    }
    write_json(output_dir / "simulation_result.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run tplan Mission shared context acceptance simulation.")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        mission_shared_context_report(Path(args.source_root), output_dir)
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"simulation_result: {output_dir / 'simulation_result.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
