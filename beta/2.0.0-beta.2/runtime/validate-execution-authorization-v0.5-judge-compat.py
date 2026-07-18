#!/usr/bin/env python3
"""Fail-closed validation for v0.5 Judge compatibility recovery authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
BASE_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.json"
BASE_VALIDATOR = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.5.py"
AMENDMENT = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.json"
LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.lock.json"
AMENDMENT_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-judge-compat-v0.5.py"
DEFAULT_AUTHORIZATION = (
    BETA_ROOT
    / "authorizations"
    / "issue-119-codex-v0.5-judge-compat.1.pending.json"
)
PENDING_AUTHORIZATION = DEFAULT_AUTHORIZATION


class AuthorizationError(ValueError):
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


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise AuthorizationError(f"{label} must be repository-relative")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise AuthorizationError(f"{label} leaves repository") from exc
    return path


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AuthorizationError(reason)


def run_validation(command: list[str], label: str) -> dict[str, Any]:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise AuthorizationError(
            f"{label} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    payload = json.loads(result.stdout)
    require(isinstance(payload, dict), f"{label} returned a non-object")
    return payload


def authorized_configuration(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "base_protocol_sha256": packet["protocol"]["sha256"],
        "base_lock_digest": packet["protocol"]["lock_digest"],
        "judge_compatibility_protocol_sha256": packet["judge_compatibility_amendment"]["sha256"],
        "judge_compatibility_lock_digest": packet["judge_compatibility_amendment"]["lock_digest"],
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


def validate_runtime(packet: Mapping[str, Any]) -> None:
    generator = packet["generator_model_by_host"]["codex-plugin"]
    expected = f"codex-cli {generator['codex_cli_version']}"
    result = subprocess.run(
        ["codex", "--version"], cwd=REPO_ROOT, text=True, capture_output=True
    )
    require(
        result.returncode == 0 and result.stdout.strip() == expected,
        "Codex CLI runtime differs",
    )
    require(Path("/usr/bin/sandbox-exec").is_file(), "macOS sandbox-exec is unavailable")


def validate_authorization(
    path: Path,
    *,
    require_active: bool = True,
    check_runtime: bool = False,
) -> dict[str, Any]:
    packet = read_json(path)
    require(
        packet.get("schema_version")
        == "mindthus-beta2-execution-authorization-v0.5-judge-compat.1",
        "unsupported Judge compatibility authorization schema",
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
    base_report = run_validation(
        ["python3", str(BASE_VALIDATOR), "--authorization", str(BASE_AUTHORIZATION)],
        "base v0.5 authorization",
    )
    require(base_report.get("status") == "authorized", "base v0.5 authority is inactive")
    receipt = packet.get("base_authorization")
    require(isinstance(receipt, Mapping), "base authorization receipt is missing")
    require(
        receipt.get("path") == str(BASE_AUTHORIZATION.relative_to(REPO_ROOT))
        and receipt.get("file_sha256") == sha256_file(BASE_AUTHORIZATION)
        and receipt.get("authorization_digest") == canonical_sha256(base),
        "base authorization receipt differs",
    )

    amendment_report = run_validation(
        [
            "python3",
            str(AMENDMENT_VALIDATOR),
            "validate",
            "--protocol",
            str(AMENDMENT),
            "--lock",
            str(LOCK),
        ],
        "v0.5 Judge compatibility amendment",
    )
    require(amendment_report.get("status") == "frozen", "compatibility amendment is not frozen")
    amendment = read_json(AMENDMENT)
    lock = read_json(LOCK)
    amendment_receipt = packet.get("judge_compatibility_amendment")
    require(isinstance(amendment_receipt, Mapping), "compatibility amendment receipt is missing")
    require(
        amendment_receipt
        == {
            "path": str(AMENDMENT.relative_to(REPO_ROOT)),
            "sha256": sha256_file(AMENDMENT),
            "lock_path": str(LOCK.relative_to(REPO_ROOT)),
            "lock_digest": lock["lock_digest"],
            "amendment_id": "0.5-judge-compat.1",
            "api_schema_path": amendment["schema_compatibility"]["api_schema_path"],
            "api_schema_sha256": amendment["schema_compatibility"]["api_schema_sha256"],
        },
        "compatibility amendment receipt differs",
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
    )
    for field in unchanged:
        require(packet.get(field) == base.get(field), f"{field} differs from base v0.5 authority")
    require(
        packet.get("current_run_consumption")
        == {
            "committed_batches": 0,
            "generation_calls": 3,
            "judge_calls": 4,
            "counted_tokens": 90_100,
        },
        "current run consumption differs",
    )
    require(
        packet.get("remaining_authority")
        == {
            "committed_batches": 5,
            "generation_calls": 14,
            "judge_calls": 30,
            "counted_tokens": 2_909_900,
            "Judge_retry_headroom": 0,
        },
        "remaining authority differs",
    )
    recovery = packet.get("recovery_scope")
    require(isinstance(recovery, Mapping), "recovery scope is missing")
    require(
        recovery.get("retained_generation_outputs") == 3
        and recovery.get("regeneration_allowed") is False
        and recovery.get("valid_judge_records_still_required") == 30
        and recovery.get("budget_expansion") is False,
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
        and human.get("design_instruction") == "那按你的建议调整吧"
        and human.get("design_evidence_id") == "E7c74a48b"
        and human.get("design_authorized") is True,
        "design authority differs",
    )

    active = packet.get("status") == "authorized"
    if active:
        require(packet.get("blocking_requirements") == [], "active authority still has blockers")
        require(human.get("semantic_recovery_execution_authorized") is True, "semantic recovery authority is missing")
        require(
            human.get("authorized_amendment_digest") == sha256_file(AMENDMENT)
            and human.get("authorized_lock_digest") == lock["lock_digest"]
            and human.get("authorized_configuration_digest") == configuration_digest,
            "exact human digest binding differs",
        )
        authorized_at = datetime.fromisoformat(
            str(human.get("authorized_at_utc") or "").replace("Z", "+00:00")
        )
        frozen_at = datetime.fromisoformat(str(lock["frozen_at_utc"]).replace("Z", "+00:00"))
        require(authorized_at >= frozen_at, "semantic recovery authority predates freeze")
        pending = read_json(PENDING_AUTHORIZATION)
        pending_unsigned = dict(pending)
        pending_digest = pending_unsigned.pop("pending_packet_digest", None)
        require(pending_digest == canonical_sha256(pending_unsigned), "pending packet digest differs")
        require(
            packet.get("source_pending_packet_digest") == pending_digest,
            "active authority is not derived from the frozen pending packet",
        )
    else:
        require(packet.get("status") == "pending", "authorization status differs")
        unsigned = dict(packet)
        pending_digest = unsigned.pop("pending_packet_digest", None)
        require(pending_digest == canonical_sha256(unsigned), "pending authorization digest differs")
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
            raise AuthorizationError("v0.5 Judge compatibility execution authorization is pending")

    if check_runtime and active:
        validate_runtime(packet)
    return {
        "status": "authorized" if active else "pending",
        "authorization_id": packet["authorization_id"],
        "authorization_digest": canonical_sha256(packet),
        "protocol_sha256": packet["protocol"]["sha256"],
        "lock_digest": packet["protocol"]["lock_digest"],
        "judge_compatibility_protocol_sha256": sha256_file(AMENDMENT),
        "judge_compatibility_lock_digest": lock["lock_digest"],
        "authorization_configuration_digest": configuration_digest,
        "maximum_committed_batches": 5,
        "maximum_generation_calls": 17,
        "maximum_judge_calls": 34,
        "remaining_generation_calls": 14,
        "remaining_judge_calls": 30,
        "token_budget": packet["token_or_cost_budget"],
        "remaining_counted_tokens": 2_909_900,
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
    except (
        OSError,
        json.JSONDecodeError,
        AuthorizationError,
        subprocess.SubprocessError,
        ValueError,
    ) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
