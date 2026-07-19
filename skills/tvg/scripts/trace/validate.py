#!/usr/bin/env python3
"""Validate Thinking Value-Gain trace bookkeeping shape.

This script does not judge whether the trace is valuable, true, or ready to exit.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime_bootstrap import activate_runtime

activate_runtime(__file__)

from _runtime.core.io import load_json

SCRIPT_DISCLAIMER = "No schema violations were detected; agentic audit is still required."


def load_schema(script_path: Path) -> dict:
    return load_json(script_path.parents[2] / "resources" / "trace-record-schema.json")


def require_mapping(value: object, path: str, errors: list[str]) -> dict:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return {}
    return value


def require_list(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path}: expected list")


def require_optional_string(value: object, path: str, errors: list[str]) -> None:
    if value is not None and not isinstance(value, str):
        errors.append(f"{path}: expected string")


def require_bool(value: object, path: str, errors: list[str]) -> None:
    if not isinstance(value, bool):
        errors.append(f"{path}: expected boolean")


def require_score(value: object, path: str, errors: list[str]) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or value > 5:
        errors.append(f"{path}: expected number from 0 to 5")


def require_int_range(value: object, path: str, minimum: int, maximum: int, errors: list[str]) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > maximum:
        errors.append(f"{path}: expected integer from {minimum} to {maximum}")


def validate(trace: dict, schema: dict) -> list[str]:
    errors: list[str] = []
    for field in schema["required_fields"]:
        if field not in trace:
            errors.append(f"missing field: {field}")

    module = require_mapping(trace.get("module"), "module", errors)
    for field in schema["required_module_fields"]:
        if field not in module:
            errors.append(f"missing module field: {field}")

    expected_value = require_mapping(trace.get("expected_value"), "expected_value", errors)
    for field in schema["required_expected_value_fields"]:
        if field not in expected_value:
            errors.append(f"missing expected_value field: {field}")
    expected_value_mode = expected_value.get("mode")
    if expected_value_mode not in schema["allowed_expected_value_modes"]:
        errors.append(f"expected_value.mode: unsupported value {expected_value_mode!r}")
    for field in (
        "target_artifact",
        "artifact_job",
        "output_bias",
        "source",
    ):
        if field in expected_value:
            require_optional_string(expected_value[field], f"expected_value.{field}", errors)
    for field in (
        "useful_when",
        "hard_constraints",
        "evidence_boundary",
        "unresolved_expected_value_items",
    ):
        if field in expected_value:
            require_list(expected_value[field], f"expected_value.{field}", errors)

    profile = require_mapping(trace.get("value_profile"), "value_profile", errors)
    for field in schema["required_value_profile_fields"]:
        if field not in profile:
            errors.append(f"missing value_profile field: {field}")
    profile_mode = profile.get("mode")
    if profile_mode not in schema["allowed_value_profile_modes"]:
        errors.append(f"value_profile.mode: unsupported value {profile_mode!r}")
    semantics = require_mapping(profile.get("value_semantics"), "value_profile.value_semantics", errors)
    for field in (
        "good_means",
        "bad_means",
        "priority_order",
        "derived_axes",
        "evidence_basis",
        "profile_veto_constraints",
    ):
        if field in semantics:
            require_list(semantics[field], f"value_profile.value_semantics.{field}", errors)
    for field in schema["required_value_semantics_fields"]:
        if field not in semantics:
            errors.append(f"missing value_profile.value_semantics field: {field}")
    for field in (
        "prompt_self_audit_questions",
        "image_self_audit_questions",
        "source_notes",
    ):
        if field in profile:
            require_list(profile[field], f"value_profile.{field}", errors)
    surface = profile.get("realization_surface")
    if surface is not None:
        surface = require_mapping(surface, "value_profile.realization_surface", errors)
        require_optional_string(surface.get("artifact_role"), "value_profile.realization_surface.artifact_role", errors)
        require_optional_string(surface.get("downstream_use"), "value_profile.realization_surface.downstream_use", errors)
        for field in (
            "observable_units",
            "granularity_pressure",
            "review_handles",
        ):
            if field in surface:
                require_list(surface[field], f"value_profile.realization_surface.{field}", errors)
    gain_policy = profile.get("gain_policy")
    if gain_policy is not None:
        gain_policy = require_mapping(gain_policy, "value_profile.gain_policy", errors)
        for field in (
            "preferred_moves",
            "discouraged_moves",
            "split_rules",
            "merge_rules",
            "density_guidance",
        ):
            if field in gain_policy:
                require_list(gain_policy[field], f"value_profile.gain_policy.{field}", errors)

    exit_gate = require_mapping(trace.get("exit_gate"), "exit_gate", errors)
    for field in schema["required_exit_gate_fields"]:
        if field not in exit_gate:
            errors.append(f"missing exit_gate field: {field}")
    gate_mode = exit_gate.get("mode")
    if gate_mode not in schema["allowed_exit_gate_modes"]:
        errors.append(f"exit_gate.mode: unsupported value {gate_mode!r}")
    for field in (
        "source",
        "module_responsibility",
        "downstream_use",
        "next_round_positive_value_check",
    ):
        if field in exit_gate:
            require_optional_string(exit_gate[field], f"exit_gate.{field}", errors)
    for field in (
        "hard_veto_checks",
        "value_profile_fit_checks",
        "downstream_use_checks",
        "evidence_boundary_checks",
        "exit_blockers",
        "unresolved_gate_items",
    ):
        if field in exit_gate:
            require_list(exit_gate[field], f"exit_gate.{field}", errors)

    debug_log = require_mapping(trace.get("debug_log"), "debug_log", errors)
    for field in schema["required_debug_log_fields"]:
        if field not in debug_log:
            errors.append(f"missing debug_log field: {field}")
    if "enabled" in debug_log:
        require_bool(debug_log["enabled"], "debug_log.enabled", errors)
    if "script_note" in debug_log:
        require_optional_string(debug_log["script_note"], "debug_log.script_note", errors)
    if "round_entries" in debug_log:
        round_entries = debug_log["round_entries"]
        require_list(round_entries, "debug_log.round_entries", errors)
        if isinstance(round_entries, list):
            for index, entry_value in enumerate(round_entries):
                entry_path = f"debug_log.round_entries[{index}]"
                entry = require_mapping(entry_value, entry_path, errors)
                for field in (
                    "round_id",
                    "input_summary",
                    "candidate_pool",
                    "value_axes_checked",
                    "gate_checks",
                    "veto_checks",
                    "next_round_positive_value_hypothesis",
                    "decision",
                    "decision_rationale",
                    "agent_judgment_required",
                ):
                    if field not in entry:
                        errors.append(f"missing {entry_path} field: {field}")
                for field in (
                    "round_id",
                    "input_summary",
                    "next_round_positive_value_hypothesis",
                    "decision_rationale",
                ):
                    if field in entry:
                        require_optional_string(entry[field], f"{entry_path}.{field}", errors)
                for field in ("value_axes_checked", "gate_checks", "veto_checks"):
                    if field in entry:
                        require_list(entry[field], f"{entry_path}.{field}", errors)
                if "agent_judgment_required" in entry:
                    require_bool(entry["agent_judgment_required"], f"{entry_path}.agent_judgment_required", errors)
                decision = entry.get("decision")
                if decision not in schema["debug_log_decisions"]:
                    errors.append(f"{entry_path}.decision: unsupported value {decision!r}")
                if "candidate_pool" in entry:
                    candidate_pool = entry["candidate_pool"]
                    require_list(candidate_pool, f"{entry_path}.candidate_pool", errors)
                    if isinstance(candidate_pool, list):
                        for candidate_index, candidate_value in enumerate(candidate_pool):
                            candidate_path = f"{entry_path}.candidate_pool[{candidate_index}]"
                            candidate = require_mapping(candidate_value, candidate_path, errors)
                            for field in ("id", "text", "status", "rationale"):
                                if field not in candidate:
                                    errors.append(f"missing {candidate_path} field: {field}")
                            for field in ("id", "text", "rationale"):
                                if field in candidate:
                                    require_optional_string(candidate[field], f"{candidate_path}.{field}", errors)
                            status = candidate.get("status")
                            if status not in schema["debug_log_candidate_statuses"]:
                                errors.append(f"{candidate_path}.status: unsupported value {status!r}")

    scoring = require_mapping(trace.get("value_gain_scoring_reference"), "value_gain_scoring_reference", errors)
    for field in schema["required_scoring_reference_fields"]:
        if field not in scoring:
            errors.append(f"missing value_gain_scoring_reference field: {field}")
    if "enabled" in scoring:
        require_bool(scoring["enabled"], "value_gain_scoring_reference.enabled", errors)
    if "script_note" in scoring:
        require_optional_string(scoring["script_note"], "value_gain_scoring_reference.script_note", errors)
    scale = require_mapping(scoring.get("scale"), "value_gain_scoring_reference.scale", errors)
    if scale.get("min") != 0:
        errors.append("value_gain_scoring_reference.scale.min: expected 0")
    if scale.get("max") != 5:
        errors.append("value_gain_scoring_reference.scale.max: expected 5")
    if "meaning" in scale:
        require_optional_string(scale["meaning"], "value_gain_scoring_reference.scale.meaning", errors)
    if "dimensions" in scoring:
        dimensions = scoring["dimensions"]
        require_list(dimensions, "value_gain_scoring_reference.dimensions", errors)
        if isinstance(dimensions, list):
            for index, dimension_value in enumerate(dimensions):
                dimension_path = f"value_gain_scoring_reference.dimensions[{index}]"
                dimension = require_mapping(dimension_value, dimension_path, errors)
                for field in (
                    "id",
                    "label",
                    "question",
                    "low_anchor",
                    "mid_anchor",
                    "high_anchor",
                ):
                    if field not in dimension:
                        errors.append(f"missing {dimension_path} field: {field}")
                    else:
                        require_optional_string(dimension[field], f"{dimension_path}.{field}", errors)
    if "round_scores" in scoring:
        round_scores = scoring["round_scores"]
        require_list(round_scores, "value_gain_scoring_reference.round_scores", errors)
        if isinstance(round_scores, list):
            for index, score_value in enumerate(round_scores):
                score_path = f"value_gain_scoring_reference.round_scores[{index}]"
                round_score = require_mapping(score_value, score_path, errors)
                for field in (
                    "round_id",
                    "dimension_scores",
                    "overall_reference_score",
                    "scoring_basis",
                    "agent_judgment_required",
                ):
                    if field not in round_score:
                        errors.append(f"missing {score_path} field: {field}")
                for field in ("round_id", "scoring_basis"):
                    if field in round_score:
                        require_optional_string(round_score[field], f"{score_path}.{field}", errors)
                if "overall_reference_score" in round_score:
                    require_score(round_score["overall_reference_score"], f"{score_path}.overall_reference_score", errors)
                if "agent_judgment_required" in round_score:
                    require_bool(round_score["agent_judgment_required"], f"{score_path}.agent_judgment_required", errors)
                if "dimension_scores" in round_score:
                    dimension_scores = round_score["dimension_scores"]
                    require_list(dimension_scores, f"{score_path}.dimension_scores", errors)
                    if isinstance(dimension_scores, list):
                        for dimension_index, dimension_score_value in enumerate(dimension_scores):
                            dimension_score_path = f"{score_path}.dimension_scores[{dimension_index}]"
                            dimension_score = require_mapping(dimension_score_value, dimension_score_path, errors)
                            for field in ("dimension_id", "score", "rationale"):
                                if field not in dimension_score:
                                    errors.append(f"missing {dimension_score_path} field: {field}")
                            if "dimension_id" in dimension_score:
                                require_optional_string(
                                    dimension_score["dimension_id"],
                                    f"{dimension_score_path}.dimension_id",
                                    errors,
                                )
                            if "score" in dimension_score:
                                require_score(dimension_score["score"], f"{dimension_score_path}.score", errors)
                            if "rationale" in dimension_score:
                                require_optional_string(
                                    dimension_score["rationale"],
                                    f"{dimension_score_path}.rationale",
                                    errors,
                                )

    pressure = require_mapping(trace.get("pressure"), "pressure", errors)
    for field in schema["required_pressure_fields"]:
        if field not in pressure:
            errors.append(f"missing pressure field: {field}")
    if "value" in pressure:
        require_int_range(pressure["value"], "pressure.value", 1, 5, errors)
    mode = pressure.get("mode")
    if mode not in schema["allowed_pressure_modes"]:
        errors.append(f"pressure.mode: unsupported value {mode!r}")
    for field in ("meaning", "typical_rounds", "script_note"):
        if field in pressure:
            require_optional_string(pressure[field], f"pressure.{field}", errors)
    if "exploration_passes" in pressure:
        require_list(pressure["exploration_passes"], "pressure.exploration_passes", errors)

    value_gain = require_mapping(trace.get("value_gain"), "value_gain", errors)
    for field in schema["required_value_gain_fields"]:
        if field not in value_gain:
            errors.append(f"missing value_gain field: {field}")
    if "value_gain_types" in value_gain:
        require_list(value_gain["value_gain_types"], "value_gain.value_gain_types", errors)
    if "selected_axes" in value_gain:
        require_list(value_gain["selected_axes"], "value_gain.selected_axes", errors)
    if "veto_constraints" in value_gain:
        require_list(value_gain["veto_constraints"], "value_gain.veto_constraints", errors)
    if "remaining_review_bound" in value_gain:
        require_list(value_gain["remaining_review_bound"], "value_gain.remaining_review_bound", errors)

    if "rounds" in trace:
        require_list(trace["rounds"], "rounds", errors)

    audit = require_mapping(trace.get("agentic_exit_audit"), "agentic_exit_audit", errors)
    for field in schema["required_audit_fields"]:
        if field not in audit:
            errors.append(f"missing agentic_exit_audit field: {field}")
    if "disagreements" in audit:
        require_list(audit["disagreements"], "agentic_exit_audit.disagreements", errors)
    audit_role = audit.get("audit_role")
    if audit_role not in schema["allowed_audit_roles"]:
        errors.append(f"agentic_exit_audit.audit_role: unsupported value {audit_role!r}")
    auditor_independence = audit.get("auditor_independence")
    if auditor_independence not in schema["allowed_auditor_independence"]:
        errors.append(f"agentic_exit_audit.auditor_independence: unsupported value {auditor_independence!r}")
    veto_result = audit.get("veto_constraint_result")
    if veto_result not in schema["allowed_veto_constraint_results"]:
        errors.append(f"agentic_exit_audit.veto_constraint_result: unsupported value {veto_result!r}")
    exit_state = audit.get("exit_state")
    if exit_state and exit_state not in schema["allowed_exit_states"]:
        errors.append(f"agentic_exit_audit.exit_state: unsupported value {exit_state!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TVG trace bookkeeping shape.")
    parser.add_argument("trace")
    args = parser.parse_args()

    trace_path = Path(args.trace)
    trace = load_json(trace_path)
    errors = validate(trace, load_schema(Path(__file__)))
    print("TVG Shape & Evidence Risk Report")
    print(f"Path: {trace_path}")
    print()
    if errors:
        print("schema_violations:")
        for error in errors:
            print(f"- {error}")
        print("script_result: schema issues found; agentic audit is still required after remediation")
        return 1

    print("No shape or evidence risks detected.")
    print(SCRIPT_DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
