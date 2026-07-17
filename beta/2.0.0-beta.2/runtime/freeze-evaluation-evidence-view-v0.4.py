#!/usr/bin/env python3
"""Validate and freeze the additive v0.4 workspace-evidence amendment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import workspace_evidence_view_v04 as evidence  # noqa: E402


DEFAULT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.json"
)
DEFAULT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.lock.json"
)
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
BLINDED_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.json"
)
BLINDED_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.lock.json"
)
BLINDED_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-blinded-view.1.json"
)

EXPECTED_BASE_SHA256 = (
    "a6e9da7ef2eb85e179d92ec909444c50e879673943b1be71f5c923b9e26d0746"
)
EXPECTED_BLINDED_SHA256 = (
    "e3244c132fba93cd977a81aad5c4f1b77b7bf4ca4c24f7643dcb9ba936aa9e4e"
)
EXPECTED_BLINDED_LOCK = (
    "a5967757d06e65ec0c64c49d43cb946ff6a8c2efe6f833fabffbf07c60c68bbd"
)
EXPECTED_BLINDED_AUTH = (
    "fb47cba14afa8f4ee58f28cbab4154cfd47fcdb86da2e959b5cb4e52bdbdcb23"
)
EXPECTED_SOURCE_PARENT = "440705c78fce387666c645214749bcbc716f3200"
EXPECTED_AMENDMENT_ID = "0.4-evidence-view.1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EvidenceViewProtocolError(ValueError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise EvidenceViewProtocolError(reason)


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise EvidenceViewProtocolError(f"{label} must be repository-relative")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise EvidenceViewProtocolError(f"{label} leaves repository") from exc
    return path


def validate_prior_bindings(binding: Mapping[str, Any]) -> None:
    require(
        sha256_file(BASE_PROTOCOL) == EXPECTED_BASE_SHA256
        and binding.get("protocol_sha256") == EXPECTED_BASE_SHA256,
        "base protocol binding differs",
    )
    require(
        sha256_file(BLINDED_PROTOCOL) == EXPECTED_BLINDED_SHA256
        and binding.get("blinded_view_sha256") == EXPECTED_BLINDED_SHA256,
        "blinded-view protocol binding differs",
    )
    require(
        load_json(BLINDED_LOCK).get("lock_digest") == EXPECTED_BLINDED_LOCK
        and binding.get("blinded_view_lock_digest") == EXPECTED_BLINDED_LOCK,
        "blinded-view lock binding differs",
    )
    require(
        canonical_sha256(load_json(BLINDED_AUTHORIZATION)) == EXPECTED_BLINDED_AUTH
        and binding.get("blinded_view_authorization_digest")
        == EXPECTED_BLINDED_AUTH,
        "blinded-view authorization binding differs",
    )


def _validate_source(source: Mapping[str, Any]) -> None:
    counts = {
        "completed_generation_outputs": 15,
        "generation_attempts": 16,
        "judge_attempts": 36,
        "completed_judge_records": 30,
        "judge_inputs": 15,
        "blinded_candidate_view_receipts": 3,
        "known_counted_tokens": 1046585,
    }
    for field, expected in counts.items():
        require(source.get(field) == expected, f"source {field} differs")
    for field in (
        "run_state_sha256",
        "run_state_digest",
        "smoke_analysis_sha256",
        "smoke_completion_sha256",
        "smoke_completion_digest",
        "cell_set_digest",
        "generation_attempt_set_digest",
        "judge_attempt_set_digest",
        "judge_record_set_digest",
        "judge_input_set_digest",
        "blinded_view_receipt_set_digest",
    ):
        require(
            bool(SHA256_RE.fullmatch(str(source.get(field) or ""))),
            f"source {field} is invalid",
        )
    require(
        source.get("terminal_status") == "vetoed"
        and source.get("terminal_veto_id") == "authority-or-evidence-regression",
        "source terminal state differs",
    )


def _validate_diagnosis(protocol: Mapping[str, Any]) -> None:
    diagnosis = protocol.get("diagnosis")
    require(isinstance(diagnosis, Mapping), "diagnosis is missing")
    require(
        diagnosis.get("case_id") == "b2-dev-near-normal-debugging"
        and diagnosis.get("paired_unit_repeat") == 1,
        "diagnosed paired unit differs",
    )
    cells = diagnosis.get("affected_cells")
    require(isinstance(cells, list) and len(cells) == 3, "affected cell set differs")
    require(
        {item.get("arm_id") for item in cells}
        == {"stable", "direct-only", "thin-kernel"},
        "affected arms differ",
    )
    require(
        {tuple(item.get("prior_authority_regression_votes", [])) for item in cells}
        == {(True, True), (False, False)},
        "prior Judge vote diagnosis differs",
    )
    for item in cells:
        for field in (
            "cell_id",
            "base_blinded_output_id",
            "answer_sha256",
            "generation_attempt_digest",
            "events_sha256",
        ):
            require(
                bool(SHA256_RE.fullmatch(str(item.get(field) or ""))),
                f"affected-cell {field} is invalid",
            )


def _validate_evidence_contract(config: Mapping[str, Any]) -> None:
    require(
        config.get("trigger_pattern") == evidence.WORKSPACE_CLAIM_PATTERN.pattern,
        "workspace trigger pattern differs",
    )
    require(
        config.get("trigger_pattern_sha256")
        == hashlib.sha256(evidence.WORKSPACE_CLAIM_PATTERN.pattern.encode()).hexdigest(),
        "workspace trigger digest differs",
    )
    require(config.get("capsule_scope") == evidence.CAPSULE_SCOPE, "capsule scope differs")
    require(
        config.get("capsule_facts")
        == {
            "project_entry_count": 0,
            "git_repository": False,
            "generator_sandbox_access": "read-only",
        },
        "capsule facts differ",
    )
    for field in (
        "arm_specific_data_allowed",
        "runtime_action_trace_allowed",
        "skill_or_method_trace_allowed",
        "candidate_answer_mutation_allowed",
        "generator_retry_allowed",
        "rubric_change_allowed",
        "judge_output_schema_change_allowed",
    ):
        require(config.get(field) is False, f"{field} weakens the evidence boundary")
    require(
        config.get("retrospective_smoke_rejudge_records") == 6
        and "complete three-arm paired unit"
        in str(config.get("retrospective_smoke_rejudge_scope") or ""),
        "retrospective rejudge scope differs",
    )
    require(config.get("prior_judge_records_retained") is True, "prior records may be replaced")
    require(config.get("post_outcome_amendment") is True, "post-outcome status is hidden")
    samples = (
        "当前工作区是空目录，也不是 Git 仓库。",
        "The working directory is read-only.",
    )
    require(all(evidence.requires_workspace_evidence(item) for item in samples), "trigger misses a frozen sample")
    require(not evidence.requires_workspace_evidence("Give a concise strategy."), "trigger overmatches the neutral sample")


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    require(
        protocol.get("schema_version")
        == "mindthus-beta2-evaluation-evidence-view-amendment-v0.1",
        "unsupported evidence-view amendment schema",
    )
    require(protocol.get("protocol_id") == "mindthus-beta2-three-arm-evaluation", "protocol id differs")
    require(protocol.get("base_protocol_version") == "0.4", "base version differs")
    require(protocol.get("amendment_id") == EXPECTED_AMENDMENT_ID, "amendment id differs")
    binding = protocol.get("base_binding")
    require(isinstance(binding, Mapping), "base binding is missing")
    validate_prior_bindings(binding)
    source = protocol.get("retained_source_run")
    require(isinstance(source, Mapping), "retained source run is missing")
    _validate_source(source)
    _validate_diagnosis(protocol)
    config = protocol.get("workspace_evidence_view")
    require(isinstance(config, Mapping), "workspace evidence config is missing")
    _validate_evidence_contract(config)
    budget = protocol.get("budget_accounting")
    require(isinstance(budget, Mapping), "budget accounting is missing")
    require(
        budget.get("maximum_judge_calls") == 480
        and budget.get("source_judge_calls_used") == 36
        and budget.get("retrospective_rejudge_records") == 6
        and budget.get("remaining_matched_judge_records_after_smoke") == 420
        and budget.get("minimum_calls_after_rejudge_and_matched") == 462
        and budget.get("retry_headroom_at_minimum") == 18,
        "Judge budget accounting differs",
    )
    require(
        budget.get("measured_token_ceiling") == 17599744
        and budget.get("total_unknown_usage_reserved_tokens") == 4352000
        and 17599744 + 4352000 == budget.get("aggregate_authority_ceiling")
        and budget.get("budget_expansion") is False,
        "token budget accounting differs",
    )
    human = protocol.get("human_authorization")
    require(isinstance(human, Mapping) and human.get("authority") == "William", "human authority differs")
    require("把0.4这个补完" in str(human.get("source_instruction") or ""), "completion authority differs")
    require(human.get("release_preparation") is False, "release preparation was authorized")
    dependencies = protocol.get("runtime_dependencies")
    require(isinstance(dependencies, list) and len(dependencies) == len(set(dependencies)), "dependency set differs")
    for index, value in enumerate(dependencies):
        require(repo_path(value, f"runtime_dependencies[{index}]").is_file(), f"runtime dependency is missing: {value}")
    freeze = protocol.get("freeze")
    require(isinstance(freeze, Mapping), "freeze declaration is missing")
    require(freeze.get("source_parent_commit") == EXPECTED_SOURCE_PARENT, "source parent differs")
    require(freeze.get("semantic_model_output_generated_before_amendment_freeze") is True, "prior output is hidden")
    require(freeze.get("semantic_judge_output_generated_under_amendment_before_freeze") is False, "amendment Judge output predates freeze")
    return {
        "status": "valid",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "base_protocol_sha256": EXPECTED_BASE_SHA256,
        "retained_generation_outputs": 15,
        "retained_judge_records": 30,
        "retrospective_rejudge_records": 6,
        "measured_token_ceiling": 17599744,
    }


def dependency_receipts(protocol: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "id": Path(value).name,
            "path": value,
            "sha256": sha256_file(repo_path(value, "runtime dependency")),
        }
        for value in protocol["runtime_dependencies"]
    ]


def build_lock(protocol_path: Path) -> dict[str, Any]:
    protocol = load_json(protocol_path)
    validate_protocol(protocol)
    lock: dict[str, Any] = {
        "schema_version": "mindthus-beta2-evidence-view-lock-v0.1",
        "protocol_id": "mindthus-beta2-three-arm-evaluation",
        "base_protocol_version": "0.4",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "protocol_path": display(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "base_protocol_sha256": EXPECTED_BASE_SHA256,
        "blinded_view_sha256": EXPECTED_BLINDED_SHA256,
        "dependency_receipts": dependency_receipts(protocol),
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_parent_commit": EXPECTED_SOURCE_PARENT,
        "semantic_model_output_generated_before_freeze": True,
        "semantic_judge_output_generated_under_amendment_before_freeze": False,
        "validator_path": display(Path(__file__)),
        "validator_sha256": sha256_file(Path(__file__)),
    }
    lock["lock_digest"] = canonical_sha256(lock)
    return lock


def validate_lock(protocol_path: Path, lock_path: Path) -> dict[str, Any]:
    protocol = load_json(protocol_path)
    report = validate_protocol(protocol)
    lock = load_json(lock_path)
    unsigned = dict(lock)
    digest = unsigned.pop("lock_digest", None)
    require(digest == canonical_sha256(unsigned), "evidence-view lock digest differs")
    require(lock.get("schema_version") == "mindthus-beta2-evidence-view-lock-v0.1", "lock schema differs")
    require(lock.get("protocol_path") == display(protocol_path), "locked protocol path differs")
    require(lock.get("protocol_sha256") == sha256_file(protocol_path), "locked protocol digest differs")
    require(lock.get("dependency_receipts") == dependency_receipts(protocol), "locked dependencies differ")
    require(lock.get("validator_path") == display(Path(__file__)), "locked validator path differs")
    require(lock.get("validator_sha256") == sha256_file(Path(__file__)), "locked validator digest differs")
    require(lock.get("semantic_judge_output_generated_under_amendment_before_freeze") is False, "lock permits pre-freeze Judge output")
    return {
        **report,
        "status": "frozen",
        "protocol_sha256": lock["protocol_sha256"],
        "lock_digest": digest,
        "frozen_at_utc": lock["frozen_at_utc"],
    }


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
            raise EvidenceViewProtocolError(
                f"evidence-view lock already exists: {path}"
            ) from exc
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "freeze", "validate"))
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()
    try:
        if args.command == "check":
            report = validate_protocol(load_json(args.protocol.resolve()))
        elif args.command == "freeze":
            write_exclusive(args.lock.resolve(), build_lock(args.protocol.resolve()))
            report = validate_lock(args.protocol.resolve(), args.lock.resolve())
        else:
            report = validate_lock(args.protocol.resolve(), args.lock.resolve())
        code = 0
    except (
        OSError,
        json.JSONDecodeError,
        EvidenceViewProtocolError,
        evidence.WorkspaceEvidenceError,
    ) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
