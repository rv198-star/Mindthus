import copy
import json
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from render_progress_view import (
    build_progress_report,
    render_progress_html,
    render_progress_text,
    write_progress_artifact,
)
from work_plan import WORK_PLAN_SCHEMA_VERSION
from tplan_runtime import new_runtime_provenance


def source_mission():
    titles = (
        ("T1", "已经验收的范围", "completed"),
        ("T2", "界面整合", "active"),
        ("T3", "回归测试", "pending"),
        ("T4", "使用文档", "pending"),
        ("T5", "交付验收", "pending"),
    )
    tasks = [
        {
            "id": task_id, "parent_id": None, "kind": "task", "level": 1,
            "title": title, "status": status, "role": "success-critical",
            "mission_contribution": "完成所声明的交付范围",
            "acceptance_evidence": ["A1"], "evidence_links": [],
        }
        for task_id, title, status in titles
    ]
    def estimate(value):
        return {"low": value, "high": value, "unit": "点", "basis": "夹具中的明确剩余估计"}

    return {
        "schema_version": "tplan.v0.1",
        "mission": {
            "id": "progress-fixture", "title": "进展视图测试夹具",
            "objective": "让已有任务、估计和前置关系被准确理解。",
            "status": "active", "human_in_loop": 0, "risk_tolerance": 50,
            "resource_sufficiency": 50,
            "acceptance_evidence": [{"id": "A1", "description": "已有验收要求"}],
        },
        "tasks": tasks, "active_task_id": "T2",
        "work_plan": {
            "schema_version": WORK_PLAN_SCHEMA_VERSION, "coverage": "complete",
            "scope_note": "这是测试夹具，包含五个互不重叠的真实任务节点。",
            "source": "测试中的显式计划记录", "as_of": "2026-10-05T00:00:00Z",
            "progress": {"label": "已验收范围", "value": 30, "unit": "%", "basis": "源计划声明的验收权重，不是任务数量比例"},
            "blocks": [
                {"task_id": "T1", "remaining": estimate(0), "depends_on": []},
                {"task_id": "T2", "remaining": estimate(15), "depends_on": ["T1"], "parallel_conditions": ["两个执行单元可用，界面与文档工作区独立"]},
                {"task_id": "T3", "remaining": estimate(20), "depends_on": ["T2"]},
                {"task_id": "T4", "remaining": estimate(10), "depends_on": ["T1"], "parallel_conditions": ["两个执行单元可用，文档不修改界面工作区"]},
                {"task_id": "T5", "remaining": estimate(15), "depends_on": ["T3", "T4"]},
            ],
        },
    }


def source_events():
    return [{
        "id": "E-accepted", "timestamp": "2026-10-05T00:00:00Z",
        "event_type": "acceptance_passed", "summary": "测试夹具：已验收范围按声明通过。",
        "task_id": "T1", "payload": {"acceptance_ids": ["A1"]},
    }]


def snapshot(mission=None, *, events=None):
    return {
        "mission": copy.deepcopy(mission or source_mission()),
        "events": copy.deepcopy(source_events() if events is None else events), "trace": [],
        "mission_digest": "sha256:" + "1" * 64,
        "evidence_digest": "sha256:" + "2" * 64,
        "interaction_guard_state": {"present": False},
    }


def run_script(name, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / name), *map(str, args)], text=True, capture_output=True)


class HTMLSurface(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []
        self.data = []
        self.in_script = False
        self.script_text = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.extend((tag, key, value) for key, value in attrs)
        if tag == "script":
            self.in_script = True

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False

    def handle_data(self, data):
        self.data.append(data)
        if self.in_script:
            self.script_text.append(data)


class ProgressViewTests(unittest.TestCase):
    def test_three_formats_share_source_ranges_and_preserve_declared_progress(self):
        original = snapshot()
        before = copy.deepcopy(original)
        report = build_progress_report(original)
        self.assertEqual(original, before, "rendering must not mutate the source snapshot")
        self.assertEqual(report["schema_version"], "tplan.progress_view.v1")
        self.assertEqual(report["work_view"]["progress"]["value"], 30)
        self.assertEqual(report["work_view"]["remaining"]["total"], {"low": 60, "high": 60, "unit": "点"})
        text = render_progress_text(report)
        page = render_progress_html(report)
        self.assertIn("已验收范围：30 %", text)
        self.assertIn("进度条：[██████░░░░░░░░░░░░░░] 30%", text)
        self.assertIn("预计剩余工作量：60 点", text)
        self.assertIn("占比 [█████░░░░░░░░░░░░░░░] 25%", text)
        self.assertIn(">30%</div>", page)
        self.assertIn(">已验收范围</div>", page)
        self.assertIn("60 点", page)
        self.assertNotIn("整体完成率：20", text)
        self.assertEqual(json.loads(json.dumps(report))["work_view"]["remaining"], report["work_view"]["remaining"])
        self.assertNotIn("T2", text)

    def test_html_first_screen_contract_is_progress_remaining_work_and_shares(self):
        mission = source_mission()
        mission["work_plan"]["risks"] = [{"summary": "测试风险", "task_ids": ["T3"]}]
        mission["work_plan"]["blockers"] = [{"summary": "测试阻塞", "task_ids": ["T2"], "release_condition": "输入到齐"}]
        report = build_progress_report(snapshot(mission))
        page = render_progress_html(report)

        dashboard_start = page.index('<section id="dashboard"')
        dashboard_end = page.index("</section>", dashboard_start)
        detail_start = page.index('<details id="deep-dive"', dashboard_end)
        dashboard = page[dashboard_start:dashboard_end]

        self.assertIn('data-ui-contract="core-progress-dashboard"', dashboard)
        self.assertIn("整体进度", dashboard)
        self.assertIn(">30%</div>", dashboard)
        self.assertIn("剩余工作", dashboard)
        self.assertIn("60 点", dashboard)
        for title in ("界面整合", "回归测试", "使用文档", "交付验收"):
            self.assertIn(title, dashboard)
        for share in ("25%", "33.3", "16.7"):
            self.assertIn(share, dashboard)

        for secondary in (
            "测试风险", "测试阻塞", "重要限制", "已有结果与依据", "下一步",
            "前置关系与并行条件", "查找工作块", "任务说明",
        ):
            self.assertNotIn(secondary, dashboard)
        self.assertLess(dashboard_end, detail_start)
        self.assertIn('<details id="deep-dive" class="deep-dive">', page)
        self.assertNotIn('<details id="deep-dive" class="deep-dive" open', page)
        self.assertGreater(page.index("测试风险"), detail_start)
        self.assertGreater(page.index("测试阻塞"), detail_start)
        self.assertGreater(page.index("前置关系与并行条件"), detail_start)

    def test_interval_share_bar_uses_source_bounds_without_midpoint(self):
        mission = source_mission()
        estimate = mission["work_plan"]["blocks"][1]["remaining"]
        estimate["low"], estimate["high"] = 10, 20
        report = build_progress_report(snapshot(mission))
        block = next(item for item in report["work_view"]["blocks"] if item["task_id"] == "T2")
        share = block["remaining_share"]
        self.assertNotEqual(share["low"], share["high"])

        text = render_progress_text(report)
        self.assertIn("▒", text)
        self.assertIn("占比图例：█ 为确定下界，▒ 为区间不确定部分", text)
        page = render_progress_html(report)
        dashboard_start = page.index('<section id="dashboard"')
        dashboard_end = page.index("</section>", dashboard_start)
        dashboard = page[dashboard_start:dashboard_end]
        self.assertIn(f'data-share-low="{share["low"]:.10g}"', dashboard)
        self.assertIn(f'data-share-high="{share["high"]:.10g}"', dashboard)
        self.assertIn('class="share-range"', dashboard)
        self.assertNotIn("midpoint", dashboard.lower())

    def test_completed_but_unresolved_work_stays_visible_without_rewriting_status(self):
        for positive_estimate in (False, True):
            with self.subTest(positive_estimate=positive_estimate):
                mission = source_mission()
                if positive_estimate:
                    mission["work_plan"]["blocks"][0]["remaining"]["low"] = 2
                    mission["work_plan"]["blocks"][0]["remaining"]["high"] = 3
                report = build_progress_report(snapshot(mission, events=source_events() if positive_estimate else []))
                view = report["work_view"]
                row = next(block for block in view["blocks"] if block["task_id"] == "T1")
                self.assertEqual(row["status"], "completed")
                self.assertFalse(row["is_remaining"])
                self.assertTrue(row["remaining_uncertain"])
                self.assertIsNone(view["remaining"]["total"])
                self.assertEqual(view["remaining"]["coverage"], "partial")
                text = render_progress_text(report)
                page = render_progress_html(report)
                self.assertIn("已经验收的范围 [已完成]", text)
                self.assertIn("状态与剩余依据待核对", text)
                self.assertIn("状态与剩余依据待核对", page)
                self.assertIn("已声明小计", text)
                self.assertIn("5 个剩余或待核对工作块", page)
                first_row = page.split('data-work-row="block-0"', 1)[1].split("</tr>", 1)[0]
                self.assertLess(first_row.index("状态与剩余依据待核对"), first_row.index("<details"))
                self.assertIn("已完成", first_row)

    def test_graph_keeps_intrinsic_readable_width_for_actual_columns(self):
        page = render_progress_html(build_progress_report(snapshot()))
        self.assertIn('width="472"', page)
        self.assertIn('viewBox="0 0 472 ', page)
        self.assertIn(".node-caption{fill:var(--muted);font-size:12px}", page)
        self.assertNotIn("min-width:580px", page)
        self.assertNotIn("width:100%;min-width", page)

    def test_legacy_relocated_and_incompatible_runtime_have_explicit_read_boundaries(self):
        for case in ("legacy_unpinned", "compatible_relocated", "incompatible"):
            with self.subTest(case=case):
                mission = source_mission()
                if case != "legacy_unpinned":
                    mission["runtime_provenance"] = new_runtime_provenance()
                    fingerprint = mission["runtime_provenance"]["fingerprint"]
                    if case == "compatible_relocated":
                        fingerprint["skill_root"] = "/previous-copy/skills/tplan"
                        fingerprint["script_root"] = "/previous-copy/skills/tplan/scripts"
                    else:
                        fingerprint["build_hash"] = "sha256:" + "0" * 64
                original = snapshot(mission)
                before = copy.deepcopy(original)
                report = build_progress_report(original)
                self.assertEqual(original, before)
                self.assertEqual(report["runtime"]["status"], case)
                text = render_progress_text(report)
                page = render_progress_html(report)
                if case == "incompatible":
                    self.assertTrue(report["diagnostic_only"])
                    self.assertIsNone(report["work_view"])
                    self.assertEqual(report["countable_progress"], [])
                    self.assertIsNone(report["next_step"])
                    self.assertIn("运行时不兼容", text)
                    self.assertIn("runtime_fingerprint_mismatch", text)
                    self.assertIn("runtime_fingerprint_mismatch", page)
                    self.assertNotIn('id="work"', page)
                    self.assertNotIn("预计剩余工作量", text)
                    self.assertNotIn("30 %", page)
                else:
                    self.assertFalse(report["diagnostic_only"])
                    warning = "运行时来源未固定" if case == "legacy_unpinned" else "运行时位置已变化"
                    self.assertIn(warning, text)
                    self.assertGreater(page.index(warning), page.index('id="deep-dive"'))
                    self.assertIn("预计剩余工作量：60 点", text)

    def test_existing_constraints_facts_next_step_and_estimate_confidence_are_preserved(self):
        mission = source_mission()
        mission["mission"]["status"] = "requires_human"
        events = source_events() + [
            {
                "id": "E-failed", "timestamp": "2026-10-05T01:00:00Z",
                "event_type": "acceptance_failed", "task_id": "T1",
                "summary": "最新验收失败：旧编码仍丢字，不能发布。",
                "payload": {"acceptance_ids": ["A1"]},
            },
            {
                "id": "E-finding", "timestamp": "2026-10-05T01:01:00Z",
                "event_type": "key_finding", "task_id": "T2",
                "summary": "事实记录：故障只出现在旧编码输入。", "payload": {},
            },
            {
                "id": "E-stop", "timestamp": "2026-10-05T01:02:00Z",
                "event_type": "stop_report", "task_id": "T2",
                "summary": "停止记录：等待发布范围确认。",
                "payload": {"need_from_human": "请确认旧编码是否属于本次发布的验收范围。"},
            },
        ]
        for confidence, label in (("low", "低"), ("unknown", "未知")):
            with self.subTest(confidence=confidence):
                mission["work_plan"]["blocks"][1]["remaining"]["confidence"] = confidence
                report = build_progress_report(snapshot(mission, events=events))
                self.assertEqual(len(report["constraint_deltas"]), 2)
                self.assertIn(events[2]["summary"], report["confirmed_facts"])
                self.assertEqual(report["next_step"], events[3]["payload"]["need_from_human"])
                self.assertEqual(report["evidence_context"]["E-failed"]["timestamp"], events[1]["timestamp"])
                for output in (render_progress_text(report), render_progress_html(report)):
                    self.assertIn(events[1]["summary"], output)
                    self.assertIn(events[0]["summary"], output)
                    self.assertIn("验收失败记录 · 2026-10-05T01:00:00Z", output)
                    self.assertIn(events[2]["summary"], output)
                    self.assertIn(events[3]["payload"]["need_from_human"], output)
                    self.assertIn("来源声明的信心：" + label, output)
                    self.assertLess(output.index("最新验收失败"), output.index("已有结果与依据"))
                    self.assertIn("历史阻塞的当前有效性", output)

    def test_shared_risk_source_scope_and_recovery_are_visible_without_scope_narrowing(self):
        mission = source_mission()
        signal = {
            "id": "R1", "source_task_id": "T1", "scope": "shared_environment",
            "signal": "共享磁盘的同步写入仍不可靠。", "severity": "high", "confidence": "medium",
            "affected_surfaces": ["验收文件", "运行记录"], "value_effect": "重复执行仍可能留下无效验收依据。",
            "recommended_gate": "environment_health_gate", "recovery_condition": "同步写入验收通过。",
            "status": "active", "created_at": "2026-10-05T01:00:00Z", "updated_at": "2026-10-05T02:00:00Z",
        }
        mission["shared_context"] = {"risk_signals": [signal]}
        report = build_progress_report(snapshot(mission))
        risk = report["work_view"]["risks"][0]
        self.assertEqual(risk["source_kind"], "shared_risk_signal")
        self.assertNotIn("task_ids", risk, "reporting task must not become the entire affected scope")
        for output in (render_progress_text(report), render_progress_html(report)):
            self.assertIn(signal["signal"], output)
            self.assertIn("影响范围：共享环境", output)
            self.assertIn("来源声明的严重程度：高", output)
            self.assertIn("来源声明的信心：中", output)
            self.assertIn("恢复条件：" + signal["recovery_condition"], output)
            self.assertIn("当前共享风险记录", output)
            self.assertIn("2026-10-05T02:00:00Z", output)
        signal["status"] = "resolved"
        next_report = build_progress_report(snapshot(mission))
        self.assertEqual(next_report["work_view"]["risks"], [])

    def test_unresolved_child_state_is_a_visible_record_without_parent_estimate_copy(self):
        mission = source_mission()
        mission["tasks"].append({
            "id": "T1.1", "parent_id": "T1", "kind": "subtask", "level": 2,
            "title": "已完成父任务下仍未结束的子任务", "status": "pending", "role": "supporting",
            "parent_contribution": "核对父任务剩余状态", "parent_acceptance": "完成状态一致",
            "mission_trace": "via T1 -> A1", "evidence_links": [],
        })
        report = build_progress_report(snapshot(mission))
        view = report["work_view"]
        row = next(block for block in view["blocks"] if block["task_id"] == "T1.1")
        self.assertEqual(row["accounting_role"], "state_context")
        self.assertIsNone(row["remaining"])
        self.assertIsNone(view["remaining"]["total"])
        for output in (render_progress_text(report), render_progress_html(report)):
            self.assertIn(row["title"], output)
            self.assertIn("另列 1 个层级状态记录", output)
            self.assertIn("不是新增估量块", output)

    def test_no_plan_preserves_unknown_and_does_not_infer_parallelism(self):
        mission = source_mission()
        del mission["work_plan"]
        report = build_progress_report(snapshot(mission))
        self.assertIsNone(report["work_view"]["progress"])
        self.assertIsNone(report["work_view"]["remaining"]["total"])
        text = render_progress_text(report)
        page = render_progress_html(report)
        self.assertIn("暂无可合计的剩余估计", text)
        self.assertNotIn("进度条：", text, "missing source progress must not create a fake percentage bar")
        self.assertIn("前置信息未提供", text)
        self.assertIn("不能据此确认可并行", text)
        self.assertNotIn("data-from=", page)
        self.assertIn("未估计不等于零", page)
        self.assertNotIn("当前风险</h2>", page)
        self.assertNotIn("主要阻塞点</h2>", page)

    def test_zero_estimates_do_not_become_unknown_or_a_completion_claim(self):
        mission = source_mission()
        for block in mission["work_plan"]["blocks"]:
            block["remaining"]["low"] = block["remaining"]["high"] = 0
        report = build_progress_report(snapshot(mission))
        self.assertEqual(report["work_view"]["remaining"]["total"], {"low": 0, "high": 0, "unit": "点"})
        self.assertTrue(all(row["remaining_share"] is None for row in report["work_view"]["blocks"]))
        text = render_progress_text(report)
        self.assertIn("预计剩余工作量：0 点", text)
        self.assertIn("占比 不可计算", text)
        self.assertEqual(report["mission"]["status"], "active")

    def test_partial_unknown_and_mixed_units_never_display_one_total(self):
        mission = source_mission()
        mission["work_plan"]["coverage"] = "partial"
        mission["work_plan"]["blocks"][1]["remaining"] = None
        mission["work_plan"]["blocks"][2]["remaining"]["unit"] = "小时"
        report = build_progress_report(snapshot(mission))
        self.assertIsNone(report["work_view"]["remaining"]["total"])
        text = render_progress_text(report)
        page = render_progress_html(report)
        self.assertIn("已声明小计", text)
        self.assertIn("不能作为整体总量", page)
        self.assertIn("覆盖不完整", text)
        self.assertIn("未知量未按零处理", page)
        self.assertNotIn("预计剩余工作量：45", text)

    def test_overlapping_parent_child_plan_cannot_gain_a_rendered_total(self):
        mission = source_mission()
        parent = mission["tasks"][1]
        child = {
            "id": "T2.1", "title": "界面内的子任务", "parent_id": parent["id"],
            "kind": "subtask", "level": 2, "status": "pending", "role": "supporting",
            "parent_contribution": "推进界面", "parent_acceptance": "子任务完成",
            "mission_trace": "via T2 -> A1", "evidence_links": [],
        }
        mission["tasks"].append(child)
        mission["work_plan"]["blocks"].append({
            "task_id": "T2.1",
            "remaining": {"low": 3, "high": 5, "unit": "点", "basis": "重复父范围"},
        })
        report = build_progress_report(snapshot(mission))
        self.assertIsNone(report["work_view"]["remaining"]["total"])
        self.assertTrue(report["work_view"]["diagnostics"])
        page = render_progress_html(report)
        self.assertIn("规划元数据未通过校验", page)
        self.assertGreater(page.index("规划元数据未通过校验"), page.index('id="deep-dive"'))

    def test_existing_risks_and_blockers_are_visible_without_flags_and_are_escaped(self):
        mission = source_mission()
        hostile = '<img src="https://example.invalid/collect" onerror="alert(1)">需要核对'
        mission["work_plan"]["risks"] = [{"summary": hostile, "impact": "可能影响验收", "task_ids": ["T3"]}]
        mission["work_plan"]["blockers"] = [{"summary": "等待已指定输入", "release_condition": "取得输入", "task_ids": ["T2"]}]
        mission["tasks"][1]["title"] = '界面 "</script><script>bad()</script>'
        report = build_progress_report(snapshot(mission))
        page = render_progress_html(report)
        parser = HTMLSurface()
        parser.feed(page)
        self.assertIn("当前风险", page)
        self.assertIn("主要阻塞点", page)
        self.assertIn("等待已指定输入", page)
        self.assertIn("解除条件：取得输入", page)
        self.assertNotIn("<img", page)
        self.assertEqual(parser.tags.count("script"), 1)
        self.assertNotIn("bad()", "".join(parser.script_text))
        self.assertFalse(any(key.startswith("on") for _, key, _ in parser.attributes))
        self.assertFalse(any(key in {"src", "srcset"} for _, key, _ in parser.attributes))
        self.assertTrue(all(value.startswith("#") for _, key, value in parser.attributes if key == "href"))
        self.assertIn(hostile, render_progress_text(report))
        self.assertIn('<details id="deep-dive" class="deep-dive">', page)
        self.assertGreater(page.index("可能影响验收"), page.index('id="deep-dive"'))

    def test_human_authority_and_guard_limits_are_preserved_below_the_dashboard(self):
        source = snapshot()
        source["mission"]["mission"]["status"] = "requires_human"
        source["interaction_guard_state"] = {"present": True, "phase": "awaiting_authority", "revision": 7}
        source["mission"]["tasks"][1]["status"] = "blocked"
        report = build_progress_report(source)
        page = render_progress_html(report)
        dashboard_start = page.index('id="dashboard"')
        detail_start = page.index('id="deep-dive"')
        self.assertIn("Mission 状态：等待人类确认", page[:dashboard_start])
        self.assertIn("项限制", page[detail_start:page.index("</summary>", detail_start)])
        for message in ("写保护已开启", "已阻塞的工作块：界面整合"):
            self.assertGreater(page.index(message), detail_start)
        self.assertNotIn("message_ref", page)

    def test_graph_uses_declared_dependencies_and_has_real_selection_controls(self):
        report = build_progress_report(snapshot())
        page = render_progress_html(report)
        parser = HTMLSurface()
        parser.feed(page)
        edges = [value for tag, key, value in parser.attributes if tag == "path" and key == "data-from"]
        self.assertEqual(len(edges), 5)
        self.assertIn('id="work-search"', page)
        self.assertIn('id="work-status"', page)
        self.assertIn("row.hidden=", "".join(parser.script_text))
        self.assertIn("deep.open=true", "".join(parser.script_text))
        self.assertIn("target.open=true", "".join(parser.script_text))
        self.assertIn("前置条件已满足只描述已记录的关系", page)
        self.assertNotIn("fetch(", "".join(parser.script_text))
        self.assertNotIn("XMLHttpRequest", page)

    def test_artifact_writer_cannot_replace_runtime_or_standard_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            mission_dir.mkdir()
            protected = mission_dir / "mission.json"
            protected.write_text("source")
            for target in (protected, mission_dir / "reports" / "execution-cost-tree.md"):
                with self.assertRaises(ValueError):
                    write_progress_artifact(target, "replacement", mission_dir)
            self.assertEqual(protected.read_text(), "source")
            output = write_progress_artifact(mission_dir / "reports" / "progress.html", "<!doctype html>", mission_dir)
            self.assertEqual(output.read_text(), "<!doctype html>")

    def test_existing_standard_artifacts_are_linked_without_writing_or_inventing_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            reports = mission_dir / "reports"
            reports.mkdir(parents=True)
            markdown = reports / "execution-cost-tree.md"
            svg = reports / "execution-cost-tree.svg"
            markdown.write_text("existing execution report")
            svg.write_text("<svg></svg>")
            report = build_progress_report(snapshot(), mission_dir=mission_dir)
            page = render_progress_html(report, output_path=reports / "progress.html")
            self.assertIn('href="execution-cost-tree.md"', page)
            self.assertIn('href="execution-cost-tree.svg"', page)
            self.assertIn("可能早于当前快照", page)
            self.assertIn(str(markdown), render_progress_text(report))
            self.assertEqual(markdown.read_text(), "existing execution report")
            self.assertEqual(svg.read_text(), "<svg></svg>")
            svg.unlink()
            next_report = build_progress_report(snapshot(), mission_dir=mission_dir)
            self.assertEqual([item["path"] for item in next_report["artifacts"]], [str(markdown)])
            self.assertFalse(svg.exists())

    def test_cli_progress_preserves_guard_release_transition_in_text_and_html(self):
        from tests.tplan.test_render_user_update import create_lite_mission

        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            initial = run_script("render_user_update.py", mission_dir, "--progress", "--json")
            self.assertEqual(initial.returncode, 0, initial.stderr)
            first = json.loads(initial.stdout)
            opened = run_script("interaction_guard.py", "begin", mission_dir, "--platform", "test-host", "--message-ref", "M-progress")
            self.assertEqual(opened.returncode, 0, opened.stderr)
            guard = json.loads(opened.stdout)
            protected = run_script("render_user_update.py", mission_dir, "--delivery", "automatic", "--cursor", first["cursor"], "--progress", "--json")
            self.assertEqual(protected.returncode, 0, protected.stderr)
            protected_data = json.loads(protected.stdout)
            self.assertIn("写保护已开启", protected_data["text"])
            awaiting = run_script("interaction_guard.py", "await", mission_dir, "--guard-id", guard["guard_id"], "--expected-revision", guard["revision"], "--message-ref", "M-progress")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr)
            waiting = json.loads(awaiting.stdout)
            closed = run_script("interaction_guard.py", "resume", mission_dir, "--guard-id", guard["guard_id"], "--expected-revision", waiting["revision"], "--message-ref", "M-progress")
            self.assertEqual(closed.returncode, 0, closed.stderr)
            html_path = mission_dir / "reports" / "after-guard.html"
            result = run_script("render_user_update.py", mission_dir, "--delivery", "automatic", "--cursor", protected_data["cursor"], "--html", html_path, "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertTrue(data["changed"])
            self.assertTrue(data["guard_just_released"])
            self.assertEqual(data["update_kind"], "progress")
            self.assertIn("交互保护：已解除", data["text"])
            self.assertIn("交互保护：已解除", html_path.read_text())
            self.assertEqual(data["progress"]["interaction_guard_text"], "交互保护：已解除。")

    def test_inline_html_is_first_class_delivery_and_does_not_require_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            mission_dir.mkdir()
            mission = source_mission()
            (mission_dir / "mission.json").write_text(json.dumps(mission, ensure_ascii=False))
            (mission_dir / "evidence.jsonl").write_text(
                "\n".join(json.dumps(event, ensure_ascii=False) for event in source_events()) + "\n"
            )
            (mission_dir / "execution_trace.jsonl").write_text("")

            inline = run_script("render_user_update.py", mission_dir, "--inline-html")
            self.assertEqual(inline.returncode, 0, inline.stderr)
            self.assertTrue(inline.stdout.startswith("<!doctype html>"))
            self.assertIn('data-select="block-', inline.stdout)
            self.assertIn("dependency-edge", inline.stdout)
            self.assertIn("<script>", inline.stdout)
            self.assertFalse((mission_dir / "reports").exists(), "inline delivery must not persist an artifact")

            envelope_result = run_script("render_user_update.py", mission_dir, "--inline-html", "--json")
            self.assertEqual(envelope_result.returncode, 0, envelope_result.stderr)
            envelope = json.loads(envelope_result.stdout)["inline_html"]
            self.assertEqual(envelope["schema_version"], "explain.inline_html.v1")
            self.assertEqual(envelope["mime_type"], "text/html")
            self.assertEqual(envelope["preferred_surface"], "sandboxed_inline_html")
            self.assertEqual(envelope["preferred_container"], "iframe")
            self.assertIsNone(envelope["fallback_surface"])
            self.assertEqual(envelope["source_inspection_surface"], "html_code_block")
            self.assertEqual(envelope["status"], "prepared_not_rendered")
            self.assertEqual(envelope["html"], inline.stdout)
            self.assertFalse((mission_dir / "reports").exists())

            html_path = mission_dir / "reports" / "progress.html"
            both_result = run_script(
                "render_user_update.py", mission_dir,
                "--inline-html", "--html", html_path, "--json",
            )
            self.assertEqual(both_result.returncode, 0, both_result.stderr)
            both = json.loads(both_result.stdout)
            self.assertEqual(both["html_path"], str(html_path))
            self.assertEqual(html_path.read_text(), both["inline_html"]["html"])

    def test_real_cli_reads_work_plan_and_preserves_existing_delivery_cadence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            mission_dir.mkdir()
            mission = source_mission()
            (mission_dir / "mission.json").write_text(json.dumps(mission, ensure_ascii=False))
            (mission_dir / "evidence.jsonl").write_text("\n".join(json.dumps(event, ensure_ascii=False) for event in source_events()) + "\n")
            (mission_dir / "execution_trace.jsonl").write_text("")
            before = (mission_dir / "mission.json").read_bytes()
            html_path = mission_dir / "reports" / "progress.html"
            output = run_script("render_progress_view.py", mission_dir, "--format", "html", "--out", html_path)
            self.assertEqual(output.returncode, 0, output.stderr)
            self.assertTrue(html_path.read_text().startswith("<!doctype html>"))
            json_result = run_script("render_progress_view.py", mission_dir, "--format", "json")
            self.assertEqual(json_result.returncode, 0, json_result.stderr)
            self.assertEqual(json.loads(json_result.stdout)["work_view"]["remaining"]["total"]["low"], 60)
            initial = run_script("render_user_update.py", mission_dir, "--delivery", "automatic", "--json")
            self.assertEqual(initial.returncode, 0, initial.stderr)
            first = json.loads(initial.stdout)
            self.assertEqual(first["update_kind"], "full")
            self.assertNotIn("progress", first)
            cursor = first["cursor"]
            for expected in ("quiet", "quiet", "heartbeat"):
                update = run_script("render_user_update.py", mission_dir, "--delivery", "automatic", "--cursor", cursor, "--progress", "--json")
                self.assertEqual(update.returncode, 0, update.stderr)
                data = json.loads(update.stdout)
                self.assertEqual(data["update_kind"], expected)
                self.assertNotIn("progress", data)
                cursor = data["cursor"]
            explicit = run_script("render_user_update.py", mission_dir, "--cursor", cursor, "--html", html_path, "--json")
            self.assertEqual(explicit.returncode, 0, explicit.stderr)
            data = json.loads(explicit.stdout)
            self.assertEqual(data["update_kind"], "progress")
            self.assertFalse(data["changed"])
            self.assertEqual(data["html_path"], str(html_path))
            self.assertEqual(data["progress"]["schema_version"], "tplan.progress_view.v1")
            self.assertIn("预计剩余工作量：60 点", data["text"])
            self.assertEqual((mission_dir / "mission.json").read_bytes(), before)

            mission["runtime_provenance"] = new_runtime_provenance()
            mission["runtime_provenance"]["fingerprint"]["build_hash"] = "sha256:" + "0" * 64
            (mission_dir / "mission.json").write_text(json.dumps(mission, ensure_ascii=False))
            incompatible_before = (mission_dir / "mission.json").read_bytes()
            diagnostic = run_script("render_user_update.py", mission_dir, "--delivery", "automatic", "--cursor", data["cursor"], "--html", html_path, "--json")
            self.assertEqual(diagnostic.returncode, 0, diagnostic.stderr)
            diagnosis = json.loads(diagnostic.stdout)
            self.assertEqual(diagnosis["update_kind"], "diagnostic")
            self.assertTrue(diagnosis["progress"]["diagnostic_only"])
            self.assertIsNone(diagnosis["progress"]["work_view"])
            self.assertNotIn('id="work"', html_path.read_text())
            unchanged = run_script("render_user_update.py", mission_dir, "--delivery", "automatic", "--cursor", diagnosis["cursor"], "--progress", "--json")
            self.assertEqual(unchanged.returncode, 0, unchanged.stderr)
            self.assertEqual(json.loads(unchanged.stdout)["update_kind"], "diagnostic")
            self.assertEqual((mission_dir / "mission.json").read_bytes(), incompatible_before)


if __name__ == "__main__":
    unittest.main()
