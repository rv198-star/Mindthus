#!/usr/bin/env python3
"""Validate and freeze the additive v0.5 Judge compatibility amendment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
DEFAULT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.json"
)
DEFAULT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.lock.json"
)
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json"
BASE_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.lock.json"
BASE_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.json"
COMPAT_RUNNER = (
    BETA_ROOT / "runtime" / "run_real_codex_evaluation_v05_judge_compat.py"
)
BASE_PROTOCOL_SHA256 = (
    "f9bc7232647b02a77c67010a74deff79f205cc99590452c2134c515e252b4336"
)
BASE_LOCK_DIGEST = (
    "8c2d7ddcb1aac478eae31b937afa85a63505d1d4e48f5082781aa6a5c7321713"
)
BASE_AUTHORIZATION_DIGEST = (
    "813b3cb648768db98d7782c0ddafc77396ac9eeb287586819e3ef5e880b79957"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ProtocolError(ValueError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ProtocolError(f"{label} must be repository-relative")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ProtocolError(f"{label} leaves repository") from exc
    return path


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProtocolError(reason)


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mindthus_beta2_v05_judge_compat_freeze_runner", COMPAT_RUNNER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load v0.5 Judge compatibility runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _validate_base_binding(binding: Mapping[str, Any]) -> None:
    require(binding.get("protocol_path") == display(BASE_PROTOCOL), "base protocol path differs")
    require(binding.get("protocol_sha256") == BASE_PROTOCOL_SHA256, "base protocol digest differs")
    require(sha256_file(BASE_PROTOCOL) == BASE_PROTOCOL_SHA256, "base protocol file drifted")
    require(binding.get("lock_path") == display(BASE_LOCK), "base lock path differs")
    base_lock = read_json(BASE_LOCK)
    require(
        base_lock.get("lock_digest") == BASE_LOCK_DIGEST
        and binding.get("lock_digest") == BASE_LOCK_DIGEST,
        "base lock digest differs",
    )
    require(
        binding.get("authorization_path") == display(BASE_AUTHORIZATION),
        "base authorization path differs",
    )
    authorization = read_json(BASE_AUTHORIZATION)
    require(
        canonical_sha256(authorization) == BASE_AUTHORIZATION_DIGEST
        and binding.get("authorization_digest") == BASE_AUTHORIZATION_DIGEST,
        "base authorization digest differs",
    )
    require(
        binding.get("authorization_file_sha256") == sha256_file(BASE_AUTHORIZATION),
        "base authorization file differs",
    )
    require(
        binding.get("authorized_configuration_digest")
        == authorization["human_authorization"]["authorized_configuration_digest"],
        "base authorized configuration differs",
    )


def _validate_source(source: Mapping[str, Any], protocol_sha256: str) -> None:
    unsigned = dict(source)
    receipt_digest = unsigned.pop("source_receipt_digest", None)
    require(
        receipt_digest == canonical_sha256(unsigned),
        "retained source receipt digest differs",
    )
    require(source.get("protocol_sha256") == protocol_sha256, "source protocol differs")
    require(source.get("generation_calls") == 3, "source Generator calls differ")
    require(source.get("completed_generation_outputs") == 3, "source outputs differ")
    require(source.get("judge_attempts") == 4, "source Judge attempts differ")
    require(source.get("completed_judge_records") == 0, "source Judge records differ")
    require(source.get("committed_batches") == 0, "source committed batches differ")
    require(source.get("known_counted_tokens") == 90_100, "source tokens differ")
    require(source.get("batch_index") == 1, "source batch differs")
    require(source.get("case_id") == "b2-dev-owner-3l5s", "source case differs")
    cells = source.get("generation_cells")
    require(isinstance(cells, list) and len(cells) == 3, "source cell receipts differ")
    require(
        sorted(item.get("arm_id") for item in cells)
        == ["direct-only", "stable", "thin-kernel"],
        "source arm set differs",
    )
    require(
        source.get("generation_cell_set_digest") == canonical_sha256(cells),
        "source cell-set digest differs",
    )
    attempts = source.get("failed_judge_attempts")
    require(
        isinstance(attempts, list)
        and [(item.get("slot"), item.get("attempt")) for item in attempts]
        == [(1, 1), (1, 2), (2, 1), (2, 2)],
        "source failed Judge attempt identities differ",
    )
    require(
        source.get("failed_judge_attempt_set_digest") == canonical_sha256(attempts),
        "source failed Judge attempt-set digest differs",
    )
    packets = source.get("failure_packets")
    require(
        isinstance(packets, list)
        and [item.get("slot") for item in packets] == [1, 2]
        and source.get("failure_packet_set_digest") == canonical_sha256(packets),
        "source failure packet receipts differ",
    )
    for collection in (cells, attempts, packets):
        for item in collection:
            for key, value in item.items():
                if key.endswith("sha256") or key.endswith("digest"):
                    require(
                        bool(SHA256_RE.fullmatch(str(value or ""))),
                        f"source receipt {key} is invalid",
                    )
    evidence = source.get("failure_evidence")
    require(isinstance(evidence, Mapping), "source failure evidence is missing")
    require(evidence.get("stage") == "before model sampling", "source failure stage differs")
    require(
        evidence.get("returncode") == 1
        and evidence.get("timed_out") is False
        and evidence.get("output_present") is False
        and evidence.get("native_usage_available") is False
        and evidence.get("counted_tokens_per_attempt") == 0,
        "source failure outcome differs",
    )
    require(
        "'uniqueItems' is not permitted" in str(evidence.get("api_error") or ""),
        "source API error differs",
    )


def validate_protocol(protocol: Mapping[str, Any], *, verify_source_files: bool = True) -> dict[str, Any]:
    require(
        protocol.get("schema_version")
        == "mindthus-beta2-evaluation-judge-compat-amendment-v0.2",
        "unsupported Judge compatibility amendment schema",
    )
    require(protocol.get("protocol_id") == "mindthus-beta2-three-arm-evaluation", "protocol id differs")
    require(protocol.get("base_protocol_version") == "0.5", "base version differs")
    require(protocol.get("amendment_id") == "0.5-judge-compat.1", "amendment id differs")
    binding = protocol.get("base_binding")
    require(isinstance(binding, Mapping), "base binding is missing")
    _validate_base_binding(binding)
    source = protocol.get("retained_source_run")
    require(isinstance(source, Mapping), "retained source receipt is missing")
    _validate_source(source, BASE_PROTOCOL_SHA256)

    runner = _load_runner()
    schema_report = runner._validate_transport_schema()
    compatibility = protocol.get("schema_compatibility")
    require(isinstance(compatibility, Mapping), "schema compatibility contract is missing")
    require(
        compatibility.get("canonical_schema_sha256")
        == schema_report["original_schema_sha256"]
        and compatibility.get("api_schema_sha256")
        == schema_report["compatible_schema_sha256"]
        and compatibility.get("removed_keyword_paths")
        == schema_report["removed_keyword_paths"]
        and compatibility.get("semantic_contract_relaxation") is False,
        "schema compatibility contract differs",
    )

    control = protocol.get("recovery_control")
    require(isinstance(control, Mapping), "recovery control is missing")
    require(control.get("failed_slot_attempt_number") == 3, "failed-slot append number differs")
    require(control.get("new_slot_attempt_number") == 1, "new-slot attempt number differs")
    require(str(control.get("retry_policy", "")).startswith("none:"), "retry policy differs")
    require("atomic" in str(control.get("batch_commit_semantics")), "batch commit semantics differ")

    budget = protocol.get("budget_accounting")
    require(isinstance(budget, Mapping), "budget accounting is missing")
    require(
        budget.get("original_ceiling")
        == {
            "maximum_committed_batches": 5,
            "maximum_generation_calls": 17,
            "maximum_judge_calls": 34,
            "maximum_counted_tokens": 3_000_000,
        },
        "original ceiling differs",
    )
    require(
        budget.get("consumed_before_amendment")
        == {
            "committed_batches": 0,
            "generation_calls": 3,
            "judge_calls": 4,
            "counted_tokens": 90_100,
        },
        "consumed budget differs",
    )
    require(
        budget.get("remaining")
        == {
            "committed_batches": 5,
            "generation_calls": 14,
            "judge_calls": 30,
            "counted_tokens": 2_909_900,
        }
        and budget.get("valid_judge_records_still_required_for_five_batches") == 30
        and budget.get("future_retry_headroom") == 0
        and budget.get("budget_expansion") is False,
        "remaining budget differs",
    )

    human = protocol.get("human_authorization")
    require(isinstance(human, Mapping), "human boundary is missing")
    require(
        human.get("authority") == "William"
        and human.get("design_instruction") == "那按你的建议调整吧"
        and human.get("design_evidence_id") == "E7c74a48b"
        and human.get("design_authorized") is True
        and human.get("semantic_recovery_execution_authorized") is False
        and human.get("fresh_exact_digest_authorization_required") is True
        and human.get("stop_authority") == "William"
        and human.get("release_preparation") is False,
        "human authorization boundary differs",
    )

    dependencies = protocol.get("dependency_receipts")
    require(isinstance(dependencies, list), "dependency receipts are missing")
    paths = [item.get("path") for item in dependencies]
    require(len(paths) == len(set(paths)) == 12, "dependency receipt set differs")
    for item in dependencies:
        path = repo_path(item.get("path"), "dependency path")
        require(path.is_file(), f"dependency is missing: {path}")
        require(item.get("sha256") == sha256_file(path), f"dependency drifted: {path}")

    freeze = protocol.get("freeze")
    require(isinstance(freeze, Mapping), "freeze boundary is missing")
    require(
        freeze.get("semantic_generator_output_generated_before_amendment") is True
        and freeze.get("semantic_judge_output_generated_before_amendment") is False
        and freeze.get("semantic_output_generated_under_amendment_before_freeze") is False,
        "pre-freeze semantic-output disclosure differs",
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", str(freeze.get("source_parent_commit")), "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    require(ancestor.returncode == 0, "source parent is not an ancestor")
    if verify_source_files:
        source_path = repo_path(source.get("path"), "retained_source_run.path")
        runner.verify_retained_source(source_path, protocol, BASE_PROTOCOL_SHA256)
    return {
        "status": "protocol-valid",
        "amendment_id": "0.5-judge-compat.1",
        "base_protocol_sha256": BASE_PROTOCOL_SHA256,
        "retained_generation_outputs": 3,
        "retained_zero_token_judge_attempts": 4,
        "remaining_judge_calls": 30,
        "budget_expansion": False,
        "model_execution_performed": False,
    }


def lock_payload(protocol_path: Path, protocol: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-judge-compat-lock-v0.2",
        "protocol_id": protocol["protocol_id"],
        "base_protocol_version": "0.5",
        "amendment_id": protocol["amendment_id"],
        "protocol_path": display(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "base_protocol_sha256": BASE_PROTOCOL_SHA256,
        "base_lock_digest": BASE_LOCK_DIGEST,
        "source_receipt_digest": protocol["retained_source_run"]["source_receipt_digest"],
        "dependency_receipts": list(protocol["dependency_receipts"]),
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_parent_commit": protocol["freeze"]["source_parent_commit"],
        "semantic_output_generated_under_amendment_before_freeze": False,
        "validator_path": display(Path(__file__).resolve()),
        "validator_sha256": sha256_file(Path(__file__).resolve()),
    }
    payload["lock_digest"] = canonical_sha256(payload)
    return payload


def validate_lock(
    protocol_path: Path,
    protocol: Mapping[str, Any],
    lock_path: Path,
) -> dict[str, Any]:
    validate_protocol(protocol)
    lock = read_json(lock_path)
    unsigned = dict(lock)
    digest = unsigned.pop("lock_digest", None)
    require(digest == canonical_sha256(unsigned), "compatibility lock digest differs")
    require(lock.get("protocol_path") == display(protocol_path), "lock protocol path differs")
    require(lock.get("protocol_sha256") == sha256_file(protocol_path), "lock protocol digest differs")
    require(lock.get("base_protocol_sha256") == BASE_PROTOCOL_SHA256, "lock base protocol differs")
    require(lock.get("base_lock_digest") == BASE_LOCK_DIGEST, "lock base digest differs")
    require(
        lock.get("source_receipt_digest")
        == protocol["retained_source_run"]["source_receipt_digest"],
        "lock source receipt differs",
    )
    require(lock.get("dependency_receipts") == protocol["dependency_receipts"], "lock dependency receipts differ")
    require(lock.get("validator_path") == display(Path(__file__).resolve()), "lock validator path differs")
    require(lock.get("validator_sha256") == sha256_file(Path(__file__).resolve()), "lock validator digest differs")
    return {
        "status": "frozen",
        "amendment_id": protocol["amendment_id"],
        "protocol_sha256": lock["protocol_sha256"],
        "lock_digest": lock["lock_digest"],
        "base_protocol_sha256": BASE_PROTOCOL_SHA256,
        "remaining_judge_calls": 30,
        "budget_expansion": False,
        "model_execution_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build-lock", "validate"))
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()
    try:
        protocol = read_json(args.protocol.resolve())
        if args.command == "check":
            report = validate_protocol(protocol)
        elif args.command == "build-lock":
            validate_protocol(protocol)
            report = lock_payload(args.protocol.resolve(), protocol)
        else:
            report = validate_lock(args.protocol.resolve(), protocol, args.lock.resolve())
        code = 0
    except (
        OSError,
        json.JSONDecodeError,
        ProtocolError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
