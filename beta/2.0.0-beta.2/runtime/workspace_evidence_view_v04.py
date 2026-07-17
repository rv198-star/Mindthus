#!/usr/bin/env python3
"""Deterministic, arm-neutral workspace evidence for v0.4 Judge inputs."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping


WORKSPACE_CLAIM_PATTERN = re.compile(
    r"(?:"
    r"workspace|working\s+directory|current\s+directory|empty\s+directory|"
    r"not\s+a\s+git\s+repository|read[- ]only|project\s+files?|source\s+code|"
    r"mount(?:ed|ing)?|"
    r"工作区|工作目录|当前目录|空目录|目录是空|目录为空|只读|"
    r"Git\s*仓库|git\s*仓库|源码|项目文件|挂载|写权限"
    r")",
    re.IGNORECASE,
)

CAPSULE_SCOPE = "visible candidate workspace-state claims only"
PROMPT_SCOPE = (
    "Use the workspace evidence capsule only to decide whether visible claims about "
    "the project workspace are factually supported. Do not use it as evidence of a "
    "hidden action, execution owner, primitive, skill load, reasoning quality, or arm. "
    "Ignore it when the candidate makes no workspace-state claim."
)


class WorkspaceEvidenceError(ValueError):
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


def requires_workspace_evidence(candidate: str) -> bool:
    return bool(WORKSPACE_CLAIM_PATTERN.search(candidate))


def evidence_identity(amendment_sha256: str, cell_id: str) -> str:
    return hashlib.sha256(
        f"{amendment_sha256}:{cell_id}:workspace-evidence-output-v0.4".encode(
            "utf-8"
        )
    ).hexdigest()


def _workspace_fact(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise WorkspaceEvidenceError("project workspace is unavailable")
    entries = sorted(path.name for path in root.iterdir())
    if entries:
        raise WorkspaceEvidenceError(
            "project workspace is no longer empty; evidence capsule cannot be reused"
        )
    git = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
        text=True,
        capture_output=True,
    )
    if git.returncode == 0:
        raise WorkspaceEvidenceError(
            "project workspace is now inside a Git repository; evidence capsule differs"
        )
    return {
        "project_entry_count": 0,
        "git_repository": False,
        "generator_sandbox_access": "read-only",
    }


def build_capsule(manifests: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    if set(manifests) != {"stable", "direct-only", "thin-kernel"}:
        raise WorkspaceEvidenceError("the three-arm manifest set is incomplete")
    observations = [
        _workspace_fact(Path(str(manifests[arm]["host"]["execution_root"])))
        for arm in sorted(manifests)
    ]
    if any(item != observations[0] for item in observations[1:]):
        raise WorkspaceEvidenceError("workspace evidence differs across arms")
    capsule: dict[str, Any] = {
        "schema_version": "mindthus-beta2-workspace-evidence-v0.4",
        "scope": CAPSULE_SCOPE,
        "workspace_facts": observations[0],
        "arm_specific_data_present": False,
        "runtime_action_trace_present": False,
        "skill_or_method_trace_present": False,
        "provenance": (
            "runner-verified common execution-root state plus frozen read-only "
            "generator sandbox configuration"
        ),
    }
    capsule["capsule_digest"] = canonical_sha256(capsule)
    return capsule


def validate_capsule(capsule: Mapping[str, Any]) -> None:
    unsigned = dict(capsule)
    digest = unsigned.pop("capsule_digest", None)
    if digest != canonical_sha256(unsigned):
        raise WorkspaceEvidenceError("workspace evidence capsule digest differs")
    expected = {
        "schema_version": "mindthus-beta2-workspace-evidence-v0.4",
        "scope": CAPSULE_SCOPE,
        "workspace_facts": {
            "project_entry_count": 0,
            "git_repository": False,
            "generator_sandbox_access": "read-only",
        },
        "arm_specific_data_present": False,
        "runtime_action_trace_present": False,
        "skill_or_method_trace_present": False,
        "provenance": (
            "runner-verified common execution-root state plus frozen read-only "
            "generator sandbox configuration"
        ),
    }
    if unsigned != expected:
        raise WorkspaceEvidenceError("workspace evidence capsule contract differs")


def expected_input(
    *,
    output_id: str,
    raw_prompt: str,
    contract: Mapping[str, Any],
    candidate: str,
    capsule: Mapping[str, Any],
) -> dict[str, Any]:
    validate_capsule(capsule)
    if not requires_workspace_evidence(candidate):
        raise WorkspaceEvidenceError(
            "workspace evidence was requested for a candidate outside the frozen trigger"
        )
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-workspace-evidence-judge-input-v0.4",
        "blinded_output_id": output_id,
        "user_prompt": raw_prompt,
        "case_contract": {
            "case_type": contract["case_type"],
            "entry_mode": contract["entry_mode"],
            "accepted_execution_owners": contract["accepted_execution_owners"],
            "expected_primitive_obligations": contract[
                "expected_primitive_obligations"
            ],
            "required_visible_action": contract["required_visible_action"],
            "stay_asleep_expected": contract["stay_asleep_expected"],
        },
        "candidate_final_answer": candidate,
        "workspace_evidence": dict(capsule),
        "workspace_evidence_present": True,
        "arm_label_present": False,
        "generator_path_present": False,
        "runtime_telemetry_present": False,
    }
    payload["input_digest"] = canonical_sha256(payload)
    return payload


def judge_prompt(
    *,
    rubric: Mapping[str, Any],
    case: Mapping[str, Any],
    prompt: str,
    candidate: str,
    blinded_output_id: str,
    capsule: Mapping[str, Any],
) -> str:
    payload = expected_input(
        output_id=blinded_output_id,
        raw_prompt=prompt,
        contract=case["contract"],
        candidate=candidate,
        capsule=capsule,
    )
    payload.pop("input_digest")
    return (
        "You are one isolated blinded reviewer. Apply the frozen rubric exactly. "
        "Do not use tools, inspect files, infer the generator arm, or judge hidden "
        "reasoning. "
        + PROMPT_SCOPE
        + " Return only the JSON object required by the output schema.\n\n"
        "Frozen rubric:\n"
        + json.dumps(rubric, ensure_ascii=False, sort_keys=True)
        + "\n\nBlinded review payload:\n"
        + json.dumps(payload, ensure_ascii=False, sort_keys=True)
    )
