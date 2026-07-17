#!/usr/bin/env python3
"""Fail-closed validation for the real #119 execution authorization packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
PROTOCOL_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.2.py"
SEALED_INDEX = BETA_ROOT / "fixtures" / "sealed-shadow-index.json"
DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.2.pending.json"
)
REQUIRED_INDEPENDENCE = {
    "arm-implementation",
    "generator-execution",
    "judge-evaluation",
}


class AuthorizationError(ValueError):
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
        raise AuthorizationError(f"{label} must be a repository-relative path")
    path = (REPO_ROOT / value).resolve(strict=False)
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise AuthorizationError(f"{label} leaves the repository") from exc
    return path


def parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise AuthorizationError(f"{label} is missing")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorizationError(f"{label} is not an ISO-8601 timestamp") from exc


def validate_protocol_receipt(authorization: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = authorization.get("protocol")
    if not isinstance(receipt, Mapping):
        raise AuthorizationError("protocol receipt is missing")
    protocol_path = repo_path(receipt.get("path"), "protocol.path")
    lock_path = repo_path(receipt.get("lock_path"), "protocol.lock_path")
    if not protocol_path.is_file() or sha256_file(protocol_path) != receipt.get("sha256"):
        raise AuthorizationError("authorization protocol path or digest differs")
    if not lock_path.is_file():
        raise AuthorizationError("authorization protocol lock is missing")
    validation = subprocess.run(
        [
            "python3",
            str(PROTOCOL_VALIDATOR),
            "validate",
            "--protocol",
            str(protocol_path),
            "--lock",
            str(lock_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if validation.returncode != 0:
        raise AuthorizationError(
            f"frozen protocol validation failed: {validation.stderr.strip() or validation.stdout.strip()}"
        )
    report = json.loads(validation.stdout)
    if report.get("protocol_sha256") != receipt.get("sha256"):
        raise AuthorizationError("authorization digest does not resolve through the lock")
    if report.get("lock_digest") != receipt.get("lock_digest"):
        raise AuthorizationError("authorization lock digest differs")
    return load_json(protocol_path), load_json(lock_path)


def validate_configuration(authorization: Mapping[str, Any], protocol: Mapping[str, Any]) -> None:
    parameters = protocol["authorization_parameters"]
    proposed = parameters["proposed_authorization"]
    expected = {
        "host_surface": parameters["authorized_host_surface"],
        "planned_generation_outputs": parameters["planned_generation_outputs"],
        "planned_judge_records": parameters["planned_judge_records"],
        "generator_model_by_host": proposed["generator_model_by_host"],
        "judge_model_and_reasoning": proposed["judge_model_and_reasoning"],
        "maximum_generation_calls": proposed["maximum_generation_calls"],
        "maximum_judge_calls": proposed["maximum_judge_calls"],
        "token_or_cost_budget": proposed["token_or_cost_budget"],
        "human_adjudicator": proposed["human_adjudicator"],
        "stop_authority": proposed["stop_authority"],
    }
    differences = {
        field: {"expected": value, "actual": authorization.get(field)}
        for field, value in expected.items()
        if authorization.get(field) != value
    }
    if differences:
        raise AuthorizationError(f"authorization configuration differs from v0.2: {differences}")


def validate_codex_runtime(authorization: Mapping[str, Any]) -> None:
    generator = authorization["generator_model_by_host"]["codex-plugin"]
    expected = f"codex-cli {generator['codex_cli_version']}"
    result = subprocess.run(
        ["codex", "--version"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0 or result.stdout.strip() != expected:
        observed = result.stdout.strip() or result.stderr.strip() or "unavailable"
        raise AuthorizationError(
            f"Codex CLI runtime differs from authorization: expected={expected!r}, observed={observed!r}"
        )


def validate_attestation(
    authorization: Mapping[str, Any],
    lock: Mapping[str, Any],
    confirmed_at: datetime,
) -> dict[str, Any]:
    path_value = authorization.get("sealed_case_attestation_path")
    if not isinstance(path_value, str) or not path_value:
        raise AuthorizationError("independent sealed-case custodian attestation is missing")
    path = Path(path_value).expanduser().resolve(strict=False)
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise AuthorizationError("sealed-case attestation must be stored outside the implementation repository")
    if not path.is_file():
        raise AuthorizationError("sealed-case attestation path is unavailable")
    attestation = load_json(path)
    if attestation.get("schema_version") != "mindthus-beta2-sealed-case-attestation-v0.1":
        raise AuthorizationError("sealed-case attestation schema differs")
    unsigned = dict(attestation)
    observed_digest = unsigned.pop("attestation_digest", None)
    if observed_digest != canonical_sha256(unsigned):
        raise AuthorizationError("sealed-case attestation digest differs")
    custodian = attestation.get("custodian_id")
    if not isinstance(custodian, str) or not custodian:
        raise AuthorizationError("sealed-case custodian identity is missing")
    if custodian in {authorization.get("human_adjudicator"), authorization.get("stop_authority")}:
        raise AuthorizationError("sealed-case custodian is not independent from run authorities")
    if set(attestation.get("independent_from", [])) != REQUIRED_INDEPENDENCE:
        raise AuthorizationError("sealed-case custodian independence boundary is incomplete")
    for field in (
        "content_absent_from_implementation_repository",
        "content_not_disclosed_to_arm_implementation",
        "same_content_across_arms",
        "judge_blinding_preserved",
    ):
        if attestation.get(field) is not True:
            raise AuthorizationError(f"sealed-case attestation does not affirm {field}")
    frozen_at = parse_time(lock.get("frozen_at_utc"), "protocol frozen_at_utc")
    attested_at = parse_time(attestation.get("attested_at_utc"), "attestation attested_at_utc")
    if not frozen_at < attested_at < confirmed_at:
        raise AuthorizationError("custodian attestation must occur after freeze and before authorization")

    index = load_json(SEALED_INDEX)
    expected_receipts = {
        item["case_id"]: item["receipt_sha256"] for item in index.get("cases", [])
    }
    bindings = attestation.get("case_bindings")
    if not isinstance(bindings, list):
        raise AuthorizationError("sealed-case bindings are missing")
    observed_receipts: dict[str, str] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping):
            raise AuthorizationError("sealed-case binding is malformed")
        case_id = str(binding.get("case_id") or "")
        if case_id in observed_receipts:
            raise AuthorizationError("sealed-case binding contains a duplicate case")
        observed_receipts[case_id] = str(binding.get("receipt_sha256") or "")
        content_path = Path(str(binding.get("sealed_content_path") or "")).expanduser().resolve(
            strict=False
        )
        try:
            content_path.relative_to(REPO_ROOT.resolve())
        except ValueError:
            pass
        else:
            raise AuthorizationError("sealed prompt content must remain outside the repository")
        if not content_path.is_file():
            raise AuthorizationError(f"sealed prompt content is unavailable for {case_id}")
        if sha256_file(content_path) != binding.get("sealed_content_sha256"):
            raise AuthorizationError(f"sealed prompt content digest differs for {case_id}")
    if observed_receipts != expected_receipts:
        raise AuthorizationError("sealed-case bindings do not exactly match the four frozen receipts")
    return {
        "custodian_id": custodian,
        "attestation_digest": observed_digest,
        "sealed_case_count": len(bindings),
    }


def validate_authorization(path: Path, *, check_runtime: bool = False) -> dict[str, Any]:
    authorization = load_json(path)
    if authorization.get("schema_version") != "mindthus-beta2-execution-authorization-v0.1":
        raise AuthorizationError("unsupported execution authorization schema")
    validator_path = repo_path(
        authorization.get("authorization_validator_path"),
        "authorization_validator_path",
    )
    if validator_path != Path(__file__).resolve():
        raise AuthorizationError("authorization validator path differs")
    if sha256_file(validator_path) != authorization.get("authorization_validator_sha256"):
        raise AuthorizationError("authorization validator digest differs")
    protocol, lock = validate_protocol_receipt(authorization)
    validate_configuration(authorization, protocol)
    if authorization.get("status") != "authorized":
        blockers = authorization.get("blocking_requirements", [])
        raise AuthorizationError(f"authorization is pending: {blockers}")
    if authorization.get("blocking_requirements") != []:
        raise AuthorizationError("authorized packet still contains blocking requirements")
    if check_runtime:
        validate_codex_runtime(authorization)
    confirmation = authorization.get("human_confirmation")
    if not isinstance(confirmation, Mapping):
        raise AuthorizationError("post-freeze human confirmation is missing")
    if confirmation.get("authority") != authorization.get("stop_authority"):
        raise AuthorizationError("digest confirmation does not come from stop authority")
    if confirmation.get("confirmed_protocol_digest") != authorization["protocol"]["sha256"]:
        raise AuthorizationError("human confirmation does not name the exact protocol digest")
    confirmed_at = parse_time(confirmation.get("confirmed_at_utc"), "confirmation confirmed_at_utc")
    if confirmed_at <= parse_time(lock.get("frozen_at_utc"), "protocol frozen_at_utc"):
        raise AuthorizationError("human digest confirmation must occur after protocol freeze")
    attestation = validate_attestation(authorization, lock, confirmed_at)
    return {
        "status": "authorized",
        "authorization_id": authorization["authorization_id"],
        "protocol_sha256": authorization["protocol"]["sha256"],
        "lock_digest": authorization["protocol"]["lock_digest"],
        "authorization_digest": canonical_sha256(authorization),
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_budget": authorization["token_or_cost_budget"],
        "sealed_case_attestation": attestation,
        "stop_authority": authorization["stop_authority"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = validate_authorization(args.authorization, check_runtime=True)
        returncode = 0
    except (OSError, json.JSONDecodeError, AuthorizationError, subprocess.SubprocessError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        returncode = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
