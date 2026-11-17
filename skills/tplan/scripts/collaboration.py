#!/usr/bin/env python3
"""Pure schema, validation, projection, and reducer for TPlan collaboration."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from typing import Any

from tplan_task_contract import TASK_STATUSES


PROTOCOL = "tplan.collaboration.command.v1"
SCHEMA = "tplan.collaboration.v0.1"
CAPABILITY = "tplan.collaboration.v0.1"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}\Z")
HASH = re.compile(r"sha256:[a-f0-9]{64}\Z")
MAX_REQUEST = 16 * 1024
MAX_SUMMARY = 2048
MAX_COMMANDS = 1024
MAX_COMMAND_STORE = 1024 * 1024
MAX_ARTIFACT = 4 * 1024 * 1024
MIN_FREE = 16 * 1024 * 1024
DEFAULT_MAX_PENDING_FEEDBACK = 128
DEFAULT_PROCESSING_DEADLINE_SECONDS = 900

ACTIONS = {
    "enable",
    "delegation.prepare",
    "dispatch.record",
    "feedback.record",
    "feedback.resolve",
    "coordination.checkpoint",
    "coordinator.handoff",
    "snapshot.get",
    "command.get",
    "runtime.recover",
}
READ_ACTIONS = {"snapshot.get", "command.get", "runtime.recover"}
COORDINATION_STATES = {"working", "waiting_external", "awaiting_owner"}
SEND_STATES = {"prepared", "confirmed", "unknown", "not_sent"}
EXECUTION_STATES = {"not_started", "running", "stopped", "completed", "failed", "unknown"}
DISPOSITIONS = {
    "answered",
    "adopted",
    "repair",
    "deferred",
    "evidence_requested",
    "path_adjusted",
    "out_of_scope",
}
FEEDBACK_KINDS = {"progress", "result", "review", "blocker", "question"}
FEEDBACK_KIND_RANK = {"progress": 0, "question": 0, "result": 1, "review": 1, "blocker": 2}
DELEGATION_STATUSES = {
    "prepared",
    "dispatched",
    "dispatch_unknown",
    "running",
    "stop_requested",
    "stopped",
    "not_sent",
    "executed",
    "failed",
    "accepted",
    "repair_required",
    "disposed",
}
UNRESOLVED_DELEGATION_STATUSES = {
    "prepared",
    "dispatched",
    "dispatch_unknown",
    "running",
    "stop_requested",
}
TERMINAL_TASK_STATUSES = {"completed", "pruned", "abandoned", "superseded"}
ALLOWED_TASK_TRANSITIONS = {
    "pending": set(TASK_STATUSES),
    "active": set(TASK_STATUSES) - {"pending"},
    "blocked": set(TASK_STATUSES) - {"pending"},
    "paused": set(TASK_STATUSES) - {"pending"},
    "completed": {"completed"},
    "pruned": {"pruned"},
    "abandoned": {"abandoned"},
    "superseded": {"superseded"},
}

EXITS = {
    "invalid_request": 2,
    "unsupported_capability": 3,
    "recovery_required": 4,
    "runtime_mismatch": 5,
    "mission_unavailable": 6,
    "invalid_state": 7,
    "runtime_unavailable": 8,
    "query_failed": 9,
    "capacity_exceeded": 10,
    "command_not_found": 11,
    "guard_open": 12,
    "command_conflict": 13,
    "outcome_unknown": 14,
    "stale_snapshot": 15,
    "stale_generation": 16,
    "feedback_conflict": 17,
    "association_required": 18,
    "execution_in_flight": 19,
    "review_required": 20,
    "repair_scope_required": 21,
}


class CollaborationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def parse_request(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_REQUEST:
        raise CollaborationError("invalid_request", "Collaboration request exceeds 16 KiB")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise CollaborationError("invalid_request", "Duplicate JSON keys")
            result[key] = value
        return result

    def constant(_: str) -> Any:
        raise CollaborationError("invalid_request", "Non-finite JSON values are unsupported")

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except CollaborationError:
        raise
    except (ValueError, RecursionError) as exc:
        raise CollaborationError("invalid_request", "Invalid collaboration request JSON") from exc
    if not isinstance(value, dict):
        raise CollaborationError("invalid_request", "Collaboration request must be an object")
    return value


def envelope(
    request: Any,
    *,
    status: str = "rejected",
    code: str | None = None,
    data: Any = None,
    message: str = "",
) -> dict[str, Any]:
    req = request if isinstance(request, dict) else {}
    return {
        "protocol": PROTOCOL,
        "mission_id": req.get("mission_id"),
        "command_id": req.get("command_id"),
        "action": req.get("action"),
        "ok": code is None,
        "status": status,
        "code": code,
        "message": message,
        "data": data,
    }


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and ID.fullmatch(value) is not None


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def _valid_time(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _exact_fields(value: Any, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CollaborationError("invalid_request", f"{label} must be an object")
    if set(value) != fields:
        missing = sorted(fields - set(value))
        extra = sorted(set(value) - fields)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unsupported " + ", ".join(extra))
        raise CollaborationError("invalid_request", f"{label} fields are invalid: {'; '.join(details)}")
    return value


def _text(value: Any, label: str, *, limit: int = 2048, one_line: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise CollaborationError("invalid_request", f"{label} must be non-empty and at most {limit} characters")
    if one_line and ("\n" in value or "\r" in value):
        raise CollaborationError("invalid_request", f"{label} must be one line")
    return value


def _ref(value: Any, label: str) -> str:
    return _text(value, label, limit=1000, one_line=True)


def _refs(value: Any, label: str, *, limit: int = 64) -> list[str]:
    if not isinstance(value, list) or len(value) > limit:
        raise CollaborationError("invalid_request", f"{label} must be a string list of at most {limit} items")
    return [_ref(item, f"{label} item") for item in value]


def _optional_ref(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _ref(value, label)


def _positive_int(value: Any, label: str, *, maximum: int = 1_000_000) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise CollaborationError("invalid_request", f"{label} must be an integer from 1 to {maximum}")
    return value


def validate_request(request: Any) -> None:
    fields = {
        "protocol",
        "action",
        "mission_id",
        "command_id",
        "expected_build_hash",
        "expected_snapshot",
        "payload",
    }
    if not isinstance(request, dict) or set(request) != fields:
        raise CollaborationError("invalid_request", "Use the exact tplan.collaboration.command.v1 fields")
    if request.get("protocol") != PROTOCOL:
        raise CollaborationError("invalid_request", "Collaboration protocol version is unsupported")
    action = request.get("action")
    if action not in ACTIONS:
        raise CollaborationError("invalid_request", "Collaboration action is unsupported")
    if not valid_id(request.get("mission_id")) or not valid_id(request.get("command_id")):
        raise CollaborationError("invalid_request", "Request identities are invalid")
    if not _valid_hash(request.get("expected_build_hash")):
        raise CollaborationError("invalid_request", "An exact runtime build hash is required")
    expected = request.get("expected_snapshot")
    if action in READ_ACTIONS:
        if expected is not None:
            raise CollaborationError("invalid_request", f"{action} requires expected_snapshot=null")
    elif not isinstance(expected, dict) or set(expected) != {"mission_digest", "evidence_digest"}:
        raise CollaborationError("invalid_request", "Mutation requires exact mission and evidence digests")
    elif not _valid_hash(expected.get("mission_digest")) or not _valid_hash(expected.get("evidence_digest")):
        raise CollaborationError("invalid_request", "Snapshot digests are invalid")
    if not isinstance(request.get("payload"), dict):
        raise CollaborationError("invalid_request", "payload must be an object")
    if action == "runtime.recover" and request["payload"] != {}:
        raise CollaborationError("invalid_request", "runtime.recover payload must be empty")
    try:
        encoded = canonical(request).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise CollaborationError("invalid_request", "Request contains unsupported JSON values") from exc
    if len(encoded) > MAX_REQUEST:
        raise CollaborationError("invalid_request", "Collaboration request exceeds 16 KiB")


def _validate_coordinator(value: Any, *, label: str = "coordinator") -> dict[str, Any]:
    fields = {"generation", "thread_ref", "host_ref", "responsibility", "communication_authorization_refs"}
    if isinstance(value, dict) and label == "coordinator payload":
        fields = fields - {"generation"}
    _exact_fields(value, fields, label)
    result = {
        "thread_ref": _ref(value["thread_ref"], f"{label} thread_ref"),
        "host_ref": _ref(value["host_ref"], f"{label} host_ref"),
        "responsibility": _text(value["responsibility"], f"{label} responsibility", limit=2048, one_line=True),
        "communication_authorization_refs": _refs(
            value["communication_authorization_refs"], f"{label} communication_authorization_refs"
        ),
    }
    if not result["communication_authorization_refs"]:
        raise CollaborationError("invalid_request", f"{label} requires at least one communication authorization reference")
    if "generation" in fields:
        result["generation"] = _positive_int(value["generation"], f"{label} generation")
    return result


def _new_state(payload: dict[str, Any], now: str) -> dict[str, Any]:
    _exact_fields(payload, {"coordinator", "participants", "policy"}, "enable payload")
    coordinator = _validate_coordinator(payload["coordinator"], label="coordinator payload")
    coordinator["generation"] = 1
    raw_participants = payload["participants"]
    if not isinstance(raw_participants, list) or len(raw_participants) > 64:
        raise CollaborationError("invalid_request", "participants must be a list of at most 64 entries")
    participants: dict[str, dict[str, Any]] = {}
    for raw in raw_participants:
        _exact_fields(
            raw,
            {"participant_id", "thread_ref", "host_ref", "responsibility", "communication_authorization_refs"},
            "participant",
        )
        participant_id = raw["participant_id"]
        if not valid_id(participant_id):
            raise CollaborationError("invalid_request", "participant_id is invalid")
        if participant_id in participants:
            raise CollaborationError("invalid_request", f"duplicate participant_id {participant_id}")
        participant = {
            "thread_ref": _ref(raw["thread_ref"], "participant thread_ref"),
            "host_ref": _ref(raw["host_ref"], "participant host_ref"),
            "responsibility": _text(raw["responsibility"], "participant responsibility", limit=2048, one_line=True),
            "communication_authorization_refs": _refs(
                raw["communication_authorization_refs"], "participant communication_authorization_refs"
            ),
        }
        if not participant["communication_authorization_refs"]:
            raise CollaborationError("invalid_request", "participant requires a communication authorization reference")
        participants[participant_id] = participant
    policy = payload["policy"]
    if not isinstance(policy, dict) or set(policy) - {"max_pending_feedback", "processing_deadline_seconds"}:
        raise CollaborationError("invalid_request", "policy must contain only supported optional fields")
    max_pending = _positive_int(
        policy.get("max_pending_feedback", DEFAULT_MAX_PENDING_FEEDBACK),
        "max_pending_feedback",
        maximum=1024,
    )
    deadline = _positive_int(
        policy.get("processing_deadline_seconds", DEFAULT_PROCESSING_DEADLINE_SECONDS),
        "processing_deadline_seconds",
        maximum=604800,
    )
    return {
        "schema_version": SCHEMA,
        "enabled_at": now,
        "coordinator": coordinator,
        "participants": participants,
        "policy": {
            "max_pending_feedback": max_pending,
            "processing_deadline_seconds": deadline,
        },
        "delegations": {},
        "intents": {},
        "feedback": {},
        "adoptions": {},
        "reviews": {},
        "coordination": {
            "state": "working",
            "focus_task_id": None,
            "gap_summary": "Collaboration enabled; A must record the current objective gap.",
            "next_action": "Continue the objective-relevant task and checkpoint the current gap.",
            "resume_basis": [],
            "waiting_on": [],
            "updated_at": now,
        },
        "commands": {},
    }


def _require_generation(collab: dict[str, Any], payload: dict[str, Any]) -> None:
    generation = payload.get("coordinator_generation")
    if isinstance(generation, bool) or not isinstance(generation, int):
        raise CollaborationError("invalid_request", "coordinator_generation must be an integer")
    if generation != collab["coordinator"]["generation"]:
        raise CollaborationError("stale_generation", "The coordinator generation is no longer current")


def _tasks(mission: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        task["id"]: task
        for task in mission.get("tasks", [])
        if isinstance(task, dict) and isinstance(task.get("id"), str)
    }


def _instruction_digest(payload: dict[str, Any]) -> str:
    return digest(
        {
            "task_id": payload["task_id"],
            "round": payload["round"],
            "assignee_id": payload["assignee_id"],
            "write_scope": payload["write_scope"],
            "contract_version": payload["contract_version"],
            "instruction_summary": payload["instruction_summary"],
            "input_refs": payload["input_refs"],
            "dependency_versions": payload["dependency_versions"],
            "required_review": payload["required_review"],
        }
    )


def _delegation_physically_in_flight(collab: dict[str, Any], delegation: dict[str, Any]) -> bool:
    """Physical write-scope occupancy from intent facts, independent of business disposition."""
    intent = collab.get("intents", {}).get(delegation.get("intent_id"), {})
    if intent.get("send_state") == "not_sent":
        return False
    if intent.get("execution_state") in {"stopped", "completed", "failed"}:
        return False
    return True


def _delegation_retired(collab: dict[str, Any], delegation: dict[str, Any]) -> bool:
    """A safely retired attempt carries no current completion responsibility."""
    intent = collab.get("intents", {}).get(delegation.get("intent_id"), {})
    if intent.get("send_state") == "not_sent":
        return True
    if intent.get("execution_state") in {"stopped", "failed"}:
        return True
    if delegation.get("status") in {"not_sent", "stopped", "failed", "superseded"}:
        return True
    return False


def _task_current_delegation(collab: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    """The current effective delegation for a task; retired history is excluded."""
    candidates = [
        delegation
        for delegation in collab.get("delegations", {}).values()
        if delegation.get("task_id") == task_id and not _delegation_retired(collab, delegation)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.get("round", 0), item.get("created_at", "")))


def _prepare_delegation(
    mission: dict[str, Any],
    payload: dict[str, Any],
    *,
    now: str,
    include_generation: bool,
) -> dict[str, Any]:
    fields = {
        "delegation_id",
        "intent_id",
        "task_id",
        "round",
        "assignee_id",
        "write_scope",
        "contract_version",
        "instruction_summary",
        "input_refs",
        "dependency_versions",
        "required_review",
    }
    if include_generation:
        fields.add("coordinator_generation")
    _exact_fields(payload, fields, "delegation payload")
    collab = mission["collaboration"]
    if include_generation:
        _require_generation(collab, payload)
    for field in ("delegation_id", "intent_id", "task_id", "assignee_id"):
        if not valid_id(payload[field]):
            raise CollaborationError("invalid_request", f"{field} is invalid")
    if payload["delegation_id"] in collab["delegations"]:
        raise CollaborationError("command_conflict", "delegation_id already exists")
    if payload["intent_id"] in collab["intents"]:
        raise CollaborationError("command_conflict", "intent_id already exists")
    tasks = _tasks(mission)
    task = tasks.get(payload["task_id"])
    if task is None:
        raise CollaborationError("invalid_request", "Delegation task does not exist")
    if task.get("status") in TERMINAL_TASK_STATUSES:
        raise CollaborationError("invalid_request", "Terminal tasks require a new bounded task before delegation")
    participant = collab["participants"].get(payload["assignee_id"])
    if participant is None:
        raise CollaborationError("invalid_request", "Delegation assignee is not configured")
    round_no = _positive_int(payload["round"], "round", maximum=100000)
    write_scope = _text(payload["write_scope"], "write_scope", limit=1000, one_line=True)
    contract_version = _text(payload["contract_version"], "contract_version", limit=1000, one_line=True)
    summary = _text(payload["instruction_summary"], "instruction_summary", limit=MAX_SUMMARY, one_line=True)
    input_refs = _refs(payload["input_refs"], "input_refs")
    dependencies = payload["dependency_versions"]
    if not isinstance(dependencies, dict) or len(dependencies) > 128 or not all(
        isinstance(key, str) and isinstance(value, str) and len(key) <= 200 and len(value) <= 500
        for key, value in dependencies.items()
    ):
        raise CollaborationError("invalid_request", "dependency_versions must map bounded strings to strings")
    review = _exact_fields(payload["required_review"], {"required", "reviewer_id", "scope_refs"}, "required_review")
    if not isinstance(review["required"], bool):
        raise CollaborationError("invalid_request", "required_review.required must be boolean")
    reviewer_id = review["reviewer_id"]
    scope_refs = _refs(review["scope_refs"], "required_review scope_refs")
    if review["required"]:
        if not valid_id(reviewer_id) or reviewer_id not in collab["participants"]:
            raise CollaborationError("invalid_request", "Required review needs a configured reviewer")
        if not scope_refs:
            raise CollaborationError("invalid_request", "Required review needs a non-empty scope")
    elif reviewer_id is not None or scope_refs:
        raise CollaborationError("invalid_request", "Optional review must use reviewer_id=null and empty scope_refs")
    for existing in collab["delegations"].values():
        if existing.get("task_id") != payload["task_id"] and existing.get("write_scope") != write_scope:
            continue
        if _delegation_physically_in_flight(collab, existing):
            raise CollaborationError(
                "execution_in_flight",
                "The same task or write scope still has a physically in-flight execution; reconcile or stop it before a new dispatch",
            )
    normalized = {
        "task_id": payload["task_id"],
        "round": round_no,
        "assignee_id": payload["assignee_id"],
        "write_scope": write_scope,
        "contract_version": contract_version,
        "instruction_summary": summary,
        "input_refs": input_refs,
        "dependency_versions": dict(sorted(dependencies.items())),
        "required_review": {"required": review["required"], "reviewer_id": reviewer_id, "scope_refs": scope_refs},
    }
    instruction_digest = _instruction_digest(normalized)
    collab["intents"][payload["intent_id"]] = {
        "intent_id": payload["intent_id"],
        "target_participant_id": payload["assignee_id"],
        "target_thread_ref": participant["thread_ref"],
        "instruction_digest": instruction_digest,
        "send_state": "prepared",
        "execution_state": "not_started",
        "stop_requested": False,
        "native_refs": [],
        "observed_at": now,
        "reason": "Intent prepared; no host send is implied",
        "created_at": now,
    }
    collab["delegations"][payload["delegation_id"]] = {
        "delegation_id": payload["delegation_id"],
        **normalized,
        "instruction_digest": instruction_digest,
        "intent_id": payload["intent_id"],
        "status": "prepared",
        "created_at": now,
        "disposition": None,
    }
    return {"delegation_id": payload["delegation_id"], "intent_id": payload["intent_id"]}


def _dispatch_status(intent: dict[str, Any]) -> str:
    execution = intent["execution_state"]
    send = intent["send_state"]
    if execution == "stopped":
        return "stopped"
    if execution == "failed":
        return "failed"
    if execution == "completed":
        return "executed"
    if send == "not_sent":
        return "not_sent"
    if send == "unknown" or execution == "unknown":
        return "dispatch_unknown"
    if execution == "running":
        return "stop_requested" if intent["stop_requested"] else "running"
    if send == "confirmed":
        return "dispatched"
    return "prepared"


def _record_dispatch(collab: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    _exact_fields(
        payload,
        {
            "coordinator_generation",
            "intent_id",
            "send_state",
            "execution_state",
            "stop_requested",
            "native_refs",
            "observed_at",
            "reason",
        },
        "dispatch payload",
    )
    _require_generation(collab, payload)
    intent = collab["intents"].get(payload["intent_id"])
    if intent is None:
        raise CollaborationError("invalid_request", "Dispatch intent does not exist")
    send_state = payload["send_state"]
    execution_state = payload["execution_state"]
    if send_state not in SEND_STATES or execution_state not in EXECUTION_STATES:
        raise CollaborationError("invalid_request", "Dispatch state is unsupported")
    if not isinstance(payload["stop_requested"], bool):
        raise CollaborationError("invalid_request", "stop_requested must be boolean")
    native_refs = _refs(payload["native_refs"], "native_refs")
    observed_at = payload["observed_at"]
    if not _valid_time(observed_at):
        raise CollaborationError("invalid_request", "observed_at must be an ISO timestamp")
    reason = _text(payload["reason"], "dispatch reason", limit=MAX_SUMMARY, one_line=True)
    old_send = intent["send_state"]
    allowed_send = {
        "prepared": {"prepared", "confirmed", "unknown", "not_sent"},
        "confirmed": {"confirmed"},
        "unknown": {"unknown", "confirmed", "not_sent"},
        "not_sent": {"not_sent"},
    }
    if send_state not in allowed_send[old_send]:
        raise CollaborationError("command_conflict", "Send-state transition conflicts with recorded facts")
    old_execution = intent["execution_state"]
    terminal_execution = {"stopped", "completed", "failed"}
    allowed_execution = {
        "not_started": {"not_started", "running", "stopped", "completed", "failed", "unknown"},
        "running": {"running", "stopped", "completed", "failed", "unknown"},
        "unknown": {"unknown", "running", "stopped", "completed", "failed"},
        "stopped": {"stopped"},
        "completed": {"completed"},
        "failed": {"failed"},
    }
    if execution_state not in allowed_execution[old_execution]:
        raise CollaborationError("command_conflict", "Execution-state transition conflicts with recorded facts")
    if old_execution in terminal_execution and execution_state != old_execution:
        raise CollaborationError("command_conflict", "Terminal execution facts cannot be rewritten")
    if intent["stop_requested"] and not payload["stop_requested"]:
        raise CollaborationError("command_conflict", "stop_requested cannot be cleared")
    effective_refs = native_refs or list(intent["native_refs"])
    if send_state == "confirmed" and not effective_refs:
        raise CollaborationError("invalid_request", "Confirmed dispatch requires a native reference")
    intent.update(
        {
            "send_state": send_state,
            "execution_state": execution_state,
            "stop_requested": payload["stop_requested"],
            "native_refs": effective_refs,
            "observed_at": observed_at,
            "reason": reason,
        }
    )
    delegation = collab["delegations"][intent["delegation_id"]] if "delegation_id" in intent else None
    if delegation is None:
        delegation = next(
            (item for item in collab["delegations"].values() if item.get("intent_id") == intent["intent_id"]),
            None,
        )
    if delegation is not None:
        delegation["status"] = _dispatch_status(intent)
    return {
        "intent_id": intent["intent_id"],
        "send_state": send_state,
        "execution_state": execution_state,
        "status": _dispatch_status(intent),
    }


def _feedback_content_digest(payload: dict[str, Any]) -> str:
    return digest(
        {
            "source_event_ref": payload["source_event_ref"],
            "summary": payload["summary"],
            "artifact_ref": payload["artifact_ref"],
            "artifact_digest": payload["artifact_digest"],
            "original_ref": payload["original_ref"],
            "attachment_refs": payload["attachment_refs"],
        }
    )


def _record_feedback(mission: dict[str, Any], payload: dict[str, Any], now: str) -> tuple[dict[str, Any], str]:
    required_fields = {
        "coordinator_generation",
        "source_event_ref",
        "source_thread_ref",
        "source_host_ref",
        "source_role_id",
        "delegation_id",
        "round",
        "contract_version",
        "artifact_ref",
        "artifact_digest",
        "summary",
        "original_ref",
        "attachment_refs",
    }
    if not isinstance(payload, dict):
        raise CollaborationError("invalid_request", "feedback payload must be an object")
    missing = required_fields - set(payload)
    unknown = set(payload) - required_fields - {"kind"}
    if missing or unknown:
        raise CollaborationError("invalid_request", "feedback payload fields are invalid")
    kind = payload.get("kind", "progress")
    if kind not in FEEDBACK_KINDS:
        raise CollaborationError("invalid_request", "feedback kind is unsupported")
    collab = mission["collaboration"]
    _require_generation(collab, payload)
    normalized = {
        "kind": kind,
        "source_event_ref": _ref(payload["source_event_ref"], "source_event_ref"),
        "source_thread_ref": _ref(payload["source_thread_ref"], "source_thread_ref"),
        "source_host_ref": _ref(payload["source_host_ref"], "source_host_ref"),
        "source_role_id": None if payload["source_role_id"] is None else _ref(payload["source_role_id"], "source_role_id"),
        "delegation_id": None if payload["delegation_id"] is None else _ref(payload["delegation_id"], "delegation_id"),
        "round": None,
        "contract_version": None if payload["contract_version"] is None else _ref(payload["contract_version"], "contract_version"),
        "artifact_ref": None if payload["artifact_ref"] is None else _ref(payload["artifact_ref"], "artifact_ref"),
        "artifact_digest": payload["artifact_digest"],
        "summary": _text(payload["summary"], "feedback summary", limit=MAX_SUMMARY, one_line=True),
        "original_ref": _ref(payload["original_ref"], "original_ref"),
        "attachment_refs": _refs(payload["attachment_refs"], "attachment_refs"),
    }
    if payload["round"] is not None:
        normalized["round"] = _positive_int(payload["round"], "feedback round", maximum=100000)
    if (normalized["artifact_ref"] is None) != (normalized["artifact_digest"] is None):
        raise CollaborationError("invalid_request", "artifact_ref and artifact_digest must appear together")
    if normalized["artifact_digest"] is not None and not _valid_hash(normalized["artifact_digest"]):
        raise CollaborationError("invalid_request", "artifact_digest must be sha256")
    content_digest = _feedback_content_digest(normalized)
    for existing in collab["feedback"].values():
        if existing.get("source_event_ref") != normalized["source_event_ref"]:
            continue
        if existing.get("content_digest") != content_digest:
            raise CollaborationError("feedback_conflict", "The source event identity already has different content")
        return {"feedback_id": existing["feedback_id"], "status": existing["status"]}, "no_change"
    pending_count = sum(1 for item in collab["feedback"].values() if item.get("status") == "pending")
    max_pending = min(
        int(collab["policy"]["max_pending_feedback"]),
        int(DEFAULT_MAX_PENDING_FEEDBACK),
    )
    if pending_count >= max_pending:
        raise CollaborationError("capacity_exceeded", "Pending collaboration feedback capacity is exhausted")
    association_gap = None
    association_status = "linked"
    delegation = None
    source_gap = None
    if normalized["source_role_id"] is not None:
        source_participant = collab["participants"].get(normalized["source_role_id"])
        if source_participant is None:
            source_gap = "source role is not configured"
        elif (
            source_participant["thread_ref"] != normalized["source_thread_ref"]
            or source_participant["host_ref"] != normalized["source_host_ref"]
        ):
            source_gap = "source thread/host does not match the claimed participant"
    if source_gap is not None:
        association_status = "needs_association"
        association_gap = source_gap
    elif normalized["delegation_id"] is None or normalized["round"] is None or normalized["contract_version"] is None:
        association_status = "needs_association"
        association_gap = "task/delegation round and contract version are required"
    else:
        delegation = collab["delegations"].get(normalized["delegation_id"])
        if delegation is None:
            association_status = "needs_association"
            association_gap = "delegation_id is not configured"
        elif normalized["round"] != delegation["round"] or normalized["contract_version"] != delegation["contract_version"]:
            association_status = "needs_association"
            association_gap = "round or contract version does not match the delegation"
    feedback_id = "F" + hashlib.sha256(
        (normalized["source_event_ref"] + "\0" + content_digest).encode("utf-8")
    ).hexdigest()[:16]
    if feedback_id in collab["feedback"]:
        raise CollaborationError("feedback_conflict", "Feedback identity collision")
    collab["feedback"][feedback_id] = {
        "feedback_id": feedback_id,
        **normalized,
        "content_digest": content_digest,
        "association_status": association_status,
        "association_gap": association_gap,
        "status": "pending",
        "recorded_at": now,
        "resolution": None,
    }
    return {
        "feedback_id": feedback_id,
        "association_status": association_status,
        "association_gap": association_gap,
        "status": "pending",
    }, "committed"


def _set_task_status_preserving_focus(mission: dict[str, Any], task_id: str, status: str) -> None:
    if status not in TASK_STATUSES:
        raise CollaborationError("invalid_request", "Task status is unsupported")
    task = _tasks(mission).get(task_id)
    if task is None:
        raise CollaborationError("invalid_request", "Task change references a missing task")
    current = task.get("status")
    if current not in TASK_STATUSES:
        raise CollaborationError("invalid_state", "Task has an unsupported current status")
    if status not in ALLOWED_TASK_TRANSITIONS.get(current, {status}):
        raise CollaborationError("invalid_request", f"Illegal task transition {current} -> {status}")
    focus = mission.get("active_task_id")
    task["status"] = status
    mission["active_task_id"] = focus


def _apply_coordination(mission: dict[str, Any], payload: dict[str, Any], now: str) -> dict[str, Any]:
    _exact_fields(
        payload,
        {"state", "focus_task_id", "gap_summary", "next_action", "resume_basis", "waiting_on", "rationale"},
        "coordination payload",
    )
    state = payload["state"]
    if state not in COORDINATION_STATES:
        raise CollaborationError("invalid_request", "Coordination state is unsupported")
    focus = payload["focus_task_id"]
    if focus is not None and not valid_id(focus):
        raise CollaborationError("invalid_request", "focus_task_id is invalid")
    if focus is not None:
        task = _tasks(mission).get(focus)
        if task is None or task.get("status") in TERMINAL_TASK_STATUSES:
            raise CollaborationError("invalid_request", "focus_task_id must name an existing non-terminal task")
    gap = _text(payload["gap_summary"], "gap_summary", limit=MAX_SUMMARY, one_line=True)
    next_action = _text(payload["next_action"], "next_action", limit=MAX_SUMMARY, one_line=True)
    resume_basis = _refs(payload["resume_basis"], "resume_basis")
    rationale = _text(payload["rationale"], "coordination rationale", limit=MAX_SUMMARY, one_line=True)
    raw_waiting = payload["waiting_on"]
    if not isinstance(raw_waiting, list) or len(raw_waiting) > 64:
        raise CollaborationError("invalid_request", "waiting_on must be a list of at most 64 entries")
    waiting: list[dict[str, str]] = []
    collab = mission["collaboration"]
    for item in raw_waiting:
        _exact_fields(item, {"kind", "ref", "condition"}, "waiting_on entry")
        kind = item["kind"]
        if kind not in {"delegation", "feedback", "owner"}:
            raise CollaborationError("invalid_request", "waiting_on kind is unsupported")
        ref = _ref(item["ref"], "waiting_on ref")
        if kind == "delegation" and ref not in collab["delegations"]:
            raise CollaborationError("invalid_request", "waiting_on delegation does not exist")
        if kind == "feedback" and ref not in collab["feedback"]:
            raise CollaborationError("invalid_request", "waiting_on feedback does not exist")
        waiting.append({"kind": kind, "ref": ref, "condition": _text(item["condition"], "waiting condition", one_line=True)})
    if state in {"waiting_external", "awaiting_owner"} and not waiting:
        raise CollaborationError("invalid_request", "Wait states require at least one waiting_on entry")
    collab["coordination"] = {
        "state": state,
        "focus_task_id": focus,
        "gap_summary": gap,
        "next_action": next_action,
        "resume_basis": resume_basis,
        "waiting_on": waiting,
        "updated_at": now,
    }
    mission["active_task_id"] = focus
    return {"state": state, "focus_task_id": focus, "next_action": next_action, "rationale": rationale}


def _validate_review(
    collab: dict[str, Any],
    review: dict[str, Any],
    feedback: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    _exact_fields(
        review,
        {
            "reviewer_id",
            "delegation_id",
            "round",
            "contract_version",
            "artifact_ref",
            "artifact_digest",
            "scope_refs",
            "verdict",
            "rationale",
        },
        "review",
    )
    reviewer_id = review["reviewer_id"]
    if not valid_id(reviewer_id) or reviewer_id not in collab["participants"]:
        raise CollaborationError("review_required", "Reviewer is not configured")
    reviewer = collab["participants"][reviewer_id]
    if (
        feedback.get("source_thread_ref") != reviewer["thread_ref"]
        or feedback.get("source_host_ref") != reviewer["host_ref"]
    ):
        raise CollaborationError("review_required", "Review source does not match the configured reviewer binding")
    delegation_id = review["delegation_id"]
    delegation = collab["delegations"].get(delegation_id)
    if delegation is None:
        raise CollaborationError("review_required", "Review delegation does not exist")
    round_no = _positive_int(review["round"], "review round", maximum=100000)
    contract_version = _text(review["contract_version"], "review contract_version", limit=1000, one_line=True)
    if round_no != delegation["round"] or contract_version != delegation["contract_version"]:
        raise CollaborationError("review_required", "Review is not for the current delegation contract and round")
    if feedback.get("delegation_id") != delegation_id:
        raise CollaborationError("review_required", "Review delegation must match the source feedback delegation")
    if feedback.get("round") != round_no:
        raise CollaborationError("review_required", "Review round must match the source feedback round")
    if feedback.get("contract_version") != contract_version:
        raise CollaborationError("review_required", "Review contract must match the source feedback contract")
    artifact_ref = _ref(review["artifact_ref"], "review artifact_ref")
    artifact_digest = review["artifact_digest"]
    if not _valid_hash(artifact_digest):
        raise CollaborationError("invalid_request", "review artifact_digest must be sha256")
    if feedback.get("artifact_ref") != artifact_ref or feedback.get("artifact_digest") != artifact_digest:
        raise CollaborationError("review_required", "Review artifact must match the source feedback artifact")
    scope_refs = _refs(review["scope_refs"], "review scope_refs")
    if not scope_refs:
        raise CollaborationError("review_required", "Review scope cannot be empty")
    required_scope = set(delegation["required_review"]["scope_refs"])
    if required_scope and not required_scope.issubset(set(scope_refs)):
        raise CollaborationError("review_required", "Review does not cover the required scope")
    verdict = review["verdict"]
    if verdict not in {"PASS", "FAIL"}:
        raise CollaborationError("invalid_request", "review verdict must be PASS or FAIL")
    review_id = "R" + hashlib.sha256(
        (feedback["feedback_id"] + "\0" + artifact_digest + "\0" + reviewer_id).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "review_id": review_id,
        "feedback_id": feedback["feedback_id"],
        "source_event_ref": feedback["source_event_ref"],
        "reviewer_id": reviewer_id,
        "delegation_id": delegation_id,
        "round": round_no,
        "contract_version": contract_version,
        "artifact_ref": artifact_ref,
        "artifact_digest": artifact_digest,
        "scope_refs": scope_refs,
        "verdict": verdict,
        "rationale": _text(review["rationale"], "review rationale", limit=MAX_SUMMARY, one_line=True),
        "recorded_at": now,
    }


def _resolve_feedback(
    mission: dict[str, Any],
    payload: dict[str, Any],
    *,
    before_mission: dict[str, Any],
    normalized_new_tasks: list[dict[str, Any]],
    now: str,
) -> dict[str, Any]:
    _exact_fields(
        payload,
        {
            "coordinator_generation",
            "feedback_id",
            "disposition",
            "goal_relation",
            "evidence_refs",
            "artifact_ref",
            "review",
            "task_changes",
            "new_tasks",
            "next_delegation",
            "coordination",
        },
        "feedback.resolve payload",
    )
    collab = mission["collaboration"]
    _require_generation(collab, payload)
    feedback = collab["feedback"].get(payload["feedback_id"])
    if feedback is None:
        raise CollaborationError("invalid_request", "Feedback does not exist")
    if feedback["status"] != "pending":
        raise CollaborationError("command_conflict", "Feedback was already resolved")
    disposition = payload["disposition"]
    if disposition not in DISPOSITIONS:
        raise CollaborationError("invalid_request", "Feedback disposition is unsupported")
    goal = _exact_fields(payload["goal_relation"], {"responsibility", "acceptance_ids", "rationale"}, "goal_relation")
    responsibility = _text(goal["responsibility"], "goal_relation responsibility", limit=MAX_SUMMARY, one_line=True)
    acceptance_ids = _refs(goal["acceptance_ids"], "goal_relation acceptance_ids")
    known_acceptance = {
        item["id"] for item in mission.get("mission", {}).get("acceptance_evidence", []) if isinstance(item, dict)
    }
    if any(item not in known_acceptance for item in acceptance_ids):
        raise CollaborationError("invalid_request", "goal_relation acceptance_ids must exist on the Mission")
    rationale = _text(goal["rationale"], "goal_relation rationale", limit=MAX_SUMMARY, one_line=True)
    evidence_refs = _refs(payload["evidence_refs"], "evidence_refs")
    artifact = payload["artifact_ref"]
    artifact_record = None
    if artifact is not None:
        _exact_fields(artifact, {"ref", "digest", "contract_version", "round"}, "artifact_ref")
        artifact_record = {
            "artifact_ref": _ref(artifact["ref"], "artifact_ref ref"),
            "artifact_digest": artifact["digest"],
            "contract_version": _text(artifact["contract_version"], "artifact contract_version", limit=1000, one_line=True),
            "round": _positive_int(artifact["round"], "artifact round", maximum=100000),
        }
        if not _valid_hash(artifact_record["artifact_digest"]):
            raise CollaborationError("invalid_request", "artifact digest must be sha256")
    if disposition == "adopted":
        if feedback["association_status"] != "linked":
            raise CollaborationError("association_required", "Adoption requires a linked feedback record")
        delegation = collab["delegations"][feedback["delegation_id"]]
        if artifact_record is None:
            raise CollaborationError("invalid_request", "Adoption requires artifact_ref")
        if (
            artifact_record["round"] != delegation["round"]
            or artifact_record["contract_version"] != delegation["contract_version"]
        ):
            raise CollaborationError("review_required", "Adopted artifact is not for the current contract and round")
        if feedback.get("artifact_ref") != artifact_record["artifact_ref"] or feedback.get("artifact_digest") != artifact_record["artifact_digest"]:
            raise CollaborationError("review_required", "Adopted artifact must match the source feedback")
        collab["adoptions"][feedback["delegation_id"]] = {
            "delegation_id": feedback["delegation_id"],
            "feedback_id": feedback["feedback_id"],
            "round": artifact_record["round"],
            "contract_version": artifact_record["contract_version"],
            "artifact_ref": artifact_record["artifact_ref"],
            "artifact_digest": artifact_record["artifact_digest"],
            "adopted_at": now,
        }
        delegation["status"] = "accepted"
        delegation["disposition"] = "adopted"
    review = payload["review"]
    if review is not None:
        if feedback["association_status"] != "linked":
            raise CollaborationError("association_required", "Review requires a linked feedback record")
        review_record = _validate_review(collab, review, feedback, now)
        existing_review = collab["reviews"].get(review_record["review_id"])
        if existing_review is not None and existing_review != review_record:
            raise CollaborationError("command_conflict", "Review history identity already has different content")
        collab["reviews"][review_record["review_id"]] = review_record
    task_changes = payload["task_changes"]
    if not isinstance(task_changes, list) or len(task_changes) > 64:
        raise CollaborationError("invalid_request", "task_changes must be a bounded list")
    for change in task_changes:
        _exact_fields(change, {"task_id", "status"}, "task change")
        task_id = change["task_id"]
        if not valid_id(task_id):
            raise CollaborationError("invalid_request", "task change task_id is invalid")
        _set_task_status_preserving_focus(mission, task_id, change["status"])
    if not isinstance(normalized_new_tasks, list) or len(normalized_new_tasks) > 64:
        raise CollaborationError("invalid_request", "new_tasks must be a bounded list")
    existing_ids = set(_tasks(mission))
    for task in normalized_new_tasks:
        if task.get("id") in existing_ids:
            raise CollaborationError("invalid_request", "new_tasks cannot replace existing task identities")
        existing_ids.add(task.get("id"))
        mission["tasks"].append(copy.deepcopy(task))
    if disposition == "repair" and feedback["association_status"] == "linked":
        delegation = collab["delegations"][feedback["delegation_id"]]
        task = _tasks(mission).get(delegation["task_id"])
        if task is not None and task.get("status") == "completed":
            if not any(
                item.get("kind") == "task" and item.get("role") == "success-critical"
                for item in normalized_new_tasks
            ):
                raise CollaborationError(
                    "repair_scope_required",
                    "Repairing a completed task requires a bounded success-critical repair task",
                )
        delegation["status"] = "repair_required"
        delegation["disposition"] = "repair"
    next_delegation = payload["next_delegation"]
    next_result = None
    if next_delegation is not None:
        next_result = _prepare_delegation(mission, next_delegation, now=now, include_generation=False)
    coordination_result = _apply_coordination(mission, payload["coordination"], now)
    feedback["status"] = "resolved"
    feedback["resolution"] = {
        "disposition": disposition,
        "goal_relation": {
            "responsibility": responsibility,
            "acceptance_ids": acceptance_ids,
            "rationale": rationale,
        },
        "evidence_refs": evidence_refs,
        "resolved_at": now,
    }
    if disposition not in {"adopted", "repair"} and feedback.get("delegation_id") in collab["delegations"]:
        collab["delegations"][feedback["delegation_id"]]["disposition"] = disposition
    completion = task_completion_findings(before_mission, mission)
    if completion:
        raise CollaborationError("review_required", "; ".join(completion))
    return {
        "feedback_id": feedback["feedback_id"],
        "disposition": disposition,
        "adoption": copy.deepcopy(collab["adoptions"].get(feedback.get("delegation_id"))),
        "review": copy.deepcopy(collab["reviews"].get(review_record["review_id"])) if review is not None else None,
        "task_changes": copy.deepcopy(task_changes),
        "new_task_ids": [item["id"] for item in normalized_new_tasks],
        "next_delegation": next_result,
        "coordination": coordination_result,
    }


def _record_command(
    collab: dict[str, Any],
    *,
    action: str,
    command_id: str,
    principal: str,
    request_digest: str,
    data: dict[str, Any],
    now: str,
) -> None:
    if command_id in collab["commands"]:
        raise CollaborationError("command_conflict", "Command identity already exists")
    if len(collab["commands"]) >= MAX_COMMANDS:
        raise CollaborationError("capacity_exceeded", "Collaboration command retention is full")
    commit_id = "CC" + hashlib.sha256((command_id + "\0" + request_digest).encode("utf-8")).hexdigest()[:12]
    collab["commands"][command_id] = {
        "command_id": command_id,
        "action": action,
        "principal": principal,
        "request_digest": request_digest,
        "commit_id": commit_id,
        "committed_at": now,
        "data": copy.deepcopy(data),
    }
    if len(canonical(collab["commands"]).encode("utf-8")) > MAX_COMMAND_STORE:
        raise CollaborationError("capacity_exceeded", "Collaboration command retention exceeds 1 MiB")


def apply_command(
    mission: dict[str, Any],
    *,
    action: str,
    payload: dict[str, Any],
    command_id: str,
    principal: str,
    request_digest: str,
    now: str,
    normalized_new_tasks: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    after = copy.deepcopy(mission)
    if action == "enable":
        if "collaboration" in after:
            raise CollaborationError("command_conflict", "Collaboration is already enabled")
        after["collaboration"] = _new_state(payload, now)
        data = {"enabled": True, "coordinator_generation": 1}
        command_status = "committed"
    else:
        collab = after.get("collaboration")
        if not isinstance(collab, dict):
            raise CollaborationError("unsupported_capability", "Collaboration is not enabled for this Mission")
        if action == "delegation.prepare":
            data = _prepare_delegation(after, payload, now=now, include_generation=True)
            command_status = "committed"
        elif action == "dispatch.record":
            data = _record_dispatch(collab, payload)
            command_status = "committed"
        elif action == "feedback.record":
            data, command_status = _record_feedback(after, payload, now)
        elif action == "feedback.resolve":
            data = _resolve_feedback(
                after,
                payload,
                before_mission=mission,
                normalized_new_tasks=normalized_new_tasks or [],
                now=now,
            )
            command_status = "committed"
        elif action == "coordination.checkpoint":
            generation = payload.get("coordinator_generation")
            if isinstance(generation, bool) or not isinstance(generation, int) or generation != collab["coordinator"]["generation"]:
                raise CollaborationError("stale_generation", "The coordinator generation is no longer current")
            coordination_payload = {key: value for key, value in payload.items() if key != "coordinator_generation"}
            data = _apply_coordination(after, coordination_payload, now)
            command_status = "committed"
        elif action == "coordinator.handoff":
            _exact_fields(payload, {"coordinator_generation", "coordinator", "rationale"}, "handoff payload")
            _require_generation(collab, payload)
            coordinator = _validate_coordinator(payload["coordinator"], label="coordinator payload")
            old_generation = collab["coordinator"]["generation"]
            coordinator["generation"] = old_generation + 1
            collab["coordinator"] = coordinator
            data = {
                "previous_generation": old_generation,
                "coordinator_generation": old_generation + 1,
                "rationale": _text(payload["rationale"], "handoff rationale", limit=MAX_SUMMARY, one_line=True),
            }
            command_status = "committed"
        else:
            raise CollaborationError("invalid_request", "Action is not a collaboration mutation")
    _record_command(
        after["collaboration"],
        action=action,
        command_id=command_id,
        principal=principal,
        request_digest=request_digest,
        data=data,
        now=now,
    )
    errors = validate_state(after)
    if errors:
        raise CollaborationError("invalid_state", "; ".join(errors))
    return after, data, command_status


def build_resume_view(mission: dict[str, Any]) -> dict[str, Any]:
    collab = mission.get("collaboration")
    if not isinstance(collab, dict):
        return {
            "objective": mission.get("mission", {}).get("objective"),
            "coordinator_responsibility": None,
            "focus_task_id": mission.get("active_task_id"),
            "acceptance_gaps": [],
            "pending_feedback": [],
            "external_pending": [],
            "waiting_on": [],
            "next_action": "Continue the ordinary TPlan path; collaboration is not enabled.",
        }
    tasks = _tasks(mission)
    acceptance_gaps = []
    for task in tasks.values():
        if task.get("role") != "success-critical" or task.get("status") == "completed":
            continue
        acceptance_gaps.append(
            {
                "task_id": task.get("id"),
                "status": task.get("status"),
                "acceptance_ids": list(task.get("acceptance_evidence", [])),
                "title": task.get("title"),
            }
        )
    pending_feedback = []
    for item in sorted(collab["feedback"].values(), key=lambda row: row["recorded_at"]):
        if item.get("status") != "pending":
            continue
        pending_feedback.append(
            {
                "feedback_id": item["feedback_id"],
                "source_event_ref": item["source_event_ref"],
                "source_thread_ref": item["source_thread_ref"],
                "delegation_id": item.get("delegation_id"),
                "association_status": item["association_status"],
                "association_gap": item.get("association_gap"),
                "summary": item["summary"],
                "artifact_ref": item.get("artifact_ref"),
                "kind": item.get("kind", "progress"),
            }
        )
    external_pending = []
    for delegation in collab["delegations"].values():
        if not _delegation_physically_in_flight(collab, delegation):
            continue
        intent = collab["intents"].get(delegation["intent_id"], {})
        external_pending.append(
            {
                "delegation_id": delegation["delegation_id"],
                "task_id": delegation["task_id"],
                "assignee_id": delegation["assignee_id"],
                "status": delegation["status"],
                "send_state": intent.get("send_state"),
                "execution_state": intent.get("execution_state"),
            }
        )
    next_action = collab["coordination"]["next_action"]
    needs_association = sum(1 for item in pending_feedback if item["association_status"] == "needs_association")
    return {
        "objective": mission.get("mission", {}).get("objective"),
        "coordinator_responsibility": collab["coordinator"]["responsibility"],
        "coordinator_generation": collab["coordinator"]["generation"],
        "focus_task_id": mission.get("active_task_id"),
        "acceptance_gaps": acceptance_gaps,
        "pending_feedback": pending_feedback,
        "pending_feedback_count": len(pending_feedback),
        "needs_association_count": needs_association,
        "external_pending": external_pending,
        "coordination_state": collab["coordination"]["state"],
        "waiting_on": copy.deepcopy(collab["coordination"]["waiting_on"]),
        "resume_basis": copy.deepcopy(collab["coordination"]["resume_basis"]),
        "next_action": next_action,
    }


def _required_review_findings(collab: dict[str, Any], delegation: dict[str, Any]) -> list[str]:
    delegation_id = delegation["delegation_id"]
    adoption = collab["adoptions"].get(delegation_id)
    if adoption is None:
        return [f"delegation {delegation_id} requires a current adopted artifact"]
    required = delegation["required_review"]
    if not required["required"]:
        return []
    matching = [
        review
        for review in collab["reviews"].values()
        if review.get("delegation_id") == delegation_id
        and review.get("round") == adoption["round"]
        and review.get("contract_version") == adoption["contract_version"]
        and review.get("artifact_ref") == adoption["artifact_ref"]
        and review.get("artifact_digest") == adoption["artifact_digest"]
        and review.get("reviewer_id") == required["reviewer_id"]
    ]
    if not matching:
        return [f"delegation {delegation_id} requires current reviewer PASS for the adopted artifact"]
    latest = matching[-1]
    if latest.get("verdict") != "PASS":
        return [
            f"delegation {delegation_id} current review for the adopted artifact is {latest.get('verdict')}; "
            "a later bounded repair/re-review PASS or explicit disposition is required before completion"
        ]
    return []


def completion_findings(mission: dict[str, Any]) -> list[str]:
    collab = mission.get("collaboration")
    if not isinstance(collab, dict):
        return []
    findings: list[str] = []
    pending = sorted(
        feedback_id for feedback_id, item in collab["feedback"].items() if item.get("status") == "pending"
    )
    if pending:
        findings.append("Mission completion requires pending collaboration feedback to be resolved: " + ", ".join(pending))
    tasks = _tasks(mission)
    for task_id, task in tasks.items():
        if task.get("status") != "completed":
            continue
        current = _task_current_delegation(collab, task_id)
        if current is None:
            continue
        findings.extend(_required_review_findings(collab, current))
    return findings

def task_completion_findings(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    collab = after.get("collaboration")
    if not isinstance(collab, dict):
        return []
    before_tasks = _tasks(before) if before else {}
    after_tasks = _tasks(after)
    findings: list[str] = []
    for task_id, task in after_tasks.items():
        previous = before_tasks.get(task_id, {}).get("status")
        if task.get("status") != "completed" or previous == "completed":
            continue
        pending = [
            item["feedback_id"]
            for item in collab["feedback"].values()
            if item.get("status") == "pending" and item.get("delegation_id") in collab["delegations"]
            and collab["delegations"][item["delegation_id"]]["task_id"] == task_id
        ]
        if pending:
            findings.append(f"task {task_id} completion requires pending feedback resolution: " + ", ".join(sorted(pending)))
        current = _task_current_delegation(collab, task_id)
        if current is not None:
            findings.extend(_required_review_findings(collab, current))
    return findings


def validate_transition(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    old = before.get("collaboration")
    new = after.get("collaboration")
    if old is None and new is None:
        return []
    if old is None:
        return []
    if new is None:
        return ["collaboration cannot be removed by this transition"]
    findings: list[str] = []
    for collection in ("feedback", "reviews", "commands"):
        for key, value in old[collection].items():
            if key not in new[collection]:
                findings.append(f"collaboration {collection} history cannot be removed: {key}")
                continue
            if collection == "feedback":
                comparable_old = copy.deepcopy(value)
                comparable_new = copy.deepcopy(new[collection][key])
                comparable_old["status"] = comparable_new["status"] = None
                comparable_old["resolution"] = comparable_new["resolution"] = None
                if comparable_old != comparable_new:
                    findings.append(f"collaboration feedback identity is immutable: {key}")
            elif old[collection][key] != new[collection][key]:
                findings.append(f"collaboration {collection} history is immutable: {key}")
    for key, value in old["intents"].items():
        if key not in new["intents"]:
            findings.append(f"collaboration intent cannot be removed: {key}")
            continue
        mutable = {"send_state", "execution_state", "stop_requested", "native_refs", "observed_at", "reason"}
        if {field: value[field] for field in set(value) - mutable} != {
            field: new["intents"][key][field] for field in set(new["intents"][key]) - mutable
        }:
            findings.append(f"collaboration intent identity is immutable: {key}")
    for key, value in old["delegations"].items():
        if key not in new["delegations"]:
            findings.append(f"collaboration delegation cannot be removed: {key}")
            continue
        mutable = {"status", "disposition"}
        if {field: value[field] for field in set(value) - mutable} != {
            field: new["delegations"][key][field] for field in set(new["delegations"][key]) - mutable
        }:
            findings.append(f"collaboration delegation identity is immutable: {key}")
    for key, value in old["participants"].items():
        if new["participants"].get(key) != value:
            findings.append(f"collaboration participant is immutable: {key}")
    if new["coordinator"]["generation"] < old["coordinator"]["generation"]:
        findings.append("coordinator generation cannot move backward")
    elif new["coordinator"]["generation"] == old["coordinator"]["generation"] and new["coordinator"] != old["coordinator"]:
        findings.append("coordinator can change only through a generation handoff")
    if new["policy"] != old["policy"]:
        findings.append("collaboration policy is immutable after enable")
    return findings


def validate_state(mission: Any) -> list[str]:
    if not isinstance(mission, dict):
        return ["mission state must be an object"]
    if "collaboration" not in mission:
        return []
    collab = mission.get("collaboration")
    if not isinstance(collab, dict):
        return ["collaboration must be an object"]
    findings: list[str] = []
    top_fields = {
        "schema_version",
        "enabled_at",
        "coordinator",
        "participants",
        "policy",
        "delegations",
        "intents",
        "feedback",
        "adoptions",
        "reviews",
        "coordination",
        "commands",
    }
    if set(collab) != top_fields:
        findings.append("collaboration fields are invalid")
        return findings
    if collab.get("schema_version") != SCHEMA:
        findings.append(f"collaboration schema_version must be {SCHEMA}")
    if not _valid_time(collab.get("enabled_at")):
        findings.append("collaboration enabled_at must be an ISO timestamp")
    coordinator = collab.get("coordinator")
    try:
        _validate_coordinator(coordinator, label="coordinator")
    except CollaborationError as exc:
        findings.append(f"collaboration coordinator invalid: {exc}")
    participants = collab.get("participants")
    if not isinstance(participants, dict):
        findings.append("collaboration participants must be an object")
        participants = {}
    for participant_id, participant in participants.items():
        if not valid_id(participant_id) or not isinstance(participant, dict):
            findings.append("collaboration participant identity is invalid")
            continue
        if set(participant) != {"thread_ref", "host_ref", "responsibility", "communication_authorization_refs"}:
            findings.append(f"collaboration participant {participant_id} fields are invalid")
    policy = collab.get("policy")
    if not isinstance(policy, dict) or set(policy) != {"max_pending_feedback", "processing_deadline_seconds"}:
        findings.append("collaboration policy fields are invalid")
    else:
        max_pending = policy.get("max_pending_feedback")
        deadline = policy.get("processing_deadline_seconds")
        if isinstance(max_pending, bool) or not isinstance(max_pending, int) or not 1 <= max_pending <= 1024:
            findings.append("collaboration max_pending_feedback is invalid")
        if isinstance(deadline, bool) or not isinstance(deadline, int) or not 1 <= deadline <= 604800:
            findings.append("collaboration processing_deadline_seconds is invalid")
    tasks = _tasks(mission)
    acceptance = {
        item.get("id") for item in mission.get("mission", {}).get("acceptance_evidence", []) if isinstance(item, dict)
    }
    delegations = collab.get("delegations")
    intents = collab.get("intents")
    if not isinstance(delegations, dict) or not isinstance(intents, dict):
        findings.append("collaboration delegations and intents must be objects")
        return findings
    for delegation_id, delegation in delegations.items():
        if set(delegation) != {
            "delegation_id", "task_id", "round", "assignee_id", "write_scope", "contract_version",
            "instruction_summary", "input_refs", "dependency_versions", "required_review",
            "instruction_digest", "intent_id", "status", "created_at", "disposition",
        }:
            findings.append(f"delegation {delegation_id} fields are invalid")
            continue
        if delegation_id != delegation.get("delegation_id"):
            findings.append(f"collaboration delegation key mismatch: {delegation_id}")
        if delegation.get("task_id") not in tasks:
            findings.append(f"delegation {delegation_id} task does not exist")
        if delegation.get("assignee_id") not in participants:
            findings.append(f"delegation {delegation_id} assignee does not exist")
        if delegation.get("intent_id") not in intents:
            findings.append(f"delegation {delegation_id} intent does not exist")
        if delegation.get("status") not in DELEGATION_STATUSES:
            findings.append(f"delegation {delegation_id} status is unsupported")
        review = delegation.get("required_review")
        if not isinstance(review, dict) or set(review) != {"required", "reviewer_id", "scope_refs"}:
            findings.append(f"delegation {delegation_id} required_review is invalid")
        else:
            if not isinstance(review.get("required"), bool):
                findings.append(f"delegation {delegation_id} required flag is invalid")
            if review.get("required") and review.get("reviewer_id") not in participants:
                findings.append(f"delegation {delegation_id} reviewer does not exist")
            if not isinstance(review.get("scope_refs"), list):
                findings.append(f"delegation {delegation_id} review scope is invalid")
    for intent_id, intent in intents.items():
        if set(intent) != {
            "intent_id", "target_participant_id", "target_thread_ref", "instruction_digest",
            "send_state", "execution_state", "stop_requested", "native_refs", "observed_at",
            "reason", "created_at",
        }:
            findings.append(f"collaboration intent {intent_id} fields are invalid")
            continue
        if intent_id != intent.get("intent_id"):
            findings.append(f"collaboration intent key mismatch: {intent_id}")
        if intent.get("send_state") not in SEND_STATES or intent.get("execution_state") not in EXECUTION_STATES:
            findings.append(f"collaboration intent {intent_id} state is unsupported")
        if intent.get("target_participant_id") not in participants:
            findings.append(f"collaboration intent {intent_id} target does not exist")
        if not isinstance(intent.get("stop_requested"), bool):
            findings.append(f"collaboration intent {intent_id} stop_requested is invalid")
        if not isinstance(intent.get("native_refs"), list):
            findings.append(f"collaboration intent {intent_id} native_refs is invalid")
        if not _valid_time(intent.get("created_at")) or not _valid_time(intent.get("observed_at")):
            findings.append(f"collaboration intent {intent_id} timestamps are invalid")
    feedback = collab.get("feedback")
    if not isinstance(feedback, dict):
        findings.append("collaboration feedback must be an object")
        feedback = {}
    source_refs: set[str] = set()
    for feedback_id, item in feedback.items():
        if set(item) != {
            "feedback_id", "kind", "source_event_ref", "source_thread_ref", "source_host_ref", "source_role_id",
            "delegation_id", "round", "contract_version", "artifact_ref", "artifact_digest",
            "content_digest", "summary", "original_ref", "attachment_refs", "association_status",
            "association_gap", "status", "recorded_at", "resolution",
        }:
            findings.append(f"collaboration feedback {feedback_id} fields are invalid")
            continue
        if feedback_id != item.get("feedback_id"):
            findings.append(f"collaboration feedback key mismatch: {feedback_id}")
        if item.get("source_event_ref") in source_refs:
            findings.append(f"duplicate collaboration source_event_ref {item.get('source_event_ref')}")
        source_refs.add(item.get("source_event_ref"))
        if item.get("status") not in {"pending", "resolved"}:
            findings.append(f"collaboration feedback {feedback_id} status is unsupported")
        if item.get("association_status") not in {"linked", "needs_association"}:
            findings.append(f"collaboration feedback {feedback_id} association is unsupported")
        if not _valid_hash(item.get("content_digest")):
            findings.append(f"collaboration feedback {feedback_id} content digest is invalid")
        if item.get("artifact_digest") is not None and not _valid_hash(item.get("artifact_digest")):
            findings.append(f"collaboration feedback {feedback_id} artifact digest is invalid")
        if not _valid_time(item.get("recorded_at")):
            findings.append(f"collaboration feedback {feedback_id} recorded_at is invalid")
        if item.get("association_status") == "needs_association" and not isinstance(item.get("association_gap"), str):
            findings.append(f"collaboration feedback {feedback_id} association gap is missing")
        if item.get("association_status") == "linked" and item.get("association_gap") is not None:
            findings.append(f"collaboration feedback {feedback_id} linked association gap must be null")
        if item.get("association_status") == "linked":
            delegation = delegations.get(item.get("delegation_id"))
            if delegation is None:
                findings.append(f"collaboration feedback {feedback_id} delegation does not exist")
            elif item.get("round") != delegation.get("round") or item.get("contract_version") != delegation.get("contract_version"):
                findings.append(f"collaboration feedback {feedback_id} association does not match delegation")
        resolution = item.get("resolution")
        if item.get("status") == "resolved":
            if not isinstance(resolution, dict) or resolution.get("disposition") not in DISPOSITIONS:
                findings.append(f"collaboration feedback {feedback_id} resolution is invalid")
            else:
                if set(resolution) != {"disposition", "goal_relation", "evidence_refs", "resolved_at"}:
                    findings.append(f"collaboration feedback {feedback_id} resolution fields are invalid")
                goal = resolution.get("goal_relation")
                if not isinstance(goal, dict):
                    findings.append(f"collaboration feedback {feedback_id} goal relation is invalid")
                elif any(ac not in acceptance for ac in goal.get("acceptance_ids", [])):
                    findings.append(f"collaboration feedback {feedback_id} acceptance reference is invalid")
        elif resolution is not None:
            findings.append(f"pending collaboration feedback {feedback_id} cannot have a resolution")
    adoptions = collab.get("adoptions")
    if not isinstance(adoptions, dict):
        findings.append("collaboration adoptions must be an object")
        adoptions = {}
    for delegation_id, adoption in adoptions.items():
        if set(adoption) != {
            "delegation_id", "feedback_id", "round", "contract_version", "artifact_ref",
            "artifact_digest", "adopted_at",
        }:
            findings.append(f"adoption {delegation_id} fields are invalid")
            continue
        if delegation_id not in delegations:
            findings.append(f"adoption {delegation_id} delegation does not exist")
        delegation = delegations.get(delegation_id, {})
        if adoption.get("delegation_id") != delegation_id:
            findings.append(f"adoption {delegation_id} identity is invalid")
        if adoption.get("feedback_id") not in feedback:
            findings.append(f"adoption {delegation_id} feedback does not exist")
        else:
            source = feedback[adoption["feedback_id"]]
            if (
                source.get("delegation_id") != delegation_id
                or source.get("artifact_ref") != adoption.get("artifact_ref")
                or source.get("artifact_digest") != adoption.get("artifact_digest")
            ):
                findings.append(f"adoption {delegation_id} does not match its source feedback")
        if (
            adoption.get("round") != delegation.get("round")
            or adoption.get("contract_version") != delegation.get("contract_version")
        ):
            findings.append(f"adoption {delegation_id} does not match the current delegation contract")
        if not _valid_hash(adoption.get("artifact_digest")):
            findings.append(f"adoption {delegation_id} artifact digest is invalid")
    reviews = collab.get("reviews")
    if not isinstance(reviews, dict):
        findings.append("collaboration reviews must be an object")
        reviews = {}
    for review_id, review in reviews.items():
        if set(review) != {
            "review_id", "feedback_id", "source_event_ref", "reviewer_id", "delegation_id", "round",
            "contract_version", "artifact_ref", "artifact_digest", "scope_refs", "verdict",
            "rationale", "recorded_at",
        }:
            findings.append(f"collaboration review {review_id} fields are invalid")
            continue
        if review_id != review.get("review_id"):
            findings.append(f"collaboration review key mismatch: {review_id}")
        if review.get("delegation_id") not in delegations or review.get("reviewer_id") not in participants:
            findings.append(f"collaboration review {review_id} references are invalid")
        source_feedback = feedback.get(review.get("feedback_id"))
        delegation = delegations.get(review.get("delegation_id"), {})
        reviewer = participants.get(review.get("reviewer_id"), {})
        if not isinstance(source_feedback, dict) or (
            source_feedback.get("source_thread_ref") != reviewer.get("thread_ref")
            or source_feedback.get("source_host_ref") != reviewer.get("host_ref")
        ):
            findings.append(f"collaboration review {review_id} source binding is invalid")
        if review.get("verdict") not in {"PASS", "FAIL"}:
            findings.append(f"collaboration review {review_id} verdict is invalid")
        if (
            review.get("round") != delegation.get("round")
            or review.get("contract_version") != delegation.get("contract_version")
            or not isinstance(source_feedback, dict)
            or review.get("source_event_ref") != source_feedback.get("source_event_ref")
            or review.get("artifact_ref") != source_feedback.get("artifact_ref")
            or review.get("artifact_digest") != source_feedback.get("artifact_digest")
            or review.get("delegation_id") != source_feedback.get("delegation_id")
            or review.get("round") != source_feedback.get("round")
            or review.get("contract_version") != source_feedback.get("contract_version")
        ):
            findings.append(f"collaboration review {review_id} does not match its source contract")
        if not _valid_hash(review.get("artifact_digest")):
            findings.append(f"collaboration review {review_id} artifact digest is invalid")
    coordination = collab.get("coordination")
    if not isinstance(coordination, dict) or set(coordination) != {
        "state", "focus_task_id", "gap_summary", "next_action", "resume_basis", "waiting_on", "updated_at"
    }:
        findings.append("collaboration coordination fields are invalid")
    else:
        if coordination.get("state") not in COORDINATION_STATES:
            findings.append("collaboration coordination state is invalid")
        focus = coordination.get("focus_task_id")
        if focus is not None and focus not in tasks:
            findings.append("collaboration focus task does not exist")
        if not _valid_time(coordination.get("updated_at")):
            findings.append("collaboration coordination updated_at is invalid")
        waiting = coordination.get("waiting_on")
        if not isinstance(waiting, list):
            findings.append("collaboration waiting_on must be a list")
        elif coordination.get("state") in {"waiting_external", "awaiting_owner"} and not waiting:
            findings.append("collaboration wait state requires waiting_on")
        elif any(
            not isinstance(item, dict)
            or set(item) != {"kind", "ref", "condition"}
            or item.get("kind") not in {"delegation", "feedback", "owner"}
            for item in waiting
        ):
            findings.append("collaboration waiting_on entries are invalid")
    commands = collab.get("commands")
    if not isinstance(commands, dict) or len(commands) > MAX_COMMANDS:
        findings.append("collaboration commands must be a bounded object")
    else:
        try:
            if len(canonical(commands).encode("utf-8")) > MAX_COMMAND_STORE:
                findings.append("collaboration command store exceeds 1 MiB")
        except (TypeError, ValueError, RecursionError):
            findings.append("collaboration command store is not finite JSON")
        for command_id, record in commands.items():
            if not valid_id(command_id) or record.get("command_id") != command_id:
                findings.append(f"collaboration command identity is invalid: {command_id}")
            if set(record) != {
                "command_id", "action", "principal", "request_digest", "commit_id", "committed_at", "data"
            }:
                findings.append(f"collaboration command fields are invalid: {command_id}")
            elif (
                not valid_id(record.get("principal"))
                or record.get("action") not in ACTIONS
                or not _valid_hash(record.get("request_digest"))
                or not _valid_time(record.get("committed_at"))
                or not isinstance(record.get("data"), dict)
            ):
                findings.append(f"collaboration command values are invalid: {command_id}")
    return findings
