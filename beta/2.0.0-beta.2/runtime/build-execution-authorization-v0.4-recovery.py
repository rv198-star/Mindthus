#!/usr/bin/env python3
"""Bind William's additive v0.4 recovery authority to the recovery lock."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
BASE_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"
RECOVERY_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.json"
RECOVERY_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.lock.json"
VALIDATOR = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-recovery.py"
DEFAULT_OUT = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-recovery.1.json"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def payload() -> dict[str, Any]:
    base = load_json(BASE_AUTHORIZATION)
    amendment = load_json(RECOVERY_PROTOCOL)
    lock = load_json(RECOVERY_LOCK)
    authorization = copy.deepcopy(base)
    now = datetime.now(timezone.utc).isoformat()
    authorization.update(
        {
            "authorization_id": "issue-119-codex-v0.4-recovery.1",
            "authorization_validator_path": display(VALIDATOR),
            "authorization_validator_sha256": hashlib.sha256(VALIDATOR.read_bytes()).hexdigest(),
            "packet_created_at_utc": now,
            "token_or_cost_budget": {
                **base["token_or_cost_budget"],
                "maximum": amendment["budget_accounting"]["amended_measured_token_ceiling"],
            },
            "recovery_amendment": {
                "path": display(RECOVERY_PROTOCOL),
                "sha256": hashlib.sha256(RECOVERY_PROTOCOL.read_bytes()).hexdigest(),
                "lock_path": display(RECOVERY_LOCK),
                "lock_digest": lock["lock_digest"],
                "amendment_id": amendment["amendment_id"],
                "base_protocol_sha256": amendment["base_binding"]["protocol_sha256"],
            },
            "recovery_budget": {
                "base_v0_4_measured_token_ceiling": amendment["budget_accounting"][
                    "base_v0_4_measured_token_ceiling"
                ],
                "unknown_usage_reserved_tokens": amendment["budget_accounting"][
                    "unknown_usage_reserve"
                ]["reserved_tokens"],
                "amended_measured_token_ceiling": amendment["budget_accounting"][
                    "amended_measured_token_ceiling"
                ],
                "budget_expansion": False,
            },
        }
    )
    expected = {
        "protocol_sha256": authorization["protocol"]["sha256"],
        "recovery_lock_digest": lock["lock_digest"],
        "generator_model_by_host": authorization["generator_model_by_host"],
        "judge_model_and_reasoning": authorization["judge_model_and_reasoning"],
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_or_cost_budget": authorization["token_or_cost_budget"],
        "recovery_budget": authorization["recovery_budget"],
        "stop_authority": authorization["stop_authority"],
    }
    authorization["human_authorization"] = {
        "authority": "William",
        "source_instructions": [
            *base["human_authorization"]["source_instructions"],
            amendment["human_authorization"]["source_instruction"],
        ],
        "source_evidence_ids": [
            *base["human_authorization"]["source_evidence_ids"],
            amendment["human_authorization"]["source_evidence_id"],
        ],
        "authorized_at_utc": amendment["human_authorization"]["authorized_at_utc"],
        "authorized_protocol_version": "0.4 + recovery amendment 1",
        "authorized_configuration_digest": canonical_sha256(expected),
        "source_summary": (
            "William authorized an additive completion of the interrupted v0.4 run: "
            "retain all prior artifacts, append one recovery attempt, finish smoke and "
            "its judges, then continue the unchanged matched workload without opening v0.5."
        ),
        "must_escalate_on": [
            "the single recovery attempt fails",
            "binary primary-axis judge disagreement",
            "new spend beyond cumulative ceilings",
            "release or publication decision",
            "irreversible action",
        ],
        "digest_binding": {
            "mode": "additive-v0.4-recovery-after-frozen-amendment",
            "bound_protocol_digest": authorization["protocol"]["sha256"],
            "bound_protocol_lock_digest": authorization["protocol"]["lock_digest"],
            "bound_recovery_digest": authorization["recovery_amendment"]["sha256"],
            "bound_recovery_lock_digest": lock["lock_digest"],
            "bound_at_utc": now,
        },
    }
    return authorization


def main() -> int:
    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT.write_text(
        json.dumps(payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(DEFAULT_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
