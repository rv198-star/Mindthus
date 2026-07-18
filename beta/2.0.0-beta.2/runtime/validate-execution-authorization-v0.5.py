#!/usr/bin/env python3
"""Fail-closed validation for #119 incremental execution authorization v0.5."""

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
PROTOCOL_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.5.py"
DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.pending.json"
)


class AuthorizationError(ValueError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise AuthorizationError(f"{label} must be repository-relative")
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
    if sha256_file(protocol_path) != receipt.get("sha256"):
        raise AuthorizationError("authorization protocol digest differs")
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
            "frozen v0.5 protocol validation failed: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    report = json.loads(result.stdout)
    if report.get("protocol_sha256") != receipt.get("sha256"):
        raise AuthorizationError("authorization protocol does not resolve through lock")
    if report.get("lock_digest") != receipt.get("lock_digest"):
        raise AuthorizationError("authorization lock digest differs")
    return load_json(protocol_path), load_json(lock_path)


def expected_initial_configuration(protocol: Mapping[str, Any]) -> dict[str, Any]:
    parameters = protocol["authorization_parameters"]
    initial = parameters["initial_batch_authorization_recommendation"]
    proposed = parameters["proposed_authorization"]
    budget = dict(proposed["token_or_cost_budget"])
    budget["maximum"] = initial["aggregate_token_ceiling"]
    return {
        "host_surface": parameters["authorized_host_surface"],
        "maximum_committed_batches": initial["maximum_committed_batches"],
        "planned_generation_outputs": initial["maximum_committed_batches"] * 3,
        "planned_judge_records": initial["maximum_committed_batches"] * 6,
        "generator_model_by_host": proposed["generator_model_by_host"],
        "judge_model_and_reasoning": proposed["judge_model_and_reasoning"],
        "maximum_generation_calls": initial["maximum_generation_calls"],
        "maximum_judge_calls": initial["maximum_judge_calls"],
        "token_or_cost_budget": budget,
        "human_adjudicator": proposed["human_adjudicator"],
        "stop_authority": proposed["stop_authority"],
    }


def validate_authorization(
    path: Path, *, require_active: bool = True, check_runtime: bool = False
) -> dict[str, Any]:
    authorization = load_json(path)
    if authorization.get("schema_version") != "mindthus-beta2-execution-authorization-v0.5":
        raise AuthorizationError("unsupported v0.5 authorization schema")
    validator = repo_path(
        authorization.get("authorization_validator_path"),
        "authorization_validator_path",
    )
    if validator != Path(__file__).resolve() or authorization.get(
        "authorization_validator_sha256"
    ) != sha256_file(validator):
        raise AuthorizationError("v0.5 authorization validator binding differs")
    protocol, lock = validate_protocol_receipt(authorization)
    expected = expected_initial_configuration(protocol)
    differences = {
        field: {"expected": value, "actual": authorization.get(field)}
        for field, value in expected.items()
        if authorization.get(field) != value
    }
    if differences:
        raise AuthorizationError(f"v0.5 initial configuration differs: {differences}")
    if authorization.get("prior_consumption") != {
        "protocol_versions": ["0.3", "0.4"],
        "generation_calls": 146,
        "judge_calls": 42,
        "counted_tokens": 8_133_510,
    }:
        raise AuthorizationError("v0.5 prior consumption differs")
    expected_cumulative = {
        "maximum_generation_calls": 163,
        "maximum_judge_calls": 76,
        "aggregate_token_ceiling": 11_133_510,
    }
    if authorization.get("requested_cumulative_ceiling") != expected_cumulative:
        raise AuthorizationError("v0.5 requested cumulative ceiling differs")
    if authorization.get("release_preparation") is not False:
        raise AuthorizationError("v0.5 does not authorize release preparation")
    basis = authorization.get("human_authorization")
    if not isinstance(basis, Mapping) or basis.get("authority") != "William":
        raise AuthorizationError("v0.5 human authority differs")
    if basis.get("design_change_instruction") != "那按你的建议调整吧" or basis.get(
        "design_change_evidence_id"
    ) != "E47ad3faa":
        raise AuthorizationError("v0.5 design authority evidence differs")

    active = authorization.get("status") == "authorized"
    if active:
        if authorization.get("blocking_requirements") != []:
            raise AuthorizationError("active v0.5 authorization still has blockers")
        if basis.get("semantic_execution_authorized") is not True:
            raise AuthorizationError("v0.5 semantic execution authority is missing")
        if basis.get("authorized_protocol_digest") != authorization["protocol"]["sha256"]:
            raise AuthorizationError("v0.5 authorized protocol digest differs")
        if basis.get("authorized_configuration_digest") != canonical_sha256(expected):
            raise AuthorizationError("v0.5 authorized configuration digest differs")
        authorized_at = parse_time(basis.get("authorized_at_utc"), "authorized_at_utc")
        frozen_at = parse_time(lock.get("frozen_at_utc"), "frozen_at_utc")
        if authorized_at < frozen_at:
            raise AuthorizationError("v0.5 authorization predates freeze")
    elif require_active:
        raise AuthorizationError("v0.5 semantic execution authorization is pending")

    if check_runtime:
        generator = authorization["generator_model_by_host"]["codex-plugin"]
        result = subprocess.run(
            ["codex", "--version"], text=True, capture_output=True, cwd=REPO_ROOT
        )
        expected_version = f"codex-cli {generator['codex_cli_version']}"
        if result.returncode != 0 or result.stdout.strip() != expected_version:
            raise AuthorizationError("Codex CLI runtime differs")
        if not Path("/usr/bin/sandbox-exec").is_file():
            raise AuthorizationError("macOS sandbox-exec is unavailable")
    return {
        "status": "authorized" if active else "pending",
        "authorization_id": authorization["authorization_id"],
        "protocol_sha256": authorization["protocol"]["sha256"],
        "lock_digest": authorization["protocol"]["lock_digest"],
        "authorization_digest": canonical_sha256(authorization),
        "maximum_committed_batches": authorization["maximum_committed_batches"],
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_budget": authorization["token_or_cost_budget"],
        "stop_authority": authorization["stop_authority"],
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
    ) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
