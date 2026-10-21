"""Opt-in H1 invariants at the existing canonical Mission writer boundary.

Shape validation grants no authority. Protected Host command handling is separate;
ordinary Python/CLI identity is never Owner authentication.
"""
from __future__ import annotations

from typing import Any

SCHEMA = "tplan.h1.v0.1"
CAPABILITY = "task_scoped_owner_gate"
CHOICES = {"approve_current", "request_changes", "withdraw_change"}
STATUS = {"pending", "decided"}


def empty_state() -> dict[str, Any]:
    return {"schema_version": SCHEMA, "requests": {}, "candidates": {},
            "decisions": {}, "execution_slots": {}, "commands": {},
            "used_nonces": {}, "adoptions": {}, "authorization_rounds": {}}


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
        "schema_version", "requests", "candidates", "decisions", "execution_slots",
        "commands", "used_nonces", "adoptions", "authorization_rounds"
    } or value.get("schema_version") != SCHEMA:
        return ["H1 human_control schema is invalid"]
    errors = []
    for field in ("requests", "candidates", "decisions", "execution_slots", "commands",
                  "used_nonces", "adoptions", "authorization_rounds"):
        if not isinstance(value[field], dict):
            errors.append(f"H1 {field} must be a mapping")
    if errors:
        return errors
    tasks = {t["id"] for t in state.get("tasks", [])
             if isinstance(t, dict) and isinstance(t.get("id"), str)}
    for key, req in value["requests"].items():
        if not isinstance(key, str) or not key or not isinstance(req, dict) or set(req) != {
            "business_task_id", "blocked_task_ids", "status", "revision", "required_actor",
            "allowed_choices", "current_candidate_id", "current_decision_id", "fallback_candidate_id"
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
        fallback = req["fallback_candidate_id"]
        if fallback is not None and (not isinstance(fallback, str) or fallback not in value["candidates"]):
            errors.append(f"H1 request {key}: fallback candidate is not recorded")
        decision_id = req["current_decision_id"]
        if decision_id is not None and (not isinstance(decision_id, str)
                                        or decision_id not in value["decisions"]):
            errors.append(f"H1 request {key}: decision is not recorded")
        if req["status"] == "decided" and decision_id is None:
            errors.append(f"H1 request {key}: decided without a decision record")
    errors.extend(_validate_records(state))
    return errors


def controlled_task_ids(state: dict[str, Any], *, include_source=False) -> set[str]:
    control = state.get("human_control")
    if not isinstance(control, dict):
        return set()
    ids = set()
    for req in control.get("requests", {}).values():
        ids.update(req["blocked_task_ids"])
        if include_source:
            ids.add(req["business_task_id"])
    for _ in state.get("tasks", []):
        for task in state["tasks"]:
            if (isinstance(task.get("parent_id"), str) and task["parent_id"] in ids
                and isinstance(task.get("id"), str)):
                ids.add(task["id"])
    return ids


def protected_contract_task_ids(state: dict[str, Any]) -> set[str]:
    """Close the scoped writer contract over ancestors and declared prerequisites."""
    protected = controlled_task_ids(state, include_source=True)
    tasks = {t["id"]:t for t in state.get("tasks", [])
             if isinstance(t,dict) and isinstance(t.get("id"),str)}
    plan = state.get("work_plan", {})
    blocks = plan.get("blocks", []) if isinstance(plan,dict) else []
    blocks = blocks if isinstance(blocks,list) else []
    while True:
        previous = set(protected)
        for task_id in list(protected):
            parent = tasks.get(task_id, {}).get("parent_id")
            if isinstance(parent,str):
                protected.add(parent)
        for block in blocks:
            if isinstance(block,dict) and isinstance(block.get("task_id"),str) and block["task_id"] in protected:
                dependencies = block.get("depends_on")
                if isinstance(dependencies,list):
                    protected.update(t for t in dependencies if isinstance(t,str))
        if protected == previous:
            return protected


def source_acceptance(state, candidate, events):
    """Shared version-scoped acceptance for adoption, claim and Mission-close."""
    import tplan_runtime as runtime
    from tplan_commands import CommandError, HASH, valid_id
    source_id = candidate["task_id"]
    required = runtime._acceptance_coverage_for_task(state, source_id)
    failure_scope = {task["id"] for task in runtime.parent_chain(state, source_id)}
    latest = {}
    seen = set()
    for event in events:
        if event.get("id") in seen:
            raise CommandError("invalid_state", "Ambiguous evidence cannot prove a dependency")
        seen.add(event.get("id"))
        kind = event.get("event_type")
        if kind not in {"acceptance_passed", "acceptance_failed"}:
            continue
        if event.get("task_id") not in failure_scope:
            continue
        if kind == "acceptance_passed" and event["task_id"] != source_id:
            continue  # Parent success alone is not delivery of A's candidate.
        if runtime.validate_evidence_event(state, event, compatibility=True, internal=True):
            raise CommandError("invalid_state", "Source acceptance is not a qualified native record")
        payload = event["payload"]
        version = {"candidate_sha256":candidate["content_sha256"],"attempt_ref":candidate["attempt_ref"]}
        supplied = {key:payload[key] for key in version if key in payload}
        if kind == "acceptance_failed":
            # SHA-only and attempt-only failures are sufficient. Missing or
            # contradictory scope blocks conservatively; clearly other valid
            # versions do not invalidate the retained candidate.
            malformed = any(not (isinstance(value,str) and HASH.fullmatch(value))
                            if key == "candidate_sha256" else not valid_id(value)
                            for key,value in supplied.items())
            relevant = (not supplied or malformed or
                        any(value == version[key] for key,value in supplied.items()))
        else:
            relevant = all(payload.get(key) == value for key,value in version.items())
        if relevant:
            for ac in payload["acceptance_ids"]:
                latest[ac] = event
    return required, latest


def completion_findings(state: dict[str, Any], events=None) -> list[str]:
    control = state.get("human_control")
    if not isinstance(control, dict):
        return []
    for request_id, req in control["requests"].items():
        decision = control["decisions"].get(req["current_decision_id"], {})
        adoption = control["adoptions"].get(request_id, {})
        if (req["status"] != "decided" or decision.get("adoption_blocked")
            or adoption.get("decision_id") != req["current_decision_id"]):
            return ["H1 current Owner decision and adoption required for Mission completion"]
        for task_id in req["blocked_task_ids"]:
            slots = [slot for slot in control["execution_slots"].values()
                     if slot["task_id"] == task_id and slot["decision_id"] == req["current_decision_id"]
                     and slot["expected_revision"] == req["revision"]]
            if len(slots) != 1 or "completion" not in slots[0]:
                return ["H1 current accepted execution result required for Mission completion"]
            slot = slots[0]
            if events is not None:
                from tplan_commands import digest
                import tplan_runtime as runtime
                completion = slot["completion"]
                matches = [e for e in events if e.get("id") == completion["evidence_id"]]
                if (len(matches) != 1 or digest(matches[0]) != completion["evidence_digest"]
                    or matches[0].get("event_type") != "acceptance_passed"
                    or matches[0].get("task_id") != task_id):
                    return ["H1 qualified completion evidence is missing or changed"]
                latest = {}
                for event in events:
                    if (event.get("task_id") == task_id
                        and event.get("event_type") in {"acceptance_passed", "acceptance_failed"}):
                        if runtime.validate_evidence_event(state,event,compatibility=True,internal=True):
                            return ["H1 completion has malformed later acceptance evidence"]
                        for ac in event["payload"]["acceptance_ids"]:
                            latest[ac] = event
                if any(latest.get(ac) != matches[0]
                       for ac in runtime._acceptance_coverage_for_task(state,task_id)):
                    return ["H1 current qualified B acceptance required for Mission completion"]
    return []


RECORD_FIELDS = {
    "candidates": {"candidate_id", "task_id", "attempt_ref", "content_sha256", "bytes_ref", "validity"},
    "decisions": {"decision_id", "request_id", "expected_revision", "choice", "candidate_id",
                  "candidate_sha256", "owner_subject_ref", "origin_binding_ref", "origin_session_ref",
                  "origin_event_ref", "issuer_id", "key_id", "committed_at", "receipt_digest", "adoption_blocked"},
    "adoptions": {"request_id", "candidate_id", "decision_id", "content_sha256"},
    "execution_slots": {"slot_id", "mission_id", "task_id", "authorization_round", "request_id",
                        "expected_revision", "candidate_id", "candidate_sha256", "decision_id",
                        "dependency_digest", "input_digest", "host_ref", "intent_id", "session_id",
                        "native_request_id", "receipts"},
    "commands": {"command_id", "action", "request_digest", "committed_at", "result"},
}


def _validate_slot_result(hc, slot):
    """Optional result/completion facts extend the original immutable slot."""
    from tplan_commands import HASH, valid_id
    if "result" not in slot:
        return ["H1 completion requires a delivered result"] if "completion" in slot else []
    result = slot["result"]
    if (not isinstance(result, dict) or set(result) != {"candidate_id", "receipt_ref", "committed_at"}
        or not all(isinstance(v, str) and v for v in result.values())
        or not valid_id(result["candidate_id"]) or not valid_id(result["receipt_ref"])):
        return ["H1 result fields invalid"]
    candidate = hc["candidates"].get(result["candidate_id"], {})
    if (candidate.get("task_id") != slot["task_id"] or candidate.get("attempt_ref") != slot["intent_id"]
        or sum(f.get("receipt_ref") == result["receipt_ref"] and f.get("status") == "delivered"
               and f.get("committed_at") == result["committed_at"]
               for f in slot["receipts"] if isinstance(f,dict)) != 1):
        return ["H1 delivered result must bind the original native slot attempt"]
    if "completion" in slot:
        completion = slot["completion"]
        if (not isinstance(completion,dict) or set(completion) != {
            "command_id", "evidence_id", "candidate_id", "receipt_digest", "evidence_digest"}
            or not all(isinstance(v,str) and v for v in completion.values())
            or completion["candidate_id"] != result["candidate_id"]
            or not valid_id(completion["evidence_id"])
            or not HASH.fullmatch(completion["receipt_digest"])
            or not HASH.fullmatch(completion["evidence_digest"])
            or hc["commands"].get(completion["command_id"],{}).get("action") != "task.complete"):
            return ["H1 completion binding invalid"]
    return []


def _validate_records(state):
    from tplan_commands import HASH, valid_id
    hc = state["human_control"]
    errors = []
    tasks = {t["id"] for t in state.get("tasks", [])
             if isinstance(t, dict) and isinstance(t.get("id"), str)}
    for table, fields in RECORD_FIELDS.items():
        for key, record in hc[table].items():
            optional = {"result", "completion"} if table == "execution_slots" else set()
            if (not valid_id(key) or not isinstance(record, dict)
                or set(record) - optional != fields):
                errors.append(f"H1 {table} record fields invalid")
                continue
            previous_errors = len(errors)
            for field, value in record.items():
                if field.endswith("_digest") or field in {"content_sha256", "candidate_sha256"}:
                    if not isinstance(value, str) or not HASH.fullmatch(value):
                        errors.append(f"H1 {table} digest invalid")
                elif field in {"authorization_round", "expected_revision"}:
                    if type(value) is not int or value < 1:
                        errors.append(f"H1 {table} revision/round invalid")
                elif field not in {"result", "completion", "receipts", "adoption_blocked"}:
                    if not isinstance(value, str) or not value:
                        errors.append(f"H1 {table} reference invalid")
            if len(errors) != previous_errors:
                continue
            if table == "candidates":
                sha = record["content_sha256"]
                if (record["candidate_id"] != key or record["task_id"] not in tasks
                    or record["validity"] != "eligible" or not isinstance(sha, str)
                    or record["bytes_ref"] != "artifacts/h1/" + sha.removeprefix("sha256:")):
                    errors.append("H1 candidate content binding invalid")
            if table == "decisions":
                if (record["decision_id"] != key or record["request_id"] not in hc["requests"]
                    or record["candidate_id"] not in hc["candidates"] or record["choice"] not in CHOICES
                    or (record["adoption_blocked"] is not None and not isinstance(record["adoption_blocked"], str))):
                    errors.append("H1 decision binding invalid")
            if table == "adoptions":
                if (record["request_id"] != key or key not in hc["requests"]
                    or record["decision_id"] not in hc["decisions"] or record["candidate_id"] not in hc["candidates"]):
                    errors.append("H1 adoption binding invalid")
            if table == "execution_slots":
                if (record["slot_id"] != key or record["mission_id"] != state["mission"]["id"]
                    or record["task_id"] not in tasks
                    or record["request_id"] not in hc["requests"] or record["decision_id"] not in hc["decisions"]
                    or record["candidate_id"] not in hc["candidates"] or not isinstance(record["receipts"], list)):
                    errors.append("H1 execution slot binding invalid")
                else:
                    import uuid
                    try:
                        session_uuid = record["session_id"].removeprefix("session-")
                        if (not record["session_id"].startswith("session-")
                            or str(uuid.UUID(session_uuid)) != session_uuid
                            or str(uuid.UUID(record["native_request_id"])) != record["native_request_id"]):
                            raise ValueError("Noncanonical native identity")
                    except ValueError:
                        errors.append("H1 slot requires native session-UUID and request UUID")
                    for fact in record["receipts"]:
                        if (not isinstance(fact, dict) or set(fact) != {"status", "receipt_ref", "committed_at"}
                            or not isinstance(fact["status"], str)
                            or fact["status"] not in {"sent", "unknown", "accepted", "delivered"}
                            or not valid_id(fact["receipt_ref"])):
                            errors.append("H1 dispatch receipt invalid")
                    errors.extend(_validate_slot_result(hc, record))
            if table == "commands" and (record["command_id"] != key or not isinstance(record["result"], dict)):
                errors.append("H1 command result invalid")
    for nonce, command_id in hc["used_nonces"].items():
        if not isinstance(nonce, str) or not HASH.fullmatch(nonce) or not isinstance(command_id, str) or command_id not in hc["commands"]:
            errors.append("H1 nonce binding invalid")
    for task_id, round_id in hc["authorization_rounds"].items():
        if task_id not in tasks or type(round_id) is not int or round_id < 1:
            errors.append("H1 authorization round invalid")
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
    if not authorized:
        protected = protected_contract_task_ids(before) | protected_contract_task_ids(after)
        old_tasks = {t["id"]: t for t in before.get("tasks", []) if isinstance(t,dict) and isinstance(t.get("id"), str)}
        new_tasks = {t["id"]: t for t in after.get("tasks", []) if isinstance(t,dict) and isinstance(t.get("id"), str)}
        for task_id in protected:
            if old_tasks.get(task_id) != new_tasks.get(task_id):
                errors.append(f"H1 controlled task {task_id} cannot be changed by a legacy writer")
        def dependencies(state):
            plan = state.get("work_plan", {})
            if not isinstance(plan, dict) or not isinstance(plan.get("blocks", []), list):
                return None
            return {b["task_id"]: {k: b.get(k) for k in ("depends_on", "parallel_conditions")}
                    for b in plan.get("blocks", []) if isinstance(b,dict) and b.get("task_id") in protected}
        if dependencies(before) != dependencies(after):
            errors.append("H1 native dependency declarations require scoped authority")
        relevant_acceptance = {ac for task_id in protected for tasks in (old_tasks,new_tasks)
                               for ac in tasks.get(task_id, {}).get("acceptance_evidence", [])
                               if isinstance(ac,str)}
        def acceptance_contract(state):
            return {a["id"]:a for a in state.get("mission", {}).get("acceptance_evidence", [])
                    if isinstance(a,dict) and isinstance(a.get("id"),str) and a["id"] in relevant_acceptance}
        if acceptance_contract(before) != acceptance_contract(after):
            errors.append("H1 inherited Mission acceptance contract requires scoped authority")
        def scoped_blockers(state):
            plan = state.get("work_plan", {})
            if not isinstance(plan,dict) or not isinstance(plan.get("blockers", []),list):
                return None
            return [b for b in plan.get("blockers", []) if isinstance(b,dict) and
                    (not b.get("task_ids") or any(t in protected for t in b.get("task_ids", []) if isinstance(t,str)))]
        if scoped_blockers(before) != scoped_blockers(after):
            errors.append("H1 scoped native blockers require scoped authority")
        if isinstance(after.get("active_task_id"), str) and after["active_task_id"] in controlled_task_ids(before):
            errors.append("H1 controlled task focus requires scoped authority")
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
    errors.extend(completion_findings(after) if after.get("mission", {}).get("status") == "completed" else [])
    return errors


def validate_evidence(state: dict[str, Any], event: dict[str, Any], *, authorized=False) -> list[str]:
    if event.get("event_type") in {"acceptance", "acceptance_passed"}:
        task_id = event.get("task_id")
        if isinstance(task_id, str) and task_id in controlled_task_ids(state):
            if authorized and event["event_type"] == "acceptance_passed":
                return []
            return ["H1 Owner authority cannot be replaced by acceptance evidence"]
    return []
