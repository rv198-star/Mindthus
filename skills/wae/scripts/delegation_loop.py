#!/usr/bin/env python3
"""Explicitly activated WAE delegation-depth loop pilot runtime.

The runtime is deliberately small. WAE Loop is disabled unless ``enable`` creates an
activation for a bounded project scope. While active, agents record each responsibility
handoff decision as a checkpoint and may record refinement work and downstream outcomes.

Runtime records observable control facts only. It never decides semantic sufficiency,
never stores private reasoning, and never creates TPlan Mission state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mindthus.wae-loop-trace.v0.3"
DEFAULT_RUNTIME_DIR = Path(".mindthus/wae-loop")
DECISIONS = ("handoff", "refine", "need_input", "stop")
REMAINDER_OWNERS = ("current", "downstream", "upstream", "external", "none", "unknown")
WORK_KINDS = (
    "design_decision",
    "evidence_acquisition",
    "algorithm",
    "reference_implementation",
    "representation",
    "correction",
    "other",
)
UNIT_KINDS = (
    "semantic_decision",
    "evidence_gap",
    "algorithm_boundary",
    "representation_boundary",
    "correction",
    "other",
)
RESULT_STATUSES = ("resolved", "blocked")
ABSORB_MODES = ("update", "confirm")
FINISH_STATUSES = ("completed", "need_input", "stopped", "aborted")
OUTCOME_RESULTS = ("accepted", "returned_upstream", "downstream_completed", "downstream_failed", "unknown")
TRINARY = ("yes", "no", "unknown")
ACCEPTANCE_RESULTS = ("pass", "fail", "partial", "unknown")
COVERAGE = ("complete", "partial", "unknown")
REWORK_OWNERS = ("current", "downstream", "upstream", "external", "none", "unknown")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
UNIT_ID_RE = re.compile(r"^RU-[0-9]{4}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
EVENT_TYPES = ("activation", "checkpoint", "work", "refine_result", "absorb", "outcome", "finish")
COST_FIELDS = ("model_requests", "input_tokens", "output_tokens", "tool_calls", "source_reads", "retry_count", "elapsed_ms")


class RuntimeErrorMessage(Exception):
    """Expected runtime/user error with a concise message."""


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def non_empty(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        raise RuntimeErrorMessage("required text must not be empty")
    return text


def runtime_root(project_root: Path, override: Path | None = None) -> Path:
    root = project_root.resolve()
    if not root.is_dir():
        raise RuntimeErrorMessage(f"project root is not a directory: {root}")
    path = root / DEFAULT_RUNTIME_DIR if override is None else (override if override.is_absolute() else root / override)
    path = path.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise RuntimeErrorMessage("runtime directory must stay inside project root") from exc
    return path


def active_path(root: Path) -> Path:
    return root / "active.json"


def run_dir(root: Path, run_id: str) -> Path:
    if not RUN_ID_RE.fullmatch(run_id):
        raise RuntimeErrorMessage(f"invalid activation id: {run_id}")
    return root / "runs" / run_id


def trace_path(root: Path, run_id: str) -> Path:
    return run_dir(root, run_id) / "trace.jsonl"


def summary_path(root: Path, run_id: str) -> Path:
    return run_dir(root, run_id) / "summary.json"


def bundle_path(root: Path, run_id: str) -> Path:
    return run_dir(root, run_id) / "wae-loop-run.json"


def activation_path(root: Path, run_id: str) -> Path:
    return run_dir(root, run_id) / "activation.json"


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def write_once_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeErrorMessage(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeErrorMessage(f"invalid JSON in {path}: {exc}") from exc


def read_trace(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeErrorMessage(f"invalid trace JSON at line {line_no}: {exc}") from exc
        if not isinstance(value, dict):
            raise RuntimeErrorMessage(f"trace line {line_no} must be a JSON object")
        records.append(value)
    return records


def event_digest(event: dict[str, Any]) -> str:
    value = dict(event)
    value.pop("event_sha256", None)
    return sha256_bytes(canonical(value))


def activation_digest(activation: dict[str, Any]) -> str:
    value = dict(activation)
    value.pop("activation_sha256", None)
    return sha256_bytes(canonical(value))


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_cost_shape(value: Any, label: str) -> list[str]:
    findings: list[str] = []
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    unknown = sorted(set(value) - set(COST_FIELDS))
    if unknown:
        findings.append(f"{label} has unknown fields: {', '.join(unknown)}")
    for field, item in value.items():
        if field in COST_FIELDS and not _nonnegative_int(item):
            findings.append(f"{label}.{field} must be a non-negative integer")
    return findings


def validate_artifact_shape(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    findings: list[str] = []
    if not isinstance(value, dict):
        return [f"{label} must be an object or null"]
    required = {"ref", "sha256", "bytes", "ref_kind"}
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        findings.append(f"{label} missing fields: {', '.join(missing)}")
    if unknown:
        findings.append(f"{label} has unknown fields: {', '.join(unknown)}")
    if not _nonempty_string(value.get("ref")):
        findings.append(f"{label}.ref must be a non-empty string")
    digest = value.get("sha256")
    if digest is not None and (not isinstance(digest, str) or not HEX64_RE.fullmatch(digest.lower())):
        findings.append(f"{label}.sha256 must be null or a SHA256 hex digest")
    size = value.get("bytes")
    if size is not None and not _nonnegative_int(size):
        findings.append(f"{label}.bytes must be null or a non-negative integer")
    if value.get("ref_kind") not in ("project_file", "logical"):
        findings.append(f"{label}.ref_kind is invalid")
    return findings


def validate_activation_shape(activation: Any, run_id: str) -> list[str]:
    findings: list[str] = []
    if not isinstance(activation, dict):
        return ["activation must be a JSON object"]
    required = (
        "schema_version", "activation_id", "activation_sha256", "enabled_at", "enabled_by",
        "scope_kind", "scope_id", "project", "host", "model_mode", "current_owner",
        "downstream_owner", "handoff_purpose", "current_owner_responsibility",
        "downstream_freedom", "reserved_decisions", "logging",
    )
    for field in required:
        if field not in activation:
            findings.append(f"activation missing field {field}")
    unknown = sorted(set(activation) - set(required))
    if unknown:
        findings.append(f"activation has unknown fields: {', '.join(unknown)}")
    if activation.get("schema_version") != SCHEMA_VERSION:
        findings.append("activation schema_version mismatch")
    if activation.get("activation_id") != run_id:
        findings.append("activation id mismatch")
    for field in ("enabled_at", "scope_id", "project", "host", "model_mode", "current_owner", "downstream_owner", "handoff_purpose"):
        if not _nonempty_string(activation.get(field)):
            findings.append(f"activation {field} must be a non-empty string")
    if activation.get("enabled_by") not in ("user", "project", "host", "other"):
        findings.append("activation enabled_by is invalid")
    if activation.get("scope_kind") not in ("task", "phase", "mission", "other"):
        findings.append("activation scope_kind is invalid")
    for field in ("current_owner_responsibility", "downstream_freedom", "reserved_decisions"):
        value = activation.get(field)
        if not isinstance(value, list) or any(not _nonempty_string(item) for item in value):
            findings.append(f"activation {field} must be a list of non-empty strings")
    if isinstance(activation.get("current_owner_responsibility"), list) and not activation["current_owner_responsibility"]:
        findings.append("activation current_owner_responsibility must not be empty")
    logging = activation.get("logging")
    if not isinstance(logging, dict):
        findings.append("activation logging must be an object")
    else:
        if not _nonempty_string(logging.get("runtime_root")):
            findings.append("activation logging.runtime_root must be a non-empty string")
        for field in ("raw_artifact_contents_recorded", "private_reasoning_recorded"):
            if not isinstance(logging.get(field), bool):
                findings.append(f"activation logging.{field} must be boolean")
    digest = activation.get("activation_sha256")
    if not isinstance(digest, str) or not HEX64_RE.fullmatch(digest):
        findings.append("activation_sha256 must be a lowercase SHA256 hex digest")
    elif digest != activation_digest(activation):
        findings.append("activation agreement digest mismatch")
    return findings


def validate_event_shape(event: Any, label: str = "event") -> list[str]:
    findings: list[str] = []
    if not isinstance(event, dict):
        return [f"{label} must be a JSON object"]
    required_base = (
        "schema_version", "activation_id", "activation_sha256", "sequence", "logged_at",
        "prev_event_sha256", "event_sha256", "event_type",
    )
    for field in required_base:
        if field not in event:
            findings.append(f"{label} missing field {field}")
    if event.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"{label} schema_version mismatch")
    if not _nonempty_string(event.get("activation_id")):
        findings.append(f"{label}.activation_id must be a non-empty string")
    if not isinstance(event.get("activation_sha256"), str) or not HEX64_RE.fullmatch(str(event.get("activation_sha256", ""))):
        findings.append(f"{label}.activation_sha256 must be a SHA256 hex digest")
    if not isinstance(event.get("sequence"), int) or isinstance(event.get("sequence"), bool) or event.get("sequence", 0) < 1:
        findings.append(f"{label}.sequence must be a positive integer")
    if not _nonempty_string(event.get("logged_at")):
        findings.append(f"{label}.logged_at must be a non-empty string")
    previous = event.get("prev_event_sha256")
    if previous is not None and (not isinstance(previous, str) or not HEX64_RE.fullmatch(previous)):
        findings.append(f"{label}.prev_event_sha256 must be null or a SHA256 hex digest")
    if not isinstance(event.get("event_sha256"), str) or not HEX64_RE.fullmatch(str(event.get("event_sha256", ""))):
        findings.append(f"{label}.event_sha256 must be a SHA256 hex digest")
    event_type = event.get("event_type")
    if event_type not in EVENT_TYPES:
        findings.append(f"{label}.event_type is invalid")
        return findings
    specific_fields = {
        "activation": {"scope_id"},
        "checkpoint": {"decision", "artifact", "blocking_remainder", "owner_of_remainder", "consequence_if_handoff_now", "next_minimum_work", "evidence_refs", "cost", "refinement_unit"},
        "work": {"unit_id", "work_kind", "changed_scope", "artifact_before", "artifact_after", "resolved_remainders", "introduced_remainders", "evidence_refs", "cost"},
        "refine_result": {"unit_id", "result_status", "result_summary", "result_artifact", "resolved_remainders", "introduced_remainders", "evidence_refs", "cost"},
        "absorb": {"unit_id", "result_sequence", "absorb_mode", "parent_before", "parent_after", "absorbed_scope", "cost"},
        "outcome": {"handoff_result", "downstream_invented_upstream_semantics", "downstream_requested_missing_upstream_decision", "downstream_overrode_handoff", "rework_required", "rework_owner", "acceptance_result", "notes", "telemetry_coverage", "cost"},
        "finish": {"status", "notes", "cost"},
    }
    allowed_fields = set(required_base) | specific_fields[event_type]
    unknown = sorted(set(event) - allowed_fields)
    if unknown:
        findings.append(f"{label} has unknown fields: {', '.join(unknown)}")

    if event_type == "activation":
        if not _nonempty_string(event.get("scope_id")):
            findings.append(f"{label}.scope_id must be a non-empty string")
    elif event_type == "checkpoint":
        required = (
            "decision", "artifact", "blocking_remainder", "owner_of_remainder",
            "consequence_if_handoff_now", "next_minimum_work", "evidence_refs", "cost",
            "refinement_unit",
        )
        for field in required:
            if field not in event:
                findings.append(f"{label} missing field {field}")
        decision = event.get("decision")
        owner = event.get("owner_of_remainder")
        remainders = event.get("blocking_remainder")
        if decision not in DECISIONS:
            findings.append(f"{label}.decision is invalid")
        if owner not in REMAINDER_OWNERS:
            findings.append(f"{label}.owner_of_remainder is invalid")
        if not isinstance(remainders, list) or any(not isinstance(item, str) for item in remainders):
            findings.append(f"{label}.blocking_remainder must be a string array")
            remainders = []
        if not isinstance(event.get("consequence_if_handoff_now"), str):
            findings.append(f"{label}.consequence_if_handoff_now must be a string")
        if not isinstance(event.get("next_minimum_work"), str):
            findings.append(f"{label}.next_minimum_work must be a string")
        if not isinstance(event.get("evidence_refs"), list) or any(not isinstance(item, str) for item in event.get("evidence_refs", [])):
            findings.append(f"{label}.evidence_refs must be a string array")
        findings.extend(validate_artifact_shape(event.get("artifact"), f"{label}.artifact"))
        findings.extend(validate_cost_shape(event.get("cost"), f"{label}.cost"))
        unit = event.get("refinement_unit")
        if decision == "refine":
            if owner != "current" or len(remainders) != 1 or not str(event.get("consequence_if_handoff_now", "")).strip() or not str(event.get("next_minimum_work", "")).strip():
                findings.append(f"{label} refine semantics are incomplete or not single-unit")
            if event.get("artifact") is None:
                findings.append(f"{label} refine requires a bound parent artifact")
            if not isinstance(unit, dict):
                findings.append(f"{label}.refinement_unit must be an object for refine")
            else:
                required_unit = {"unit_id", "unit_kind", "question", "scope_boundary", "completion_criterion", "parent_artifact"}
                missing = sorted(required_unit - set(unit))
                unknown = sorted(set(unit) - required_unit)
                if missing:
                    findings.append(f"{label}.refinement_unit missing fields: {', '.join(missing)}")
                if unknown:
                    findings.append(f"{label}.refinement_unit has unknown fields: {', '.join(unknown)}")
                if not isinstance(unit.get("unit_id"), str) or not UNIT_ID_RE.fullmatch(unit.get("unit_id", "")):
                    findings.append(f"{label}.refinement_unit.unit_id is invalid")
                if unit.get("unit_kind") not in UNIT_KINDS:
                    findings.append(f"{label}.refinement_unit.unit_kind is invalid")
                for field in ("question", "scope_boundary", "completion_criterion"):
                    if not _nonempty_string(unit.get(field)):
                        findings.append(f"{label}.refinement_unit.{field} must be a non-empty string")
                findings.extend(validate_artifact_shape(unit.get("parent_artifact"), f"{label}.refinement_unit.parent_artifact"))
                if remainders and unit.get("question") != remainders[0]:
                    findings.append(f"{label}.refinement_unit.question must equal the single blocking remainder")
                if unit.get("parent_artifact") != event.get("artifact"):
                    findings.append(f"{label}.refinement_unit.parent_artifact must equal checkpoint artifact")
        else:
            if unit is not None:
                findings.append(f"{label}.refinement_unit must be null unless decision is refine")
        if decision == "need_input" and (owner not in ("upstream", "external") or not remainders or not str(event.get("consequence_if_handoff_now", "")).strip()):
            findings.append(f"{label} need_input semantics are incomplete")
        if decision == "handoff" and owner not in ("downstream", "none"):
            findings.append(f"{label} handoff remainder owner is invalid")
    elif event_type == "work":
        required = ("unit_id", "work_kind", "changed_scope", "artifact_before", "artifact_after", "resolved_remainders", "introduced_remainders", "evidence_refs", "cost")
        for field in required:
            if field not in event:
                findings.append(f"{label} missing field {field}")
        if not isinstance(event.get("unit_id"), str) or not UNIT_ID_RE.fullmatch(event.get("unit_id", "")):
            findings.append(f"{label}.unit_id is invalid")
        if event.get("work_kind") not in WORK_KINDS:
            findings.append(f"{label}.work_kind is invalid")
        if not _nonempty_string(event.get("changed_scope")):
            findings.append(f"{label}.changed_scope must be a non-empty string")
        for field in ("resolved_remainders", "introduced_remainders", "evidence_refs"):
            value = event.get(field)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                findings.append(f"{label}.{field} must be a string array")
        findings.extend(validate_artifact_shape(event.get("artifact_before"), f"{label}.artifact_before"))
        findings.extend(validate_artifact_shape(event.get("artifact_after"), f"{label}.artifact_after"))
        findings.extend(validate_cost_shape(event.get("cost"), f"{label}.cost"))
    elif event_type == "refine_result":
        required = ("unit_id", "result_status", "result_summary", "result_artifact", "resolved_remainders", "introduced_remainders", "evidence_refs", "cost")
        for field in required:
            if field not in event:
                findings.append(f"{label} missing field {field}")
        if not isinstance(event.get("unit_id"), str) or not UNIT_ID_RE.fullmatch(event.get("unit_id", "")):
            findings.append(f"{label}.unit_id is invalid")
        if event.get("result_status") not in RESULT_STATUSES:
            findings.append(f"{label}.result_status is invalid")
        if not _nonempty_string(event.get("result_summary")):
            findings.append(f"{label}.result_summary must be a non-empty string")
        elif len(event.get("result_summary", "")) > 4096:
            findings.append(f"{label}.result_summary exceeds 4096 characters")
        findings.extend(validate_artifact_shape(event.get("result_artifact"), f"{label}.result_artifact"))
        for field in ("resolved_remainders", "introduced_remainders", "evidence_refs"):
            value = event.get(field)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                findings.append(f"{label}.{field} must be a string array")
        findings.extend(validate_cost_shape(event.get("cost"), f"{label}.cost"))
    elif event_type == "absorb":
        required = ("unit_id", "result_sequence", "absorb_mode", "parent_before", "parent_after", "absorbed_scope", "cost")
        for field in required:
            if field not in event:
                findings.append(f"{label} missing field {field}")
        if not isinstance(event.get("unit_id"), str) or not UNIT_ID_RE.fullmatch(event.get("unit_id", "")):
            findings.append(f"{label}.unit_id is invalid")
        if not isinstance(event.get("result_sequence"), int) or isinstance(event.get("result_sequence"), bool) or event.get("result_sequence", 0) < 1:
            findings.append(f"{label}.result_sequence must be a positive integer")
        if event.get("absorb_mode") not in ABSORB_MODES:
            findings.append(f"{label}.absorb_mode is invalid")
        findings.extend(validate_artifact_shape(event.get("parent_before"), f"{label}.parent_before"))
        findings.extend(validate_artifact_shape(event.get("parent_after"), f"{label}.parent_after"))
        if not _nonempty_string(event.get("absorbed_scope")):
            findings.append(f"{label}.absorbed_scope must be a non-empty string")
        findings.extend(validate_cost_shape(event.get("cost"), f"{label}.cost"))
    elif event_type == "outcome":
        required = ("handoff_result", "downstream_invented_upstream_semantics", "downstream_requested_missing_upstream_decision", "downstream_overrode_handoff", "rework_required", "rework_owner", "acceptance_result", "notes", "telemetry_coverage", "cost")
        for field in required:
            if field not in event:
                findings.append(f"{label} missing field {field}")
        if event.get("handoff_result") not in OUTCOME_RESULTS:
            findings.append(f"{label}.handoff_result is invalid")
        for field in ("downstream_invented_upstream_semantics", "downstream_requested_missing_upstream_decision", "downstream_overrode_handoff", "rework_required"):
            if event.get(field) not in TRINARY:
                findings.append(f"{label}.{field} is invalid")
        if event.get("rework_owner") not in REWORK_OWNERS:
            findings.append(f"{label}.rework_owner is invalid")
        if event.get("acceptance_result") not in ACCEPTANCE_RESULTS:
            findings.append(f"{label}.acceptance_result is invalid")
        if not isinstance(event.get("notes"), str):
            findings.append(f"{label}.notes must be a string")
        coverage = event.get("telemetry_coverage")
        if not isinstance(coverage, dict):
            findings.append(f"{label}.telemetry_coverage must be an object")
        else:
            required_coverage = {"model_calls", "tool_calls", "artifact_changes", "downstream_outcome"}
            if set(coverage) != required_coverage:
                findings.append(f"{label}.telemetry_coverage fields are invalid")
            for field in required_coverage:
                if coverage.get(field) not in COVERAGE:
                    findings.append(f"{label}.telemetry_coverage.{field} is invalid")
        findings.extend(validate_cost_shape(event.get("cost"), f"{label}.cost"))
    else:
        for field in ("status", "notes", "cost"):
            if field not in event:
                findings.append(f"{label} missing field {field}")
        if event.get("status") not in FINISH_STATUSES:
            findings.append(f"{label}.status is invalid")
        if not isinstance(event.get("notes"), str):
            findings.append(f"{label}.notes must be a string")
        findings.extend(validate_cost_shape(event.get("cost"), f"{label}.cost"))
    return findings


def validate_trace_integrity(
    activation: dict[str, Any],
    events: list[dict[str, Any]],
    *,
    allow_empty: bool = False,
    expected_run_id: str | None = None,
) -> list[str]:
    findings = validate_activation_shape(activation, expected_run_id or str(activation.get("activation_id", "")))
    run_id = activation.get("activation_id")
    activation_sha = activation.get("activation_sha256")
    if not events:
        if not allow_empty:
            findings.append("trace has no activation event")
        return findings
    previous: str | None = None
    latest_checkpoint: dict[str, Any] | None = None
    seen_handoff = False
    finish_seen = False
    activation_events = 0
    current_unit: dict[str, Any] | None = None
    current_parent: dict[str, Any] | None = None
    unit_count = 0
    for index, event in enumerate(events, start=1):
        label = f"event {index}"
        findings.extend(validate_event_shape(event, label))
        if event.get("activation_id") != run_id:
            findings.append(f"{label}: activation id mismatch")
        if event.get("activation_sha256") != activation_sha:
            findings.append(f"{label}: activation agreement binding mismatch")
        if event.get("sequence") != index:
            findings.append(f"{label}: sequence must equal {index}")
        if event.get("prev_event_sha256") != previous:
            findings.append(f"{label}: previous-event hash mismatch")
        digest = event_digest(event)
        if event.get("event_sha256") != digest:
            findings.append(f"{label}: event hash mismatch")
        event_type = event.get("event_type")
        if event_type == "activation":
            activation_events += 1
            if index != 1:
                findings.append(f"{label}: activation event must be first")
            if event.get("scope_id") != activation.get("scope_id"):
                findings.append(f"{label}: scope id does not match activation agreement")
        elif event_type == "checkpoint":
            if finish_seen:
                findings.append(f"{label}: checkpoint cannot occur after finish")
            decision = event.get("decision")
            if current_unit is not None:
                state = current_unit.get("state")
                if state in ("open", "resolved"):
                    findings.append(f"{label}: checkpoint cannot bypass active refinement unit {current_unit.get('unit_id')}")
                elif state == "blocked" and decision not in ("need_input", "stop"):
                    findings.append(f"{label}: blocked refinement unit only permits need_input or stop")
                if state == "blocked" and decision in ("need_input", "stop"):
                    current_unit = None
            if decision == "refine":
                unit = event.get("refinement_unit") or {}
                unit_count += 1
                expected_unit_id = f"RU-{unit_count:04d}"
                if unit.get("unit_id") != expected_unit_id:
                    findings.append(f"{label}: refinement unit id must be {expected_unit_id}")
                if current_parent is not None and event.get("artifact") != current_parent:
                    findings.append(f"{label}: refine parent must equal the latest absorbed parent")
                current_unit = {
                    **unit,
                    "state": "open",
                    "result_sequence": None,
                }
            elif decision == "handoff":
                if current_unit is not None:
                    findings.append(f"{label}: handoff cannot occur with an unfinished refinement unit")
                if current_parent is not None and event.get("artifact") != current_parent:
                    findings.append(f"{label}: handoff artifact must equal the latest absorbed parent")
                seen_handoff = True
            latest_checkpoint = event
        elif event_type == "work":
            if finish_seen:
                findings.append(f"{label}: work cannot occur after finish")
            if current_unit is None or current_unit.get("state") != "open":
                findings.append(f"{label}: work requires one open refinement unit")
            elif event.get("unit_id") != current_unit.get("unit_id"):
                findings.append(f"{label}: work unit id does not match the open refinement unit")
        elif event_type == "refine_result":
            if finish_seen:
                findings.append(f"{label}: refine_result cannot occur after finish")
            if current_unit is None or current_unit.get("state") != "open":
                findings.append(f"{label}: refine_result requires one open refinement unit")
            elif event.get("unit_id") != current_unit.get("unit_id"):
                findings.append(f"{label}: refine_result unit id does not match the open refinement unit")
            else:
                if event.get("result_status") == "resolved":
                    question = current_unit.get("question")
                    if question not in event.get("resolved_remainders", []):
                        findings.append(f"{label}: resolved result must explicitly resolve the refinement-unit question")
                    current_unit["state"] = "resolved"
                elif event.get("result_status") == "blocked":
                    current_unit["state"] = "blocked"
                current_unit["result_sequence"] = index
        elif event_type == "absorb":
            if finish_seen:
                findings.append(f"{label}: absorb cannot occur after finish")
            if current_unit is None or current_unit.get("state") != "resolved":
                findings.append(f"{label}: absorb requires one resolved refinement unit")
            elif event.get("unit_id") != current_unit.get("unit_id"):
                findings.append(f"{label}: absorb unit id does not match the resolved refinement unit")
            else:
                if event.get("result_sequence") != current_unit.get("result_sequence"):
                    findings.append(f"{label}: absorb result_sequence does not match the unit result")
                if event.get("parent_before") != current_unit.get("parent_artifact"):
                    findings.append(f"{label}: absorb parent_before must equal the unit parent artifact")
                before = event.get("parent_before")
                after = event.get("parent_after")
                if event.get("absorb_mode") == "update" and after == before:
                    findings.append(f"{label}: update absorb requires a new parent identity")
                if event.get("absorb_mode") == "confirm" and after != before:
                    findings.append(f"{label}: confirm absorb must retain the parent identity")
                current_parent = after
                current_unit = None
        elif event_type == "outcome":
            if not seen_handoff:
                findings.append(f"{label}: outcome requires an earlier handoff checkpoint")
        elif event_type == "finish":
            if finish_seen:
                findings.append(f"{label}: trace contains more than one finish event")
            finish_seen = True
            expected = {"completed": "handoff", "need_input": "need_input", "stopped": "stop"}
            status = event.get("status")
            if status != "aborted" and (latest_checkpoint is None or latest_checkpoint.get("decision") != expected.get(status)):
                findings.append(f"{label}: finish status does not match latest checkpoint")
            if status == "completed" and current_unit is not None:
                findings.append(f"{label}: completed finish cannot leave an unfinished refinement unit")
        previous = event.get("event_sha256")
    if activation_events != 1:
        findings.append("trace must contain exactly one activation event")
    return findings


def derive_refinement_state(events: list[dict[str, Any]]) -> dict[str, Any]:
    current_unit: dict[str, Any] | None = None
    current_parent: dict[str, Any] | None = None
    unit_count = 0
    for event in events:
        event_type = event.get("event_type")
        if event_type == "checkpoint":
            if event.get("decision") == "refine":
                unit_count += 1
                current_unit = {**(event.get("refinement_unit") or {}), "state": "open", "result_sequence": None}
            elif current_unit is not None and current_unit.get("state") == "blocked" and event.get("decision") in ("need_input", "stop"):
                current_unit = None
        elif event_type == "refine_result" and current_unit is not None and event.get("unit_id") == current_unit.get("unit_id"):
            current_unit["state"] = event.get("result_status")
            current_unit["result_sequence"] = event.get("sequence")
        elif event_type == "absorb" and current_unit is not None and event.get("unit_id") == current_unit.get("unit_id"):
            current_parent = event.get("parent_after")
            current_unit = None
    return {"current_unit": current_unit, "current_parent": current_parent, "unit_count": unit_count}


def derive_summary(activation: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    refinement = derive_refinement_state(events)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "activation_id": activation["activation_id"],
        "activation_sha256": activation["activation_sha256"],
        "status": "active",
        "event_count": len(events),
        "checkpoint_count": 0,
        "refine_count": 0,
        "work_event_count": 0,
        "refine_result_count": 0,
        "absorb_count": 0,
        "outcome_count": 0,
        "refinement_unit_count": refinement["unit_count"],
        "active_refinement_unit_id": refinement["current_unit"].get("unit_id") if refinement["current_unit"] else None,
        "active_refinement_unit_state": refinement["current_unit"].get("state") if refinement["current_unit"] else None,
        "current_parent_artifact": refinement["current_parent"],
        "last_checkpoint_decision": None,
        "last_checkpoint_sequence": None,
        "last_event_at": events[-1]["logged_at"] if events else None,
        "last_event_sha256": events[-1]["event_sha256"] if events else None,
        "finished_at": None,
    }
    for event in events:
        if event.get("event_type") == "checkpoint":
            summary["checkpoint_count"] += 1
            summary["last_checkpoint_decision"] = event.get("decision")
            summary["last_checkpoint_sequence"] = event.get("sequence")
            if event.get("decision") == "refine":
                summary["refine_count"] += 1
        elif event.get("event_type") == "work":
            summary["work_event_count"] += 1
        elif event.get("event_type") == "refine_result":
            summary["refine_result_count"] += 1
        elif event.get("event_type") == "absorb":
            summary["absorb_count"] += 1
        elif event.get("event_type") == "outcome":
            summary["outcome_count"] += 1
        elif event.get("event_type") == "finish":
            summary["status"] = event.get("status")
            summary["finished_at"] = event.get("logged_at")
    return summary


def expected_bundle(activation: dict[str, Any], events: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "activation": activation, "events": events, "summary": summary}


def write_derived_state(root: Path, run_id: str, activation: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    summary = derive_summary(activation, events)
    atomic_json(summary_path(root, run_id), summary)
    atomic_json(bundle_path(root, run_id), expected_bundle(activation, events, summary))
    return summary


def load_authoritative_run(root: Path, run_id: str, *, allow_empty: bool = False, repair_derived: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    activation = read_json(activation_path(root, run_id))
    events = read_trace(trace_path(root, run_id))
    findings = validate_trace_integrity(activation, events, allow_empty=allow_empty, expected_run_id=run_id)
    if findings:
        raise RuntimeErrorMessage("run integrity invalid: " + "; ".join(findings[:8]))
    summary = derive_summary(activation, events)
    if repair_derived:
        write_derived_state(root, run_id, activation, events)
    return activation, events, summary


def append_event(root: Path, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    allow_empty = payload.get("event_type") == "activation"
    activation, events, _ = load_authoritative_run(root, run_id, allow_empty=allow_empty, repair_derived=True)
    if not events and payload.get("event_type") != "activation":
        raise RuntimeErrorMessage("first trace event must be activation")
    if events and payload.get("event_type") == "activation":
        raise RuntimeErrorMessage("activation event already exists")
    event = {
        "schema_version": SCHEMA_VERSION,
        "activation_id": run_id,
        "activation_sha256": activation["activation_sha256"],
        "sequence": len(events) + 1,
        "logged_at": now_utc(),
        "prev_event_sha256": events[-1]["event_sha256"] if events else None,
        **payload,
    }
    event["event_sha256"] = event_digest(event)
    shape_findings = validate_event_shape(event)
    if shape_findings:
        raise RuntimeErrorMessage("event shape invalid: " + "; ".join(shape_findings[:8]))
    candidate = events + [event]
    findings = validate_trace_integrity(activation, candidate, expected_run_id=run_id)
    if findings:
        raise RuntimeErrorMessage("event would invalidate run: " + "; ".join(findings[:8]))
    path = trace_path(root, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    write_derived_state(root, run_id, activation, candidate)
    return event


def refresh_bundle(root: Path, run_id: str) -> None:
    load_authoritative_run(root, run_id, repair_derived=True)


def make_run_id(scope_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", scope_id.strip()).strip("-._") or "scope"
    slug = slug[:48]
    return f"{timestamp}-{slug}-{uuid.uuid4().hex[:8]}"


def load_active(root: Path, *, required: bool = True) -> dict[str, Any] | None:
    path = active_path(root)
    if not path.exists():
        if required:
            raise RuntimeErrorMessage("WAE Loop is not active for this project root")
        return None
    value = read_json(path)
    if value.get("schema_version") != SCHEMA_VERSION or value.get("status") != "active":
        raise RuntimeErrorMessage("active pointer is invalid")
    run_id = value.get("activation_id")
    if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
        raise RuntimeErrorMessage("active pointer activation id is invalid")
    activation = read_json(activation_path(root, run_id))
    findings = validate_activation_shape(activation, run_id)
    if findings:
        raise RuntimeErrorMessage("active activation agreement is invalid: " + "; ".join(findings[:8]))
    if value.get("activation_sha256") != activation.get("activation_sha256"):
        raise RuntimeErrorMessage("active pointer activation binding mismatch")
    return value


def resolve_run_id(root: Path, requested: str | None, *, require_active: bool = False) -> str:
    if requested:
        if require_active:
            active = load_active(root)
            if active["activation_id"] != requested:
                raise RuntimeErrorMessage("requested activation is not the active scope")
        return requested
    active = load_active(root, required=require_active)
    if active:
        return active["activation_id"]
    runs = sorted((root / "runs").glob("*")) if (root / "runs").exists() else []
    if not runs:
        raise RuntimeErrorMessage("no WAE Loop run found")
    return runs[-1].name


def string_list(values: list[str] | None) -> list[str]:
    return [item.strip() for item in (values or []) if item.strip()]


def artifact_record(project_root: Path, path_value: str | None, logical_ref: str | None, supplied_hash: str | None) -> dict[str, Any] | None:
    if path_value and logical_ref:
        raise RuntimeErrorMessage("use either --artifact or --artifact-ref, not both")
    if not path_value and not logical_ref:
        return None
    if path_value:
        root = project_root.resolve()
        path = Path(path_value)
        path = (root / path).resolve() if not path.is_absolute() else path.resolve()
        try:
            rel = path.relative_to(root)
        except ValueError as exc:
            raise RuntimeErrorMessage("artifact path must stay inside project root") from exc
        if not path.is_file():
            raise RuntimeErrorMessage(f"artifact file not found: {rel.as_posix()}")
        return {
            "ref": rel.as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "ref_kind": "project_file",
        }
    ref = non_empty(logical_ref)
    result = {"ref": ref, "sha256": (supplied_hash or "").strip() or None, "bytes": None, "ref_kind": "logical"}
    if result["sha256"] is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", result["sha256"]):
        raise RuntimeErrorMessage("--artifact-sha256 must be a 64-character SHA256 hex digest")
    return result


def ensure_parent_unchanged(project_root: Path, unit: dict[str, Any] | None) -> None:
    if not unit:
        return
    parent = unit.get("parent_artifact")
    if not isinstance(parent, dict) or parent.get("ref_kind") != "project_file":
        return
    current = artifact_record(project_root, parent.get("ref"), None, None)
    if current != parent:
        raise RuntimeErrorMessage(
            "refinement parent changed before Refine Result; restore the bound parent or start a new activation"
        )


def cost_record(args: argparse.Namespace) -> dict[str, Any]:
    fields = ("model_requests", "input_tokens", "output_tokens", "tool_calls", "source_reads", "retry_count", "elapsed_ms")
    result: dict[str, Any] = {}
    for field in fields:
        value = getattr(args, field, None)
        if value is not None:
            if value < 0:
                raise RuntimeErrorMessage(f"{field} must be >= 0")
            result[field] = value
    return result


def enable(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    if load_active(root, required=False):
        raise RuntimeErrorMessage("WAE Loop is already active; finish the current scope before enabling another")
    scope_id = non_empty(args.scope_id)
    run_id = args.activation_id or make_run_id(scope_id)
    if not RUN_ID_RE.fullmatch(run_id):
        raise RuntimeErrorMessage("--activation-id contains unsupported characters")
    target_dir = run_dir(root, run_id)
    if target_dir.exists():
        raise RuntimeErrorMessage(f"activation id already exists: {run_id}")
    activation = {
        "schema_version": SCHEMA_VERSION,
        "activation_id": run_id,
        "enabled_at": now_utc(),
        "enabled_by": args.enabled_by,
        "scope_kind": args.scope_kind,
        "scope_id": scope_id,
        "project": (args.project or project_root.name).strip(),
        "host": (args.host or "unknown").strip(),
        "model_mode": (args.model_mode or "unknown").strip(),
        "current_owner": non_empty(args.current_owner),
        "downstream_owner": non_empty(args.downstream_owner),
        "handoff_purpose": non_empty(args.handoff_purpose),
        "current_owner_responsibility": string_list(args.current_responsibility),
        "downstream_freedom": string_list(args.downstream_freedom),
        "reserved_decisions": string_list(args.reserved_decision),
        "logging": {
            "runtime_root": DEFAULT_RUNTIME_DIR.as_posix() if args.runtime_dir is None else str(args.runtime_dir),
            "raw_artifact_contents_recorded": False,
            "private_reasoning_recorded": False,
        },
    }
    if not activation["current_owner_responsibility"]:
        raise RuntimeErrorMessage("at least one current owner responsibility item is required")
    activation["activation_sha256"] = activation_digest(activation)
    target_dir.mkdir(parents=True, exist_ok=False)
    write_once_json(activation_path(root, run_id), activation)
    event = append_event(root, run_id, {"event_type": "activation", "scope_id": scope_id})
    pointer = {
        "schema_version": SCHEMA_VERSION,
        "activation_id": run_id,
        "activation_sha256": activation["activation_sha256"],
        "status": "active",
        "scope_id": scope_id,
        "scope_kind": args.scope_kind,
        "enabled_at": activation["enabled_at"],
        "last_event_sha256": event["event_sha256"],
        "run_bundle": str(bundle_path(root, run_id).relative_to(project_root)),
    }
    atomic_json(active_path(root), pointer)
    return {"status": "active", "activation_id": run_id, "runtime_root": str(root), "bundle": str(bundle_path(root, run_id))}


def checkpoint(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    run_id = resolve_run_id(root, args.activation_id, require_active=True)
    _, events, _ = load_authoritative_run(root, run_id, repair_derived=True)
    refinement = derive_refinement_state(events)
    current_unit = refinement["current_unit"]
    decision = args.decision
    remainders = string_list(args.blocking_remainder)
    owner = args.owner_of_remainder
    if current_unit is not None:
        state = current_unit.get("state")
        if state in ("open", "resolved"):
            raise RuntimeErrorMessage(
                f"checkpoint cannot bypass refinement unit {current_unit.get('unit_id')}; record its result/absorb first"
            )
        if state == "blocked" and decision not in ("need_input", "stop"):
            raise RuntimeErrorMessage("blocked refinement unit only permits need_input or stop")
    if decision == "refine":
        if owner != "current" or len(remainders) != 1:
            raise RuntimeErrorMessage("refine requires exactly one concrete blocking remainder owned by current Owner")
    elif decision == "need_input":
        if owner not in ("upstream", "external") or not remainders:
            raise RuntimeErrorMessage("need_input requires an upstream/external blocking remainder")
    elif decision == "handoff":
        if owner not in ("downstream", "none"):
            raise RuntimeErrorMessage("handoff remainder must be downstream-owned or none")
    artifact = artifact_record(project_root, args.artifact, args.artifact_ref, args.artifact_sha256)
    current_parent = refinement["current_parent"]
    if decision == "refine" and artifact is None:
        raise RuntimeErrorMessage("refine requires a bound Parent Artifact")
    if current_parent is not None and decision in ("refine", "handoff") and artifact != current_parent:
        raise RuntimeErrorMessage("checkpoint artifact must equal the latest absorbed Parent Artifact")
    refinement_unit = None
    if decision == "refine":
        unit_id = f"RU-{refinement['unit_count'] + 1:04d}"
        refinement_unit = {
            "unit_id": unit_id,
            "unit_kind": args.unit_kind,
            "question": remainders[0],
            "scope_boundary": non_empty(args.unit_scope),
            "completion_criterion": non_empty(args.completion_criterion),
            "parent_artifact": artifact,
        }
    payload = {
        "event_type": "checkpoint",
        "decision": decision,
        "artifact": artifact,
        "blocking_remainder": remainders,
        "owner_of_remainder": owner,
        "consequence_if_handoff_now": (args.consequence_if_handoff_now or "").strip(),
        "next_minimum_work": (args.next_minimum_work or "").strip(),
        "evidence_refs": string_list(args.evidence_ref),
        "cost": cost_record(args),
        "refinement_unit": refinement_unit,
    }
    if decision in ("refine", "need_input") and not payload["consequence_if_handoff_now"]:
        raise RuntimeErrorMessage(f"{decision} requires --consequence-if-handoff-now")
    if decision == "refine" and not payload["next_minimum_work"]:
        raise RuntimeErrorMessage("refine requires --next-minimum-work")
    event = append_event(root, run_id, payload)
    result = {"status": "recorded", "activation_id": run_id, "sequence": event["sequence"], "decision": decision, "bundle": str(bundle_path(root, run_id))}
    if refinement_unit is not None:
        result["refinement_unit_id"] = refinement_unit["unit_id"]
    return result


def work(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    run_id = resolve_run_id(root, args.activation_id, require_active=True)
    _, events, _ = load_authoritative_run(root, run_id, repair_derived=True)
    refinement = derive_refinement_state(events)
    unit = refinement["current_unit"]
    if unit is None or unit.get("state") != "open":
        raise RuntimeErrorMessage("work event requires one open Refinement Unit")
    if args.unit_id and args.unit_id != unit.get("unit_id"):
        raise RuntimeErrorMessage("--unit-id does not match the open Refinement Unit")
    ensure_parent_unchanged(project_root, unit)
    before = artifact_record(project_root, args.artifact_before, args.artifact_before_ref, args.artifact_before_sha256)
    after = artifact_record(project_root, args.artifact_after, args.artifact_after_ref, args.artifact_after_sha256)
    payload = {
        "event_type": "work",
        "unit_id": unit["unit_id"],
        "work_kind": args.work_kind,
        "changed_scope": non_empty(args.changed_scope),
        "artifact_before": before,
        "artifact_after": after,
        "resolved_remainders": string_list(args.resolved_remainder),
        "introduced_remainders": string_list(args.introduced_remainder),
        "evidence_refs": string_list(args.evidence_ref),
        "cost": cost_record(args),
    }
    event = append_event(root, run_id, payload)
    return {"status": "recorded", "activation_id": run_id, "sequence": event["sequence"], "unit_id": unit["unit_id"], "work_kind": args.work_kind, "bundle": str(bundle_path(root, run_id))}


def refine_result(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    run_id = resolve_run_id(root, args.activation_id, require_active=True)
    _, events, _ = load_authoritative_run(root, run_id, repair_derived=True)
    refinement = derive_refinement_state(events)
    unit = refinement["current_unit"]
    if unit is None or unit.get("state") != "open":
        raise RuntimeErrorMessage("refine-result requires one open Refinement Unit")
    if args.unit_id and args.unit_id != unit.get("unit_id"):
        raise RuntimeErrorMessage("--unit-id does not match the open Refinement Unit")
    ensure_parent_unchanged(project_root, unit)
    resolved = string_list(args.resolved_remainder)
    introduced = string_list(args.introduced_remainder)
    if args.result_status == "resolved" and unit.get("question") not in resolved:
        raise RuntimeErrorMessage("resolved refine-result must explicitly resolve the Refinement Unit question")
    result_artifact = artifact_record(project_root, args.result_artifact, args.result_artifact_ref, args.result_artifact_sha256)
    payload = {
        "event_type": "refine_result",
        "unit_id": unit["unit_id"],
        "result_status": args.result_status,
        "result_summary": non_empty(args.result_summary),
        "result_artifact": result_artifact,
        "resolved_remainders": resolved,
        "introduced_remainders": introduced,
        "evidence_refs": string_list(args.evidence_ref),
        "cost": cost_record(args),
    }
    if len(payload["result_summary"]) > 4096:
        raise RuntimeErrorMessage("--result-summary must be at most 4096 characters; put large results in --result-artifact")
    event = append_event(root, run_id, payload)
    return {"status": "recorded", "activation_id": run_id, "sequence": event["sequence"], "unit_id": unit["unit_id"], "result_status": args.result_status, "bundle": str(bundle_path(root, run_id))}


def absorb(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    run_id = resolve_run_id(root, args.activation_id, require_active=True)
    _, events, _ = load_authoritative_run(root, run_id, repair_derived=True)
    refinement = derive_refinement_state(events)
    unit = refinement["current_unit"]
    if unit is None or unit.get("state") != "resolved":
        raise RuntimeErrorMessage("absorb requires one resolved Refinement Unit")
    if args.unit_id and args.unit_id != unit.get("unit_id"):
        raise RuntimeErrorMessage("--unit-id does not match the resolved Refinement Unit")
    before = unit.get("parent_artifact")
    if args.absorb_mode == "confirm" and not any((args.parent_after, args.parent_after_ref, args.parent_after_sha256)):
        if isinstance(before, dict) and before.get("ref_kind") == "project_file":
            live_parent = artifact_record(project_root, before.get("ref"), None, None)
            if live_parent != before:
                raise RuntimeErrorMessage("confirm absorb requires the live Parent Artifact to remain unchanged")
        after = before
    else:
        after = artifact_record(project_root, args.parent_after, args.parent_after_ref, args.parent_after_sha256)
    if after is None:
        raise RuntimeErrorMessage("absorb requires --parent-after/--parent-after-ref unless mode=confirm")
    if args.absorb_mode == "update" and after == before:
        raise RuntimeErrorMessage("update absorb requires a new Parent Artifact identity")
    if args.absorb_mode == "confirm" and after != before:
        raise RuntimeErrorMessage("confirm absorb must retain the Parent Artifact identity")
    payload = {
        "event_type": "absorb",
        "unit_id": unit["unit_id"],
        "result_sequence": unit["result_sequence"],
        "absorb_mode": args.absorb_mode,
        "parent_before": before,
        "parent_after": after,
        "absorbed_scope": non_empty(args.absorbed_scope),
        "cost": cost_record(args),
    }
    event = append_event(root, run_id, payload)
    return {"status": "recorded", "activation_id": run_id, "sequence": event["sequence"], "unit_id": unit["unit_id"], "parent_artifact": after, "bundle": str(bundle_path(root, run_id))}


def guard_handoff(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    active = load_active(root, required=False)
    if active is None:
        return {"allowed": True, "status": "disabled", "reason": "WAE Loop is not active"}
    run_id = active["activation_id"]
    _, events, _ = load_authoritative_run(root, run_id, repair_derived=True)
    checkpoints = [event for event in events if event.get("event_type") == "checkpoint"]
    if not checkpoints:
        raise RuntimeErrorMessage("active WAE Loop requires a checkpoint before handoff")
    latest = checkpoints[-1]
    if latest.get("decision") != "handoff":
        raise RuntimeErrorMessage(
            f"active WAE Loop latest checkpoint is {latest.get('decision')!r}; handoff is not authorized"
        )
    requested_artifact = artifact_record(
        project_root,
        args.artifact,
        args.artifact_ref,
        args.artifact_sha256,
    )
    checkpoint_artifact = latest.get("artifact")
    if requested_artifact is not None:
        if checkpoint_artifact is None:
            raise RuntimeErrorMessage("latest handoff checkpoint is not bound to the requested artifact")
        for field in ("ref", "sha256"):
            expected = requested_artifact.get(field)
            actual = checkpoint_artifact.get(field)
            if expected is not None and expected != actual:
                raise RuntimeErrorMessage(
                    f"handoff artifact {field} does not match latest checkpoint"
                )
    return {
        "allowed": True,
        "status": "active",
        "activation_id": run_id,
        "checkpoint_sequence": latest["sequence"],
        "artifact": checkpoint_artifact,
        "bundle": str(bundle_path(root, run_id)),
    }


def outcome(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    run_id = resolve_run_id(root, args.activation_id, require_active=False)
    _, events, _ = load_authoritative_run(root, run_id, repair_derived=True)
    if not any(event.get("event_type") == "checkpoint" and event.get("decision") == "handoff" for event in events):
        raise RuntimeErrorMessage("downstream outcome requires at least one recorded handoff checkpoint")
    payload = {
        "event_type": "outcome",
        "handoff_result": args.handoff_result,
        "downstream_invented_upstream_semantics": args.downstream_invented_upstream_semantics,
        "downstream_requested_missing_upstream_decision": args.downstream_requested_missing_upstream_decision,
        "downstream_overrode_handoff": args.downstream_overrode_handoff,
        "rework_required": args.rework_required,
        "rework_owner": args.rework_owner,
        "acceptance_result": args.acceptance_result,
        "notes": (args.notes or "").strip(),
        "telemetry_coverage": {
            "model_calls": args.model_calls_coverage,
            "tool_calls": args.tool_calls_coverage,
            "artifact_changes": args.artifact_changes_coverage,
            "downstream_outcome": args.downstream_outcome_coverage,
        },
        "cost": cost_record(args),
    }
    event = append_event(root, run_id, payload)
    return {"status": "recorded", "activation_id": run_id, "sequence": event["sequence"], "handoff_result": args.handoff_result, "bundle": str(bundle_path(root, run_id))}


def finish(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    run_id = resolve_run_id(root, args.activation_id, require_active=True)
    _, _, summary = load_authoritative_run(root, run_id, repair_derived=True)
    last = summary.get("last_checkpoint_decision")
    expected = {"completed": "handoff", "need_input": "need_input", "stopped": "stop"}
    if args.status != "aborted" and expected[args.status] != last:
        raise RuntimeErrorMessage(f"finish status {args.status} requires latest checkpoint decision {expected[args.status]!r}, found {last!r}")
    event = append_event(
        root,
        run_id,
        {
            "event_type": "finish",
            "status": args.status,
            "notes": (args.notes or "").strip(),
            "cost": cost_record(args),
        },
    )
    path = active_path(root)
    if path.exists():
        current = read_json(path)
        if current.get("activation_id") == run_id:
            path.unlink()
    refresh_bundle(root, run_id)
    return {"status": args.status, "activation_id": run_id, "sequence": event["sequence"], "bundle": str(bundle_path(root, run_id))}


def validate_run(root: Path, run_id: str) -> list[str]:
    findings: list[str] = []
    try:
        activation = read_json(activation_path(root, run_id))
        events = read_trace(trace_path(root, run_id))
    except RuntimeErrorMessage as exc:
        return [str(exc)]
    findings.extend(validate_trace_integrity(activation, events, expected_run_id=run_id))
    if findings:
        return findings
    expected_summary = derive_summary(activation, events)
    try:
        actual_summary = read_json(summary_path(root, run_id))
        if actual_summary != expected_summary:
            findings.append("summary does not match authoritative activation/trace state")
    except RuntimeErrorMessage as exc:
        findings.append(str(exc))
    try:
        actual_bundle = read_json(bundle_path(root, run_id))
        if actual_bundle != expected_bundle(activation, events, expected_summary):
            findings.append("portable wae-loop-run.json does not match authoritative activation/trace state")
    except RuntimeErrorMessage as exc:
        findings.append(str(exc))
    return findings


def validate_cmd(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    if args.all:
        ids = sorted(path.name for path in (root / "runs").glob("*") if path.is_dir()) if (root / "runs").exists() else []
    else:
        ids = [resolve_run_id(root, args.activation_id, require_active=False)]
    reports = []
    for run_id in ids:
        findings = validate_run(root, run_id)
        reports.append({"activation_id": run_id, "valid": not findings, "findings": findings, "bundle": str(bundle_path(root, run_id))})
    return {"schema_version": SCHEMA_VERSION, "runs": reports, "valid": all(item["valid"] for item in reports)}


def status(args: argparse.Namespace) -> dict[str, Any]:
    project_root = args.project_root.resolve()
    root = runtime_root(project_root, args.runtime_dir)
    active = load_active(root, required=False)
    if active:
        run_id = active["activation_id"]
        _, _, summary = load_authoritative_run(root, run_id, repair_derived=True)
        return {"status": "active", "activation": active, "summary": summary, "bundle": str(bundle_path(root, run_id))}
    if args.activation_id:
        run_id = resolve_run_id(root, args.activation_id, require_active=False)
        _, _, summary = load_authoritative_run(root, run_id, repair_derived=True)
        return {"status": "inactive", "summary": summary, "bundle": str(bundle_path(root, run_id))}
    return {"status": "disabled", "runtime_root": str(root)}


def add_cost_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model-requests", type=int)
    parser.add_argument("--input-tokens", type=int)
    parser.add_argument("--output-tokens", type=int)
    parser.add_argument("--tool-calls", type=int)
    parser.add_argument("--source-reads", type=int)
    parser.add_argument("--retry-count", type=int)
    parser.add_argument("--elapsed-ms", type=int)


def add_artifact_args(parser: argparse.ArgumentParser, prefix: str = "artifact") -> None:
    option = prefix.replace("_", "-")
    parser.add_argument(f"--{option}", dest=prefix)
    parser.add_argument(f"--{option}-ref", dest=f"{prefix}_ref")
    parser.add_argument(f"--{option}-sha256", dest=f"{prefix}_sha256")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root that owns the pilot trace. Default: cwd.")
    result.add_argument("--runtime-dir", type=Path, help="Override .mindthus/wae-loop beneath project root.")
    sub = result.add_subparsers(dest="command", required=True)

    p = sub.add_parser("enable", help="Explicitly activate WAE Loop for one bounded scope.")
    p.add_argument("--activation-id")
    p.add_argument("--scope-id", required=True)
    p.add_argument("--scope-kind", choices=("task", "phase", "mission", "other"), default="task")
    p.add_argument("--enabled-by", choices=("user", "project", "host", "other"), default="user")
    p.add_argument("--project")
    p.add_argument("--host")
    p.add_argument("--model-mode")
    p.add_argument("--current-owner", required=True)
    p.add_argument("--downstream-owner", required=True)
    p.add_argument("--handoff-purpose", required=True)
    p.add_argument("--current-responsibility", action="append", default=[], required=True)
    p.add_argument("--downstream-freedom", action="append", default=[])
    p.add_argument("--reserved-decision", action="append", default=[])

    p = sub.add_parser("checkpoint", help="Record a mandatory handoff sufficiency decision while active.")
    p.add_argument("--activation-id")
    p.add_argument("--decision", choices=DECISIONS, required=True)
    add_artifact_args(p)
    p.add_argument("--blocking-remainder", action="append", default=[])
    p.add_argument("--owner-of-remainder", choices=REMAINDER_OWNERS, required=True)
    p.add_argument("--consequence-if-handoff-now")
    p.add_argument("--next-minimum-work")
    p.add_argument("--unit-kind", choices=UNIT_KINDS, default="semantic_decision")
    p.add_argument("--unit-scope", help="Bounded semantic scope owned by this Refinement Unit.")
    p.add_argument("--completion-criterion", help="Observable condition that closes this Refinement Unit.")
    p.add_argument("--evidence-ref", action="append", default=[])
    add_cost_args(p)

    p = sub.add_parser("work", help="Record bounded work inside the open Refinement Unit.")
    p.add_argument("--activation-id")
    p.add_argument("--unit-id")
    p.add_argument("--work-kind", choices=WORK_KINDS, required=True)
    p.add_argument("--changed-scope", required=True)
    add_artifact_args(p, "artifact_before")
    add_artifact_args(p, "artifact_after")
    p.add_argument("--resolved-remainder", action="append", default=[])
    p.add_argument("--introduced-remainder", action="append", default=[])
    p.add_argument("--evidence-ref", action="append", default=[])
    add_cost_args(p)

    p = sub.add_parser("refine-result", help="Record the bounded canonical result of the open Refinement Unit before Parent absorption.")
    p.add_argument("--activation-id")
    p.add_argument("--unit-id")
    p.add_argument("--result-status", choices=RESULT_STATUSES, required=True)
    p.add_argument("--result-summary", required=True)
    add_artifact_args(p, "result_artifact")
    p.add_argument("--resolved-remainder", action="append", default=[])
    p.add_argument("--introduced-remainder", action="append", default=[])
    p.add_argument("--evidence-ref", action="append", default=[])
    add_cost_args(p)

    p = sub.add_parser("absorb", help="Bind a resolved Refinement Unit result into the Parent Handoff Artifact.")
    p.add_argument("--activation-id")
    p.add_argument("--unit-id")
    p.add_argument("--absorb-mode", choices=ABSORB_MODES, required=True)
    add_artifact_args(p, "parent_after")
    p.add_argument("--absorbed-scope", required=True)
    add_cost_args(p)

    p = sub.add_parser("guard-handoff", help="Mechanically allow handoff only when the active scope has a matching handoff checkpoint.")
    add_artifact_args(p)

    p = sub.add_parser("outcome", help="Record the actual downstream result after a handoff.")
    p.add_argument("--activation-id")
    p.add_argument("--handoff-result", choices=OUTCOME_RESULTS, required=True)
    p.add_argument("--downstream-invented-upstream-semantics", choices=TRINARY, default="unknown")
    p.add_argument("--downstream-requested-missing-upstream-decision", choices=TRINARY, default="unknown")
    p.add_argument("--downstream-overrode-handoff", choices=TRINARY, default="unknown")
    p.add_argument("--rework-required", choices=TRINARY, default="unknown")
    p.add_argument("--rework-owner", choices=REWORK_OWNERS, default="unknown")
    p.add_argument("--acceptance-result", choices=ACCEPTANCE_RESULTS, default="unknown")
    p.add_argument("--notes")
    p.add_argument("--model-calls-coverage", choices=COVERAGE, default="unknown")
    p.add_argument("--tool-calls-coverage", choices=COVERAGE, default="unknown")
    p.add_argument("--artifact-changes-coverage", choices=COVERAGE, default="unknown")
    p.add_argument("--downstream-outcome-coverage", choices=COVERAGE, default="unknown")
    add_cost_args(p)

    p = sub.add_parser("finish", help="Close the active scope after a terminal checkpoint.")
    p.add_argument("--activation-id")
    p.add_argument("--status", choices=FINISH_STATUSES, required=True)
    p.add_argument("--notes")
    add_cost_args(p)

    p = sub.add_parser("status", help="Show whether WAE Loop is active and the portable bundle path.")
    p.add_argument("--activation-id")

    p = sub.add_parser("validate", help="Validate trace structure and the event hash chain.")
    p.add_argument("--activation-id")
    p.add_argument("--all", action="store_true")

    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "enable":
            result = enable(args)
        elif args.command == "checkpoint":
            result = checkpoint(args)
        elif args.command == "work":
            result = work(args)
        elif args.command == "refine-result":
            result = refine_result(args)
        elif args.command == "absorb":
            result = absorb(args)
        elif args.command == "guard-handoff":
            result = guard_handoff(args)
        elif args.command == "outcome":
            result = outcome(args)
        elif args.command == "finish":
            result = finish(args)
        elif args.command == "validate":
            result = validate_cmd(args)
        else:
            result = status(args)
    except RuntimeErrorMessage as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.command == "validate" and not result["valid"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
