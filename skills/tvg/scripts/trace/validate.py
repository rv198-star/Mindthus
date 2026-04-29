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


def validate(trace: dict, schema: dict) -> list[str]:
    errors: list[str] = []
    for field in schema["required_fields"]:
        if field not in trace:
            errors.append(f"missing field: {field}")

    module = require_mapping(trace.get("module"), "module", errors)
    for field in schema["required_module_fields"]:
        if field not in module:
            errors.append(f"missing module field: {field}")

    value_gain = require_mapping(trace.get("value_gain"), "value_gain", errors)
    for field in schema["required_value_gain_fields"]:
        if field not in value_gain:
            errors.append(f"missing value_gain field: {field}")
    if "value_gain_types" in value_gain:
        require_list(value_gain["value_gain_types"], "value_gain.value_gain_types", errors)
    if "selected_axes" in value_gain:
        require_list(value_gain["selected_axes"], "value_gain.selected_axes", errors)
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
    exit_state = audit.get("exit_state")
    if exit_state and exit_state not in schema["allowed_exit_states"]:
        errors.append(f"agentic_exit_audit.exit_state: unsupported value {exit_state!r}")

    script_support = require_mapping(trace.get("script_support"), "script_support", errors)
    for field in schema["required_script_support_fields"]:
        if field not in script_support:
            errors.append(f"missing script_support field: {field}")
    if "trace_boundary" in script_support:
        require_list(script_support["trace_boundary"], "script_support.trace_boundary", errors)
    if "script_cannot_decide" in script_support:
        require_list(script_support["script_cannot_decide"], "script_support.script_cannot_decide", errors)
    if script_support.get("trace_role") != schema["trace_role"]:
        errors.append(f"script_support.trace_role: expected {schema['trace_role']!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TVG trace bookkeeping shape.")
    parser.add_argument("trace")
    args = parser.parse_args()

    trace_path = Path(args.trace)
    trace = json.loads(trace_path.read_text())
    errors = validate(trace, load_schema(Path(__file__)))
    if errors:
        print("schema_violations:")
        for error in errors:
            print(f"- {error}")
        print("script_result: schema issues found; agentic audit is still required after remediation")
        return 1

    print(SCRIPT_DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
