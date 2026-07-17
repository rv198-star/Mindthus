#!/usr/bin/env python3
"""Validate and freeze the additive v0.4 blinded-candidate-view amendment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import blinded_candidate_view_v04 as view  # noqa: E402


DEFAULT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.json"
)
DEFAULT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.lock.json"
)
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
RECOVERY_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.json"
)
RECOVERY_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.lock.json"
)
COMPAT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.json"
)
COMPAT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.lock.json"
)
COMPAT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-judge-compat.1.json"
)
EXPECTED_BASE_SHA256 = (
    "a6e9da7ef2eb85e179d92ec909444c50e879673943b1be71f5c923b9e26d0746"
)
EXPECTED_RECOVERY_SHA256 = (
    "3c4b8b60a94592ce667ce271e58dba894772ba455c944778c6afa1aa0111aa48"
)
EXPECTED_RECOVERY_LOCK = (
    "46143196f02198accf28106e5747ea21e8ca1dbd88ed34777ad4cb8fca8945d4"
)
EXPECTED_COMPAT_SHA256 = (
    "b9ef851c0b056c76fea045411dc17803151a3bff5419636b39bbdc63d60a0990"
)
EXPECTED_COMPAT_LOCK = (
    "04b3c287b033d889a5215831e27f5c633a3d030161a95218eb59e50424a11f5e"
)
EXPECTED_COMPAT_AUTHORIZATION = (
    "82583dcf3c20f642bb0531233673eae16079dc0e048154b1b3d10dca79d43ef1"
)
EXPECTED_SOURCE_PARENT = "7405d8c55b52aadce7aa87c84c8dc0a9e136ad73"
EXPECTED_AMENDMENT_ID = "0.4-blinded-view.1"
EXPECTED_PATH_SET_DIGEST = (
    "8aedffebe74d119001204eebe5960ca27b7f976c35989cedc8975234bad4f9bd"
)
EXPECTED_DEPENDENCIES = [
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4.json",
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4-recovery.1.json",
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4-recovery.1.lock.json",
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4-judge-compat.1.json",
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4-judge-compat.1.lock.json",
    "beta/2.0.0-beta.2/authorizations/issue-119-codex-v0.4-judge-compat.1.json",
    "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v04.py",
    "beta/2.0.0-beta.2/runtime/analyze_codex_evaluation_v04.py",
    "beta/2.0.0-beta.2/runtime/analyze_codex_evaluation_v04_recovery.py",
    "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v04_judge_compat.py",
    "beta/2.0.0-beta.2/runtime/blinded_candidate_view_v04.py",
    "beta/2.0.0-beta.2/runtime/analyze_codex_evaluation_v04_blinded_view.py",
    "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v04_blinded_view.py",
    "beta/2.0.0-beta.2/runtime/build-execution-authorization-v0.4-blinded-view.py",
    "beta/2.0.0-beta.2/runtime/validate-execution-authorization-v0.4-blinded-view.py",
]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class BlindedViewProtocolError(ValueError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise BlindedViewProtocolError(f"{label} must be repository-relative")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise BlindedViewProtocolError(f"{label} leaves repository") from exc
    return path


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise BlindedViewProtocolError(reason)


def validate_prior_bindings(binding: Mapping[str, Any]) -> None:
    require(sha256_file(BASE_PROTOCOL) == EXPECTED_BASE_SHA256, "base protocol drifted")
    require(
        binding.get("protocol_sha256") == EXPECTED_BASE_SHA256,
        "base protocol binding differs",
    )
    require(
        sha256_file(RECOVERY_PROTOCOL) == EXPECTED_RECOVERY_SHA256
        and binding.get("generation_recovery_sha256") == EXPECTED_RECOVERY_SHA256,
        "generation recovery binding differs",
    )
    require(
        load_json(RECOVERY_LOCK).get("lock_digest") == EXPECTED_RECOVERY_LOCK
        and binding.get("generation_recovery_lock_digest") == EXPECTED_RECOVERY_LOCK,
        "generation recovery lock differs",
    )
    require(
        sha256_file(COMPAT_PROTOCOL) == EXPECTED_COMPAT_SHA256
        and binding.get("judge_compatibility_sha256") == EXPECTED_COMPAT_SHA256,
        "Judge compatibility binding differs",
    )
    require(
        load_json(COMPAT_LOCK).get("lock_digest") == EXPECTED_COMPAT_LOCK
        and binding.get("judge_compatibility_lock_digest") == EXPECTED_COMPAT_LOCK,
        "Judge compatibility lock differs",
    )
    require(
        canonical_sha256(load_json(COMPAT_AUTHORIZATION))
        == EXPECTED_COMPAT_AUTHORIZATION
        and binding.get("judge_compatibility_authorization_digest")
        == EXPECTED_COMPAT_AUTHORIZATION,
        "Judge compatibility authorization differs",
    )


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    require(
        protocol.get("schema_version")
        == "mindthus-beta2-evaluation-blinded-view-amendment-v0.1",
        "unsupported blinded-view amendment schema",
    )
    require(protocol.get("protocol_id") == "mindthus-beta2-three-arm-evaluation", "protocol id differs")
    require(protocol.get("base_protocol_version") == "0.4", "base version differs")
    require(protocol.get("amendment_id") == EXPECTED_AMENDMENT_ID, "amendment id differs")
    binding = protocol.get("base_binding")
    require(isinstance(binding, Mapping), "base binding is missing")
    validate_prior_bindings(binding)

    source = protocol.get("retained_source_run")
    require(isinstance(source, Mapping), "source-run receipt is missing")
    expected_counts = {
        "completed_generation_outputs": 15,
        "generation_attempts": 16,
        "judge_attempts": 17,
        "completed_judge_records": 12,
        "known_counted_tokens": 789490,
    }
    for field, expected in expected_counts.items():
        require(source.get(field) == expected, f"source {field} differs")
    for field in (
        "run_state_sha256",
        "run_state_digest",
        "judge_compatibility_stop_report_sha256",
        "judge_attempt_set_digest",
        "judge_record_set_digest",
    ):
        require(bool(SHA256_RE.fullmatch(str(source.get(field) or ""))), f"{field} is invalid")
    timeout = source.get("timed_out_judge_attempt")
    require(isinstance(timeout, Mapping), "timed-out Judge receipt is missing")
    require(
        timeout.get("attempt_digest")
        == "0f40bf5d5f3371a3eb4c7a8265e996c95e783bbd1e6ab1f2ec94086a48f87ddd"
        and timeout.get("returncode") == -15
        and timeout.get("timed_out") is True
        and timeout.get("output_present") is False
        and timeout.get("native_usage_available") is False
        and timeout.get("counted_tokens") == 0,
        "timed-out Judge evidence differs",
    )
    scan = source.get("identifier_exposure_scan")
    require(isinstance(scan, Mapping), "identifier exposure scan is missing")
    require(
        scan.get("scanned_generation_outputs") == 15
        and scan.get("exposed_generation_outputs") == 3,
        "identifier exposure counts differ",
    )
    items = scan.get("items")
    require(isinstance(items, list) and len(items) == 3, "identifier exposure items differ")
    require(
        scan.get("exposed_set_digest") == canonical_sha256(items),
        "identifier exposure set digest differs",
    )

    config = protocol.get("blinded_candidate_view")
    require(isinstance(config, Mapping), "blinded candidate view config is missing")
    paths = config.get("sensitive_paths")
    require(isinstance(paths, list) and view.normalized_paths(paths) == paths, "sensitive path order differs")
    require(canonical_sha256(paths) == EXPECTED_PATH_SET_DIGEST, "sensitive path set differs")
    require(config.get("sensitive_paths_digest") == EXPECTED_PATH_SET_DIGEST, "sensitive path digest differs")
    require(config.get("label_pattern") == view.LABEL_PATTERN.pattern, "label pattern differs")
    require(config.get("path_replacement") == view.PATH_REPLACEMENT, "path replacement differs")
    require(config.get("arm_label_replacement") == view.ARM_REPLACEMENT, "arm replacement differs")
    require(config.get("namespace_prefix_replacement") == "", "namespace replacement differs")
    for field in (
        "original_answer_mutation_allowed",
        "generation_retry_for_identifier_exposure_allowed",
    ):
        require(config.get(field) is False, f"{field} permits semantic replacement")
    require(config.get("receipt_required_when_non_identity") is True, "view receipts are optional")
    require(config.get("receipt_hidden_from_judges") is True, "view receipts leak to Judges")
    require(config.get("semantic_scoring_contract_unchanged") is True, "scoring contract differs")
    sample, trace = view.transform_candidate(
        f"{paths[-2]} mindthus-beta:wae direct-only", paths
    )
    view.assert_blind(sample, paths)
    require(
        sample == f"{view.PATH_REPLACEMENT} wae {view.ARM_REPLACEMENT}"
        and len(trace) == 3,
        "view transformation behavior differs",
    )

    budget = protocol.get("budget_accounting")
    require(isinstance(budget, Mapping), "budget accounting is missing")
    require(
        budget.get("judge_calls_used") == 17
        and budget.get("judge_calls_remaining") == 463
        and budget.get("valid_judge_records_still_required") == 438
        and budget.get("judge_retry_headroom_after_required_records") == 25,
        "Judge budget accounting differs",
    )
    reserve = budget.get("new_unknown_judge_usage_reserve")
    require(isinstance(reserve, Mapping) and reserve.get("reserved_tokens") == 2176000, "Judge unknown-usage reserve differs")
    require(
        budget.get("prior_unknown_generation_usage_reserved_tokens") == 2176000
        and budget.get("total_unknown_usage_reserved_tokens") == 4352000
        and budget.get("prior_measured_token_ceiling") == 19775744
        and budget.get("amended_measured_token_ceiling") == 17599744
        and 17599744 + 4352000 == 21951744
        and budget.get("budget_expansion") is False,
        "cumulative token budget differs",
    )

    human = protocol.get("human_authorization")
    require(isinstance(human, Mapping) and human.get("authority") == "William", "human authority differs")
    require("把0.4这个补完" in str(human.get("source_instruction") or ""), "human instruction differs")
    require(human.get("release_preparation") is False, "release preparation was authorized")
    dependencies = protocol.get("runtime_dependencies")
    require(dependencies == EXPECTED_DEPENDENCIES, "runtime dependency set differs")
    for index, value in enumerate(dependencies):
        require(repo_path(value, f"runtime_dependencies[{index}]").is_file(), f"runtime dependency is missing: {value}")
    freeze = protocol.get("freeze")
    require(isinstance(freeze, Mapping), "freeze declaration is missing")
    require(freeze.get("source_parent_commit") == EXPECTED_SOURCE_PARENT, "source parent differs")
    require(freeze.get("semantic_model_output_generated_before_amendment_freeze") is True, "prior output is hidden")
    require(freeze.get("semantic_model_output_generated_under_amendment_before_freeze") is False, "amendment output predates freeze")
    return {
        "status": "valid",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "base_protocol_sha256": EXPECTED_BASE_SHA256,
        "retained_generation_outputs": 15,
        "retained_judge_records": 12,
        "retained_judge_attempts": 17,
        "identifier_exposed_outputs": 3,
        "amended_measured_token_ceiling": 17599744,
    }


def dependency_receipts(protocol: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"id": Path(value).name, "path": value, "sha256": sha256_file(repo_path(value, "runtime dependency"))}
        for value in protocol["runtime_dependencies"]
    ]


def build_lock(protocol_path: Path) -> dict[str, Any]:
    protocol = load_json(protocol_path)
    validate_protocol(protocol)
    lock: dict[str, Any] = {
        "schema_version": "mindthus-beta2-blinded-view-lock-v0.1",
        "protocol_id": "mindthus-beta2-three-arm-evaluation",
        "base_protocol_version": "0.4",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "protocol_path": display(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "base_protocol_sha256": EXPECTED_BASE_SHA256,
        "generation_recovery_sha256": EXPECTED_RECOVERY_SHA256,
        "judge_compatibility_sha256": EXPECTED_COMPAT_SHA256,
        "dependency_receipts": dependency_receipts(protocol),
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_parent_commit": EXPECTED_SOURCE_PARENT,
        "semantic_model_output_generated_before_freeze": True,
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
    digest = unsigned.pop("lock_digest", None)
    require(digest == canonical_sha256(unsigned), "blinded-view lock digest differs")
    require(lock.get("schema_version") == "mindthus-beta2-blinded-view-lock-v0.1", "lock schema differs")
    require(lock.get("protocol_path") == display(protocol_path), "locked protocol path differs")
    require(lock.get("protocol_sha256") == sha256_file(protocol_path), "locked protocol digest differs")
    require(lock.get("dependency_receipts") == dependency_receipts(protocol), "locked dependencies differ")
    require(lock.get("validator_path") == display(Path(__file__)), "locked validator path differs")
    require(lock.get("validator_sha256") == sha256_file(Path(__file__)), "locked validator digest differs")
    require(lock.get("semantic_model_output_generated_under_amendment_before_freeze") is False, "lock permits pre-freeze output")
    return {**report, "status": "frozen", "protocol_sha256": lock["protocol_sha256"], "lock_digest": digest, "frozen_at_utc": lock["frozen_at_utc"]}


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
            raise BlindedViewProtocolError(f"blinded-view lock already exists: {path}") from exc
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
    except (OSError, json.JSONDecodeError, BlindedViewProtocolError, view.BlindedViewError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
