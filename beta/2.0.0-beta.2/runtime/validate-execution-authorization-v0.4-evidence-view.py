#!/usr/bin/env python3
"""Fail-closed validation for the additive v0.4 evidence-view authority."""

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
BASE_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-blinded-view.1.json"
)
BASE_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-blinded-view.py"
)
AMENDMENT = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.json"
LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.lock.json"
AMENDMENT_VALIDATOR = (
    BETA_ROOT / "runtime" / "freeze-evaluation-evidence-view-v0.4.py"
)
DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-evidence-view.1.json"
)


class EvidenceViewAuthorizationError(ValueError):
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


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise EvidenceViewAuthorizationError(reason)


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise EvidenceViewAuthorizationError(f"{label} must be repository-relative")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise EvidenceViewAuthorizationError(f"{label} leaves repository") from exc
    return path


def run_validation(command: list[str], label: str) -> dict[str, Any]:
    result = subprocess.run(
        command, cwd=REPO_ROOT, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise EvidenceViewAuthorizationError(
            f"{label} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    payload = json.loads(result.stdout)
    require(isinstance(payload, dict), f"{label} returned a non-object")
    return payload


def expected_configuration(authorization: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "protocol_sha256": authorization["protocol"]["sha256"],
        "generation_recovery_lock_digest": authorization["recovery_amendment"][
            "lock_digest"
        ],
        "judge_compatibility_lock_digest": authorization[
            "judge_compatibility_amendment"
        ]["lock_digest"],
        "blinded_view_lock_digest": authorization["blinded_view_amendment"][
            "lock_digest"
        ],
        "evidence_view_lock_digest": authorization["evidence_view_amendment"][
            "lock_digest"
        ],
        "generator_model_by_host": authorization["generator_model_by_host"],
        "judge_model_and_reasoning": authorization["judge_model_and_reasoning"],
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_or_cost_budget": authorization["token_or_cost_budget"],
        "recovery_budget": authorization["recovery_budget"],
        "blinded_view_budget": authorization["blinded_view_budget"],
        "evidence_view_budget": authorization["evidence_view_budget"],
        "stop_authority": authorization["stop_authority"],
    }


def validate_codex_runtime(authorization: Mapping[str, Any]) -> None:
    generator = authorization["generator_model_by_host"]["codex-plugin"]
    expected = f"codex-cli {generator['codex_cli_version']}"
    result = subprocess.run(
        ["codex", "--version"], cwd=REPO_ROOT, text=True, capture_output=True
    )
    observed = result.stdout.strip() or result.stderr.strip() or "unavailable"
    require(
        result.returncode == 0 and observed == expected,
        f"Codex CLI runtime differs: expected={expected!r}, observed={observed!r}",
    )


def validate_authorization(
    path: Path, *, check_runtime: bool = False
) -> dict[str, Any]:
    authorization = load_json(path)
    base = load_json(BASE_AUTHORIZATION)
    amendment = load_json(AMENDMENT)
    lock = load_json(LOCK)
    require(
        authorization.get("schema_version")
        == "mindthus-beta2-execution-authorization-v0.2",
        "unsupported execution authorization schema",
    )
    validator = repo_path(
        authorization.get("authorization_validator_path"),
        "authorization_validator_path",
    )
    require(validator == Path(__file__).resolve(), "authorization validator path differs")
    require(
        authorization.get("authorization_validator_sha256") == sha256_file(validator),
        "authorization validator digest differs",
    )
    prior = run_validation(
        ["python3", str(BASE_VALIDATOR), "--authorization", str(BASE_AUTHORIZATION)],
        "blinded-view authorization",
    )
    require(prior.get("status") == "authorized", "prior authority is inactive")
    frozen = run_validation(
        [
            "python3",
            str(AMENDMENT_VALIDATOR),
            "validate",
            "--protocol",
            str(AMENDMENT),
            "--lock",
            str(LOCK),
        ],
        "evidence-view amendment",
    )
    require(frozen.get("status") == "frozen", "evidence-view amendment is not frozen")

    unchanged = (
        "schema_version",
        "status",
        "protocol",
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
        "release_preparation",
        "blocking_requirements",
        "recovery_amendment",
        "recovery_budget",
        "judge_compatibility_amendment",
        "blinded_view_amendment",
        "blinded_view_budget",
        "token_or_cost_budget",
    )
    for field in unchanged:
        require(
            authorization.get(field) == base.get(field),
            f"{field} differs from prior authority",
        )
    expected_budget = {
        "prior_measured_token_ceiling": 17599744,
        "amended_measured_token_ceiling": 17599744,
        "source_judge_calls_used": 36,
        "retrospective_rejudge_records": 6,
        "remaining_matched_judge_records": 420,
        "minimum_total_judge_calls": 462,
        "minimum_retry_headroom": 18,
        "budget_expansion": False,
    }
    require(
        authorization.get("evidence_view_budget") == expected_budget,
        "evidence-view budget differs",
    )
    require(authorization.get("release_preparation") is False, "release preparation is authorized")

    receipt = authorization.get("evidence_view_amendment")
    require(isinstance(receipt, Mapping), "evidence-view amendment receipt is missing")
    require(receipt.get("path") == str(AMENDMENT.relative_to(REPO_ROOT)), "amendment path differs")
    require(receipt.get("sha256") == sha256_file(AMENDMENT), "amendment digest differs")
    require(receipt.get("lock_path") == str(LOCK.relative_to(REPO_ROOT)), "lock path differs")
    require(receipt.get("lock_digest") == lock.get("lock_digest"), "lock digest differs")
    require(receipt.get("amendment_id") == "0.4-evidence-view.1", "amendment id differs")
    require(
        receipt.get("source_judge_attempt_set_digest")
        == amendment["retained_source_run"]["judge_attempt_set_digest"]
        and receipt.get("source_judge_record_set_digest")
        == amendment["retained_source_run"]["judge_record_set_digest"],
        "source Judge binding differs",
    )

    human = authorization.get("human_authorization")
    require(isinstance(human, Mapping), "human authorization is missing")
    require(
        human.get("authority") == "William" == authorization.get("stop_authority"),
        "human authority differs",
    )
    require(
        human.get("authorized_configuration_digest")
        == canonical_sha256(expected_configuration(authorization)),
        "authorized evidence-view configuration differs",
    )
    binding = human.get("digest_binding")
    require(isinstance(binding, Mapping), "evidence-view digest binding is missing")
    require(
        binding.get("mode")
        == "additive-v0.4-evidence-view-after-frozen-smoke-veto",
        "evidence-view binding mode differs",
    )
    require(
        binding.get("bound_evidence_view_digest") == receipt["sha256"],
        "bound amendment differs",
    )
    require(
        binding.get("bound_evidence_view_lock_digest") == receipt["lock_digest"],
        "bound lock differs",
    )
    frozen_at = datetime.fromisoformat(str(lock["frozen_at_utc"]).replace("Z", "+00:00"))
    bound_at = datetime.fromisoformat(str(binding["bound_at_utc"]).replace("Z", "+00:00"))
    created_at = datetime.fromisoformat(
        str(authorization["packet_created_at_utc"]).replace("Z", "+00:00")
    )
    require(frozen_at <= bound_at <= created_at, "evidence-view binding predates freeze")
    if check_runtime:
        validate_codex_runtime(authorization)
    return {
        "status": "authorized",
        "authorization_id": authorization["authorization_id"],
        "authorization_digest": canonical_sha256(authorization),
        "protocol_sha256": authorization["protocol"]["sha256"],
        "lock_digest": authorization["protocol"]["lock_digest"],
        "recovery_protocol_sha256": authorization["recovery_amendment"]["sha256"],
        "recovery_lock_digest": authorization["recovery_amendment"]["lock_digest"],
        "judge_compatibility_protocol_sha256": authorization[
            "judge_compatibility_amendment"
        ]["sha256"],
        "judge_compatibility_lock_digest": authorization[
            "judge_compatibility_amendment"
        ]["lock_digest"],
        "blinded_view_protocol_sha256": authorization["blinded_view_amendment"][
            "sha256"
        ],
        "blinded_view_lock_digest": authorization["blinded_view_amendment"][
            "lock_digest"
        ],
        "evidence_view_protocol_sha256": receipt["sha256"],
        "evidence_view_lock_digest": receipt["lock_digest"],
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_budget": authorization["token_or_cost_budget"],
        "unknown_usage_reserved_tokens": 4352000,
        "cumulative_authority": authorization["cumulative_authority"],
        "stop_authority": authorization["stop_authority"],
        "release_preparation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    args = parser.parse_args()
    try:
        report = validate_authorization(
            args.authorization.resolve(), check_runtime=True
        )
        code = 0
    except (
        OSError,
        json.JSONDecodeError,
        EvidenceViewAuthorizationError,
        subprocess.SubprocessError,
        ValueError,
    ) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
