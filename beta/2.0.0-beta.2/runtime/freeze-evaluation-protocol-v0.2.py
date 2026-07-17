#!/usr/bin/env python3
"""Validate, freeze, and verify the Codex-only Beta.2 protocol v0.2."""

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
REPO_ROOT = BETA_ROOT.parents[1]
BASE_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol.py"
DEFAULT_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.2.json"
DEFAULT_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.2.lock.json"
EXPECTED_MODEL = {"model_id": "gpt-5.6-sol", "reasoning_effort": "xhigh"}


def load_base_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mindthus_beta2_protocol_v01_validator", BASE_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base protocol validator: {BASE_VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base_validator()
ProtocolError = BASE.ProtocolError


def _validate_codex_amendment(protocol: Mapping[str, Any]) -> None:
    if protocol.get("protocol_version") != "0.2" or protocol.get("status") != "frozen":
        raise ProtocolError("protocol version/status is not the frozen v0.2 contract")
    workload = protocol.get("workload", {})
    if workload.get("host_surfaces") != ["codex-plugin"]:
        raise ProtocolError("v0.2 must contain exactly the Codex host stratum")
    design = protocol.get("execution_design", {})
    if design.get("supported_result_surface") != "codex-plugin":
        raise ProtocolError("Codex result-surface boundary is missing")
    if design.get("cross_host_generalization") != "forbidden":
        raise ProtocolError("cross-host generalization is not forbidden")
    endpoint_text = json.dumps(
        [*protocol.get("primary_endpoints", []), *protocol.get("secondary_endpoints", [])],
        ensure_ascii=False,
    )
    if "in each host" in endpoint_text or "each host and overall" in endpoint_text:
        raise ProtocolError("v0.2 endpoint language still implies multiple host strata")
    dependencies = {item.get("id"): item for item in protocol.get("dependencies", [])}
    if "base_protocol_validator" not in dependencies:
        raise ProtocolError("v0.2 must seal the imported v0.1 validator as a dependency")

    auth = protocol.get("authorization_parameters", {})
    if auth.get("authorized_host_surface") != "codex-plugin":
        raise ProtocolError("authorization host differs from the frozen workload")
    if auth.get("planned_generation_outputs") != 261 or auth.get("planned_judge_records") != 522:
        raise ProtocolError("Codex-only output cardinality is not frozen")
    proposed = auth.get("proposed_authorization", {})
    generator = proposed.get("generator_model_by_host", {}).get("codex-plugin", {})
    if {key: generator.get(key) for key in EXPECTED_MODEL} != EXPECTED_MODEL:
        raise ProtocolError("generator model/reasoning differs from the authorized Sol xHigh choice")
    if generator.get("codex_cli_version") != "0.144.4":
        raise ProtocolError("Codex CLI version differs from the preregistered runtime")
    judge = proposed.get("judge_model_and_reasoning", {})
    if {key: judge.get(key) for key in EXPECTED_MODEL} != EXPECTED_MODEL:
        raise ProtocolError("judge model/reasoning differs from the authorized Sol xHigh choice")
    if judge.get("independent_sessions_per_output") != 2:
        raise ProtocolError("two independent judge sessions are required")
    if proposed.get("maximum_generation_calls") != 276:
        raise ProtocolError("generation call ceiling differs from the authorized value")
    if proposed.get("maximum_judge_calls") != 552:
        raise ProtocolError("judge call ceiling differs from the authorized value")
    token_budget = proposed.get("token_or_cost_budget", {})
    if token_budget.get("kind") != "aggregate-token-ceiling" or token_budget.get("maximum") != 25000000:
        raise ProtocolError("aggregate token ceiling differs from the authorized value")
    if token_budget.get("counted_components") != ["input", "output", "reasoning"]:
        raise ProtocolError("token budget components are ambiguous or mutable")
    if token_budget.get("cached_input_double_counted") is not False:
        raise ProtocolError("cached input must not be double-counted in the token ceiling")
    if proposed.get("human_adjudicator") != "William" or proposed.get("stop_authority") != "William":
        raise ProtocolError("human adjudication or stop authority is unresolved")


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    compatibility_view = copy.deepcopy(protocol)
    compatibility_view["protocol_version"] = "0.1"
    compatibility_view["workload"]["host_surfaces"] = ["codex-plugin", "claude-plugin"]
    BASE.validate_protocol(compatibility_view)
    _validate_codex_amendment(protocol)
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
        "supported_surfaces": list(workload["host_surfaces"]),
        "planned_generation_cells": planned_generation_cells,
        "planned_judge_records": planned_generation_cells
        * protocol["execution_design"]["judge_count_per_output"],
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
                    "lock already exists; frozen v0.2 cannot be overwritten—create a new protocol version"
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
