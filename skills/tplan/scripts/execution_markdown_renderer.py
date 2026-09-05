#!/usr/bin/env python3
"""Compact-text, Markdown, and JSON presentation for TPlan execution-cost reports."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from outcome_attribution import attribution_audit_text, attribution_text, short_attribution_label
from tplan_runtime import TplanError
from execution_cost_tree import (
    ABNORMAL_TASK_STATUSES, STATUS_LABELS,
    _compact_cost_summary, _compact_node_summary, _compact_source_legend, _compact_status,
    _elapsed_scope_label, _execution_presentation_title, _fmt_covered_duration,
    _fmt_duration, _fmt_kind_duration, _fmt_not_exactly_recorded, _fmt_resource_duration,
    _fmt_tokens, _fmt_tokens_inline, _node_cost_view, _shorten,
)


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _coverage_note(report: dict[str, Any]) -> str:
    coverage = report["trace"]["coverage"]
    if coverage == "exact":
        return "生命周期追踪可从 Mission 初始化完整回放到当前快照；各类成本仍只包含宿主实际上报的 span。"
    if coverage == "partial":
        return "生命周期追踪不完整或与当前快照不一致；这里只显示已观测窗口，不把最后一条事件当作 Mission 完成时间。"
    return "没有执行轨迹；当前仅展示 Mission 快照，时间与 Token 成本保持未知。"


def _coverage_diagnostic_text(report: dict[str, Any]) -> str | None:
    diagnostics = report["trace"].get("coverage_diagnostics", [])
    if not diagnostics:
        return None
    return "；".join(f"{item['code']}: {item['message']}" for item in diagnostics)


def _runtime_diagnostic_text(report: dict[str, Any]) -> str | None:
    diagnostics = report["runtime"].get("diagnostics", [])
    if not diagnostics:
        return None
    return "；".join(f"{item['code']}: {item['message']}" for item in diagnostics)


def render_compact_text(report: dict[str, Any]) -> str:
    if report["view"] != "compact":
        raise TplanError("text tree is only available for compact view")
    mission = report["mission"]
    mission_elapsed = _fmt_covered_duration(
        mission["elapsed_ms"], mission["observed_elapsed_ms"], mission["elapsed_coverage"]
    )
    if mission["elapsed_coverage"] == "partial":
        mission_elapsed = f"观测 {mission_elapsed}"
    mission_token = _fmt_tokens_inline(mission["cost"])
    mission_line = (
        f"Mission · {_shorten(mission['title'], 60)} {_compact_status(mission['status'])} "
        f"{mission_elapsed} · {_compact_cost_summary(mission['cost'])}"
    )
    if mission_token != "—":
        mission_line += f" · Tok {mission_token}"
    mission_line += f" · {short_attribution_label(mission['outcome_attribution'])}"
    lines = [mission_line, "层级：[T] Task · [ST] SubTask · [P] Step"]
    node_by_id = {node["id"]: node for node in report["nodes"]}
    selection_reasons = {
        task_id: set(reasons)
        for task_id, reasons in report["trace"]["selection_reasons"].items()
    }
    order = {node["id"]: index for index, node in enumerate(report["nodes"])}
    children: dict[str, list[str]] = defaultdict(list)
    roots: list[str] = []
    for node in report["nodes"]:
        parent_id = node.get("parent_id")
        if parent_id in node_by_id:
            children[parent_id].append(node["id"])
        else:
            roots.append(node["id"])
    for parent_id in children:
        children[parent_id].sort(key=lambda task_id: order[task_id])
    roots.sort(key=lambda task_id: order[task_id])

    def visit(task_id: str, prefix: str, is_last: bool) -> None:
        connector = "└─ " if is_last else "├─ "
        lines.append(prefix + connector + _compact_node_summary(
            node_by_id[task_id], selection_reasons.get(task_id, set())
        ))
        next_prefix = prefix + ("   " if is_last else "│  ")
        child_ids = children.get(task_id, [])
        for index, child_id in enumerate(child_ids):
            visit(child_id, next_prefix, index == len(child_ids) - 1)

    for index, task_id in enumerate(roots):
        visit(task_id, "", index == len(roots) - 1)
    lines.extend([
        "",
        f"显示 {report['trace']['visible_node_count']}/{report['trace']['total_node_count']}；省略 {report['trace']['hidden_node_count']}",
        f"{_compact_source_legend(mission['cost'])}；未精确记录 {_fmt_not_exactly_recorded(mission['elapsed_reconciliation'])}；— 未采集 · ? 未知 · ≈ 估算 · ≥ 部分采集",
    ])
    runtime_text = _runtime_diagnostic_text(report)
    if runtime_text:
        lines.extend(["", f"运行时告警：{runtime_text}"])
    return "\n".join(lines) + "\n"


def _append_telemetry_capture_markdown(lines: list[str], report: dict[str, Any]) -> None:
    capture = report["telemetry_capture"]
    activation = capture["activation"]
    labels = {
        "local_tools": "本地工具/脚本",
        "hosted_tools": "托管工具",
        "model_turns": "模型/Turn",
        "tokens": "Token",
        "waits": "等待",
        "subagents": "SubAgent",
    }
    lines.extend([
        "", "## Codex 遥测覆盖", "",
        (
            f"绑定：`{capture['binding']['status']}`；范围：`{capture['binding'].get('scope') or 'none'}`；"
            f"generation：`{capture['binding'].get('generation') or 'none'}`。"
            "没有观测值的类别保持 `not_reported`，不会按零处理。"
        ), "",
        (
            f"激活：`{activation['status']}`；当前 surface：`{activation.get('active_surface') or 'none'}`；"
            f"原因：{activation['reason']}。"
        ), "",
        "| Surface | 激活状态 | Codex build/version | Hook source | 原因 |",
        "| --- | --- | --- | --- | --- |",
    ])
    for surface_name, surface in activation["surfaces"].items():
        source = surface.get("source")
        source_text = "none"
        if isinstance(source, dict):
            source_text = (
                f"{source['scope']}:{source['path']}；hash={source.get('sha256') or 'absent'}；"
                f"enumerated={str(source['enumerated']).lower()}；trust={','.join(source['trust_statuses']) or 'none'}；"
                f"enabled={source.get('enabled')}"
            )
        build = surface.get("host_build") or surface.get("codex_version") or "none"
        lines.append("| " + " | ".join((
            _markdown_cell(surface_name), _markdown_cell(surface["status"]),
            _markdown_cell(build), _markdown_cell(source_text), _markdown_cell(surface["reason"]),
        )) + " |")
    lines.extend(["", "| 通道 | 状态 | 已完成 span | 原因 |", "| --- | --- | ---: | --- |"])
    for name, channel in capture["channels"].items():
        lines.append("| " + " | ".join((
            labels[name], _markdown_cell(channel["status"]), str(channel["observed_span_count"]),
            _markdown_cell(channel["reason"]),
        )) + " |")


def render_markdown(report: dict[str, Any], *, timeline_svg_ref: str | None = None) -> str:
    if report["view"] == "compact":
        if timeline_svg_ref is not None:
            raise TplanError("compact Markdown is a Unicode text tree and has no SVG sidecar")
        lines = [
            "# TPlan 执行摘要", "", f"> {_coverage_note(report)}", "", "```text",
            render_compact_text(report).rstrip(), "```", "",
            "Task/SubTask 成本为其真实子树累计；Step 为直接成本。没有出现的下级节点只是被省略，没有被合并。",
            "", "LLM、脚本、工具和等待是累计资源时间，可能相互重叠；逐节点详情见 Standard/Audit。",
        ]
        diagnostic_text = _coverage_diagnostic_text(report)
        if diagnostic_text:
            lines[3:3] = [f"> 覆盖告警：{diagnostic_text}", ""]
        runtime_text = _runtime_diagnostic_text(report)
        if runtime_text:
            lines[3:3] = [f"> 运行时告警：{runtime_text}", ""]
        return "\n".join(lines).rstrip() + "\n"

    mission = report["mission"]
    cost = mission["cost"]
    overhead = report["overhead"]["cost"]
    presentation_title = _execution_presentation_title(report)
    markdown_title = {
        "exact": "# TPlan 实际执行与成本树",
        "partial": "# TPlan 已观测执行窗口与成本树",
        "snapshot_only": "# TPlan Mission 结构快照与成本边界",
    }[report["trace"]["coverage"]]
    lines = [markdown_title, "", f"> {_coverage_note(report)}", ""]
    diagnostic_text = _coverage_diagnostic_text(report)
    if diagnostic_text:
        lines.extend([f"> 覆盖告警：{diagnostic_text}", ""])
    runtime_text = _runtime_diagnostic_text(report)
    if runtime_text:
        lines.extend([f"> 运行时告警：{runtime_text}", ""])
    if timeline_svg_ref:
        lines.extend([f"![{presentation_title}](<{timeline_svg_ref}>)", ""])
    else:
        from execution_svg_renderer import render_svg
        inline_svg = render_svg(report).split("\n", 1)[1].rstrip()
        lines.extend([inline_svg, ""])
    if report["view"] == "audit":
        _append_telemetry_capture_markdown(lines, report)
    lines.append("")
    visible_node_label = "可见真实节点" if report["trace"]["projection"] else "真实节点"
    lines.append(
        f"视图：`{report['view']}`；布局：`vertical_execution_timeline`；"
        f"{visible_node_label}：{report['trace']['visible_node_count']}/{report['trace']['total_node_count']}。"
    )
    if report["trace"]["hidden_node_count"]:
        lines.append(
            f"这是投影视图，省略了 {report['trace']['hidden_node_count']} 个真实节点；"
            "使用 `--view standard` 或 `--view audit` 查看完整拓扑。"
        )
    mission_attribution = mission["outcome_attribution"]
    node_yield_counts = mission_attribution.get("node_yield_counts", {})
    lines.append(
        "产出归因："
        f"{len(mission_attribution['countable_progress'])} 项可计推进 · "
        f"{len(mission_attribution['constraint_deltas'])} 项关键约束 · "
        f"{node_yield_counts.get('writeback_only', 0)} 个仅状态写回节点 · "
        f"{node_yield_counts.get('telemetry_only', 0)} 个仅遥测节点。"
    )
    lines.extend([
        "",
        "口径：覆盖 exact 时，实际历时按可回放生命周期的开始到结束计算；覆盖 partial 时，"
        "这里只显示已观测窗口，不把它当作 Mission 完成时间。LLM 调用、脚本、工具和等待显示的是"
        "各自累计资源时间，嵌套或并行时不可直接相加。调用端实测覆盖完整模型请求，可能包含"
        "排队、网络和流式传输，不等于平台内部纯推理时间。未被精确记录 = 实际历时减去已完成且"
        "时间来源精确的区间并集；它不自动属于 LLM、脚本或其他类别。已缓存输入包含在输入 Token 中，"
        "不会重复累计。",
    ])
    if report["trace"]["open_span_count"]:
        lines.append(
            f"未结束调用：{report['trace']['open_span_count']} 个；已有入口记录但没有配对结束记录，"
            "因此不计入累计成本。"
        )
    if report["view"] == "audit" and cost["envelope_span_count"]:
        lines.append(
            f"Agent turn 包络：{cost['envelope_span_count']} 个 span，"
            f"{_fmt_kind_duration(cost, {'agent_turn'})}；仅用于审计，不计入 LLM 调用累计或可加资源时间。"
        )
    if report["view"] == "audit" and overhead["span_count"]:
        lines.append(
            f"Mission 级共享/未归属 span：{_fmt_duration(overhead['additive_resource_time_ms'])} 可加资源时间，"
            f"{_fmt_tokens(overhead)} Token；这些成本不分摊到任务节点。"
        )
    notable = [
        node for node in report["nodes"]
        if node["outcome_summary"] or node["status"] in ABNORMAL_TASK_STATUSES
        or node["attempts"] > 1 or node["direct_cost"]["error_span_count"]
        or node["direct_open_span_count"]
    ]
    if notable and report["view"] == "audit":
        lines.extend(["", "## 结果与异常", ""])
        for node in notable:
            details: list[str] = []
            if node["outcome_summary"]:
                details.append(_shorten(node["outcome_summary"], 180))
            if node["attempts"] > 1:
                details.append(f"执行 {node['attempts']} 次")
            if node["direct_cost"]["error_span_count"]:
                details.append(f"{node['direct_cost']['error_span_count']} 个错误 span")
            if node["direct_open_span_count"]:
                details.append(f"{node['direct_open_span_count']} 个未结束调用")
            if not details:
                details.append(STATUS_LABELS.get(node["status"], node["status"]))
            lines.append(f"- {node['title']} (`{node['id']}`): {'; '.join(details)}")
    if report["view"] == "audit":
        mission_audit_relevant = any(
            mission_attribution[field]
            for field in ("countable_progress", "constraint_deltas", "state_writebacks", "unclassified_writebacks", "warnings")
        )
        audit_nodes = [
            node for node in report["nodes"]
            if node["outcome_attribution"]["unclassified_writebacks"]
            or node["outcome_attribution"]["warnings"]
            or node["outcome_attribution"]["countable_progress"]
            or node["outcome_attribution"]["constraint_deltas"]
        ]
        if mission_audit_relevant or audit_nodes:
            lines.extend(["", "## 产出归因审计", ""])
            if mission_audit_relevant:
                lines.append(
                    f"- Mission (`{mission['id']}`): {attribution_text(mission_attribution)}；"
                    f"{attribution_audit_text(mission_attribution)}。"
                )
            for node in audit_nodes:
                attribution = node["outcome_attribution"]
                evidence_ids = sorted({
                    evidence_id
                    for bucket in ("countable_progress", "constraint_deltas", "unclassified_writebacks")
                    for item in attribution[bucket]
                    for evidence_id in item.get("evidence_ids", [])
                })
                commit_ids = sorted({
                    commit_id
                    for bucket in ("countable_progress", "constraint_deltas", "state_writebacks", "unclassified_writebacks")
                    for item in attribution[bucket]
                    for commit_id in item.get("commit_ids", [])
                })
                reasons = [item.get("reason") for item in attribution["unclassified_writebacks"] if isinstance(item.get("reason"), str)]
                warning_codes = [item["code"] for item in attribution["warnings"]]
                lines.append(
                    f"- {node['title']} (`{node['id']}`): {attribution_text(attribution)}；"
                    f"evidence={evidence_ids or ['none']}；commit={commit_ids or ['none']}；"
                    f"unclassified={reasons or ['none']}；warnings={warning_codes or ['none']}。"
                )
        lines.extend([
            "", "## 审计明细", "",
            "| 顺序 | 节点 | 状态 | 产出归因 | "
            f"{_elapsed_scope_label(report['trace']['coverage'])} | 活跃时间 | 次数 | 直接资源 | 子树资源 | 子树未精确记录 | 证据 | 产物 |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ])
        for node in report["nodes"]:
            lines.append("| " + " | ".join([
                str(node["execution_order"] or "—"),
                _markdown_cell(f"{node['title']} ({node['id']})"),
                _markdown_cell(node["actual_state"]),
                _markdown_cell(attribution_text(node["outcome_attribution"])),
                _fmt_covered_duration(node["elapsed_ms"], node["observed_elapsed_ms"], node["elapsed_coverage"]),
                _fmt_covered_duration(node["active_duration_ms"], node["observed_active_duration_ms"], node["active_duration_source"]),
                str(node["attempts"]), _fmt_resource_duration(node["direct_cost"]),
                _fmt_resource_duration(node["inclusive_cost"]),
                _fmt_not_exactly_recorded(node["subtree_elapsed_reconciliation"]),
                str(len(node["evidence_refs"])), str(len(node["artifact_refs"])),
            ]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
