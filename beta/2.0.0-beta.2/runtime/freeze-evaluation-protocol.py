#!/usr/bin/env python3
"""Validate, freeze, and verify the Mindthus Beta.2 evaluation protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
DEFAULT_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.1.json"
DEFAULT_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.1.lock.json"
VALID_PROVENANCE = {"native", "deterministic", "judge-inferred", "self-reported", "unavailable"}
REQUIRED_ARMS = {"stable", "direct-only", "thin-kernel"}
REQUIRED_DOMAINS = {
    "quality",
    "execution-owner-fidelity",
    "primitive-recall",
    "primitive-precision",
    "joint-owner-primitive",
    "false-wakeup",
    "lifecycle",
    "efficiency",
    "user-visible-interaction-cost",
}
REQUIRED_VETOES = {
    "cross-arm-contamination",
    "protocol-or-arm-drift",
    "untraceable-or-partial-artifact",
    "missing-primary-native-evidence",
    "judge-environment-contamination",
    "systematic-critical-primitive-miss",
    "authority-or-evidence-regression",
    "insufficient-kernel-benefit",
    "negligible-efficiency-savings",
}
REQUIRED_AUTHORIZATION_FIELDS = {
    "protocol_digest",
    "generator_model_by_host",
    "judge_model_and_reasoning",
    "maximum_generation_calls",
    "maximum_judge_calls",
    "token_or_cost_budget",
    "stop_authority",
}


class ProtocolError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _unique_ids(items: Iterable[Mapping[str, Any]], label: str) -> set[str]:
    values = [str(item.get("id") or "") for item in items]
    if any(not value for value in values) or len(values) != len(set(values)):
        raise ProtocolError(f"{label} ids must be present and unique")
    return set(values)


def _repo_path(relative: str) -> Path:
    path = (REPO_ROOT / relative).resolve(strict=False)
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ProtocolError(f"dependency leaves repository: {relative}") from exc
    return path


def _validate_dependencies(protocol: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    dependencies = protocol.get("dependencies")
    if not isinstance(dependencies, list) or len(dependencies) < 6:
        raise ProtocolError("protocol must reference accepted arm/scoring/telemetry/case contracts")
    ids = _unique_ids(dependencies, "dependency")
    required = {
        "protocol_schema",
        "protocol_lock_schema",
        "arm_definitions",
        "arm_manifest_schema",
        "scoring_case_schema",
        "scoring_contract",
        "telemetry_schema",
        "case_matrix_schema",
        "case_matrix_fixture",
    }
    if not required.issubset(ids):
        raise ProtocolError(f"missing dependency receipts: {sorted(required - ids)}")
    by_id: dict[str, Mapping[str, Any]] = {}
    for item in dependencies:
        identifier = str(item["id"])
        relative = str(item.get("path") or "")
        path = _repo_path(relative)
        if not path.is_file():
            raise ProtocolError(f"dependency does not exist: {relative}")
        observed = sha256_file(path)
        if item.get("sha256") != observed:
            raise ProtocolError(f"dependency drift: {identifier}")
        by_id[identifier] = item
    return by_id


def _validate_endpoints(protocol: Mapping[str, Any]) -> None:
    primary = protocol.get("primary_endpoints")
    secondary = protocol.get("secondary_endpoints")
    if not isinstance(primary, list) or not primary:
        raise ProtocolError("primary endpoints are unresolved or empty")
    if not isinstance(secondary, list) or not secondary:
        raise ProtocolError("secondary endpoints are unresolved or empty")
    primary_ids = _unique_ids(primary, "primary endpoint")
    secondary_ids = _unique_ids(secondary, "secondary endpoint")
    if primary_ids & secondary_ids:
        raise ProtocolError("primary and secondary endpoint ids overlap")
    domains = {str(item.get("domain")) for item in [*primary, *secondary]}
    if not REQUIRED_DOMAINS.issubset(domains):
        raise ProtocolError(f"endpoint domain gaps: {sorted(REQUIRED_DOMAINS - domains)}")
    if "composite" in domains:
        raise ProtocolError("quality, behavior, efficiency, and UX may not use a composite endpoint")

    for item in primary:
        identifier = item.get("id")
        if item.get("status") != "resolved":
            raise ProtocolError(f"unresolved primary endpoint: {identifier}")
        margin = item.get("margin")
        if not isinstance(margin, Mapping):
            raise ProtocolError(f"primary endpoint has no margin: {identifier}")
        if not isinstance(margin.get("value"), (int, float)) or not margin.get("kind") or not margin.get("unit"):
            raise ProtocolError(f"primary endpoint margin is incomplete: {identifier}")
        if item.get("missing_policy") != "veto":
            raise ProtocolError(f"primary endpoint must veto on missing evidence: {identifier}")
        if not item.get("comparison") or not item.get("direction") or not item.get("decision_rule"):
            raise ProtocolError(f"primary endpoint decision rule is incomplete: {identifier}")
        _validate_evidence_requirements(item, primary=True)
    for item in secondary:
        identifier = item.get("id")
        if item.get("status") != "resolved" or not item.get("reporting_rule"):
            raise ProtocolError(f"unresolved secondary endpoint: {identifier}")
        if item.get("missing_policy") not in {"block-endpoint", "veto"}:
            raise ProtocolError(f"secondary missing policy is invalid: {identifier}")
        _validate_evidence_requirements(item, primary=False)


def _validate_evidence_requirements(item: Mapping[str, Any], *, primary: bool) -> None:
    requirements = item.get("required_evidence")
    if not isinstance(requirements, list) or not requirements:
        raise ProtocolError(f"endpoint has no evidence requirements: {item.get('id')}")
    for requirement in requirements:
        if not isinstance(requirement, Mapping) or not requirement.get("endpoint"):
            raise ProtocolError(f"endpoint evidence requirement is malformed: {item.get('id')}")
        allowed = set(requirement.get("allowed_provenance", []))
        if not allowed or not allowed.issubset(VALID_PROVENANCE):
            raise ProtocolError(f"endpoint evidence provenance is invalid: {item.get('id')}")
        if primary and allowed & {"self-reported", "unavailable"}:
            raise ProtocolError(f"primary evidence cannot be self-reported/unavailable: {item.get('id')}")
        if not isinstance(requirement.get("minimum_per_cell"), int) or requirement["minimum_per_cell"] < 1:
            raise ProtocolError(f"endpoint evidence minimum is invalid: {item.get('id')}")


def _validate_workload(
    protocol: Mapping[str, Any],
    dependencies: Mapping[str, Mapping[str, Any]],
) -> None:
    workload = protocol.get("workload")
    if not isinstance(workload, Mapping):
        raise ProtocolError("workload is missing")
    matrix_path = _repo_path(str(dependencies["case_matrix_fixture"]["path"]))
    matrix = load_json(matrix_path)
    matrix_cases = {case["case_id"]: case for case in matrix.get("cases", [])}
    matched = list(workload.get("matched_case_ids", []))
    smoke = list(workload.get("smoke_case_ids", []))
    excluded = list(workload.get("excluded_case_ids", []))
    if len(matched) != len(set(matched)) or len(excluded) != len(set(excluded)):
        raise ProtocolError("workload case ids must be unique")
    if set(matched) & set(excluded):
        raise ProtocolError("matched and excluded cases overlap")
    if set(matched) | set(excluded) != set(matrix_cases):
        raise ProtocolError("matched and excluded cases must partition the frozen matrix")
    if not set(smoke).issubset(matched):
        raise ProtocolError("smoke cases must be a subset of matched cases")
    if workload.get("smoke_repeats") != 1 or workload.get("smoke_outputs_count_toward_matched") is not True:
        raise ProtocolError("smoke repeat/carry-forward policy is unresolved")
    for case_id in matched:
        eligibility = matrix_cases[case_id]["source"]["run_eligibility"]
        if eligibility == "requires-user-authorization":
            raise ProtocolError(f"unauthorized replay included in matched workload: {case_id}")
    expected_excluded = {
        case_id
        for case_id, case in matrix_cases.items()
        if case["source"]["run_eligibility"] == "requires-user-authorization"
    }
    if set(excluded) != expected_excluded:
        raise ProtocolError("excluded workload does not exactly preserve unauthorized replays")
    if workload.get("case_type_weighting") != "equal-positive-negative-mass":
        raise ProtocolError("workload case-type weighting is unresolved")
    if set(workload.get("host_surfaces", [])) != {"codex-plugin", "claude-plugin"}:
        raise ProtocolError("host strata are incomplete or mutable")
    if set(workload.get("entry_modes", [])) != {
        "owner-direct",
        "passive-kernel",
        "arbitrator",
        "stay-asleep",
        "evidence-first",
    }:
        raise ProtocolError("entry-mode strata are incomplete or mutable")
    floor = workload.get("repeat_count_floor")
    planned = workload.get("planned_repeats")
    if not isinstance(floor, int) or floor < 3 or not isinstance(planned, int) or planned < floor:
        raise ProtocolError("repeat count floor is unresolved or too small")
    if workload.get("repeat_count_is_release_proof") is not False:
        raise ProtocolError("repeat count must explicitly not be release proof")


def _git_ancestor(commit: str) -> bool:
    if not re_fullmatch_git_commit(commit):
        return False
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def re_fullmatch_git_commit(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    return all(character in "0123456789abcdef" for character in value)


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    if protocol.get("schema_version") != "mindthus-beta2-evaluation-protocol-v0.1":
        raise ProtocolError("unsupported protocol schema_version")
    if protocol.get("protocol_id") != "mindthus-beta2-three-arm-evaluation":
        raise ProtocolError("unexpected protocol_id")
    if protocol.get("protocol_version") != "0.1" or protocol.get("status") != "frozen":
        raise ProtocolError("protocol version/status is not the frozen v0.1 contract")
    dependencies = _validate_dependencies(protocol)
    arms = protocol.get("arms")
    if not isinstance(arms, list) or {item.get("arm_id") for item in arms} != REQUIRED_ARMS:
        raise ProtocolError("arm ids are missing or mutable")
    if any(item.get("mutable") is not False for item in arms):
        raise ProtocolError("arm ids are marked mutable")
    if any(item.get("identity_source") != "sealed-arm-manifest.identity_digest" for item in arms):
        raise ProtocolError("arm identity is not sealed-manifest based")
    _validate_workload(protocol, dependencies)
    _validate_endpoints(protocol)

    design = protocol.get("execution_design")
    if not isinstance(design, Mapping):
        raise ProtocolError("execution design is missing")
    if design.get("generator_judge_separated") is not True or design.get("judge_sessions_independent") is not True:
        raise ProtocolError("generator/judge separation is unresolved")
    if design.get("judge_count_per_output", 0) < 2 or design.get("bootstrap_iterations", 0) < 10000:
        raise ProtocolError("blinded review or analysis floor is unresolved")
    if not design.get("order_seed_sha256") or not design.get("blinding"):
        raise ProtocolError("randomization or blinding is unresolved")
    if design.get("sealed_case_custodian_attestation_required") is not True:
        raise ProtocolError("sealed shadow cases lack an independent custodian gate")

    missing = protocol.get("missing_data_policy")
    if not isinstance(missing, Mapping):
        raise ProtocolError("missing-data policy is absent")
    if missing.get("zero_imputation") != "forbidden" or missing.get("pass_imputation") != "forbidden":
        raise ProtocolError("missing data may be silently imputed")
    if missing.get("cross_host_substitution") != "forbidden" or missing.get("cross_entry_mode_substitution") != "forbidden":
        raise ProtocolError("missing strata may be collapsed")

    vetoes = protocol.get("vetoes")
    if not isinstance(vetoes, list):
        raise ProtocolError("vetoes are absent")
    veto_ids = _unique_ids(vetoes, "veto")
    if not REQUIRED_VETOES.issubset(veto_ids):
        raise ProtocolError(f"required veto gaps: {sorted(REQUIRED_VETOES - veto_ids)}")
    if not isinstance(protocol.get("rerun_policy"), Mapping):
        raise ProtocolError("rerun policy is absent")

    authorization = protocol.get("authorization_parameters")
    if not isinstance(authorization, Mapping) or authorization.get("status") != "required-before-issue-119":
        raise ProtocolError("#119 authorization gate is unresolved")
    if not REQUIRED_AUTHORIZATION_FIELDS.issubset(set(authorization.get("must_name", []))):
        raise ProtocolError("#119 authorization packet fields are incomplete")
    if authorization.get("model_name_routing") != "forbidden":
        raise ProtocolError("model-name routing is not forbidden")
    if len(protocol.get("rejected_alternatives", [])) < 5:
        raise ProtocolError("rejected alternatives are not recorded")

    freeze = protocol.get("freeze")
    if not isinstance(freeze, Mapping):
        raise ProtocolError("freeze declaration is absent")
    if freeze.get("semantic_model_output_generated_before_freeze") is not False:
        raise ProtocolError("pre-freeze semantic model output is not explicitly absent")
    if freeze.get("amendment_policy") != "new protocol version and new lock required":
        raise ProtocolError("post-freeze amendment policy is mutable")
    source_parent = freeze.get("source_parent_commit")
    if not _git_ancestor(str(source_parent)):
        raise ProtocolError("source parent commit is not an ancestor of the current checkout")
    return {
        "status": "protocol-valid",
        "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["protocol_version"],
        "dependency_count": len(dependencies),
        "primary_endpoint_count": len(protocol["primary_endpoints"]),
        "secondary_endpoint_count": len(protocol["secondary_endpoints"]),
        "matched_case_count": len(protocol["workload"]["matched_case_ids"]),
        "planned_generation_cells": (
            len(protocol["workload"]["matched_case_ids"])
            * len(protocol["arms"])
            * len(protocol["workload"]["host_surfaces"])
            * protocol["workload"]["planned_repeats"]
        ),
    }


def _display_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(resolved)


def lock_payload(protocol_path: Path, protocol: Mapping[str, Any]) -> dict[str, Any]:
    validator_path = Path(__file__).resolve()
    base = {
        "schema_version": "mindthus-beta2-protocol-lock-v0.1",
        "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["protocol_version"],
        "protocol_path": _display_path(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "dependency_receipts": [
            {"id": item["id"], "path": item["path"], "sha256": item["sha256"]}
            for item in protocol["dependencies"]
        ],
        "arm_ids": [item["arm_id"] for item in protocol["arms"]],
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_parent_commit": protocol["freeze"]["source_parent_commit"],
        "semantic_model_output_generated_before_freeze": False,
        "validator_path": _display_path(validator_path),
        "validator_sha256": sha256_file(validator_path),
    }
    base["lock_digest"] = canonical_sha256(base)
    return base


def write_atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_lock(protocol_path: Path, protocol: Mapping[str, Any], lock_path: Path) -> dict[str, Any]:
    if not lock_path.is_file():
        raise ProtocolError("protocol lock receipt is missing")
    lock = load_json(lock_path)
    if lock.get("schema_version") != "mindthus-beta2-protocol-lock-v0.1":
        raise ProtocolError("unsupported protocol lock schema")
    if lock.get("protocol_id") != protocol.get("protocol_id") or lock.get("protocol_version") != protocol.get("protocol_version"):
        raise ProtocolError("protocol lock identity/version mismatch")
    if lock.get("protocol_sha256") != sha256_file(protocol_path):
        raise ProtocolError("post-freeze protocol edit detected; create a new protocol version")
    if lock.get("protocol_path") != _display_path(protocol_path):
        raise ProtocolError("protocol lock path differs from the validated protocol")
    expected_dependencies = [
        {"id": item["id"], "path": item["path"], "sha256": item["sha256"]}
        for item in protocol["dependencies"]
    ]
    if lock.get("dependency_receipts") != expected_dependencies:
        raise ProtocolError("protocol lock dependency receipts differ")
    if set(lock.get("arm_ids", [])) != REQUIRED_ARMS:
        raise ProtocolError("protocol lock arm ids differ")
    validator_path = _repo_path(str(lock.get("validator_path")))
    if lock.get("validator_sha256") != sha256_file(validator_path):
        raise ProtocolError("protocol validator changed after freeze")
    unsigned = dict(lock)
    observed_lock_digest = unsigned.pop("lock_digest", None)
    if observed_lock_digest != canonical_sha256(unsigned):
        raise ProtocolError("protocol lock receipt digest mismatch")
    return {
        "status": "frozen-valid",
        "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["protocol_version"],
        "protocol_sha256": lock["protocol_sha256"],
        "lock_digest": lock["lock_digest"],
        "frozen_at_utc": lock["frozen_at_utc"],
    }


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
        protocol = load_json(args.protocol)
        report = validate_protocol(protocol)
        if args.command == "freeze":
            if args.lock.exists():
                raise ProtocolError(
                    "lock already exists; frozen v0.1 cannot be overwritten—create a new protocol version"
                )
            write_atomic_json(args.lock, lock_payload(args.protocol, protocol))
            report = validate_lock(args.protocol, protocol, args.lock)
        elif args.command == "validate":
            report = validate_lock(args.protocol, protocol, args.lock)
    except (OSError, json.JSONDecodeError, ProtocolError, subprocess.SubprocessError) as exc:
        print(f"protocol {args.command} failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
