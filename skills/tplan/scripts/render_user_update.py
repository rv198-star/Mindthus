#!/usr/bin/env python3
"""Render a user-facing tplan progress update.

Internal IDs stay in runtime files. This script leads with Mission meaning and exposes
IDs only when debug or recovery references are requested.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from typing import Any

from outcome_attribution import build_outcome_attribution
from tplan_runtime import (
    USER_UPDATE_CURSOR_SCHEMA_VERSION,
    TplanError,
    active_task,
    read_user_update_snapshot,
)


CURSOR_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def render_confirmed_facts(events: list[dict[str, Any]]) -> list[str]:
    useful_types = {"acceptance_evidence", "key_finding", "state_transition"}
    summaries = [
        str(event["summary"]).strip()
        for event in events
        if event.get("event_type") in useful_types
        and isinstance(event.get("summary"), str)
        and event["summary"].strip()
    ]
    return summaries[-3:]


def _outcome_summaries(attribution: dict[str, Any], field: str) -> list[str]:
    return [
        str(item["summary"]).strip()
        for item in attribution.get(field, [])
        if isinstance(item.get("summary"), str) and item["summary"].strip()
    ][-3:]


def _latest_meaningful_summary(attribution: dict[str, Any], events: list[dict[str, Any]]) -> str:
    meaningful_ids = {
        evidence_id
        for field in ("countable_progress", "constraint_deltas")
        for item in attribution.get(field, [])
        for evidence_id in item.get("evidence_ids", [])
        if isinstance(evidence_id, str)
    }
    fact_types = {"acceptance_evidence", "key_finding", "state_transition"}
    for event in reversed(events):
        if event.get("id") in meaningful_ids or event.get("event_type") in fact_types:
            summary = event.get("summary")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()
    return "暂无可验证变化记录"


def _encode_cursor(snapshot: dict[str, Any], quiet_streak: int) -> str:
    mission = snapshot["mission"]
    payload = {
        "schema_version": USER_UPDATE_CURSOR_SCHEMA_VERSION,
        "mission_id": mission["mission"]["id"],
        "mission_binding": snapshot["mission_binding"],
        "mission_digest": snapshot["mission_digest"],
        "evidence_digest": snapshot["evidence_digest"],
        "interaction_guard_digest": snapshot["interaction_guard_digest"],
        "quiet_streak": quiet_streak,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(value: str) -> dict[str, Any]:
    if not value or len(value) > 4096:
        raise ValueError("user update cursor is empty or too long")
    try:
        padded = value + "=" * (-len(value) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
        cursor = json.loads(decoded.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("user update cursor is invalid") from exc
    required = {
        "schema_version",
        "mission_id",
        "mission_binding",
        "mission_digest",
        "evidence_digest",
        "interaction_guard_digest",
        "quiet_streak",
    }
    if not isinstance(cursor, dict) or set(cursor) != required:
        raise ValueError("user update cursor schema is invalid")
    if cursor["schema_version"] != USER_UPDATE_CURSOR_SCHEMA_VERSION:
        raise ValueError("user update cursor schema version is unsupported")
    if not isinstance(cursor["mission_id"], str) or not cursor["mission_id"].strip() or "\n" in cursor["mission_id"]:
        raise ValueError("user update cursor mission id is invalid")
    for field in ("mission_binding", "mission_digest", "evidence_digest", "interaction_guard_digest"):
        if not isinstance(cursor[field], str) or not CURSOR_DIGEST_RE.fullmatch(cursor[field]):
            raise ValueError(f"user update cursor {field} is invalid")
    if isinstance(cursor["quiet_streak"], bool) or not isinstance(cursor["quiet_streak"], int) or not 0 <= cursor["quiet_streak"] <= 2:
        raise ValueError("user update cursor quiet streak is invalid")
    return cursor


def next_step_text(mission: dict[str, Any], current: dict[str, Any] | None, events: list[dict[str, Any]]) -> str:
    status = mission["mission"]["status"]
    if status == "requires_human":
        stop_events = [event for event in events if event.get("event_type") == "stop_report"]
        if stop_events:
            payload = stop_events[-1].get("payload", {})
            if isinstance(payload, dict) and isinstance(payload.get("need_from_human"), str):
                return payload["need_from_human"]
        return "需要人类确认后再继续。"
    if current is None:
        return "当前没有 active task；下一步应先选择可推进的任务。"
    if current.get("status") == "blocked":
        return "当前任务被阻塞；先处理阻碍或请求用户确认。"
    return f"继续推进“{current['title']}”，并只在验收、阻碍或决策变化时记录证据。"


def _current_subject(mission: dict[str, Any], current: dict[str, Any] | None) -> str:
    if mission["mission"]["status"] == "requires_human":
        return "等待人类确认"
    if current is None:
        return "没有 active task"
    return f"仍在“{current['title']}”"


def render_brief_unchanged(mission: dict[str, Any], current: dict[str, Any] | None) -> str:
    return f"暂无新的可验证变化，{_current_subject(mission, current)}。\n"


def render_heartbeat(
    mission: dict[str, Any],
    current: dict[str, Any] | None,
    events: list[dict[str, Any]],
    attribution: dict[str, Any],
) -> str:
    latest = _latest_meaningful_summary(attribution, events)
    return (
        "状态心跳：连续 3 次自动检查没有新的 Mission 或验收证据变化。"
        f"当前{_current_subject(mission, current)}；最近一次可验证变化是“{latest}”。\n"
    )


def interaction_guard_text(state: dict[str, Any], *, just_released: bool = False) -> str | None:
    if not state.get("present"):
        return "交互保护：已解除。" if just_released else None
    phase_text = {
        "protecting": "写保护已开启",
        "awaiting_authority": "写保护已开启，等待授权确认",
        "orphaned": "写保护持续，等待人工恢复",
    }.get(state.get("phase"), "写保护已开启")
    return f"交互保护：{phase_text}（修订 {state['revision']}）。"


def render_update(
    mission: dict[str, Any],
    events: list[dict[str, Any]],
    trace: list[dict[str, Any]],
    include_internal: bool,
    interaction_guard_state: dict[str, Any],
    *,
    guard_just_released: bool = False,
) -> str:
    current = active_task(mission)
    attribution = build_outcome_attribution(mission, events, trace)["mission"]
    progress = _outcome_summaries(attribution, "countable_progress")
    constraints = _outcome_summaries(attribution, "constraint_deltas")
    facts = render_confirmed_facts(events)
    lines = [
        "当前目标：",
        mission["mission"]["objective"],
        "",
        "当前进展：",
        current["title"] if current else "暂未选择当前任务。",
        "",
        "可计推进：",
    ]
    if progress:
        lines.extend(f"- {summary}" for summary in progress)
    else:
        lines.append("- 暂无合格的 acceptance 或已应用路径决策。")
    if constraints:
        lines.extend(["", "关键约束：", *[f"- {summary}" for summary in constraints]])
    if facts:
        lines.extend(["", "已确认事实：", *[f"- {summary}" for summary in facts]])
    lines.extend(
        [
            "",
            "下一步：",
            next_step_text(mission, current, events),
        ]
    )
    guard_line = interaction_guard_text(interaction_guard_state, just_released=guard_just_released)
    if guard_line:
        lines.extend(["", guard_line])
    if include_internal:
        evidence_ids = ", ".join(
            str(event["id"]) for event in events if isinstance(event.get("id"), str)
        ) or "none"
        lines.extend(
            [
                "",
                "内部恢复引用：",
                f"- mission_id: {mission['mission']['id']}",
                f"- active_task_id: {mission.get('active_task_id') or 'none'}",
                f"- evidence_ids: {evidence_ids}",
            ]
        )
    return "\n".join(lines) + "\n"


def render_delivery(
    snapshot: dict[str, Any],
    *,
    cursor_value: str | None,
    delivery: str,
    include_internal: bool,
) -> dict[str, Any]:
    mission = snapshot["mission"]
    events = snapshot["events"]
    trace = snapshot["trace"]
    attribution = build_outcome_attribution(mission, events, trace)["mission"]
    current = active_task(mission)
    if cursor_value is None:
        return {
            "changed": True,
            "update_kind": "full",
            "quiet_streak": 0,
            "cursor": _encode_cursor(snapshot, 0),
            "text": render_update(mission, events, trace, include_internal, snapshot["interaction_guard_state"]),
        }

    cursor = _decode_cursor(cursor_value)
    if cursor["mission_id"] != mission["mission"]["id"]:
        raise ValueError("user update cursor belongs to a different mission")
    if cursor["mission_binding"] != snapshot["mission_binding"]:
        raise ValueError("user update cursor belongs to a different mission")
    guard_changed = cursor["interaction_guard_digest"] != snapshot["interaction_guard_digest"]
    changed = (
        cursor["mission_digest"] != snapshot["mission_digest"]
        or cursor["evidence_digest"] != snapshot["evidence_digest"]
        or guard_changed
    )
    if changed:
        return {
            "changed": True,
            "update_kind": "full",
            "quiet_streak": 0,
            "cursor": _encode_cursor(snapshot, 0),
            "text": render_update(
                mission,
                events,
                trace,
                include_internal,
                snapshot["interaction_guard_state"],
                guard_just_released=guard_changed and not snapshot["interaction_guard_state"]["present"],
            ),
        }
    if delivery == "explicit":
        return {
            "changed": False,
            "update_kind": "brief",
            "quiet_streak": 0,
            "cursor": _encode_cursor(snapshot, 0),
            "text": render_brief_unchanged(mission, current),
        }

    next_streak = cursor["quiet_streak"] + 1
    if next_streak == 3:
        return {
            "changed": False,
            "update_kind": "heartbeat",
            "quiet_streak": 0,
            "cursor": _encode_cursor(snapshot, 0),
            "text": render_heartbeat(mission, current, events, attribution),
        }
    return {
        "changed": False,
        "update_kind": "quiet",
        "quiet_streak": next_streak,
        "cursor": _encode_cursor(snapshot, next_streak),
        "text": "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a user-facing tplan update.")
    parser.add_argument("mission_dir")
    parser.add_argument("--include-internal", action="store_true")
    parser.add_argument("--cursor", help="Opaque cursor returned by a prior user update render.")
    parser.add_argument("--delivery", choices=("automatic", "explicit"), default="explicit")
    parser.add_argument("--json", action="store_true", help="Print machine-readable render fields.")
    args = parser.parse_args()

    try:
        mission_dir = Path(args.mission_dir)
        result = render_delivery(
            read_user_update_snapshot(mission_dir),
            cursor_value=args.cursor,
            delivery=args.delivery,
            include_internal=args.include_internal,
        )
    except (KeyError, OSError, json.JSONDecodeError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({**result, "include_internal": args.include_internal, "delivery": args.delivery}, ensure_ascii=False, indent=2))
    else:
        print(result["text"], end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
