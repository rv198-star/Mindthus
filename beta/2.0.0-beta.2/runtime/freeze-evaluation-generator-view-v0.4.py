#!/usr/bin/env python3
"""Validate and freeze the additive v0.4 generator-resource-view amendment."""

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

import generator_resource_view_v04 as resource_view  # noqa: E402


DEFAULT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-generator-view.1.json"
)
DEFAULT_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-generator-view.1.lock.json"
)
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
EVIDENCE_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.json"
)
EVIDENCE_LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.lock.json"
)
EVIDENCE_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-evidence-view.1.json"
)

EXPECTED_BASE_SHA256 = "a6e9da7ef2eb85e179d92ec909444c50e879673943b1be71f5c923b9e26d0746"
EXPECTED_EVIDENCE_SHA256 = "500f186106a7458b522e5d6b5c1476c72b76d31100e276e1eed4a1f8664b751c"
EXPECTED_EVIDENCE_LOCK = "da36d4455241de0dd5ea7af47da71be13a39aaf0c2e2eb31b6df4ccfb782b1a0"
EXPECTED_EVIDENCE_AUTH = "9ef91d5ff332f8603e8dae4a5e1e76aa735d66de807c85706ae7d69b0d71d886"
EXPECTED_SOURCE_PARENT = "aba30ed8d0cb55570ee251ba8d2e019a555c88da"
EXPECTED_AMENDMENT_ID = "0.4-generator-view.1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class GeneratorViewProtocolError(ValueError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise GeneratorViewProtocolError(reason)


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise GeneratorViewProtocolError(f"{label} must be repository-relative")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise GeneratorViewProtocolError(f"{label} leaves repository") from exc
    return path


def validate_prior_bindings(binding: Mapping[str, Any]) -> None:
    require(
        sha256_file(BASE_PROTOCOL) == EXPECTED_BASE_SHA256
        and binding.get("protocol_sha256") == EXPECTED_BASE_SHA256,
        "base protocol binding differs",
    )
    require(
        sha256_file(EVIDENCE_PROTOCOL) == EXPECTED_EVIDENCE_SHA256
        and binding.get("evidence_view_sha256") == EXPECTED_EVIDENCE_SHA256,
        "evidence-view protocol binding differs",
    )
    require(
        load_json(EVIDENCE_LOCK).get("lock_digest") == EXPECTED_EVIDENCE_LOCK
        and binding.get("evidence_view_lock_digest") == EXPECTED_EVIDENCE_LOCK,
        "evidence-view lock binding differs",
    )
    require(
        canonical_sha256(load_json(EVIDENCE_AUTHORIZATION)) == EXPECTED_EVIDENCE_AUTH
        and binding.get("evidence_view_authorization_digest")
        == EXPECTED_EVIDENCE_AUTH,
        "evidence-view authorization binding differs",
    )


def _validate_source(source: Mapping[str, Any]) -> None:
    expected = {
        "cells_count": 73,
        "generation_attempts_count": 75,
        "judge_attempts_count": 42,
        "judge_records_count": 36,
        "judge_inputs_count": 18,
        "blinded_views_count": 4,
        "known_generation_calls": 75,
        "known_judge_calls": 42,
        "known_counted_tokens": 4192604,
    }
    for field, value in expected.items():
        require(source.get(field) == value, f"source {field} differs")
    expected_digests = {
        "run_state_sha256": "96b4c5ae534a23d5230ee05015ed426209faf0100525a624cff1d00199362543",
        "run_state_digest": "05439c99c187739549831366e38e65594cb4a7facbb6c6b24462ac73a4a9777e",
        "stop_report_sha256": "e2d50ed897fdd191c95e54c4c01addc4da43c2a5e078c82b708709deb6f08d3e",
        "cells_set_digest": "0db46dbef41d917a378cc3651421c385d91dd5fa7381dafb16a1293a291d3211",
        "generation_attempts_set_digest": "1483c0d8843f4bb33ceb96758c94dece06a03c04e424a217f5a914b4c86a71a9",
        "judge_attempts_set_digest": "9cfc4a6607b1415977a6f986c7dc6b3954a18869438d879ed950024447f97771",
        "judge_records_set_digest": "11b39f797cfc68584c9d771d6c3ed89b0ded57c29c9b5d9aca8033f52b5609e3",
        "judge_inputs_set_digest": "d4145484c70629b78a4ac01cef91b86fb57909117ab9afdd9cb8f2f1664d65f4",
        "blinded_views_set_digest": "25f311718508a76c8ef973e06d07f7540cfa598fce45dd2c9fd66316d2c65573",
    }
    for field, value in expected_digests.items():
        require(source.get(field) == value, f"source {field} differs")
    require(
        source.get("phase") == "matched"
        and source.get("terminal_status") == "stopped"
        and source.get("terminal_veto_id") == "cross-arm-contamination"
        and source.get("stop_report_path")
        == "recovery/0.4-evidence-view.1/stop-report.json",
        "source terminal state differs",
    )


def _validate_diagnosis(diagnosis: Mapping[str, Any]) -> None:
    expected = {
        "cell_id": "21de6914da6970d3fe7522ee39690ed3de187cb95ce70348bbfb04934c8006c4",
        "case_id": "b2-dev-lifecycle-clear",
        "arm_id": "stable",
        "repeat": 1,
        "attempt": 1,
        "attempt_digest": "cc2eb0851b0cdb463f9724209f767f98a66c2a6ddc114cc7675d31673093fc4e",
        "attempt_file_sha256": "b495fd3a8767088d418415e4be092ca4c9befcde36730fa522dcbb17648d9f43",
        "answer_sha256": "810267b97dad24a8d137660c71ab842e2b2cfd9900130991250787a1c66b94fc",
        "events_sha256": "90a87d2f82290da19a60da60ab8fa240efa6ddcb5ad1030da21cce8e33fd36d3",
        "stderr_sha256": "f740ab2863c540fe9c2411b9e526667d3e977b0f9933e7e324418b8984926fea",
        "counted_tokens": 72889,
    }
    for field, value in expected.items():
        require(diagnosis.get(field) == value, f"diagnosis {field} differs")
    require(
        diagnosis.get("returncode") == 0
        and diagnosis.get("timed_out") is False
        and diagnosis.get("answer_present") is True,
        "diagnosed attempt outcome differs",
    )
    require(
        diagnosis.get("false_positive_causes")
        == ["negative-selector-keyword-match"],
        "false-positive diagnosis differs",
    )
    require(
        diagnosis.get("original_detector_trigger_count") == 2
        and diagnosis.get("corrected_detector_trigger_count") == 0,
        "detector trigger diagnosis differs",
    )


def _validate_resource_contract(config: Mapping[str, Any]) -> None:
    expected_true = (
        "active_arm_package_allowed",
        "active_execution_root_allowed",
        "other_arm_roots_forbidden",
        "control_and_result_roots_forbidden",
        "parent_traversal_forbidden",
        "negative_rg_glob_is_not_a_read",
        "find_prune_selector_is_not_a_read",
        "real_cross_arm_veto_retained",
        "existing_attempt_promoted_without_model_call",
    )
    require(all(config.get(field) is True for field in expected_true), "resource-view contract weakens a required boundary")
    for field in (
        "answer_mutation_allowed",
        "attempt_deletion_allowed",
        "target_retry_allowed",
        "workload_change_allowed",
        "threshold_change_allowed",
        "budget_expansion_allowed",
    ):
        require(config.get(field) is False, f"{field} weakens the recovery boundary")

    active = "/run/arms/stable/package"
    active_execution = "/run/arms/stable/project"
    forbidden = ["/run", "/run/arms/direct-only", "/control/judge-rubric"]
    safe_commands = (
        f"sed -n '1,20p' {active}/skills/tplan/SKILL.md",
        f"pwd && find {active_execution} -maxdepth 1 -print",
        "rg --files -g '!*Superpowers*' -g '!**/judge*'",
        "find . -iname '*superpowers*' -prune -o -print",
    )
    require(
        all(
            not resource_view.command_violations(
                command,
                active_package_root=active,
                active_execution_root=active_execution,
                forbidden_path_fragments=forbidden,
            )
            for command in safe_commands
        ),
        "corrected detector rejects a frozen safe sample",
    )
    unsafe_commands = (
        "cat /run/arms/direct-only/package/skills/3l5s/SKILL.md",
        "cat /control/judge-rubric.json",
        "cat ../evaluation-case-matrix.json",
    )
    require(
        all(
            resource_view.command_violations(
                command,
                active_package_root=active,
                active_execution_root=active_execution,
                forbidden_path_fragments=forbidden,
            )
            for command in unsafe_commands
        ),
        "corrected detector misses a frozen unsafe sample",
    )


def validate_protocol(protocol: Mapping[str, Any]) -> dict[str, Any]:
    require(
        protocol.get("schema_version")
        == "mindthus-beta2-evaluation-generator-view-amendment-v0.1",
        "unsupported generator-view amendment schema",
    )
    require(
        protocol.get("protocol_id") == "mindthus-beta2-three-arm-evaluation"
        and protocol.get("base_protocol_version") == "0.4"
        and protocol.get("amendment_id") == EXPECTED_AMENDMENT_ID,
        "generator-view identity differs",
    )
    binding = protocol.get("base_binding")
    require(isinstance(binding, Mapping), "base binding is missing")
    validate_prior_bindings(binding)
    source = protocol.get("retained_source_run")
    require(isinstance(source, Mapping), "retained source run is missing")
    _validate_source(source)
    diagnosis = protocol.get("diagnosis")
    require(isinstance(diagnosis, Mapping), "diagnosis is missing")
    _validate_diagnosis(diagnosis)
    config = protocol.get("generator_resource_view")
    require(isinstance(config, Mapping), "generator resource view is missing")
    _validate_resource_contract(config)
    budget = protocol.get("budget_accounting")
    require(isinstance(budget, Mapping), "budget accounting is missing")
    require(
        budget.get("measured_token_ceiling") == 17599744
        and budget.get("source_known_counted_tokens") == 4192604
        and budget.get("promotion_model_calls") == 0
        and budget.get("budget_expansion") is False,
        "budget accounting differs",
    )
    human = protocol.get("human_authorization")
    require(
        isinstance(human, Mapping)
        and human.get("authority") == "William"
        and "把0.4这个补完" in str(human.get("source_instruction") or "")
        and human.get("release_preparation") is False,
        "human authority differs",
    )
    dependencies = protocol.get("runtime_dependencies")
    require(
        isinstance(dependencies, list)
        and len(dependencies) == len(set(dependencies)),
        "dependency set differs",
    )
    for index, value in enumerate(dependencies):
        require(
            repo_path(value, f"runtime_dependencies[{index}]").is_file(),
            f"runtime dependency is missing: {value}",
        )
    freeze = protocol.get("freeze")
    require(isinstance(freeze, Mapping), "freeze declaration is missing")
    require(freeze.get("source_parent_commit") == EXPECTED_SOURCE_PARENT, "source parent differs")
    require(freeze.get("semantic_model_output_generated_before_amendment_freeze") is True, "prior output is hidden")
    require(freeze.get("semantic_model_output_generated_under_amendment_before_freeze") is False, "amendment model output predates freeze")
    require(freeze.get("future_change_policy") == "separate frozen amendment or new protocol before semantic execution", "future change policy differs")
    return {
        "status": "valid",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "base_protocol_sha256": EXPECTED_BASE_SHA256,
        "retained_cells": 73,
        "retained_generation_attempts": 75,
        "promotion_model_calls": 0,
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
        "schema_version": "mindthus-beta2-generator-view-lock-v0.1",
        "protocol_id": "mindthus-beta2-three-arm-evaluation",
        "base_protocol_version": "0.4",
        "amendment_id": EXPECTED_AMENDMENT_ID,
        "protocol_path": display(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "base_protocol_sha256": EXPECTED_BASE_SHA256,
        "evidence_view_sha256": EXPECTED_EVIDENCE_SHA256,
        "dependency_receipts": dependency_receipts(protocol),
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_parent_commit": EXPECTED_SOURCE_PARENT,
        "semantic_model_output_generated_before_freeze": True,
        "semantic_model_output_generated_under_amendment_before_freeze": False,
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
    require(digest == canonical_sha256(unsigned), "generator-view lock digest differs")
    require(lock.get("schema_version") == "mindthus-beta2-generator-view-lock-v0.1", "lock schema differs")
    require(lock.get("protocol_path") == display(protocol_path), "locked protocol path differs")
    require(lock.get("protocol_sha256") == sha256_file(protocol_path), "locked protocol digest differs")
    require(lock.get("dependency_receipts") == dependency_receipts(protocol), "locked dependencies differ")
    require(lock.get("validator_path") == display(Path(__file__)), "locked validator path differs")
    require(lock.get("validator_sha256") == sha256_file(Path(__file__)), "locked validator digest differs")
    require(lock.get("semantic_model_output_generated_under_amendment_before_freeze") is False, "lock permits pre-freeze model output")
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
            raise GeneratorViewProtocolError(
                f"generator-view lock already exists: {path}"
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
    except (OSError, json.JSONDecodeError, GeneratorViewProtocolError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
