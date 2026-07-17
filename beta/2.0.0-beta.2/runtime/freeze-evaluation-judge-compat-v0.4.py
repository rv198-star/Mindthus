#!/usr/bin/env python3
"""Validate and freeze the additive v0.4 Judge-schema compatibility amendment."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
DEFAULT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.json"
)
DEFAULT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.lock.json"
)
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
RECOVERY_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.json"
)
RECOVERY_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.lock.json"
)
RECOVERY_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-recovery.1.json"
)
ORIGINAL_SCHEMA = BETA_ROOT / "fixtures" / "judge-output-v0.4.schema.json"
COMPATIBLE_SCHEMA = (
    BETA_ROOT / "fixtures" / "judge-output-v0.4-openai-compatible.schema.json"
)
EXPECTED_BASE_SHA256 = (
    "a6e9da7ef2eb85e179d92ec909444c50e879673943b1be71f5c923b9e26d0746"
)
EXPECTED_RECOVERY_SHA256 = (
    "3c4b8b60a94592ce667ce271e58dba894772ba455c944778c6afa1aa0111aa48"
)
EXPECTED_RECOVERY_LOCK_DIGEST = (
    "46143196f02198accf28106e5747ea21e8ca1dbd88ed34777ad4cb8fca8945d4"
)
EXPECTED_RECOVERY_AUTHORIZATION_DIGEST = (
    "99c5676fa16bf3987ad9de33288c0b38cde0267246f47f252f863befb25869e2"
)
EXPECTED_SOURCE_PARENT = "da0a7b89a14fdbae1282c23ef8e42aff20cd5340"
EXPECTED_AMENDMENT_ID = "0.4-judge-compat.1"
EXPECTED_OUTPUT_ID = (
    "bd75595351da48405cd5eb84085714f1c8df1dbc01fe7b6bbdfa35b591c31712"
)
EXPECTED_DEPENDENCIES = [
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4.json",
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4-recovery.1.json",
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4-recovery.1.lock.json",
    "beta/2.0.0-beta.2/authorizations/issue-119-codex-v0.4-recovery.1.json",
    "beta/2.0.0-beta.2/fixtures/judge-output-v0.4.schema.json",
    "beta/2.0.0-beta.2/fixtures/judge-output-v0.4-openai-compatible.schema.json",
    "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v04.py",
    "beta/2.0.0-beta.2/runtime/analyze_codex_evaluation_v04.py",
    "beta/2.0.0-beta.2/runtime/analyze_codex_evaluation_v04_recovery.py",
    "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v04_judge_compat.py",
    "beta/2.0.0-beta.2/runtime/build-execution-authorization-v0.4-judge-compat.py",
    "beta/2.0.0-beta.2/runtime/validate-execution-authorization-v0.4-judge-compat.py",
]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class JudgeCompatProtocolError(ValueError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise JudgeCompatProtocolError(f"{label} must be repository-relative")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise JudgeCompatProtocolError(f"{label} leaves repository") from exc
    return path


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise JudgeCompatProtocolError(reason)


def validate_compatible_schema() -> dict[str, Any]:
    original = load_json(ORIGINAL_SCHEMA)
    compatible = load_json(COMPATIBLE_SCHEMA)
    expected = copy.deepcopy(original)
    removed = []
    for property_name in (
        "primitive_obligation_results",
        "unexpected_primitive_actions",
    ):
        node = expected["properties"][property_name]
        require(node.pop("uniqueItems", None) is True, f"original {property_name} uniqueness differs")
        removed.append(f"properties.{property_name}.uniqueItems")
    require(compatible == expected, "compatible schema changes more than two uniqueItems keywords")
    return {
        "original_schema_sha256": sha256_file(ORIGINAL_SCHEMA),
        "compatible_schema_sha256": sha256_file(COMPATIBLE_SCHEMA),
        "removed_keyword_paths": removed,
    }


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    require(
        protocol.get("schema_version")
        == "mindthus-beta2-evaluation-judge-compat-amendment-v0.1",
        "unsupported Judge compatibility schema",
    )
    require(protocol.get("protocol_id") == "mindthus-beta2-three-arm-evaluation", "protocol id differs")
    require(protocol.get("base_protocol_version") == "0.4", "base version differs")
    require(protocol.get("amendment_id") == EXPECTED_AMENDMENT_ID, "amendment id differs")
    binding = protocol.get("base_binding")
    require(isinstance(binding, Mapping), "base binding is missing")
    require(binding.get("protocol_path") == display(BASE_PROTOCOL), "base protocol path differs")
    require(binding.get("protocol_sha256") == EXPECTED_BASE_SHA256, "base protocol digest differs")
    require(sha256_file(BASE_PROTOCOL) == EXPECTED_BASE_SHA256, "base protocol file drifted")
    require(binding.get("generation_recovery_path") == display(RECOVERY_PROTOCOL), "recovery protocol path differs")
    require(binding.get("generation_recovery_sha256") == EXPECTED_RECOVERY_SHA256, "recovery protocol binding differs")
    require(sha256_file(RECOVERY_PROTOCOL) == EXPECTED_RECOVERY_SHA256, "recovery protocol drifted")
    recovery_lock = load_json(RECOVERY_LOCK)
    require(recovery_lock.get("lock_digest") == EXPECTED_RECOVERY_LOCK_DIGEST, "recovery lock drifted")
    require(binding.get("generation_recovery_lock_digest") == EXPECTED_RECOVERY_LOCK_DIGEST, "recovery lock binding differs")
    require(binding.get("generation_recovery_authorization_path") == display(RECOVERY_AUTHORIZATION), "recovery authorization path differs")
    require(canonical_sha256(load_json(RECOVERY_AUTHORIZATION)) == EXPECTED_RECOVERY_AUTHORIZATION_DIGEST, "recovery authorization drifted")
    require(binding.get("generation_recovery_authorization_digest") == EXPECTED_RECOVERY_AUTHORIZATION_DIGEST, "recovery authorization binding differs")

    source = protocol.get("retained_source_run")
    require(isinstance(source, Mapping), "source-run receipt is missing")
    require(source.get("phase") == "smoke", "source phase differs")
    require(source.get("completed_generation_outputs") == 15, "generation outputs differ")
    require(source.get("generation_attempts") == 16, "generation attempts differ")
    require(source.get("judge_attempts") == 4, "Judge attempt count differs")
    require(source.get("completed_judge_records") == 0, "source already has Judge records")
    require(source.get("known_counted_tokens") == 618258, "source token count differs")
    require(source.get("failed_output_id") == EXPECTED_OUTPUT_ID, "failed output differs")
    for field in (
        "generation_cell_set_digest",
        "run_state_sha256",
        "run_state_digest",
        "generation_metadata_repair_sha256",
        "generation_recovery_stop_report_sha256",
        "judge_attempt_set_digest",
        "judge_failure_packet_set_digest",
    ):
        require(bool(SHA256_RE.fullmatch(str(source.get(field) or ""))), f"{field} is invalid")
    failed = source.get("failed_attempts")
    require(isinstance(failed, list) and len(failed) == 4, "failed Judge receipts differ")
    require(
        [(item.get("slot"), item.get("attempt")) for item in failed]
        == [(1, 1), (1, 2), (2, 1), (2, 2)],
        "failed Judge attempt identities differ",
    )
    for item in failed:
        for field in ("attempt_digest", "attempt_file_sha256", "events_sha256"):
            require(bool(SHA256_RE.fullmatch(str(item.get(field) or ""))), f"failed Judge {field} is invalid")
    require(
        source.get("judge_attempt_set_digest") == canonical_sha256(failed),
        "failed Judge attempt set digest differs",
    )
    packets = source.get("failure_packets")
    require(
        isinstance(packets, list)
        and [item.get("slot") for item in packets] == [1, 2],
        "Judge failure packet receipts differ",
    )
    for item in packets:
        for field in ("packet_digest", "file_sha256"):
            require(
                bool(SHA256_RE.fullmatch(str(item.get(field) or ""))),
                f"Judge failure packet {field} is invalid",
            )
    require(
        source.get("judge_failure_packet_set_digest")
        == canonical_sha256(packets),
        "Judge failure packet set digest differs",
    )
    evidence = source.get("failure_evidence")
    require(isinstance(evidence, Mapping), "failure evidence is missing")
    require(evidence.get("stage") == "before model sampling", "failure stage differs")
    require(evidence.get("returncode") == 1 and evidence.get("timed_out") is False, "failure outcome differs")
    require(evidence.get("output_present") is False, "failed Judge output was hidden")
    require(evidence.get("native_usage_available") is False, "failed Judge usage was invented")
    require(evidence.get("counted_tokens_per_attempt") == 0, "failed Judge token count differs")
    require("'uniqueItems' is not permitted" in str(evidence.get("api_error") or ""), "API schema error differs")
    require(evidence.get("original_judge_schema_sha256") == sha256_file(ORIGINAL_SCHEMA), "original Judge schema receipt differs")

    schema_report = validate_compatible_schema()
    compatibility = protocol.get("schema_compatibility")
    require(isinstance(compatibility, Mapping), "schema compatibility declaration is missing")
    require(compatibility.get("original_schema_path") == display(ORIGINAL_SCHEMA), "original schema path differs")
    require(compatibility.get("compatible_schema_path") == display(COMPATIBLE_SCHEMA), "compatible schema path differs")
    require(compatibility.get("removed_keyword_paths") == schema_report["removed_keyword_paths"], "removed schema paths differ")
    require(compatibility.get("semantic_contract_relaxation") is False, "schema compatibility relaxes the Judge contract")

    amendment = protocol.get("amendment")
    require(isinstance(amendment, Mapping), "amendment controls are missing")
    slots = amendment.get("failed_slots")
    require(isinstance(slots, Mapping), "failed-slot controls are missing")
    require(slots.get("append_attempt_numbers") == [3, 4], "compatibility attempts differ")
    require(slots.get("prior_attempts_retained") is True, "prior Judge attempts may be discarded")
    remaining = amendment.get("remaining_judges")
    require(isinstance(remaining, Mapping), "remaining Judge controls are missing")
    require(remaining.get("compatible_schema_required") is True, "compatible schema is not required")
    require(remaining.get("base_two-attempt_policy_unchanged") is True, "remaining retry policy differs")
    require(remaining.get("maximum_judge_calls") == 480, "Judge ceiling differs")
    require(remaining.get("workload_truncation_allowed") is False, "Judge workload may be truncated")

    budget = protocol.get("budget_accounting")
    require(isinstance(budget, Mapping), "budget accounting is missing")
    require(budget.get("generation_calls_used") == 16, "generation call accounting differs")
    require(budget.get("judge_calls_used_by_schema_rejections") == 4, "schema rejection accounting differs")
    require(budget.get("judge_calls_remaining") == 476, "remaining Judge authority differs")
    require(budget.get("valid_judge_records_still_required") == 450, "required Judge records differ")
    require(budget.get("judge_retry_headroom_after_required_records") == 26, "Judge headroom differs")
    require(budget.get("budget_expansion") is False, "compatibility amendment expands budget")

    human = protocol.get("human_authorization")
    require(isinstance(human, Mapping), "human authorization is missing")
    require(human.get("authority") == "William", "human authority differs")
    require(human.get("source_evidence_id") == "E46a11b5c", "human evidence anchor differs")
    require("把0.4这个补完" in str(human.get("source_instruction") or ""), "human recovery instruction differs")
    require(human.get("release_preparation") is False, "release preparation was authorized")

    dependencies = protocol.get("runtime_dependencies")
    require(dependencies == EXPECTED_DEPENDENCIES, "runtime dependency set differs")
    for index, path_text in enumerate(dependencies):
        require(repo_path(path_text, f"runtime_dependencies[{index}]").is_file(), f"runtime dependency is missing: {path_text}")
    freeze = protocol.get("freeze")
    require(isinstance(freeze, Mapping), "freeze declaration is missing")
    require(freeze.get("source_parent_commit") == EXPECTED_SOURCE_PARENT, "source parent differs")
    require(freeze.get("semantic_model_output_generated_before_amendment_freeze") is True, "prior generator output is hidden")
    require(freeze.get("semantic_judge_output_generated_before_amendment_freeze") is False, "Judge output predates compatibility freeze")
    require(freeze.get("semantic_model_output_generated_under_amendment_before_freeze") is False, "compatibility output predates freeze")
    return {
        "status": "valid",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "base_protocol_sha256": EXPECTED_BASE_SHA256,
        "failed_output_id": EXPECTED_OUTPUT_ID,
        "retained_generation_outputs": 15,
        "retained_zero_output_judge_attempts": 4,
        **schema_report,
    }


def dependency_receipts(protocol: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "id": Path(path_text).name,
            "path": path_text,
            "sha256": sha256_file(repo_path(path_text, "runtime dependency")),
        }
        for path_text in protocol["runtime_dependencies"]
    ]


def build_lock(protocol_path: Path) -> dict[str, Any]:
    protocol = load_json(protocol_path)
    validate_protocol(protocol)
    lock: dict[str, Any] = {
        "schema_version": "mindthus-beta2-judge-compat-lock-v0.1",
        "protocol_id": "mindthus-beta2-three-arm-evaluation",
        "base_protocol_version": "0.4",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "protocol_path": display(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "base_protocol_sha256": EXPECTED_BASE_SHA256,
        "generation_recovery_sha256": EXPECTED_RECOVERY_SHA256,
        "generation_recovery_lock_digest": EXPECTED_RECOVERY_LOCK_DIGEST,
        "dependency_receipts": dependency_receipts(protocol),
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_parent_commit": EXPECTED_SOURCE_PARENT,
        "semantic_model_output_generated_before_freeze": True,
        "semantic_judge_output_generated_before_freeze": False,
        "semantic_model_output_generated_under_amendment_before_freeze": False,
        "validator_path": display(Path(__file__)),
        "validator_sha256": sha256_file(Path(__file__)),
    }
    lock["lock_digest"] = canonical_sha256(lock)
    return lock


def validate_lock(protocol_path: Path, lock_path: Path) -> dict[str, Any]:
    protocol = load_json(protocol_path)
    report = validate_protocol(protocol)
    lock = load_json(lock_path)
    unsigned = dict(lock)
    observed = unsigned.pop("lock_digest", None)
    require(observed == canonical_sha256(unsigned), "Judge compatibility lock digest differs")
    require(lock.get("schema_version") == "mindthus-beta2-judge-compat-lock-v0.1", "Judge compatibility lock schema differs")
    require(lock.get("amendment_id") == EXPECTED_AMENDMENT_ID, "locked amendment id differs")
    require(lock.get("protocol_path") == display(protocol_path), "locked protocol path differs")
    require(lock.get("protocol_sha256") == sha256_file(protocol_path), "locked protocol digest differs")
    require(lock.get("dependency_receipts") == dependency_receipts(protocol), "locked dependencies differ")
    require(lock.get("validator_path") == display(Path(__file__)), "locked validator path differs")
    require(lock.get("validator_sha256") == sha256_file(Path(__file__)), "locked validator digest differs")
    require(lock.get("semantic_judge_output_generated_before_freeze") is False, "lock hides prior Judge output")
    require(lock.get("semantic_model_output_generated_under_amendment_before_freeze") is False, "lock permits pre-freeze compatibility output")
    return {
        **report,
        "status": "frozen",
        "protocol_sha256": lock["protocol_sha256"],
        "lock_digest": observed,
        "frozen_at_utc": lock["frozen_at_utc"],
    }


def write_exclusive(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise JudgeCompatProtocolError(f"Judge compatibility lock already exists: {path}") from exc
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "freeze", "validate"))
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()
    try:
        if args.command == "check":
            report = validate_protocol(load_json(args.protocol.resolve()))
        elif args.command == "freeze":
            write_exclusive(args.lock.resolve(), build_lock(args.protocol.resolve()))
            report = validate_lock(args.protocol.resolve(), args.lock.resolve())
        else:
            report = validate_lock(args.protocol.resolve(), args.lock.resolve())
        code = 0
    except (OSError, json.JSONDecodeError, JudgeCompatProtocolError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
