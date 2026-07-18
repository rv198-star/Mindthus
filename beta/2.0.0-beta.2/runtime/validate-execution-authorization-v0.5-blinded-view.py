#!/usr/bin/env python3
"""Fail-closed validation for v0.5 blinded-view recovery authority."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
BASE_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.5-judge-compat.1.json"
)
BASE_VALIDATOR_PATH = (
    RUNTIME_ROOT / "validate-execution-authorization-v0.5-judge-compat.py"
)
AMENDMENT = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-blinded-view.1.json"
)
LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-blinded-view.1.lock.json"
)
AMENDMENT_VALIDATOR_PATH = RUNTIME_ROOT / "freeze-evaluation-blinded-view-v0.5.py"
DEFAULT_AUTHORIZATION = (
    BETA_ROOT
    / "authorizations"
    / "issue-119-codex-v0.5-blinded-view.1.pending.json"
)
PENDING_AUTHORIZATION = DEFAULT_AUTHORIZATION
BASE_AUTHORIZATION_DIGEST = (
    "3a87294be05939455de1157a1466acdd71710bae30bed852361afe28c7789e5a"
)


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE_VALIDATOR = _load(
    "mindthus_beta2_v05_blinded_base_auth", BASE_VALIDATOR_PATH
)
AMENDMENT_VALIDATOR = _load(
    "mindthus_beta2_v05_blinded_amendment", AMENDMENT_VALIDATOR_PATH
)


class AuthorizationError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AuthorizationError(reason)


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


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise AuthorizationError(f"{label} must be repository-relative")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise AuthorizationError(f"{label} leaves repository") from exc
    return path


def authorized_configuration(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "base_protocol_sha256": packet["protocol"]["sha256"],
        "base_lock_digest": packet["protocol"]["lock_digest"],
        "judge_compatibility_protocol_sha256": packet[
            "judge_compatibility_amendment"
        ]["sha256"],
        "judge_compatibility_lock_digest": packet[
            "judge_compatibility_amendment"
        ]["lock_digest"],
        "blinded_view_protocol_sha256": packet["blinded_view_amendment"]["sha256"],
        "blinded_view_lock_digest": packet["blinded_view_amendment"]["lock_digest"],
        "host_surface": packet["host_surface"],
        "maximum_committed_batches": packet["maximum_committed_batches"],
        "maximum_generation_calls": packet["maximum_generation_calls"],
        "maximum_judge_calls": packet["maximum_judge_calls"],
        "token_or_cost_budget": packet["token_or_cost_budget"],
        "generator_model_by_host": packet["generator_model_by_host"],
        "judge_model_and_reasoning": packet["judge_model_and_reasoning"],
        "human_adjudicator": packet["human_adjudicator"],
        "stop_authority": packet["stop_authority"],
        "release_preparation": packet["release_preparation"],
    }


def validate_authorization(
    path: Path,
    *,
    require_active: bool = True,
    check_runtime: bool = False,
) -> dict[str, Any]:
    packet = read_json(path)
    require(
        packet.get("schema_version")
        == "mindthus-beta2-execution-authorization-v0.5-blinded-view.1",
        "unsupported blinded-view authorization schema",
    )
    validator = repo_path(
        packet.get("authorization_validator_path"), "authorization_validator_path"
    )
    require(validator == Path(__file__).resolve(), "authorization validator path differs")
    require(
        packet.get("authorization_validator_sha256") == sha256_file(validator),
        "authorization validator digest differs",
    )

    base = read_json(BASE_AUTHORIZATION)
    require(
        canonical_sha256(base) == BASE_AUTHORIZATION_DIGEST,
        "base Judge compatibility authorization drifted",
    )
    base_report = BASE_VALIDATOR.validate_authorization(
        BASE_AUTHORIZATION, require_active=True, check_runtime=False
    )
    require(base_report.get("status") == "authorized", "base recovery authority is inactive")
    base_receipt = packet.get("base_judge_compatibility_authorization")
    require(isinstance(base_receipt, Mapping), "base authorization receipt is missing")
    require(
        base_receipt
        == {
            "path": str(BASE_AUTHORIZATION.relative_to(REPO_ROOT)),
            "file_sha256": sha256_file(BASE_AUTHORIZATION),
            "authorization_digest": BASE_AUTHORIZATION_DIGEST,
        },
        "base authorization receipt differs",
    )

    amendment_report = AMENDMENT_VALIDATOR.validate_lock(
        AMENDMENT, read_json(AMENDMENT), LOCK
    )
    require(amendment_report.get("status") == "frozen", "blinded-view amendment is not frozen")
    amendment = read_json(AMENDMENT)
    lock = read_json(LOCK)
    receipt = packet.get("blinded_view_amendment")
    require(isinstance(receipt, Mapping), "blinded-view amendment receipt is missing")
    require(
        receipt
        == {
            "path": str(AMENDMENT.relative_to(REPO_ROOT)),
            "sha256": sha256_file(AMENDMENT),
            "lock_path": str(LOCK.relative_to(REPO_ROOT)),
            "lock_digest": lock["lock_digest"],
            "amendment_id": "0.5-blinded-view.1",
            "source_receipt_digest": amendment["retained_source_run"][
                "snapshot_receipt_digest"
            ],
        },
        "blinded-view amendment receipt differs",
    )

    unchanged = (
        "protocol",
        "host_surface",
        "maximum_committed_batches",
        "planned_generation_outputs",
        "planned_judge_records",
        "generator_model_by_host",
        "judge_model_and_reasoning",
        "maximum_generation_calls",
        "maximum_judge_calls",
        "token_or_cost_budget",
        "human_adjudicator",
        "stop_authority",
        "prior_consumption",
        "requested_cumulative_ceiling",
        "case_scope",
        "release_preparation",
        "judge_compatibility_amendment",
    )
    for field in unchanged:
        require(packet.get(field) == base.get(field), f"{field} differs from base authority")
    require(
        packet.get("current_run_consumption")
        == {
            "committed_batches": 1,
            "generation_calls": 6,
            "judge_calls": 10,
            "counted_tokens": 274_864,
        },
        "current run consumption differs",
    )
    require(
        packet.get("remaining_authority")
        == {
            "committed_batches": 4,
            "generation_calls": 11,
            "judge_calls": 24,
            "counted_tokens": 2_725_136,
            "Judge_retry_headroom": 0,
        },
        "remaining authority differs",
    )
    scope = packet.get("recovery_scope")
    require(isinstance(scope, Mapping), "recovery scope is missing")
    require(
        scope.get("retained_uncommitted_generation_outputs") == 3
        and scope.get("regeneration_allowed") is False
        and scope.get("valid_judge_records_still_required") == 24
        and scope.get("candidate_view_scope") == "Judge input and Judge prompt only"
        and scope.get("original_answer_mutation_allowed") is False
        and scope.get("budget_expansion") is False,
        "recovery scope differs",
    )
    require(packet.get("release_preparation") is False, "release preparation is authorized")

    configuration_digest = canonical_sha256(authorized_configuration(packet))
    require(
        packet.get("authorization_configuration_digest") == configuration_digest,
        "authorized configuration digest differs",
    )
    human = packet.get("human_authorization")
    require(isinstance(human, Mapping), "human authorization is missing")
    require(
        human.get("authority") == "William"
        and human.get("design_instruction") == "继续"
        and human.get("design_evidence_id") == "E0ed03902"
        and human.get("zero_model_amendment_authorized") is True,
        "design authority differs",
    )

    active = packet.get("status") == "authorized"
    if active:
        require(packet.get("blocking_requirements") == [], "active authority still has blockers")
        require(
            human.get("semantic_recovery_execution_authorized") is True,
            "semantic recovery authority is missing",
        )
        require(
            human.get("authorized_amendment_digest") == sha256_file(AMENDMENT)
            and human.get("authorized_lock_digest") == lock["lock_digest"]
            and human.get("authorized_configuration_digest") == configuration_digest,
            "exact human digest binding differs",
        )
        authorized_at = datetime.fromisoformat(
            str(human.get("authorized_at_utc") or "").replace("Z", "+00:00")
        )
        frozen_at = datetime.fromisoformat(
            str(lock["frozen_at_utc"]).replace("Z", "+00:00")
        )
        require(authorized_at >= frozen_at, "semantic recovery authority predates freeze")
        pending = read_json(PENDING_AUTHORIZATION)
        pending_unsigned = dict(pending)
        pending_digest = pending_unsigned.pop("pending_packet_digest", None)
        require(
            pending_digest == canonical_sha256(pending_unsigned),
            "pending packet digest differs",
        )
        require(
            packet.get("source_pending_packet_digest") == pending_digest,
            "active authority is not derived from the frozen pending packet",
        )
    else:
        require(packet.get("status") == "pending", "authorization status differs")
        unsigned = dict(packet)
        pending_digest = unsigned.pop("pending_packet_digest", None)
        require(
            pending_digest == canonical_sha256(unsigned),
            "pending authorization digest differs",
        )
        require(
            human.get("semantic_recovery_execution_authorized") is False
            and human.get("authorized_amendment_digest") is None
            and human.get("authorized_lock_digest") is None
            and human.get("authorized_configuration_digest") is None
            and human.get("authorized_at_utc") is None,
            "pending human authority is already populated",
        )
        require(
            len(packet.get("blocking_requirements", [])) == 2,
            "pending authorization blockers differ",
        )
        if require_active:
            raise AuthorizationError("v0.5 blinded-view execution authorization is pending")

    if check_runtime and active:
        BASE_VALIDATOR.validate_runtime(packet)
    return {
        "status": "authorized" if active else "pending",
        "authorization_id": packet["authorization_id"],
        "authorization_digest": canonical_sha256(packet),
        "protocol_sha256": packet["protocol"]["sha256"],
        "lock_digest": packet["protocol"]["lock_digest"],
        "judge_compatibility_protocol_sha256": packet[
            "judge_compatibility_amendment"
        ]["sha256"],
        "judge_compatibility_lock_digest": packet[
            "judge_compatibility_amendment"
        ]["lock_digest"],
        "blinded_view_protocol_sha256": sha256_file(AMENDMENT),
        "blinded_view_lock_digest": lock["lock_digest"],
        "authorization_configuration_digest": configuration_digest,
        "maximum_committed_batches": 5,
        "maximum_generation_calls": 17,
        "maximum_judge_calls": 34,
        "remaining_committed_batches": 4,
        "remaining_generation_calls": 11,
        "remaining_judge_calls": 24,
        "remaining_counted_tokens": 2_725_136,
        "token_budget": packet["token_or_cost_budget"],
        "stop_authority": "William",
        "release_preparation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--allow-pending", action="store_true")
    args = parser.parse_args()
    try:
        report = validate_authorization(
            args.authorization.resolve(),
            require_active=not args.allow_pending,
            check_runtime=not args.allow_pending,
        )
        code = 0
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
