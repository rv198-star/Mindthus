#!/usr/bin/env python3
"""Map native host lifecycle events onto the bounded TPlan interaction guard.

The guard is released on the first owned end event.  It must never depend on a
model-visible continuation prompt to become unlockable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # pragma: no cover - platform import
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None  # type: ignore[assignment]

try:  # pragma: no cover - platform import
    import msvcrt
except ImportError:  # pragma: no cover - Unix path
    msvcrt = None  # type: ignore[assignment]

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from interaction_host import PROFILES, HostProfile, profile_for  # noqa: E402
from tplan_runtime import (  # noqa: E402
    TplanError,
    begin_interaction_guard,
    orphan_expired_interaction_guard,
    orphan_interaction_guard,
    read_interaction_guard,
    read_json,
    resolve_guard_at_turn_end,
    resolve_interaction_guard,
    stop_interaction_guard,
    write_json,
)


PLATFORM_EVENTS = {
    name: {
        "message": profile.message_event,
        "before_tool": profile.before_tool_event,
        "turn_end": profile.turn_end_event,
        "session_start": profile.session_start_event,
    }
    for name, profile in PROFILES.items()
}
HOST_STATE_SCHEMA_VERSION = "tplan.interaction_host_session.v0.2"
LEGACY_HOST_STATE_SCHEMA_VERSION = "tplan.interaction_host_session.v0.1"
HOST_TRACE_SCHEMA_VERSION = "tplan.interaction_host_trace.v0.1"
HOST_STATE_LOCK = threading.Lock()
CONTROL_ENVELOPE = re.compile(
    r"^TPLAN_CONTROL\s+guard=(?P<guard>IG[0-9a-fA-F]+)\s+revision=(?P<revision>[1-9][0-9]*)\s+action=(?P<action>resume|stop)\s*$"
)


def _host_state_path(mission_dir: Path, state_dir: Path | None = None) -> Path:
    if state_dir is None:
        return mission_dir / ".interaction-host-session.json"
    mission_key = hashlib.sha256(str(mission_dir.resolve()).encode("utf-8")).hexdigest()[:32]
    return state_dir / f"{mission_key}.json"


def _host_trace_path(mission_dir: Path, state_dir: Path | None = None) -> Path:
    if state_dir is None:
        return mission_dir / ".interaction-host-trace.jsonl"
    mission_key = hashlib.sha256(str(mission_dir.resolve()).encode("utf-8")).hexdigest()[:32]
    return state_dir / f"{mission_key}.trace.jsonl"


@contextmanager
def _host_state_lock(mission_dir: Path, state_dir: Path | None = None):
    state_path = _host_state_path(mission_dir, state_dir)
    lock_path = state_path.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with HOST_STATE_LOCK, lock_path.open("a+b") as handle:
        if hasattr(os, "fchmod"):
            os.fchmod(handle.fileno(), 0o600)
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


@contextmanager
def _host_trace_lock(mission_dir: Path, state_dir: Path | None = None):
    trace_path = _host_trace_path(mission_dir, state_dir)
    lock_path = trace_path.with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with HOST_STATE_LOCK, lock_path.open("a+b") as handle:
        if hasattr(os, "fchmod"):
            os.fchmod(handle.fileno(), 0o600)
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


def _safe_ref(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise TplanError(f"{label} must be a non-empty single-line string")
    return value


def _new_host_state(profile: HostProfile, session_id: str, message_ref: str, turn_id: str | None) -> dict[str, Any]:
    return {
        "schema_version": HOST_STATE_SCHEMA_VERSION,
        "profile_id": profile.profile_id,
        "platform": profile.platform,
        "session_id": session_id,
        "event_seq": 1,
        "first_message_ref": message_ref,
        "last_message_ref": message_ref,
        "active_turn_id": turn_id,
        "guard_id": None,
        "guard_turn_id": None,
        "last_failure": None,
        "legacy_continuation_state": False,
    }


def _normalize_legacy_host_state(raw: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version",
        "platform",
        "session_id",
        "first_message_ref",
        "last_message_ref",
        "continuation_requested",
        "continuation_token",
        "continuation_observed",
        "guard_turn_id",
        "continuation_turn_id",
    }
    if set(raw) != required or raw.get("schema_version") != LEGACY_HOST_STATE_SCHEMA_VERSION:
        raise TplanError("invalid interaction host-session state")
    platform = _safe_ref(raw.get("platform"), "host platform")
    profile = profile_for(platform)
    state = _new_host_state(
        profile,
        _safe_ref(raw.get("session_id"), "host session_id"),
        _safe_ref(raw.get("first_message_ref"), "host first_message_ref"),
        raw.get("guard_turn_id") if isinstance(raw.get("guard_turn_id"), str) else None,
    )
    state["last_message_ref"] = _safe_ref(raw.get("last_message_ref"), "host last_message_ref")
    state["guard_turn_id"] = raw.get("guard_turn_id")
    state["legacy_continuation_state"] = True
    state["last_failure"] = "legacy_continuation_state"
    return state


def _read_host_state(mission_dir: Path, state_dir: Path | None = None) -> dict[str, Any] | None:
    path = _host_state_path(mission_dir, state_dir)
    if not path.exists():
        return None
    raw = read_json(path)
    if raw.get("schema_version") == LEGACY_HOST_STATE_SCHEMA_VERSION:
        return _normalize_legacy_host_state(raw)
    required = {
        "schema_version",
        "profile_id",
        "platform",
        "session_id",
        "event_seq",
        "first_message_ref",
        "last_message_ref",
        "active_turn_id",
        "guard_id",
        "guard_turn_id",
        "last_failure",
        "legacy_continuation_state",
    }
    if set(raw) != required or raw.get("schema_version") != HOST_STATE_SCHEMA_VERSION:
        raise TplanError("invalid interaction host-session state")
    profile = profile_for(_safe_ref(raw.get("platform"), "host platform"))
    if raw.get("profile_id") != profile.profile_id:
        raise TplanError("interaction host-session profile mismatch")
    _safe_ref(raw.get("session_id"), "host session_id")
    _safe_ref(raw.get("first_message_ref"), "host first_message_ref")
    _safe_ref(raw.get("last_message_ref"), "host last_message_ref")
    if isinstance(raw.get("event_seq"), bool) or not isinstance(raw.get("event_seq"), int) or raw["event_seq"] < 1:
        raise TplanError("interaction host-session event_seq must be positive")
    for field in ("active_turn_id", "guard_id", "guard_turn_id", "last_failure"):
        if raw.get(field) is not None:
            _safe_ref(raw[field], f"host {field}")
    if not isinstance(raw.get("legacy_continuation_state"), bool):
        raise TplanError("interaction host-session legacy_continuation_state must be boolean")
    return raw


def _write_host_state(mission_dir: Path, state: dict[str, Any] | None, state_dir: Path | None = None) -> None:
    path = _host_state_path(mission_dir, state_dir)
    if state is None:
        if path.exists():
            path.unlink()
        return
    # Re-use validation before durable write.
    write_json(path, _read_host_state_from_value(state), durable=True)
    if os.name != "nt":
        path.chmod(0o600)


def _read_host_state_from_value(state: dict[str, Any]) -> dict[str, Any]:
    """Validate an in-memory state using the same exact schema as stored state."""

    # Avoid a temporary file and keep errors deterministic for hook callers.
    required = {
        "schema_version", "profile_id", "platform", "session_id", "event_seq", "first_message_ref",
        "last_message_ref", "active_turn_id", "guard_id", "guard_turn_id", "last_failure",
        "legacy_continuation_state",
    }
    if set(state) != required or state.get("schema_version") != HOST_STATE_SCHEMA_VERSION:
        raise TplanError("invalid interaction host-session state")
    profile = profile_for(_safe_ref(state.get("platform"), "host platform"))
    if state.get("profile_id") != profile.profile_id:
        raise TplanError("interaction host-session profile mismatch")
    for field in ("session_id", "first_message_ref", "last_message_ref"):
        _safe_ref(state.get(field), f"host {field}")
    if isinstance(state.get("event_seq"), bool) or not isinstance(state.get("event_seq"), int) or state["event_seq"] < 1:
        raise TplanError("interaction host-session event_seq must be positive")
    for field in ("active_turn_id", "guard_id", "guard_turn_id", "last_failure"):
        if state.get(field) is not None:
            _safe_ref(state[field], f"host {field}")
    if not isinstance(state.get("legacy_continuation_state"), bool):
        raise TplanError("interaction host-session legacy_continuation_state must be boolean")
    return state


def _event_kind(profile: HostProfile, event: Any) -> str | None:
    if event == profile.session_start_event:
        return "session_start"
    if event == profile.message_event:
        return "message"
    if event == profile.before_tool_event:
        return "before_tool"
    if event == profile.turn_end_event:
        return "turn_end"
    return None


def _hash_host_ref(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _host_boundary_digests(mission_dir: Path) -> dict[str, str]:
    mission_path = mission_dir / "mission.json"
    evidence_path = mission_dir / "evidence.jsonl"
    return {
        "mission": "sha256:" + hashlib.sha256(
            mission_path.read_bytes() if mission_path.exists() else b""
        ).hexdigest(),
        "evidence": "sha256:" + hashlib.sha256(
            evidence_path.read_bytes() if evidence_path.exists() else b""
        ).hexdigest(),
    }


def _host_guard_snapshot(guard: dict[str, Any] | None) -> dict[str, Any] | None:
    if guard is None:
        return None
    return {
        "phase": guard.get("phase"),
        "revision": guard.get("revision"),
    }


def _trace_message_ref(profile: HostProfile, kind: str | None, payload: dict[str, Any]) -> str | None:
    if kind != "message":
        return None
    try:
        return _message_ref(profile, payload)
    except TplanError:
        return None


def _host_result_kind(result: dict[str, Any]) -> str:
    if not result:
        return "allow"
    if "systemMessage" in result:
        return "turn_end_warning"
    if "decision" in result:
        return "operator_block" if result.get("decision") == "block" else "deny"
    hook_output = result.get("hookSpecificOutput")
    if isinstance(hook_output, dict):
        if hook_output.get("permissionDecision") == "deny":
            return "deny_tool"
        if "additionalContext" in hook_output:
            return "guard_context"
    return "other"


def _profile_digest(profile: HostProfile) -> str:
    payload = {
        "platform": profile.platform,
        "profile_id": profile.profile_id,
        "message_event": profile.message_event,
        "before_tool_event": profile.before_tool_event,
        "turn_end_event": profile.turn_end_event,
        "session_start_event": profile.session_start_event,
        "read_only_tools": sorted(profile.read_only_tools),
        "safe_control_tools": sorted(profile.safe_control_tools),
        "native_turn_id": profile.native_turn_id,
        "stable_message_identity": profile.stable_message_identity,
        "release_strategy": profile.release_strategy,
        "resume_strategy": profile.resume_strategy,
        "certified": profile.certified,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _new_host_trace_context(profile: HostProfile, mission_dir: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
    kind = _event_kind(profile, payload.get("hook_event_name"))
    if kind is None:
        return None
    event_name = {
        "session_start": profile.session_start_event,
        "message": profile.message_event,
        "before_tool": profile.before_tool_event,
        "turn_end": profile.turn_end_event,
    }[kind]
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "platform": profile.platform,
        "profile_id": profile.profile_id,
        "host": {
            "profile_digest": _profile_digest(profile),
            "build": "unavailable",
            "hook_sources": "unavailable",
        },
        "event_name": event_name,
        "event_kind": kind,
        "event_id_hash": _hash_host_ref(payload.get("event_id") or payload.get("message_id")),
        "session_id_hash": _hash_host_ref(payload.get("session_id")),
        "turn_id_hash": _hash_host_ref(payload.get("turn_id")),
        "message_ref_hash": _hash_host_ref(_trace_message_ref(profile, kind, payload)),
        "guard_before": _host_guard_snapshot(read_interaction_guard(mission_dir)),
        "boundary_before": _host_boundary_digests(mission_dir),
    }


def _append_host_trace(
    mission_dir: Path,
    context: dict[str, Any],
    result: dict[str, Any],
    *,
    state_dir: Path | None = None,
) -> None:
    """Append a sanitized lifecycle observation; it never controls Guard resolution."""

    trace_path = _host_trace_path(mission_dir, state_dir)
    record = {
        "schema_version": HOST_TRACE_SCHEMA_VERSION,
        "trace_seq": 0,
        **context,
        "guard_after": _host_guard_snapshot(read_interaction_guard(mission_dir)),
        "boundary_after": _host_boundary_digests(mission_dir),
        "result_kind": _host_result_kind(result),
    }
    with _host_trace_lock(mission_dir, state_dir):
        if trace_path.exists():
            with trace_path.open("r", encoding="utf-8") as handle:
                prior_records = [json.loads(line) for line in handle if line.strip()]
            for expected_seq, prior in enumerate(prior_records, start=1):
                if (
                    not isinstance(prior, dict)
                    or prior.get("schema_version") != HOST_TRACE_SCHEMA_VERSION
                    or prior.get("trace_seq") != expected_seq
                ):
                    raise TplanError("interaction host trace is invalid; refusing to append")
            record["trace_seq"] = len(prior_records) + 1
        else:
            record["trace_seq"] = 1
        with trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        if os.name != "nt":
            trace_path.chmod(0o600)


def _message_ref(profile: HostProfile, payload: dict[str, Any]) -> str:
    session_id = _safe_ref(payload.get("session_id"), "session_id")
    for field in ("event_id", "message_id", "message_uuid"):
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return f"{profile.platform}:{session_id}:{_safe_ref(value, field)}"
    prompt = payload.get("prompt") if isinstance(payload.get("prompt"), str) else ""
    stable_turn_part = ":".join(
        str(item)
        for item in (payload.get("turn_id") or "", payload.get("timestamp") or "", prompt)
    )
    digest = hashlib.sha256(f"{profile.platform}:{session_id}:{stable_turn_part}".encode("utf-8")).hexdigest()[:24]
    return f"{profile.platform}:{digest}"


def _is_read_only_tool(profile: HostProfile, tool_name: Any) -> bool:
    return isinstance(tool_name, str) and tool_name in profile.read_only_tools


def _is_safe_control_tool(profile: HostProfile, tool_name: Any) -> bool:
    return isinstance(tool_name, str) and tool_name in profile.safe_control_tools


def _additional_context(profile: HostProfile, text: str) -> dict[str, Any]:
    if profile.platform == "gemini-cli":
        return {"hookSpecificOutput": {"additionalContext": text}}
    return {
        "hookSpecificOutput": {
            "hookEventName": profile.message_event,
            "additionalContext": text,
        }
    }


def _block_message(profile: HostProfile, reason: str) -> dict[str, Any]:
    return {"decision": "deny" if profile.platform == "gemini-cli" else "block", "reason": reason}


def _deny_tool(profile: HostProfile, reason: str) -> dict[str, Any]:
    if profile.platform == "gemini-cli":
        return {"decision": "deny", "reason": reason}
    return {
        "hookSpecificOutput": {
            "hookEventName": profile.before_tool_event,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _turn_end_warning(text: str) -> dict[str, Any]:
    return {"systemMessage": text}


def _finish_turn(mission_dir: Path, profile: HostProfile, session_id: str, state_dir: Path | None) -> bool:
    with _host_state_lock(mission_dir, state_dir):
        state = _read_host_state(mission_dir, state_dir)
        if state is None:
            return True
        if state["platform"] != profile.platform or state["session_id"] != session_id:
            return False
        _write_host_state(mission_dir, None, state_dir)
        return True


def _orphan_for_legacy_state(mission_dir: Path, state: dict[str, Any], state_dir: Path | None) -> None:
    if not state.get("legacy_continuation_state"):
        return
    guard = read_interaction_guard(mission_dir)
    if guard is not None:
        try:
            orphan_interaction_guard(
                mission_dir,
                guard_id=guard["guard_id"],
                expected_revision=guard["revision"],
                reason="legacy_continuation_state",
            )
        except TplanError:
            pass
    state["legacy_continuation_state"] = False
    state["last_failure"] = "legacy_continuation_state"
    _write_host_state(mission_dir, state, state_dir)


def _orphan_stale_session_start(mission_dir: Path, profile: HostProfile, state_dir: Path | None) -> None:
    """A new host session never guesses that a persisted active turn ended cleanly."""

    with _host_state_lock(mission_dir, state_dir):
        state = _read_host_state(mission_dir, state_dir)
        if state is None or state.get("platform") != profile.platform:
            return
        prior_session_id = state["session_id"]
    guard = read_interaction_guard(mission_dir)
    if guard is not None and guard.get("platform") == profile.platform and guard.get("binding_id") == prior_session_id:
        try:
            orphan_interaction_guard(
                mission_dir,
                guard_id=guard["guard_id"],
                expected_revision=guard["revision"],
                reason="host_session_restart",
            )
        except TplanError:
            pass
    with _host_state_lock(mission_dir, state_dir):
        state = _read_host_state(mission_dir, state_dir)
        if state is not None and state.get("platform") == profile.platform and state.get("session_id") == prior_session_id:
            _write_host_state(mission_dir, None, state_dir)


def _start_or_interrupt_turn(
    profile: HostProfile,
    mission_dir: Path,
    session_id: str,
    message_ref: str,
    turn_id: str | None,
    state_dir: Path | None,
) -> tuple[str, dict[str, Any] | None]:
    """Return normal/duplicate/interrupt/conflict without any continuation path."""

    with _host_state_lock(mission_dir, state_dir):
        state = _read_host_state(mission_dir, state_dir)
        if state is not None:
            _orphan_for_legacy_state(mission_dir, state, state_dir)
            state = _read_host_state(mission_dir, state_dir)
        guard = read_interaction_guard(mission_dir)
        if guard is not None:
            if guard.get("platform") != profile.platform or guard.get("binding_id") != session_id:
                return "conflict", guard
            if guard.get("phase") == "orphaned":
                return "orphaned", guard
            if any(message["message_ref"] == message_ref for message in guard["messages"]):
                return "duplicate", guard
            opened = begin_interaction_guard(
                mission_dir,
                platform=profile.platform,
                platform_profile_id=profile.profile_id,
                binding_id=session_id,
                message_ref=message_ref,
                owner_turn_id=turn_id,
                opened_event_id=f"message:{message_ref}",
                event_seq=(state["event_seq"] + 1) if state else 1,
            )
            if state is None:
                state = _new_host_state(profile, session_id, message_ref, turn_id)
            else:
                state["event_seq"] += 1
                state["last_message_ref"] = message_ref
                state["active_turn_id"] = turn_id
            state["guard_id"] = opened["guard_id"]
            state["guard_turn_id"] = turn_id
            _write_host_state(mission_dir, state, state_dir)
            return "interrupt", opened
        if state is None:
            _write_host_state(mission_dir, _new_host_state(profile, session_id, message_ref, turn_id), state_dir)
            return "normal", None
        if state["platform"] != profile.platform or state["session_id"] != session_id:
            conflict_binding = f"conflict:{state['session_id']}:{session_id}"
            opened = begin_interaction_guard(
                mission_dir,
                platform="tplan-conflict",
                platform_profile_id="tplan-conflict@v0.2",
                binding_id=conflict_binding,
                message_ref=message_ref,
                owner_turn_id=turn_id,
                opened_event_id=f"conflict:{message_ref}",
                event_seq=state["event_seq"] + 1,
            )
            resolve_interaction_guard(
                mission_dir,
                guard_id=opened["guard_id"],
                expected_revision=opened["revision"],
                message_refs=[message_ref],
                disposition="await_clarification",
            )
            return "conflict", read_interaction_guard(mission_dir)
        if state["last_message_ref"] == message_ref:
            return "duplicate", None
        opened = begin_interaction_guard(
            mission_dir,
            platform=profile.platform,
            platform_profile_id=profile.profile_id,
            binding_id=session_id,
            message_ref=message_ref,
            owner_turn_id=turn_id,
            opened_event_id=f"message:{message_ref}",
            event_seq=state["event_seq"] + 1,
        )
        state["event_seq"] += 1
        state["last_message_ref"] = message_ref
        state["active_turn_id"] = turn_id
        state["guard_id"] = opened["guard_id"]
        state["guard_turn_id"] = turn_id
        state["last_failure"] = None
        _write_host_state(mission_dir, state, state_dir)
        return "interrupt", opened


def _control_envelope(
    profile: HostProfile, mission_dir: Path, session_id: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        return None
    match = CONTROL_ENVELOPE.fullmatch(prompt.strip())
    if match is None:
        return None
    guard = read_interaction_guard(mission_dir)
    if guard is None:
        return _block_message(profile, "No TPlan guard is open for this recovery command.")
    if guard.get("platform") != profile.platform or guard.get("binding_id") != session_id:
        return _block_message(profile, "This TPlan recovery command is not from the guard-owning host session.")
    if guard["guard_id"] != match["guard"] or guard["revision"] != int(match["revision"]):
        return _block_message(profile, "TPlan recovery command is stale; inspect the current guard and retry.")
    try:
        refs = [message["message_ref"] for message in guard["messages"] if message.get("status") == "pending"]
        if match["action"] == "resume":
            resolve_interaction_guard(
                mission_dir,
                guard_id=guard["guard_id"],
                expected_revision=guard["revision"],
                message_refs=refs,
                disposition="resume_original",
            )
            return _block_message(profile, "TPlan guard resumed the unchanged original path.")
        task_id = guard.get("baseline_active_task_id")
        if not isinstance(task_id, str):
            return _block_message(profile, "TPlan cannot fixed-stop a guard without a baseline active task.")
        stop_interaction_guard(
            mission_dir,
            guard_id=guard["guard_id"],
            expected_revision=guard["revision"],
            message_refs=refs,
            task_id=task_id,
            summary="User invoked TPlan fixed-stop recovery.",
            payload={
                "current_goal": "Preserve the baseline Mission path until explicit human direction is available.",
                "attempts": ["Opened a TPlan interaction guard.", "Processed a user recovery stop command."],
                "blocking_issue": "The user requested an immediate safe stop.",
                "why_cannot_continue_safely": "Continuing or changing the path would exceed the fixed-stop recovery boundary.",
                "need_from_human": "Provide the next explicit Mission instruction when ready.",
                "resume_condition": "A new explicit Mission instruction is received.",
            },
        )
        return _block_message(profile, "TPlan Mission safely stopped and now requires human input.")
    except TplanError as exc:
        return _block_message(profile, f"TPlan recovery command did not change the Mission: {exc}")


def _handle_hook(
    platform: str,
    mission_dir: Path,
    payload: dict[str, Any],
    *,
    state_dir: Path | None = None,
) -> dict[str, Any]:
    try:
        profile = profile_for(platform)
    except ValueError as exc:
        raise TplanError(str(exc)) from exc
    kind = _event_kind(profile, payload.get("hook_event_name"))
    if kind is None:
        return {}
    if kind == "session_start":
        _orphan_stale_session_start(mission_dir, profile, state_dir)
        orphan_expired_interaction_guard(mission_dir)
        return {}
    session_id = _safe_ref(payload.get("session_id"), "session_id")
    raw_turn_id = payload.get("turn_id")
    turn_id = _safe_ref(raw_turn_id, "turn_id") if isinstance(raw_turn_id, str) else None

    if kind == "message":
        orphan_expired_interaction_guard(mission_dir)
        operator_result = _control_envelope(profile, mission_dir, session_id, payload)
        if operator_result is not None:
            _finish_turn(mission_dir, profile, session_id, state_dir)
            return operator_result
        message_ref = _message_ref(profile, payload)
        try:
            status, guard = _start_or_interrupt_turn(profile, mission_dir, session_id, message_ref, turn_id, state_dir)
        except TplanError as exc:
            return _block_message(profile, f"TPlan remains fail-closed: {exc}")
        if status == "normal":
            return {}
        if status == "duplicate":
            return _additional_context(profile, "TPlan ignored a duplicate prompt-hook delivery.")
        if status == "conflict":
            return _block_message(profile, "TPlan detected competing host ownership; Mission mutation is fail-closed.")
        if status == "orphaned":
            assert guard is not None
            return _additional_context(
                profile,
                (
                    f"TPlan guard {guard['guard_id']} revision {guard['revision']} is orphaned. "
                    "Answer read-only. The Agent-safe controls are exactly "
                    "mcp__tplan_guard__inspect, mcp__tplan_guard__await_proposal, and "
                    "mcp__tplan_guard__stop_fixed; discover the MCP tools if they are not already visible. "
                    f"Operator recovery is TPLAN_CONTROL guard={guard['guard_id']} "
                    f"revision={guard['revision']} action=resume|stop."
                ),
            )
        assert guard is not None
        return _additional_context(
            profile,
            (
                f"TPlan guard {guard['guard_id']} revision {guard['revision']} is active. "
                "Answer the message read-only. Mission and worktree mutation remain blocked; "
                "the first owning turn-end will restore the unchanged baseline unless a safe control disposition runs. "
                "The Agent-safe controls are exactly mcp__tplan_guard__inspect, "
                "mcp__tplan_guard__await_proposal, and mcp__tplan_guard__stop_fixed; discover the MCP tools "
                "if they are not already visible. "
                f"Operator recovery is TPLAN_CONTROL guard={guard['guard_id']} "
                f"revision={guard['revision']} action=resume|stop."
            ),
        )

    owner_turn_id = None
    if kind == "turn_end" and profile.native_turn_id:
        with _host_state_lock(mission_dir, state_dir):
            state = _read_host_state(mission_dir, state_dir)
            owner_turn_id = state.get("guard_turn_id") if state is not None else None

    orphan_expired_interaction_guard(mission_dir)
    guard = read_interaction_guard(mission_dir)
    if guard is None:
        if kind == "turn_end" and not _finish_turn(mission_dir, profile, session_id, state_dir):
            return _turn_end_warning("Another host session owns the active TPlan turn marker.")
        return {}
    if guard.get("platform") != profile.platform or guard.get("binding_id") != session_id:
        if kind == "before_tool" and not _is_read_only_tool(profile, payload.get("tool_name")):
            return _deny_tool(profile, "A TPlan guard belongs to another host session; mutation is fail-closed.")
        return _turn_end_warning("A TPlan guard belongs to another host session and remains recoverable but locked.")

    if kind == "before_tool":
        if _is_read_only_tool(profile, payload.get("tool_name")) or _is_safe_control_tool(profile, payload.get("tool_name")):
            return {}
        return _deny_tool(
            profile,
            "TPlan is handling an interruption; only fixed read-only and safe guard-control tools are available.",
        )

    if profile.native_turn_id:
        if turn_id is None or owner_turn_id != turn_id:
            try:
                orphan_interaction_guard(mission_dir, reason="non_owning_turn_end")
            except TplanError:
                pass
            _finish_turn(mission_dir, profile, session_id, state_dir)
            return _turn_end_warning("TPlan received a non-owning turn end; Mission remains locked for operator recovery.")

    try:
        result = resolve_guard_at_turn_end(mission_dir, platform=profile.platform, binding_id=session_id)
    except TplanError as exc:
        try:
            orphan_interaction_guard(mission_dir, reason="turn_end_resolution_failed")
        except TplanError:
            pass
        _finish_turn(mission_dir, profile, session_id, state_dir)
        return _turn_end_warning(f"TPlan could not resolve this guard; Mission remains locked for recovery: {exc}")
    _finish_turn(mission_dir, profile, session_id, state_dir)
    if result.get("disposition") == "resume_original":
        return {}
    return _turn_end_warning(
        f"TPlan guard {result.get('guard_id')} remains {result.get('phase', 'locked')} awaiting an explicit recovery disposition."
    )


def handle_hook(
    platform: str,
    mission_dir: Path,
    payload: dict[str, Any],
    *,
    state_dir: Path | None = None,
) -> dict[str, Any]:
    """Run a hook without ever converting a turn-end failure into continuation."""

    profile = profile_for(platform)
    try:
        trace_context = _new_host_trace_context(profile, mission_dir, payload)
    except (OSError, ValueError, TplanError):
        # Telemetry acquisition cannot control normal recovery. A missing context
        # simply leaves this callback unavailable for host certification.
        trace_context = None
    try:
        result = _handle_hook(platform, mission_dir, payload, state_dir=state_dir)
    except Exception as exc:
        if payload.get("hook_event_name") != profile.turn_end_event:
            raise
        try:
            orphan_interaction_guard(mission_dir, reason="turn_end_hook_exception")
        except (OSError, ValueError, TplanError):
            pass
        result = _turn_end_warning(
            f"TPlan turn-end hook failed safely; Mission remains locked for recovery: {type(exc).__name__}."
        )
    try:
        if trace_context is not None:
            _append_host_trace(mission_dir, trace_context, result, state_dir=state_dir)
    except (OSError, ValueError, TplanError, json.JSONDecodeError):
        # Trace is certification evidence, not a new controller for safety recovery.
        # A failed append caps host certification but must not turn a completed stop or
        # direct release into another continuation or lockout path.
        pass
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a native platform hook against a TPlan Mission.")
    parser.add_argument("--platform", required=True, choices=sorted(PROFILES))
    parser.add_argument("--mission-dir", required=True)
    parser.add_argument("--state-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise TplanError("hook input must be a JSON object")
        result = handle_hook(args.platform, Path(args.mission_dir).resolve(), payload, state_dir=Path(args.state_dir).resolve())
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
