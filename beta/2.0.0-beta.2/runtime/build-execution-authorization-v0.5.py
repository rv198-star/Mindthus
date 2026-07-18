#!/usr/bin/env python3
"""Build the pending initial five-batch authorization packet for v0.5."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json"
LOCK_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.lock.json"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.5.py"
DEFAULT_OUT = BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.pending.json"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def payload() -> dict[str, Any]:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    proposed = protocol["authorization_parameters"]["proposed_authorization"]
    initial = protocol["authorization_parameters"][
        "initial_batch_authorization_recommendation"
    ]
    token_budget = dict(proposed["token_or_cost_budget"])
    token_budget["maximum"] = initial["aggregate_token_ceiling"]
    configuration = {
        "host_surface": protocol["authorization_parameters"]["authorized_host_surface"],
        "maximum_committed_batches": initial["maximum_committed_batches"],
        "planned_generation_outputs": initial["maximum_committed_batches"] * 3,
        "planned_judge_records": initial["maximum_committed_batches"] * 6,
        "generator_model_by_host": proposed["generator_model_by_host"],
        "judge_model_and_reasoning": proposed["judge_model_and_reasoning"],
        "maximum_generation_calls": initial["maximum_generation_calls"],
        "maximum_judge_calls": initial["maximum_judge_calls"],
        "token_or_cost_budget": token_budget,
        "human_adjudicator": proposed["human_adjudicator"],
        "stop_authority": proposed["stop_authority"],
    }
    now = datetime.now(timezone.utc).isoformat()
    packet: dict[str, Any] = {
        "schema_version": "mindthus-beta2-execution-authorization-v0.5",
        "authorization_id": "issue-119-codex-v0.5-initial-five-batches",
        "authorization_validator_path": display(VALIDATOR_PATH),
        "authorization_validator_sha256": hashlib.sha256(
            VALIDATOR_PATH.read_bytes()
        ).hexdigest(),
        "status": "pending",
        "packet_created_at_utc": now,
        "protocol": {
            "path": display(PROTOCOL_PATH),
            "sha256": hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest(),
            "lock_path": display(LOCK_PATH),
            "lock_digest": lock["lock_digest"],
        },
        **configuration,
        "prior_consumption": protocol["authorization_parameters"]["cumulative_authority"]
        ["prior_consumption"],
        "requested_cumulative_ceiling": {
            "maximum_generation_calls": 146 + initial["maximum_generation_calls"],
            "maximum_judge_calls": 42 + initial["maximum_judge_calls"],
            "aggregate_token_ceiling": 8_133_510
            + initial["aggregate_token_ceiling"],
        },
        "case_scope": {
            "batch_count": initial["maximum_committed_batches"],
            "generation_outputs": initial["maximum_committed_batches"] * 3,
            "judge_records": initial["maximum_committed_batches"] * 6,
            "evidence_visibility": "implementation-visible",
            "host_session_scope": "startup-only",
            "result_ceiling": "five Judge-backed smoke triplets; no architecture conclusion",
        },
        "human_authorization": {
            "authority": "William",
            "design_change_instruction": "那按你的建议调整吧",
            "design_change_evidence_id": "E47ad3faa",
            "design_change_authorized": True,
            "semantic_execution_authorized": False,
            "authorized_protocol_digest": None,
            "authorized_configuration_digest": None,
            "authorized_at_utc": None,
        },
        "release_preparation": False,
        "blocking_requirements": [
            "William must confirm the exact frozen v0.5 protocol and lock digests",
            "William must authorize the initial 5-batch, 17-generation-call, 34-Judge-call, 3,000,000-token ceiling",
        ],
    }
    packet["pending_packet_digest"] = canonical_sha256(packet)
    return packet


def main() -> int:
    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT.write_text(
        json.dumps(payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(DEFAULT_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
