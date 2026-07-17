#!/usr/bin/env python3
"""Validate, freeze, and verify the evidence-honest Codex protocol v0.4."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
V03_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.3.py"
DEFAULT_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
DEFAULT_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.lock.json"
EXPECTED_DEPENDENCIES = {
    "visible_protocol_v03_validator",
    "telemetry_builder",
    "codex_stream_capture",
    "codex_hook_probe",
    "real_arm_materializer",
    "real_evaluation_runner_v04",
    "real_evaluation_analyzer_v04",
    "judge_output_schema_v04",
    "judge_rubric_v04",
    "dry_run_plan_schema_v04",
    "dry_run_fixture_builder",
    "dry_run_orchestrator",
}
EXPECTED_PRIMARY_IDS = {
    "quality_noninferiority_vs_stable",
    "execution_owner_fidelity_vs_stable",
    "primitive_recall_kernel_benefit",
    "joint_owner_primitive_kernel_benefit",
    "false_wakeup_harm_vs_stable",
    "passive_kernel_session_start_injection_fidelity",
    "input_token_savings_vs_stable",
    "kernel_token_overhead_vs_direct",
    "wall_time_savings_vs_stable",
    "first_observable_action_latency",
}


def load_v03_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mindthus_beta2_protocol_v03_validator", V03_VALIDATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.3 validator: {V03_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V03 = load_v03_validator()
BASE = V03.BASE
ProtocolError = V03.ProtocolError


def _v03_compatibility_view(protocol: Mapping[str, Any]) -> dict[str, Any]:
    compatibility = copy.deepcopy(protocol)
    compatibility["protocol_version"] = "0.3"
    compatibility["freeze"]["semantic_model_output_generated_before_freeze"] = False
    authorization = compatibility["authorization_parameters"]
    proposed = authorization["proposed_authorization"]
    proposed["maximum_generation_calls"] = 240
    proposed["maximum_judge_calls"] = 480
    proposed["token_or_cost_budget"]["maximum"] = 22000000
    return compatibility


def _evidence(endpoint: Mapping[str, Any]) -> dict[str, set[str]]:
    return {
        str(item["endpoint"]): set(item["allowed_provenance"])
        for item in endpoint["required_evidence"]
    }


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    V03.validate_protocol(_v03_compatibility_view(protocol))
    if protocol.get("protocol_version") != "0.4" or protocol.get("status") != "frozen":
        raise ProtocolError("protocol version/status is not frozen v0.4")
    dependencies = BASE._validate_dependencies(protocol)
    if not EXPECTED_DEPENDENCIES.issubset(dependencies):
        raise ProtocolError(
            f"v0.4 runtime dependency gaps: {sorted(EXPECTED_DEPENDENCIES - set(dependencies))}"
        )
    BASE._validate_endpoints(protocol)
    primary = {item["id"]: item for item in protocol["primary_endpoints"]}
    if set(primary) != EXPECTED_PRIMARY_IDS:
        raise ProtocolError("v0.4 primary endpoint set differs")
    timing = primary["first_observable_action_latency"]
    if _evidence(timing) != {
        "first_observable_action_latency_seconds": {"deterministic"}
    }:
        raise ProtocolError("v0.4 observable timing provenance differs")
    lifecycle = primary["passive_kernel_session_start_injection_fidelity"]
    if _evidence(lifecycle) != {
        "arm.hook_observation_receipt": {"deterministic"},
        "hook_state": {"native"},
        "lifecycle_event": {"native"},
    }:
        raise ProtocolError("v0.4 SessionStart evidence contract differs")
    secondary = {item["id"]: item for item in protocol["secondary_endpoints"]}
    if "native_first_useful_action_latency" not in secondary:
        raise ProtocolError("v0.4 must retain native first-useful timing as secondary")
    if secondary["native_first_useful_action_latency"]["missing_policy"] != "block-endpoint":
        raise ProtocolError("native first-useful timing must remain unknown rather than veto")
    if "nonstartup_lifecycle_scenario_behavior" not in secondary:
        raise ProtocolError("v0.4 nonstartup lifecycle claim boundary is missing")

    design = protocol["execution_design"]
    if design.get("timing_contract", {}).get("substitution") != "forbidden":
        raise ProtocolError("v0.4 timing substitution is not forbidden")
    lifecycle_scope = design.get("host_lifecycle_scope", {})
    if lifecycle_scope.get("real_model_session_mode") != "startup-only":
        raise ProtocolError("v0.4 real lifecycle scope differs")
    if "without hook-trust bypass" not in str(
        lifecycle_scope.get("direct_only_kernel_absence")
    ):
        raise ProtocolError("v0.4 direct-only negative hook proof is missing")
    if lifecycle_scope.get("nonstartup_host_fidelity_claim") != "forbidden":
        raise ProtocolError("v0.4 nonstartup host claim is not forbidden")
    prior = design.get("prior_protocol_output_accounting", {})
    if prior != {
        "protocol_version": "0.3",
        "protocol_sha256": "ce8c06eb0656e1023de9ff477ab7a0b5a3302194e9e5af952b916130a231b144",
        "cell_record_digest": "c3f4964fb5eb992f867d781afac0a037409d4ce8708515479d820d2ee40d85ad",
        "generation_calls": 1,
        "judge_calls": 0,
        "counted_tokens": 48256,
        "retention": "retained and excluded from v0.4 analysis",
        "same_case_new_cell_rule": (
            "allowed only under the distinct v0.4 protocol digest because the measurement "
            "contract changed; the v0.3 output is never replaced"
        ),
    }:
        raise ProtocolError("v0.4 prior output accounting differs")

    authorization = protocol["authorization_parameters"]
    proposed = authorization["proposed_authorization"]
    if authorization.get("planned_generation_outputs") != 225:
        raise ProtocolError("v0.4 planned generation cardinality differs")
    if authorization.get("planned_judge_records") != 450:
        raise ProtocolError("v0.4 planned judge cardinality differs")
    if proposed.get("maximum_generation_calls") != 239:
        raise ProtocolError("v0.4 generation budget does not debit v0.3")
    if proposed.get("maximum_judge_calls") != 480:
        raise ProtocolError("v0.4 judge budget differs")
    if proposed.get("token_or_cost_budget", {}).get("maximum") != 21951744:
        raise ProtocolError("v0.4 token budget does not debit v0.3")
    cumulative = authorization.get("cumulative_authority", {})
    if cumulative.get("maximum_generation_calls") != 240:
        raise ProtocolError("v0.4 cumulative generation authority differs")
    if cumulative.get("maximum_judge_calls") != 480:
        raise ProtocolError("v0.4 cumulative judge authority differs")
    if cumulative.get("aggregate_token_ceiling") != 22000000:
        raise ProtocolError("v0.4 cumulative token authority differs")
    if cumulative.get("budget_expansion") is not False:
        raise ProtocolError("v0.4 expands the authorized budget")
    if proposed.get("human_adjudicator") != "William" or proposed.get("stop_authority") != "William":
        raise ProtocolError("v0.4 human authority differs")
    freeze = protocol["freeze"]
    if freeze.get("semantic_model_output_generated_before_freeze") is not True:
        raise ProtocolError("v0.4 does not disclose the retained v0.3 semantic output")
    if freeze.get("semantic_model_output_generated_under_v0_4_before_freeze") is not False:
        raise ProtocolError("semantic output occurred under v0.4 before freeze")
    if "one retained v0.3 output" not in str(freeze.get("prior_semantic_output_scope")):
        raise ProtocolError("v0.4 prior semantic-output scope is missing")
    if not BASE._git_ancestor(str(protocol["freeze"].get("source_parent_commit"))):
        raise ProtocolError("v0.4 source parent is not an ancestor")
    workload = protocol["workload"]
    planned = len(workload["matched_case_ids"]) * len(protocol["arms"]) * workload[
        "planned_repeats"
    ]
    return {
        "status": "protocol-valid",
        "protocol_id": protocol["protocol_id"],
        "protocol_version": "0.4",
        "dependency_count": len(dependencies),
        "primary_endpoint_count": len(protocol["primary_endpoints"]),
        "secondary_endpoint_count": len(protocol["secondary_endpoints"]),
        "matched_case_count": len(workload["matched_case_ids"]),
        "planned_generation_cells": planned,
        "planned_judge_records": planned * 2,
        "claim_ceiling": "visible-case Codex startup-session exploratory evidence only",
    }


def lock_payload(protocol_path: Path, protocol: Mapping[str, Any]) -> dict[str, Any]:
    validator_path = Path(__file__).resolve()
    base = {
        "schema_version": "mindthus-beta2-protocol-lock-v0.1",
        "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["protocol_version"],
        "protocol_path": BASE._display_path(protocol_path),
        "protocol_sha256": BASE.sha256_file(protocol_path),
        "dependency_receipts": [
            {"id": item["id"], "path": item["path"], "sha256": item["sha256"]}
            for item in protocol["dependencies"]
        ],
        "arm_ids": [item["arm_id"] for item in protocol["arms"]],
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_parent_commit": protocol["freeze"]["source_parent_commit"],
        "semantic_model_output_generated_before_freeze": True,
        "semantic_model_output_generated_under_v0_4_before_freeze": False,
        "validator_path": BASE._display_path(validator_path),
        "validator_sha256": BASE.sha256_file(validator_path),
    }
    base["lock_digest"] = BASE.canonical_sha256(base)
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "freeze", "validate"):
        child = subparsers.add_parser(command)
        child.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
        child.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()
    try:
        protocol = BASE.load_json(args.protocol)
        report = validate_protocol(protocol)
        if args.command == "freeze":
            if args.lock.exists():
                raise ProtocolError(
                    "lock already exists; frozen v0.4 cannot be overwritten—create a new protocol version"
                )
            BASE.write_atomic_json(args.lock, lock_payload(args.protocol, protocol))
            report = BASE.validate_lock(args.protocol, protocol, args.lock)
        elif args.command == "validate":
            report = BASE.validate_lock(args.protocol, protocol, args.lock)
    except (
        OSError,
        json.JSONDecodeError,
        ProtocolError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"protocol {args.command} failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
