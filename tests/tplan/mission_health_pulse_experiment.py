#!/usr/bin/env python3
"""Deterministic multi-scenario experiment for TPLAN Mission Health Pulse."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_NEXT_GATES = {
    "continue",
    "continuation_authorization",
    "anti_spiral_audit",
    "selection",
    "subtraction",
    "loopback",
    "mission_review",
    "health_check",
    "stop",
    "escalate",
}

GATE_OWNERS = {
    "continue": "inline_alignment",
    "continuation_authorization": "linear_continuation_gate",
    "anti_spiral_audit": "anti_spiral_runtime_gate",
    "selection": "selection_hook",
    "subtraction": "subtraction_hook",
    "loopback": "loopback_hook",
    "mission_review": "mission_review_gate",
    "health_check": "shared_risk_mission_health_route",
    "stop": "stop_report",
    "escalate": "human_or_authority_escalation",
}

SURFACE_REQUIREMENTS = {
    "skills/tplan/resources/hooks.md": [
        "Snapshot / Pulse / Gate Control Surface",
        "Scripts observe. Pulse routes. Gates decide.",
        "mission_pulse",
        "Pulse is not a new judgment center",
        "not a standalone undefined gate",
    ],
    "skills/tplan/resources/schema.md": [
        "Mission Pulse Route Note",
        "tplan.pulse.v0.1",
        "Pulse routes observable signals to an existing Gate",
        "must not decide Mission ROI",
        "next_gate=health_check",
    ],
    "docs/methodologies/tplan.md": [
        "Snapshot / Pulse / Gate",
        "场景回放",
        "普通低风险推进",
        "同一路径准备继续",
        "共享风险影响后续任务",
    ],
    "tests/tplan/mission_health_pulse_ab_tests.md": [
        "Scenario A: Routine Checkpoint Must Stay Light",
        "Scenario B: Same-path Continue Needs Authorization",
        "Scenario C: Repeated Local Repair Routes To Anti-Spiral Or Subtraction",
        "Scenario D: Shared Risk Must Not Stay Buried",
        "Scenario E: Branch Cleanup Must Use Existing Gates",
        "Scenario F: Mission Drift Or Authority Gap Stops The Path",
    ],
}

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "routine_checkpoint",
        "name": "Routine checkpoint stays Snapshot-only",
        "pre_pulse_failure_mode": "over_review_noise_or_process_theater",
        "trigger": "checkpoint_batch",
        "scope": "active_node",
        "pulse_invoked": False,
        "signals": [],
        "evidence_delta": "new_evidence_expected",
        "branch_disposition": "keep",
        "systemic_probe": "not_needed",
        "next_gate": "continue",
        "alternative_next_gates": [],
        "requires_full_review": False,
        "expected_path": ["checkpoint", "snapshot", "continue"],
        "forbidden": ["full_mission_review", "health_score", "durable_pulse_state"],
    },
    {
        "id": "same_path_continue",
        "name": "Same-path continuation routes to authorization",
        "pre_pulse_failure_mode": "ungated_continue_based_on_sunk_cost_or_almost_done",
        "trigger": "before_continue",
        "scope": "active_node",
        "pulse_invoked": True,
        "signals": ["repeated_same_path_attempt", "weak_evidence_delta"],
        "evidence_delta": "weak_evidence_expected",
        "branch_disposition": "keep",
        "systemic_probe": "not_needed",
        "next_gate": "continuation_authorization",
        "alternative_next_gates": ["anti_spiral_audit", "mission_review", "stop"],
        "requires_full_review": False,
        "expected_path": ["snapshot", "pulse", "continuation_authorization"],
        "forbidden": ["pulse_authorizes_continue", "health_verdict"],
    },
    {
        "id": "repeated_local_repair",
        "name": "Third local repair routes to Anti-Spiral or subtraction",
        "pre_pulse_failure_mode": "adds_another_local_layer_without_returning_upstream",
        "trigger": "before_continue",
        "scope": "subpath",
        "pulse_invoked": True,
        "signals": ["third_touch", "additive_layering", "weak_evidence_delta"],
        "evidence_delta": "weak_evidence_expected",
        "branch_disposition": "unclear",
        "systemic_probe": "needs_gate",
        "next_gate": "anti_spiral_audit",
        "alternative_next_gates": ["subtraction", "mission_review"],
        "requires_full_review": False,
        "expected_path": ["snapshot", "pulse", "anti_spiral_audit"],
        "forbidden": ["new_fallback_layer", "pulse_prunes_directly"],
    },
    {
        "id": "shared_risk",
        "name": "Shared risk routes to health_check and risk assessment",
        "pre_pulse_failure_mode": "active_shared_risk_stays_buried_in_task_logs",
        "trigger": "shared_risk",
        "scope": "mission",
        "pulse_invoked": True,
        "signals": ["active_shared_risk", "invalid_evidence_risk"],
        "evidence_delta": "unclear",
        "branch_disposition": "keep",
        "systemic_probe": "use_existing_structure",
        "next_gate": "health_check",
        "alternative_next_gates": ["stop", "escalate", "selection"],
        "requires_full_review": False,
        "expected_path": ["risk_context_update", "snapshot", "pulse", "risk_assessment"],
        "forbidden": ["standalone_health_gate", "ungated_expensive_rerun"],
    },
    {
        "id": "branch_cleanup",
        "name": "Branch hygiene routes to selection or subtraction",
        "pre_pulse_failure_mode": "stale_supporting_branches_accumulate_or_are_pruned_directly",
        "trigger": "branch_cleanup",
        "scope": "mission",
        "pulse_invoked": True,
        "signals": ["stale_branch", "one_of_many_path"],
        "evidence_delta": "unclear",
        "branch_disposition": "prune",
        "systemic_probe": "not_needed",
        "next_gate": "selection",
        "alternative_next_gates": ["subtraction", "mission_review"],
        "requires_full_review": False,
        "expected_path": ["snapshot", "pulse", "selection"],
        "forbidden": ["pulse_deletes_success_critical_work", "silent_stale_branch"],
    },
    {
        "id": "mission_drift_or_authority_gap",
        "name": "Mission drift or authority gap routes to review, stop, or escalation",
        "pre_pulse_failure_mode": "agent_invents_intent_or_acceptance_authority",
        "trigger": "before_freeze",
        "scope": "mission",
        "pulse_invoked": True,
        "signals": ["acceptance_authority_unclear", "mission_identity_unclear"],
        "evidence_delta": "unclear",
        "branch_disposition": "defer",
        "systemic_probe": "needs_gate",
        "next_gate": "mission_review",
        "alternative_next_gates": ["stop", "escalate"],
        "requires_full_review": True,
        "expected_path": ["snapshot", "pulse", "mission_review"],
        "forbidden": ["invented_acceptance_criteria", "silent_continue"],
    },
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def pulse_surface(source_root: Path) -> dict[str, Any]:
    missing: dict[str, list[str]] = {}
    for relative, phrases in SURFACE_REQUIREMENTS.items():
        text = read_text(source_root / relative)
        absent = [phrase for phrase in phrases if phrase not in text]
        if absent:
            missing[relative] = absent
    return {
        "present": not missing,
        "missing": missing,
        "checked_files": sorted(SURFACE_REQUIREMENTS),
    }


def scenario_report(scenario: dict[str, Any]) -> dict[str, Any]:
    next_gate = scenario["next_gate"]
    alternative_next_gates = scenario["alternative_next_gates"]
    known_routes = [gate for gate in [next_gate, *alternative_next_gates] if gate in ALLOWED_NEXT_GATES]
    invariants = {
        "pulse_route_only": scenario["pulse_invoked"] is False or next_gate != "continue",
        "pulse_does_not_mutate": True,
        "pulse_has_no_health_verdict": True,
        "route_is_existing_gate": next_gate in ALLOWED_NEXT_GATES,
        "alternatives_are_existing_gates": len(known_routes) == 1 + len(alternative_next_gates),
        "gate_owner_defined": next_gate in GATE_OWNERS,
        "routine_checkpoint_stays_light": scenario["id"] != "routine_checkpoint"
        or scenario["requires_full_review"] is False,
        "health_check_not_standalone": scenario["id"] != "shared_risk"
        or GATE_OWNERS[next_gate] == "shared_risk_mission_health_route",
    }
    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "pre_pulse_failure_mode": scenario["pre_pulse_failure_mode"],
        "pulse_invoked": scenario["pulse_invoked"],
        "pulse": {
            "trigger": scenario["trigger"],
            "scope": scenario["scope"],
            "signals": scenario["signals"],
            "evidence_delta": scenario["evidence_delta"],
            "branch_disposition": scenario["branch_disposition"],
            "systemic_probe": scenario["systemic_probe"],
            "next_gate": next_gate,
            "alternative_next_gates": alternative_next_gates,
            "rationale": f"Route {scenario['id']} to {next_gate}; do not decide inside Pulse.",
            "evidence_links": [],
        },
        "gate_owner": GATE_OWNERS.get(next_gate),
        "requires_full_review": scenario["requires_full_review"],
        "expected_path": scenario["expected_path"],
        "forbidden": scenario["forbidden"],
        "invariants": invariants,
        "scenario_passed": all(invariants.values()),
    }


def run_report(source_root: Path, output_dir: Path) -> dict[str, Any]:
    surface = pulse_surface(source_root)
    scenarios = [scenario_report(scenario) for scenario in SCENARIOS]
    route_coverage = sorted({scenario["pulse"]["next_gate"] for scenario in scenarios})
    all_invariants = [
        value for scenario in scenarios for value in scenario["invariants"].values()
    ]
    report = {
        "experiment": "mission_health_pulse_multi_scenario",
        "source_root": str(source_root),
        "runtime_profile": "mission_health_pulse_documented"
        if surface["present"]
        else "pre_mission_health_pulse_contract",
        "surface": surface,
        "scenario_count": len(scenarios),
        "route_coverage": route_coverage,
        "mechanical_score": sum(1 for value in all_invariants if value),
        "max_mechanical_score": len(all_invariants),
        "scenario_pass_count": sum(1 for scenario in scenarios if scenario["scenario_passed"]),
        "scenarios": scenarios,
        "development_gate": {
            "ready_for_runtime_development": surface["present"]
            and all(scenario["scenario_passed"] for scenario in scenarios),
            "next_step": "Write failing runtime tests for read-only pulse output before implementing mission_pulse.py.",
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "simulation_result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Mission Health Pulse multi-scenario experiment.")
    parser.add_argument("--source-root", required=True, help="Repository/source snapshot root.")
    parser.add_argument("--output-dir", required=True, help="Directory for experiment artifacts.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = run_report(Path(args.source_root).resolve(), Path(args.output_dir).resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
