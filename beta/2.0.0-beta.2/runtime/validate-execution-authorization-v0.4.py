#!/usr/bin/env python3
"""Fail-closed validation for evidence-honest #119 execution authorization v0.4."""

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
PROTOCOL_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.4.py"
DEFAULT_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"
EXPECTED_BINDING_MODE = "bounded-continuation-first-frozen-v0.4"
EXPECTED_INSTRUCTIONS = [
    "去掉4道隐藏题，继续",
    "推进，直到有具体结论或者必须我决策参与的时候才停下来",
]
EXPECTED_EVIDENCE_IDS = ["E22324196", "Eea1fda65"]


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
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise AuthorizationError(f"{label} leaves repository") from exc
    return path


def parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise AuthorizationError(f"{label} is missing")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorizationError(f"{label} is not ISO-8601") from exc


def validate_protocol_receipt(
    authorization: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = authorization.get("protocol")
    if not isinstance(receipt, Mapping):
        raise AuthorizationError("protocol receipt is missing")
    protocol_path = repo_path(receipt.get("path"), "protocol.path")
    lock_path = repo_path(receipt.get("lock_path"), "protocol.lock_path")
    if not protocol_path.is_file() or sha256_file(protocol_path) != receipt.get("sha256"):
        raise AuthorizationError("authorization protocol path or digest differs")
    if not lock_path.is_file():
        raise AuthorizationError("authorization protocol lock is missing")
    result = subprocess.run(
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
    if result.returncode != 0:
        raise AuthorizationError(
            "frozen protocol validation failed: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    report = json.loads(result.stdout)
    if report.get("protocol_sha256") != receipt.get("sha256"):
        raise AuthorizationError("authorization digest does not resolve through lock")
    if report.get("lock_digest") != receipt.get("lock_digest"):
        raise AuthorizationError("authorization lock digest differs")
    return load_json(protocol_path), load_json(lock_path)


def expected_configuration(protocol: Mapping[str, Any]) -> dict[str, Any]:
    parameters = protocol["authorization_parameters"]
    proposed = parameters["proposed_authorization"]
    return {
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


def validate_configuration(
    authorization: Mapping[str, Any], protocol: Mapping[str, Any]
) -> dict[str, Any]:
    expected = expected_configuration(protocol)
    differences = {
        field: {"expected": value, "actual": authorization.get(field)}
        for field, value in expected.items()
        if authorization.get(field) != value
    }
    if differences:
        raise AuthorizationError(f"authorization configuration differs from v0.4: {differences}")
    cumulative = protocol["authorization_parameters"]["cumulative_authority"]
    if authorization.get("cumulative_authority") != cumulative:
        raise AuthorizationError("authorization cumulative authority differs")
    if cumulative.get("budget_expansion") is not False:
        raise AuthorizationError("authorization expands the prior budget")
    prior = cumulative["prior_consumption"]
    available = cumulative["v04_available"]
    if prior["generation_calls"] + available["maximum_generation_calls"] != cumulative[
        "maximum_generation_calls"
    ]:
        raise AuthorizationError("generation authority accounting does not balance")
    if prior["judge_calls"] + available["maximum_judge_calls"] != cumulative[
        "maximum_judge_calls"
    ]:
        raise AuthorizationError("judge authority accounting does not balance")
    if prior["counted_tokens"] + available["aggregate_token_ceiling"] != cumulative[
        "aggregate_token_ceiling"
    ]:
        raise AuthorizationError("token authority accounting does not balance")
    return expected


def validate_case_scope(
    authorization: Mapping[str, Any], protocol: Mapping[str, Any]
) -> None:
    workload = protocol["workload"]
    expected = {
        "matched_case_ids": workload["matched_case_ids"],
        "excluded_case_ids": workload["excluded_case_ids"],
        "matched_case_count": 25,
        "excluded_sealed_case_count": 4,
        "included_sealed_case_count": 0,
        "evidence_visibility": "implementation-visible",
        "host_session_scope": "startup-only",
        "claim_ceiling": "visible-case Codex startup-session exploratory evidence only",
    }
    if authorization.get("case_scope") != expected:
        raise AuthorizationError("authorization case scope differs from frozen v0.4")
    if authorization.get("sealed_case_attestation_path") is not None:
        raise AuthorizationError("v0.4 must not bind excluded sealed cases")


def validate_human_basis(
    authorization: Mapping[str, Any],
    protocol: Mapping[str, Any],
    lock: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    basis = authorization.get("human_authorization")
    if not isinstance(basis, Mapping):
        raise AuthorizationError("human authorization basis is missing")
    if basis.get("authority") != "William" or basis.get("authority") != authorization.get(
        "stop_authority"
    ):
        raise AuthorizationError("human authorization authority differs")
    if basis.get("source_instructions") != EXPECTED_INSTRUCTIONS:
        raise AuthorizationError("human authorization instructions differ")
    if basis.get("source_evidence_ids") != EXPECTED_EVIDENCE_IDS:
        raise AuthorizationError("human authorization evidence anchors differ")
    if basis.get("authorized_protocol_version") != "0.4":
        raise AuthorizationError("human authorization protocol version differs")
    if basis.get("authorized_configuration_digest") != canonical_sha256(expected):
        raise AuthorizationError("human authorization configuration digest differs")
    if basis.get("must_escalate_on") != [
        "binary primary-axis judge disagreement",
        "new spend beyond cumulative ceilings",
        "release or publication decision",
        "irreversible action",
    ]:
        raise AuthorizationError("human escalation boundary differs")
    binding = basis.get("digest_binding")
    if not isinstance(binding, Mapping) or binding.get("mode") != EXPECTED_BINDING_MODE:
        raise AuthorizationError("v0.4 digest binding mode differs")
    if binding.get("bound_protocol_digest") != authorization["protocol"]["sha256"]:
        raise AuthorizationError("v0.4 bound protocol digest differs")
    if binding.get("bound_lock_digest") != authorization["protocol"]["lock_digest"]:
        raise AuthorizationError("v0.4 bound lock digest differs")
    authorized_at = parse_time(basis.get("authorized_at_utc"), "authorized_at_utc")
    frozen_at = parse_time(lock.get("frozen_at_utc"), "frozen_at_utc")
    bound_at = parse_time(binding.get("bound_at_utc"), "bound_at_utc")
    created_at = parse_time(authorization.get("packet_created_at_utc"), "packet_created_at_utc")
    if not authorized_at < frozen_at <= bound_at <= created_at:
        raise AuthorizationError("v0.4 binding must follow authorization and freeze")
    if protocol["authorization_parameters"].get("delegated_digest_binding_allowed") is not True:
        raise AuthorizationError("protocol does not allow delegated binding")
    return {
        "mode": binding["mode"],
        "source_evidence_ids": basis["source_evidence_ids"],
        "authorized_at_utc": basis["authorized_at_utc"],
        "bound_at_utc": binding["bound_at_utc"],
    }


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
            f"Codex CLI runtime differs: expected={expected!r}, observed={observed!r}"
        )


def validate_authorization(path: Path, *, check_runtime: bool = False) -> dict[str, Any]:
    authorization = load_json(path)
    if authorization.get("schema_version") != "mindthus-beta2-execution-authorization-v0.2":
        raise AuthorizationError("unsupported execution authorization schema")
    validator = repo_path(
        authorization.get("authorization_validator_path"),
        "authorization_validator_path",
    )
    if validator != Path(__file__).resolve():
        raise AuthorizationError("authorization validator path differs")
    if authorization.get("authorization_validator_sha256") != sha256_file(validator):
        raise AuthorizationError("authorization validator digest differs")
    protocol, lock = validate_protocol_receipt(authorization)
    expected = validate_configuration(authorization, protocol)
    validate_case_scope(authorization, protocol)
    if authorization.get("status") != "authorized" or authorization.get(
        "blocking_requirements"
    ) != []:
        raise AuthorizationError("authorization is not active")
    if authorization.get("release_preparation") is not False:
        raise AuthorizationError("v0.4 does not authorize release preparation")
    binding = validate_human_basis(authorization, protocol, lock, expected)
    if check_runtime:
        validate_codex_runtime(authorization)
    return {
        "status": "authorized",
        "authorization_id": authorization["authorization_id"],
        "protocol_sha256": authorization["protocol"]["sha256"],
        "lock_digest": authorization["protocol"]["lock_digest"],
        "authorization_digest": canonical_sha256(authorization),
        "matched_case_count": 25,
        "included_sealed_case_count": 0,
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_budget": authorization["token_or_cost_budget"],
        "cumulative_authority": authorization["cumulative_authority"],
        "delegated_digest_binding": binding,
        "stop_authority": authorization["stop_authority"],
        "release_preparation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    args = parser.parse_args()
    try:
        report = validate_authorization(args.authorization, check_runtime=True)
        code = 0
    except (OSError, json.JSONDecodeError, AuthorizationError, subprocess.SubprocessError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
