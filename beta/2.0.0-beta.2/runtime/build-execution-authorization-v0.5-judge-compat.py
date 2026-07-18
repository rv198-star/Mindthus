#!/usr/bin/env python3
"""Build the pending v0.5 Judge compatibility recovery authorization on stdout."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
BASE_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.json"
AMENDMENT = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.json"
LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.lock.json"
VALIDATOR = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.5-judge-compat.py"


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


def authorized_configuration(packet: dict[str, Any]) -> dict[str, Any]:
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


def build() -> dict[str, Any]:
    base = read_json(BASE_AUTHORIZATION)
    amendment = read_json(AMENDMENT)
    lock = read_json(LOCK)
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
    packet: dict[str, Any] = {
        "schema_version": "mindthus-beta2-execution-authorization-v0.5-judge-compat.1",
        "authorization_id": "issue-119-codex-v0.5-judge-compat.1",
        "authorization_validator_path": display(VALIDATOR),
        "authorization_validator_sha256": sha256_file(VALIDATOR),
        "status": "pending",
        "packet_created_at_utc": datetime.now(timezone.utc).isoformat(),
        **{field: base[field] for field in unchanged},
        "base_authorization": {
            "path": display(BASE_AUTHORIZATION),
            "file_sha256": sha256_file(BASE_AUTHORIZATION),
            "authorization_digest": canonical_sha256(base),
        },
        "judge_compatibility_amendment": {
            "path": display(AMENDMENT),
            "sha256": sha256_file(AMENDMENT),
            "lock_path": display(LOCK),
            "lock_digest": lock["lock_digest"],
            "amendment_id": amendment["amendment_id"],
            "api_schema_path": amendment["schema_compatibility"]["api_schema_path"],
            "api_schema_sha256": amendment["schema_compatibility"]["api_schema_sha256"],
        },
        "current_run_consumption": {
            "committed_batches": 0,
            "generation_calls": 3,
            "judge_calls": 4,
            "counted_tokens": 90_100,
        },
        "remaining_authority": {
            "committed_batches": 5,
            "generation_calls": 14,
            "judge_calls": 30,
            "counted_tokens": 2_909_900,
            "Judge_retry_headroom": 0,
        },
        "recovery_scope": {
            "retained_generation_outputs": 3,
            "regeneration_allowed": False,
            "valid_judge_records_still_required": 30,
            "result_ceiling": "five Judge-backed smoke triplets; no architecture conclusion",
            "budget_expansion": False,
        },
        "human_authorization": {
            "authority": "William",
            "design_instruction": "那按你的建议调整吧",
            "design_evidence_id": "E7c74a48b",
            "design_authorized": True,
            "semantic_recovery_execution_authorized": False,
            "authorized_amendment_digest": None,
            "authorized_lock_digest": None,
            "authorized_configuration_digest": None,
            "authorized_at_utc": None,
        },
        "blocking_requirements": [
            "William must confirm the exact v0.5 Judge compatibility amendment and lock digests",
            "William must authorize resumption within the unchanged 5-batch, 17-Generator-call, 34-Judge-call, and 3,000,000-token ceilings",
        ],
    }
    packet["authorization_configuration_digest"] = canonical_sha256(
        authorized_configuration(packet)
    )
    packet["pending_packet_digest"] = canonical_sha256(packet)
    return packet


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
