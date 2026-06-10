#!/usr/bin/env python3
"""Validate Thinking Value-Gain trace bookkeeping shape.

This script does not judge whether the trace is valuable, true, or ready to exit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCRIPT_DISCLAIMER = "No schema violations were detected; agentic audit is still required."


def load_schema(script_path: Path) -> dict:
    return json.loads((script_path.parents[2] / "resources" / "trace-record-schema.json").read_text())


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
    trace = json.loads(trace_path.read_text())
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
