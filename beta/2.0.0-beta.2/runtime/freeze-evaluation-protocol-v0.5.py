#!/usr/bin/env python3
"""Validate, freeze, and verify incremental isolated protocol v0.5."""

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
V04_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.4.py"
V04_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
DEFAULT_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json"
DEFAULT_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.lock.json"
EXPECTED_DEPENDENCIES = {
    "visible_protocol_v04_validator",
    "filesystem_isolation_v05",
    "real_arm_materializer_v05",
    "real_evaluation_runner_v05",
    "incremental_analyzer_v05",
    "incremental_dry_run_v05",
}


def load_v04() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mindthus_beta2_protocol_v04_validator", V04_VALIDATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load v0.4 protocol validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V04 = load_v04()
BASE = V04.BASE
ProtocolError = V04.ProtocolError


def _v04_compatibility_view(protocol: Mapping[str, Any]) -> dict[str, Any]:
    compatibility = copy.deepcopy(protocol)
    frozen_v04 = BASE.load_json(V04_PROTOCOL)
    compatibility["protocol_version"] = "0.4"
    compatibility["authorization_parameters"] = copy.deepcopy(
        frozen_v04["authorization_parameters"]
    )
    compatibility["freeze"] = copy.deepcopy(frozen_v04["freeze"])
    compatibility["execution_design"]["prior_protocol_output_accounting"] = copy.deepcopy(
        frozen_v04["execution_design"]["prior_protocol_output_accounting"]
    )
    return compatibility


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    V04.validate_protocol(_v04_compatibility_view(protocol))
    if protocol.get("protocol_version") != "0.5" or protocol.get("status") != "frozen":
        raise ProtocolError("protocol version/status is not frozen v0.5")
    dependencies = BASE._validate_dependencies(protocol)
    if not EXPECTED_DEPENDENCIES.issubset(dependencies):
        raise ProtocolError(
            f"v0.5 runtime dependency gaps: {sorted(EXPECTED_DEPENDENCIES - set(dependencies))}"
        )
    design = protocol["execution_design"]
    batch = design.get("incremental_batch_control", {})
    if batch.get("batch_unit") != "case_id/repeat three-arm triplet":
        raise ProtocolError("v0.5 batch unit differs")
    if (
        batch.get("batch_count") != 75
        or batch.get("generation_outputs_per_batch") != 3
        or batch.get("judge_records_per_batch") != 6
    ):
        raise ProtocolError("v0.5 batch cardinality differs")
    if batch.get("order") != [
        "generate-three-arms",
        "verify-three-filesystem-isolation-receipts",
        "judge-each-output-in-two-isolated-sessions",
        "write-one-hash-chained-atomic-batch-commit",
        "advance-to-next-batch",
    ]:
        raise ProtocolError("v0.5 control order differs")
    if "only this record" not in str(batch.get("counting_rule")):
        raise ProtocolError("v0.5 commit counting rule is missing")
    if "exclude" not in str(batch.get("partial_batch_rule")):
        raise ProtocolError("v0.5 partial batch rule is missing")

    isolation = design.get("filesystem_isolation", {})
    if isolation.get("command_string_as_access_proof") != "forbidden":
        raise ProtocolError("v0.5 still treats command strings as access proof")
    if isolation.get("staging_policy") != (
        "builder package staging is deleted before any semantic model call"
    ):
        raise ProtocolError("v0.5 staging policy differs")
    if isolation.get("pre_call_probes") != [
        "positive-own-root-read",
        "negative-evaluation-control-read",
        "negative-other-arm-read",
        "negative-parent-traversal-read",
        "negative-symlink-escape-read",
    ]:
        raise ProtocolError("v0.5 native probe set differs")

    prior = design.get("v05_prior_output_accounting", {})
    if prior.get("v04_protocol_sha256") != (
        "a6e9da7ef2eb85e179d92ec909444c50e879673943b1be71f5c923b9e26d0746"
    ):
        raise ProtocolError("v0.5 prior protocol digest differs")
    if (
        prior.get("v03_and_v04_generation_attempts") != 146
        or prior.get("v04_judge_attempts") != 42
        or prior.get("v03_and_v04_counted_tokens") != 8_133_510
        or prior.get("v04_valid_comparison_records") != 0
    ):
        raise ProtocolError("v0.5 prior consumption differs")

    workload = protocol["workload"]
    if (
        workload.get("incremental_batch_count") != 75
        or workload.get("smoke_batch_count") != 5
        or workload.get("batch_generation_outputs") != 3
        or workload.get("batch_judge_records") != 6
    ):
        raise ProtocolError("v0.5 workload batch shape differs")
    authorization = protocol["authorization_parameters"]
    proposed = authorization["proposed_authorization"]
    if authorization.get("fresh_authorization_required") is not True:
        raise ProtocolError("v0.5 fresh authorization gate is missing")
    if authorization.get("delegated_digest_binding_allowed") is not False:
        raise ProtocolError("v0.4 delegated authority leaked into v0.5")
    if (
        proposed.get("maximum_committed_batches") != 75
        or proposed.get("maximum_generation_calls") != 239
        or proposed.get("maximum_judge_calls") != 480
        or proposed.get("token_or_cost_budget", {}).get("maximum") != 22_000_000
    ):
        raise ProtocolError("v0.5 full ceiling differs")
    initial = authorization.get("initial_batch_authorization_recommendation", {})
    if initial != {
        "maximum_committed_batches": 5,
        "maximum_generation_calls": 17,
        "maximum_judge_calls": 34,
        "aggregate_token_ceiling": 3_000_000,
        "result": "five Judge-backed smoke triplets, not an architecture conclusion",
        "continuation": "a later authorization may raise the batch ceiling under the same frozen protocol after reviewing committed evidence",
    }:
        raise ProtocolError("v0.5 initial authorization recommendation differs")
    cumulative = authorization.get("cumulative_authority", {})
    if cumulative.get("prior_consumption") != {
        "protocol_versions": ["0.3", "0.4"],
        "generation_calls": 146,
        "judge_calls": 42,
        "counted_tokens": 8_133_510,
    }:
        raise ProtocolError("v0.5 cumulative prior consumption differs")
    if cumulative.get("budget_expansion") is not True or cumulative.get(
        "authorization_state"
    ) != "pending-human-choice":
        raise ProtocolError("v0.5 expanded budget is not explicitly pending")

    veto_ids = {item["id"] for item in protocol["vetoes"]}
    if not {
        "filesystem-isolation-unavailable",
        "incremental-batch-integrity-failure",
    }.issubset(veto_ids):
        raise ProtocolError("v0.5 veto set is incomplete")
    freeze = protocol["freeze"]
    if freeze.get("semantic_model_output_generated_under_v0_5_before_freeze") is not False:
        raise ProtocolError("semantic output occurred under v0.5 before freeze")
    if "v0.3 and v0.4 artifacts" not in str(freeze.get("prior_semantic_output_scope")):
        raise ProtocolError("v0.5 prior semantic-output disclosure differs")
    if not BASE._git_ancestor(str(freeze.get("source_parent_commit"))):
        raise ProtocolError("v0.5 source parent is not an ancestor")
    return {
        "status": "protocol-valid",
        "protocol_id": protocol["protocol_id"],
        "protocol_version": "0.5",
        "dependency_count": len(dependencies),
        "matched_case_count": len(workload["matched_case_ids"]),
        "planned_batches": 75,
        "planned_generation_cells": 225,
        "planned_judge_records": 450,
        "initial_authorization_batches": 5,
        "claim_ceiling": "visible-case Codex startup-session exploratory evidence only; partial commits are descriptive",
    }


def lock_payload(protocol_path: Path, protocol: Mapping[str, Any]) -> dict[str, Any]:
    validator_path = Path(__file__).resolve()
    payload: dict[str, Any] = {
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
        "semantic_model_output_generated_under_v0_5_before_freeze": False,
        "validator_path": BASE._display_path(validator_path),
        "validator_sha256": BASE.sha256_file(validator_path),
    }
    payload["lock_digest"] = BASE.canonical_sha256(payload)
    return payload


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
                    "lock already exists; frozen v0.5 cannot be overwritten—create a new protocol version"
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
