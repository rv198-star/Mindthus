#!/usr/bin/env python3
"""Render a read-only TPlan work view as text, JSON, or self-contained HTML.

Work estimates, coverage and dependency facts belong to work_plan.build_work_view.
This module presents that result; it never changes Mission state or authorizes work.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import sys
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import quote

from outcome_attribution import build_outcome_attribution
from tplan_runtime import TplanError, read_user_update_snapshot, runtime_provenance_report, write_text_atomic
from render_user_update import interaction_guard_text, next_step_text, render_confirmed_facts
from work_plan import build_work_view


SCHEMA_VERSION = "tplan.progress_view.v1"
STATUS_LABELS = {
    "active": "进行中", "pending": "待开始", "in_progress": "执行中",
    "completed": "已完成", "blocked": "已阻塞", "requires_human": "等待人类确认",
    "budget_exhausted": "预算已用尽", "abandoned": "已放弃", "superseded": "已被替代",
    "deferred": "已延后", "cancelled": "已取消", "paused": "已暂停",
}
MISSION_LIMITS = {
    "blocked": "Mission 已阻塞；展示剩余工作不表示已经可以继续。",
    "requires_human": "Mission 正在等待人类确认；此视图不提供继续授权。",
    "budget_exhausted": "Mission 预算已用尽；剩余估计不代表已获得新增预算。",
    "abandoned": "Mission 已放弃；这里保留的是已有工作记录。",
    "superseded": "Mission 已被替代；这里保留的是旧 Mission 的工作记录。",
}
SHARE_NOTE = "占比只描述已估算、同单位的剩余工作构成；区间占比不要求合计为 100%。"
PARALLEL_NOTE = "前置条件已满足只描述已记录的关系；并行仍取决于明确的资源、工作区与权限条件。未提供依赖信息不表示可以并行。"
PROGRESS_NOTE = "整体进展只展示源计划的声明及依据，不由任务数量、已花时间或剩余估计倒算。"


def _number(value: Any) -> str:
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        return format(value, ".10g")
    return str(value)


def _range(value: dict[str, Any] | None, *, percent: bool = False) -> str:
    if value is None:
        return "未估计" if not percent else "不可计算"
    low, high = value["low"], value["high"]
    if percent:
        # Display a readable approximation while preserving exact values in JSON.
        left, right = format(low, ".3g"), format(high, ".3g")
        approximate = float(left) != low or float(right) != high
        amount = left if low == high else f"{left}–{right}"
        return ("约 " if approximate else "") + amount + "%"
    amount = _number(low) if low == high else f"{_number(low)}–{_number(high)}"
    return f"{amount} {value['unit']}"


def _status(value: Any) -> str:
    return STATUS_LABELS.get(str(value), str(value))


def _title_lookup(view: dict[str, Any], task_titles: dict[str, str]) -> dict[str, str]:
    titles = dict(task_titles)
    titles.update({block["task_id"]: block["title"] for block in view["blocks"]})
    for block in view["blocks"]:
        for dep in block.get("dependencies") or []:
            titles[dep["task_id"]] = dep["title"]
    return titles


def _dependencies_text(block: dict[str, Any]) -> str:
    dependencies = block.get("dependencies")
    if dependencies is None:
        return "前置信息未提供"
    if not dependencies:
        return "已声明无前置"
    return "；".join(
        f"{dep['title']}（{'已满足' if dep['satisfied'] else '尚未满足'}，{_status(dep['status'])}）"
        for dep in dependencies
    )


def _parallel_text(block: dict[str, Any]) -> str:
    conditions = block.get("parallel_conditions")
    if not conditions:
        return "并行条件未提供，不能据此确认可并行"
    return "；".join(conditions)


def _progress_text(view: dict[str, Any]) -> str:
    progress = view.get("progress")
    if progress is None:
        return "未提供可用的整体进度数值"
    return f"{progress['label']}：{_number(progress['value'])} {progress['unit']}"


def _text_percent_bar(low: float, high: float | None = None, *, width: int = 20) -> str:
    """Render a conservative chat-native percentage bar.

    Exact values use solid/empty cells. Intervals use solid cells only for the
    guaranteed lower bound and shaded cells for the uncertain interval.
    """
    low = max(0.0, min(100.0, float(low)))
    high = low if high is None else max(low, min(100.0, float(high)))
    if low == high:
        filled = max(0, min(width, round(low * width / 100)))
        return "█" * filled + "░" * (width - filled)
    guaranteed = max(0, min(width, math.floor(low * width / 100)))
    possible = max(guaranteed, min(width, math.ceil(high * width / 100)))
    return "█" * guaranteed + "▒" * (possible - guaranteed) + "░" * (width - possible)


def _progress_bar_text(view: dict[str, Any]) -> str | None:
    progress = view.get("progress")
    if progress is None or progress.get("unit") not in {"%", "percent"}:
        return None
    value = progress.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return f"[{_text_percent_bar(float(value))}] {_number(value)}%"


def _share_bar_text(share: dict[str, Any] | None) -> str | None:
    if share is None:
        return None
    return f"[{_text_percent_bar(float(share['low']), float(share['high']))}]"


def _remaining_text(view: dict[str, Any]) -> str:
    remaining = view["remaining"]
    total = remaining.get("total")
    if total is not None:
        return _range(total)
    groups = remaining.get("totals_by_unit", [])
    if groups:
        return "；".join(_range(group) for group in groups) + "（已声明小计，不能作为整体总量）"
    return "暂无可合计的剩余估计"


def _remaining_blocks(view: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        block for block in view["blocks"]
        if block["is_remaining"] or block.get("remaining_uncertain")
    ]


def _block_count_text(blocks: list[dict[str, Any]]) -> str:
    counted = [block for block in blocks if block.get("accounting_role") != "state_context"]
    contexts = len(blocks) - len(counted)
    label = "剩余或待核对工作块" if any(block.get("remaining_uncertain") for block in counted) else "剩余工作块"
    text = f"{len(counted)} 个{label}"
    if contexts:
        text += f"；另列 {contexts} 个层级状态记录"
    return text


def _confidence_text(value: str) -> str:
    return {"low": "低", "medium": "中", "high": "高", "unknown": "未知"}.get(value, value)


def _record_details(record: dict[str, Any], titles: dict[str, str]) -> list[str]:
    details = []
    names = [titles.get(task_id, task_id) for task_id in record.get("task_ids", [])]
    if names:
        details.append("相关工作：" + "、".join(names))
    for field, label in (("impact", "影响"), ("release_condition", "解除条件"), ("recovery_condition", "恢复条件")):
        if record.get(field):
            details.append(f"{label}：{record[field]}")
    if record.get("severity"):
        severity = {"low": "低", "medium": "中", "high": "高", "critical": "严重"}.get(record["severity"], record["severity"])
        details.append(f"来源声明的严重程度：{severity}")
    if record.get("scope"):
        scope = {
            "shared_environment": "共享环境", "mission": "整个 Mission",
            "task": "任务", "cross_task": "跨任务",
        }.get(record["scope"], record["scope"])
        details.append(f"影响范围：{scope}")
    if record.get("affected_surfaces"):
        details.append("受影响部分：" + "、".join(record["affected_surfaces"]))
    if record.get("confidence"):
        details.append("来源声明的信心：" + _confidence_text(record["confidence"]))
    if record.get("source_kind") == "shared_risk_signal":
        source = "当前共享风险记录"
        if record.get("source_task_id"):
            source += "，由“" + titles.get(record["source_task_id"], record["source_task_id"]) + "”报告"
        if record.get("updated_at"):
            source += "，更新时间 " + record["updated_at"]
        details.append("来源：" + source)
    elif record.get("source_kind") == "work_plan":
        details.append("来源：当前工作计划")
    if record.get("source"):
        details.append("来源说明：" + record["source"])
    return details


def _record_text(record: dict[str, Any], titles: dict[str, str]) -> str:
    return "；".join([record["summary"], *_record_details(record, titles)])


def _runtime_limitations(runtime: dict[str, Any]) -> list[str]:
    labels = {
        "runtime_provenance_missing": "运行时来源未固定：无法核实创建此 Mission 的版本。",
        "runtime_path_relocated": "运行时位置已变化：内容指纹兼容，当前读取位置与记录不同。",
        "runtime_legacy_adopted": "运行时由后续版本补记：最初创建版本仍无法核实。",
        "runtime_fingerprint_mismatch": "运行时不兼容：当前版本与 Mission 记录的指纹不同，仅能提供来源诊断。",
        "runtime_provenance_invalid": "运行时来源记录无效，仅能提供来源诊断。",
    }
    return [
        labels.get(item["code"], "运行时来源诊断：" + item.get("message", item["code"]))
        for item in runtime.get("diagnostics", [])
    ]


def _outcome_text(entry: dict[str, Any], report: dict[str, Any]) -> str:
    labels = {
        "acceptance": "验收通过记录", "acceptance_passed": "验收通过记录",
        "acceptance_failed": "验收失败记录", "blocker": "阻塞记录",
        "stop_report": "停止记录", "user_feedback": "反馈记录",
        "decision_applied": "已应用决策记录", "decision_recommendation": "建议记录",
        "risk_context_update": "风险变化记录", "risk_context_recovery": "风险恢复记录",
    }
    sources = []
    for evidence_id in entry.get("evidence_ids", []):
        event = report["evidence_context"].get(evidence_id)
        if event:
            source = labels.get(event["event_type"], "证据记录")
            if event.get("timestamp"):
                source += " · " + event["timestamp"]
            if event.get("task_title"):
                source += " · " + event["task_title"]
            sources.append(source)
    return entry["summary"] + ("（来源：" + "；".join(sources) + "）" if sources else "")


def build_progress_report(
    snapshot: dict[str, Any], *, include_internal: bool = False,
    mission_dir: Path | None = None, guard_just_released: bool = False,
) -> dict[str, Any]:
    """Build a stable presentation payload from one no-write runtime snapshot."""
    mission = snapshot["mission"]
    runtime = snapshot.get("runtime_provenance") or runtime_provenance_report(mission)
    diagnostic_only = runtime.get("compatible") is False
    status = mission["mission"]["status"]
    current_id = mission.get("active_task_id")
    current = next((task for task in mission["tasks"] if task["id"] == current_id), None)
    report = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": diagnostic_only,
        "runtime": runtime,
        "mission": {
            "id": mission["mission"]["id"], "title": mission["mission"]["title"],
            "objective": None if diagnostic_only else mission["mission"]["objective"],
            "status": None if diagnostic_only else status,
            "active_task_title": current["title"] if current and not diagnostic_only else None,
        },
        "source": {
            "mission_digest": snapshot.get("mission_digest"),
            "evidence_digest": snapshot.get("evidence_digest"),
            "work_plan": "mission.json.work_plan", "as_of": None,
        },
        "work_view": None, "task_titles": {},
        "countable_progress": [], "constraint_deltas": [], "confirmed_facts": [],
        "evidence_context": {}, "next_step": None,
        "interaction_guard_text": None, "guard_just_released": guard_just_released,
        "artifacts": [], "limitations": _runtime_limitations(runtime),
        "include_internal": include_internal,
    }
    if diagnostic_only:
        return report

    attribution = build_outcome_attribution(mission, snapshot["events"], snapshot["trace"])
    view = build_work_view(mission, evidence=snapshot["events"], outcome_attribution=attribution)
    limitations = report["limitations"] + list(view.get("limitations", []))
    if status in MISSION_LIMITS:
        limitations.insert(0, MISSION_LIMITS[status])
    guard_line = interaction_guard_text(
        snapshot.get("interaction_guard_state", {"present": False}),
        just_released=guard_just_released,
    )
    if guard_line:
        limitations.insert(0, guard_line)
    blocked = [task["title"] for task in mission["tasks"] if task["status"] == "blocked"]
    if blocked:
        limitations.append("已阻塞的工作块：" + "、".join(blocked) + "。")
    titles = {task["id"]: task["title"] for task in mission["tasks"]}
    report.update({
        "work_view": view, "task_titles": titles,
        "countable_progress": attribution["mission"]["countable_progress"],
        "constraint_deltas": attribution["mission"]["constraint_deltas"],
        "confirmed_facts": render_confirmed_facts(snapshot["events"]),
        "next_step": next_step_text(mission, current, snapshot["events"]),
        "interaction_guard_text": guard_line,
        "evidence_context": {
            event["id"]: {
                "timestamp": event.get("timestamp"), "event_type": event.get("event_type"),
                "task_id": event.get("task_id"), "task_title": titles.get(event.get("task_id")),
                "source_path": "evidence.jsonl",
            }
            for event in snapshot["events"] if isinstance(event.get("id"), str)
        },
        "artifacts": existing_execution_artifacts(mission_dir),
        "limitations": list(dict.fromkeys(limitations)),
    })
    report["source"]["as_of"] = view["planning"].get("as_of")
    return report


def existing_execution_artifacts(mission_dir: Path | None) -> list[dict[str, str]]:
    if mission_dir is None:
        return []
    reports = mission_dir.expanduser().resolve() / "reports"
    names = (("execution-cost-tree.md", "TPlan 执行报告"), ("execution-cost-tree.svg", "TPlan 执行过程图"))
    return [
        {"label": label, "path": str(reports / name)}
        for name, label in names if (reports / name).is_file()
    ]


def render_progress_text(report: dict[str, Any]) -> str:
    if report["diagnostic_only"]:
        lines = [
            "TPlan 运行时来源诊断", f"Mission：{report['mission']['title']}",
            f"运行时状态：{report['runtime']['status']}", *report["limitations"], "",
            "诊断明细：",
        ]
        lines.extend(f"- {item['code']}: {item['message']}" for item in report["runtime"].get("diagnostics", []))
        if report["runtime"].get("differences"):
            lines.append("指纹差异：" + json.dumps(report["runtime"]["differences"], ensure_ascii=False, sort_keys=True))
        return "\n".join(lines) + "\n"
    view = report["work_view"]
    mission = report["mission"]
    titles = _title_lookup(view, report["task_titles"])
    blocks = _remaining_blocks(view)
    lines = [
        "当前目标：", mission["objective"], "",
        "整体进展：", _progress_text(view),
        f"Mission 状态：{_status(mission['status'])}",
    ]
    if mission["active_task_title"]:
        lines.append(f"当前工作：{mission['active_task_title']}")
    progress_bar = _progress_bar_text(view)
    if progress_bar:
        lines.append(f"进度条：{progress_bar}")
    if view.get("progress"):
        lines.append(f"进展依据：{view['progress']['basis']}")
    lines.extend(["", f"预计剩余工作量：{_remaining_text(view)}", f"工作范围：{_block_count_text(blocks)}"])
    if view["planning"].get("scope_note"):
        lines.append(f"覆盖范围：{view['planning']['scope_note']}")
    if report["limitations"]:
        lines.extend(["", "重要限制：", *[f"- {item}" for item in report["limitations"]]])
    for field, label in (("risks", "当前风险"), ("blockers", "主要阻塞点")):
        if view.get(field):
            lines.extend(["", label + "：", *[f"- {_record_text(item, titles)}" for item in view[field]]])
    if report["constraint_deltas"]:
        lines.extend(["", "已记录限制与验收反例：", "以下保留各次记录的时点；历史阻塞的当前有效性以当前状态为准。"])
        lines.extend(f"- {_outcome_text(item, report)}" for item in report["constraint_deltas"])
    if report["countable_progress"]:
        lines.extend(["", "已有结果与依据：", *[f"- {_outcome_text(item, report)}" for item in report["countable_progress"]]])
    if report["confirmed_facts"]:
        lines.extend(["", "已确认事实：", *[f"- {item}" for item in report["confirmed_facts"]]])
    lines.extend(["", "下一步：", report["next_step"], "", "剩余工作与前置关系："])
    if not blocks:
        lines.append("当前记录中没有剩余工作块；是否满足 Mission 验收仍以原状态和证据为准。")
    for block in blocks:
        share = block.get("remaining_share")
        share_label = _range(share, percent=True)
        if share is not None:
            share_label += f"（已估 {share['denominator_unit']} 剩余构成"
            if share["coverage"] != "complete":
                share_label += "，覆盖不完整"
            share_label += "）"
        share_bar = _share_bar_text(share)
        share_visual = f"{share_bar} " if share_bar else ""
        lines.append(f"- {block['title']} [{_status(block['status'])}]：预计剩余 {_range(block['remaining'])}；占比 {share_visual}{share_label}。")
        if block.get("remaining_uncertain"):
            lines.append("  状态与剩余依据待核对：" + "；".join(block.get("uncertainty_reasons", [])))
        if block.get("accounting_role") == "state_context":
            lines.append("  此行为层级状态记录，不是新增估量块；未分摊或复制父子估计。")
        lines.append(f"  前置：{_dependencies_text(block)}。")
        lines.append(f"  并行条件：{_parallel_text(block)}。")
        if block.get("remaining"):
            lines.append(f"  估计依据：{block['remaining']['basis']}")
            if block["remaining"].get("confidence"):
                lines.append("  来源声明的信心：" + _confidence_text(block["remaining"]["confidence"]))
    if any(block.get("remaining_share") and block["remaining_share"]["low"] != block["remaining_share"]["high"] for block in blocks):
        lines.append("占比图例：█ 为确定下界，▒ 为区间不确定部分，░ 为其余范围。")
    lines.extend(["", SHARE_NOTE, PARALLEL_NOTE, PROGRESS_NOTE])
    if report["source"].get("as_of"):
        lines.append(f"估计记录时点：{report['source']['as_of']}")
    if report["artifacts"]:
        lines.extend(["", "已有执行记录（可能早于当前快照）："])
        lines.extend(f"- [{item['label']}](<{item['path']}>)" for item in report["artifacts"])
    if report["include_internal"]:
        lines.extend(["", "内部恢复引用：", f"- mission_id: {mission['id']}"])
        for block in view["blocks"]:
            lines.append(f"- {block['title']}: {block['task_id']}")
    return "\n".join(lines) + "\n"


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _label_lines(value: str) -> list[str]:
    lines, line, used = [], "", 0
    for character in value:
        weight = 2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1
        if used + weight > 23:
            lines.append(line)
            line, used = "", 0
        line += character
        used += weight
    lines.append(line)
    if len(lines) > 2:
        return [lines[0], lines[1][:-1] + "…"]
    return lines


def _graph(view: dict[str, Any], keys: dict[str, str]) -> str:
    """Draw only declared dependencies; hierarchy and display order create no edges."""
    nodes = {block["task_id"]: block for block in view["blocks"]}
    edges: list[tuple[str, str]] = []
    for block in view["blocks"]:
        for dep in block.get("dependencies") or []:
            nodes.setdefault(dep["task_id"], {
                **dep, "dependency_status": "unknown", "is_remaining": False,
                "outside_frontier": True,
            })
            edges.append((dep["task_id"], block["task_id"]))
    if not nodes:
        return '<p class="muted">没有可绘制的工作块。</p>'
    if len(nodes) > 40:
        return '<p class="muted">工作块较多，请使用下方完整前置关系表查看，避免缩小成难以阅读的图。</p>'
    predecessors = {node_id: [] for node_id in nodes}
    for before, after in edges:
        predecessors[after].append(before)
    levels: dict[str, int] = {}

    def depth(node_id: str, visiting: set[str]) -> int:
        if node_id in levels:
            return levels[node_id]
        if node_id in visiting:
            raise ValueError("dependency cycle cannot be drawn as an ordered graph")
        value = max((depth(parent, visiting | {node_id}) + 1 for parent in predecessors[node_id]), default=0)
        levels[node_id] = value
        return value

    try:
        for node_id in nodes:
            depth(node_id, set())
    except ValueError:
        return '<p class="notice">前置记录包含循环，不能画成可执行顺序；请查看源记录中的限制。</p>'
    positions: dict[str, tuple[float, float]] = {}
    row = 0
    card_width, card_height, gap, margin = 200, 88, 24, 24
    columns = min(4, max(sum(value == level for value in levels.values()) for level in set(levels.values())))
    width = columns * card_width + (columns - 1) * gap + margin * 2
    for level in sorted(set(levels.values())):
        ids = [node_id for node_id in nodes if levels[node_id] == level]
        for start in range(0, len(ids), 4):
            chunk = ids[start:start + 4]
            left = (width - len(chunk) * card_width - (len(chunk) - 1) * 24) / 2
            for index, node_id in enumerate(chunk):
                positions[node_id] = (left + index * (card_width + 24), 24 + row * 134)
            row += 1
    height = max(130, row * 134)
    parts = [
        f'<svg class="dependency-graph" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="group" aria-label="已声明的前置关系；箭头表示前置，不表示执行授权">',
        '<defs><marker id="dependency-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor"/></marker></defs>',
    ]
    for before, after in edges:
        x1, y1 = positions[before]
        x2, y2 = positions[after]
        x1 += card_width / 2
        x2 += card_width / 2
        y1 += card_height
        middle = (y1 + y2) / 2
        parts.append(
            f'<path class="dependency-edge" data-from="{_esc(keys.get(before, ""))}" data-to="{_esc(keys.get(after, ""))}" '
            f'd="M{x1},{y1} C{x1},{middle} {x2},{middle} {x2},{y2 - 3}" marker-end="url(#dependency-arrow)"/>'
        )
    for node_id, node in nodes.items():
        x, y = positions[node_id]
        status = _status(node["status"])
        caption = "范围外的前置" if node.get("outside_frontier") else {
            "unknown": "前置未明", "unmet": "等待前置", "declared_clear": "前置满足",
        }[node["dependency_status"]]
        if node.get("remaining_uncertain"):
            caption = "层级状态待核对" if node.get("accounting_role") == "state_context" else "剩余依据待核对"
        key = keys.get(node_id)
        selectable = key and (node.get("is_remaining") or node.get("remaining_uncertain"))
        attrs = f' role="button" tabindex="0" aria-pressed="false" data-select="{key}"' if selectable else ""
        parts.append(f'<g class="graph-node" data-uncertain="{str(bool(node.get("remaining_uncertain"))).lower()}" transform="translate({x} {y})"{attrs} aria-label="{_esc(node["title"] + "：" + status + "；" + caption)}">')
        parts.append(f'<title>{_esc(node["title"])}：{_esc(status)}；{_esc(caption)}</title><rect width="{card_width}" height="{card_height}" rx="10"/>')
        visible = _label_lines(node["title"])
        for index, line in enumerate(visible):
            parts.append(f'<text x="14" y="{25 + index * 19}" class="node-title">{_esc(line)}</text>')
        parts.append(f'<text x="14" y="70" class="node-caption">{_esc(status)} · {_esc(caption)}</text></g>')
    parts.append("</svg>")
    parts.append('<p class="muted">箭头只连接源计划已声明的前置；同一行的位置不证明能并行。选择剩余或待核对的工作块可查看依据与条件。</p>')
    if not edges:
        parts.append('<p class="muted">没有已记录的前置连线；请逐块区分“已声明无前置”和“前置信息未提供”。</p>')
    return "".join(parts)


def _progress_display(progress: dict[str, Any] | None) -> str:
    if progress is None:
        return "未提供数值"
    unit = progress["unit"]
    value = _number(progress["value"])
    return f"{value}%" if unit in {"%", "percent"} else f"{value} {unit}"


def _progress_percent(progress: dict[str, Any] | None) -> float | None:
    if progress is None or progress.get("unit") not in {"%", "percent"}:
        return None
    value = progress.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return max(0.0, min(100.0, float(value)))


def _primary_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return real remaining accounting blocks for the first-screen dashboard."""
    return [block for block in blocks if block.get("accounting_role") != "state_context"]


def _share_bar_html(share: dict[str, Any] | None) -> str:
    if share is None:
        return (
            '<div class="share-track is-unknown" aria-label="剩余占比未估算">'
            '<span class="share-unknown">未估算</span></div>'
        )
    low = max(0.0, min(100.0, float(share["low"])))
    high = max(low, min(100.0, float(share["high"])))
    label = _range(share, percent=True)
    if low == high:
        fill = f'<span class="share-fill" style="width:{low:.6g}%"></span>'
    else:
        fill = (
            f'<span class="share-fill" style="width:{low:.6g}%"></span>'
            f'<span class="share-range" style="left:{low:.6g}%;width:{high - low:.6g}%"></span>'
        )
    return (
        f'<div class="share-track" aria-label="剩余占比 {html.escape(label, quote=True)}" '
        f'data-share-low="{low:.10g}" data-share-high="{high:.10g}">{fill}</div>'
    )


STYLE = """
:root{color-scheme:light dark;--bg:#f5f6f8;--paper:#fff;--ink:#20252b;--muted:#687280;--line:#d9dfe7;--soft:#f0f4f8;--accent:#315f9a;--accent-soft:#e9f0fa;--warn:#805315;--warn-bg:#fff6e7}
@media(prefers-color-scheme:dark){:root{--bg:#191c21;--paper:#242930;--ink:#edf1f6;--muted:#b8c1ce;--line:#424d5c;--soft:#2d3540;--accent:#9bc0f1;--accent-soft:#2c3e57;--warn:#f1c57b;--warn-bg:#3a3021}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{overflow-wrap:anywhere;max-width:980px;margin:28px auto;padding:28px;background:var(--paper);border:1px solid var(--line);border-radius:16px}
h1{font-size:27px;line-height:1.3;margin:0 0 8px}h2{font-size:19px;margin:0 0 10px}h3{font-size:15px;margin:0 0 7px}p{margin:7px 0}a{color:var(--accent)}button,input,select{font:inherit;color:inherit}
.page-head{padding-bottom:15px}.eyebrow,.muted,.meta{color:var(--muted);font-size:13px}.eyebrow{letter-spacing:.08em;margin-bottom:7px}.meta{margin:0}
.dashboard{margin-top:6px}.dashboard-grid{display:grid;grid-template-columns:1.25fr 1fr;gap:14px}.summary-card{border:1px solid var(--line);border-radius:12px;padding:15px 17px;min-width:0}.summary-label{font-size:13px;color:var(--muted)}.summary-value{font-size:32px;font-weight:680;line-height:1.2;margin:5px 0}.summary-sub{font-size:13px;color:var(--muted)}
.progress-track{height:10px;border-radius:999px;background:var(--soft);overflow:hidden;margin-top:14px}.progress-fill{display:block;height:100%;background:var(--accent);border-radius:inherit}
.work-overview{margin-top:24px}.work-overview-head{display:flex;justify-content:space-between;gap:18px;align-items:baseline;margin-bottom:10px}.work-overview-head p{margin:0;max-width:560px}
.work-chart{border-top:1px solid var(--line)}.work-bar{padding:11px 0;border-bottom:1px solid var(--line);cursor:pointer}.work-bar:hover .work-title,.work-bar:focus .work-title{color:var(--accent)}.work-bar[data-selected="true"]{background:var(--accent-soft);margin-inline:-10px;padding-inline:10px;border-radius:8px}
.work-bar-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px}.work-title-wrap{min-width:0}.work-title{font-weight:650}.work-state{display:inline-block;margin-left:8px;font-size:12px;color:var(--muted);font-weight:500}.work-numbers{flex:none;text-align:right}.share-value{font-size:18px;font-weight:650;font-variant-numeric:tabular-nums}.remaining-value{font-size:12px;color:var(--muted)}
.share-line{display:grid;grid-template-columns:minmax(0,1fr);gap:5px;margin-top:9px}.share-track{height:10px;border-radius:999px;background:var(--soft);position:relative;overflow:hidden}.share-fill{position:absolute;inset:0 auto 0 0;background:var(--accent);border-radius:999px}.share-range{position:absolute;top:0;bottom:0;background:repeating-linear-gradient(135deg,var(--accent),var(--accent) 4px,var(--accent-soft) 4px,var(--accent-soft) 8px)}.share-track.is-unknown{height:24px;display:flex;align-items:center;padding:0 8px}.share-unknown{font-size:12px;color:var(--muted)}
.work-footnote{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;color:var(--muted);font-size:12px}.uncertain-inline{color:var(--warn)}
.deep-dive{margin-top:28px;border-top:1px solid var(--line);padding-top:16px}.deep-dive>summary{cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:18px;font-weight:650}.deep-dive>summary::marker{color:var(--accent)}.detail-counts{font-weight:400;color:var(--muted);font-size:12px}.deep-dive-body{padding-top:8px}.detail-section{margin-top:26px}
.notice{padding:13px 16px;background:var(--warn-bg);color:var(--warn);border-left:4px solid var(--warn);border-radius:7px}.notice ul{margin:4px 0;padding-left:22px}.signal{padding:13px 16px;border:1px solid var(--line);border-radius:9px;margin-top:10px}.signal strong{display:block}.signal p{margin:3px 0}.signal-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.controls{display:none;gap:12px;flex-wrap:wrap;align-items:end;margin:14px 0}.js .controls{display:flex}.controls label{display:flex;flex-direction:column;gap:4px;font-size:13px;color:var(--muted)}input,select{border:1px solid var(--line);border-radius:6px;background:var(--paper);padding:8px 10px}input{min-width:235px}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;text-align:left;font-size:14px}th{font-size:12px;color:var(--muted);font-weight:600;border-bottom:2px solid var(--line);padding:10px 9px}td{vertical-align:top;border-bottom:1px solid var(--line);padding:13px 9px}td:first-child{min-width:210px;width:28%}td:nth-child(3),td:nth-child(4){min-width:105px}.select-block{border:0;background:none;padding:0;text-align:left;font-weight:600;color:var(--ink);cursor:pointer}tr[data-selected="true"]{background:var(--accent-soft)}.badge{display:inline-block;font-size:12px;color:var(--muted);white-space:nowrap}.metric{font-variant-numeric:tabular-nums}
details details{font-size:13px;margin-top:8px}summary{width:fit-content}details p{overflow-wrap:anywhere}.detail-list{padding-left:18px;margin:7px 0}
.dependency-graph{display:block;max-width:none;margin:0 auto}.graph-wrap{overflow-x:auto}.graph-node rect{fill:var(--paper);stroke:var(--line);stroke-width:1.4}.graph-node[role="button"]{cursor:pointer}.graph-node[data-selected="true"] rect{fill:var(--accent-soft);stroke:var(--accent);stroke-width:2}.node-title{fill:var(--ink);font-size:14px;font-weight:600}.node-caption{fill:var(--muted);font-size:12px}.graph-node[data-uncertain="true"] rect{stroke:var(--warn)}.uncertain{color:var(--warn);font-size:12px;margin:7px 0}.dependency-edge{fill:none;stroke:var(--line);color:var(--muted);stroke-width:1.8}.dependency-edge[data-selected="true"]{stroke:var(--accent);color:var(--accent);stroke-width:2.5}
*:focus-visible{outline:3px solid var(--accent);outline-offset:3px}.empty{padding:18px 0;color:var(--muted)}[hidden]{display:none!important}.source{padding:15px;background:var(--soft);border-radius:9px}footer{margin-top:28px;border-top:1px solid var(--line);padding-top:15px;font-size:12px;color:var(--muted)}.sr-only{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(max-width:720px){main{margin:0;padding:20px 15px;border-radius:0;border:0}.dashboard-grid,.signal-grid{grid-template-columns:1fr}.summary-card{padding:15px}.summary-value{font-size:30px}.work-bar-head{gap:10px}.work-numbers{max-width:42%}.work-overview-head{display:block}.work-overview-head p{margin-top:3px}.deep-dive>summary{align-items:flex-start}.detail-counts{text-align:right}h1{font-size:23px}}
@media print{body{background:white;color:black}main{max-width:none;border:0;margin:0;padding:0}.controls{display:none!important}.dashboard-grid{grid-template-columns:1.25fr 1fr}.table-wrap,.graph-wrap{overflow:visible}.work-bar,.summary-card,.signal{break-inside:avoid}.dependency-graph{min-width:0}a{color:inherit}.deep-dive{display:block}.deep-dive>summary{display:none}.deep-dive-body{display:block!important}}
"""


SCRIPT = """
(function(){
  const root=document.getElementById('progress-view');
  root.classList.add('js');
  const search=root.querySelector('#work-search');
  const filter=root.querySelector('#work-status');
  const rows=Array.from(root.querySelectorAll('tr[data-work-row]'));
  const count=root.querySelector('#visible-count');
  function applyFilter(){
    if(!search||!filter||!count)return;
    const term=search.value.trim().toLocaleLowerCase();
    let visible=0;
    rows.forEach(function(row){
      row.hidden=!!((term&&!row.dataset.search.includes(term))||(filter.value&&row.dataset.state!==filter.value));
      if(!row.hidden)visible++;
    });
    count.textContent='显示 '+visible+' / '+rows.length+' 条工作记录';
    const empty=root.querySelector('#no-match');
    if(empty)empty.hidden=visible!==0||rows.length===0;
  }
  function select(key){
    root.querySelectorAll('[data-select]').forEach(function(node){
      const active=node.dataset.select===key;
      node.dataset.selected=String(active);
      node.setAttribute('aria-pressed',String(active));
    });
    rows.forEach(function(row){row.dataset.selected=String(row.dataset.workRow===key);});
    root.querySelectorAll('.dependency-edge').forEach(function(edge){edge.dataset.selected=String(edge.dataset.from===key||edge.dataset.to===key);});
    const deep=root.querySelector('#deep-dive');
    if(deep)deep.open=true;
    const target=root.querySelector('[data-detail="'+key+'"]');
    if(target){
      if(search&&filter){search.value='';filter.value='';applyFilter();}
      target.open=true;
      target.scrollIntoView({block:'nearest'});
    }
  }
  if(search&&filter){
    search.addEventListener('input',applyFilter);
    filter.addEventListener('change',applyFilter);
  }
  root.querySelectorAll('[data-select]').forEach(function(node){
    node.addEventListener('click',function(){select(node.dataset.select);});
    if(node.tagName.toLowerCase()!=='button')node.addEventListener('keydown',function(event){
      if(event.key==='Enter'||event.key===' '){event.preventDefault();select(node.dataset.select);}
    });
  });
  applyFilter();
})();
"""


def render_progress_html(report: dict[str, Any], *, output_path: Path | None = None) -> str:
    if report["diagnostic_only"]:
        diagnostic = json.dumps(report["runtime"], ensure_ascii=False, indent=2, allow_nan=False)
        warnings = "".join(f"<li>{_esc(item)}</li>" for item in report["limitations"])
        return (
            '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
            f'<title>TPlan 运行时来源诊断</title><style>{STYLE}</style></head><body><main>'
            f'<h1>运行时来源诊断</h1><p>Mission：{_esc(report["mission"]["title"])}</p>'
            f'<div class="notice"><p>运行时状态：{_esc(report["runtime"]["status"])}</p><ul>{warnings}</ul></div>'
            f'<section><h2>诊断明细</h2><pre style="white-space:pre-wrap;overflow-wrap:anywhere">{_esc(diagnostic)}</pre></section>'
            '</main></body></html>\n'
        )

    view = report["work_view"]
    mission = report["mission"]
    titles = _title_lookup(view, report["task_titles"])
    blocks = _remaining_blocks(view)
    primary_blocks = _primary_blocks(blocks)
    keys = {block["task_id"]: f"block-{index}" for index, block in enumerate(view["blocks"])}
    progress = view.get("progress")
    progress_percent = _progress_percent(progress)

    detail_counts = []
    if view.get("risks"):
        detail_counts.append(f"{len(view['risks'])} 项风险")
    if view.get("blockers"):
        detail_counts.append(f"{len(view['blockers'])} 项阻塞")
    if report["limitations"]:
        detail_counts.append(f"{len(report['limitations'])} 项限制")
    detail_count_text = " · ".join(detail_counts) if detail_counts else "依赖、证据与口径"

    parts = [
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; img-src data:; base-uri \'none\'; form-action \'none\'; connect-src \'none\'">',
        f"<title>{_esc(mission['title'])} · 进展与剩余工作</title><style>{STYLE}</style></head>",
        '<body><main id="progress-view"><header class="page-head"><div class="eyebrow">TPLAN · 进展与剩余工作</div>',
        f"<h1>{_esc(mission['title'])}</h1>",
        f'<p class="meta">Mission 状态：{_esc(_status(mission["status"]))}',
    ]
    if mission["active_task_title"]:
        parts.append(f" · 当前工作：{_esc(mission['active_task_title'])}")
    if report["source"].get("as_of"):
        parts.append(f" · 更新：{_esc(report['source']['as_of'])}")
    parts.append("</p></header>")

    parts.extend([
        '<section id="dashboard" class="dashboard" data-ui-contract="core-progress-dashboard" aria-label="核心进展看板">',
        '<div class="dashboard-grid">',
        '<article class="summary-card"><div class="summary-label">整体进度</div>',
        f'<div class="summary-value">{_esc(_progress_display(progress))}</div>',
    ])
    if progress is not None:
        parts.append(f'<div class="summary-sub">{_esc(progress["label"])}</div>')
    else:
        parts.append('<div class="summary-sub">源计划没有可用的整体进度数值</div>')
    if progress_percent is not None:
        parts.append(
            f'<div class="progress-track" role="img" aria-label="整体进度 {_esc(_progress_display(progress))}">'
            f'<span class="progress-fill" style="width:{progress_percent:.6g}%"></span></div>'
        )
    parts.extend([
        '</article>',
        '<article class="summary-card"><div class="summary-label">剩余工作</div>',
        f'<div class="summary-value">{_esc(_remaining_text(view))}</div>',
        f'<div class="summary-sub">{_esc(_block_count_text(blocks))}</div></article>',
        '</div>',
        '<div class="work-overview"><div class="work-overview-head"><div><h2>剩余工作构成</h2>',
        '<p class="muted">先看还剩哪些工作，以及它们占已估剩余工作量的比例。</p></div></div>',
        '<div id="work" class="work-chart" aria-label="剩余工作块及工作量占比">',
    ])

    if not primary_blocks:
        parts.append('<p class="empty">当前没有可作为独立剩余工作量展示的工作块；验收仍以原状态和证据为准。</p>')
    for block in primary_blocks:
        key = keys[block["task_id"]]
        share = block.get("remaining_share")
        share_label = _range(share, percent=True)
        remaining_label = _range(block.get("remaining"))
        parts.append(
            f'<article class="work-bar" role="button" tabindex="0" data-select="{key}" '
            f'aria-pressed="false" data-primary-work="{_esc(block["task_id"])}">'
            '<div class="work-bar-head"><div class="work-title-wrap">'
            f'<span class="work-title">{_esc(block["title"])}</span>'
            f'<span class="work-state">{_esc(_status(block["status"]) + (" · 待核对" if block.get("remaining_uncertain") else ""))}</span></div>'
            f'<div class="work-numbers"><div class="share-value">{_esc(share_label)}</div>'
            f'<div class="remaining-value">剩余 {_esc(remaining_label)}</div></div></div>'
            f'{_share_bar_html(share)}'
        )
        parts.append("</article>")
    parts.extend([
        '</div>',
        f'<div class="work-footnote"><span>{_esc(SHARE_NOTE)}</span></div>',
        '</div></section>',
        f'<details id="deep-dive" class="deep-dive"><summary><span>查看风险、阻塞、依赖与依据</span>'
        f'<span class="detail-counts">{_esc(detail_count_text)}</span></summary><div class="deep-dive-body">',
        '<section class="detail-section" aria-labelledby="mission-detail-title"><h2 id="mission-detail-title">任务说明</h2>',
        f'<p>{_esc(mission["objective"])}</p>',
    ])
    if view["planning"].get("scope_note"):
        parts.append(f'<p class="muted">覆盖范围：{_esc(view["planning"]["scope_note"])}</p>')
    parts.append("</section>")

    if report["limitations"]:
        parts.append('<section class="detail-section"><div class="notice" role="note"><h3>重要限制</h3><ul>')
        parts.extend(f"<li>{_esc(item)}</li>" for item in report["limitations"])
        parts.append("</ul></div></section>")

    if view.get("risks") or view.get("blockers"):
        parts.append('<section class="detail-section signal-grid" aria-label="已有风险和主要阻塞">')
        for field, label in (("risks", "当前风险"), ("blockers", "主要阻塞点")):
            if not view.get(field):
                continue
            parts.append(f"<div><h2>{label}</h2>")
            for record in view[field]:
                parts.append(f'<article class="signal"><strong>{_esc(record["summary"])}</strong>')
                parts.extend(f'<p>{_esc(detail)}</p>' for detail in _record_details(record, titles))
                parts.append("</article>")
            parts.append("</div>")
        parts.append("</section>")

    if report["constraint_deltas"]:
        parts.append('<section class="detail-section" aria-labelledby="constraints-title"><h2 id="constraints-title">已记录限制与验收反例</h2><p class="muted">以下保留各次记录的时点；历史阻塞的当前有效性以当前状态为准。</p><ul>')
        parts.extend(f"<li>{_esc(_outcome_text(item, report))}</li>" for item in report["constraint_deltas"])
        parts.append("</ul></section>")
    if report["countable_progress"]:
        parts.append('<section class="detail-section" aria-labelledby="verified-title"><h2 id="verified-title">已有结果与依据</h2><ul>')
        parts.extend(f"<li>{_esc(_outcome_text(item, report))}</li>" for item in report["countable_progress"])
        parts.append("</ul></section>")
    if report["confirmed_facts"]:
        parts.append('<section class="detail-section"><h2>已确认事实</h2><ul>')
        parts.extend(f"<li>{_esc(item)}</li>" for item in report["confirmed_facts"])
        parts.append("</ul></section>")
    parts.append(f'<section class="detail-section"><h2>下一步</h2><p>{_esc(report["next_step"])}</p></section>')

    parts.extend([
        '<section id="work-details" class="detail-section" aria-labelledby="work-detail-title"><h2 id="work-detail-title">工作块详情</h2>',
        '<div class="controls"><label for="work-search">查找工作块<input id="work-search" type="search" placeholder="按名称、前置或条件查找"></label>',
        '<label for="work-status">状态<select id="work-status"><option value="">全部状态</option>',
    ])
    for status in dict.fromkeys(block["status"] for block in blocks):
        parts.append(f'<option value="{_esc(status)}">{_esc(_status(status))}</option>')
    parts.append('</select></label><span id="visible-count" class="muted" aria-live="polite"></span></div>')
    if not blocks:
        parts.append('<p class="empty">当前记录中没有剩余工作块；是否满足 Mission 验收仍以原状态和证据为准。</p>')
    parts.append('<div class="table-wrap"><table><caption class="sr-only">完整剩余工作、估计和已记录条件</caption><thead><tr><th scope="col">工作块与依据</th><th scope="col">状态</th><th scope="col">预计剩余</th><th scope="col">剩余占比</th><th scope="col">已知前置</th><th scope="col">并行条件</th></tr></thead><tbody>')
    for block in blocks:
        key = keys[block["task_id"]]
        share = block.get("remaining_share")
        search_text = " ".join([block["title"], _dependencies_text(block), _parallel_text(block)]).lower()
        parts.append(f'<tr data-work-row="{key}" data-state="{_esc(block["status"])}" data-search="{_esc(search_text)}"><td>')
        parts.append(f'<button type="button" class="select-block" data-select="{key}" aria-pressed="false">{_esc(block["title"])}</button>')
        if block.get("remaining_uncertain"):
            parts.append('<p class="uncertain"><strong>状态与剩余依据待核对</strong><br>')
            parts.append(_esc("；".join(block.get("uncertainty_reasons", []))) + "</p>")
        if block.get("accounting_role") == "state_context":
            parts.append('<p class="muted">层级状态记录，不是新增估量块；未分摊或复制父子估计。</p>')
        parts.append(f'<details data-detail="{key}" id="{key}"><summary>查看依据与条件</summary>')
        if block.get("remaining"):
            estimate = block["remaining"]
            parts.append(f'<p>估计依据：{_esc(estimate["basis"])}</p>')
            if estimate.get("confidence"):
                parts.append(f'<p>来源声明的信心：{_esc(_confidence_text(estimate["confidence"]))}</p>')
        else:
            parts.append('<p>源计划未给出剩余估计；未估计不等于零。</p>')
        if share:
            parts.append(f'<p>占比依据：{_esc(share["basis"])}；分母单位：{_esc(share["denominator_unit"])}。</p>')
        parts.append(f'<p>{_esc(_dependencies_text(block))}。</p><p>{_esc(_parallel_text(block))}。</p>')
        if report["include_internal"]:
            parts.append(f'<p class="muted">内部恢复引用：{_esc(block["task_id"])}</p>')
        parts.append(f'</details></td><td><span class="badge">{_esc(_status(block["status"]))}</span></td>')
        parts.append(f'<td class="metric">{_esc(_range(block["remaining"]))}</td><td class="metric">{_esc(_range(share, percent=True))}')
        if share:
            scope = "已估同单位构成" if share["coverage"] == "complete" else "已估同单位构成 · 覆盖不完整"
            parts.append(f'<div class="muted">{_esc(scope)}</div>')
        parts.append(f'</td><td>{_esc(_dependencies_text(block))}</td><td>{_esc(_parallel_text(block))}</td></tr>')
    parts.append('</tbody></table></div><p id="no-match" class="empty" hidden>没有匹配的工作块，请调整搜索或状态筛选。</p></section>')

    parts.extend([
        '<section id="dependencies" class="detail-section" aria-labelledby="dependencies-title"><h2 id="dependencies-title">前置关系与并行条件</h2>',
        f'<p>{_esc(PARALLEL_NOTE)}</p><div class="graph-wrap">{_graph(view, keys)}</div></section>',
        '<section id="sources" class="detail-section source" aria-labelledby="sources-title"><h2 id="sources-title">口径与已有依据</h2>',
        f'<p>{_esc(PROGRESS_NOTE)}</p><p>{_esc(SHARE_NOTE)}</p>',
    ])
    if view.get("progress"):
        parts.append(f'<p>进展声明依据：{_esc(view["progress"]["basis"])}</p>')
    parts.append('<p>工作量来自当前计划的已有估计。不同单位不合并，父子范围不重复计算；未知信息保留为未知。工作量不是完工日期，也不等同于执行成本。</p>')
    if view["planning"].get("source"):
        parts.append(f'<p>计划来源：{_esc(view["planning"]["source"])}</p>')
    if report["include_internal"]:
        parts.append(f'<details><summary>内部恢复引用</summary><p>mission_id: {_esc(mission["id"])}</p><p>Mission digest: {_esc(report["source"]["mission_digest"])}</p><p>Evidence digest: {_esc(report["source"]["evidence_digest"])}</p></details>')
    if report["artifacts"]:
        parts.append('<h3>已有执行记录</h3><ul>')
        for artifact in report["artifacts"]:
            artifact_path = Path(artifact["path"])
            if output_path is not None:
                href = quote(os.path.relpath(artifact_path, output_path.expanduser().resolve().parent).replace(os.sep, "/"), safe="/.")
            else:
                href = artifact_path.as_uri()
            parts.append(f'<li><a href="{_esc(href)}">{_esc(artifact["label"])}</a></li>')
        parts.append('</ul><p class="muted">这些链接指向已有产物，可能早于当前快照；本次只生成理解视图，没有重新生成执行记录。</p>')
    parts.extend([
        '</section></div></details>',
        '<footer>这是从同一 Mission 快照生成的理解视图，不修改任务状态、验收结果或执行授权。终态交付仍需保留 TPlan Standard 执行报告与 SVG 链接。</footer>',
        f"</main><script>{SCRIPT}</script></body></html>\n",
    ])
    return "".join(parts)

def write_progress_artifact(path: Path, rendered: str, mission_dir: Path) -> Path:
    """Write only a delivery artifact, never replace Mission control or Standard reports."""
    output = path.expanduser().resolve()
    root = mission_dir.expanduser().resolve()
    if output.is_relative_to(root) and not output.is_relative_to(root / "reports"):
        raise ValueError("progress output inside the Mission must be under reports/; runtime state is read-only")
    if output.name in {"execution-cost-tree.md", "execution-cost-tree.svg"}:
        raise ValueError("progress output must not replace the Standard execution reports")
    write_text_atomic(output, rendered)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Render TPlan progress and remaining work without changing Mission state.")
    parser.add_argument("mission_dir")
    parser.add_argument("--format", choices=("text", "html", "json"), default="text")
    parser.add_argument("--out", "--output", dest="out", help="Write the view atomically to this file; default is stdout.")
    parser.add_argument("--include-internal", action="store_true", help="Show secondary recovery references.")
    args = parser.parse_args()
    try:
        mission_dir = Path(args.mission_dir)
        report = build_progress_report(read_user_update_snapshot(mission_dir), include_internal=args.include_internal, mission_dir=mission_dir)
        if args.format == "html":
            rendered = render_progress_html(report, output_path=Path(args.out) if args.out else None)
        elif args.format == "json":
            rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        else:
            rendered = render_progress_text(report)
        if args.out:
            output = write_progress_artifact(Path(args.out), rendered, mission_dir)
            print(f"- [TPlan 进展与剩余工作](<{output}>)")
        else:
            print(rendered, end="")
    except (KeyError, OSError, json.JSONDecodeError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
