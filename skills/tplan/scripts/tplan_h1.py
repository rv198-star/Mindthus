"""Optional H1-A scoped waiting invariants for the single TPlan Mission writer.

No Owner receipt, signer, dispatch, or approval capability is provided here.
This only protects new opt-in Missions against legacy writer bypasses.
"""
from __future__ import annotations

from typing import Any

SCHEMA = "tplan.h1.v0.1"
CAPABILITY = "task_scoped_owner_gate"
CHOICES = {"approve_current", "request_changes", "withdraw_change"}
STATUS = {"pending", "decided"}


def empty_state() -> dict[str, Any]:
    return {"schema_version": SCHEMA, "requests": {}, "candidates": {},
            "decisions": {}, "execution_slots": {}}


def pending_blocked_task_ids(state: dict[str, Any]) -> set[str]:
    control = state.get("human_control")
    if not isinstance(control, dict) or not isinstance(control.get("requests"), dict):
        return set()
    directly_blocked = {task for req in control["requests"].values()
                        if isinstance(req, dict) and req.get("status") == "pending"
                        for task in (req.get("blocked_task_ids")
                                     if isinstance(req.get("blocked_task_ids"), list) else [])
                        if isinstance(task, str)}
    # Team Tasks include subtasks/steps; a pending parent gate must cover them.
    blocked = set(directly_blocked)
    tasks = state.get("tasks") if isinstance(state.get("tasks"), list) else []
    for _ in range(len(tasks)):
        before = len(blocked)
        for task in tasks:
            if isinstance(task, dict) and isinstance(task.get("id"), str):
                parent = task.get("parent_id")
                if isinstance(parent, str) and parent in blocked:
                    blocked.add(task["id"])
        if len(blocked) == before:
            break
    return blocked


def validate_control(state: dict[str, Any]) -> list[str]:
    """Pure shape checks; a valid record is not an approved Owner decision."""
    if "human_control" not in state:
        return []
    value = state["human_control"]
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "requests", "candidates", "decisions", "execution_slots"
    } or value.get("schema_version") != SCHEMA:
        return ["H1 human_control schema is invalid"]
    errors = []
    for field in ("requests", "candidates", "decisions", "execution_slots"):
        if not isinstance(value[field], dict):
            errors.append(f"H1 {field} must be a mapping")
    if errors:
        return errors
    tasks = {t.get("id") for t in state.get("tasks", []) if isinstance(t, dict)}
    for key, req in value["requests"].items():
        if not isinstance(key, str) or not key or not isinstance(req, dict) or set(req) != {
            "business_task_id", "blocked_task_ids", "status", "revision", "required_actor",
            "allowed_choices", "current_candidate_id", "current_decision_id"
        }:
            errors.append("H1 request fields invalid")
            continue
        blocked = req["blocked_task_ids"]
        choices = req["allowed_choices"]
        if (not isinstance(req["business_task_id"], str)
            or req["business_task_id"] not in tasks
            or not isinstance(blocked, list) or not blocked
            or any(not isinstance(t, str) or t not in tasks for t in blocked)
            or (len(set(blocked)) != len(blocked)
                if isinstance(blocked, list) and all(isinstance(x,str) for x in blocked) else True)
            or req["business_task_id"] in blocked):
            errors.append(f"H1 request {key}: invalid business task or blocked dependencies")
        if (not isinstance(req["status"], str) or req["status"] not in STATUS
            or not isinstance(req["revision"], int)
            or isinstance(req["revision"], bool) or req["revision"] < 1
            or req["required_actor"] != "owner"
            or not isinstance(choices, list) or not choices
            or any(not isinstance(c,str) or c not in CHOICES for c in choices)
            or (len(set(choices)) != len(choices)
                if isinstance(choices,list) and all(isinstance(x,str) for x in choices) else True)):
            errors.append(f"H1 request {key}: invalid choice/status/revision")
        candidate_id = req["current_candidate_id"]
        if candidate_id is not None and (not isinstance(candidate_id, str)
                                         or candidate_id not in value["candidates"]):
            errors.append(f"H1 request {key}: candidate is not recorded")
        decision_id = req["current_decision_id"]
        if decision_id is not None and (not isinstance(decision_id, str)
                                        or decision_id not in value["decisions"]):
            errors.append(f"H1 request {key}: decision is not recorded")
        if req["status"] == "decided" and decision_id is None:
            errors.append(f"H1 request {key}: decided without a decision record")
    # Later slices will define full candidate/decision/slot schemas. Until then,
    # reject any external-looking payload rather than implying it is verified.
    if value["candidates"] or value["decisions"] or value["execution_slots"]:
        errors.append("H1-A does not support candidates, decisions or execution slots yet")
    return errors


def validate_transition(before: dict[str, Any], after: dict[str, Any], *,
                        authorized: bool = False) -> list[str]:
    """Compare before and after, so removing a waiting object cannot bypass it."""
    errors = []
    if "human_control" not in before and "human_control" not in after:
        # Existing non-H1 Missions continue through their established validators.
        return errors
    old = before.get("human_control")
    new = after.get("human_control")
    if old != new and not authorized:
        errors.append("H1 human_control is owned by the scoped authority")
    # Include both graphs. Re-parenting a pending child's parent in 'after'
    # must not remove it from the old waiting scope in the same legacy commit.
    pending = pending_blocked_task_ids(before) | pending_blocked_task_ids(after)
    before_tasks = {t["id"]: t for t in before.get("tasks", [])
                    if isinstance(t, dict) and isinstance(t.get("id"), str)}
    after_tasks = {t["id"]: t for t in after.get("tasks", [])
                   if isinstance(t, dict) and isinstance(t.get("id"), str)}
    for task_id in pending:
        prev, following = before_tasks.get(task_id), after_tasks.get(task_id)
        if prev is not None and following is None:
            errors.append(f"H1 pending task {task_id} cannot be removed")
        elif prev is not None and following != prev:
            errors.append(f"H1 pending task {task_id} cannot be changed by a legacy writer")
        elif following is not None and following.get("status") in {"active", "completed"}:
            errors.append(f"H1 pending task {task_id} cannot be active or completed")
    focus = after.get("active_task_id")
    if isinstance(focus, str) and focus in pending:
        errors.append("H1 pending task cannot become the active Mission focus")
    if pending and after.get("mission", {}).get("status") == "completed":
        errors.append("H1 pending human decision prevents Mission completion")
    return errors


def validate_evidence(state: dict[str, Any], event: dict[str, Any]) -> list[str]:
    if event.get("event_type") in {"acceptance", "acceptance_passed"}:
        if event.get("task_id") in pending_blocked_task_ids(state):
            return ["H1 pending Owner decision cannot be replaced by acceptance evidence"]
    return []
