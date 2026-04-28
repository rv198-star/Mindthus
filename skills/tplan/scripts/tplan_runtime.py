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


def task_map(tasks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in tasks if isinstance(task.get("id"), str)}


def acceptance_ids(mission: dict[str, Any]) -> set[str]:
    evidence = mission.get("acceptance_evidence", [])
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

    evidence = mission.get("acceptance_evidence")
    if "acceptance_evidence" in mission:
        if not isinstance(evidence, list):
            errors.append("mission acceptance_evidence must be a list")
        else:
            for index, item in enumerate(evidence, start=1):
                if not isinstance(item, dict):
                    errors.append(f"mission acceptance_evidence item {index} must be an object")
                elif "id" not in item:
                    errors.append(f"mission acceptance_evidence item {index} is missing id")
                elif not isinstance(item["id"], str):
                    errors.append(f"mission acceptance_evidence item {index} id must be a string")

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
            if "evidence_links" in task:
                _require_string_list(errors, task_id, "evidence_links", task["evidence_links"])

            normalized_tasks.append(task)

    tasks_by_id = task_map(normalized_tasks)
    for task in normalized_tasks:
        task_id = _task_label(0, task)
        parent_id = task.get("parent_id")
        if parent_id is None:
            continue
        if not isinstance(parent_id, str):
            errors.append(f"task {task_id} parent_id must be a string or null")
        elif parent_id not in tasks_by_id:
            errors.append(f"task {task_id} parent_id {parent_id} does not exist")

    active_task_id = state.get("active_task_id")
    if active_task_id is not None:
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

    for evidence_id in sorted(acceptance_ids(mission)):
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
