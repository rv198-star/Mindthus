#!/usr/bin/env python3
"""Render a user-facing tplan progress update.

Internal IDs stay in runtime files. This script leads with Mission meaning and exposes
IDs only when debug or recovery references are requested.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tplan_runtime import active_task, read_events, read_mission


def render_confirmed(events: list[dict[str, Any]]) -> list[str]:
    useful_types = {
        "acceptance",
        "blocker",
        "user_feedback",
        "decision",
        "decision_recommendation",
        "key_finding",
        "state_transition",
        "stop_report",
    }
    summaries = [
        str(event["summary"]).strip()
        for event in events
        if event.get("event_type") in useful_types
        and isinstance(event.get("summary"), str)
        and event["summary"].strip()
    ]
    return summaries[-3:]


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


def render_update(mission: dict[str, Any], events: list[dict[str, Any]], include_internal: bool) -> str:
    current = active_task(mission)
    lines = [
        "当前目标：",
        mission["mission"]["objective"],
        "",
        "当前进展：",
        current["title"] if current else "暂未选择当前任务。",
        "",
        "已确认：",
    ]
    confirmed = render_confirmed(events)
    if confirmed:
        lines.extend(f"- {summary}" for summary in confirmed)
    else:
        lines.append("- 暂无可约束结论；只有运行状态已建立。")
    lines.extend(
        [
            "",
            "下一步：",
            next_step_text(mission, current, events),
        ]
    )
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a user-facing tplan update.")
    parser.add_argument("mission_dir")
    parser.add_argument("--include-internal", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print machine-readable render fields.")
    args = parser.parse_args()

    try:
        mission_dir = Path(args.mission_dir)
        mission = read_mission(mission_dir)
        events = read_events(mission_dir)
        text = render_update(mission, events, args.include_internal)
    except (KeyError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "text": text,
                    "include_internal": args.include_internal,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
