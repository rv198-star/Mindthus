#!/usr/bin/env python3
"""Shared helpers for tplan runtime scripts.

These helpers enforce runtime shape, state, and authority. They do not decide semantic
truth.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
import threading
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX path
    msvcrt = None  # type: ignore[assignment]


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime_bootstrap import activate_runtime

activate_runtime(__file__)

from _runtime.core.io import load_json
from _runtime.core.report import Finding
from _runtime.core.shape import findings_from_messages


SCHEMA_VERSION = "tplan.v0.1"
EXECUTION_TRACE_SCHEMA_VERSION = "tplan.execution_trace.v0.1"
MISSION_TRANSACTION_SCHEMA_VERSION = "tplan.mission_transaction.v0.1"
SHARED_CONTEXT_SCHEMA_VERSION = "tplan.shared_context.v0.1"
SHARED_CONTEXT_MARKER_START = "<!-- tplan-shared-context"
SHARED_CONTEXT_MARKER_END = "-->"

MISSION_STATUSES = {
    "active",
    "completed",
    "blocked",
    "budget_exhausted",
    "abandoned",
    "superseded",
    "requires_human",
}

TERMINAL_MISSION_STATUSES = MISSION_STATUSES - {"active"}

TASK_STATUSES = {
    "pending",
    "active",
    "blocked",
    "completed",
    "paused",
    "pruned",
    "abandoned",
    "superseded",
}
TERMINAL_TASK_STATUSES = {"completed", "pruned", "abandoned", "superseded"}
ALLOWED_TASK_TRANSITIONS = {
    "pending": TASK_STATUSES,
    "active": TASK_STATUSES - {"pending"},
    "blocked": TASK_STATUSES - {"pending"},
    "paused": TASK_STATUSES - {"pending"},
    "completed": {"completed"},
    "pruned": {"pruned"},
    "abandoned": {"abandoned"},
    "superseded": {"superseded"},
}

TASK_ROLES = {"success-critical", "supporting", "exploratory"}
NODE_KINDS = {"task", "subtask", "step"}

TRACE_EVENT_TYPES = {
    "mission_initialized",
    "node_added",
    "task_status_changed",
    "active_node_changed",
    "mission_status_changed",
    "span_started",
    "span_completed",
}
TRACE_SPAN_EVENT_TYPES = {"span_started", "span_completed"}
TRACE_SPAN_KINDS = {"model", "agent_turn", "script", "tool", "wait", "runtime"}
TRACE_SPAN_STATUSES = {"ok", "error", "cancelled", "unknown"}
TRACE_MEASUREMENT_SOURCES = {"platform_reported", "host_measured", "inferred", "unavailable"}
TRACE_ATTRIBUTIONS = {"exact", "shared", "mission_overhead", "unattributed"}
TRACE_USAGE_FIELDS = {
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
}
TRACE_SPAN_FIELDS = {
    "span_id",
    "parent_span_id",
    "kind",
    "label",
    "status",
    "measurement_source",
    "attribution",
    "started_at",
    "finished_at",
    "duration_ms",
    "attempt",
    "shared_task_ids",
}
TRACE_SPAN_START_FIELDS = TRACE_SPAN_FIELDS - {"status", "started_at", "finished_at", "duration_ms"}
TRACE_METADATA_FIELDS = {
    "agent_role",
    "cache_hit",
    "exit_code",
    "model",
    "operation",
    "parallel_group_id",
    "provider",
    "tool_class",
}
TRACE_REF_FIELDS = {"artifact_refs", "evidence_ids", "evidence_links"}
TRACE_COMMON_RECORD_FIELDS = {
    "schema_version",
    "event_id",
    "event_type",
    "timestamp",
    "mission_id",
    "task_id",
    "refs",
}
TRACE_LIFECYCLE_PAYLOAD_FIELDS = {
    "mission_initialized": {"mission_status", "active_task_id", "tasks"},
    "node_added": {"parent_id", "kind", "status", "title", "dynamic"},
    "task_status_changed": {"from_status", "to_status", "outcome_summary", "artifact_refs"},
    "active_node_changed": {"from_task_id", "to_task_id"},
    "mission_status_changed": {"from_status", "to_status"},
}
TRACE_THREAD_LOCK = threading.RLock()
TRACE_FORBIDDEN_KEYS = {
    "prompt",
    "raw_prompt",
    "response",
    "raw_response",
    "stdout",
    "stderr",
    "environment",
    "env",
    "credentials",
    "credential",
    "secrets",
    "secret",
    "command",
    "command_args",
    "arguments",
}

RECOMMENDATIONS = {"add", "subtract", "continue", "switch", "close", "escalate"}

PATH_ASSESSMENT_FIELDS = {
    "marginal_roi": {"positive", "weak", "negative", "unclear"},
    "path_role": {"unique_blocker", "dominant_path", "one_of_many", "unclear"},
    "evidence_delta": {
        "new_evidence_expected",
        "weak_evidence_expected",
        "no_new_evidence_expected",
        "unclear",
    },
}

PATH_ASSESSMENT_HOOKS = {"selection", "subtraction", "loopback", "chain_role"}

RISK_ASSESSMENT_FIELDS = {
    "invalid_evidence_risk": {"low", "medium", "high", "unclear"},
    "failure_risk": {"low", "medium", "high", "unclear"},
    "risk_adjusted_value": {"positive", "weak", "negative", "unclear"},
    "next_gate": {"continue", "health_check", "switch", "stop", "escalate"},
}

MISSION_PULSE_SCHEMA_VERSION = "tplan.pulse.v0.2"
MISSION_PULSE_TRIGGERS = {
    "manual",
    "before_continue",
    "before_freeze",
    "before_handoff",
    "before_stop",
    "checkpoint_batch",
    "feedback",
    "blocker",
    "shared_risk",
    "active_switch_candidate",
    "branch_cleanup",
}
MISSION_PULSE_SCOPES = {"active_node", "subpath", "mission"}
MISSION_PULSE_NEXT_GATES = {
    "continue",
    "continuation_authorization",
    "anti_spiral_audit",
    "selection",
    "subtraction",
    "loopback",
    "mission_review",
    "health_check",
    "stop",
    "escalate",
}
MISSION_PULSE_EVIDENCE_DELTAS = {
    "new_evidence_expected",
    "weak_evidence_expected",
    "no_new_evidence_expected",
    "unclear",
}
MISSION_PULSE_BRANCH_DISPOSITIONS = {"keep", "close", "merge", "defer", "prune", "unclear"}
MISSION_PULSE_SYSTEMIC_PROBES = {
    "not_needed",
    "use_existing_structure",
    "replace_local_fix",
    "needs_gate",
    "unclear",
}
MISSION_PULSE_CANDIDATE_SOURCE_KINDS = {
    "trigger",
    "mission_state",
    "evidence_event",
    "step_log",
    "risk_signal",
    "task",
    "validation",
    "derived",
}
MISSION_PULSE_CANDIDATE_PRIORITIES = {
    "requires_human_or_stop",
    "mission_boundary",
    "runtime_integrity",
    "active_shared_risk",
    "current_blocker_or_feedback",
    "anti_spiral",
    "checkpoint_weak_evidence_delta",
    "branch_or_switch_cleanup",
    "same_path_continuation",
}
MISSION_PULSE_PRIORITY_ORDER = {
    "requires_human_or_stop": 1,
    "mission_boundary": 2,
    "runtime_integrity": 3,
    "active_shared_risk": 4,
    "current_blocker_or_feedback": 5,
    "anti_spiral": 6,
    "checkpoint_weak_evidence_delta": 7,
    "branch_or_switch_cleanup": 8,
    "same_path_continuation": 9,
}
MISSION_PULSE_SIGNAL_TIE_BREAK_ORDER = {
    "requires_human": 1,
    "mission_boundary_review": 2,
    "active_node_missing": 3,
    "active_shared_risk": 4,
    "blocker_or_surprise": 5,
    "user_feedback": 6,
    "third_touch": 7,
    "checkpoint_batch_without_acceptance_evidence": 8,
    "branch_cleanup_candidate": 9,
    "same_path_continuation": 10,
}
MISSION_PULSE_CANDIDATE_SEVERITIES = {"low", "medium", "high", "critical"}
MISSION_PULSE_SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
MISSION_PULSE_CANDIDATE_FRESHNESS = {
    "current_trigger",
    "current_state",
    "current_path",
    "checkpoint_window",
    "recent_evidence",
    "historical",
    "unknown",
}
MISSION_PULSE_CANDIDATE_REQUIRED_FIELDS = {
    "signal",
    "candidate_next_gate",
    "scope",
    "source_kind",
    "source_ids",
    "priority_class",
    "severity",
    "freshness",
    "reason",
    "context",
}
MISSION_PULSE_GATE_OWNERS = {
    "continue": "inline_alignment",
    "continuation_authorization": "linear_continuation_gate",
    "anti_spiral_audit": "anti_spiral_runtime_gate",
    "selection": "selection_hook",
    "subtraction": "subtraction_hook",
    "loopback": "loopback_hook",
    "mission_review": "mission_review_gate",
    "health_check": "shared_risk_mission_health_route",
    "stop": "stop_report",
    "escalate": "human_or_authority_escalation",
}
MISSION_PULSE_CONSUMABLE_SIGNALS = {
    "requires_human",
    "blocker_or_surprise",
    "user_feedback",
    "third_touch",
    "checkpoint_batch_without_acceptance_evidence",
    "branch_cleanup_candidate",
}
MISSION_PULSE_STICKY_SIGNALS = {
    "active_shared_risk",
    "same_path_continuation",
    "mission_boundary_review",
    "active_node_missing",
}
PULSE_STATE_REQUIRED_FIELDS = {
    "fingerprint",
    "signal",
    "candidate_next_gate",
    "priority_class",
    "source_ids",
    "consumed_at",
}
PULSE_STATE_STRING_FIELDS = (
    "fingerprint",
    "signal",
    "candidate_next_gate",
    "priority_class",
    "consumed_at",
    "trigger",
    "consumption_event_id",
    "note",
)

CONTINUATION_TRIGGER_REASONS = {
    "third_touch",
    "repeated_same_path_attempt",
    "post_continuation_defect",
    "high_cost_or_high_blast_radius_continuation",
    # Compatibility aliases from the original pressure-test scenario. New records should
    # prefer the generic same-path continuation reasons above.
    "second_large_rerun",
    "post_generation_defect",
    "repeated_negative_feedback",
    "weak_or_unclear_evidence_delta",
    "manual_authorization",
}

CONTINUATION_AUTHORIZATION_FIELDS = {
    "evidence_shape_lint": {"pass", "fail", "not_applicable", "unclear"},
    "defect_classification": {"none", "acceptance_blocking", "batchable_detail", "unclear"},
    "expected_evidence_delta": PATH_ASSESSMENT_FIELDS["evidence_delta"],
    "authorized_action": {
        "continue_same_path",
        "targeted_fix",
        "batch_details",
        "mission_review",
        "anti_spiral_audit",
        "stop",
    },
}

RISK_SIGNAL_SCOPES = {
    "shared_environment",
    "shared_dependency",
    "shared_data",
    "shared_authority",
    "shared_evidence_channel",
    "mission_policy",
    "other",
}

RISK_SIGNAL_SEVERITIES = {"low", "medium", "high", "critical"}
RISK_SIGNAL_SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}
RISK_SIGNAL_CONFIDENCES = {"low", "medium", "high", "unclear"}
RISK_SIGNAL_STATUSES = {"active", "resolved", "superseded", "invalidated"}

RISK_SIGNAL_REQUIRED_FIELDS = {
    "id",
    "source_task_id",
    "scope",
    "signal",
    "severity",
    "confidence",
    "affected_surfaces",
    "value_effect",
    "recommended_gate",
    "recovery_condition",
    "status",
    "created_at",
    "updated_at",
}

RISK_SIGNAL_STRING_FIELDS = (
    "id",
    "source_task_id",
    "signal",
    "value_effect",
    "recommended_gate",
    "recovery_condition",
    "created_at",
    "updated_at",
    "source_evidence_id",
    "notes",
)

MISSION_REQUIRED_FIELDS = {
    "id",
    "title",
    "objective",
    "status",
    "human_in_loop",
    "risk_tolerance",
    "resource_sufficiency",
    "acceptance_evidence",
}

BASE_TASK_REQUIRED_FIELDS = {
    "id",
    "parent_id",
    "kind",
    "level",
    "title",
    "status",
    "role",
    "evidence_links",
}

MISSION_ALIGNED_TASK_FIELDS = {
    "mission_contribution",
    "acceptance_evidence",
}

PARENT_ALIGNED_TASK_FIELDS = {
    "parent_contribution",
    "parent_acceptance",
    "mission_trace",
}

STEP_TASK_FIELDS = {
    "parent_contribution",
    "mission_trace",
    "step_action",
    "done_condition",
}

POLICY_FIELDS = ("human_in_loop", "risk_tolerance", "resource_sufficiency")
MISSION_STRING_FIELDS = ("id", "title", "objective")
TASK_STRING_FIELDS = (
    "title",
    "kind",
    "mission_contribution",
    "parent_contribution",
    "parent_acceptance",
    "mission_trace",
    "step_action",
    "done_condition",
)


class TplanError(ValueError):
    """Runtime contract violation."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "unnamed"


def runtime_dir_identity(project_root: Path, mission_dir: Path) -> str:
    try:
        return str(mission_dir.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(mission_dir.resolve())


def validate_mission_directory_identity(mission: Any, mission_dir: Path) -> list[str]:
    if not isinstance(mission, dict):
        return []
    mission_meta = mission.get("mission")
    if not isinstance(mission_meta, dict):
        return []
    mission_id = mission_meta.get("id")
    if not isinstance(mission_id, str) or not mission_id:
        return []
    dir_slug = slugify(mission_dir.name)
    if dir_slug in {"mission", "missions"}:
        return []
    if slugify(mission_id) not in dir_slug:
        return [f"mission directory {mission_dir.name} does not match mission_id {mission_id}"]
    return []


def find_project_runtime_dirs(project_root: Path, mission_id: str) -> list[str]:
    if not project_root.exists():
        return []
    runtime_dirs: set[str] = set()
    for path in project_root.rglob("evidence.jsonl"):
        mission_path = path.parent / "mission.json"
        if not mission_path.exists():
            continue
        try:
            mission = read_json(mission_path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if mission.get("schema_version") != SCHEMA_VERSION:
            continue
        mission_meta = mission.get("mission")
        if not isinstance(mission_meta, dict):
            continue
        if mission_meta.get("id") == mission_id:
            runtime_dirs.add(runtime_dir_identity(project_root, mission_path.parent))
    return sorted(runtime_dirs)


def require_policy_value(name: str, value: int) -> int:
    if not 0 <= value <= 100:
        raise TplanError(f"{name} must be between 0 and 100")
    if name == "human_in_loop" and value not in {0, 100}:
        raise TplanError("human_in_loop must be 0 or 100 in tplan.v0.1")
    return value


def mission_paths(mission_dir: Path) -> dict[str, Path]:
    return {
        "dir": mission_dir,
        "mission": mission_dir / "mission.json",
        "narrative": mission_dir / "mission.md",
        "evidence": mission_dir / "evidence.jsonl",
        "trace": mission_dir / "execution_trace.jsonl",
        "transaction": mission_dir / ".mission-transaction.json",
        "logs": mission_dir / "logs",
        "archive": mission_dir / "archive",
        "reports": mission_dir / "reports",
    }


def cleanup_failed_initialization(mission_dir: Path) -> None:
    """Remove only files/directories owned by an initialization attempt."""

    paths = mission_paths(mission_dir)
    for name in ("transaction", "trace", "evidence", "narrative", "mission"):
        path = paths[name]
        if path.exists() and path.is_file():
            path.unlink()
    lock_path = mission_dir / ".execution_trace.lock"
    if lock_path.exists() and lock_path.is_file():
        lock_path.unlink()
    for name in ("logs", "archive", "reports"):
        path = paths[name]
        if path.exists() and path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    if mission_dir.exists():
        try:
            mission_dir.rmdir()
        except OSError:
            pass


def read_json(path: Path) -> dict[str, Any]:
    return load_json(path, error_factory=TplanError)


def _fsync_directory(path: Path) -> None:
    try:
        directory_fd = os.open(path, os.O_RDONLY)
    except OSError:  # pragma: no cover - platform-specific directory handles
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def write_json(path: Path, data: dict[str, Any], *, durable: bool = False) -> None:
    write_text_atomic(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n", durable=durable)


def write_text_atomic(path: Path, text: str, *, durable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            if durable:
                handle.flush()
                os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        if durable:
            _fsync_directory(path.parent)
    except OSError:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


@contextmanager
def execution_trace_lock(mission_dir: Path):
    """Serialize trace append/state commits across local processes."""

    lock_path = mission_dir / ".execution_trace.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_THREAD_LOCK, lock_path.open("a+b") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows fallback
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows fallback
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _read_mission_unlocked(mission_dir: Path) -> dict[str, Any]:
    return read_json(mission_paths(mission_dir)["mission"])


def read_mission(mission_dir: Path) -> dict[str, Any]:
    if not mission_dir.exists():
        return _read_mission_unlocked(mission_dir)
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        return _read_mission_unlocked(mission_dir)


LITE_RUNTIME_STATE_HEADING = "## Lite Runtime State"
LITE_RUNTIME_STATE_SECTION = re.compile(
    r"(?ms)^##[ \t]+Lite Runtime State[ \t]*\n.*?(?=^##[ \t]+|\Z)"
)
LITE_RUNTIME_LATEST_STATE = re.compile(r"(?m)^- latest_state: (.*)$")


def _one_line(value: object) -> str:
    return " ".join(str(value).split()) or "none"


def _lite_active_task_title(mission: dict[str, Any]) -> str:
    active_task_id = mission.get("active_task_id")
    if active_task_id is None:
        return "none"
    for task in mission.get("tasks", []):
        if isinstance(task, dict) and task.get("id") == active_task_id:
            return _one_line(task.get("title", "none"))
    return "missing"


def _lite_task_statuses(mission: dict[str, Any]) -> str:
    grouped: dict[str, list[str]] = {status: [] for status in sorted(TASK_STATUSES)}
    for task in mission.get("tasks", []):
        if not isinstance(task, dict):
            continue
        status = task.get("status")
        task_id = task.get("id")
        if isinstance(status, str) and status in grouped and isinstance(task_id, str):
            grouped[status].append(task_id)
    parts = [f"{status}: {', '.join(ids)}" for status, ids in grouped.items() if ids]
    return "; ".join(parts) or "none"


def render_lite_runtime_state(mission: dict[str, Any], latest_state: str) -> str:
    mission_meta = mission.get("mission", {})
    mission_status = mission_meta.get("status", "unknown") if isinstance(mission_meta, dict) else "unknown"
    active_task_id = mission.get("active_task_id") or "none"
    return (
        f"{LITE_RUNTIME_STATE_HEADING}\n\n"
        f"- mission_status: {_one_line(mission_status)}\n"
        f"- active_task_id: {_one_line(active_task_id)}\n"
        f"- active_task_title: {_lite_active_task_title(mission)}\n"
        f"- task_statuses: {_lite_task_statuses(mission)}\n"
        f"- latest_state: {_one_line(latest_state)}\n"
    )


def _existing_lite_latest_state(narrative: str) -> str:
    match = LITE_RUNTIME_LATEST_STATE.search(narrative)
    if match:
        return match.group(1)
    return "Runtime state synchronized from mission.json."


def _replace_lite_runtime_state_sections(narrative: str, next_block: str) -> str:
    matches = list(LITE_RUNTIME_STATE_SECTION.finditer(narrative))
    if not matches:
        return narrative

    parts: list[str] = []
    last_end = 0
    for index, match in enumerate(matches):
        parts.append(narrative[last_end : match.start()])
        if index == 0:
            parts.append(next_block)
        last_end = match.end()
    parts.append(narrative[last_end:])
    return "".join(parts)


def sync_mission_narrative(
    mission_dir: Path,
    mission: dict[str, Any],
    *,
    latest_state: str | None = None,
) -> None:
    narrative_path = mission_paths(mission_dir)["narrative"]
    if not narrative_path.exists():
        return
    narrative = narrative_path.read_text(encoding="utf-8")
    if LITE_RUNTIME_STATE_HEADING not in narrative:
        return

    state = latest_state if latest_state is not None else _existing_lite_latest_state(narrative)
    next_block = render_lite_runtime_state(mission, state)
    updated = _replace_lite_runtime_state_sections(narrative, next_block)
    if updated != narrative:
        write_text_atomic(narrative_path, updated)


def write_mission(mission_dir: Path, data: dict[str, Any], *, latest_state: str | None = None) -> None:
    write_json(mission_paths(mission_dir)["mission"], data)
    sync_mission_narrative(mission_dir, data, latest_state=latest_state)


def _recover_pending_mission_transaction_unlocked(mission_dir: Path) -> bool:
    """Roll a prepared lifecycle mutation forward after an interrupted process."""

    paths = mission_paths(mission_dir)
    transaction_path = paths["transaction"]
    if not transaction_path.exists():
        return False
    transaction = read_json(transaction_path)
    if transaction.get("schema_version") != MISSION_TRANSACTION_SCHEMA_VERSION:
        raise TplanError("unsupported pending Mission transaction schema")
    mission = transaction.get("mission")
    trace_text = transaction.get("trace_text")
    evidence_text = transaction.get("evidence_text")
    latest_state = transaction.get("latest_state")
    if not isinstance(mission, dict) or not isinstance(trace_text, str):
        raise TplanError("pending Mission transaction is malformed")
    if evidence_text is not None and not isinstance(evidence_text, str):
        raise TplanError("pending Mission transaction evidence_text is malformed")
    if latest_state is not None and not isinstance(latest_state, str):
        raise TplanError("pending Mission transaction latest_state is malformed")

    write_text_atomic(paths["trace"], trace_text, durable=True)
    if evidence_text is not None:
        write_text_atomic(paths["evidence"], evidence_text, durable=True)
    write_json(paths["mission"], mission, durable=True)
    sync_mission_narrative(mission_dir, mission, latest_state=latest_state)
    transaction_path.unlink()
    _fsync_directory(transaction_path.parent)
    return True


def task_map(mission: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = mission.get("tasks", [])
    if not isinstance(tasks, list):
        return {}
    return {task["id"]: task for task in tasks if isinstance(task, dict) and isinstance(task.get("id"), str)}


def acceptance_ids(mission: dict[str, Any]) -> set[str]:
    mission_meta = mission.get("mission", {})
    if not isinstance(mission_meta, dict):
        return set()
    evidence = mission_meta.get("acceptance_evidence", [])
    if not isinstance(evidence, list):
        return set()
    return {item["id"] for item in evidence if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _task_label(index: int, task: dict[str, Any]) -> str:
    task_id = task.get("id")
    return str(task_id) if isinstance(task_id, str) and task_id else str(index)


def _require_string_list(errors: list[str], task_id: str, name: str, value: Any) -> None:
    if not isinstance(value, list):
        errors.append(f"task {task_id} {name} must be a list")
        return
    if not all(isinstance(item, str) for item in value):
        errors.append(f"task {task_id} {name} items must be strings")


def _require_string_fields(errors: list[str], label: str, data: dict[str, Any], fields: tuple[str, ...]) -> None:
    for field in fields:
        if field in data and not isinstance(data[field], str):
            errors.append(f"{label} {field} must be a string")


def _risk_signal_label(index: int, signal: dict[str, Any]) -> str:
    risk_id = signal.get("id")
    return str(risk_id) if isinstance(risk_id, str) and risk_id else str(index)


def _validate_risk_signal_enum(
    errors: list[str],
    label: str,
    signal: dict[str, Any],
    field: str,
    allowed_values: set[str],
) -> None:
    value = signal.get(field)
    if field not in signal:
        return
    if not isinstance(value, str):
        errors.append(f"risk signal {label} {field} must be a string")
    elif value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        errors.append(f"risk signal {label} {field} unsupported: {value!r}; expected one of: {allowed}")


def _validate_shared_context(
    errors: list[str],
    state: dict[str, Any],
    tasks_by_id: dict[str, dict[str, Any]],
) -> None:
    if "shared_context" not in state:
        return

    shared_context = state.get("shared_context")
    if not isinstance(shared_context, dict):
        errors.append("shared_context must be an object")
        return

    risk_signals = shared_context.get("risk_signals")
    if not isinstance(risk_signals, list):
        errors.append("shared_context risk_signals must be a list")
        return

    seen_risk_ids: set[str] = set()
    for index, signal in enumerate(risk_signals, start=1):
        if not isinstance(signal, dict):
            errors.append(f"risk signal {index} must be an object")
            continue

        label = _risk_signal_label(index, signal)
        for field in sorted(RISK_SIGNAL_REQUIRED_FIELDS):
            if field not in signal:
                errors.append(f"risk signal {label} is missing {field}")

        _require_string_fields(errors, f"risk signal {label}", signal, RISK_SIGNAL_STRING_FIELDS)

        risk_id = signal.get("id")
        if isinstance(risk_id, str):
            if risk_id in seen_risk_ids:
                errors.append(f"duplicate risk signal id {risk_id}")
            else:
                seen_risk_ids.add(risk_id)

        source_task_id = signal.get("source_task_id")
        if isinstance(source_task_id, str) and source_task_id not in tasks_by_id:
            errors.append(f"risk signal {label} source_task_id {source_task_id} does not exist")

        affected_surfaces = signal.get("affected_surfaces")
        if "affected_surfaces" in signal:
            if not isinstance(affected_surfaces, list):
                errors.append(f"risk signal {label} affected_surfaces must be a list")
            elif not affected_surfaces:
                errors.append(f"risk signal {label} affected_surfaces must not be empty")
            elif not all(isinstance(item, str) for item in affected_surfaces):
                errors.append(f"risk signal {label} affected_surfaces items must be strings")

        supersedes = signal.get("supersedes")
        if "supersedes" in signal:
            if not isinstance(supersedes, list):
                errors.append(f"risk signal {label} supersedes must be a list")
            elif not all(isinstance(item, str) for item in supersedes):
                errors.append(f"risk signal {label} supersedes items must be strings")

        _validate_risk_signal_enum(errors, label, signal, "scope", RISK_SIGNAL_SCOPES)
        _validate_risk_signal_enum(errors, label, signal, "severity", RISK_SIGNAL_SEVERITIES)
        _validate_risk_signal_enum(errors, label, signal, "confidence", RISK_SIGNAL_CONFIDENCES)
        _validate_risk_signal_enum(errors, label, signal, "status", RISK_SIGNAL_STATUSES)


def _validate_pulse_state(errors: list[str], state: dict[str, Any]) -> None:
    if "pulse_state" not in state:
        return
    pulse_state = state.get("pulse_state")
    if not isinstance(pulse_state, dict):
        errors.append("pulse_state must be an object")
        return

    consumed_candidates = pulse_state.get("consumed_candidates")
    if not isinstance(consumed_candidates, list):
        errors.append("pulse_state consumed_candidates must be a list")
        return

    seen_fingerprints: set[str] = set()
    for index, item in enumerate(consumed_candidates, start=1):
        if not isinstance(item, dict):
            errors.append(f"pulse_state consumed candidate {index} must be an object")
            continue
        label = item.get("signal") if isinstance(item.get("signal"), str) else str(index)
        for field in sorted(PULSE_STATE_REQUIRED_FIELDS):
            if field not in item:
                errors.append(f"pulse_state consumed candidate {label} is missing {field}")
        _require_string_fields(errors, f"pulse_state consumed candidate {label}", item, PULSE_STATE_STRING_FIELDS)

        fingerprint = item.get("fingerprint")
        if isinstance(fingerprint, str):
            if fingerprint in seen_fingerprints:
                errors.append(f"duplicate pulse_state fingerprint {fingerprint}")
            else:
                seen_fingerprints.add(fingerprint)

        if "source_ids" in item:
            _require_string_list(errors, label, "source_ids", item["source_ids"])

        signal = item.get("signal")
        if isinstance(signal, str) and signal not in MISSION_PULSE_SIGNAL_TIE_BREAK_ORDER:
            allowed = ", ".join(sorted(MISSION_PULSE_SIGNAL_TIE_BREAK_ORDER))
            errors.append(
                f"pulse_state consumed candidate {label} signal unsupported: {signal!r}; expected one of: {allowed}"
            )

        next_gate = item.get("candidate_next_gate")
        if isinstance(next_gate, str) and next_gate not in MISSION_PULSE_NEXT_GATES:
            allowed = ", ".join(sorted(MISSION_PULSE_NEXT_GATES))
            errors.append(
                f"pulse_state consumed candidate {label} candidate_next_gate unsupported: {next_gate!r}; expected one of: {allowed}"
            )

        priority_class = item.get("priority_class")
        if isinstance(priority_class, str) and priority_class not in MISSION_PULSE_CANDIDATE_PRIORITIES:
            allowed = ", ".join(sorted(MISSION_PULSE_CANDIDATE_PRIORITIES))
            errors.append(
                f"pulse_state consumed candidate {label} priority_class unsupported: {priority_class!r}; expected one of: {allowed}"
            )


def _is_parent_aligned_task(task: dict[str, Any]) -> bool:
    return task.get("parent_id") is not None


def _required_task_fields(task: dict[str, Any]) -> set[str]:
    fields = set(BASE_TASK_REQUIRED_FIELDS)
    kind = task.get("kind")
    if kind == "step":
        fields.update(STEP_TASK_FIELDS)
    elif kind == "subtask" or _is_parent_aligned_task(task):
        fields.update(PARENT_ALIGNED_TASK_FIELDS)
    else:
        fields.update(MISSION_ALIGNED_TASK_FIELDS)
    return fields


def _find_parent_cycle(task_id: str, tasks_by_id: dict[str, dict[str, Any]]) -> str | None:
    path: list[str] = []
    positions: dict[str, int] = {}
    current = task_id
    while current in tasks_by_id:
        if current in positions:
            return sorted(path[positions[current] :])[0]
        positions[current] = len(path)
        path.append(current)
        parent_id = tasks_by_id[current].get("parent_id")
        if not isinstance(parent_id, str):
            return None
        current = parent_id
    return None


def validate_mission(state: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return ["mission state must be an object"]

    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    mission = state.get("mission")
    if not isinstance(mission, dict):
        errors.append("mission must be an object")
        mission = {}

    for field in sorted(MISSION_REQUIRED_FIELDS):
        if field not in mission:
            errors.append(f"mission is missing {field}")
    _require_string_fields(errors, "mission", mission, MISSION_STRING_FIELDS)

    status = mission.get("status")
    if "status" in mission:
        if not isinstance(status, str):
            errors.append("mission status must be a string")
        elif status not in MISSION_STATUSES:
            allowed = ", ".join(sorted(MISSION_STATUSES))
            errors.append(f"mission status must be one of: {allowed}")

    for field in POLICY_FIELDS:
        if field not in mission:
            continue
        value = mission[field]
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"mission {field} must be an integer")
        elif not 0 <= value <= 100:
            errors.append(f"mission {field} must be between 0 and 100")
        elif field == "human_in_loop" and value not in {0, 100}:
            errors.append("mission human_in_loop must be 0 or 100 in tplan.v0.1")

    evidence = mission.get("acceptance_evidence")
    mission_acceptance_ids: set[str] = set()
    if "acceptance_evidence" in mission:
        if not isinstance(evidence, list):
            errors.append("mission acceptance_evidence must be a list")
        else:
            seen_evidence_ids: set[str] = set()
            for index, item in enumerate(evidence, start=1):
                if not isinstance(item, dict):
                    errors.append(f"mission acceptance_evidence item {index} must be an object")
                elif "id" not in item:
                    errors.append(f"mission acceptance_evidence item {index} is missing id")
                elif not isinstance(item["id"], str):
                    errors.append(f"mission acceptance_evidence item {index} id must be a string")
                else:
                    evidence_id = item["id"]
                    if evidence_id in seen_evidence_ids:
                        errors.append(f"duplicate mission acceptance evidence id {evidence_id}")
                    else:
                        seen_evidence_ids.add(evidence_id)
                        mission_acceptance_ids.add(evidence_id)
                    if "description" in item and not isinstance(item["description"], str):
                        errors.append(f"mission acceptance_evidence {evidence_id} description must be a string")

    tasks = state.get("tasks")
    normalized_tasks: list[dict[str, Any]] = []
    if not isinstance(tasks, list):
        errors.append("tasks must be a list")
    else:
        seen_task_ids: set[str] = set()
        for index, task in enumerate(tasks, start=1):
            if not isinstance(task, dict):
                errors.append(f"task {index} must be an object")
                continue

            task_id = _task_label(index, task)
            for field in sorted(_required_task_fields(task)):
                if field not in task:
                    errors.append(f"task {task_id} is missing {field}")
            _require_string_fields(errors, f"task {task_id}", task, TASK_STRING_FIELDS)

            raw_id = task.get("id")
            if "id" in task:
                if not isinstance(raw_id, str):
                    errors.append(f"task {index} id must be a string")
                elif raw_id in seen_task_ids:
                    errors.append(f"duplicate task id {raw_id}")
                else:
                    seen_task_ids.add(raw_id)

            if "level" in task and (isinstance(task["level"], bool) or not isinstance(task["level"], int)):
                errors.append(f"task {task_id} level must be an integer")

            status = task.get("status")
            if "status" in task:
                if not isinstance(status, str):
                    errors.append(f"task {task_id} status must be a string")
                elif status not in TASK_STATUSES:
                    allowed = ", ".join(sorted(TASK_STATUSES))
                    errors.append(f"task {task_id} status must be one of: {allowed}")

            role = task.get("role")
            if "role" in task:
                if not isinstance(role, str):
                    errors.append(f"task {task_id} role must be a string")
                elif role not in TASK_ROLES:
                    allowed = ", ".join(sorted(TASK_ROLES))
                    errors.append(f"task {task_id} role must be one of: {allowed}")

            kind = task.get("kind")
            if "kind" in task:
                if not isinstance(kind, str):
                    errors.append(f"task {task_id} kind must be a string")
                elif kind not in NODE_KINDS:
                    allowed = ", ".join(sorted(NODE_KINDS))
                    errors.append(f"task {task_id} kind must be one of: {allowed}")

            if "acceptance_evidence" in task:
                _require_string_list(errors, task_id, "acceptance_evidence", task["acceptance_evidence"])
                if isinstance(task["acceptance_evidence"], list):
                    for evidence_id in task["acceptance_evidence"]:
                        if isinstance(evidence_id, str) and evidence_id not in mission_acceptance_ids:
                            errors.append(f"task {task_id} acceptance_evidence {evidence_id} does not exist")
            if "evidence_links" in task:
                _require_string_list(errors, task_id, "evidence_links", task["evidence_links"])

            normalized_tasks.append(task)

    tasks_by_id = task_map(state)
    _validate_shared_context(errors, state, tasks_by_id)
    _validate_pulse_state(errors, state)

    for task in normalized_tasks:
        task_id = _task_label(0, task)
        parent_id = task.get("parent_id")
        kind = task.get("kind")
        level = task.get("level")
        if parent_id is None:
            if kind != "task":
                errors.append(f"task {task_id} root node must be kind task")
            if level != 1:
                errors.append(f"task {task_id} task must be level 1")
            continue
        if not isinstance(parent_id, str):
            errors.append(f"task {task_id} parent_id must be a string or null")
        elif parent_id not in tasks_by_id:
            errors.append(f"task {task_id} parent_id {parent_id} does not exist")
        elif parent_id == task_id:
            errors.append(f"task {task_id} parent_id cannot reference itself")
        else:
            parent = tasks_by_id[parent_id]
            parent_kind = parent.get("kind")
            parent_level = parent.get("level")
            if parent_kind == "step":
                errors.append(f"task {task_id} parent {parent_id} cannot be a step")
            if kind == "task":
                errors.append(f"task {task_id} task nodes cannot have a parent")
            elif kind == "subtask":
                if parent_kind != "task":
                    errors.append(f"task {task_id} subtask parent must be a task")
                if level != 2:
                    errors.append(f"task {task_id} subtask must be level 2")
            elif kind == "step":
                if parent_kind not in {"task", "subtask"}:
                    errors.append(f"task {task_id} step parent must be a task or subtask")
                if isinstance(parent_level, int) and level != parent_level + 1:
                    errors.append(f"task {task_id} step level must be parent level plus 1")
                elif level not in {2, 3}:
                    errors.append(f"task {task_id} step must be level 2 or 3")

    cycle_roots: set[str] = set()
    for task_id in sorted(tasks_by_id):
        cycle_root = _find_parent_cycle(task_id, tasks_by_id)
        if cycle_root is not None and cycle_root not in cycle_roots:
            cycle_roots.add(cycle_root)
            errors.append(f"task tree contains a cycle involving {cycle_root}")

    if "active_task_id" not in state:
        errors.append("missing field: active_task_id")
    active_task_id = state.get("active_task_id")
    if "active_task_id" in state and active_task_id is not None:
        if not isinstance(active_task_id, str):
            errors.append("active_task_id must be a string or null")
        elif active_task_id not in tasks_by_id:
            errors.append(f"active_task_id {active_task_id} does not exist")

    covered_acceptance_ids: set[str] = set()
    for task in normalized_tasks:
        if task.get("role") != "success-critical" or task.get("kind") != "task":
            continue
        task_evidence = task.get("acceptance_evidence", [])
        if isinstance(task_evidence, list):
            covered_acceptance_ids.update(item for item in task_evidence if isinstance(item, str))

    for evidence_id in sorted(acceptance_ids(state)):
        if evidence_id not in covered_acceptance_ids:
            errors.append(f"acceptance evidence {evidence_id} is not covered by a success-critical task")

    return errors


def parse_acceptance_evidence(values: list[str]) -> list[dict[str, str]]:
    evidence = []
    for index, raw in enumerate(values, start=1):
        if ":" in raw:
            evidence_id, description = raw.split(":", 1)
        else:
            evidence_id, description = f"A{index}", raw
        evidence.append({"id": evidence_id.strip(), "description": description.strip()})
    return evidence


def load_task_json(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    tasks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tasks, list):
        raise TplanError("task JSON must be a list")
    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            raise TplanError(f"task {index} must be an object")
    return tasks


def require_string_list(task_id: str, name: str, value: Any) -> list[str]:
    if not isinstance(value, list):
        raise TplanError(f"task {task_id} {name} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise TplanError(f"task {task_id} {name} items must be strings")
    return list(value)


def require_task_enum(task_id: str, name: str, value: Any, allowed_values: set[str]) -> str:
    if not isinstance(value, str):
        raise TplanError(f"task {task_id} {name} must be a string")
    if value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise TplanError(f"task {task_id} {name} must be one of: {allowed}")
    return value


def require_task_level(task_id: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TplanError(f"task {task_id} level must be an integer")
    return value


def require_task_kind(task_id: str, value: Any) -> str:
    if not isinstance(value, str):
        raise TplanError(f"task {task_id} kind must be a string")
    if value not in NODE_KINDS:
        allowed = ", ".join(sorted(NODE_KINDS))
        raise TplanError(f"task {task_id} kind must be one of: {allowed}")
    return value


def _default_kind(raw: dict[str, Any]) -> str:
    return "task" if raw.get("parent_id") is None else "subtask"


def _default_level(raw: dict[str, Any], kind: str, raw_tasks_by_id: dict[str, dict[str, Any]]) -> int:
    if kind == "task":
        return 1
    if kind == "subtask":
        return 2
    parent_id = raw.get("parent_id")
    parent = raw_tasks_by_id.get(str(parent_id)) if parent_id is not None else None
    if parent is None:
        return 2
    parent_kind = parent.get("kind", _default_kind(parent))
    return 3 if parent_kind == "subtask" else 2


def normalize_task(
    raw: dict[str, Any],
    default_level: int = 1,
    raw_tasks_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if "id" not in raw:
        raise TplanError("task is missing id")
    if "title" not in raw:
        raise TplanError(f"task {raw['id']} is missing title")

    raw_tasks_by_id = raw_tasks_by_id or {}
    task_id = str(raw["id"])
    parent_id = raw.get("parent_id")
    kind = require_task_kind(task_id, raw.get("kind", _default_kind(raw)))
    default_role = "success-critical" if kind == "task" else "supporting"
    status = require_task_enum(task_id, "status", raw.get("status", "pending"), TASK_STATUSES)
    role = require_task_enum(task_id, "role", raw.get("role", default_role), TASK_ROLES)
    inferred_level = _default_level(raw, kind, raw_tasks_by_id) if "level" not in raw else default_level
    level = require_task_level(task_id, raw.get("level", inferred_level))

    task = {
        "id": task_id,
        "parent_id": parent_id,
        "kind": kind,
        "level": level,
        "title": str(raw["title"]),
        "status": status,
        "role": role,
        "evidence_links": require_string_list(task_id, "evidence_links", raw.get("evidence_links", [])),
    }
    if kind == "task":
        task["mission_contribution"] = str(raw.get("mission_contribution", ""))
        task["acceptance_evidence"] = require_string_list(
            task_id, "acceptance_evidence", raw.get("acceptance_evidence", [])
        )
    elif kind == "subtask":
        for field in sorted(PARENT_ALIGNED_TASK_FIELDS):
            if field not in raw:
                raise TplanError(f"task {task_id} is missing {field}")
            value = raw[field]
            if not isinstance(value, str):
                raise TplanError(f"task {task_id} {field} must be a string")
            task[field] = value
        if "acceptance_evidence" in raw:
            task["acceptance_evidence"] = require_string_list(task_id, "acceptance_evidence", raw["acceptance_evidence"])
        if "mission_contribution" in raw:
            if not isinstance(raw["mission_contribution"], str):
                raise TplanError(f"task {task_id} mission_contribution must be a string")
            task["mission_contribution"] = raw["mission_contribution"]
    else:
        for field in sorted(STEP_TASK_FIELDS):
            if field not in raw:
                raise TplanError(f"task {task_id} is missing {field}")
            value = raw[field]
            if not isinstance(value, str):
                raise TplanError(f"task {task_id} {field} must be a string")
            task[field] = value
    return task


def normalize_task_for_mission(mission: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    raw_tasks_by_id = task_map(mission)
    raw_tasks_by_id[str(raw.get("id"))] = raw
    return normalize_task(raw, raw_tasks_by_id=raw_tasks_by_id)


def add_task_node(mission_dir: Path, raw: dict[str, Any]) -> dict[str, Any]:
    mission = read_mission(mission_dir)
    node = normalize_task_for_mission(mission, raw)
    updated = copy.deepcopy(mission)
    updated["tasks"] = list(mission.get("tasks", [])) + [node]
    commit_mission_state(
        mission_dir,
        mission,
        updated,
        source={"kind": "runtime_script", "name": "add_node"},
        latest_state=f"Task node {node['id']} was added.",
    )
    return node


def build_mission(
    *,
    mission_id: str,
    title: str,
    objective: str,
    acceptance_evidence: list[dict[str, str]],
    human_in_loop: int,
    risk_tolerance: int,
    resource_sufficiency: int,
    tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mission": {
            "id": mission_id,
            "title": title,
            "objective": objective,
            "status": "active",
            "human_in_loop": require_policy_value("human_in_loop", human_in_loop),
            "risk_tolerance": require_policy_value("risk_tolerance", risk_tolerance),
            "resource_sufficiency": require_policy_value("resource_sufficiency", resource_sufficiency),
            "acceptance_evidence": acceptance_evidence,
        },
        "tasks": [
            normalize_task(task, raw_tasks_by_id={str(item["id"]): item for item in tasks if "id" in item})
            for task in tasks
        ],
        "active_task_id": None,
    }


def render_mission_md(mission: dict[str, Any]) -> str:
    policy = mission["mission"]
    return (
        f"# {policy['title']}\n\n"
        "## Objective\n\n"
        f"{policy['objective']}\n\n"
        "## Policy\n\n"
        f"- human_in_loop: {policy['human_in_loop']}\n"
        f"- risk_tolerance: {policy['risk_tolerance']}\n"
        f"- resource_sufficiency: {policy['resource_sufficiency']}\n\n"
        "## Decision Log\n\n"
        "No decisions recorded yet.\n"
    )


def shared_context_dir(project_root: Path) -> Path:
    return project_root / ".tplan" / "shared_contexts"


def shared_context_path(project_root: Path, mission_id: str) -> Path:
    return shared_context_dir(project_root) / f"tplan_mission_shared_context-{slugify(mission_id)}.md"


def shared_context_relative_path(mission_id: str) -> str:
    return f".tplan/shared_contexts/tplan_mission_shared_context-{slugify(mission_id)}.md"


def _mission_acceptance_evidence(mission: dict[str, Any]) -> list[dict[str, Any]]:
    mission_meta = mission.get("mission", {})
    if not isinstance(mission_meta, dict):
        return []
    evidence = mission_meta.get("acceptance_evidence", [])
    return list(evidence) if isinstance(evidence, list) else []


def render_shared_context_markdown(
    mission: dict[str, Any],
    *,
    source_contexts: list[str] | None = None,
) -> str:
    mission_meta = mission["mission"]
    shared_context = mission.get("shared_context", {})
    if not isinstance(shared_context, dict):
        shared_context = {}
    source_contexts = source_contexts if source_contexts is not None else list(shared_context.get("source_contexts", []))
    metadata = {
        "schema_version": SHARED_CONTEXT_SCHEMA_VERSION,
        "mission_id": mission_meta["id"],
        "title": mission_meta["title"],
        "objective": mission_meta["objective"],
        "status": mission_meta["status"],
        "active_task_id": mission.get("active_task_id"),
        "acceptance_evidence": _mission_acceptance_evidence(mission),
        "source_contexts": source_contexts,
        "runtime_dir": shared_context.get("runtime_dir"),
        "runtime_dir_name": shared_context.get("runtime_dir_name"),
        "risk_signals": _risk_signals(mission),
        "updated_at": now_iso(),
    }
    risk_signals = _risk_signals(mission)
    active_risks = [signal for signal in risk_signals if signal.get("status") == "active"]
    resolved_risks = [signal for signal in risk_signals if signal.get("status") != "active"]
    acceptance_lines = "\n".join(
        f"- {item.get('id')}: {item.get('description', '')}"
        for item in metadata["acceptance_evidence"]
        if isinstance(item, dict)
    )
    source_lines = "\n".join(f"- {item}" for item in source_contexts) or "- none"
    active_risk_lines = "\n".join(
        f"- {signal.get('id')}: {signal.get('signal')} ({signal.get('severity')}, {signal.get('status')})"
        for signal in active_risks
    ) or "- none"
    resolved_risk_lines = "\n".join(
        f"- {signal.get('id')}: {signal.get('signal')} ({signal.get('status')})"
        for signal in resolved_risks[-5:]
    ) or "- none"
    return (
        f"{SHARED_CONTEXT_MARKER_START}\n"
        + json.dumps(metadata, ensure_ascii=False, indent=2)
        + f"\n{SHARED_CONTEXT_MARKER_END}\n"
        + f"# TPlan Mission Shared Context: {mission_meta['id']}\n\n"
        "## Mission Snapshot\n\n"
        f"- title: {mission_meta['title']}\n"
        f"- objective: {mission_meta['objective']}\n"
        f"- status: {mission_meta['status']}\n"
        f"- active_task_id: {mission.get('active_task_id') or 'none'}\n\n"
        "### Acceptance Evidence\n\n"
        f"{acceptance_lines or '- none'}\n\n"
        "## Source Contexts\n\n"
        f"{source_lines}\n\n"
        "## Current State\n\n"
        "- latest_state: not recorded in shared context yet\n\n"
        "## Shared Risks\n\n"
        "### Active\n\n"
        f"{active_risk_lines}\n\n"
        "### Recently Resolved\n\n"
        f"{resolved_risk_lines}\n\n"
        "## Key Findings\n\n"
        "- none recorded yet\n\n"
        "## Resume Notes\n\n"
        "- Load this file before starting or resuming the Mission.\n"
    )


def parse_shared_context_metadata(text: str) -> dict[str, Any]:
    start = text.find(SHARED_CONTEXT_MARKER_START)
    if start == -1:
        return {}
    json_start = start + len(SHARED_CONTEXT_MARKER_START)
    end = text.find(SHARED_CONTEXT_MARKER_END, json_start)
    if end == -1:
        return {}
    raw = text[json_start:end].strip()
    if not raw:
        return {}
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def read_shared_context_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return parse_shared_context_metadata(path.read_text(encoding="utf-8"))


def _acceptance_fingerprint(evidence: list[dict[str, Any]]) -> list[tuple[str, str]]:
    fingerprint: list[tuple[str, str]] = []
    for item in evidence:
        if isinstance(item, dict):
            fingerprint.append((str(item.get("id", "")), str(item.get("description", ""))))
    return fingerprint


def _shared_context_candidate(path: Path) -> dict[str, Any]:
    metadata = read_shared_context_metadata(path)
    return {
        "mission_id": metadata.get("mission_id") or path.stem.removeprefix("tplan_mission_shared_context-"),
        "title": metadata.get("title"),
        "objective": metadata.get("objective"),
        "status": metadata.get("status"),
        "context_file": str(path),
    }


def build_mission_preflight(
    project_root: Path,
    *,
    mission_id: str | None,
    objective: str | None = None,
    acceptance_evidence: list[dict[str, Any]] | None = None,
    mission_dir: Path | None = None,
) -> dict[str, Any]:
    context_dir = shared_context_dir(project_root)
    if mission_id is None:
        candidates = []
        if context_dir.exists():
            candidates = [
                _shared_context_candidate(path)
                for path in sorted(context_dir.glob("tplan_mission_shared_context-*.md"))
            ]
        return {
            "action": "needs_agentic_selection" if candidates else "create_new",
            "mission_id": None,
            "context_file": None,
            "candidates": candidates,
            "conflicts": [],
        }

    path = shared_context_path(project_root, mission_id)
    requested_runtime_dir = runtime_dir_identity(project_root, mission_dir) if mission_dir is not None else None
    requested_runtime_dir_name = mission_dir.name if mission_dir is not None else None
    discovered_runtime_dirs = find_project_runtime_dirs(project_root, mission_id) if requested_runtime_dir is not None else []
    if not path.exists():
        conflicts = []
        if discovered_runtime_dirs and requested_runtime_dir not in discovered_runtime_dirs:
            conflicts.append("runtime_dir")
        conflicts = list(dict.fromkeys(conflicts))
        return {
            "action": "needs_agentic_selection" if conflicts else "create_new",
            "mission_id": mission_id,
            "context_file": str(path),
            "loaded_context": None,
            "runtime_dirs": discovered_runtime_dirs,
            "conflicts": conflicts,
        }

    metadata = read_shared_context_metadata(path)
    conflicts: list[str] = []
    if metadata.get("mission_id") not in {None, mission_id}:
        conflicts.append("mission_id")
    if objective is not None and metadata.get("objective") not in {None, objective}:
        conflicts.append("objective")
    if acceptance_evidence is not None:
        existing = metadata.get("acceptance_evidence")
        if isinstance(existing, list) and _acceptance_fingerprint(existing) != _acceptance_fingerprint(acceptance_evidence):
            conflicts.append("acceptance_evidence")
    existing_runtime_dir = metadata.get("runtime_dir")
    existing_runtime_dir_name = metadata.get("runtime_dir_name")
    if requested_runtime_dir is not None:
        if isinstance(existing_runtime_dir, str) and existing_runtime_dir != requested_runtime_dir:
            conflicts.append("runtime_dir")
        elif isinstance(existing_runtime_dir_name, str) and existing_runtime_dir_name != requested_runtime_dir_name:
            conflicts.append("runtime_dir")
        elif discovered_runtime_dirs and any(item != requested_runtime_dir for item in discovered_runtime_dirs):
            conflicts.append("runtime_dir")
    conflicts = list(dict.fromkeys(conflicts))
    return {
        "action": "needs_agentic_selection" if conflicts else "continue_existing",
        "mission_id": mission_id,
        "context_file": str(path),
        "loaded_context": metadata,
        "runtime_dirs": discovered_runtime_dirs or [item for item in (existing_runtime_dir,) if isinstance(item, str)],
        "conflicts": conflicts,
    }


def attach_project_shared_context(
    mission: dict[str, Any],
    project_root: Path,
    *,
    mission_dir: Path | None = None,
    source_contexts: list[str] | None = None,
) -> dict[str, Any]:
    mission_meta = mission["mission"]
    preflight = build_mission_preflight(
        project_root,
        mission_id=mission_meta["id"],
        objective=mission_meta["objective"],
        acceptance_evidence=_mission_acceptance_evidence(mission),
        mission_dir=mission_dir,
    )
    if preflight.get("conflicts"):
        conflicts = ", ".join(preflight["conflicts"])
        raise TplanError(f"shared context preflight conflict: {conflicts}")

    loaded_context = preflight.get("loaded_context")
    loaded_sources = []
    if isinstance(loaded_context, dict) and isinstance(loaded_context.get("source_contexts"), list):
        loaded_sources = [str(item) for item in loaded_context["source_contexts"]]
    loaded_risk_signals = []
    if isinstance(loaded_context, dict) and isinstance(loaded_context.get("risk_signals"), list):
        loaded_risk_signals = [item for item in loaded_context["risk_signals"] if isinstance(item, dict)]
    active_sources = source_contexts if source_contexts is not None else loaded_sources
    current = mission.get("shared_context")
    if not isinstance(current, dict):
        current = {}
    risk_signals = current.get("risk_signals")
    if not isinstance(risk_signals, list):
        risk_signals = loaded_risk_signals
    runtime_dir = current.get("runtime_dir")
    runtime_dir_name = current.get("runtime_dir_name")
    if mission_dir is not None:
        runtime_dir = runtime_dir_identity(project_root, mission_dir)
        runtime_dir_name = mission_dir.name
    elif isinstance(loaded_context, dict):
        if not isinstance(runtime_dir, str):
            runtime_dir = loaded_context.get("runtime_dir")
        if not isinstance(runtime_dir_name, str):
            runtime_dir_name = loaded_context.get("runtime_dir_name")
    mission["shared_context"] = {
        **current,
        "project_root": str(project_root),
        "context_file": shared_context_relative_path(mission_meta["id"]),
        "source_contexts": active_sources,
        "risk_signals": risk_signals,
        "runtime_dir": runtime_dir,
        "runtime_dir_name": runtime_dir_name,
    }
    return preflight


def write_project_shared_context(project_root: Path, mission: dict[str, Any]) -> Path | None:
    shared_context = mission.get("shared_context")
    if not isinstance(shared_context, dict):
        return None
    context_file = shared_context.get("context_file")
    if not isinstance(context_file, str) or not context_file:
        return None
    path = project_root / context_file
    path.parent.mkdir(parents=True, exist_ok=True)
    source_contexts = shared_context.get("source_contexts")
    if not isinstance(source_contexts, list):
        source_contexts = []
    path.write_text(
        render_shared_context_markdown(mission, source_contexts=[str(item) for item in source_contexts]),
        encoding="utf-8",
    )
    return path


def require_indexed_shared_context_target(mission: dict[str, Any]) -> bool:
    shared_context = mission.get("shared_context")
    if not isinstance(shared_context, dict):
        return False
    indexed_keys = {"project_root", "context_file", "source_contexts", "runtime_dir", "runtime_dir_name"}
    if not any(key in shared_context for key in indexed_keys):
        return False
    project_root = shared_context.get("project_root")
    context_file = shared_context.get("context_file")
    if not isinstance(project_root, str) or not project_root:
        raise TplanError("shared_context propagation configured without project_root")
    if not isinstance(context_file, str) or not context_file:
        raise TplanError("shared_context propagation configured without context_file")
    return True


def write_indexed_shared_context(mission: dict[str, Any]) -> Path | None:
    if not require_indexed_shared_context_target(mission):
        return None
    shared_context = mission["shared_context"]
    project_root = shared_context.get("project_root")
    return write_project_shared_context(Path(project_root), mission)


def _read_events_unlocked(mission_dir: Path) -> list[dict[str, Any]]:
    path = mission_paths(mission_dir)["evidence"]
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def read_events(mission_dir: Path) -> list[dict[str, Any]]:
    if not mission_dir.exists():
        return []
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        return _read_events_unlocked(mission_dir)


def prepare_event(mission_dir: Path, event: dict[str, Any]) -> dict[str, Any]:
    event = dict(event)
    event.setdefault("id", _next_event_id(mission_dir))
    event.setdefault("timestamp", now_iso())
    event.setdefault("task_id", None)
    event.setdefault("payload", {})
    return event


def append_event(mission_dir: Path, event: dict[str, Any]) -> dict[str, Any]:
    path = mission_paths(mission_dir)["evidence"]
    event = prepare_event(mission_dir, event)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def _read_execution_trace_unlocked(mission_dir: Path) -> list[dict[str, Any]]:
    path = mission_paths(mission_dir)["trace"]
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TplanError(f"execution trace line {line_number} is invalid JSON: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise TplanError(f"execution trace line {line_number} must be an object")
        records.append(record)
    return records


def read_execution_trace(mission_dir: Path) -> list[dict[str, Any]]:
    if not mission_dir.exists():
        return []
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        return _read_execution_trace_unlocked(mission_dir)


def _trace_mission_id(mission: dict[str, Any]) -> str:
    mission_meta = mission.get("mission")
    mission_id = mission_meta.get("id") if isinstance(mission_meta, dict) else None
    if not isinstance(mission_id, str) or not mission_id:
        raise TplanError("mission id is required for execution tracing")
    return mission_id


def _parse_trace_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise TplanError(f"execution trace {field} must be a non-empty ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise TplanError(f"execution trace {field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise TplanError(f"execution trace {field} must include a timezone")
    return parsed


def _trace_forbidden_path(value: Any, path: str = "record") -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            next_path = f"{path}.{key}"
            if normalized in TRACE_FORBIDDEN_KEYS:
                return next_path
            forbidden = _trace_forbidden_path(item, next_path)
            if forbidden:
                return forbidden
    elif isinstance(value, list):
        for index, item in enumerate(value):
            forbidden = _trace_forbidden_path(item, f"{path}[{index}]")
            if forbidden:
                return forbidden
    return None


def _require_trace_string(errors: list[str], data: dict[str, Any], field: str, label: str) -> str | None:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        errors.append(f"{label} {field} must be a non-empty string")
        return None
    return value


def _valid_safe_trace_text(value: Any, *, limit: int) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit and "\n" not in value and "\r" not in value


def _safe_trace_summary(value: Any, *, limit: int) -> str:
    summary = re.sub(r"\s+", " ", str(value or "")).strip()
    return summary if len(summary) <= limit else summary[: limit - 1].rstrip() + "…"


def _valid_trace_refs(values: Any) -> bool:
    return isinstance(values, list) and all(
        _valid_safe_trace_text(item, limit=500) for item in values
    )


def _validate_lifecycle_payload(
    errors: list[str],
    mission: dict[str, Any],
    event_type: str,
    payload: dict[str, Any],
) -> None:
    allowed = TRACE_LIFECYCLE_PAYLOAD_FIELDS.get(event_type, set())
    unsupported = sorted(set(payload) - allowed)
    if unsupported:
        errors.append(f"execution trace {event_type} payload fields unsupported: {', '.join(unsupported)}")
    tasks = task_map(mission)
    if event_type == "mission_initialized":
        if payload.get("mission_status") not in MISSION_STATUSES:
            errors.append("execution trace mission_initialized mission_status unsupported")
        active_task_id = payload.get("active_task_id")
        if active_task_id is not None and active_task_id not in tasks:
            errors.append("execution trace mission_initialized active_task_id must reference a task or be null")
        snapshots = payload.get("tasks")
        if not isinstance(snapshots, list):
            errors.append("execution trace mission_initialized tasks must be a list")
        else:
            for snapshot in snapshots:
                if not isinstance(snapshot, dict) or set(snapshot) != {"id", "parent_id", "kind", "status", "title"}:
                    errors.append("execution trace mission_initialized task snapshots have invalid shape")
                    continue
                if snapshot.get("id") not in tasks:
                    errors.append("execution trace mission_initialized task snapshot must reference a task")
                if snapshot.get("kind") not in NODE_KINDS or snapshot.get("status") not in TASK_STATUSES:
                    errors.append("execution trace mission_initialized task snapshot kind/status unsupported")
                if not _valid_safe_trace_text(snapshot.get("title"), limit=240):
                    errors.append("execution trace mission_initialized task title must be a safe single-line summary")
    elif event_type == "node_added":
        if payload.get("parent_id") is not None and payload.get("parent_id") not in tasks:
            errors.append("execution trace node_added parent_id must reference a task or be null")
        if payload.get("kind") not in NODE_KINDS or payload.get("status") not in TASK_STATUSES:
            errors.append("execution trace node_added kind/status unsupported")
        if not _valid_safe_trace_text(payload.get("title"), limit=240):
            errors.append("execution trace node_added title must be a safe single-line summary")
        if payload.get("dynamic") is not True:
            errors.append("execution trace node_added dynamic must be true")
    elif event_type == "task_status_changed":
        if payload.get("from_status") not in TASK_STATUSES or payload.get("to_status") not in TASK_STATUSES:
            errors.append("execution trace task_status_changed from_status/to_status unsupported")
        if "outcome_summary" in payload and not _valid_safe_trace_text(payload["outcome_summary"], limit=500):
            errors.append("execution trace outcome_summary must be a safe single-line summary of at most 500 characters")
        if "artifact_refs" in payload and not _valid_trace_refs(payload["artifact_refs"]):
            errors.append("execution trace task_status_changed artifact_refs must be safe references")
    elif event_type == "active_node_changed":
        for field in ("from_task_id", "to_task_id"):
            value = payload.get(field)
            if value is not None and value not in tasks:
                errors.append(f"execution trace active_node_changed {field} must reference a task or be null")
    elif event_type == "mission_status_changed":
        if payload.get("from_status") not in MISSION_STATUSES or payload.get("to_status") not in MISSION_STATUSES:
            errors.append("execution trace mission_status_changed from_status/to_status unsupported")


def validate_execution_trace_record(mission: dict[str, Any], record: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["execution trace record must be an object"]

    forbidden = _trace_forbidden_path(record)
    if forbidden:
        errors.append(f"execution trace contains forbidden raw-content field: {forbidden}")

    if record.get("schema_version") != EXECUTION_TRACE_SCHEMA_VERSION:
        errors.append(f"execution trace schema_version must be {EXECUTION_TRACE_SCHEMA_VERSION}")
    _require_trace_string(errors, record, "event_id", "execution trace")
    event_type = _require_trace_string(errors, record, "event_type", "execution trace")
    if event_type is not None and event_type not in TRACE_EVENT_TYPES:
        errors.append(f"execution trace event_type unsupported: {event_type}")
    try:
        _parse_trace_timestamp(record.get("timestamp"), "timestamp")
    except TplanError as exc:
        errors.append(str(exc))

    mission_id = record.get("mission_id")
    expected_mission_id = _trace_mission_id(mission)
    if mission_id != expected_mission_id:
        errors.append(f"execution trace mission_id must be {expected_mission_id}")

    task_id = record.get("task_id")
    tasks = task_map(mission)
    if task_id is not None:
        if not isinstance(task_id, str) or not task_id:
            errors.append("execution trace task_id must be a non-empty string or null")
        elif task_id not in tasks:
            errors.append(f"execution trace task_id {task_id} does not exist")

    if event_type == "span_completed":
        event_fields = {"span", "usage", "usage_source", "metadata"}
    elif event_type == "span_started":
        event_fields = {"span", "metadata"}
    else:
        event_fields = {"payload", "source", "commit_id"}
    allowed_record_fields = TRACE_COMMON_RECORD_FIELDS | event_fields
    unsupported_record_fields = sorted(set(record) - allowed_record_fields)
    if unsupported_record_fields:
        errors.append(f"execution trace record fields unsupported: {', '.join(unsupported_record_fields)}")

    refs = record.get("refs", {})
    if not isinstance(refs, dict):
        errors.append("execution trace refs must be an object")
    else:
        unsupported_refs = sorted(set(refs) - TRACE_REF_FIELDS)
        if unsupported_refs:
            errors.append(f"execution trace refs fields unsupported: {', '.join(unsupported_refs)}")
        for field, values in refs.items():
            if not _valid_trace_refs(values):
                errors.append(f"execution trace refs {field} must be a list of safe single-line references")
    if event_type not in TRACE_SPAN_EVENT_TYPES:
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            errors.append("execution trace payload must be an object")
        elif isinstance(event_type, str):
            _validate_lifecycle_payload(errors, mission, event_type, payload)
        source_record = record.get("source", {})
        if not isinstance(source_record, dict):
            errors.append("execution trace source must be an object")
        elif set(source_record) != {"kind", "name"}:
            errors.append("execution trace source requires only kind and name")
        elif not all(_valid_safe_trace_text(value, limit=160) for value in source_record.values()):
            errors.append("execution trace source values must be safe single-line strings")
        commit_id = record.get("commit_id")
        if event_type != "mission_initialized" and not _valid_safe_trace_text(commit_id, limit=80):
            errors.append(f"execution trace {event_type} requires commit_id")
        return errors

    span = record.get("span")
    if not isinstance(span, dict):
        errors.append("execution trace span must be an object")
        return errors

    allowed_span_fields = TRACE_SPAN_START_FIELDS if event_type == "span_started" else TRACE_SPAN_FIELDS
    unsupported_span_fields = sorted(set(span) - allowed_span_fields)
    if unsupported_span_fields:
        errors.append(f"execution trace span fields unsupported: {', '.join(unsupported_span_fields)}")

    _require_trace_string(errors, span, "span_id", "execution trace span")
    label = span.get("label")
    if label is not None and not _valid_safe_trace_text(label, limit=160):
        errors.append("execution trace span label must be a non-empty single-line string of at most 160 characters")
    kind = _require_trace_string(errors, span, "kind", "execution trace span")
    if kind is not None and kind not in TRACE_SPAN_KINDS:
        errors.append(f"execution trace span kind unsupported: {kind}")
    source = _require_trace_string(errors, span, "measurement_source", "execution trace span")
    if source is not None and source not in TRACE_MEASUREMENT_SOURCES:
        errors.append(f"execution trace span measurement_source unsupported: {source}")
    attribution = _require_trace_string(errors, span, "attribution", "execution trace span")
    if attribution is not None and attribution not in TRACE_ATTRIBUTIONS:
        errors.append(f"execution trace span attribution unsupported: {attribution}")

    attempt = span.get("attempt")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        errors.append("execution trace span attempt must be a positive integer")
    parent_span_id = span.get("parent_span_id")
    if parent_span_id is not None and (not isinstance(parent_span_id, str) or not parent_span_id):
        errors.append("execution trace span parent_span_id must be a non-empty string or null")

    if attribution == "exact" and task_id is None:
        errors.append("execution trace exact attribution requires task_id")
    if attribution == "shared":
        shared_task_ids = span.get("shared_task_ids")
        if (
            not isinstance(shared_task_ids, list)
            or not all(isinstance(item, str) for item in shared_task_ids)
            or len(set(shared_task_ids)) < 2
        ):
            errors.append("execution trace shared attribution requires at least two distinct shared_task_ids")
        elif not all(isinstance(item, str) and item in tasks for item in shared_task_ids):
            errors.append("execution trace shared_task_ids must reference existing tasks")
        if task_id is not None:
            errors.append("execution trace shared attribution uses shared_task_ids and requires task_id null")
    elif "shared_task_ids" in span:
        errors.append("execution trace shared_task_ids is allowed only for shared attribution")
    if attribution in {"mission_overhead", "unattributed"} and task_id is not None:
        errors.append(f"execution trace {attribution} attribution requires task_id null")

    metadata = record.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("execution trace metadata must be an object")
    else:
        unsupported_metadata = sorted(set(metadata) - TRACE_METADATA_FIELDS)
        if unsupported_metadata:
            errors.append(f"execution trace metadata fields unsupported: {', '.join(unsupported_metadata)}")
        for field, value in metadata.items():
            if not isinstance(value, (str, int, bool)) or isinstance(value, float):
                errors.append(f"execution trace metadata {field} must be a string, integer, or boolean")
            elif isinstance(value, str) and not _valid_safe_trace_text(value, limit=160):
                errors.append(f"execution trace metadata {field} must be a safe single-line string")

    if event_type == "span_started":
        return errors

    status = _require_trace_string(errors, span, "status", "execution trace span")
    if status is not None and status not in TRACE_SPAN_STATUSES:
        errors.append(f"execution trace span status unsupported: {status}")
    try:
        started_at = _parse_trace_timestamp(span.get("started_at"), "span.started_at")
        finished_at = _parse_trace_timestamp(span.get("finished_at"), "span.finished_at")
        if finished_at < started_at:
            errors.append("execution trace span finished_at must not precede started_at")
    except TplanError as exc:
        errors.append(str(exc))

    duration_ms = span.get("duration_ms")
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, int) or duration_ms < 0:
        errors.append("execution trace span duration_ms must be a non-negative integer")
    if source == "unavailable" and duration_ms != 0:
        errors.append("execution trace unavailable duration measurement must use duration_ms 0")

    usage = record.get("usage", {})
    if not isinstance(usage, dict):
        errors.append("execution trace usage must be an object")
    else:
        unknown_usage = sorted(set(usage) - TRACE_USAGE_FIELDS)
        if unknown_usage:
            errors.append(f"execution trace usage fields unsupported: {', '.join(unknown_usage)}")
        for field, value in usage.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"execution trace usage {field} must be a non-negative integer")
        input_tokens = usage.get("input_tokens")
        cached_tokens = usage.get("cached_input_tokens")
        if isinstance(input_tokens, int) and isinstance(cached_tokens, int) and cached_tokens > input_tokens:
            errors.append("execution trace cached_input_tokens must not exceed input_tokens")
    usage_source = record.get("usage_source")
    if usage_source is not None and usage_source not in TRACE_MEASUREMENT_SOURCES:
        errors.append("execution trace usage_source unsupported")
    if isinstance(usage, dict) and usage and usage_source is None:
        errors.append("execution trace non-empty usage requires usage_source")
    return errors


def validate_execution_trace(mission: dict[str, Any], records: Any) -> list[str]:
    if not isinstance(records, list):
        return ["execution trace must be a list of records"]
    errors: list[str] = []
    event_ids: set[str] = set()
    span_events: dict[str, dict[str, tuple[int, dict[str, Any]]]] = {}

    def validate_span_pair(
        span_id: str,
        started_line: int,
        started_record: dict[str, Any],
        completed_line: int,
        completed_record: dict[str, Any],
    ) -> None:
        if started_line >= completed_line:
            errors.append(
                f"execution trace line {started_line}: span_started must precede span_completed for {span_id}"
            )
        started_span = started_record.get("span", {})
        completed_span = completed_record.get("span", {})
        for field in (
            "kind",
            "label",
            "measurement_source",
            "attribution",
            "attempt",
            "parent_span_id",
            "shared_task_ids",
        ):
            if started_span.get(field) != completed_span.get(field):
                errors.append(
                    f"execution trace line {completed_line}: span_started/span_completed {field} mismatch for {span_id}"
                )
        if started_record.get("task_id") != completed_record.get("task_id"):
            errors.append(
                f"execution trace line {completed_line}: span_started/span_completed task_id mismatch for {span_id}"
            )
        started_metadata = started_record.get("metadata", {})
        completed_metadata = completed_record.get("metadata", {})
        if isinstance(started_metadata, dict) and isinstance(completed_metadata, dict):
            for field in set(started_metadata) & set(completed_metadata):
                if started_metadata[field] != completed_metadata[field]:
                    errors.append(
                        f"execution trace line {completed_line}: span_started/span_completed metadata.{field} mismatch for {span_id}"
                    )
        try:
            start_marker = _parse_trace_timestamp(started_record.get("timestamp"), "timestamp")
            measured_start = _parse_trace_timestamp(completed_span.get("started_at"), "span.started_at")
            if measured_start < start_marker:
                errors.append(
                    f"execution trace line {completed_line}: measured span start precedes span_started marker for {span_id}"
                )
        except TplanError:
            pass

    for index, record in enumerate(records, start=1):
        for error in validate_execution_trace_record(mission, record):
            errors.append(f"execution trace line {index}: {error}")
        if not isinstance(record, dict):
            continue
        event_id = record.get("event_id")
        if isinstance(event_id, str):
            if event_id in event_ids:
                errors.append(f"execution trace line {index}: duplicate event_id {event_id}")
            event_ids.add(event_id)
        event_type = record.get("event_type")
        span = record.get("span")
        span_id = span.get("span_id") if isinstance(span, dict) else None
        if isinstance(span_id, str) and event_type in TRACE_SPAN_EVENT_TYPES:
            events = span_events.setdefault(span_id, {})
            if event_type in events:
                errors.append(f"execution trace line {index}: duplicate {event_type} for span_id {span_id}")
                continue
            events[event_type] = (index, record)
            if "span_started" in events and "span_completed" in events:
                started_line, started_record = events["span_started"]
                completed_line, completed_record = events["span_completed"]
                validate_span_pair(
                    span_id,
                    started_line,
                    started_record,
                    completed_line,
                    completed_record,
                )
    return errors


def _new_trace_record(
    mission: dict[str, Any],
    event_type: str,
    *,
    task_id: str | None = None,
    timestamp: str | None = None,
    payload: dict[str, Any] | None = None,
    refs: dict[str, Any] | None = None,
    source: dict[str, Any] | None = None,
    commit_id: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": EXECUTION_TRACE_SCHEMA_VERSION,
        "event_id": f"X{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "timestamp": timestamp or now_iso(),
        "mission_id": _trace_mission_id(mission),
        "task_id": task_id,
        "payload": payload or {},
        "refs": refs or {},
    }
    if source:
        record["source"] = source
    if commit_id:
        record["commit_id"] = commit_id
    return record


def _append_execution_trace_record_unlocked(mission_dir: Path, record: dict[str, Any]) -> dict[str, Any]:
    mission = _read_mission_unlocked(mission_dir)
    normalized = dict(record)
    normalized.setdefault("schema_version", EXECUTION_TRACE_SCHEMA_VERSION)
    normalized.setdefault("event_id", f"X{uuid.uuid4().hex[:12]}")
    normalized.setdefault("timestamp", now_iso())
    normalized.setdefault("mission_id", _trace_mission_id(mission))
    normalized.setdefault("task_id", None)
    normalized.setdefault("refs", {})
    if normalized.get("event_type") not in TRACE_SPAN_EVENT_TYPES:
        normalized.setdefault("payload", {})
    errors = validate_execution_trace_record(mission, normalized)
    if errors:
        raise TplanError("; ".join(errors))

    existing = _read_execution_trace_unlocked(mission_dir)
    event_id = normalized["event_id"]
    if any(item.get("event_id") == event_id for item in existing):
        raise TplanError(f"execution trace event_id already exists: {event_id}")
    span_id = normalized.get("span", {}).get("span_id")
    trace_errors = validate_execution_trace(mission, [*existing, normalized])
    if trace_errors:
        raise TplanError("; ".join(trace_errors))
    initialized = next((item for item in existing if item.get("event_type") == "mission_initialized"), None)
    if span_id and initialized is not None:
        observed_at = (
            _parse_trace_timestamp(normalized["span"]["finished_at"], "span.finished_at")
            if normalized.get("event_type") == "span_completed"
            else _parse_trace_timestamp(normalized["timestamp"], "timestamp")
        )
        mission_started = _parse_trace_timestamp(initialized["timestamp"], "mission_initialized.timestamp")
        if observed_at < mission_started:
            raise TplanError("execution trace span event must not precede Mission initialization")

    path = mission_paths(mission_dir)["trace"]
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    if previous and not previous.endswith("\n"):
        previous += "\n"
    write_text_atomic(path, previous + json.dumps(normalized, ensure_ascii=False) + "\n")
    return normalized


def append_execution_trace_record(mission_dir: Path, record: dict[str, Any]) -> dict[str, Any]:
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        return _append_execution_trace_record_unlocked(mission_dir, record)


def _initialize_execution_trace_unlocked(
    mission_dir: Path, mission: dict[str, Any], *, timestamp: str | None = None
) -> dict[str, Any]:
    path = mission_paths(mission_dir)["trace"]
    if path.exists() and path.read_text(encoding="utf-8").strip():
        raise TplanError(f"execution trace already exists: {path}")
    tasks = [
        {
            "id": task.get("id"),
            "parent_id": task.get("parent_id"),
            "kind": task.get("kind"),
            "status": task.get("status"),
            "title": _safe_trace_summary(task.get("title"), limit=240),
        }
        for task in mission.get("tasks", [])
        if isinstance(task, dict)
    ]
    record = _new_trace_record(
        mission,
        "mission_initialized",
        task_id=mission.get("active_task_id"),
        timestamp=timestamp,
        payload={
            "mission_status": mission.get("mission", {}).get("status"),
            "active_task_id": mission.get("active_task_id"),
            "tasks": tasks,
        },
        source={"kind": "runtime", "name": "mission_initialization"},
    )
    errors = validate_execution_trace_record(mission, record)
    if errors:
        raise TplanError("; ".join(errors))
    write_text_atomic(path, json.dumps(record, ensure_ascii=False) + "\n")
    return record


def initialize_execution_trace(mission_dir: Path, mission: dict[str, Any], *, timestamp: str | None = None) -> dict[str, Any]:
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        return _initialize_execution_trace_unlocked(mission_dir, mission, timestamp=timestamp)


def _state_change_trace_records(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    source: dict[str, Any],
    refs: dict[str, Any] | None = None,
    task_details: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    timestamp = now_iso()
    commit_id = f"C{uuid.uuid4().hex[:12]}"
    records: list[dict[str, Any]] = []
    before_tasks = task_map(before)
    after_tasks = task_map(after)
    task_details = task_details or {}

    for task_id in sorted(set(after_tasks) - set(before_tasks)):
        task = after_tasks[task_id]
        records.append(
            _new_trace_record(
                after,
                "node_added",
                task_id=task_id,
                timestamp=timestamp,
                payload={
                    "parent_id": task.get("parent_id"),
                    "kind": task.get("kind"),
                    "status": task.get("status"),
                    "title": _safe_trace_summary(task.get("title"), limit=240),
                    "dynamic": True,
                },
                refs=refs,
                source=source,
                commit_id=commit_id,
            )
        )

    for task_id in sorted(set(before_tasks) & set(after_tasks)):
        previous_status = before_tasks[task_id].get("status")
        next_status = after_tasks[task_id].get("status")
        if previous_status == next_status:
            continue
        payload = {"from_status": previous_status, "to_status": next_status}
        payload.update(task_details.get(task_id, {}))
        records.append(
            _new_trace_record(
                after,
                "task_status_changed",
                task_id=task_id,
                timestamp=timestamp,
                payload=payload,
                refs=refs,
                source=source,
                commit_id=commit_id,
            )
        )

    previous_active = before.get("active_task_id")
    next_active = after.get("active_task_id")
    if previous_active != next_active:
        records.append(
            _new_trace_record(
                after,
                "active_node_changed",
                task_id=next_active,
                timestamp=timestamp,
                payload={"from_task_id": previous_active, "to_task_id": next_active},
                refs=refs,
                source=source,
                commit_id=commit_id,
            )
        )

    previous_mission_status = before.get("mission", {}).get("status")
    next_mission_status = after.get("mission", {}).get("status")
    if previous_mission_status != next_mission_status:
        records.append(
            _new_trace_record(
                after,
                "mission_status_changed",
                timestamp=timestamp,
                payload={"from_status": previous_mission_status, "to_status": next_mission_status},
                refs=refs,
                source=source,
                commit_id=commit_id,
            )
        )
    return records


def _commit_mission_state_unlocked(
    mission_dir: Path,
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    source: dict[str, Any],
    refs: dict[str, Any] | None = None,
    task_details: dict[str, dict[str, Any]] | None = None,
    latest_state: str | None = None,
    prepared_evidence_events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    current = _read_mission_unlocked(mission_dir)
    if current != before:
        raise TplanError("Mission state changed concurrently; reload and retry the mutation")
    errors = validate_mission(after)
    if errors:
        raise TplanError("; ".join(errors))
    records = _state_change_trace_records(
        before,
        after,
        source=source,
        refs=refs,
        task_details=task_details,
    )
    for record in records:
        errors = validate_execution_trace_record(after, record)
        if errors:
            raise TplanError("; ".join(errors))

    paths = mission_paths(mission_dir)
    previous_trace = paths["trace"].read_text(encoding="utf-8") if paths["trace"].exists() else ""
    next_trace = previous_trace
    if next_trace and not next_trace.endswith("\n"):
        next_trace += "\n"
    next_trace += "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)

    evidence_text: str | None = None
    if prepared_evidence_events:
        evidence_text = paths["evidence"].read_text(encoding="utf-8") if paths["evidence"].exists() else ""
        if evidence_text and not evidence_text.endswith("\n"):
            evidence_text += "\n"
        evidence_text += "".join(
            json.dumps(event, ensure_ascii=False) + "\n" for event in prepared_evidence_events
        )

    transaction = {
        "schema_version": MISSION_TRANSACTION_SCHEMA_VERSION,
        "transaction_id": f"TX{uuid.uuid4().hex[:12]}",
        "prepared_at": now_iso(),
        "mission": after,
        "trace_text": next_trace,
        "evidence_text": evidence_text,
        "latest_state": latest_state,
    }
    write_json(paths["transaction"], transaction, durable=True)
    _recover_pending_mission_transaction_unlocked(mission_dir)
    return records


def commit_mission_state(
    mission_dir: Path,
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    source: dict[str, Any],
    refs: dict[str, Any] | None = None,
    task_details: dict[str, dict[str, Any]] | None = None,
    latest_state: str | None = None,
    prepared_evidence_events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        return _commit_mission_state_unlocked(
            mission_dir,
            before,
            after,
            source=source,
            refs=refs,
            task_details=task_details,
            latest_state=latest_state,
            prepared_evidence_events=prepared_evidence_events,
        )


def transition_task_status(
    mission_dir: Path,
    task_id: str,
    status: str,
    *,
    outcome_summary: str | None = None,
    evidence_refs: list[str] | None = None,
    artifact_refs: list[str] | None = None,
    source_name: str = "transition_task",
) -> dict[str, Any]:
    before = read_mission(mission_dir)
    after = copy.deepcopy(before)
    set_task_status(after, task_id, status)
    details: dict[str, Any] = {}
    if outcome_summary:
        details["outcome_summary"] = outcome_summary
    if artifact_refs:
        details["artifact_refs"] = artifact_refs
    refs = {"evidence_ids": evidence_refs or [], "artifact_refs": artifact_refs or []}
    commit_mission_state(
        mission_dir,
        before,
        after,
        source={"kind": "runtime_script", "name": source_name},
        refs=refs,
        task_details={task_id: details},
        latest_state=f"Task {task_id} transitioned to {status}.",
    )
    return after


def start_execution_span(mission_dir: Path, raw: Any) -> dict[str, Any]:
    """Persist a sanitized host-entry marker before an observed operation begins."""
    if not isinstance(raw, dict):
        raise TplanError("execution span start input must be an object")
    mission = read_mission(mission_dir)
    span = dict(raw.get("span", {})) if isinstance(raw.get("span"), dict) else raw.get("span")
    if isinstance(span, dict):
        span.setdefault("span_id", f"SP{uuid.uuid4().hex[:12]}")
        span.setdefault("parent_span_id", None)
        span.setdefault("attempt", 1)
    record = {
        "schema_version": EXECUTION_TRACE_SCHEMA_VERSION,
        "event_id": f"X{uuid.uuid4().hex[:12]}",
        "event_type": "span_started",
        "timestamp": raw.get("timestamp") or now_iso(),
        "mission_id": _trace_mission_id(mission),
        "task_id": raw.get("task_id"),
        "span": span,
        "refs": raw.get("refs", {}),
    }
    if "metadata" in raw:
        record["metadata"] = raw["metadata"]
    return append_execution_trace_record(mission_dir, record)


def record_execution_span(mission_dir: Path, raw: Any) -> dict[str, Any]:
    """Persist a completed span, either standalone or paired with span_started."""
    if not isinstance(raw, dict):
        raise TplanError("execution span input must be an object")
    mission = read_mission(mission_dir)
    span = dict(raw.get("span", {})) if isinstance(raw.get("span"), dict) else raw.get("span")
    started_record: dict[str, Any] | None = None
    if isinstance(span, dict):
        span.setdefault("span_id", f"SP{uuid.uuid4().hex[:12]}")
        started_record = next(
            (
                record
                for record in read_execution_trace(mission_dir)
                if record.get("event_type") == "span_started"
                and record.get("span", {}).get("span_id") == span["span_id"]
            ),
            None,
        )
        if started_record is not None:
            for field, value in started_record["span"].items():
                span.setdefault(field, value)
        span.setdefault("parent_span_id", None)
        span.setdefault("attempt", 1)
    usage = raw.get("usage", {})
    task_id = raw.get("task_id") if "task_id" in raw else (
        started_record.get("task_id") if started_record is not None else None
    )
    record = {
        "schema_version": EXECUTION_TRACE_SCHEMA_VERSION,
        "event_id": f"X{uuid.uuid4().hex[:12]}",
        "event_type": "span_completed",
        "timestamp": raw.get("timestamp") or (span.get("finished_at") if isinstance(span, dict) else now_iso()),
        "mission_id": _trace_mission_id(mission),
        "task_id": task_id,
        "span": span,
        "usage": usage,
        "refs": raw.get("refs", {}),
    }
    if isinstance(usage, dict) and usage:
        record["usage_source"] = raw.get("usage_source") or (
            span.get("measurement_source") if isinstance(span, dict) else None
        )
    if "metadata" in raw and not isinstance(raw.get("metadata"), dict):
        record["metadata"] = raw["metadata"]
    elif started_record is not None or "metadata" in raw:
        metadata = dict(started_record.get("metadata", {})) if started_record is not None else {}
        metadata.update(raw.get("metadata", {}))
        record["metadata"] = metadata
    return append_execution_trace_record(mission_dir, record)


def _risk_signals(mission: dict[str, Any]) -> list[dict[str, Any]]:
    shared_context = mission.get("shared_context")
    if not isinstance(shared_context, dict):
        return []
    risk_signals = shared_context.get("risk_signals")
    if not isinstance(risk_signals, list):
        return []
    return [signal for signal in risk_signals if isinstance(signal, dict)]


def active_risk_signals(mission: dict[str, Any]) -> list[dict[str, Any]]:
    return [signal for signal in _risk_signals(mission) if signal.get("status") == "active"]


def recent_resolved_risk_signals(mission: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    resolved = [
        signal
        for signal in _risk_signals(mission)
        if signal.get("status") in {"resolved", "superseded", "invalidated"}
    ]
    return resolved[-limit:]


def highest_active_risk_severity(mission: dict[str, Any]) -> str | None:
    severities = [
        signal.get("severity")
        for signal in active_risk_signals(mission)
        if signal.get("severity") in RISK_SIGNAL_SEVERITY_ORDER
    ]
    if not severities:
        return None
    return max(severities, key=lambda severity: RISK_SIGNAL_SEVERITY_ORDER[str(severity)])


def shared_context_summary(mission: dict[str, Any]) -> dict[str, Any]:
    active = active_risk_signals(mission)
    return {
        "active_risk_signals": active,
        "recent_resolved_risk_signals": recent_resolved_risk_signals(mission),
        "active_risk_signal_count": len(active),
        "highest_active_severity": highest_active_risk_severity(mission),
    }


def _ensure_shared_context(mission: dict[str, Any]) -> dict[str, Any]:
    shared_context = mission.get("shared_context")
    if not isinstance(shared_context, dict):
        shared_context = {}
        mission["shared_context"] = shared_context
    risk_signals = shared_context.get("risk_signals")
    if not isinstance(risk_signals, list):
        shared_context["risk_signals"] = []
    return shared_context


def _next_risk_signal_id(mission: dict[str, Any]) -> str:
    used = {signal.get("id") for signal in _risk_signals(mission) if isinstance(signal.get("id"), str)}
    index = len(used) + 1
    while f"R{index}" in used:
        index += 1
    return f"R{index}"


def _next_event_id(mission_dir: Path) -> str:
    return f"E{uuid.uuid4().hex[:8]}"


def record_risk_signal(mission_dir: Path, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    mission = read_mission(mission_dir)
    find_task(mission, task_id)
    shared_context = _ensure_shared_context(mission)
    event_id = _next_event_id(mission_dir)
    timestamp = now_iso()
    signal = {
        "id": _next_risk_signal_id(mission),
        "source_task_id": task_id,
        "source_evidence_id": event_id,
        "scope": payload.get("scope"),
        "signal": payload.get("signal"),
        "severity": payload.get("severity"),
        "confidence": payload.get("confidence"),
        "affected_surfaces": payload.get("affected_surfaces"),
        "value_effect": payload.get("value_effect"),
        "recommended_gate": payload.get("recommended_gate"),
        "recovery_condition": payload.get("recovery_condition"),
        "status": "active",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    for optional_field in ("supersedes", "notes"):
        if optional_field in payload:
            signal[optional_field] = payload[optional_field]
    shared_context["risk_signals"].append(signal)
    errors = validate_mission(mission)
    if errors:
        raise TplanError("; ".join(errors))
    require_indexed_shared_context_target(mission)
    event = append_event(
        mission_dir,
        {
            "id": event_id,
            "timestamp": timestamp,
            "event_type": "risk_context_update",
            "summary": payload.get("summary", signal["value_effect"]),
            "task_id": task_id,
            "payload": {"risk_signal": signal},
        },
    )
    write_mission(mission_dir, mission)
    write_indexed_shared_context(mission)
    return {"risk_signal": signal, "event": event}


def resolve_risk_signal(
    mission_dir: Path,
    task_id: str,
    risk_id: str,
    status: str,
    summary: str,
    recovery_note: str,
) -> dict[str, Any]:
    if status not in RISK_SIGNAL_STATUSES - {"active"}:
        raise TplanError("risk status for recovery must be resolved, superseded, or invalidated")
    mission = read_mission(mission_dir)
    find_task(mission, task_id)
    signals = _risk_signals(mission)
    signal = next((item for item in signals if item.get("id") == risk_id), None)
    if signal is None:
        raise TplanError(f"risk signal {risk_id} does not exist")

    event_id = _next_event_id(mission_dir)
    timestamp = now_iso()
    signal["status"] = status
    signal["updated_at"] = timestamp
    signal["resolution_task_id"] = task_id
    signal["resolution_evidence_id"] = event_id
    signal["recovery_note"] = recovery_note
    errors = validate_mission(mission)
    if errors:
        raise TplanError("; ".join(errors))
    require_indexed_shared_context_target(mission)
    event = append_event(
        mission_dir,
        {
            "id": event_id,
            "timestamp": timestamp,
            "event_type": "risk_context_recovery",
            "summary": summary,
            "task_id": task_id,
            "payload": {
                "risk_id": risk_id,
                "status": status,
                "recovery_note": recovery_note,
                "risk_signal": signal,
            },
        },
    )
    write_mission(mission_dir, mission)
    write_indexed_shared_context(mission)
    return {"risk_signal": signal, "event": event}


def step_log_path(mission_dir: Path, task_id: str) -> Path:
    return mission_paths(mission_dir)["logs"] / f"{slugify(task_id)}.jsonl"


def read_step_logs(mission_dir: Path, task_id: str) -> list[dict[str, Any]]:
    path = step_log_path(mission_dir, task_id)
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def append_step_log(mission_dir: Path, event: dict[str, Any]) -> dict[str, Any]:
    task_id = event.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise TplanError("step log task_id must be a non-empty string")
    find_task(read_mission(mission_dir), task_id)
    path = step_log_path(mission_dir, task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    events = read_step_logs(mission_dir, task_id)
    event = dict(event)
    event.setdefault("id", f"L{len(events) + 1}")
    event.setdefault("timestamp", now_iso())
    event.setdefault("payload", {})
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def archive_task_logs(mission_dir: Path, task_id: str, summary: str) -> Path:
    find_task(read_mission(mission_dir), task_id)
    paths = mission_paths(mission_dir)
    active_log = step_log_path(mission_dir, task_id)
    archive_dir = paths["archive"] / slugify(task_id)
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived_log = archive_dir / "step_logs.jsonl"
    if active_log.exists():
        active_log.replace(archived_log)
    elif not archived_log.exists():
        archived_log.write_text("", encoding="utf-8")
    summary_md = archive_dir / "summary.md"
    summary_md.write_text(
        f"# Task {task_id} Summary\n\n"
        f"{summary}\n\n"
        f"- archived_at: {now_iso()}\n"
        f"- step_log: step_logs.jsonl\n",
        encoding="utf-8",
    )
    return archive_dir


def format_stop_report(payload: dict[str, Any]) -> str:
    attempts = payload.get("attempts", [])
    attempt_lines = "\n".join(f"{index}. {attempt}" for index, attempt in enumerate(attempts, start=1))
    return (
        "停止报告\n\n"
        f"当前目标：\n{payload['current_goal']}\n\n"
        f"已尝试：\n{attempt_lines}\n\n"
        f"阻碍：\n{payload['blocking_issue']}\n\n"
        f"为何不能安全继续：\n{payload['why_cannot_continue_safely']}\n\n"
        f"需要人类提供：\n{payload['need_from_human']}\n\n"
        f"恢复条件：\n{payload['resume_condition']}"
    )


def record_stop_report(mission_dir: Path, task_id: str, summary: str, payload: dict[str, Any]) -> dict[str, Any]:
    attempts = payload.get("attempts")
    if not isinstance(attempts, list):
        raise TplanError("attempts must be a list")
    if len(attempts) > 3:
        raise TplanError("attempts must contain at most 3 items")
    if not attempts:
        raise TplanError("attempts must contain at least 1 item")
    required_fields = (
        "current_goal",
        "blocking_issue",
        "why_cannot_continue_safely",
        "need_from_human",
        "resume_condition",
    )
    for field in required_fields:
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise TplanError(f"stop report {field} must be a non-empty string")
    for attempt in attempts:
        if not isinstance(attempt, str) or not attempt.strip():
            raise TplanError("stop report attempts must be non-empty strings")

    before = read_mission(mission_dir)
    find_task(before, task_id)
    mission = copy.deepcopy(before)
    set_task_status(mission, task_id, "blocked")
    mission["active_task_id"] = task_id
    mission["mission"]["status"] = "requires_human"
    errors = validate_mission(mission)
    if errors:
        raise TplanError("; ".join(errors))
    event = prepare_event(
        mission_dir,
        {
            "event_type": "stop_report",
            "summary": summary,
            "task_id": task_id,
            "payload": payload,
        },
    )
    commit_mission_state(
        mission_dir,
        before,
        mission,
        source={"kind": "runtime_script", "name": "stop_report"},
        refs={"evidence_ids": [event["id"]]},
        task_details={task_id: {"outcome_summary": summary}},
        latest_state=f"Task {task_id} is blocked and requires human input.",
        prepared_evidence_events=[event],
    )
    return event


def find_task(mission: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in mission.get("tasks", []):
        if str(task.get("id")) == task_id:
            return task
    raise TplanError(f"task {task_id} does not exist")


def set_task_status(mission: dict[str, Any], task_id: str, status: str) -> dict[str, Any]:
    if status not in TASK_STATUSES:
        raise TplanError(f"task status unsupported: {status}")
    task = find_task(mission, task_id)
    current_status = task.get("status")
    if current_status not in TASK_STATUSES:
        raise TplanError(f"task {task_id} current status unsupported: {current_status}")
    allowed = ALLOWED_TASK_TRANSITIONS.get(str(current_status), {status})
    if status not in allowed:
        raise TplanError(f"illegal task status transition for {task_id}: {current_status} -> {status}")
    task["status"] = status
    if status == "active":
        mission["active_task_id"] = task_id
    elif mission.get("active_task_id") == task_id and status != "active":
        mission["active_task_id"] = None
    return mission


def parent_chain(mission: dict[str, Any], task_id: str | None) -> list[dict[str, Any]]:
    if task_id is None:
        return []
    tasks = task_map(mission)
    chain: list[dict[str, Any]] = []
    current = tasks.get(task_id)
    seen: set[str] = set()
    while current:
        current_id = str(current.get("id"))
        if current_id in seen:
            break
        seen.add(current_id)
        chain.append(current)
        parent_id = current.get("parent_id")
        current = tasks.get(str(parent_id)) if parent_id is not None else None
    return list(reversed(chain))


def tasks_by_status(mission: dict[str, Any]) -> dict[str, list[str]]:
    grouped = {status: [] for status in sorted(TASK_STATUSES)}
    for task in mission.get("tasks", []):
        status = task.get("status")
        if status in grouped:
            grouped[status].append(str(task.get("id")))
    return grouped


def active_task(mission: dict[str, Any]) -> dict[str, Any] | None:
    task_id = mission.get("active_task_id")
    if task_id is None:
        return None
    return task_map(mission).get(str(task_id))


def build_survey(mission_dir: Path) -> dict[str, Any]:
    mission = read_mission(mission_dir)
    active = active_task(mission)
    return {
        "mission": mission["mission"],
        "active_task": active,
        "active_parent_chain": parent_chain(mission, active.get("id") if active else None),
        "tasks_by_status": tasks_by_status(mission),
        "resource_sufficiency": mission["mission"]["resource_sufficiency"],
        "shared_context": shared_context_summary(mission),
        "event_count": len(read_events(mission_dir)),
    }


def _brief_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": event.get("id"),
        "event_type": event.get("event_type"),
        "task_id": event.get("task_id"),
        "summary": event.get("summary"),
    }


def _recent_evidence_summary(events: list[dict[str, Any]], limit: int = 5) -> dict[str, Any]:
    counts_by_type: dict[str, int] = {}
    for event in events:
        event_type = event.get("event_type")
        if isinstance(event_type, str):
            counts_by_type[event_type] = counts_by_type.get(event_type, 0) + 1
    return {
        "total_events": len(events),
        "last_event_id": events[-1].get("id") if events else None,
        "counts_by_type": counts_by_type,
        "recent_events": [_brief_event(event) for event in events[-limit:]],
    }


def _brief_step_log(log: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": log.get("id"),
        "step_id": log.get("step_id"),
        "summary": log.get("summary"),
    }


def _active_log_summary(
    active: dict[str, Any] | None,
    logs: list[dict[str, Any]],
    limit: int = 5,
) -> dict[str, Any]:
    object_touch_counts: dict[str, int] = {}
    for log in logs:
        payload = log.get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("object_id"), str):
            object_id = payload["object_id"]
            object_touch_counts[object_id] = object_touch_counts.get(object_id, 0) + 1
    return {
        "task_id": active.get("id") if active else None,
        "log_count": len(logs),
        "last_log_id": logs[-1].get("id") if logs else None,
        "recent_logs": [_brief_step_log(log) for log in logs[-limit:]],
        "object_touch_counts": object_touch_counts,
        "repeated_object_ids": sorted(object_id for object_id, count in object_touch_counts.items() if count >= 3),
        "additive_layering_seen": any(_is_additive_layer_log(log) for log in logs),
    }


def _evidence_link_lint(mission: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    event_ids = {event.get("id") for event in events if isinstance(event.get("id"), str)}
    invalid: list[dict[str, Any]] = []
    unbound: list[dict[str, Any]] = []
    for task in mission.get("tasks", []):
        if not isinstance(task, dict):
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str):
            task_id = "<unknown>"
        links = task.get("evidence_links", [])
        if not isinstance(links, list):
            invalid.append({"task_id": task_id, "field": "evidence_links", "reason": "not_a_list"})
            continue
        for link in links:
            if not isinstance(link, str):
                invalid.append({"task_id": task_id, "evidence_link": link, "reason": "not_a_string"})
            elif link not in event_ids:
                unbound.append({"task_id": task_id, "evidence_link": link})
    return {
        "invalid_evidence_links": invalid,
        "unbound_evidence_links": unbound,
    }


def _validate_mission_pulse_candidate(candidate: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    missing = sorted(MISSION_PULSE_CANDIDATE_REQUIRED_FIELDS - set(candidate))
    if missing:
        findings.append(f"candidate missing fields: {', '.join(missing)}")
        return findings
    if candidate.get("candidate_next_gate") not in MISSION_PULSE_NEXT_GATES - {"continue"}:
        findings.append("candidate.candidate_next_gate is invalid")
    if candidate.get("scope") not in MISSION_PULSE_SCOPES:
        findings.append("candidate.scope is invalid")
    if candidate.get("source_kind") not in MISSION_PULSE_CANDIDATE_SOURCE_KINDS:
        findings.append("candidate.source_kind is invalid")
    if candidate.get("priority_class") not in MISSION_PULSE_CANDIDATE_PRIORITIES:
        findings.append("candidate.priority_class is invalid")
    if candidate.get("severity") not in MISSION_PULSE_CANDIDATE_SEVERITIES:
        findings.append("candidate.severity is invalid")
    if candidate.get("freshness") not in MISSION_PULSE_CANDIDATE_FRESHNESS:
        findings.append("candidate.freshness is invalid")
    if not isinstance(candidate.get("source_ids"), list) or not all(
        isinstance(item, str) for item in candidate.get("source_ids", [])
    ):
        findings.append("candidate.source_ids must be a string list")
    if not isinstance(candidate.get("context"), dict):
        findings.append("candidate.context must be an object")
    for name in ("signal", "reason"):
        if not isinstance(candidate.get(name), str) or not candidate.get(name):
            findings.append(f"candidate.{name} must be a non-empty string")
    signals = candidate.get("signals")
    if signals is not None and (
        not isinstance(signals, list) or not all(isinstance(item, str) for item in signals)
    ):
        findings.append("candidate.signals must be a string list")
    return findings


def _pulse_arbitration_trace_key(item: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (
        item.get("signal"),
        item.get("priority_class"),
        item.get("candidate_next_gate"),
        item.get("severity"),
    )


def _validate_mission_pulse_output(output: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    pulse = output.get("mission_pulse")
    if not isinstance(pulse, dict):
        return ["mission_pulse must be an object"]
    if output.get("schema_version") != MISSION_PULSE_SCHEMA_VERSION:
        findings.append("schema_version is invalid")
    if output.get("script_verdict") != "shape_only":
        findings.append("script_verdict must be shape_only")
    if output.get("agentic_judgment_required") is not True:
        findings.append("agentic_judgment_required must be true")
    if pulse.get("schema_version") != MISSION_PULSE_SCHEMA_VERSION:
        findings.append("mission_pulse.schema_version is invalid")
    if pulse.get("trigger") not in MISSION_PULSE_TRIGGERS:
        findings.append("mission_pulse.trigger is invalid")
    if pulse.get("scope") not in MISSION_PULSE_SCOPES:
        findings.append("mission_pulse.scope is invalid")
    next_gate = pulse.get("next_gate")
    if next_gate not in MISSION_PULSE_NEXT_GATES:
        findings.append("mission_pulse.next_gate is invalid")
    if next_gate in MISSION_PULSE_GATE_OWNERS and output.get("gate_owner") != MISSION_PULSE_GATE_OWNERS[next_gate]:
        findings.append("gate_owner does not match mission_pulse.next_gate")
    if pulse.get("evidence_delta") not in MISSION_PULSE_EVIDENCE_DELTAS:
        findings.append("mission_pulse.evidence_delta is invalid")
    if pulse.get("branch_disposition") not in MISSION_PULSE_BRANCH_DISPOSITIONS:
        findings.append("mission_pulse.branch_disposition is invalid")
    if pulse.get("systemic_probe") not in MISSION_PULSE_SYSTEMIC_PROBES:
        findings.append("mission_pulse.systemic_probe is invalid")
    for name in ("signals", "evidence_links"):
        value = pulse.get(name)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            findings.append(f"mission_pulse.{name} must be a string list")
    candidates = output.get("review_trigger_candidates")
    if not isinstance(candidates, list):
        findings.append("review_trigger_candidates must be a list")
        candidates = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            findings.append("review_trigger_candidates entries must be objects")
            continue
        findings.extend(_validate_mission_pulse_candidate(candidate))
    winning_candidate = output.get("winning_candidate")
    if winning_candidate is not None and not isinstance(winning_candidate, dict):
        findings.append("winning_candidate must be an object or null")
    suppressed_candidates = output.get("suppressed_candidates")
    if not isinstance(suppressed_candidates, list):
        findings.append("suppressed_candidates must be a list")
        suppressed_candidates = []
    arbitration_trace = output.get("arbitration_trace")
    if not isinstance(arbitration_trace, list):
        findings.append("arbitration_trace must be a list")
        arbitration_trace = []
    trace_objects: list[dict[str, Any]] = []
    for entry in arbitration_trace:
        if not isinstance(entry, dict):
            findings.append("arbitration_trace entries must be objects")
            continue
        trace_objects.append(entry)
        for name in ("signal", "priority_class", "candidate_next_gate", "severity", "decision", "reason"):
            if not isinstance(entry.get(name), str) or not entry.get(name):
                findings.append(f"arbitration_trace.{name} must be a non-empty string")
        if entry.get("decision") not in {"selected", "suppressed"}:
            findings.append("arbitration_trace.decision must be selected or suppressed")
    if Counter(_pulse_arbitration_trace_key(entry) for entry in trace_objects) != Counter(
        _pulse_arbitration_trace_key(candidate)
        for candidate in candidates
        if isinstance(candidate, dict)
    ):
        findings.append("arbitration_trace entries must match review_trigger_candidates")
    selected_trace = [entry for entry in trace_objects if entry.get("decision") == "selected"]
    suppressed_trace = [entry for entry in trace_objects if entry.get("decision") == "suppressed"]
    active_candidates = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict) and candidate.get("candidate_state") != "stale"
    ]
    expected_selected_count = 1 if active_candidates else 0
    if len(selected_trace) != expected_selected_count:
        findings.append("arbitration_trace must contain exactly one selected entry when active candidates exist")
    if winning_candidate is not None and isinstance(winning_candidate, dict) and selected_trace:
        if _pulse_arbitration_trace_key(selected_trace[0]) != _pulse_arbitration_trace_key(winning_candidate):
            findings.append("arbitration_trace selected entry must match winning_candidate")
    if Counter(_pulse_arbitration_trace_key(entry) for entry in suppressed_trace) != Counter(
        _pulse_arbitration_trace_key(candidate)
        for candidate in suppressed_candidates
        if isinstance(candidate, dict)
    ):
        findings.append("arbitration_trace suppressed entries must match suppressed_candidates")
    if next_gate == "continue" and winning_candidate is not None:
        findings.append("mission_pulse.next_gate=continue requires null winning_candidate")
    if next_gate != "continue" and winning_candidate is None:
        findings.append("non-continue mission_pulse.next_gate requires winning_candidate")
    for name in ("recent_evidence_summary", "active_log_summary", "evidence_link_lint"):
        if not isinstance(output.get(name), dict):
            findings.append(f"{name} must be an object")
    return findings


def _pulse_candidate(
    *,
    signal: str,
    candidate_next_gate: str,
    scope: str,
    source_kind: str,
    source_ids: list[str] | None = None,
    priority_class: str,
    severity: str,
    freshness: str,
    reason: str,
    context: dict[str, Any] | None = None,
    signals: list[str] | None = None,
    evidence_delta: str = "unclear",
    branch_disposition: str = "unclear",
    systemic_probe: str = "needs_gate",
    rationale: str | None = None,
) -> dict[str, Any]:
    return {
        "signal": signal,
        "candidate_next_gate": candidate_next_gate,
        "scope": scope,
        "source_kind": source_kind,
        "source_ids": list(source_ids or []),
        "priority_class": priority_class,
        "severity": severity,
        "freshness": freshness,
        "reason": reason,
        "context": dict(context or {}),
        "signals": signals or [signal],
        "evidence_delta": evidence_delta,
        "branch_disposition": branch_disposition,
        "systemic_probe": systemic_probe,
        "rationale": rationale or reason,
    }


def _active_risk_implies_invalid_evidence(signal: dict[str, Any]) -> bool:
    fields: list[str] = []
    for field in ("scope", "signal"):
        value = signal.get(field)
        if isinstance(value, str):
            fields.append(value)
    surfaces = signal.get("affected_surfaces")
    if isinstance(surfaces, list):
        fields.extend(str(item) for item in surfaces if isinstance(item, str))
    haystack = " ".join(fields).lower()
    return "evidence" in haystack


def _collect_shared_risk_candidates(active_risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not active_risks:
        return []
    source_ids = [
        str(signal.get("source_evidence_id"))
        for signal in active_risks
        if isinstance(signal.get("source_evidence_id"), str)
    ]
    risk_signal_ids = [str(signal.get("id")) for signal in active_risks if isinstance(signal.get("id"), str)]
    signals = ["active_shared_risk"]
    if any(_active_risk_implies_invalid_evidence(signal) for signal in active_risks):
        signals.append("invalid_evidence_risk")
    return [
        _pulse_candidate(
            signal="active_shared_risk",
            candidate_next_gate="health_check",
            scope="mission",
            source_kind="evidence_event",
            source_ids=source_ids,
            priority_class="active_shared_risk",
            severity="high",
            freshness="current_state",
            reason="Active shared risk can change risk-adjusted Mission value before another local action.",
            context={"risk_signal_ids": risk_signal_ids},
            signals=signals,
            branch_disposition="keep",
            systemic_probe="use_existing_structure",
            rationale="Active shared risk should be routed to existing risk assessment before continuation.",
        )
    ]


def _collect_requires_human_candidates(mission: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if mission.get("mission", {}).get("status") != "requires_human":
        return []
    source_ids = [
        str(event.get("id"))
        for event in events
        if event.get("event_type") == "stop_report" and isinstance(event.get("id"), str)
    ]
    return [
        _pulse_candidate(
            signal="requires_human",
            candidate_next_gate="stop",
            scope="mission",
            source_kind="mission_state",
            source_ids=source_ids[-3:],
            priority_class="requires_human_or_stop",
            severity="critical",
            freshness="current_state",
            reason="Mission already requires human authority before safe continuation.",
            signals=["requires_human", "authority_boundary_unclear"],
            branch_disposition="defer",
            rationale="Continuation is not authorized while Mission status requires human intervention.",
        )
    ]


def _is_additive_layer_log(log: dict[str, Any]) -> bool:
    payload = log.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    change_kind = payload.get("change_kind")
    if isinstance(change_kind, str) and change_kind in {
        "add_layer",
        "add_fallback",
        "add_rule",
        "add_branch",
        "special_case",
    }:
        return True
    summary = log.get("summary")
    return isinstance(summary, str) and any(
        marker in summary.lower() for marker in ("fallback", "new layer", "special-case", "special case")
    )


def _collect_anti_spiral_candidates(
    active: dict[str, Any] | None,
    logs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if active is None or not isinstance(active.get("id"), str):
        return []
    object_touches: dict[str, int] = {}
    object_log_ids: dict[str, list[str]] = {}
    additive_layering = False
    for log in logs:
        payload = log.get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("object_id"), str):
            object_id = payload["object_id"]
            object_touches[object_id] = object_touches.get(object_id, 0) + 1
            log_id = log.get("id")
            if isinstance(log_id, str):
                object_log_ids.setdefault(object_id, []).append(log_id)
        additive_layering = additive_layering or _is_additive_layer_log(log)
    repeated = sorted(object_id for object_id, count in object_touches.items() if count >= 3)
    if not repeated:
        return []
    source_ids: list[str] = []
    for object_id in repeated:
        source_ids.extend(object_log_ids.get(object_id, []))
    signals = ["third_touch"]
    if additive_layering:
        signals.append("additive_layering")
    return [
        _pulse_candidate(
            signal="third_touch",
            candidate_next_gate="anti_spiral_audit",
            scope="subpath",
            source_kind="step_log",
            source_ids=source_ids,
            priority_class="anti_spiral",
            severity="medium",
            freshness="current_path",
            reason="The same local object appears in three or more active task logs.",
            context={"object_ids": repeated},
            signals=signals,
            evidence_delta="weak_evidence_expected",
            rationale="Repeated local repair should route through Anti-Spiral before another local change.",
        )
    ]


def _events_by_type(events: list[dict[str, Any]], event_types: set[str]) -> list[dict[str, Any]]:
    return [event for event in events if event.get("event_type") in event_types]


def _event_source_ids(events: list[dict[str, Any]], limit: int = 3) -> list[str]:
    return [
        str(event.get("id"))
        for event in events[-limit:]
        if isinstance(event.get("id"), str)
    ]


def _event_is_on_current_path(
    event: dict[str, Any],
    mission: dict[str, Any],
    active: dict[str, Any] | None,
) -> bool:
    task_id = event.get("task_id")
    if task_id is None:
        return True
    if not isinstance(task_id, str):
        return False
    task = task_map(mission).get(task_id)
    if task and task.get("status") in {"completed", "pruned", "abandoned", "superseded"}:
        return False
    return active is not None and task_id == active.get("id")


def _collect_feedback_or_blocker_candidates(
    mission: dict[str, Any],
    active: dict[str, Any] | None,
    events: list[dict[str, Any]],
    trigger: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    feedback_events = [
        event
        for event in _events_by_type(events, {"feedback", "user_feedback"})
        if _event_is_on_current_path(event, mission, active)
    ]
    if trigger == "feedback" and feedback_events:
        candidates.append(
            _pulse_candidate(
                signal="user_feedback",
                candidate_next_gate="loopback",
                scope="active_node",
                source_kind="evidence_event",
                source_ids=_event_source_ids(feedback_events),
                priority_class="current_blocker_or_feedback",
                severity="high",
                freshness="current_path",
                reason="Feedback can mean the current problem definition needs a loopback before more execution.",
                branch_disposition="keep",
                rationale="Feedback should be routed to loopback for definition or resolution adjustment.",
            )
        )

    blocker_events = [
        event
        for event in _events_by_type(events, {"blocker", "blocked", "failure", "interruption", "surprise"})
        if _event_is_on_current_path(event, mission, active)
    ]
    if blocker_events:
        candidates.append(
            _pulse_candidate(
                signal="blocker_or_surprise",
                candidate_next_gate="mission_review",
                scope="mission",
                source_kind="evidence_event",
                source_ids=_event_source_ids(blocker_events),
                priority_class="current_blocker_or_feedback",
                severity="high",
                freshness="current_path",
                reason="A blocker or surprise may change the Mission-relative path, authority, or acceptance boundary.",
                rationale="Blockers and surprises should be reviewed at Mission level before local continuation.",
            )
        )
    return candidates


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _active_task_has_acceptance_evidence_movement(
    active: dict[str, Any],
    events: list[dict[str, Any]],
    batch_start: datetime,
) -> bool:
    active_id = str(active["id"])
    evidence_links = active.get("evidence_links", [])
    linked_event_ids = {link for link in evidence_links if isinstance(link, str)} if isinstance(evidence_links, list) else set()
    acceptance_event_types = {"acceptance", "acceptance_passed", "acceptance_failed"}
    return any(
        event.get("task_id") == active_id
        and _parse_iso_timestamp(event.get("timestamp")) is not None
        and _parse_iso_timestamp(event.get("timestamp")) >= batch_start
        and (event.get("event_type") in acceptance_event_types or event.get("id") in linked_event_ids)
        for event in events
    )


def _collect_checkpoint_batch_candidates(
    active: dict[str, Any] | None,
    logs: list[dict[str, Any]],
    events: list[dict[str, Any]],
    trigger: str,
) -> list[dict[str, Any]]:
    if trigger != "checkpoint_batch" or active is None or not isinstance(active.get("id"), str):
        return []
    checkpoint_logs = [log for log in logs if log.get("step_id") == "checkpoint"]
    if len(checkpoint_logs) < 3:
        return []
    batch_logs = checkpoint_logs[-3:]
    batch_start = _parse_iso_timestamp(batch_logs[0].get("timestamp"))
    if batch_start is not None and _active_task_has_acceptance_evidence_movement(active, events, batch_start):
        return []
    return [
        _pulse_candidate(
            signal="checkpoint_batch_without_acceptance_evidence",
            candidate_next_gate="continuation_authorization",
            scope="active_node",
            source_kind="step_log",
            source_ids=_event_source_ids(batch_logs),
            priority_class="checkpoint_weak_evidence_delta",
            severity="medium",
            freshness="checkpoint_window",
            reason="Several active-task checkpoints were recorded without fresh active-task evidence movement.",
            signals=["weak_evidence_delta", "checkpoint_batch_without_acceptance_evidence"],
            evidence_delta="weak_evidence_expected",
            branch_disposition="keep",
            rationale="A checkpoint batch with no fresh evidence movement should authorize continuation explicitly.",
        )
    ]


def _collect_mission_boundary_candidates(trigger: str) -> list[dict[str, Any]]:
    if trigger not in {"before_freeze", "before_handoff", "before_stop"}:
        return []
    return [
        _pulse_candidate(
            signal="mission_boundary_review",
            candidate_next_gate="mission_review",
            scope="mission",
            source_kind="trigger",
            source_ids=[],
            priority_class="mission_boundary",
            severity="high",
            freshness="current_trigger",
            reason="Freeze, handoff, or stop is a Mission-facing boundary and should be reviewed before closure.",
            context={"trigger": trigger},
            branch_disposition="defer",
            rationale="Mission boundary triggers should route to Mission Review before freeze, handoff, or stop.",
        )
    ]


def _collect_branch_cleanup_candidates(mission: dict[str, Any], trigger: str) -> list[dict[str, Any]]:
    if trigger not in {"branch_cleanup", "active_switch_candidate"}:
        return []
    active_id = mission.get("active_task_id")
    branch_ids = [
        str(task.get("id"))
        for task in mission.get("tasks", [])
        if task.get("role") in {"supporting", "exploratory"}
        and task.get("status") in {"pending", "active", "paused"}
        and task.get("id") != active_id
    ]
    if not branch_ids:
        return []
    return [
        _pulse_candidate(
            signal="branch_cleanup_candidate",
            candidate_next_gate="selection",
            scope="mission",
            source_kind="task",
            source_ids=branch_ids,
            priority_class="branch_or_switch_cleanup",
            severity="low",
            freshness="current_state",
            reason="Supporting or exploratory branches need Mission-relative disposition.",
            branch_disposition="unclear",
            systemic_probe="not_needed",
            rationale="Branch cleanup should route to selection or subtraction instead of direct pruning.",
        )
    ]


def _collect_same_path_continuation_candidates(
    trigger: str,
    active: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if trigger != "before_continue":
        return []
    if active is None:
        return []
    return [
        _pulse_candidate(
            signal="same_path_continuation",
            candidate_next_gate="continuation_authorization",
            scope="active_node",
            source_kind="trigger",
            source_ids=[],
            priority_class="same_path_continuation",
            severity="low",
            freshness="current_trigger",
            reason="Same-path continuation requires authorization when Mission-facing value is uncertain.",
            context={"trigger": trigger},
            branch_disposition="keep",
            systemic_probe="not_needed",
            rationale="Before continuing the active path, route to continuation authorization.",
        )
    ]


def _collect_no_active_path_candidates(trigger: str, active: dict[str, Any] | None) -> list[dict[str, Any]]:
    if active is not None:
        return []
    if trigger not in {"manual", "checkpoint_batch", "before_continue"}:
        return []
    return [
        _pulse_candidate(
            signal="active_node_missing",
            candidate_next_gate="mission_review",
            scope="mission",
            source_kind="mission_state",
            source_ids=[],
            priority_class="runtime_integrity",
            severity="high",
            freshness="current_state",
            reason="Pulse was asked to continue or inspect the current path without an active runtime node.",
            context={"trigger": trigger},
            rationale="Continuation needs an active node; without one, route to Mission Review.",
        )
    ]


def _collect_pulse_candidates(
    mission: dict[str, Any],
    events: list[dict[str, Any]],
    active: dict[str, Any] | None,
    active_logs: list[dict[str, Any]],
    active_risks: list[dict[str, Any]],
    trigger: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    candidates.extend(_collect_requires_human_candidates(mission, events))
    candidates.extend(_collect_mission_boundary_candidates(trigger))
    candidates.extend(_collect_no_active_path_candidates(trigger, active))
    candidates.extend(_collect_shared_risk_candidates(active_risks))
    candidates.extend(_collect_feedback_or_blocker_candidates(mission, active, events, trigger))
    candidates.extend(_collect_anti_spiral_candidates(active, active_logs))
    candidates.extend(_collect_checkpoint_batch_candidates(active, active_logs, events, trigger))
    candidates.extend(_collect_branch_cleanup_candidates(mission, trigger))
    candidates.extend(_collect_same_path_continuation_candidates(trigger, active))
    return candidates


def _ensure_pulse_state(mission: dict[str, Any]) -> dict[str, Any]:
    pulse_state = mission.get("pulse_state")
    if not isinstance(pulse_state, dict):
        pulse_state = {}
        mission["pulse_state"] = pulse_state
    consumed_candidates = pulse_state.get("consumed_candidates")
    if not isinstance(consumed_candidates, list):
        pulse_state["consumed_candidates"] = []
    return pulse_state


def _consumed_pulse_candidates(mission: dict[str, Any]) -> list[dict[str, Any]]:
    pulse_state = mission.get("pulse_state")
    if not isinstance(pulse_state, dict):
        return []
    consumed_candidates = pulse_state.get("consumed_candidates")
    if not isinstance(consumed_candidates, list):
        return []
    return [item for item in consumed_candidates if isinstance(item, dict)]


def _pulse_candidate_fingerprint(candidate: dict[str, Any]) -> str:
    payload = {
        "signal": candidate.get("signal"),
        "candidate_next_gate": candidate.get("candidate_next_gate"),
        "scope": candidate.get("scope"),
        "source_kind": candidate.get("source_kind"),
        "source_ids": candidate.get("source_ids"),
        "priority_class": candidate.get("priority_class"),
        "severity": candidate.get("severity"),
        "freshness": candidate.get("freshness"),
        "context": candidate.get("context"),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _pulse_candidate_is_active_by_design(candidate: dict[str, Any], trigger: str) -> bool:
    signal = candidate.get("signal")
    if signal in MISSION_PULSE_STICKY_SIGNALS:
        return True
    if signal == "requires_human" and trigger in {"before_continue", "before_freeze", "before_handoff", "before_stop"}:
        return True
    return False


def _apply_pulse_consumption_state(
    mission: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    trigger: str,
) -> list[dict[str, Any]]:
    consumed_index = {
        str(item.get("fingerprint")): item
        for item in _consumed_pulse_candidates(mission)
        if isinstance(item.get("fingerprint"), str)
    }
    annotated: list[dict[str, Any]] = []
    for raw_candidate in candidates:
        candidate = dict(raw_candidate)
        fingerprint = _pulse_candidate_fingerprint(candidate)
        candidate["fingerprint"] = fingerprint
        consumption = consumed_index.get(fingerprint)
        if consumption is None:
            candidate["candidate_state"] = "active"
            annotated.append(candidate)
            continue

        candidate["pulse_consumption"] = {
            "consumed_at": consumption.get("consumed_at"),
            "trigger": consumption.get("trigger"),
            "consumption_event_id": consumption.get("consumption_event_id"),
            "note": consumption.get("note"),
        }
        if _pulse_candidate_is_active_by_design(candidate, trigger):
            candidate["candidate_state"] = "active"
        else:
            candidate["candidate_state"] = "stale"
            candidate["stale_reason"] = (
                f"already consumed at {consumption.get('consumed_at')} and no new source delta was observed"
            )
        annotated.append(candidate)
    return annotated


def _pulse_candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, int]:
    priority = MISSION_PULSE_PRIORITY_ORDER.get(str(candidate.get("priority_class")), 999)
    severity = MISSION_PULSE_SEVERITY_ORDER.get(str(candidate.get("severity")), 0)
    tie_break = MISSION_PULSE_SIGNAL_TIE_BREAK_ORDER.get(str(candidate.get("signal")), 999)
    return (priority, -severity, tie_break)


def _pulse_suppression_reason(candidate: dict[str, Any], selected: dict[str, Any]) -> str:
    candidate_priority = MISSION_PULSE_PRIORITY_ORDER.get(str(candidate.get("priority_class")), 999)
    selected_priority = MISSION_PULSE_PRIORITY_ORDER.get(str(selected.get("priority_class")), 999)
    if candidate_priority != selected_priority:
        return "lower priority than selected candidate"
    candidate_severity = MISSION_PULSE_SEVERITY_ORDER.get(str(candidate.get("severity")), 0)
    selected_severity = MISSION_PULSE_SEVERITY_ORDER.get(str(selected.get("severity")), 0)
    if candidate_severity != selected_severity:
        return "lower severity than selected candidate within the same priority class"
    candidate_tie_break = MISSION_PULSE_SIGNAL_TIE_BREAK_ORDER.get(str(candidate.get("signal")), 999)
    selected_tie_break = MISSION_PULSE_SIGNAL_TIE_BREAK_ORDER.get(str(selected.get("signal")), 999)
    if candidate_tie_break != selected_tie_break:
        return "same priority and severity; explicit signal tie-breaker selected a stronger control route"
    return "same arbitration rank; deterministic collection order selected the first candidate"


def _arbitrate_pulse_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidates:
        return {
            "winning_candidate": None,
            "suppressed_candidates": [],
            "arbitration_trace": [],
        }
    stale_candidates = [candidate for candidate in candidates if candidate.get("candidate_state") == "stale"]
    active_candidates = [candidate for candidate in candidates if candidate.get("candidate_state") != "stale"]
    ordered = sorted(active_candidates, key=_pulse_candidate_sort_key)
    winning_candidate = ordered[0] if ordered else None
    suppressed_candidates = [candidate for candidate in candidates if candidate is not winning_candidate]
    arbitration_trace: list[dict[str, Any]] = []
    trace_candidates = ordered + sorted(stale_candidates, key=_pulse_candidate_sort_key)
    for candidate in trace_candidates:
        selected = candidate is winning_candidate
        if candidate.get("candidate_state") == "stale":
            decision = "suppressed"
            reason = candidate.get("stale_reason") or "already consumed without a new source delta"
        elif selected:
            decision = "selected"
            reason = "highest-ranked candidate"
        else:
            decision = "suppressed"
            reason = _pulse_suppression_reason(candidate, winning_candidate)
        arbitration_trace.append(
            {
                "signal": candidate["signal"],
                "priority_class": candidate["priority_class"],
                "candidate_next_gate": candidate["candidate_next_gate"],
                "severity": candidate["severity"],
                "decision": decision,
                "reason": reason,
            }
        )
    return {
        "winning_candidate": winning_candidate,
        "suppressed_candidates": suppressed_candidates,
        "arbitration_trace": arbitration_trace,
    }


def build_mission_pulse(mission_dir: Path, *, trigger: str = "manual") -> dict[str, Any]:
    if trigger not in MISSION_PULSE_TRIGGERS:
        allowed = ", ".join(sorted(MISSION_PULSE_TRIGGERS))
        raise TplanError(f"unsupported pulse trigger: {trigger}; expected one of: {allowed}")
    mission = read_mission(mission_dir)
    survey = build_survey(mission_dir)
    validation_findings = validate_mission(mission)
    events = read_events(mission_dir)
    active = active_task(mission)
    active_logs = read_step_logs(mission_dir, str(active["id"])) if active and isinstance(active.get("id"), str) else []
    active_risks = shared_context_summary(mission)["active_risk_signals"]
    recent_evidence_summary = _recent_evidence_summary(events)
    active_log_summary = _active_log_summary(active, active_logs)
    evidence_link_lint = _evidence_link_lint(mission, events)

    review_trigger_candidates = _collect_pulse_candidates(
        mission,
        events,
        active,
        active_logs,
        active_risks,
        trigger,
    )
    review_trigger_candidates = _apply_pulse_consumption_state(
        mission,
        review_trigger_candidates,
        trigger=trigger,
    )
    arbitration = _arbitrate_pulse_candidates(review_trigger_candidates)
    winning_candidate = arbitration["winning_candidate"]
    if winning_candidate is not None:
        signals = winning_candidate["signals"]
        scope = winning_candidate["scope"]
        evidence_delta = winning_candidate["evidence_delta"]
        branch_disposition = winning_candidate["branch_disposition"]
        systemic_probe = winning_candidate["systemic_probe"]
        next_gate = winning_candidate["candidate_next_gate"]
        rationale = winning_candidate["rationale"]
    else:
        signals = []
        scope = "active_node" if survey["active_task"] else "mission"
        evidence_delta = "new_evidence_expected"
        branch_disposition = "keep"
        systemic_probe = "not_needed"
        next_gate = "continue"
        rationale = "No review trigger candidates were mechanically observed; ordinary inline alignment may continue."

    mission_pulse = {
        "schema_version": MISSION_PULSE_SCHEMA_VERSION,
        "trigger": trigger,
        "scope": scope,
        "signals": signals,
        "evidence_delta": evidence_delta,
        "branch_disposition": branch_disposition,
        "systemic_probe": systemic_probe,
        "next_gate": next_gate,
        "rationale": rationale,
        "evidence_links": [],
    }

    output = {
        "schema_version": MISSION_PULSE_SCHEMA_VERSION,
        "script_verdict": "shape_only",
        "agentic_judgment_required": True,
        "snapshot": survey,
        "validation_findings": validation_findings,
        "recent_evidence_summary": recent_evidence_summary,
        "active_log_summary": active_log_summary,
        "evidence_link_lint": evidence_link_lint,
        "review_trigger_candidates": review_trigger_candidates,
        "winning_candidate": winning_candidate,
        "suppressed_candidates": arbitration["suppressed_candidates"],
        "arbitration_trace": arbitration["arbitration_trace"],
        "mission_pulse": mission_pulse,
        "gate_owner": MISSION_PULSE_GATE_OWNERS[next_gate],
        "suggested_agent_checks": [
            "Confirm the route is appropriate for Mission convergence.",
            "Do not treat this pulse output as semantic proof.",
            "Use the selected Gate for authorization, mutation, stop, or escalation.",
        ],
    }
    output["pulse_shape_findings"] = _validate_mission_pulse_output(output)
    return output


def consume_pulse_candidate(
    mission_dir: Path,
    candidate: dict[str, Any],
    *,
    trigger: str,
    note: str | None = None,
) -> dict[str, Any]:
    mission = read_mission(mission_dir)
    fingerprint = candidate.get("fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint:
        fingerprint = _pulse_candidate_fingerprint(candidate)
    timestamp = now_iso()
    event_id = _next_event_id(mission_dir)
    entry = {
        "fingerprint": fingerprint,
        "signal": candidate.get("signal"),
        "candidate_next_gate": candidate.get("candidate_next_gate"),
        "priority_class": candidate.get("priority_class"),
        "source_ids": list(candidate.get("source_ids", [])) if isinstance(candidate.get("source_ids"), list) else [],
        "consumed_at": timestamp,
        "trigger": trigger,
        "consumption_event_id": event_id,
        "note": note or "",
    }
    pulse_state = _ensure_pulse_state(mission)
    existing = _consumed_pulse_candidates(mission)
    pulse_state["consumed_candidates"] = [
        item for item in existing if item.get("fingerprint") != fingerprint
    ] + [entry]
    errors = validate_mission(mission)
    if errors:
        raise TplanError("; ".join(errors))
    event = append_event(
        mission_dir,
        {
            "id": event_id,
            "timestamp": timestamp,
            "event_type": "pulse_consumed",
            "summary": f"Consumed pulse candidate {candidate.get('signal')} -> {candidate.get('candidate_next_gate')}.",
            "task_id": mission.get("active_task_id"),
            "payload": {
                "trigger": trigger,
                "fingerprint": fingerprint,
                "candidate": {
                    "signal": candidate.get("signal"),
                    "candidate_next_gate": candidate.get("candidate_next_gate"),
                    "priority_class": candidate.get("priority_class"),
                    "source_ids": entry["source_ids"],
                },
                "note": note,
            },
        },
    )
    write_mission(mission_dir, mission)
    return {"consumed_candidate": entry, "event": event}


def consume_current_pulse_candidate(
    mission_dir: Path,
    *,
    trigger: str = "manual",
    signal: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    pulse = build_mission_pulse(mission_dir, trigger=trigger)
    if signal is None:
        candidate = pulse.get("winning_candidate")
        if not isinstance(candidate, dict):
            raise TplanError("no winning pulse candidate is available to consume")
    else:
        matches = [
            item
            for item in pulse.get("review_trigger_candidates", [])
            if isinstance(item, dict) and item.get("signal") == signal
        ]
        if not matches:
            raise TplanError(f"pulse candidate {signal!r} was not observed for trigger {trigger}")
        if len(matches) != 1:
            raise TplanError(f"pulse candidate {signal!r} is ambiguous for trigger {trigger}")
        candidate = matches[0]
    result = consume_pulse_candidate(mission_dir, candidate, trigger=trigger, note=note)
    result["pulse"] = pulse
    return result


def build_decision_packet(mission_dir: Path, hook: str) -> dict[str, Any]:
    mission = read_mission(mission_dir)
    events = read_events(mission_dir)
    active = active_task(mission)
    return {
        "schema_version": SCHEMA_VERSION,
        "hook": hook,
        "mission": {
            "id": mission["mission"]["id"],
            "title": mission["mission"]["title"],
            "objective": mission["mission"]["objective"],
            "status": mission["mission"]["status"],
            "acceptance_evidence": mission["mission"]["acceptance_evidence"],
        },
        "policy": {
            "human_in_loop": mission["mission"]["human_in_loop"],
            "risk_tolerance": mission["mission"]["risk_tolerance"],
            "resource_sufficiency": mission["mission"]["resource_sufficiency"],
        },
        "active_task": active,
        "parent_chain": parent_chain(mission, active.get("id") if active else None),
        "task_tree_summary": tasks_by_status(mission),
        "shared_context": shared_context_summary(mission),
        "relevant_evidence_events": events[-10:],
        "current_blockers_or_surprises": [
            event for event in events[-10:] if event.get("event_type") in {"failure", "blocked", "interruption"}
        ],
    }


def _is_high_impact_decision(decision: dict[str, Any]) -> bool:
    if decision.get("recommendation") in {"add", "subtract", "close", "escalate"}:
        return True
    for mutation in decision.get("proposed_mutations", []):
        if not isinstance(mutation, dict):
            continue
        mutation_type = mutation.get("type")
        if mutation_type in {"set_active_task", "set_mission_status"}:
            return True
        if mutation_type == "transition_task" and mutation.get("status") in {
            "paused",
            "pruned",
            "abandoned",
            "superseded",
        }:
            return True
    return False


def _requires_path_assessment(decision: dict[str, Any]) -> bool:
    hook = decision.get("hook")
    if hook in PATH_ASSESSMENT_HOOKS:
        return True
    if "mission_alignment" in decision:
        return True
    return _is_high_impact_decision(decision)


def _validate_path_assessment(decision: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _requires_path_assessment(decision):
        if "path_assessment" in decision and not isinstance(decision.get("path_assessment"), dict):
            return ["path_assessment must be an object"]
        return errors

    if "path_assessment" not in decision:
        return ["decision missing field: path_assessment"]

    assessment = decision.get("path_assessment")
    if not isinstance(assessment, dict):
        return ["path_assessment must be an object"]

    for field, allowed_values in PATH_ASSESSMENT_FIELDS.items():
        value = assessment.get(field)
        if not isinstance(value, str):
            errors.append(f"path_assessment {field} must be a string")
        elif value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            errors.append(f"path_assessment {field} unsupported: {value!r}; expected one of: {allowed}")
    return errors


def _requires_risk_assessment(decision: dict[str, Any], active_shared_risks: list[dict[str, Any]]) -> bool:
    return bool(active_shared_risks) and _requires_path_assessment(decision)


def _validate_risk_assessment(decision: dict[str, Any], active_shared_risks: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    required = _requires_risk_assessment(decision, active_shared_risks)
    if not required and "risk_assessment" not in decision:
        return errors
    if "risk_assessment" not in decision:
        return ["decision missing field: risk_assessment"]

    assessment = decision.get("risk_assessment")
    if not isinstance(assessment, dict):
        return ["risk_assessment must be an object"]

    shared_context_used = assessment.get("shared_context_used")
    if "shared_context_used" not in assessment:
        errors.append("risk_assessment missing field: shared_context_used")
    elif not isinstance(shared_context_used, list):
        errors.append("risk_assessment shared_context_used must be a list")
    elif not all(isinstance(item, str) for item in shared_context_used):
        errors.append("risk_assessment shared_context_used items must be strings")

    for field, allowed_values in RISK_ASSESSMENT_FIELDS.items():
        value = assessment.get(field)
        if field not in assessment:
            errors.append(f"risk_assessment missing field: {field}")
        elif not isinstance(value, str):
            errors.append(f"risk_assessment {field} must be a string")
        elif value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            errors.append(f"risk_assessment {field} unsupported: {value!r}; expected one of: {allowed}")
    return errors


def _requires_continuation_authorization(decision: dict[str, Any]) -> bool:
    return decision.get("recommendation") == "continue" and _requires_path_assessment(decision)


def _validate_continuation_authorization(decision: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = _requires_continuation_authorization(decision)
    if not required and "continuation_authorization" not in decision:
        return errors
    if "continuation_authorization" not in decision:
        return ["decision missing field: continuation_authorization"]

    authorization = decision.get("continuation_authorization")
    if not isinstance(authorization, dict):
        return ["continuation_authorization must be an object"]

    trigger_reasons = authorization.get("trigger_reasons")
    if "trigger_reasons" not in authorization:
        errors.append("continuation_authorization missing field: trigger_reasons")
    elif not isinstance(trigger_reasons, list):
        errors.append("continuation_authorization trigger_reasons must be a list")
    else:
        for reason in trigger_reasons:
            if not isinstance(reason, str):
                errors.append("continuation_authorization trigger_reasons items must be strings")
                break
            if reason not in CONTINUATION_TRIGGER_REASONS:
                allowed = ", ".join(sorted(CONTINUATION_TRIGGER_REASONS))
                errors.append(
                    f"continuation_authorization trigger_reasons unsupported: {reason!r}; "
                    f"expected one of: {allowed}"
                )

    for field, allowed_values in CONTINUATION_AUTHORIZATION_FIELDS.items():
        value = authorization.get(field)
        if field not in authorization:
            errors.append(f"continuation_authorization missing field: {field}")
        elif not isinstance(value, str):
            errors.append(f"continuation_authorization {field} must be a string")
        elif value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            errors.append(
                f"continuation_authorization {field} unsupported: {value!r}; expected one of: {allowed}"
            )
    return errors


def _validate_hook_output_messages(
    decision: Any,
    active_shared_risks: list[dict[str, Any]] | None = None,
) -> list[str]:
    errors: list[str] = []
    active_shared_risks = active_shared_risks or []
    if not isinstance(decision, dict):
        return ["decision must be an object"]
    for field in (
        "recommendation",
        "rationale",
        "confidence",
        "evidence_links",
        "proposed_mutations",
        "requires_human",
    ):
        if field not in decision:
            errors.append(f"decision missing field: {field}")

    recommendation = decision.get("recommendation")
    if not isinstance(recommendation, str):
        errors.append("recommendation must be a string")
    elif recommendation not in RECOMMENDATIONS:
        errors.append(f"recommendation unsupported: {recommendation!r}")

    confidence = decision.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100:
        errors.append("confidence must be an integer between 0 and 100")
    if not isinstance(decision.get("evidence_links", []), list):
        errors.append("evidence_links must be a list")
    if not isinstance(decision.get("proposed_mutations", []), list):
        errors.append("proposed_mutations must be a list")
    if not isinstance(decision.get("requires_human"), bool):
        errors.append("requires_human must be a boolean")
    if isinstance(decision, dict):
        if _is_high_impact_decision(decision):
            if "mission_alignment" not in decision:
                errors.append("decision missing field: mission_alignment")
            elif not isinstance(decision.get("mission_alignment"), str):
                errors.append("mission_alignment must be a string")
        elif "mission_alignment" in decision:
            if not isinstance(decision.get("mission_alignment"), str):
                errors.append("mission_alignment must be a string")
        else:
            for field in ("parent_alignment", "mission_trace"):
                if field not in decision:
                    errors.append(f"decision missing field: {field}")
                elif not isinstance(decision.get(field), str):
                    errors.append(f"{field} must be a string")
        errors.extend(_validate_path_assessment(decision))
        errors.extend(_validate_risk_assessment(decision, active_shared_risks))
        errors.extend(_validate_continuation_authorization(decision))
    return errors


def validate_hook_output_findings(
    decision: Any,
    active_shared_risks: list[dict[str, Any]] | None = None,
) -> list[Finding]:
    return findings_from_messages(
        _validate_hook_output_messages(decision, active_shared_risks),
        code="tplan-hook-output",
    )


def validate_hook_output(decision: Any, active_shared_risks: list[dict[str, Any]] | None = None) -> list[str]:
    return [finding.message for finding in validate_hook_output_findings(decision, active_shared_risks)]


def record_decision_recommendation(mission_dir: Path, decision: dict[str, Any]) -> dict[str, Any]:
    return append_event(
        mission_dir,
        {
            "event_type": "decision_recommendation",
            "summary": decision["rationale"],
            "task_id": None,
            "payload": decision,
        },
    )


def authority_mode(mission: dict[str, Any]) -> str:
    mission_meta = mission.get("mission", {})
    value = mission_meta.get("human_in_loop") if isinstance(mission_meta, dict) else None
    if value == 0:
        return "autonomous"
    if value == 100:
        return "advisory"
    raise TplanError("human_in_loop must be 0 or 100 in tplan.v0.1")


def require_mutation_field(mutation: dict[str, Any], mutation_type: str, field: str) -> Any:
    if field not in mutation:
        raise TplanError(f"mutation {mutation_type} missing field: {field}")
    value = mutation[field]
    if not isinstance(value, str):
        raise TplanError(f"mutation {mutation_type} {field} must be a string")
    return value


def apply_mutation(mission: dict[str, Any], mutation: Any) -> None:
    if not isinstance(mutation, dict):
        raise TplanError("mutation must be an object")
    mutation_type = mutation.get("type")
    if not isinstance(mutation_type, str):
        raise TplanError("mutation type must be a string")
    if mutation_type == "set_active_task":
        task_id = require_mutation_field(mutation, mutation_type, "task_id")
        set_task_status(mission, task_id, "active")
    elif mutation_type == "transition_task":
        task_id = require_mutation_field(mutation, mutation_type, "task_id")
        status = require_mutation_field(mutation, mutation_type, "status")
        set_task_status(mission, task_id, status)
    elif mutation_type == "set_mission_status":
        status = require_mutation_field(mutation, mutation_type, "status")
        if status not in MISSION_STATUSES:
            raise TplanError(f"mission status unsupported: {status}")
        mission["mission"]["status"] = status
    else:
        raise TplanError(f"mutation type unsupported: {mutation_type}")


def apply_decision(mission_dir: Path, decision: Any) -> str:
    before = read_mission(mission_dir)
    errors = validate_hook_output(decision, active_risk_signals(before))
    if errors:
        raise TplanError("; ".join(errors))

    mode = authority_mode(before)
    if mode == "advisory" or decision["requires_human"]:
        record_decision_recommendation(mission_dir, decision)
        return "recorded_recommendation"

    mission = copy.deepcopy(before)
    for mutation in decision["proposed_mutations"]:
        apply_mutation(mission, mutation)
    errors = validate_mission(mission)
    if errors:
        raise TplanError("; ".join(errors))
    event = prepare_event(
        mission_dir,
        {
            "event_type": "decision_applied",
            "summary": decision["rationale"],
            "task_id": None,
            "payload": decision,
        },
    )
    task_details = {
        mutation["task_id"]: {"outcome_summary": decision["rationale"]}
        for mutation in decision["proposed_mutations"]
        if mutation.get("type") == "transition_task" and isinstance(mutation.get("task_id"), str)
    }
    commit_mission_state(
        mission_dir,
        before,
        mission,
        source={"kind": "decision_hook", "name": decision["recommendation"]},
        refs={"evidence_ids": [event["id"]], "evidence_links": decision.get("evidence_links", [])},
        task_details=task_details,
        latest_state=f"Decision applied: {decision['recommendation']}.",
        prepared_evidence_events=[event],
    )
    return "applied_decision"
