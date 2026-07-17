#!/usr/bin/env python3
"""Bind William's v0.4 completion authority to the Judge compatibility lock."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
BASE_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-recovery.1.json"
)
COMPAT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.json"
)
COMPAT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.lock.json"
)
VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-judge-compat.py"
)
DEFAULT_OUT = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-judge-compat.1.json"
)


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
    amendment = load_json(COMPAT_PROTOCOL)
    lock = load_json(COMPAT_LOCK)
    authorization = copy.deepcopy(base)
    now = datetime.now(timezone.utc).isoformat()
    authorization.update(
        {
            "authorization_id": "issue-119-codex-v0.4-judge-compat.1",
            "authorization_validator_path": display(VALIDATOR),
            "authorization_validator_sha256": hashlib.sha256(
                VALIDATOR.read_bytes()
            ).hexdigest(),
            "packet_created_at_utc": now,
            "judge_compatibility_amendment": {
                "path": display(COMPAT_PROTOCOL),
                "sha256": hashlib.sha256(COMPAT_PROTOCOL.read_bytes()).hexdigest(),
                "lock_path": display(COMPAT_LOCK),
                "lock_digest": lock["lock_digest"],
                "amendment_id": amendment["amendment_id"],
                "compatible_schema_path": amendment["schema_compatibility"][
                    "compatible_schema_path"
                ],
            },
        }
    )
    expected = {
        "protocol_sha256": authorization["protocol"]["sha256"],
        "generation_recovery_lock_digest": authorization["recovery_amendment"][
            "lock_digest"
        ],
        "judge_compatibility_lock_digest": lock["lock_digest"],
        "generator_model_by_host": authorization["generator_model_by_host"],
        "judge_model_and_reasoning": authorization["judge_model_and_reasoning"],
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_or_cost_budget": authorization["token_or_cost_budget"],
        "recovery_budget": authorization["recovery_budget"],
        "stop_authority": authorization["stop_authority"],
    }
    human = copy.deepcopy(base["human_authorization"])
    human.update(
        {
            "authorized_protocol_version": (
                "0.4 + generation recovery amendment 1 + Judge compatibility amendment 1"
            ),
            "authorized_configuration_digest": canonical_sha256(expected),
            "source_summary": (
                "William's instruction to complete v0.4 binds an equivalent Judge-schema "
                "compatibility repair after four pre-sampling API rejections. It preserves "
                "all failures and changes no rubric, field, enum, local validation, model, "
                "workload, threshold, budget, or release boundary."
            ),
            "must_escalate_on": [
                "the compatible Judge request is rejected or exhausts its attempts",
                "binary primary-axis judge disagreement",
                "new spend beyond cumulative ceilings",
                "release or publication decision",
                "irreversible action",
            ],
            "digest_binding": {
                "mode": "additive-v0.4-judge-compat-after-frozen-amendment",
                "bound_protocol_digest": authorization["protocol"]["sha256"],
                "bound_generation_recovery_digest": authorization[
                    "recovery_amendment"
                ]["sha256"],
                "bound_generation_recovery_lock_digest": authorization[
                    "recovery_amendment"
                ]["lock_digest"],
                "bound_judge_compatibility_digest": authorization[
                    "judge_compatibility_amendment"
                ]["sha256"],
                "bound_judge_compatibility_lock_digest": lock["lock_digest"],
                "bound_at_utc": now,
            },
        }
    )
    authorization["human_authorization"] = human
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
