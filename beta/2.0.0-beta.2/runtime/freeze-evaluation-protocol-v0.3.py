#!/usr/bin/env python3
"""Validate, freeze, and verify the visible-case Codex protocol v0.3."""

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
V02_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.2.py"
DEFAULT_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.3.json"
DEFAULT_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.3.lock.json"
EXPECTED_MODEL = {"model_id": "gpt-5.6-sol", "reasoning_effort": "xhigh"}
SEALED_CASE_IDS = (
    "b2-shadow-owner-overlap",
    "b2-shadow-passive-intersection",
    "b2-shadow-anti-rename",
    "b2-shadow-near-negative",
)
REPLAY_CASE_IDS = (
    "b2-replay-architecture-review",
    "b2-replay-debugging-session",
)


def load_v02_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mindthus_beta2_protocol_v02_validator", V02_VALIDATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.2 protocol validator: {V02_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V02 = load_v02_validator()
BASE = V02.BASE
ProtocolError = V02.ProtocolError


def _v02_compatibility_view(protocol: Mapping[str, Any]) -> dict[str, Any]:
    compatibility = copy.deepcopy(protocol)
    compatibility["protocol_version"] = "0.2"
    workload = compatibility["workload"]
    matrix = BASE.load_json(
        BASE._repo_path(
            next(
                item["path"]
                for item in compatibility["dependencies"]
                if item["id"] == "case_matrix_fixture"
            )
        )
    )
    compatibility["workload"]["matched_case_ids"] = [
        case["case_id"]
        for case in matrix["cases"]
        if case["source"]["run_eligibility"] != "requires-user-authorization"
    ]
    workload["excluded_case_ids"] = list(REPLAY_CASE_IDS)
    design = compatibility["execution_design"]
    design["sealed_case_custodian_attestation_required"] = True
    design["sealed_receipt_binding_timing"] = (
        "after protocol freeze and before #119 authorization"
    )
    authorization = compatibility["authorization_parameters"]
    authorization["planned_generation_outputs"] = 261
    authorization["planned_judge_records"] = 522
    proposed = authorization["proposed_authorization"]
    proposed["maximum_generation_calls"] = 276
    proposed["maximum_judge_calls"] = 552
    proposed["token_or_cost_budget"]["maximum"] = 25000000
    return compatibility


def _validate_visible_case_amendment(protocol: Mapping[str, Any]) -> None:
    if protocol.get("protocol_version") != "0.3" or protocol.get("status") != "frozen":
        raise ProtocolError("protocol version/status is not the frozen v0.3 contract")

    dependencies = {item.get("id"): item for item in protocol.get("dependencies", [])}
    if "codex_protocol_v02_validator" not in dependencies:
        raise ProtocolError("v0.3 must seal the imported v0.2 validator as a dependency")

    workload = protocol.get("workload", {})
    matrix_dependency = dependencies.get("case_matrix_fixture", {})
    matrix = BASE.load_json(BASE._repo_path(str(matrix_dependency.get("path") or "")))
    eligible = [
        case["case_id"]
        for case in matrix["cases"]
        if case["source"]["run_eligibility"] == "eligible"
    ]
    if workload.get("matched_case_ids") != eligible or len(eligible) != 25:
        raise ProtocolError("v0.3 matched workload must be exactly the 25 visible eligible cases")
    if set(workload.get("excluded_case_ids", [])) != {
        *SEALED_CASE_IDS,
        *REPLAY_CASE_IDS,
    }:
        raise ProtocolError("v0.3 exclusions must be exactly four sealed cases and two replays")
    if workload.get("evidence_visibility") != "implementation-visible":
        raise ProtocolError("v0.3 visible-case evidence boundary is missing")
    if workload.get("hidden_generalization_claim") != "forbidden":
        raise ProtocolError("v0.3 does not forbid hidden-set generalization claims")

    design = protocol.get("execution_design", {})
    if design.get("sealed_case_custodian_attestation_required") is not False:
        raise ProtocolError("v0.3 must not require a custodian for excluded sealed cases")
    if design.get("sealed_receipt_binding_timing") != (
        "not-applicable: all sealed-shadow cases are excluded"
    ):
        raise ProtocolError("v0.3 sealed-case exclusion rationale differs")
    if not design.get("visible_case_evidence_limitation"):
        raise ProtocolError("v0.3 visible-case claim limitation is missing")

    authorization = protocol.get("authorization_parameters", {})
    if authorization.get("planned_generation_outputs") != 225:
        raise ProtocolError("v0.3 generation output cardinality differs")
    if authorization.get("planned_judge_records") != 450:
        raise ProtocolError("v0.3 judge record cardinality differs")
    if authorization.get("delegated_digest_binding_allowed") is not True:
        raise ProtocolError("v0.3 delegated digest binding authority is unresolved")
    proposed = authorization.get("proposed_authorization", {})
    generator = proposed.get("generator_model_by_host", {}).get("codex-plugin", {})
    if {key: generator.get(key) for key in EXPECTED_MODEL} != EXPECTED_MODEL:
        raise ProtocolError("v0.3 generator differs from Sol xHigh")
    if generator.get("codex_cli_version") != "0.144.4":
        raise ProtocolError("v0.3 Codex CLI version differs")
    judge = proposed.get("judge_model_and_reasoning", {})
    if {key: judge.get(key) for key in EXPECTED_MODEL} != EXPECTED_MODEL:
        raise ProtocolError("v0.3 judge differs from Sol xHigh")
    if judge.get("independent_sessions_per_output") != 2:
        raise ProtocolError("v0.3 requires two isolated judge sessions per output")
    if proposed.get("maximum_generation_calls") != 240:
        raise ProtocolError("v0.3 generation call ceiling differs")
    if proposed.get("maximum_judge_calls") != 480:
        raise ProtocolError("v0.3 judge call ceiling differs")
    token_budget = proposed.get("token_or_cost_budget", {})
    if token_budget.get("kind") != "aggregate-token-ceiling":
        raise ProtocolError("v0.3 token budget kind differs")
    if token_budget.get("maximum") != 22000000:
        raise ProtocolError("v0.3 aggregate token ceiling differs")
    if token_budget.get("counted_components") != ["input", "output", "reasoning"]:
        raise ProtocolError("v0.3 token budget components differ")
    if token_budget.get("cached_input_double_counted") is not False:
        raise ProtocolError("v0.3 cached input accounting differs")
    if proposed.get("human_adjudicator") != "William":
        raise ProtocolError("v0.3 human adjudicator differs")
    if proposed.get("stop_authority") != "William":
        raise ProtocolError("v0.3 stop authority differs")


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    V02.validate_protocol(_v02_compatibility_view(protocol))
    _validate_visible_case_amendment(protocol)
    workload = protocol["workload"]
    planned_generation_cells = (
        len(workload["matched_case_ids"])
        * len(protocol["arms"])
        * len(workload["host_surfaces"])
        * workload["planned_repeats"]
    )
    return {
        "status": "protocol-valid",
        "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["protocol_version"],
        "dependency_count": len(protocol["dependencies"]),
        "primary_endpoint_count": len(protocol["primary_endpoints"]),
        "secondary_endpoint_count": len(protocol["secondary_endpoints"]),
        "matched_case_count": len(workload["matched_case_ids"]),
        "excluded_sealed_case_count": len(SEALED_CASE_IDS),
        "supported_surfaces": list(workload["host_surfaces"]),
        "planned_generation_cells": planned_generation_cells,
        "planned_judge_records": (
            planned_generation_cells
            * protocol["execution_design"]["judge_count_per_output"]
        ),
        "claim_ceiling": "visible-case exploratory evidence only",
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
        "semantic_model_output_generated_before_freeze": False,
        "validator_path": BASE._display_path(validator_path),
        "validator_sha256": BASE.sha256_file(validator_path),
    }
    base["lock_digest"] = BASE.canonical_sha256(base)
    return base


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "freeze", "validate"):
        child = subparsers.add_parser(command)
        child.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
        child.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        protocol = BASE.load_json(args.protocol)
        report = validate_protocol(protocol)
        if args.command == "freeze":
            if args.lock.exists():
                raise ProtocolError(
                    "lock already exists; frozen v0.3 cannot be overwritten—create a new protocol version"
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
