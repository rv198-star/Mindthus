#!/usr/bin/env python3
"""Build the digest-bound v0.4 generator-resource-view authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
BASE_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-evidence-view.1.json"
)
BASE_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-evidence-view.py"
)
AMENDMENT = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-generator-view.1.json"
)
LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-generator-view.1.lock.json"
)
FREEZE_VALIDATOR = (
    BETA_ROOT / "runtime" / "freeze-evaluation-generator-view-v0.4.py"
)
AUTHORIZATION_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-generator-view.py"
)
DEFAULT_OUTPUT = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-generator-view.1.json"
)


class GeneratorViewAuthorizationBuildError(ValueError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise GeneratorViewAuthorizationBuildError(reason)


def run_validation(command: list[str], label: str) -> dict[str, Any]:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise GeneratorViewAuthorizationBuildError(
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
        "generator_view_lock_digest": authorization["generator_view_amendment"][
            "lock_digest"
        ],
        "generator_model_by_host": authorization["generator_model_by_host"],
        "judge_model_and_reasoning": authorization["judge_model_and_reasoning"],
        "maximum_generation_calls": authorization["maximum_generation_calls"],
        "maximum_judge_calls": authorization["maximum_judge_calls"],
        "token_or_cost_budget": authorization["token_or_cost_budget"],
        "generator_view_budget": authorization["generator_view_budget"],
        "stop_authority": authorization["stop_authority"],
    }


def build_authorization() -> dict[str, Any]:
    prior = run_validation(
        ["python3", str(BASE_VALIDATOR), "--authorization", str(BASE_AUTHORIZATION)],
        "evidence-view authorization",
    )
    require(prior.get("status") == "authorized", "prior authority is inactive")
    frozen = run_validation(
        [
            "python3",
            str(FREEZE_VALIDATOR),
            "validate",
            "--protocol",
            str(AMENDMENT),
            "--lock",
            str(LOCK),
        ],
        "generator-view amendment",
    )
    require(frozen.get("status") == "frozen", "generator-view amendment is not frozen")
    base = load_json(BASE_AUTHORIZATION)
    amendment = load_json(AMENDMENT)
    lock = load_json(LOCK)
    now = datetime.now(timezone.utc).isoformat()
    authorization = deepcopy(base)
    authorization["authorization_id"] = "issue-119-codex-v0.4-generator-view.1"
    authorization["authorization_validator_path"] = str(
        AUTHORIZATION_VALIDATOR.relative_to(REPO_ROOT)
    )
    authorization["authorization_validator_sha256"] = sha256_file(
        AUTHORIZATION_VALIDATOR
    )
    authorization["packet_created_at_utc"] = now
    authorization["generator_view_amendment"] = {
        "path": str(AMENDMENT.relative_to(REPO_ROOT)),
        "sha256": sha256_file(AMENDMENT),
        "lock_path": str(LOCK.relative_to(REPO_ROOT)),
        "lock_digest": lock["lock_digest"],
        "amendment_id": "0.4-generator-view.1",
        "source_generation_attempt_set_digest": amendment["retained_source_run"][
            "generation_attempts_set_digest"
        ],
        "target_attempt_digest": amendment["diagnosis"]["attempt_digest"],
    }
    authorization["generator_view_budget"] = {
        "prior_measured_token_ceiling": 17599744,
        "amended_measured_token_ceiling": 17599744,
        "source_generation_calls_used": 75,
        "source_judge_calls_used": 42,
        "source_known_counted_tokens": 4192604,
        "promotion_model_calls": 0,
        "budget_expansion": False,
    }
    human = deepcopy(base["human_authorization"])
    human["authorized_protocol_version"] = (
        "0.4 + generation recovery amendment 1 + Judge compatibility amendment 1 "
        "+ blinded-view amendment 1 + evidence-view amendment 1 + generator-view amendment 1"
    )
    human["source_summary"] = (
        "William's instruction to complete v0.4 authorizes a narrow detector correction "
        "after matched execution exposed a deterministic false positive. The successful "
        "attempt is retained and promoted without another model call; the real cross-arm "
        "veto, workload, models, thresholds, and budgets remain unchanged."
    )
    human["must_escalate_on"] = [
        "any actual other-arm or control-resource read",
        "source snapshot, target attempt, classifier, or promotion drift",
        "new spend beyond cumulative ceilings",
        "binary primary-axis Judge disagreement",
        "release or publication decision",
        "irreversible action",
    ]
    human["digest_binding"] = {
        "mode": "additive-v0.4-generator-view-after-false-positive-veto",
        "bound_protocol_digest": authorization["protocol"]["sha256"],
        "bound_evidence_view_digest": authorization["evidence_view_amendment"][
            "sha256"
        ],
        "bound_generator_view_digest": authorization["generator_view_amendment"][
            "sha256"
        ],
        "bound_generator_view_lock_digest": authorization[
            "generator_view_amendment"
        ]["lock_digest"],
        "bound_target_attempt_digest": authorization["generator_view_amendment"][
            "target_attempt_digest"
        ],
        "bound_at_utc": now,
    }
    authorization["human_authorization"] = human
    human["authorized_configuration_digest"] = canonical_sha256(
        expected_configuration(authorization)
    )
    return authorization


def write_exclusive(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise GeneratorViewAuthorizationBuildError(
                f"authorization already exists: {path}"
            ) from exc
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        authorization = build_authorization()
        write_exclusive(args.output.resolve(), authorization)
        report = {
            "status": "authorized",
            "authorization_path": str(args.output.resolve()),
            "authorization_digest": canonical_sha256(authorization),
            "generator_view_protocol_sha256": authorization[
                "generator_view_amendment"
            ]["sha256"],
            "generator_view_lock_digest": authorization[
                "generator_view_amendment"
            ]["lock_digest"],
            "promotion_model_calls": 0,
        }
        code = 0
    except (OSError, json.JSONDecodeError, GeneratorViewAuthorizationBuildError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
