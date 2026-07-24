#!/usr/bin/env python3
"""Capture privacy-minimized Codex hook/OTel telemetry into a bound TPlan Mission."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from tplan_runtime import (
    EXECUTION_TRACE_SCHEMA_VERSION,
    TplanError,
    _append_execution_trace_record_unlocked,
    _ensure_no_interaction_guard_unlocked,
    _prepare_supported_runtime_write_unlocked,
    _recover_pending_mission_transaction_unlocked,
    _trace_mission_id,
    execution_trace_lock,
    now_iso,
    read_mission,
    task_map,
    write_json,
)


BINDING_SCHEMA_VERSION = "tplan.codex_telemetry_binding.v0.1"
COVERAGE_SCHEMA_VERSION = "tplan.codex_telemetry_coverage.v0.1"
OTEL_EVENT_SCHEMA_VERSION = "tplan.codex_otel_event.v0.1"
ADAPTER_VERSION = "tplan.codex_telemetry_adapter.v0.1"
CORRELATION_KINDS = {"tool", "subagent"}
HOOK_EVENTS = {"PreToolUse", "PostToolUse", "SubagentStart", "SubagentStop"}
OTEL_RECORD_TYPES = {"model", "agent_turn", "tool"}
OTEL_SOURCE_EVENTS = {
    "model": {
        "codex.api_request",
        "codex.sse_event",
        "codex.websocket_request",
        "codex.websocket_event",
    },
    "agent_turn": {"codex.turn.e2e_duration"},
    "tool": {"codex.tool_result"},
}
OTEL_ALLOWED_FIELDS = {
    "schema_version",
    "event_id",
    "session_id",
    "thread_id",
    "turn_id",
    "record_type",
    "tool_use_id",
    "started_at",
    "finished_at",
    "duration_ms",
    "status",
    "task_id",
    "model",
    "usage",
    "source_event",
}
PRIVATE_FIELD_NAMES = {
    "arguments",
    "command",
    "content",
    "environment",
    "input",
    "last_assistant_message",
    "output",
    "payload",
    "prompt",
    "response",
    "secret",
    "stderr",
    "stdout",
    "tool_input",
    "tool_response",
    "transcript",
    "transcript_path",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,199}$")
SAFE_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,79}$")
SECRET_VALUE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})"
)
TERMINAL_SPAN_STATUSES = {"ok", "error", "cancelled", "unknown"}
SPAWN_TOOL_NAMES = {"Agent", "spawn_agent", "functions.spawn_agent"}


def _canonical_mission_dir(mission_dir: Path) -> Path:
    resolved = mission_dir.resolve()
    read_mission(resolved)
    return resolved


def _validated_state_dir(state_dir: Path, mission_dir: Path) -> Path:
    resolved = state_dir.resolve()
    if not resolved.is_dir():
        raise TplanError("--state-dir must be a pre-created host-controlled directory")
    try:
        resolved.relative_to(mission_dir)
    except ValueError:
        return resolved
    raise TplanError("--state-dir must be outside the Mission directory")


def _state_path(state_dir: Path, mission_dir: Path) -> Path:
    digest = hashlib.sha256(str(mission_dir).encode("utf-8")).hexdigest()[:20]
    return state_dir / f"tplan-codex-telemetry-{digest}.json"


def coverage_path(mission_dir: Path) -> Path:
    return mission_dir / "reports" / "codex-telemetry-coverage.json"


def _safe_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or SAFE_ID.fullmatch(value) is None:
        raise TplanError(f"Codex telemetry {field} must be a safe stable identifier")
    if SECRET_VALUE.search(value):
        raise TplanError(f"Codex telemetry {field} looks like a secret, not an identifier")
    return value


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise TplanError(f"Codex telemetry {field} must be an ISO-8601 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise TplanError(f"Codex telemetry {field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise TplanError(f"Codex telemetry {field} must include a timezone")
    return parsed


def _duration_ms(started_at: str, finished_at: str) -> int:
    started = _parse_timestamp(started_at, "started_at")
    finished = _parse_timestamp(finished_at, "finished_at")
    if finished < started:
        raise TplanError("Codex telemetry finished_at must not precede started_at")
    return round((finished - started).total_seconds() * 1000)


def _span_id(channel: str, session_id: str, correlation_id: str) -> str:
    digest = hashlib.sha256(
        f"{channel}\0{session_id}\0{correlation_id}".encode("utf-8")
    ).hexdigest()[:24]
    return f"SPC{digest}"


def _new_state(
    mission_dir: Path,
    mission: dict[str, Any],
    *,
    session_id: str,
    thread_id: str | None,
) -> dict[str, Any]:
    timestamp = now_iso()
    return {
        "schema_version": BINDING_SCHEMA_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "mission": {
            "id": _trace_mission_id(mission),
            "path": str(mission_dir),
        },
        "binding": {
            "session_id": session_id,
            "thread_id": thread_id,
            "scope": "session_and_thread" if thread_id else "session",
        },
        "created_at": timestamp,
        "updated_at": timestamp,
        "correlations": {"tool": {}, "subagent": {}},
        "completed_ids": {"tool": [], "subagent": [], "otel_event": [], "otel_tool": []},
        "turns": {},
        "counters": {
            "local_tool_spans": 0,
            "local_tool_hook_callbacks": 0,
            "subagent_spans": 0,
            "subagent_hook_callbacks": 0,
            "model_spans": 0,
            "token_usage_spans": 0,
            "turn_spans": 0,
            "otel_tool_spans": 0,
            "deduplicated_events": 0,
            "binding_failures": 0,
            "unpaired_events": 0,
            "trace_write_failures": 0,
        },
        "last_diagnostic": None,
    }


def _read_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TplanError(
            "Codex telemetry binding is missing; bind an explicit session before capture"
        ) from exc
    except json.JSONDecodeError as exc:
        raise TplanError("Codex telemetry binding state is invalid JSON") from exc
    if not isinstance(state, dict) or state.get("schema_version") != BINDING_SCHEMA_VERSION:
        raise TplanError("Codex telemetry binding state has an unsupported schema")
    counters = state.get("counters")
    if isinstance(counters, dict):
        counters.setdefault("local_tool_hook_callbacks", 0)
        counters.setdefault("subagent_hook_callbacks", 0)
    return state


def _validate_state_target(
    state: dict[str, Any], mission_dir: Path, mission: dict[str, Any]
) -> None:
    target = state.get("mission")
    if not isinstance(target, dict):
        raise TplanError("Codex telemetry binding has no Mission target")
    if target.get("path") != str(mission_dir) or target.get("id") != _trace_mission_id(mission):
        raise TplanError("Codex telemetry binding does not match this Mission")


def _write_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    write_json(path, state, durable=True)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _coverage_report(state: dict[str, Any]) -> dict[str, Any]:
    counters = state["counters"]

    def hook_coverage(count: int, callbacks: int, channel: str) -> dict[str, Any]:
        if count:
            status = "observed"
            reason = "sanitized paired lifecycle events were written"
        elif callbacks:
            status = "available_not_observed"
            reason = f"a bound {channel} hook callback was observed; no completed pair was written"
        else:
            status = "not_reported"
            reason = (
                f"Mission binding exists, but {channel} hook installation/trust "
                "has not been observed by the adapter"
            )
        return {
            "status": status,
            "observed_span_count": count,
            "reason": reason,
        }

    def observed_or_not_reported(count: int, reason: str) -> dict[str, Any]:
        return {
            "status": "observed" if count else "not_reported",
            "observed_span_count": count,
            "reason": (
                "exactly bound sanitized Codex OTel data was written"
                if count
                else reason
            ),
        }

    return {
        "schema_version": COVERAGE_SCHEMA_VERSION,
        "adapter_version": ADAPTER_VERSION,
        "generated_at": now_iso(),
        "binding": {
            "status": "exact",
            "scope": state["binding"]["scope"],
            "mission_id": state["mission"]["id"],
        },
        "channels": {
            "local_tools": hook_coverage(
                counters["local_tool_spans"],
                counters["local_tool_hook_callbacks"],
                "local-tool",
            ),
            "hosted_tools": {
                "status": "not_reported",
                "observed_span_count": 0,
                "reason": "Codex hosted tools do not currently expose PreToolUse/PostToolUse hooks",
            },
            "model_turns": observed_or_not_reported(
                counters["model_spans"] + counters["turn_spans"],
                "no exactly bound sanitized Codex OTel model/turn event was ingested",
            ),
            "tokens": observed_or_not_reported(
                counters["token_usage_spans"],
                "token usage is not inferred from hooks and no exactly bound sanitized model event was ingested",
            ),
            "waits": {
                "status": "not_reported",
                "observed_span_count": 0,
                "reason": "Codex exposes no distinct wait lifecycle hook; shell elapsed time is kept as script time",
            },
            "subagents": hook_coverage(
                counters["subagent_spans"],
                counters["subagent_hook_callbacks"],
                "SubAgent",
            ),
        },
        "deduplication": {
            "hook_preferred_for_tools": True,
            "deduplicated_event_count": counters["deduplicated_events"],
            "agent_turn_is_non_additive_envelope": True,
        },
        "privacy": {
            "raw_prompts": "rejected",
            "raw_model_responses": "rejected",
            "command_arguments": "not_persisted",
            "tool_inputs_and_outputs": "not_persisted",
            "connector_payloads": "not_persisted",
            "stable_ids": "host_state_only",
        },
        "diagnostics": {
            "binding_failure_count": counters["binding_failures"],
            "unpaired_event_count": counters["unpaired_events"],
            "trace_write_failure_count": counters["trace_write_failures"],
            "last_code": state.get("last_diagnostic"),
        },
    }


def _persist_state_and_coverage(
    state_path: Path, mission_dir: Path, state: dict[str, Any]
) -> None:
    _write_state(state_path, state)
    write_json(coverage_path(mission_dir), _coverage_report(state), durable=True)


def bind_session(
    mission_dir: Path,
    state_dir: Path,
    *,
    session_id: str,
    thread_id: str | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    session_id = _safe_id(session_id, "session_id")
    if thread_id is not None:
        thread_id = _safe_id(thread_id, "thread_id")
    path = _state_path(state_dir, mission_dir)
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        mission = _prepare_supported_runtime_write_unlocked(
            mission_dir,
            operation="codex_telemetry_bind",
        )
        if path.exists() and not replace:
            current = _read_state(path)
            current_binding = current.get("binding", {})
            if (
                current_binding.get("session_id") != session_id
                or current_binding.get("thread_id") != thread_id
            ):
                raise TplanError(
                    "Codex telemetry is already bound to a different session/thread; use --replace explicitly"
                )
            state = current
        else:
            state = _new_state(
                mission_dir,
                mission,
                session_id=session_id,
                thread_id=thread_id,
            )
        _validate_state_target(state, mission_dir, mission)
        _persist_state_and_coverage(path, mission_dir, state)
    return {
        "status": "bound",
        "mission_id": state["mission"]["id"],
        "binding_scope": state["binding"]["scope"],
        "state_file": str(path),
        "coverage_file": str(coverage_path(mission_dir)),
    }


def _binding_matches(state: dict[str, Any], event: dict[str, Any], *, otel: bool) -> bool:
    binding = state["binding"]
    if event.get("session_id") != binding["session_id"]:
        return False
    if otel and binding.get("thread_id") is not None:
        return event.get("thread_id") == binding["thread_id"]
    return True


def _task_attribution(mission: dict[str, Any]) -> tuple[str | None, str]:
    active_task_id = mission.get("active_task_id")
    task = task_map(mission).get(active_task_id) if isinstance(active_task_id, str) else None
    if isinstance(task, dict) and task.get("status") == "active":
        return active_task_id, "exact"
    return None, "mission_overhead"


def _record_turn_binding(
    state: dict[str, Any], turn_id: str, task_id: str | None, attribution: str
) -> None:
    turn = state["turns"].setdefault(
        turn_id, {"task_ids": [], "mission_overhead_observed": False}
    )
    if attribution == "exact" and task_id not in turn["task_ids"]:
        turn["task_ids"].append(task_id)
    elif attribution != "exact":
        turn["mission_overhead_observed"] = True


def _tool_shape(tool_name: str) -> tuple[str, str, str]:
    if tool_name == "Bash":
        return "script", "Codex shell tool", "shell"
    if tool_name == "apply_patch":
        return "tool", "Codex patch tool", "patch"
    if tool_name.startswith("mcp__"):
        return "tool", "Codex MCP tool", "mcp"
    return "tool", "Codex local tool", "local_function"


def _safe_class_label(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 160
        or "\n" in value
        or "\r" in value
        or SECRET_VALUE.search(value)
    ):
        raise TplanError(f"Codex telemetry {field} must be a safe class label")
    return value


def _post_tool_status(event: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if event.get("tool_name") != "Bash":
        return "unknown", {}
    response = event.get("tool_response")
    if not isinstance(response, dict):
        return "unknown", {}
    exit_code = response.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        return "unknown", {}
    return ("ok" if exit_code == 0 else "error"), {"exit_code": exit_code}


def _start_record(
    mission: dict[str, Any],
    *,
    span_id: str,
    task_id: str | None,
    attribution: str,
    kind: str,
    label: str,
    observed_at: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": EXECUTION_TRACE_SCHEMA_VERSION,
        "event_id": f"X{uuid.uuid4().hex[:12]}",
        "event_type": "span_started",
        "timestamp": observed_at,
        "mission_id": _trace_mission_id(mission),
        "task_id": task_id,
        "span": {
            "span_id": span_id,
            "parent_span_id": None,
            "kind": kind,
            "label": label,
            "measurement_source": "host_measured",
            "attribution": attribution,
            "attempt": 1,
        },
        "metadata": metadata,
        "refs": {},
    }


def _completion_record(
    mission: dict[str, Any],
    entry: dict[str, Any],
    *,
    finished_at: str,
    status: str,
    completion_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = dict(entry["metadata"])
    metadata.update(completion_metadata or {})
    return {
        "schema_version": EXECUTION_TRACE_SCHEMA_VERSION,
        "event_id": f"X{uuid.uuid4().hex[:12]}",
        "event_type": "span_completed",
        "timestamp": finished_at,
        "mission_id": _trace_mission_id(mission),
        "task_id": entry["task_id"],
        "span": {
            "span_id": entry["span_id"],
            "parent_span_id": None,
            "kind": entry["kind"],
            "label": entry["label"],
            "status": status,
            "measurement_source": "host_measured",
            "attribution": entry["attribution"],
            "started_at": entry["started_at"],
            "finished_at": finished_at,
            "duration_ms": _duration_ms(entry["started_at"], finished_at),
            "attempt": 1,
        },
        "usage": {},
        "metadata": metadata,
        "refs": {},
    }


def _diagnose(state: dict[str, Any], counter: str, code: str) -> None:
    state["counters"][counter] += 1
    state["last_diagnostic"] = code


def _hook_start(
    mission: dict[str, Any],
    state: dict[str, Any],
    *,
    channel: str,
    correlation_id: str,
    turn_id: str,
    observed_at: str,
    kind: str,
    label: str,
    metadata: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    correlations = state["correlations"][channel]
    if correlation_id in correlations:
        _diagnose(state, "deduplicated_events", "duplicate_start")
        return None, {"status": "deduplicated", "reason": "duplicate_start"}
    if correlation_id in state["completed_ids"][channel]:
        _diagnose(state, "deduplicated_events", "completed_correlation_replayed")
        return None, {"status": "deduplicated", "reason": "completed_correlation_replayed"}
    if channel == "tool" and correlation_id in state["completed_ids"]["otel_tool"]:
        _diagnose(state, "deduplicated_events", "otel_tool_already_recorded")
        return None, {"status": "deduplicated", "reason": "otel_tool_already_recorded"}
    task_id, attribution = _task_attribution(mission)
    _record_turn_binding(state, turn_id, task_id, attribution)
    entry = {
        "span_id": _span_id(channel, state["binding"]["session_id"], correlation_id),
        "task_id": task_id,
        "attribution": attribution,
        "turn_id": turn_id,
        "started_at": observed_at,
        "kind": kind,
        "label": label,
        "metadata": metadata,
    }
    return _start_record(
        mission,
        span_id=entry["span_id"],
        task_id=task_id,
        attribution=attribution,
        kind=kind,
        label=label,
        observed_at=observed_at,
        metadata=metadata,
    ), entry


def _hook_stop(
    mission: dict[str, Any],
    state: dict[str, Any],
    *,
    channel: str,
    correlation_id: str,
    turn_id: str,
    observed_at: str,
    status: str,
    expected_kind: str,
    expected_label: str,
    expected_metadata: dict[str, Any],
    completion_metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any]]:
    entry = state["correlations"][channel].get(correlation_id)
    if entry is None:
        if correlation_id in state["completed_ids"][channel]:
            _diagnose(state, "deduplicated_events", "duplicate_stop")
            return None, None, {"status": "deduplicated", "reason": "duplicate_stop"}
        _diagnose(state, "unpaired_events", "stop_without_start")
        return None, None, {"status": "not_reported", "reason": "stop_without_start"}
    if (
        entry.get("turn_id") != turn_id
        or entry.get("kind") != expected_kind
        or entry.get("label") != expected_label
        or any(
            entry.get("metadata", {}).get(field) != value
            for field, value in expected_metadata.items()
        )
    ):
        _diagnose(state, "unpaired_events", "correlation_identity_mismatch")
        return (
            None,
            None,
            {"status": "not_reported", "reason": "correlation_identity_mismatch"},
        )
    record = _completion_record(
        mission,
        entry,
        finished_at=observed_at,
        status=status,
        completion_metadata=completion_metadata,
    )
    return record, entry, {"status": "recorded", "span_id": entry["span_id"]}


def handle_hook(
    mission_dir: Path,
    state_dir: Path,
    event: Any,
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Handle one official Codex hook event without persisting raw hook content."""

    if not isinstance(event, dict):
        raise TplanError("Codex hook input must be an object")
    observed_at = observed_at or now_iso()
    _parse_timestamp(observed_at, "observed_at")
    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    path = _state_path(state_dir, mission_dir)
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        mission = _prepare_supported_runtime_write_unlocked(
            mission_dir,
            operation="codex_telemetry_hook",
        )
        state = _read_state(path)
        _validate_state_target(state, mission_dir, mission)
        if not _binding_matches(state, event, otel=False):
            _diagnose(state, "binding_failures", "session_binding_mismatch")
            _persist_state_and_coverage(path, mission_dir, state)
            return {
                "status": "not_reported",
                "reason": "session_binding_mismatch",
                "attribution": "none",
            }

        event_name = event.get("hook_event_name")
        if event_name not in HOOK_EVENTS:
            return {"status": "ignored", "reason": "unsupported_hook_event"}
        turn_id = _safe_id(event.get("turn_id"), "turn_id")
        start_record: dict[str, Any] | None = None
        completion_record: dict[str, Any] | None = None
        entry: dict[str, Any] | None = None

        if event_name in {"PreToolUse", "PostToolUse"}:
            tool_name = event.get("tool_name")
            if not isinstance(tool_name, str) or not tool_name or len(tool_name) > 200:
                raise TplanError("Codex telemetry tool_name must be a non-empty safe class label")
            tool_use_id = _safe_id(event.get("tool_use_id"), "tool_use_id")
            if tool_name in SPAWN_TOOL_NAMES:
                _diagnose(state, "deduplicated_events", "spawn_tool_deferred_to_subagent_hooks")
                _persist_state_and_coverage(path, mission_dir, state)
                return {
                    "status": "deduplicated",
                    "reason": "spawn_tool_deferred_to_subagent_hooks",
                }
            state["counters"]["local_tool_hook_callbacks"] += 1
            kind, label, tool_class = _tool_shape(tool_name)
            if event_name == "PreToolUse":
                start_record, entry_or_result = _hook_start(
                    mission,
                    state,
                    channel="tool",
                    correlation_id=tool_use_id,
                    turn_id=turn_id,
                    observed_at=observed_at,
                    kind=kind,
                    label=label,
                    metadata={"provider": "codex", "tool_class": tool_class},
                )
                if start_record is None:
                    _persist_state_and_coverage(path, mission_dir, state)
                    return entry_or_result
                entry = entry_or_result
                result = {"status": "recorded", "span_id": entry["span_id"]}
            else:
                completion_status, completion_metadata = _post_tool_status(event)
                completion_record, entry, result = _hook_stop(
                    mission,
                    state,
                    channel="tool",
                    correlation_id=tool_use_id,
                    turn_id=turn_id,
                    observed_at=observed_at,
                    status=completion_status,
                    expected_kind=kind,
                    expected_label=label,
                    expected_metadata={
                        "provider": "codex",
                        "tool_class": tool_class,
                    },
                    completion_metadata=completion_metadata,
                )
        else:
            agent_id = _safe_id(event.get("agent_id"), "agent_id")
            agent_type = _safe_class_label(event.get("agent_type"), "agent_type")
            state["counters"]["subagent_hook_callbacks"] += 1
            if event_name == "SubagentStart":
                start_record, entry_or_result = _hook_start(
                    mission,
                    state,
                    channel="subagent",
                    correlation_id=agent_id,
                    turn_id=turn_id,
                    observed_at=observed_at,
                    kind="agent_turn",
                    label="Codex SubAgent",
                    metadata={
                        "provider": "codex",
                        "agent_role": agent_type,
                        "parallel_group_id": "turn-"
                        + hashlib.sha256(turn_id.encode("utf-8")).hexdigest()[:12],
                    },
                )
                if start_record is None:
                    _persist_state_and_coverage(path, mission_dir, state)
                    return entry_or_result
                entry = entry_or_result
                result = {"status": "recorded", "span_id": entry["span_id"]}
            else:
                completion_record, entry, result = _hook_stop(
                    mission,
                    state,
                    channel="subagent",
                    correlation_id=agent_id,
                    turn_id=turn_id,
                    observed_at=observed_at,
                    status="ok",
                    expected_kind="agent_turn",
                    expected_label="Codex SubAgent",
                    expected_metadata={
                        "provider": "codex",
                        "agent_role": agent_type,
                    },
                )

        try:
            _ensure_no_interaction_guard_unlocked(mission_dir, "codex_telemetry_hook")
            if start_record is not None and entry is not None:
                _append_execution_trace_record_unlocked(mission_dir, start_record)
                channel = "subagent" if entry["kind"] == "agent_turn" else "tool"
                correlation_id = (
                    _safe_id(event.get("agent_id"), "agent_id")
                    if channel == "subagent"
                    else _safe_id(event.get("tool_use_id"), "tool_use_id")
                )
                state["correlations"][channel][correlation_id] = entry
            if completion_record is not None and entry is not None:
                _append_execution_trace_record_unlocked(mission_dir, completion_record)
                channel = "subagent" if entry["kind"] == "agent_turn" else "tool"
                correlation_id = (
                    _safe_id(event.get("agent_id"), "agent_id")
                    if channel == "subagent"
                    else _safe_id(event.get("tool_use_id"), "tool_use_id")
                )
                state["correlations"][channel].pop(correlation_id, None)
                state["completed_ids"][channel].append(correlation_id)
                counter = "subagent_spans" if channel == "subagent" else "local_tool_spans"
                state["counters"][counter] += 1
        except TplanError:
            _diagnose(state, "trace_write_failures", "trace_write_refused")
            result = {
                "status": "not_reported",
                "reason": "trace_write_refused",
                "attribution": "none",
            }
        _persist_state_and_coverage(path, mission_dir, state)
        return result


def _find_private_field(value: Any, path: str = "event") -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            next_path = f"{path}.{key}"
            compact = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
            if (
                normalized in PRIVATE_FIELD_NAMES
                or compact.startswith("raw_prompt")
                or compact.startswith("raw_response")
                or compact.startswith("model_response")
                or compact.startswith("command_arg")
                or compact.startswith("connector_payload")
                or compact.startswith("tool_payload")
            ):
                return next_path
            found = _find_private_field(item, next_path)
            if found:
                return found
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found = _find_private_field(item, f"{path}[{index}]")
            if found:
                return found
    return None


def _find_secret_value(value: Any, path: str = "event") -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            found = _find_secret_value(item, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found = _find_secret_value(item, f"{path}[{index}]")
            if found:
                return found
    elif isinstance(value, str) and SECRET_VALUE.search(value):
        return path
    return None


def _otel_attribution(
    mission: dict[str, Any], state: dict[str, Any], event: dict[str, Any]
) -> tuple[str | None, str]:
    turn = state["turns"].get(event["turn_id"])
    requested_task = event.get("task_id")
    if requested_task is None:
        return None, "mission_overhead"
    if requested_task not in task_map(mission):
        raise TplanError("Codex OTel task_id does not exist in the bound Mission")
    if (
        not isinstance(turn, dict)
        or turn.get("task_ids") != [requested_task]
        or turn.get("mission_overhead_observed")
    ):
        return None, "mission_overhead"
    return requested_task, "exact"


def ingest_otel_event(
    mission_dir: Path, state_dir: Path, event: Any
) -> dict[str, Any]:
    """Ingest one explicitly bound, sanitized Codex OTel projection."""

    if not isinstance(event, dict):
        raise TplanError("Codex OTel input must be an object")
    forbidden = _find_private_field(event)
    if forbidden:
        raise TplanError(f"Codex OTel input contains forbidden raw-content field: {forbidden}")
    secret = _find_secret_value(event)
    if secret:
        raise TplanError(f"Codex OTel input contains a secret-shaped value: {secret}")
    unsupported = sorted(set(event) - OTEL_ALLOWED_FIELDS)
    if unsupported:
        raise TplanError(
            "Codex OTel input fields unsupported: " + ", ".join(unsupported)
        )
    if event.get("schema_version") != OTEL_EVENT_SCHEMA_VERSION:
        raise TplanError(f"Codex OTel schema_version must be {OTEL_EVENT_SCHEMA_VERSION}")
    event_id = _safe_id(event.get("event_id"), "event_id")
    _safe_id(event.get("session_id"), "session_id")
    if event.get("thread_id") is not None:
        _safe_id(event.get("thread_id"), "thread_id")
    turn_id = _safe_id(event.get("turn_id"), "turn_id")
    record_type = event.get("record_type")
    if record_type not in OTEL_RECORD_TYPES:
        raise TplanError("Codex OTel record_type must be model, agent_turn, or tool")
    started_at = event.get("started_at")
    finished_at = event.get("finished_at")
    measured_duration = _duration_ms(started_at, finished_at)
    duration_ms = event.get("duration_ms")
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, int) or duration_ms < 0:
        raise TplanError("Codex OTel duration_ms must be a non-negative integer")
    if abs(duration_ms - measured_duration) > 1:
        raise TplanError("Codex OTel duration_ms does not match its timestamp interval")
    status = event.get("status", "unknown")
    if status not in TERMINAL_SPAN_STATUSES:
        raise TplanError("Codex OTel status is unsupported")
    source_event = event.get("source_event")
    if source_event not in OTEL_SOURCE_EVENTS[record_type]:
        raise TplanError("Codex OTel source_event is unsupported for this record_type")
    usage = event.get("usage", {})
    if not isinstance(usage, dict):
        raise TplanError("Codex OTel usage must be an object")
    allowed_usage = {
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    }
    if set(usage) - allowed_usage:
        raise TplanError("Codex OTel usage contains unsupported fields")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in usage.values()
    ):
        raise TplanError("Codex OTel token usage must contain non-negative integers")
    if record_type != "model" and usage:
        raise TplanError("only Codex model spans may carry token usage")

    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    path = _state_path(state_dir, mission_dir)
    with execution_trace_lock(mission_dir):
        _recover_pending_mission_transaction_unlocked(mission_dir)
        mission = _prepare_supported_runtime_write_unlocked(
            mission_dir,
            operation="codex_otel_ingestion",
        )
        state = _read_state(path)
        _validate_state_target(state, mission_dir, mission)
        if not _binding_matches(state, event, otel=True):
            _diagnose(state, "binding_failures", "otel_binding_mismatch")
            _persist_state_and_coverage(path, mission_dir, state)
            raise TplanError("Codex OTel session/thread binding mismatch")
        if event_id in state["completed_ids"]["otel_event"]:
            _diagnose(state, "deduplicated_events", "duplicate_otel_event")
            _persist_state_and_coverage(path, mission_dir, state)
            return {"status": "deduplicated", "reason": "duplicate_otel_event"}
        tool_use_id = event.get("tool_use_id")
        if record_type == "tool":
            tool_use_id = _safe_id(tool_use_id, "tool_use_id")
            if (
                tool_use_id in state["completed_ids"]["tool"]
                or tool_use_id in state["correlations"]["tool"]
            ):
                state["completed_ids"]["otel_event"].append(event_id)
                _diagnose(state, "deduplicated_events", "hook_tool_preferred")
                _persist_state_and_coverage(path, mission_dir, state)
                return {"status": "deduplicated", "reason": "hook_tool_preferred"}

        task_id, attribution = _otel_attribution(mission, state, event)
        kind = record_type
        label = {
            "model": "Codex model request",
            "agent_turn": "Codex turn envelope",
            "tool": "Codex OTel tool",
        }[record_type]
        metadata: dict[str, Any] = {
            "provider": "codex_otel",
            "operation": source_event,
        }
        model = event.get("model")
        if model is not None:
            if record_type != "model" or not isinstance(model, str) or SAFE_MODEL.fullmatch(model) is None:
                raise TplanError("Codex OTel model must be a safe model identifier on a model span")
            metadata["model"] = model
        span_id = _span_id("otel", state["binding"]["session_id"], event_id)
        record: dict[str, Any] = {
            "schema_version": EXECUTION_TRACE_SCHEMA_VERSION,
            "event_id": f"X{uuid.uuid4().hex[:12]}",
            "event_type": "span_completed",
            "timestamp": finished_at,
            "mission_id": _trace_mission_id(mission),
            "task_id": task_id,
            "span": {
                "span_id": span_id,
                "parent_span_id": None,
                "kind": kind,
                "label": label,
                "status": status,
                "measurement_source": "platform_reported",
                "attribution": attribution,
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_ms": duration_ms,
                "attempt": 1,
            },
            "usage": usage,
            "metadata": metadata,
            "refs": {},
        }
        if usage:
            record["usage_source"] = "platform_reported"
        _append_execution_trace_record_unlocked(mission_dir, record)
        state["completed_ids"]["otel_event"].append(event_id)
        if record_type == "tool":
            state["completed_ids"]["otel_tool"].append(tool_use_id)
            state["counters"]["otel_tool_spans"] += 1
        elif record_type == "model":
            state["counters"]["model_spans"] += 1
            if usage:
                state["counters"]["token_usage_spans"] += 1
        else:
            state["counters"]["turn_spans"] += 1
        _persist_state_and_coverage(path, mission_dir, state)
        return {
            "status": "recorded",
            "span_id": span_id,
            "attribution": attribution,
            "task_id": task_id,
        }


def capabilities(mission_dir: Path, state_dir: Path) -> dict[str, Any]:
    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    state = _read_state(_state_path(state_dir, mission_dir))
    _validate_state_target(state, mission_dir, read_mission(mission_dir))
    return _coverage_report(state)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture explicitly bound Codex hook/OTel telemetry for TPlan."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bind = subparsers.add_parser("bind", help="Bind one Codex session to one Mission.")
    bind.add_argument("mission_dir")
    bind.add_argument("--state-dir", required=True)
    bind.add_argument("--session-id", required=True)
    bind.add_argument("--thread-id")
    bind.add_argument("--replace", action="store_true")

    hook = subparsers.add_parser("hook", help="Consume one Codex hook JSON object from stdin.")
    hook.add_argument("mission_dir")
    hook.add_argument("--state-dir", required=True)
    hook.add_argument("--print-result", action="store_true")

    otel = subparsers.add_parser(
        "ingest-otel", help="Consume one sanitized, exactly bound OTel projection from stdin."
    )
    otel.add_argument("mission_dir")
    otel.add_argument("--state-dir", required=True)

    report = subparsers.add_parser("capabilities", help="Print capture/degradation coverage.")
    report.add_argument("mission_dir")
    report.add_argument("--state-dir", required=True)
    return parser.parse_args()


def _read_stdin_object() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise TplanError("Codex telemetry stdin must contain one JSON object") from exc
    if not isinstance(value, dict):
        raise TplanError("Codex telemetry stdin must contain one JSON object")
    return value


def main() -> int:
    args = parse_args()
    hook_event_name: str | None = None
    try:
        if args.command == "bind":
            result = bind_session(
                Path(args.mission_dir),
                Path(args.state_dir),
                session_id=args.session_id,
                thread_id=args.thread_id,
                replace=args.replace,
            )
        elif args.command == "hook":
            hook_event = _read_stdin_object()
            raw_hook_event_name = hook_event.get("hook_event_name")
            if isinstance(raw_hook_event_name, str):
                hook_event_name = raw_hook_event_name
            result = handle_hook(
                Path(args.mission_dir), Path(args.state_dir), hook_event
            )
            if not args.print_result:
                if hook_event_name == "SubagentStop":
                    print("{}")
                return 0
        elif args.command == "ingest-otel":
            result = ingest_otel_event(
                Path(args.mission_dir), Path(args.state_dir), _read_stdin_object()
            )
        else:
            result = capabilities(Path(args.mission_dir), Path(args.state_dir))
    except Exception as exc:
        if args.command == "hook":
            if args.print_result:
                print(
                    json.dumps(
                        {
                            "status": "not_reported",
                            "reason": "adapter_input_or_binding_error",
                            "attribution": "none",
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            elif hook_event_name == "SubagentStop":
                print("{}")
            return 0
        if not isinstance(exc, (OSError, ValueError, TplanError)):
            raise
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
