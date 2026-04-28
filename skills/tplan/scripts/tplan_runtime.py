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
    return tasks


def normalize_task(raw: dict[str, Any], default_level: int = 2) -> dict[str, Any]:
    task_id = str(raw["id"])
    return {
        "id": task_id,
        "parent_id": raw.get("parent_id"),
        "level": int(raw.get("level", default_level)),
        "title": str(raw["title"]),
        "status": raw.get("status", "pending"),
        "role": raw.get("role", "success-critical"),
        "mission_contribution": str(raw.get("mission_contribution", "")),
        "acceptance_evidence": list(raw.get("acceptance_evidence", [])),
        "evidence_links": list(raw.get("evidence_links", [])),
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
