#!/usr/bin/env python3
"""SVG presentation for TPlan execution-cost reports."""

from __future__ import annotations

from typing import Any

from outcome_attribution import attribution_audit_lines, attribution_text
from tplan_runtime import TplanError
from execution_cost_tree import (
    LLM_KINDS, SCRIPT_KINDS, STATUS_ICONS, STATUS_LABELS, TOOL_KINDS, WAIT_KINDS,
    _elapsed_scope_label, _execution_presentation_title, _fmt_covered_duration,
    _fmt_kind_duration, _fmt_not_exactly_recorded, _fmt_timeline_offset,
    _fmt_tokens_compact, _html, _node_cost_view, _shorten,
    _standard_mission_header_lines, _standard_node_content_lines,
    _svg_node_status_details, _svg_status_palette, _svg_text,
)


def render_svg(report: dict[str, Any]) -> str:
    """Render a portrait SVG: chronological rows plus the real hierarchy overlay."""
    if report["view"] == "compact":
        raise TplanError("compact view uses a Unicode text tree; SVG is only available for standard/audit")
    mission = report["mission"]
    timeline = report["timeline"]
    node_by_id = {node["id"]: node for node in report["nodes"]}
    rows = timeline["rows"]
    view = report["view"]
    hotspot_by_id = {
        item["task_id"]: item for item in report.get("duration_hotspots", {}).get("tasks", [])
    }
    time_coverage = timeline.get("offset_coverage") or report["trace"]["coverage"]
    standard_node_lines = (
        {
            row["node_id"]: _standard_node_content_lines(
                node_by_id[row["node_id"]], row, time_coverage=time_coverage,
            )
            for row in rows
        }
        if view == "standard" else {}
    )
    standard_header_lines = _standard_mission_header_lines(report) if view == "standard" else []
    width = 1180
    header_x = 32
    header_y = 24
    header_width = width - 64
    header_height = 288 if view == "audit" else max(168, 120 + 24 * len(standard_header_lines))
    axis_x = 112
    card_base_x = 270
    depth_indent = 42
    right_margin = 34
    legend_y = header_y + header_height + 30
    row_top = legend_y + 22
    card_height = 296 if view == "audit" else max(
        154, 54 + 25 * max((len(lines) for lines in standard_node_lines.values()), default=4)
    )
    row_gap_by_kind = {"task": 30, "subtask": 18, "step": 12}
    row_ys: list[float] = []
    row_cursor = float(row_top)
    for index, row in enumerate(rows):
        if index:
            row_kind = node_by_id[row["node_id"]]["kind"]
            row_cursor += row_gap_by_kind.get(row_kind, 16)
        row_ys.append(row_cursor)
        row_cursor += card_height
    footer_height = 70
    content_bottom = row_cursor if rows else row_top + card_height
    height = content_bottom + footer_height
    axis_start_y = row_ys[0] + card_height / 2 if rows else row_top + card_height / 2
    axis_end_y = row_ys[-1] + card_height / 2 if rows else axis_start_y
    mission_elapsed = timeline.get("window_elapsed_ms")
    time_label = (
        "实际相对时间" if time_coverage == "exact" else
        "已观测相对时间" if time_coverage == "partial" else "无执行时间刻度"
    )
    mission_status = STATUS_LABELS.get(mission["status"], mission["status"])
    mission_cost = mission["cost"]
    mission_reconciliation = mission["elapsed_reconciliation"]
    report_title = _execution_presentation_title(report)
    visible_node_label = "可见真实节点" if report["trace"]["projection"] else "真实节点"
    coverage_warning_count = len(report["trace"].get("coverage_diagnostics", []))
    runtime = report["runtime"]
    time_domain_description = (
        "左侧刻度显示 Mission 生命周期相对时间，时间条按同一 Mission 历时等比例显示"
        if time_coverage == "exact" else
        "左侧刻度只显示已观测窗口相对时间，时间条不代表完整 Mission 历时"
        if time_coverage == "partial" else
        "没有执行时间观测，卡片按声明拓扑顺序排列且不显示时间条"
    )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="tplan-title tplan-desc" '
            f'data-layout="vertical-execution-timeline" data-view="{_html(view)}" '
            f'data-schema-version="{_html(report["schema_version"])}">'
        ),
        f'<title id="tplan-title">{_html(mission["title"])} · {_html(report_title)}</title>',
        (
            '<desc id="tplan-desc">纵向排列真实任务节点；'
            f'{time_domain_description}；弱配色折线保留真实父子关系；'
            '缩进、6/4/2px 主干与分支结构线、短层级标记、类型牌及标题字重共同区分 Task、SubTask 与 Step；'
            'Task 主干与分支全线不透明以保持同色；父子线共享接头由父级等效色不透明覆盖，'
            '避免子级颜色透出混色；状态颜色集中在状态标签，异常节点才使用状态底色；中性耗时排名标签不表示失败。</desc>'
        ),
        "<style>",
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif}",
        ".report-title{font-size:22px;font-weight:700;fill:#ffffff}",
        ".mission-title{font-size:18px;font-weight:650;fill:#dbeafe}",
        ".mission-meta{font-size:14px;fill:#dbeafe}",
        ".legend{font-size:13px;fill:#475569}",
        ".time-label{font-size:12px;font-variant-numeric:tabular-nums;fill:#475569}",
        ".node-title-task{font-size:16px;font-weight:700;fill:#0f172a}",
        ".node-title-subtask{font-size:15px;font-weight:650;fill:#0f172a}",
        ".node-title-step{font-size:14px;font-weight:600;fill:#0f172a}",
        ".kind-label{font-size:11px;font-weight:750;letter-spacing:.35px}",
        ".node-meta{font-size:12.5px;fill:#475569}",
        ".node-metric{font-size:13px;fill:#1e293b}",
        ".node-result{font-size:12.5px;fill:#334155}",
        ".status-label{font-size:12px;font-weight:650}",
        ".duration-hotspot-label{font-size:12px;font-weight:650;fill:#475569}",
        ".tree-edge{fill:none;stroke-linecap:round;stroke-linejoin:round}",
        ".time-guide{stroke:#cbd5e1;stroke-width:1;stroke-dasharray:3 5}",
        ".axis{stroke:#64748b;stroke-width:2}",
        ".range-track{fill:#e8edf3}",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#f8fafc"/>',
        f'<rect x="{header_x}" y="{header_y}" width="{header_width}" height="{header_height}" rx="16" fill="#172554" stroke="#3b82f6" stroke-width="1.5"/>',
        _svg_text(58, 58, report_title, "report-title"),
        _svg_text(58, 88, _shorten(mission["title"], 72), "mission-title"),
        *(
            [
                _svg_text(58, 116 + index * 24, _shorten(part, 135), "mission-meta")
                for index, part in enumerate(standard_header_lines)
            ]
            if view == "standard" else [
                _svg_text(58, 116, f"Mission · {mission_status} · {_elapsed_scope_label(mission['elapsed_coverage'], mission=True)} {_fmt_covered_duration(mission['elapsed_ms'], mission['observed_elapsed_ms'], mission['elapsed_coverage'])}", "mission-meta"),
                _svg_text(58, 140, f"LLM调用累计 {_fmt_kind_duration(mission_cost, LLM_KINDS, host_label='调用端实测')} · 脚本累计 {_fmt_kind_duration(mission_cost, SCRIPT_KINDS)}", "mission-meta"),
                _svg_text(58, 164, f"工具累计 {_fmt_kind_duration(mission_cost, TOOL_KINDS)} · 等待累计 {_fmt_kind_duration(mission_cost, WAIT_KINDS)} · 未被精确记录 {_fmt_not_exactly_recorded(mission_reconciliation)}", "mission-meta"),
                _svg_text(58, 188, f"Token {_fmt_tokens_compact(mission_cost)} · {visible_node_label} {report['trace']['visible_node_count']}/{report['trace']['total_node_count']} · 产出归因 P{len(mission['outcome_attribution']['countable_progress'])}/C{len(mission['outcome_attribution']['constraint_deltas'])} · 覆盖 {report['trace']['coverage']}" + (f" · 生命周期告警 {coverage_warning_count}" if coverage_warning_count else "") + f" · 运行时 {runtime['status']} · {view}", "mission-meta"),
                *[
                    _svg_text(58, 212 + index * 24, ("Mission 审计：" if index == 0 else "") + _shorten(part, 135), "mission-meta")
                    for index, part in enumerate(attribution_audit_lines(mission["outcome_attribution"]))
                ],
            ]
        ),
        _svg_text(32, legend_y, f"纵向=首次执行；左侧是{time_label}；蓝灰条=起止/持续；层级线=Task 主干 6 / SubTask 分支 4 / Step 末梢 2px；中性标签=Task 耗时排名。", "legend"),
    ]

    if rows:
        lines.append(f'<line x1="{axis_x}" y1="{axis_start_y}" x2="{axis_x}" y2="{axis_end_y}" class="axis"/>')

    positions: dict[str, dict[str, float]] = {}
    for index, row in enumerate(rows):
        node = node_by_id[row["node_id"]]
        card_x = card_base_x + row["depth"] * depth_indent
        card_y = row_ys[index]
        card_width = width - right_margin - card_x
        center_y = card_y + card_height / 2
        positions[node["id"]] = {"x": card_x, "y": card_y, "width": card_width, "height": card_height, "center_y": center_y, "kind": node["kind"]}
        lines.extend([
            f'<line x1="{axis_x + 8}" y1="{center_y}" x2="{card_x - 10}" y2="{center_y}" class="time-guide"/>',
            f'<circle cx="{axis_x}" cy="{center_y}" r="5" fill="#ffffff" stroke="#475569" stroke-width="2"/>',
            _svg_text(axis_x - 12, center_y + 4, _fmt_timeline_offset(row["start_offset_ms"], time_coverage), "time-label", anchor="end"),
        ])

    edge_paint_order = {"step": 0, "subtask": 1, "task": 2}
    edge_styles = {
        "task": {"width": 6.0, "color": "#64748b", "opacity": 1.0, "opaque_equivalent": "#64748b"},
        "subtask": {"width": 4.0, "color": "#8b5cf6", "opacity": 0.72, "opaque_equivalent": "#aa88f8"},
        "step": {"width": 2.0, "color": "#60a5fa", "opacity": 0.84, "opaque_equivalent": "#78b3fa"},
    }
    painted_edges = sorted(report["tree_edges"], key=lambda edge: edge_paint_order.get(positions.get(edge["to"], {}).get("kind", ""), -1))
    junction_caps: dict[tuple[str, float, float, float], dict[str, Any]] = {}
    for edge in painted_edges:
        child_position = positions.get(edge["to"])
        if child_position is None:
            continue
        child_x, child_y = child_position["x"], child_position["center_y"]
        edge_style = edge_styles.get(child_position["kind"], {"width": 2.0, "color": "#94a3b8", "opacity": 0.72, "opaque_equivalent": "#a7b0bd"})
        if edge["from"] == "mission":
            branch_x = card_base_x - 28
            path = f"M {branch_x} {header_y + header_height} V {child_y} H {child_x}"
        else:
            parent_position = positions.get(edge["from"])
            if parent_position is None:
                continue
            parent_x, parent_y = parent_position["x"], parent_position["center_y"]
            branch_x = min(parent_x, child_x) - 18
            path = f"M {parent_x} {parent_y} H {branch_x} V {child_y} H {child_x}"
            parent_kind = parent_position["kind"]
            parent_style = edge_styles.get(parent_kind)
            if parent_style is not None:
                junction_caps[(edge["from"], parent_x, parent_y, branch_x)] = {"parent_id": edge["from"], "kind": parent_kind, "x1": branch_x, "x2": parent_x, "y": parent_y, "style": parent_style}
        lines.append(f'<path d="{path}" class="tree-edge" stroke="{edge_style["color"]}" stroke-width="{edge_style["width"]}" opacity="{edge_style["opacity"]}" data-tree-from="{_html(edge["from"])}" data-tree-to="{_html(edge["to"])}" data-child-kind="{_html(child_position["kind"])}"/>')

    for cap in sorted(junction_caps.values(), key=lambda item: edge_paint_order.get(item["kind"], -1)):
        cap_style = cap["style"]
        lines.append(f'<line x1="{cap["x1"]}" y1="{cap["y"]}" x2="{cap["x2"]}" y2="{cap["y"]}" class="tree-edge junction-cap" stroke="{cap_style["opaque_equivalent"]}" stroke-width="{cap_style["width"]}" opacity="1" data-junction-parent="{_html(cap["parent_id"])}" data-parent-kind="{_html(cap["kind"])}"/>')

    for row in rows:
        node = node_by_id[row["node_id"]]
        hotspot = hotspot_by_id.get(node["id"])
        position = positions[node["id"]]
        card_x, card_y, card_width = position["x"], position["y"], position["width"]
        status_fill, status_stroke, text_color = _svg_status_palette(node["status"])
        if node["status"] == "completed":
            card_fill, card_stroke, card_stroke_width = "#ffffff", "#d8e0ea", 1.2
        else:
            card_fill, card_stroke, card_stroke_width = status_fill, status_stroke, 1.5
        cost, reconciliation, scope_label = _node_cost_view(node)
        kind_label = {"task": "Task", "subtask": "SubTask", "step": "Step"}.get(node["kind"], str(node["kind"] or "Node"))
        kind_style = {
            "task": {"label": "TASK", "fill": "#475569", "stroke": "#475569", "text": "#ffffff"},
            "subtask": {"label": "SUBTASK", "fill": "#f3e8ff", "stroke": "#8b5cf6", "text": "#6d28d9"},
            "step": {"label": "STEP", "fill": "#eff6ff", "stroke": "#3b82f6", "text": "#1d4ed8"},
        }.get(node["kind"], {"label": kind_label.upper(), "fill": "#f8fafc", "stroke": "#94a3b8", "text": "#475569"})
        hierarchy_accent = {"task": {"color": "#64748b", "width": 6}, "subtask": {"color": "#8b5cf6", "width": 4}, "step": {"color": "#60a5fa", "width": 2}}.get(node["kind"], {"color": "#94a3b8", "width": 2})
        title_class = {"task": "node-title-task", "subtask": "node-title-subtask", "step": "node-title-step"}.get(node["kind"], "node-title-subtask")
        status = STATUS_LABELS.get(node["status"], node["status"])
        icon = STATUS_ICONS.get(node["status"], "•")
        title = f"{_shorten(node['title'], 32 if view != 'audit' else 46)} · {node['id']}"
        elapsed = _fmt_covered_duration(node["elapsed_ms"], node["observed_elapsed_ms"], node["elapsed_coverage"])
        range_text = f"{_fmt_timeline_offset(row['start_offset_ms'], time_coverage)} → {_fmt_timeline_offset(row['finish_offset_ms'], time_coverage)}"
        hotspot_rank_attr = f' data-duration-hotspot-rank="{hotspot["rank"]}"' if hotspot else ""
        lines.extend([
            f'<g id="node-{_html(node["id"])}" class="task-card" data-task-id="{_html(node["id"])}" data-depth="{row["depth"]}" data-start-offset-ms="{row["start_offset_ms"] if row["start_offset_ms"] is not None else ""}" data-finish-offset-ms="{row["finish_offset_ms"] if row["finish_offset_ms"] is not None else ""}"{hotspot_rank_attr}>',
            f'<rect x="{card_x}" y="{card_y}" width="{card_width}" height="{card_height}" rx="10" fill="{card_fill}" stroke="{card_stroke}" stroke-width="{card_stroke_width}"/>',
            f'<rect x="{card_x + 3}" y="{card_y + 13}" width="{hierarchy_accent["width"]}" height="28" rx="{hierarchy_accent["width"] / 2}" fill="{hierarchy_accent["color"]}" class="hierarchy-accent" data-node-kind="{_html(node["kind"])}"/>',
            f'<rect x="{card_x + 18}" y="{card_y + 13}" width="72" height="24" rx="6" fill="{kind_style["fill"]}" stroke="{kind_style["stroke"]}" stroke-width="1.25"/>',
            f'<text x="{card_x + 54}" y="{card_y + 30}" class="kind-label" text-anchor="middle" fill="{kind_style["text"]}">{_html(kind_style["label"])}</text>',
            _svg_text(card_x + 104, card_y + 29, title, title_class),
            f'<rect x="{card_x + card_width - 94}" y="{card_y + 13}" width="76" height="24" rx="12" fill="{status_stroke}" opacity=".13"/>',
            f'<text x="{card_x + card_width - 56}" y="{card_y + 30}" class="status-label" text-anchor="middle" fill="{text_color}">{_html(icon + " " + status)}</text>',
        ])
        if hotspot:
            hotspot_badge_x = card_x + card_width - 224
            lines.extend([
                f'<rect x="{hotspot_badge_x}" y="{card_y + 13}" width="118" height="24" rx="12" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.25"/>',
                f'<text x="{hotspot_badge_x + 59}" y="{card_y + 30}" class="duration-hotspot-label" text-anchor="middle">耗时排名 #{hotspot["rank"]}</text>',
            ])
        if view == "standard":
            lines.extend(_svg_text(card_x + 18, card_y + 54 + index * 25, text, class_name) for index, (text, class_name) in enumerate(standard_node_lines[node["id"]]))
            range_y = card_y + card_height - 14
        else:
            lines.extend([
                _svg_text(card_x + 18, card_y + 54, _svg_node_status_details(node, scope_label), "node-meta"),
                _svg_text(card_x + 18, card_y + 79, f"时间 {range_text} · {_elapsed_scope_label(node['elapsed_coverage'])} {elapsed} · 未被精确记录 {_fmt_not_exactly_recorded(reconciliation)}", "node-metric"),
                _svg_text(card_x + 18, card_y + 104, f"LLM调用累计 {_fmt_kind_duration(cost, LLM_KINDS, host_label='调用端实测')} · 脚本累计 {_fmt_kind_duration(cost, SCRIPT_KINDS)}", "node-metric"),
                _svg_text(card_x + 18, card_y + 129, f"工具累计 {_fmt_kind_duration(cost, TOOL_KINDS)} · 等待累计 {_fmt_kind_duration(cost, WAIT_KINDS)} · Token {_fmt_tokens_compact(cost)}", "node-metric"),
                _svg_text(card_x + 18, card_y + 151, f"结果：{_shorten(node['outcome_summary'], 82) if node['outcome_summary'] else '未记录'}", "node-result"),
                _svg_text(card_x + 18, card_y + 174, f"产出归因：{_shorten(attribution_text(node['outcome_attribution']), 74)}", "node-result"),
            ])
            lines.extend(_svg_text(card_x + 18, card_y + 197 + index * 23, ("审计：" if index == 0 else "") + _shorten(part, 105), "node-meta") for index, part in enumerate(attribution_audit_lines(node["outcome_attribution"])))
            range_y = card_y + 282
        track_x = card_x + 18
        track_width = card_width - 36
        lines.append(f'<rect x="{track_x}" y="{range_y}" width="{track_width}" height="6" rx="3" class="range-track"/>')
        start_offset, finish_offset = row["start_offset_ms"], row["finish_offset_ms"]
        if mission_elapsed and start_offset is not None and finish_offset is not None:
            start_fraction = min(1.0, max(0.0, start_offset / mission_elapsed))
            finish_fraction = min(1.0, max(start_fraction, finish_offset / mission_elapsed))
            range_x = min(track_x + track_width - 4.0, track_x + start_fraction * track_width)
            range_width = min(max(4.0, (finish_fraction - start_fraction) * track_width), track_x + track_width - range_x)
            lines.append(f'<rect x="{range_x:.2f}" y="{range_y}" width="{range_width:.2f}" height="6" rx="4" fill="#64748b" class="node-range" data-task-id="{_html(node["id"])}"/>')
        lines.append("</g>")

    footer_y = content_bottom + 40
    if time_coverage == "exact":
        footer_text = f"Mission 结束 {_fmt_timeline_offset(mission_elapsed, time_coverage)} · 纵向行距不代表持续时间；精确时间由刻度、节点起止值及统一比例时间条表达。"
    elif time_coverage == "partial":
        footer_text = f"观测窗口结束 {_fmt_timeline_offset(mission_elapsed, time_coverage)} · 纵向行距不代表持续时间；刻度和时间条仅表达已观测事件的相对位置，不代表完整 Mission 历时。"
    else:
        footer_text = "没有执行时间观测；纵向行距不代表持续时间；卡片仅保留声明拓扑、状态和异常信号，未显示成本不按零处理。"
    lines.extend([
        f'<line x1="32" y1="{footer_y - 24}" x2="{width - 32}" y2="{footer_y - 24}" stroke="#e2e8f0"/>',
        _svg_text(32, footer_y, footer_text, "legend"),
    ])
    if report["trace"]["hidden_node_count"]:
        lines.append(_svg_text(32, footer_y + 24, f"投影视图省略 {report['trace']['hidden_node_count']} 个真实节点；Standard/Audit 可查看完整拓扑。", "legend"))
    lines.append("</svg>")
    return "\n".join(lines) + "\n"
