#!/usr/bin/env python3
"""Bind the user-authorized bounded v0.4 continuation to its frozen digest."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
LOCK_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.lock.json"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4.py"
DEFAULT_OUT = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"


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


def payload() -> dict[str, Any]:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
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
    now = datetime.now(timezone.utc).isoformat()
    authorization: dict[str, Any] = {
        "schema_version": "mindthus-beta2-execution-authorization-v0.2",
        "authorization_id": "issue-119-codex-v0.4-evidence-honest",
        "authorization_validator_path": display(VALIDATOR_PATH),
        "authorization_validator_sha256": hashlib.sha256(
            VALIDATOR_PATH.read_bytes()
        ).hexdigest(),
        "status": "authorized",
        "packet_created_at_utc": now,
        "protocol": {
            "path": display(PROTOCOL_PATH),
            "sha256": hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest(),
            "lock_path": display(LOCK_PATH),
            "lock_digest": lock["lock_digest"],
        },
        **expected,
        "cumulative_authority": parameters["cumulative_authority"],
        "case_scope": {
            "matched_case_ids": protocol["workload"]["matched_case_ids"],
            "excluded_case_ids": protocol["workload"]["excluded_case_ids"],
            "matched_case_count": 25,
            "excluded_sealed_case_count": 4,
            "included_sealed_case_count": 0,
            "evidence_visibility": "implementation-visible",
            "host_session_scope": "startup-only",
            "claim_ceiling": "visible-case Codex startup-session exploratory evidence only",
        },
        "human_authorization": {
            "authority": "William",
            "source_instructions": [
                "去掉4道隐藏题，继续",
                "推进，直到有具体结论或者必须我决策参与的时候才停下来",
            ],
            "source_evidence_ids": ["E22324196", "Eea1fda65"],
            "authorized_at_utc": "2026-07-17T10:50:05.036251+00:00",
            "authorized_protocol_version": "0.4",
            "authorized_configuration_digest": canonical_sha256(expected),
            "source_summary": (
                "The maintainer preserved the 25-visible-case Sol xHigh design and "
                "authorized autonomous evidence-honest continuation until a concrete "
                "result or genuinely human-owned decision, without budget expansion."
            ),
            "must_escalate_on": [
                "binary primary-axis judge disagreement",
                "new spend beyond cumulative ceilings",
                "release or publication decision",
                "irreversible action",
            ],
            "digest_binding": {
                "mode": "bounded-continuation-first-frozen-v0.4",
                "bound_protocol_digest": hashlib.sha256(
                    PROTOCOL_PATH.read_bytes()
                ).hexdigest(),
                "bound_lock_digest": lock["lock_digest"],
                "bound_at_utc": now,
            },
        },
        "sealed_case_attestation_path": None,
        "release_preparation": False,
        "blocking_requirements": [],
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
