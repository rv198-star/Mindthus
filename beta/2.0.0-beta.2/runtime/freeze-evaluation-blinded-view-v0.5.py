#!/usr/bin/env python3
"""Build, validate, and freeze the additive v0.5 blinded-view amendment."""

from __future__ import annotations

import argparse
import hashlib
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
RUNTIME_ROOT = BETA_ROOT / "runtime"
DEFAULT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-blinded-view.1.json"
)
DEFAULT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-blinded-view.1.lock.json"
)
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json"
BASE_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.lock.json"
COMPAT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.json"
)
COMPAT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.lock.json"
)
COMPAT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.5-judge-compat.1.json"
)
RUNNER_PATH = RUNTIME_ROOT / "run_real_codex_evaluation_v05_blinded_view.py"
ANALYZER_PATH = RUNTIME_ROOT / "analyze_incremental_v05_blinded_view.py"
VIEW_PRIMITIVE = RUNTIME_ROOT / "blinded_candidate_view_v04.py"
AUTH_BUILDER = RUNTIME_ROOT / "build-execution-authorization-v0.5-blinded-view.py"
AUTH_VALIDATOR = RUNTIME_ROOT / "validate-execution-authorization-v0.5-blinded-view.py"
BASE_PROTOCOL_SHA256 = (
    "f9bc7232647b02a77c67010a74deff79f205cc99590452c2134c515e252b4336"
)
BASE_LOCK_DIGEST = (
    "8c2d7ddcb1aac478eae31b937afa85a63505d1d4e48f5082781aa6a5c7321713"
)
COMPAT_PROTOCOL_SHA256 = (
    "fd5312d66f59a11215bb78929a683cf3c57377d84b3f2d53390ae6d27578efe6"
)
COMPAT_LOCK_DIGEST = (
    "420e8cb9473c944cd41ca33166a0258f986bb4855d7a2ecefc42a5d44bbad16e"
)
COMPAT_AUTHORIZATION_DIGEST = (
    "3a87294be05939455de1157a1466acdd71710bae30bed852361afe28c7789e5a"
)
AMENDMENT_ID = "0.5-blinded-view.1"
DEPENDENCIES = (
    BASE_PROTOCOL,
    BASE_LOCK,
    COMPAT_PROTOCOL,
    COMPAT_LOCK,
    COMPAT_AUTHORIZATION,
    RUNTIME_ROOT / "run_real_codex_evaluation_v05.py",
    RUNTIME_ROOT / "run_real_codex_evaluation_v05_judge_compat.py",
    RUNTIME_ROOT / "analyze_incremental_v05.py",
    VIEW_PRIMITIVE,
    RUNNER_PATH,
    ANALYZER_PATH,
    Path(__file__).resolve(),
    AUTH_BUILDER,
    AUTH_VALIDATOR,
)


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = _load("mindthus_beta2_v05_blinded_freeze_runner", RUNNER_PATH)


class ProtocolError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProtocolError(reason)


def canonical_sha256(value: object) -> str:
    return RUNNER.canonical_sha256(value)


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


def dependency_receipts() -> list[dict[str, str]]:
    for path in DEPENDENCIES:
        require(path.is_file(), f"dependency is missing: {path}")
    return [
        {"path": display(path), "sha256": sha256_file(path)}
        for path in DEPENDENCIES
    ]


def _base_binding() -> dict[str, Any]:
    base_lock = read_json(BASE_LOCK)
    compat_lock = read_json(COMPAT_LOCK)
    compat_authorization = read_json(COMPAT_AUTHORIZATION)
    require(sha256_file(BASE_PROTOCOL) == BASE_PROTOCOL_SHA256, "base protocol drifted")
    require(base_lock.get("lock_digest") == BASE_LOCK_DIGEST, "base lock drifted")
    require(
        sha256_file(COMPAT_PROTOCOL) == COMPAT_PROTOCOL_SHA256,
        "Judge compatibility amendment drifted",
    )
    require(
        compat_lock.get("lock_digest") == COMPAT_LOCK_DIGEST,
        "Judge compatibility lock drifted",
    )
    require(
        canonical_sha256(compat_authorization) == COMPAT_AUTHORIZATION_DIGEST,
        "Judge compatibility authorization drifted",
    )
    return {
        "protocol_path": display(BASE_PROTOCOL),
        "protocol_sha256": BASE_PROTOCOL_SHA256,
        "lock_path": display(BASE_LOCK),
        "lock_digest": BASE_LOCK_DIGEST,
        "judge_compatibility_protocol_path": display(COMPAT_PROTOCOL),
        "judge_compatibility_protocol_sha256": COMPAT_PROTOCOL_SHA256,
        "judge_compatibility_lock_path": display(COMPAT_LOCK),
        "judge_compatibility_lock_digest": COMPAT_LOCK_DIGEST,
        "judge_compatibility_authorization_path": display(COMPAT_AUTHORIZATION),
        "judge_compatibility_authorization_file_sha256": sha256_file(
            COMPAT_AUTHORIZATION
        ),
        "judge_compatibility_authorization_digest": COMPAT_AUTHORIZATION_DIGEST,
    }


def build_protocol() -> dict[str, Any]:
    source = RUNNER.build_source_snapshot()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    source_binding = {
        "snapshot_receipt_path": display(RUNNER.SOURCE_RECEIPT_PATH),
        "snapshot_receipt_sha256": sha256_file(RUNNER.SOURCE_RECEIPT_PATH),
        "snapshot_receipt_digest": source["receipt_digest"],
        "source_run_path": source["source_run_path"],
        "usage": source["usage"],
        "remaining_authority": source["remaining_authority"],
        "active_batch": source["active_batch"],
        "identifier_exposure_scan": source["identifier_exposure_scan"],
    }
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-evaluation-blinded-view-amendment-v0.1",
        "protocol_id": "mindthus-beta2-three-arm-evaluation",
        "base_protocol_version": "0.5",
        "amendment_id": AMENDMENT_ID,
        "purpose": (
            "Resume the stopped v0.5 incremental run by removing experiment "
            "identifiers only from the Judge-facing candidate copy, while preserving "
            "the original Generator answer and every frozen execution ceiling."
        ),
        "base_binding": _base_binding(),
        "retained_source_run": source_binding,
        "blinded_candidate_view": {
            "scope": "Judge input and Judge prompt only",
            "primitive_path": display(VIEW_PRIMITIVE),
            "primitive_sha256": sha256_file(VIEW_PRIMITIVE),
            "label_pattern": RUNNER.VIEW.LABEL_PATTERN.pattern,
            "sensitive_paths": source["sensitive_paths"],
            "sensitive_path_set_digest": source["sensitive_path_set_digest"],
            "transformations": {
                "mindthus_or_mindthus_beta_namespace_prefix": "remove prefix only; preserve owner name",
                "explicit_arm_label": RUNNER.VIEW.ARM_REPLACEMENT,
                "exact_sensitive_path": "terminal stop before transformation",
            },
            "original_answer_mutation_allowed": False,
            "identity_view_receipt": False,
            "transformed_view_receipt_schema": "mindthus-beta2-blinded-candidate-view-v0.1",
            "receipt_path": "recovery/0.5-blinded-view.1/candidate-views/{blinded_output_id}.json",
            "analysis_reconstruction_required": True,
            "semantic_scoring_contract_relaxation": False,
        },
        "recovery_control": {
            "retained_generation_policy": "reuse all three uncommitted batch-2 Generator outputs; never regenerate them",
            "resume_point": "one committed batch; batch 2 generated; zero batch-2 Judge calls",
            "call_order": "Judge retained batch 2, atomically commit it, then continue remaining authorized batches",
            "batch_commit_semantics": "unchanged frozen v0.5 hash-chained atomic commit",
            "analysis_semantics": "base v0.5 committed-batch analysis plus deterministic candidate-view validation",
            "future_retry_policy": "unchanged Generator retry rules; no Judge retry headroom",
            "terminal_stops": [
                "exact sensitive path exposure",
                "candidate-view transformation or receipt drift",
                "source or isolation drift",
                "any new Judge failure",
                "binary Judge disagreement requiring William",
                "any original cumulative ceiling breach",
            ],
        },
        "budget_accounting": {
            "original_ceiling": {
                "maximum_committed_batches": 5,
                "maximum_generation_calls": 17,
                "maximum_judge_calls": 34,
                "maximum_counted_tokens": 3_000_000,
            },
            "consumed_before_amendment": source["usage"],
            "remaining": source["remaining_authority"],
            "retained_uncommitted_generation_outputs": 3,
            "valid_judge_records_still_required_for_five_batches": 24,
            "future_judge_retry_headroom": 0,
            "budget_expansion": False,
        },
        "human_authorization": {
            "authority": "William",
            "design_instruction": "继续",
            "design_evidence_id": "E0ed03902",
            "zero_model_amendment_authorized": True,
            "semantic_recovery_execution_authorized": False,
            "fresh_exact_digest_authorization_required": True,
            "human_adjudicator": "William",
            "stop_authority": "William",
            "release_preparation": False,
        },
        "dependency_receipts": dependency_receipts(),
        "freeze": {
            "source_parent_commit": commit,
            "built_at_utc": datetime.now(timezone.utc).isoformat(),
            "semantic_generator_output_existed_before_amendment": True,
            "semantic_judge_output_existed_before_amendment": True,
            "semantic_output_generated_under_amendment_before_freeze": False,
            "immutable_after": "blinded-view lock creation and containing git commit",
            "future_change_policy": "another additive amendment must be frozen and exactly authorized before semantic calls",
        },
    }
    return payload


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    require(
        protocol.get("schema_version")
        == "mindthus-beta2-evaluation-blinded-view-amendment-v0.1",
        "unsupported blinded-view amendment schema",
    )
    require(protocol.get("protocol_id") == "mindthus-beta2-three-arm-evaluation", "protocol id differs")
    require(protocol.get("base_protocol_version") == "0.5", "base version differs")
    require(protocol.get("amendment_id") == AMENDMENT_ID, "amendment id differs")
    require(protocol.get("base_binding") == _base_binding(), "base binding differs")

    source_binding = protocol.get("retained_source_run")
    require(isinstance(source_binding, Mapping), "retained source binding is missing")
    source = RUNNER.validate_source_snapshot(source_binding)
    require(source_binding.get("usage") == source["usage"], "source usage binding differs")
    require(
        source_binding.get("remaining_authority") == source["remaining_authority"],
        "source remaining authority differs",
    )
    require(
        source_binding.get("identifier_exposure_scan")
        == source["identifier_exposure_scan"],
        "source exposure scan binding differs",
    )

    view = protocol.get("blinded_candidate_view")
    require(isinstance(view, Mapping), "blinded candidate-view contract is missing")
    require(
        view.get("scope") == "Judge input and Judge prompt only"
        and view.get("primitive_path") == display(VIEW_PRIMITIVE)
        and view.get("primitive_sha256") == sha256_file(VIEW_PRIMITIVE)
        and view.get("label_pattern") == RUNNER.VIEW.LABEL_PATTERN.pattern
        and view.get("sensitive_paths") == source["sensitive_paths"]
        and view.get("sensitive_path_set_digest")
        == source["sensitive_path_set_digest"]
        and view.get("original_answer_mutation_allowed") is False
        and view.get("identity_view_receipt") is False
        and view.get("analysis_reconstruction_required") is True
        and view.get("semantic_scoring_contract_relaxation") is False,
        "blinded candidate-view contract differs",
    )

    budget = protocol.get("budget_accounting")
    require(isinstance(budget, Mapping), "budget accounting is missing")
    require(
        budget.get("original_ceiling")
        == {
            "maximum_committed_batches": 5,
            "maximum_generation_calls": 17,
            "maximum_judge_calls": 34,
            "maximum_counted_tokens": 3_000_000,
        }
        and budget.get("consumed_before_amendment") == source["usage"]
        and budget.get("remaining") == source["remaining_authority"]
        and budget.get("retained_uncommitted_generation_outputs") == 3
        and budget.get("valid_judge_records_still_required_for_five_batches") == 24
        and budget.get("future_judge_retry_headroom") == 0
        and budget.get("budget_expansion") is False,
        "budget accounting differs",
    )

    human = protocol.get("human_authorization")
    require(isinstance(human, Mapping), "human boundary is missing")
    require(
        human.get("authority") == "William"
        and human.get("design_instruction") == "继续"
        and human.get("design_evidence_id") == "E0ed03902"
        and human.get("zero_model_amendment_authorized") is True
        and human.get("semantic_recovery_execution_authorized") is False
        and human.get("fresh_exact_digest_authorization_required") is True
        and human.get("human_adjudicator") == "William"
        and human.get("stop_authority") == "William"
        and human.get("release_preparation") is False,
        "human authorization boundary differs",
    )

    dependencies = protocol.get("dependency_receipts")
    require(
        isinstance(dependencies, list)
        and dependencies == dependency_receipts(),
        "dependency receipts differ",
    )
    freeze = protocol.get("freeze")
    require(isinstance(freeze, Mapping), "freeze boundary is missing")
    require(
        freeze.get("semantic_output_generated_under_amendment_before_freeze") is False,
        "pre-freeze semantic-output boundary differs",
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", str(freeze.get("source_parent_commit")), "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    require(ancestor.returncode == 0, "source parent is not an ancestor")
    return {
        "status": "protocol-valid",
        "amendment_id": AMENDMENT_ID,
        "base_protocol_sha256": BASE_PROTOCOL_SHA256,
        "judge_compatibility_protocol_sha256": COMPAT_PROTOCOL_SHA256,
        "retained_uncommitted_generation_outputs": 3,
        "remaining_generation_calls": 11,
        "remaining_judge_calls": 24,
        "remaining_counted_tokens": 2_725_136,
        "budget_expansion": False,
        "model_execution_performed": False,
    }


def lock_payload(protocol_path: Path, protocol: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-blinded-view-lock-v0.1",
        "protocol_id": protocol["protocol_id"],
        "base_protocol_version": "0.5",
        "amendment_id": AMENDMENT_ID,
        "protocol_path": display(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "base_protocol_sha256": BASE_PROTOCOL_SHA256,
        "base_lock_digest": BASE_LOCK_DIGEST,
        "judge_compatibility_protocol_sha256": COMPAT_PROTOCOL_SHA256,
        "judge_compatibility_lock_digest": COMPAT_LOCK_DIGEST,
        "source_receipt_digest": protocol["retained_source_run"]["snapshot_receipt_digest"],
        "dependency_receipts": protocol["dependency_receipts"],
        "validator_path": display(Path(__file__).resolve()),
        "validator_sha256": sha256_file(Path(__file__).resolve()),
        "source_parent_commit": protocol["freeze"]["source_parent_commit"],
        "semantic_output_generated_under_amendment_before_freeze": False,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    payload["lock_digest"] = canonical_sha256(payload)
    return payload


def validate_lock(
    protocol_path: Path, protocol: Mapping[str, Any], lock_path: Path
) -> dict[str, Any]:
    validate_protocol(protocol)
    lock = read_json(lock_path)
    unsigned = dict(lock)
    digest = unsigned.pop("lock_digest", None)
    require(digest == canonical_sha256(unsigned), "blinded-view lock digest differs")
    require(lock.get("schema_version") == "mindthus-beta2-blinded-view-lock-v0.1", "lock schema differs")
    require(lock.get("protocol_path") == display(protocol_path), "lock protocol path differs")
    require(lock.get("protocol_sha256") == sha256_file(protocol_path), "lock protocol digest differs")
    require(lock.get("base_protocol_sha256") == BASE_PROTOCOL_SHA256, "lock base protocol differs")
    require(lock.get("base_lock_digest") == BASE_LOCK_DIGEST, "lock base digest differs")
    require(
        lock.get("judge_compatibility_protocol_sha256") == COMPAT_PROTOCOL_SHA256
        and lock.get("judge_compatibility_lock_digest") == COMPAT_LOCK_DIGEST,
        "lock Judge compatibility binding differs",
    )
    require(
        lock.get("source_receipt_digest")
        == protocol["retained_source_run"]["snapshot_receipt_digest"],
        "lock source receipt differs",
    )
    require(lock.get("dependency_receipts") == protocol["dependency_receipts"], "lock dependencies differ")
    require(lock.get("validator_path") == display(Path(__file__).resolve()), "lock validator path differs")
    require(lock.get("validator_sha256") == sha256_file(Path(__file__).resolve()), "lock validator digest differs")
    return {
        "status": "frozen",
        "amendment_id": AMENDMENT_ID,
        "protocol_sha256": lock["protocol_sha256"],
        "lock_digest": lock["lock_digest"],
        "remaining_generation_calls": 11,
        "remaining_judge_calls": 24,
        "remaining_counted_tokens": 2_725_136,
        "budget_expansion": False,
        "model_execution_performed": False,
    }


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    RUNNER.V04.write_atomic_json(path, dict(payload))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("build-protocol", "check", "build-lock", "validate")
    )
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build-protocol":
            report = build_protocol()
            if args.output:
                write_json(args.output.resolve(), report)
        else:
            protocol = read_json(args.protocol.resolve())
            if args.command == "check":
                report = validate_protocol(protocol)
            elif args.command == "build-lock":
                validate_protocol(protocol)
                report = lock_payload(args.protocol.resolve(), protocol)
                if args.output:
                    write_json(args.output.resolve(), report)
            else:
                report = validate_lock(
                    args.protocol.resolve(), protocol, args.lock.resolve()
                )
        code = 0
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
