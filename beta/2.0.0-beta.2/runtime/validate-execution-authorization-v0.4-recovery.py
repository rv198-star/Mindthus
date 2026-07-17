#!/usr/bin/env python3
"""Fail-closed validation for the additive #119 v0.4 recovery authority."""

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
BASE_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"
BASE_AUTHORIZATION_VALIDATOR = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4.py"
RECOVERY_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.json"
RECOVERY_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.lock.json"
RECOVERY_PROTOCOL_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-recovery-v0.4.py"
DEFAULT_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-recovery.1.json"


class RecoveryAuthorizationError(ValueError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise RecoveryAuthorizationError(f"{label} must be a repository-relative path")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise RecoveryAuthorizationError(f"{label} leaves repository") from exc
    return path


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RecoveryAuthorizationError(reason)


def run_validation(command: list[str], label: str) -> dict[str, Any]:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise RecoveryAuthorizationError(
            f"{label} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RecoveryAuthorizationError(f"{label} returned a non-object")
    return payload


def validate_codex_runtime(authorization: Mapping[str, Any]) -> None:
    generator = authorization["generator_model_by_host"]["codex-plugin"]
    expected = f"codex-cli {generator['codex_cli_version']}"
    result = subprocess.run(["codex", "--version"], cwd=REPO_ROOT, text=True, capture_output=True)
    observed = result.stdout.strip() or result.stderr.strip() or "unavailable"
    if result.returncode != 0 or observed != expected:
        raise RecoveryAuthorizationError(
            f"Codex CLI runtime differs: expected={expected!r}, observed={observed!r}"
        )


def expected_configuration(
    authorization: Mapping[str, Any], amendment: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "protocol_sha256": authorization["protocol"]["sha256"],
        "recovery_lock_digest": authorization["recovery_amendment"]["lock_digest"],
        "generator_model_by_host": authorization["generator_model_by_host"],
        "judge_model_and_reasoning": authorization["judge_model_and_reasoning"],
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_or_cost_budget": authorization["token_or_cost_budget"],
        "recovery_budget": authorization["recovery_budget"],
        "stop_authority": authorization["stop_authority"],
    }


def validate_authorization(path: Path, *, check_runtime: bool = False) -> dict[str, Any]:
    authorization = load_json(path)
    base = load_json(BASE_AUTHORIZATION)
    amendment = load_json(RECOVERY_PROTOCOL)
    lock = load_json(RECOVERY_LOCK)
    require(
        authorization.get("schema_version") == "mindthus-beta2-execution-authorization-v0.2",
        "unsupported execution authorization schema",
    )
    validator = repo_path(authorization.get("authorization_validator_path"), "authorization_validator_path")
    require(validator == Path(__file__).resolve(), "authorization validator path differs")
    require(authorization.get("authorization_validator_sha256") == sha256_file(validator), "authorization validator digest differs")

    base_report = run_validation(
        ["python3", str(BASE_AUTHORIZATION_VALIDATOR), "--authorization", str(BASE_AUTHORIZATION)],
        "base v0.4 authorization",
    )
    require(base_report.get("status") == "authorized", "base v0.4 authorization is inactive")
    recovery_report = run_validation(
        [
            "python3",
            str(RECOVERY_PROTOCOL_VALIDATOR),
            "validate",
            "--protocol",
            str(RECOVERY_PROTOCOL),
            "--lock",
            str(RECOVERY_LOCK),
        ],
        "recovery amendment",
    )
    require(recovery_report.get("status") == "frozen", "recovery amendment is not frozen")

    protocol_receipt = authorization.get("protocol")
    require(isinstance(protocol_receipt, Mapping), "base protocol receipt is missing")
    require(protocol_receipt == base["protocol"], "base v0.4 protocol receipt differs")
    recovery_receipt = authorization.get("recovery_amendment")
    require(isinstance(recovery_receipt, Mapping), "recovery receipt is missing")
    require(recovery_receipt.get("path") == str(RECOVERY_PROTOCOL.relative_to(REPO_ROOT)), "recovery path differs")
    require(recovery_receipt.get("sha256") == sha256_file(RECOVERY_PROTOCOL), "recovery digest differs")
    require(recovery_receipt.get("lock_path") == str(RECOVERY_LOCK.relative_to(REPO_ROOT)), "recovery lock path differs")
    require(recovery_receipt.get("lock_digest") == lock.get("lock_digest"), "recovery lock digest differs")
    require(recovery_receipt.get("amendment_id") == "0.4-recovery.1", "recovery amendment id differs")
    require(recovery_receipt.get("base_protocol_sha256") == base_report.get("protocol_sha256"), "recovery base digest differs")

    unchanged_fields = (
        "host_surface",
        "planned_generation_outputs",
        "planned_judge_records",
        "generator_model_by_host",
        "judge_model_and_reasoning",
        "maximum_generation_calls",
        "maximum_judge_calls",
        "human_adjudicator",
        "stop_authority",
        "cumulative_authority",
        "case_scope",
        "sealed_case_attestation_path",
    )
    for field in unchanged_fields:
        require(authorization.get(field) == base.get(field), f"{field} differs from base v0.4")
    require(authorization["maximum_generation_calls"] == 239, "generation ceiling differs")
    require(authorization["maximum_judge_calls"] == 480, "judge ceiling differs")
    expected_token_budget = {
        **base["token_or_cost_budget"],
        "maximum": amendment["budget_accounting"]["amended_measured_token_ceiling"],
    }
    require(authorization.get("token_or_cost_budget") == expected_token_budget, "amended measured token ceiling differs")
    expected_recovery_budget = {
        "base_v0_4_measured_token_ceiling": 21951744,
        "unknown_usage_reserved_tokens": 2176000,
        "amended_measured_token_ceiling": 19775744,
        "budget_expansion": False,
    }
    require(authorization.get("recovery_budget") == expected_recovery_budget, "recovery budget receipt differs")
    require(19775744 + 2176000 == 21951744, "recovery budget does not balance")
    require(authorization.get("status") == "authorized", "recovery authority is inactive")
    require(authorization.get("blocking_requirements") == [], "recovery authority has blockers")
    require(authorization.get("release_preparation") is False, "release preparation is authorized")

    human = authorization.get("human_authorization")
    require(isinstance(human, Mapping), "human authorization basis is missing")
    require(human.get("authority") == "William", "human authority differs")
    require(human.get("authority") == authorization.get("stop_authority"), "stop authority differs")
    require(human.get("source_evidence_ids") == ["E22324196", "Eea1fda65", "E46a11b5c"], "human evidence anchors differ")
    require(human.get("source_instructions")[-1:] == [amendment["human_authorization"]["source_instruction"]], "recovery instruction differs")
    require(human.get("authorized_at_utc") == amendment["human_authorization"]["authorized_at_utc"], "recovery authorization time differs")
    expected = expected_configuration(authorization, amendment)
    require(human.get("authorized_configuration_digest") == canonical_sha256(expected), "authorized recovery configuration differs")
    require(
        human.get("must_escalate_on")
        == [
            "the single recovery attempt fails",
            "binary primary-axis judge disagreement",
            "new spend beyond cumulative ceilings",
            "release or publication decision",
            "irreversible action",
        ],
        "human escalation boundary differs",
    )
    binding = human.get("digest_binding")
    require(isinstance(binding, Mapping), "recovery digest binding is missing")
    require(binding.get("mode") == "additive-v0.4-recovery-after-frozen-amendment", "recovery binding mode differs")
    require(binding.get("bound_protocol_digest") == authorization["protocol"]["sha256"], "bound base protocol differs")
    require(binding.get("bound_protocol_lock_digest") == authorization["protocol"]["lock_digest"], "bound base lock differs")
    require(binding.get("bound_recovery_digest") == recovery_receipt["sha256"], "bound recovery protocol differs")
    require(binding.get("bound_recovery_lock_digest") == recovery_receipt["lock_digest"], "bound recovery lock differs")
    frozen_at = datetime.fromisoformat(str(lock["frozen_at_utc"]).replace("Z", "+00:00"))
    bound_at = datetime.fromisoformat(str(binding["bound_at_utc"]).replace("Z", "+00:00"))
    created_at = datetime.fromisoformat(str(authorization["packet_created_at_utc"]).replace("Z", "+00:00"))
    require(frozen_at <= bound_at <= created_at, "recovery binding predates its freeze")
    if check_runtime:
        validate_codex_runtime(authorization)
    return {
        "status": "authorized",
        "authorization_id": authorization["authorization_id"],
        "authorization_digest": canonical_sha256(authorization),
        "protocol_sha256": authorization["protocol"]["sha256"],
        "lock_digest": authorization["protocol"]["lock_digest"],
        "recovery_protocol_sha256": recovery_receipt["sha256"],
        "recovery_lock_digest": recovery_receipt["lock_digest"],
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_budget": authorization["token_or_cost_budget"],
        "unknown_usage_reserved_tokens": 2176000,
        "cumulative_authority": authorization["cumulative_authority"],
        "stop_authority": authorization["stop_authority"],
        "release_preparation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    args = parser.parse_args()
    try:
        report = validate_authorization(args.authorization.resolve(), check_runtime=True)
        code = 0
    except (OSError, json.JSONDecodeError, RecoveryAuthorizationError, subprocess.SubprocessError, ValueError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
