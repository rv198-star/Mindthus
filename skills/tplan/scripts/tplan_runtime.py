#!/usr/bin/env python3
"""Shared helpers for tplan runtime scripts.

These helpers enforce runtime shape, state, and authority. They do not decide semantic
truth.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "tplan.v0.1"

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

TASK_ROLES = {"success-critical", "supporting", "exploratory"}

RECOMMENDATIONS = {"add", "subtract", "continue", "switch", "close", "escalate"}

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

TASK_REQUIRED_FIELDS = {
    "id",
    "parent_id",
    "level",
    "title",
    "status",
    "role",
    "mission_contribution",
    "acceptance_evidence",
    "evidence_links",
}

POLICY_FIELDS = ("human_in_loop", "risk_tolerance", "resource_sufficiency")
MISSION_STRING_FIELDS = ("id", "title", "objective")
TASK_STRING_FIELDS = ("title", "mission_contribution")


class TplanError(ValueError):
    """Runtime contract violation."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "unnamed"


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
        "archive": mission_dir / "archive",
    }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_mission(mission_dir: Path) -> dict[str, Any]:
    return read_json(mission_paths(mission_dir)["mission"])


def write_mission(mission_dir: Path, data: dict[str, Any]) -> None:
    write_json(mission_paths(mission_dir)["mission"], data)


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
            for field in sorted(TASK_REQUIRED_FIELDS):
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
    for task in normalized_tasks:
        task_id = _task_label(0, task)
        parent_id = task.get("parent_id")
        if parent_id is None:
            continue
        if not isinstance(parent_id, str):
            errors.append(f"task {task_id} parent_id must be a string or null")
        elif parent_id not in tasks_by_id:
            errors.append(f"task {task_id} parent_id {parent_id} does not exist")
        elif parent_id == task_id:
            errors.append(f"task {task_id} parent_id cannot reference itself")

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
        if task.get("role") != "success-critical":
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


def normalize_task(raw: dict[str, Any], default_level: int = 2) -> dict[str, Any]:
    if "id" not in raw:
        raise TplanError("task is missing id")
    if "title" not in raw:
        raise TplanError(f"task {raw['id']} is missing title")

    task_id = str(raw["id"])
    status = require_task_enum(task_id, "status", raw.get("status", "pending"), TASK_STATUSES)
    role = require_task_enum(task_id, "role", raw.get("role", "success-critical"), TASK_ROLES)
    level = require_task_level(task_id, raw.get("level", default_level))

    return {
        "id": task_id,
        "parent_id": raw.get("parent_id"),
        "level": level,
        "title": str(raw["title"]),
        "status": status,
        "role": role,
        "mission_contribution": str(raw.get("mission_contribution", "")),
        "acceptance_evidence": require_string_list(
            task_id, "acceptance_evidence", raw.get("acceptance_evidence", [])
        ),
        "evidence_links": require_string_list(task_id, "evidence_links", raw.get("evidence_links", [])),
    }


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
        "tasks": [normalize_task(task) for task in tasks],
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


def read_events(mission_dir: Path) -> list[dict[str, Any]]:
    path = mission_paths(mission_dir)["evidence"]
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def append_event(mission_dir: Path, event: dict[str, Any]) -> dict[str, Any]:
    path = mission_paths(mission_dir)["evidence"]
    events = read_events(mission_dir)
    event = dict(event)
    event.setdefault("id", f"E{len(events) + 1}")
    event.setdefault("timestamp", now_iso())
    event.setdefault("task_id", None)
    event.setdefault("payload", {})
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
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
        "event_count": len(read_events(mission_dir)),
    }


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
        "relevant_evidence_events": events[-10:],
        "current_blockers_or_surprises": [
            event for event in events[-10:] if event.get("event_type") in {"failure", "blocked", "interruption"}
        ],
    }


def validate_hook_output(decision: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(decision, dict):
        return ["decision must be an object"]
    for field in (
        "recommendation",
        "rationale",
        "confidence",
        "evidence_links",
        "proposed_mutations",
        "requires_human",
        "mission_alignment",
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
    if not isinstance(decision.get("mission_alignment"), str):
        errors.append("mission_alignment must be a string")
    return errors


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
    errors = validate_hook_output(decision)
    if errors:
        raise TplanError("; ".join(errors))

    mission = read_mission(mission_dir)
    mode = authority_mode(mission)
    if mode == "advisory" or decision["requires_human"]:
        record_decision_recommendation(mission_dir, decision)
        return "recorded_recommendation"

    for mutation in decision["proposed_mutations"]:
        apply_mutation(mission, mutation)
    write_mission(mission_dir, mission)
    append_event(
        mission_dir,
        {
            "event_type": "decision_applied",
            "summary": decision["rationale"],
            "task_id": None,
            "payload": decision,
        },
    )
    return "applied_decision"
