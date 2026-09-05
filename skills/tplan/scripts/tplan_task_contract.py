#!/usr/bin/env python3
"""Pure task normalization, acceptance parsing, and Mission Markdown formatting for TPlan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tplan_errors import TplanError


TASK_STATUSES = {
    "pending", "active", "blocked", "completed", "paused", "pruned", "abandoned", "superseded",
}
TASK_ROLES = {"success-critical", "supporting", "exploratory"}
NODE_KINDS = {"task", "subtask", "step"}
PARENT_ALIGNED_TASK_FIELDS = {"parent_contribution", "parent_acceptance", "mission_trace"}
STEP_TASK_FIELDS = {"parent_contribution", "mission_trace", "step_action", "done_condition"}


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
