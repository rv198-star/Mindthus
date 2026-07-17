#!/usr/bin/env python3
"""Validate and freeze the additive v0.4 recovery amendment."""

from __future__ import annotations

import argparse
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
DEFAULT_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.json"
DEFAULT_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.lock.json"
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
BASE_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.lock.json"
BASE_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_AMENDMENT_ID = "0.4-recovery.1"
EXPECTED_BASE_PROTOCOL_SHA256 = (
    "a6e9da7ef2eb85e179d92ec909444c50e879673943b1be71f5c923b9e26d0746"
)
EXPECTED_BASE_LOCK_DIGEST = (
    "dc00e9564e655ae202a543f8719d40e9ad23858cf508a1889187bd4591fae62b"
)
EXPECTED_BASE_AUTHORIZATION_DIGEST = (
    "a8e270c919da161fb4eac2ef2d862e2157074d4ae84641d9057d10d79affd74f"
)
EXPECTED_SOURCE_PARENT = "93378d63b0c4da6bb6c1f25fedb0fa375ebb079e"
EXPECTED_RECOVERY_CELL = (
    "6721d94969c4893b4d5b7ffcc6b12fb38d334fd551f929114e2e7d1688a39dd5"
)
EXPECTED_RUNTIME_DEPENDENCIES = [
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4.json",
    "beta/2.0.0-beta.2/protocols/evaluation-protocol-v0.4.lock.json",
    "beta/2.0.0-beta.2/authorizations/issue-119-codex-v0.4.json",
    "scripts/mindthus_beta2_telemetry.py",
    "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v04.py",
    "beta/2.0.0-beta.2/runtime/analyze_codex_evaluation_v04.py",
    "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v04_recovery.py",
    "beta/2.0.0-beta.2/runtime/analyze_codex_evaluation_v04_recovery.py",
    "beta/2.0.0-beta.2/runtime/build-execution-authorization-v0.4-recovery.py",
    "beta/2.0.0-beta.2/runtime/validate-execution-authorization-v0.4-recovery.py",
]


class RecoveryProtocolError(ValueError):
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
        raise RecoveryProtocolError(f"{label} must be a repository-relative path")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise RecoveryProtocolError(f"{label} leaves repository") from exc
    return path


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RecoveryProtocolError(reason)


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    require(
        protocol.get("schema_version")
        == "mindthus-beta2-evaluation-recovery-amendment-v0.1",
        "unsupported recovery amendment schema",
    )
    require(protocol.get("protocol_id") == "mindthus-beta2-three-arm-evaluation", "protocol id differs")
    require(protocol.get("base_protocol_version") == "0.4", "base version differs")
    require(protocol.get("amendment_id") == EXPECTED_AMENDMENT_ID, "amendment id differs")

    binding = protocol.get("base_binding")
    require(isinstance(binding, Mapping), "base binding is missing")
    require(binding.get("protocol_path") == display(BASE_PROTOCOL), "base protocol path differs")
    require(binding.get("protocol_sha256") == EXPECTED_BASE_PROTOCOL_SHA256, "base protocol digest differs")
    require(sha256_file(BASE_PROTOCOL) == EXPECTED_BASE_PROTOCOL_SHA256, "base protocol file drifted")
    require(binding.get("lock_path") == display(BASE_LOCK), "base lock path differs")
    base_lock = load_json(BASE_LOCK)
    require(base_lock.get("lock_digest") == EXPECTED_BASE_LOCK_DIGEST, "base lock digest differs")
    require(binding.get("lock_digest") == EXPECTED_BASE_LOCK_DIGEST, "base lock binding differs")
    require(binding.get("authorization_path") == display(BASE_AUTHORIZATION), "base authorization path differs")
    require(
        canonical_sha256(load_json(BASE_AUTHORIZATION)) == EXPECTED_BASE_AUTHORIZATION_DIGEST,
        "base authorization file drifted",
    )
    require(
        binding.get("authorization_digest") == EXPECTED_BASE_AUTHORIZATION_DIGEST,
        "base authorization binding differs",
    )

    source = protocol.get("retained_source_run")
    require(isinstance(source, Mapping), "source-run receipt is missing")
    require(source.get("phase") == "smoke", "source phase differs")
    require(source.get("completed_generation_outputs") == 10, "source output count differs")
    require(source.get("generation_attempts") == 11, "source generation count differs")
    require(source.get("judge_attempts") == 0, "source judge count differs")
    require(source.get("known_counted_tokens") == 444034, "source measured tokens differ")
    for field in ("run_state_sha256", "run_state_digest", "stop_report_sha256"):
        require(bool(SHA256_RE.fullmatch(str(source.get(field) or ""))), f"{field} is invalid")
    cells = source.get("completed_cells")
    require(isinstance(cells, list) and len(cells) == 10, "retained cell receipt count differs")
    require(len({item.get("cell_id") for item in cells if isinstance(item, Mapping)}) == 10, "retained cell ids differ")
    for item in cells:
        require(isinstance(item, Mapping), "retained cell receipt is invalid")
        for field in ("cell_id", "record_digest", "file_sha256"):
            require(bool(SHA256_RE.fullmatch(str(item.get(field) or ""))), f"retained cell {field} is invalid")
        require(item.get("repeat") == 1, "retained cell repeat differs")
        require(item.get("arm_id") in {"stable", "direct-only", "thin-kernel"}, "retained cell arm differs")
    incomplete = source.get("incomplete_cell")
    require(isinstance(incomplete, Mapping), "incomplete cell receipt is missing")
    require(incomplete.get("cell_id") == EXPECTED_RECOVERY_CELL, "recovery cell differs")
    require(incomplete.get("case_id") == "b2-dev-near-normal-debugging", "recovery case differs")
    require(incomplete.get("arm_id") == "direct-only", "recovery arm differs")
    require(incomplete.get("entry_mode") == "stay-asleep", "recovery entry mode differs")
    require(incomplete.get("attempt") == 1, "source attempt number differs")
    require(incomplete.get("timed_out") is True and incomplete.get("returncode") == -15, "source failure differs")
    require(incomplete.get("semantic_output_retained") is True, "source semantic output is not retained")
    require(incomplete.get("native_usage_available") is False, "unknown usage was rewritten as known")
    for field in ("attempt_file_sha256", "attempt_digest", "answer_sha256", "events_sha256", "stderr_sha256"):
        require(bool(SHA256_RE.fullmatch(str(incomplete.get(field) or ""))), f"incomplete {field} is invalid")

    amendment = protocol.get("amendment")
    require(isinstance(amendment, Mapping), "amendment controls are missing")
    attempt = amendment.get("recovery_attempt")
    require(isinstance(attempt, Mapping), "recovery attempt control is missing")
    require(attempt.get("attempt_number") == 2, "recovery must be attempt-02")
    require(attempt.get("timeout_seconds") == 1800, "recovery timeout differs")
    require(attempt.get("same_cell_identity") is True, "cell identity may not change")
    require(attempt.get("same_prompt_and_generator_configuration") is True, "prompt/model may not change")
    require(attempt.get("append_only") is True, "recovery is not append-only")
    require(attempt.get("on_any_failure") == "terminal-stop-v0.4", "terminal stop differs")
    require(attempt.get("additional_recovery_attempts") == 0, "nested recovery is allowed")
    remaining = amendment.get("remaining_calls")
    require(isinstance(remaining, Mapping), "remaining-call controls are missing")
    require(remaining.get("timeout_seconds") == 1800, "remaining-call timeout differs")
    require(remaining.get("base_generation_call_ceiling") == 239, "generation ceiling differs")
    require(remaining.get("base_judge_call_ceiling") == 480, "judge ceiling differs")
    require(remaining.get("workload_truncation_allowed") is False, "workload truncation is allowed")

    budget = protocol.get("budget_accounting")
    require(isinstance(budget, Mapping), "budget accounting is missing")
    reserve = budget.get("unknown_usage_reserve")
    require(isinstance(reserve, Mapping), "unknown usage reserve is missing")
    require(reserve.get("model_context_window_tokens") == 272000, "context-window receipt differs")
    require(reserve.get("context_window_multiplier") == 8, "reserve multiplier differs")
    require(reserve.get("reserved_tokens") == 2176000, "unknown usage reserve differs")
    require(budget.get("base_v0_4_measured_token_ceiling") == 21951744, "base token ceiling differs")
    require(budget.get("amended_measured_token_ceiling") == 19775744, "amended token ceiling differs")
    require(19775744 + 2176000 == 21951744, "token reserve does not balance")
    require(budget.get("budget_expansion") is False, "recovery expands the token budget")

    analysis = protocol.get("analysis_policy")
    require(isinstance(analysis, Mapping), "analysis policy is missing")
    censored = analysis.get("right_censored_paired_unit")
    require(isinstance(censored, Mapping), "censored paired unit is missing")
    require(censored.get("case_id") == "b2-dev-near-normal-debugging", "censored case differs")
    require(censored.get("repeat") == 1, "censored repeat differs")
    require(
        censored.get("excluded_only_from_endpoints")
        == [
            "input_token_savings_vs_stable",
            "kernel_token_overhead_vs_direct",
            "wall_time_savings_vs_stable",
            "first_observable_action_latency",
        ],
        "censored endpoint set differs",
    )

    human = protocol.get("human_authorization")
    require(isinstance(human, Mapping), "human authorization is missing")
    require(human.get("authority") == "William", "stop authority differs")
    require(human.get("source_evidence_id") == "E46a11b5c", "human evidence anchor differs")
    require("把0.4这个补完" in str(human.get("source_instruction") or ""), "recovery instruction differs")
    require(human.get("release_preparation") is False, "release preparation was authorized")

    dependencies = protocol.get("runtime_dependencies")
    require(dependencies == EXPECTED_RUNTIME_DEPENDENCIES, "runtime dependency set differs")
    for index, path_text in enumerate(dependencies):
        path = repo_path(path_text, f"runtime_dependencies[{index}]")
        require(path.is_file(), f"runtime dependency is missing: {path_text}")

    freeze = protocol.get("freeze")
    require(isinstance(freeze, Mapping), "freeze declaration is missing")
    require(freeze.get("source_parent_commit") == EXPECTED_SOURCE_PARENT, "source parent differs")
    require(freeze.get("semantic_model_output_generated_before_amendment_freeze") is True, "prior semantic output is hidden")
    require(freeze.get("semantic_model_output_generated_under_amendment_before_freeze") is False, "amendment output predates freeze")
    return {
        "status": "valid",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "base_protocol_sha256": EXPECTED_BASE_PROTOCOL_SHA256,
        "recovery_cell_id": EXPECTED_RECOVERY_CELL,
        "retained_generation_outputs": 10,
        "retained_generation_attempts": 11,
        "unknown_usage_reserve": 2176000,
        "amended_measured_token_ceiling": 19775744,
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
        "schema_version": "mindthus-beta2-recovery-lock-v0.1",
        "protocol_id": "mindthus-beta2-three-arm-evaluation",
        "base_protocol_version": "0.4",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "protocol_path": display(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "base_protocol_sha256": EXPECTED_BASE_PROTOCOL_SHA256,
        "base_lock_digest": EXPECTED_BASE_LOCK_DIGEST,
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
    protocol_report = validate_protocol(protocol)
    lock = load_json(lock_path)
    unsigned = dict(lock)
    observed_digest = unsigned.pop("lock_digest", None)
    require(observed_digest == canonical_sha256(unsigned), "recovery lock digest differs")
    require(lock.get("schema_version") == "mindthus-beta2-recovery-lock-v0.1", "recovery lock schema differs")
    require(lock.get("amendment_id") == EXPECTED_AMENDMENT_ID, "locked amendment id differs")
    require(lock.get("protocol_path") == display(protocol_path), "locked protocol path differs")
    require(lock.get("protocol_sha256") == sha256_file(protocol_path), "locked protocol digest differs")
    require(lock.get("base_protocol_sha256") == EXPECTED_BASE_PROTOCOL_SHA256, "locked base protocol differs")
    require(lock.get("base_lock_digest") == EXPECTED_BASE_LOCK_DIGEST, "locked base lock differs")
    require(lock.get("source_parent_commit") == EXPECTED_SOURCE_PARENT, "locked source parent differs")
    require(lock.get("semantic_model_output_generated_before_freeze") is True, "lock hides prior output")
    require(lock.get("semantic_model_output_generated_under_amendment_before_freeze") is False, "lock permits pre-freeze recovery output")
    require(lock.get("validator_path") == display(Path(__file__)), "lock validator path differs")
    require(lock.get("validator_sha256") == sha256_file(Path(__file__)), "lock validator digest differs")
    require(lock.get("dependency_receipts") == dependency_receipts(protocol), "locked dependency receipts differ")
    return {
        **protocol_report,
        "status": "frozen",
        "protocol_sha256": lock["protocol_sha256"],
        "lock_digest": observed_digest,
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
            raise RecoveryProtocolError(f"recovery lock already exists: {path}") from exc
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
            lock = build_lock(args.protocol.resolve())
            write_exclusive(args.lock.resolve(), lock)
            report = validate_lock(args.protocol.resolve(), args.lock.resolve())
        else:
            report = validate_lock(args.protocol.resolve(), args.lock.resolve())
        code = 0
    except (OSError, json.JSONDecodeError, RecoveryProtocolError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
