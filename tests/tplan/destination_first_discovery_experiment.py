#!/usr/bin/env python3
"""Deterministic fixture and replay experiment for TPLAN issue #109.

The experiment compares eager Task materialization, correct use of current TPLAN, and
an optional destination-first discovery representation. It is a research harness, not
production runtime support.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


TERMINAL_TASK_STATUSES = {"completed", "pruned", "abandoned", "superseded"}
FOG_DISPOSITIONS = {"open", "materialized", "out_of_scope", "superseded"}


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "issue_109_destination_first"
REPLAY_INPUTS_PATH = FIXTURE_ROOT / "replay_inputs.json"


def load_replay_inputs() -> dict[str, Any]:
    inputs = json.loads(REPLAY_INPUTS_PATH.read_text(encoding="utf-8"))
    required_keys = {"evidence_status", "real_mission_replays", "negative_control"}
    missing = required_keys.difference(inputs)
    if missing:
        raise ValueError(f"Replay input fixture is missing required keys: {sorted(missing)}")
    if not isinstance(inputs["real_mission_replays"], list):
        raise ValueError("Replay input fixture real_mission_replays must be a list")
    if not isinstance(inputs["negative_control"], dict):
        raise ValueError("Replay input fixture negative_control must be an object")
    return inputs


REPLAY_INPUTS = load_replay_inputs()
REAL_MISSION_REPLAYS: list[dict[str, Any]] = REPLAY_INPUTS["real_mission_replays"]
NEGATIVE_CONTROL: dict[str, Any] = REPLAY_INPUTS["negative_control"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def baseline_surface(source_root: Path) -> dict[str, Any]:
    schema = read_text(source_root / "skills/tplan/resources/schema.md")
    hooks = read_text(source_root / "skills/tplan/resources/hooks.md")
    lifecycle = read_text(source_root / "skills/tplan/resources/lifecycle.md")
    runtime = read_text(source_root / "skills/tplan/scripts/tplan_runtime.py")
    checks = {
        "schema_is_v0_1": "must be `tplan.v0.1`" in schema,
        "runtime_nodes_are_task_subtask_step": (
            "supports `task`, `subtask`, and\n  `step` nodes" in schema
        ),
        "lite_still_requires_active_task": (
            "Mission -> active Task" in schema and "with no materialized Step" in schema
        ),
        "exploratory_means_uncertain_payoff": (
            "`exploratory`: uncertain payoff governed by risk/resource policy" in schema
        ),
        "existing_hooks_cover_discovery_handoff": all(
            phrase in hooks
            for phrase in (
                "| `mission_intake` |",
                "| `addition` |",
                "| `selection` |",
                "| `loopback` |",
            )
        ),
        "task_lifecycle_has_no_fog_state": (
            "- `pending`" in lifecycle
            and "- `superseded`" in lifecycle
            and "fog" not in lifecycle.lower()
        ),
        "no_declared_task_dependency_contract": (
            "depends_on" not in schema and '"depends_on"' not in runtime
        ),
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "finding": (
            "Current TPLAN has a real pre-Task representation gap, but already has the semantic "
            "handoff gates needed to avoid eager materialization."
        ),
    }


def core_fixture() -> dict[str, Any]:
    return {
        "mission": {
            "objective": "Deliver a recoverable decision package for a stable Mission destination.",
            "acceptance_evidence": ["A1", "A2"],
            "acceptance_satisfied": ["A1"],
            "human_in_loop": 0,
        },
        "discovery": {
            "destination": {
                "objective_ref": "mission.objective",
                "acceptance_refs": ["A1", "A2"],
                "authority_ref": "mission.human_in_loop",
            },
            "fog": [
                {
                    "id": "F1",
                    "region": "Choose the evidence carrier after the source boundary is known.",
                    "disposition": "materialized",
                    "materialized_task_ids": ["T1"],
                    "source_refs": ["mission_intake"],
                },
                {
                    "id": "F2",
                    "region": "A newly exposed recovery condition is not yet precise enough to task.",
                    "disposition": "open",
                    "materialized_task_ids": [],
                    "source_refs": ["T1"],
                },
                {
                    "id": "F3",
                    "region": "A neighboring product adapter is outside this Mission.",
                    "disposition": "out_of_scope",
                    "materialized_task_ids": [],
                    "source_refs": ["mission_intake"],
                },
                {
                    "id": "F4",
                    "region": "An earlier recovery guess was replaced by the F2 finding.",
                    "disposition": "superseded",
                    "materialized_task_ids": [],
                    "superseded_by": "F2",
                    "source_refs": ["T1"],
                },
            ],
        },
        "tasks": [
            {
                "id": "T0",
                "status": "superseded",
                "role": "supporting",
                "acceptance_evidence": [],
                "depends_on": [],
            },
            {
                "id": "T1",
                "status": "completed",
                "role": "success-critical",
                "acceptance_evidence": ["A1"],
                "depends_on": [],
            },
            {
                "id": "T2",
                "status": "pending",
                "role": "success-critical",
                "acceptance_evidence": ["A2"],
                "depends_on": ["T1"],
            },
            {
                "id": "T3",
                "status": "pending",
                "role": "supporting",
                "acceptance_evidence": [],
                "depends_on": [],
            },
            {
                "id": "T4",
                "status": "blocked",
                "role": "supporting",
                "acceptance_evidence": [],
                "depends_on": ["T5"],
            },
            {
                "id": "T5",
                "status": "active",
                "role": "supporting",
                "acceptance_evidence": [],
                "depends_on": [],
            },
        ],
    }


def validate_fixture(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tasks = {task["id"]: task for task in state["tasks"]}
    destination = state["discovery"]["destination"]
    if set(destination) != {"objective_ref", "acceptance_refs", "authority_ref"}:
        errors.append("Destination must be reference-only and must not duplicate Mission truth.")

    fog_ids = {fog["id"] for fog in state["discovery"]["fog"]}
    for fog in state["discovery"]["fog"]:
        if fog.get("disposition") not in FOG_DISPOSITIONS:
            errors.append(f"Fog {fog.get('id')} has an invalid disposition.")
        for forbidden in ("status", "role", "selected", "active", "resolved"):
            if forbidden in fog:
                errors.append(f"Fog {fog.get('id')} illegally carries executable field {forbidden}.")
        materialized = fog.get("materialized_task_ids", [])
        if fog.get("disposition") == "materialized" and not materialized:
            errors.append(f"Fog {fog.get('id')} is materialized without a Task reference.")
        for task_id in materialized:
            if task_id not in tasks:
                errors.append(f"Fog {fog.get('id')} references missing Task {task_id}.")
        superseded_by = fog.get("superseded_by")
        if superseded_by is not None and superseded_by not in fog_ids:
            errors.append(f"Fog {fog.get('id')} references missing superseding Fog {superseded_by}.")

    for task in tasks.values():
        for blocker_id in task.get("depends_on", []):
            if blocker_id not in tasks:
                errors.append(f"Task {task['id']} depends on missing Task {blocker_id}.")
    return errors


def compute_frontier(state: dict[str, Any]) -> list[str]:
    tasks = {task["id"]: task for task in state["tasks"]}
    frontier = []
    for task in state["tasks"]:
        if task["status"] != "pending":
            continue
        blockers = [tasks[task_id] for task_id in task.get("depends_on", [])]
        if all(blocker["status"] in TERMINAL_TASK_STATUSES for blocker in blockers):
            frontier.append(task["id"])
    return sorted(frontier)


def mission_completion_ready(state: dict[str, Any]) -> bool:
    success_critical = [task for task in state["tasks"] if task["role"] == "success-critical"]
    tasks_complete = all(task["status"] == "completed" for task in success_critical)
    required = set(state["mission"]["acceptance_evidence"])
    satisfied = set(state["mission"]["acceptance_satisfied"])
    return tasks_complete and required.issubset(satisfied)


def core_fixture_report() -> dict[str, Any]:
    state = core_fixture()
    errors = validate_fixture(state)
    frontier = compute_frontier(state)
    serialized = json.dumps(state, ensure_ascii=False, sort_keys=True)
    restarted = json.loads(serialized)
    restarted_frontier = compute_frontier(restarted)
    fog_ids = sorted(fog["id"] for fog in state["discovery"]["fog"])
    task_ids = sorted(task["id"] for task in state["tasks"])
    invariants = {
        "shape_valid": not errors,
        "destination_is_derived": set(state["discovery"]["destination"])
        == {"objective_ref", "acceptance_refs", "authority_ref"},
        "fog_and_tasks_have_disjoint_identity": not set(fog_ids).intersection(task_ids),
        "fog_never_enters_frontier": not set(fog_ids).intersection(frontier),
        "blocked_task_excluded": "T4" not in frontier,
        "terminal_blocker_unlocks_candidate": "T2" in frontier,
        "multiple_candidates_route_to_selection": frontier == ["T2", "T3"],
        "restart_frontier_is_deterministic": frontier == restarted_frontier,
        "fog_does_not_satisfy_completion": mission_completion_ready(state) is False,
        "history_is_retained": {fog["disposition"] for fog in state["discovery"]["fog"]}
        >= {"out_of_scope", "superseded", "materialized"},
    }
    return {
        "errors": errors,
        "frontier": frontier,
        "restarted_frontier": restarted_frontier,
        "next_gate": "selection" if len(frontier) > 1 else "continue",
        "invariants": invariants,
        "passed": all(invariants.values()),
    }


def replay_report(replay: dict[str, Any]) -> dict[str, Any]:
    vague_regions = [
        region for region in replay["regions"] if region["precision_on_first_observation"] == "vague"
    ]
    specified_regions = [
        region
        for region in replay["regions"]
        if region["precision_on_first_observation"] == "specified"
    ]
    missing_additions = [
        region for region in replay["regions"] if region["later_disposition"] == "missing_addition"
    ]
    current_tplan_can_represent_vague_regions = all(
        "discovery Task" in region["correct_current_tplan_handling"]
        or "Mission narrative" in region["correct_current_tplan_handling"]
        for region in vague_regions
    )
    unique_value_over_current = bool(vague_regions) and not current_tplan_can_represent_vague_regions
    comparison = {
        "eager_task_materialization": {
            "premature_runtime_nodes": len(vague_regions),
            "specified_regions_materialized_or_handled": len(specified_regions),
            "recovery_visibility_requires_maintenance": True,
        },
        "current_tplan_correct_use": {
            "premature_runtime_nodes": 0,
            "vague_regions_kept_in_discovery_task_or_narrative": len(vague_regions),
            "specified_regions_requiring_addition": len(
                [
                    region
                    for region in specified_regions
                    if "addition" in region["correct_current_tplan_handling"]
                ]
            ),
            "observed_missing_additions": len(missing_additions),
            "recovery_visibility_requires_maintenance": True,
        },
        "destination_first_discovery": {
            "premature_runtime_nodes": 0,
            "durable_fog_records": len(vague_regions),
            "specified_regions_requiring_addition": len(
                [
                    region
                    for region in specified_regions
                    if "addition" in region["correct_current_tplan_handling"]
                ]
            ),
            "extra_durable_state": len(vague_regions),
            "recovery_visibility_requires_maintenance": True,
        },
    }
    return {
        "id": replay["id"],
        "title": replay["title"],
        "source_anchors": replay["source_anchors"],
        "observed_runtime_shape": replay["observed_runtime_shape"],
        "region_count": len(replay["regions"]),
        "vague_region_count": len(vague_regions),
        "specified_region_count": len(specified_regions),
        "regions": replay["regions"],
        "observed_defects": replay["observed_defects"],
        "defect_classification": replay["defect_classification"],
        "comparison": comparison,
        "beats_eager_materialization": (
            comparison["destination_first_discovery"]["premature_runtime_nodes"]
            < comparison["eager_task_materialization"]["premature_runtime_nodes"]
        ),
        "current_tplan_can_represent_vague_regions": current_tplan_can_represent_vague_regions,
        "narrative_proven_insufficient_when_maintained": False,
        "unique_value_over_current_tplan": unique_value_over_current,
    }


def negative_control_report() -> dict[str, Any]:
    mode = "off" if not NEGATIVE_CONTROL["not_yet_precise_regions"] else "on"
    return {
        **NEGATIVE_CONTROL,
        "actual_mode": mode,
        "passed": mode == NEGATIVE_CONTROL["expected_mode"],
    }


def adoption_decision(
    baseline: dict[str, Any],
    fixture: dict[str, Any],
    replays: list[dict[str, Any]],
    control: dict[str, Any],
) -> dict[str, Any]:
    rule_results = {
        "baseline_gap_confirmed": baseline["passed"],
        "core_fixture_passes": fixture["passed"],
        "at_least_one_replay_improves_over_eager": any(
            replay["beats_eager_materialization"] for replay in replays
        ),
        "no_replay_adds_premature_nodes": all(
            replay["comparison"]["destination_first_discovery"]["premature_runtime_nodes"]
            <= replay["comparison"]["current_tplan_correct_use"]["premature_runtime_nodes"]
            for replay in replays
        ),
        "unique_value_over_correct_current_tplan": any(
            replay["unique_value_over_current_tplan"] for replay in replays
        ),
        "narrative_insufficiency_proven": any(
            replay["narrative_proven_insufficient_when_maintained"] for replay in replays
        ),
        "negative_control_stays_off": control["passed"],
    }
    recommend_core_runtime_change = all(rule_results.values())
    return {
        "rule_results": rule_results,
        "recommend_core_runtime_change": recommend_core_runtime_change,
        "recommend_task_schema_change": False,
        "recommend_new_runtime_node_kind": False,
        "recommended_scope": (
            "production_destination_first_capability"
            if recommend_core_runtime_change
            else "documentation_pattern_and_prospective_trial_only"
        ),
        "rationale": (
            "The fixture proves the representation can be bounded, but the real replays do not "
            "show unique value over correct use of the existing discovery Task, Mission narrative, "
            "addition, selection, and loopback surfaces. The observed failures are stale state or "
            "missing addition, not proof that narrative recovery is intrinsically insufficient."
        ),
    }


def run_report(source_root: Path, output_dir: Path) -> dict[str, Any]:
    baseline = baseline_surface(source_root)
    fixture = core_fixture_report()
    replays = [replay_report(copy.deepcopy(replay)) for replay in REAL_MISSION_REPLAYS]
    control = negative_control_report()
    decision = adoption_decision(baseline, fixture, replays, control)
    report = {
        "experiment": "tplan_destination_first_discovery_issue_109",
        "source_root": str(source_root),
        "baseline": baseline,
        "core_fixture": fixture,
        "real_mission_replays": replays,
        "negative_control": control,
        "adoption_decision": decision,
        "evidence_status": copy.deepcopy(REPLAY_INPUTS["evidence_status"]),
        "claim_ceiling": (
            "The result applies to the bounded fixture and replayed Missions only. It does not "
            "prove general planning superiority, semantic correctness, concurrency safety, or "
            "independently verified historical replay facts."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "simulation_result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the TPLAN issue #109 destination-first discovery experiment."
    )
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = run_report(Path(args.source_root).resolve(), Path(args.output_dir).resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
