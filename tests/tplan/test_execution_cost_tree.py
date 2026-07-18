import json
import subprocess
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from observe_model_call import ModelCallObserver
from tplan_runtime import TplanError, record_execution_span, start_execution_span


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_time(value):
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def create_tree_mission(tmp):
    mission_dir = Path(tmp) / "execution-tree"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Ship execution tree",
                    "role": "success-critical",
                    "mission_contribution": "Produces the actual route and cost view.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "S1",
                    "parent_id": "T1",
                    "title": "Capture high-cost execution",
                    "role": "supporting",
                    "parent_contribution": "Captures model and script cost.",
                    "parent_acceptance": "Observed costs are attributed without guessing.",
                    "mission_trace": "via T1 -> A1",
                },
                {
                    "id": "S2",
                    "parent_id": "T1",
                    "title": "Optional untouched path",
                    "role": "exploratory",
                    "parent_contribution": "Tests progressive disclosure.",
                    "parent_acceptance": "Low-signal nodes stay out of the standard view.",
                    "mission_trace": "via T1 -> A1",
                },
            ]
        ),
        encoding="utf-8",
    )
    result = run_script(
        "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "execution-tree",
        "--title",
        "Execution Tree Mission",
        "--objective",
        "Render an honest actual-execution and cost tree.",
        "--acceptance-evidence",
        "A1:Tree and cost report render.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


def record_span(tmp, mission_dir, raw, name):
    path = Path(tmp) / f"{name}.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    result = run_script("record_execution_span.py", str(mission_dir), "--input", str(path))
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result


def render_json(mission_dir, *args):
    result = run_script(
        "render_execution_cost_tree.py",
        str(mission_dir),
        "--format",
        "json",
        *args,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class ExecutionCostTreeTests(unittest.TestCase):
    def test_initialization_creates_trace_and_reports_without_evidence_pollution(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)

            self.assertTrue((mission_dir / "reports").is_dir())
            records = read_jsonl(mission_dir / "execution_trace.jsonl")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["schema_version"], "tplan.execution_trace.v0.1")
            self.assertEqual(records[0]["event_type"], "mission_initialized")
            self.assertEqual([task["id"] for task in records[0]["payload"]["tasks"]], ["T1", "S1", "S2"])
            self.assertEqual((mission_dir / "evidence.jsonl").read_text(encoding="utf-8"), "")

    def test_lifecycle_trace_captures_dynamic_node_status_result_and_shared_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            added = run_script(
                "add_node.py",
                str(mission_dir),
                "--id",
                "E1",
                "--kind",
                "step",
                "--parent-id",
                "S1",
                "--title",
                "Render route",
                "--parent-contribution",
                "Produces the route artifact.",
                "--mission-trace",
                "via S1 -> T1 -> A1",
                "--step-action",
                "Render the tree.",
                "--done-condition",
                "Tree artifact exists.",
            )
            self.assertEqual(added.returncode, 0, added.stderr)
            active = run_script("transition_task.py", str(mission_dir), "--task-id", "E1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)
            completed = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "E1",
                "--status",
                "completed",
                "--outcome-summary",
                "Route artifact rendered",
                "--evidence-ref",
                "E-acceptance",
                "--artifact-ref",
                "reports/execution-cost-tree.md",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            records = read_jsonl(mission_dir / "execution_trace.jsonl")
            self.assertIn("node_added", [record["event_type"] for record in records])
            completion = next(
                record
                for record in records
                if record["event_type"] == "task_status_changed"
                and record["payload"].get("to_status") == "completed"
            )
            active_change = next(
                record
                for record in records
                if record["event_type"] == "active_node_changed"
                and record.get("commit_id") == completion.get("commit_id")
            )
            self.assertEqual(active_change["payload"]["from_task_id"], "E1")
            self.assertEqual(completion["payload"]["outcome_summary"], "Route artifact rendered")
            self.assertEqual(completion["refs"]["evidence_ids"], ["E-acceptance"])

            report = render_json(mission_dir, "--view", "audit")
            node = next(item for item in report["nodes"] if item["id"] == "E1")
            self.assertTrue(node["dynamic"])
            self.assertEqual(node["status"], "completed")
            self.assertEqual(node["attempts"], 1)
            self.assertEqual(node["outcome_summary"], "Route artifact rendered")
            self.assertEqual(node["artifact_refs"], ["reports/execution-cost-tree.md"])

    def test_cost_rollup_separates_model_script_tokens_and_unallocated_shared_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script("transition_task.py", str(mission_dir), "--task-id", "S1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)
            last_event = read_jsonl(mission_dir / "execution_trace.jsonl")[-1]
            base = parse_time(last_event["timestamp"]) + timedelta(microseconds=1)

            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "model",
                        "label": "model inference",
                        "status": "ok",
                        "measurement_source": "platform_reported",
                        "attribution": "exact",
                        "started_at": iso(base),
                        "finished_at": iso(base + timedelta(milliseconds=5)),
                        "duration_ms": 2000,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                    "usage": {
                        "input_tokens": 1000,
                        "cached_input_tokens": 400,
                        "output_tokens": 300,
                        "reasoning_output_tokens": 80,
                    },
                },
                "model",
            )
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "script",
                        "label": "test suite",
                        "status": "ok",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                        "started_at": iso(base + timedelta(milliseconds=1)),
                        "finished_at": iso(base + timedelta(milliseconds=4)),
                        "duration_ms": 500,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                },
                "script",
            )
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": None,
                    "span": {
                        "kind": "model",
                        "label": "shared review",
                        "status": "ok",
                        "measurement_source": "platform_reported",
                        "attribution": "shared",
                        "shared_task_ids": ["S1", "S2"],
                        "started_at": iso(base),
                        "finished_at": iso(base + timedelta(milliseconds=2)),
                        "duration_ms": 200,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                    "usage": {"input_tokens": 100, "output_tokens": 20},
                },
                "shared",
            )
            completed = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S1",
                "--status",
                "completed",
                "--outcome-summary",
                "High-cost path measured",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            report = render_json(mission_dir, "--view", "standard")
            mission_cost = report["mission"]["cost"]
            self.assertEqual(mission_cost["by_kind_resource_ms"], {"model": 2200, "script": 500})
            self.assertEqual(mission_cost["usage"]["input_tokens"], 1100)
            self.assertEqual(mission_cost["usage"]["cached_input_tokens"], 400)
            self.assertEqual(mission_cost["usage"]["output_tokens"], 320)

            node = next(item for item in report["nodes"] if item["id"] == "S1")
            self.assertEqual(node["direct_cost"]["by_kind_resource_ms"], {"model": 2000, "script": 500})
            self.assertEqual(node["direct_cost"]["usage"]["input_tokens"], 1000)
            self.assertEqual(report["overhead"]["by_attribution"]["shared"]["resource_time_ms"], 200)

            markdown = run_script(
                "render_execution_cost_tree.py", str(mission_dir), "--view", "standard"
            )
            self.assertEqual(markdown.returncode, 0, markdown.stderr)
            self.assertIn("Token 入 1.1k / 出 320", markdown.stdout)
            self.assertNotIn("Token 入 1.5k", markdown.stdout)

            compact = render_json(mission_dir, "--view", "compact", "--top-cost", "1")
            self.assertEqual(compact["visible_node_ids"], ["T1", "S1"])
            self.assertEqual(
                compact["trace"]["selection_reasons"]["S1"],
                ["top_direct_cost"],
            )
            self.assertIn("selected_path", compact["trace"]["selection_reasons"]["T1"])
            compact_text = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "compact",
                "--top-cost",
                "1",
                "--format",
                "text",
            )
            self.assertEqual(compact_text.returncode, 0, compact_text.stderr)
            self.assertIn("└─ Ship execution tree", compact_text.stdout)
            self.assertIn("   └─ Capture high-cost execution", compact_text.stdout)
            self.assertIn("LLM 2.0s（平台上报） · 脚本 500ms（宿主实测）", compact_text.stdout)
            self.assertIn("→ High-cost path measured", compact_text.stdout)

    def test_elapsed_reconciliation_conserves_time_and_agent_turn_is_only_an_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script("transition_task.py", str(mission_dir), "--task-id", "S1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)
            base = parse_time(read_jsonl(mission_dir / "execution_trace.jsonl")[-1]["timestamp"]) + timedelta(
                microseconds=1
            )

            spans = [
                ("model", 0, 5, "platform_reported"),
                ("script", 1, 4, "host_measured"),
                ("agent_turn", 0, 6, "host_measured"),
            ]
            for kind, start_ms, finish_ms, source in spans:
                raw = {
                    "task_id": "S1",
                    "span": {
                        "kind": kind,
                        "label": f"{kind} coverage",
                        "status": "ok",
                        "measurement_source": source,
                        "attribution": "exact",
                        "started_at": iso(base + timedelta(milliseconds=start_ms)),
                        "finished_at": iso(base + timedelta(milliseconds=finish_ms)),
                        "duration_ms": finish_ms - start_ms,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                }
                if kind in {"model", "agent_turn"}:
                    raw["usage"] = {"input_tokens": 100, "output_tokens": 20}
                record_span(
                    tmp,
                    mission_dir,
                    raw,
                    kind,
                )
            completed = run_script(
                "transition_task.py", str(mission_dir), "--task-id", "S1", "--status", "completed"
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            report = render_json(mission_dir, "--view", "standard")
            node = next(item for item in report["nodes"] if item["id"] == "S1")
            reconciliation = node["subtree_elapsed_reconciliation"]
            self.assertEqual(reconciliation["exact_interval_coverage_ms"], 5)
            self.assertEqual(reconciliation["excluded_envelope_span_count"], 1)
            self.assertEqual(
                node["elapsed_ms"],
                reconciliation["exact_interval_coverage_ms"]
                + reconciliation["not_exactly_recorded_elapsed_ms"],
            )
            mission_reconciliation = report["mission"]["elapsed_reconciliation"]
            self.assertEqual(
                report["mission"]["elapsed_ms"],
                mission_reconciliation["exact_interval_coverage_ms"]
                + mission_reconciliation["not_exactly_recorded_elapsed_ms"],
            )
            self.assertEqual(node["inclusive_cost"]["by_kind_resource_ms"]["model"], 5)
            self.assertEqual(node["inclusive_cost"]["additive_resource_time_ms"], 8)
            self.assertEqual(node["inclusive_cost"]["usage"]["input_tokens"], 100)
            self.assertEqual(node["inclusive_cost"]["usage"]["output_tokens"], 20)

            standard = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "standard")
            self.assertEqual(standard.returncode, 0, standard.stderr)
            self.assertIn(
                "LLM调用累计 5ms（平台上报） · 脚本累计 3ms（宿主实测）",
                standard.stdout,
            )
            self.assertIn("未被精确记录", standard.stdout)
            self.assertNotIn("Agent turn 包络", standard.stdout)
            audit = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "audit")
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("Agent turn 包络：1 个 span，6ms（宿主实测）", audit.stdout)

    def test_standard_and_audit_preserve_every_real_node_and_declared_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script("transition_task.py", str(mission_dir), "--task-id", "S1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)
            completed = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S1",
                "--status",
                "completed",
                "--outcome-summary",
                "Cost path completed",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

            compact = render_json(mission_dir, "--view", "compact")
            standard = render_json(mission_dir, "--view", "standard")
            audit = render_json(mission_dir, "--view", "audit")
            self.assertEqual(compact["visible_node_ids"], ["T1"])
            self.assertEqual(standard["visible_node_ids"], ["T1", "S1", "S2"])
            self.assertEqual(audit["visible_node_ids"], ["T1", "S1", "S2"])
            self.assertEqual(standard["trace"]["hidden_node_count"], 0)
            self.assertEqual(standard["trace"]["structure_fidelity"], "one_to_one")
            self.assertEqual(
                standard["tree_edges"],
                [
                    {"from": "mission", "to": "T1"},
                    {"from": "T1", "to": "S1"},
                    {"from": "T1", "to": "S2"},
                ],
            )
            self.assertEqual(compact["trace"]["hidden_node_count"], 2)
            self.assertTrue(compact["trace"]["projection"])
            self.assertEqual(compact["presentation"], "unicode_text_tree")
            self.assertNotIn("timeline", compact)
            self.assertEqual(compact["trace"]["selection_reasons"], {"T1": ["root"]})

            compact_text = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "compact",
                "--format",
                "text",
            )
            self.assertEqual(compact_text.returncode, 0, compact_text.stderr)
            for label in ["LLM调用累计", "脚本累计", "工具累计", "等待累计", "Token", "结果："]:
                self.assertNotIn(label, compact_text.stdout)
            self.assertIn("Mission · Execution Tree Mission", compact_text.stdout)
            self.assertIn("└─ Ship execution tree", compact_text.stdout)
            self.assertIn("LLM 未采集 · 脚本 未采集", compact_text.stdout)
            self.assertNotIn("Capture high-cost execution", compact_text.stdout)

            compact_svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "compact",
                "--format",
                "svg",
            )
            self.assertNotEqual(compact_svg.returncode, 0)
            self.assertIn("compact view uses a Unicode text tree", compact_svg.stderr)

    def test_standard_svg_is_a_vertical_timeline_with_one_card_per_real_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            for task_id, status in [
                ("T1", "active"),
                ("S1", "active"),
                ("S1", "completed"),
                ("T1", "completed"),
            ]:
                result = run_script(
                    "transition_task.py",
                    str(mission_dir),
                    "--task-id",
                    task_id,
                    "--status",
                    status,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            report = render_json(mission_dir, "--view", "standard")
            self.assertEqual(report["schema_version"], "tplan.execution_cost_tree.v0.5")
            self.assertEqual(report["timeline"]["axis"], "vertical")
            self.assertEqual(
                report["timeline"]["row_positioning"],
                "first_observed_chronological",
            )
            self.assertEqual(
                report["timeline"]["row_spacing"],
                "ordinal_not_duration_proportional",
            )
            observed_offsets = [
                row["start_offset_ms"]
                for row in report["timeline"]["rows"]
                if row["start_offset_ms"] is not None
            ]
            self.assertEqual(observed_offsets, sorted(observed_offsets))

            svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "standard",
                "--format",
                "svg",
            )
            self.assertEqual(svg.returncode, 0, svg.stderr)
            root = ET.fromstring(svg.stdout)
            self.assertEqual(root.attrib["data-layout"], "vertical-execution-timeline")
            task_cards = [
                element
                for element in root.iter()
                if element.attrib.get("class") == "task-card"
            ]
            self.assertEqual(
                [element.attrib["data-task-id"] for element in task_cards],
                [row["node_id"] for row in report["timeline"]["rows"]],
            )
            self.assertEqual(len(task_cards), report["trace"]["visible_node_count"])
            range_bars = [
                element.attrib["data-task-id"]
                for element in root.iter()
                if element.attrib.get("class") == "node-range"
            ]
            self.assertEqual(
                range_bars,
                [
                    row["node_id"]
                    for row in report["timeline"]["rows"]
                    if row["start_offset_ms"] is not None
                    and row["finish_offset_ms"] is not None
                ],
            )
            tree_edges = {
                (element.attrib["data-tree-from"], element.attrib["data-tree-to"])
                for element in root.iter()
                if "data-tree-from" in element.attrib
            }
            self.assertEqual(
                tree_edges,
                {(edge["from"], edge["to"]) for edge in report["tree_edges"]},
            )
            self.assertIn("纵向行距不代表持续时间", svg.stdout)
            self.assertNotIn("flowchart TB", svg.stdout)

    def test_markdown_output_writes_and_embeds_timeline_svg_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            output = Path(tmp) / "execution-tree.md"
            result = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "standard",
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            svg_output = output.with_suffix(".svg")
            self.assertTrue(svg_output.is_file())
            self.assertIn("rendered_execution_cost_tree_svg", result.stdout)
            markdown = output.read_text(encoding="utf-8")
            self.assertIn(
                "![TPlan 纵向实际执行时间轴](<execution-tree.svg>)",
                markdown,
            )
            self.assertIn("布局：`vertical_execution_timeline`", markdown)
            self.assertNotIn("flowchart TB", markdown)
            root = ET.parse(svg_output).getroot()
            self.assertEqual(root.attrib["data-layout"], "vertical-execution-timeline")

    def test_compact_markdown_writes_only_a_unicode_text_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            output = Path(tmp) / "execution-summary.md"
            result = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "compact",
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("rendered_execution_cost_tree_svg", result.stdout)
            self.assertFalse(output.with_suffix(".svg").exists())
            markdown = output.read_text(encoding="utf-8")
            self.assertIn("# TPlan 执行摘要", markdown)
            self.assertIn("```text", markdown)
            self.assertIn("Mission · Execution Tree Mission", markdown)
            self.assertIn("└─ Ship execution tree", markdown)
            self.assertIn("直接成本 Top 5", markdown)
            self.assertNotIn("<svg", markdown)

    def test_compact_selects_signal_nodes_and_preserves_their_real_ancestors(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S1",
                "--status",
                "active",
            )
            self.assertEqual(active.returncode, 0, active.stderr)
            started = parse_time(read_jsonl(mission_dir / "execution_trace.jsonl")[-1]["timestamp"])
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "script",
                        "label": "second attempt",
                        "status": "ok",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                        "started_at": iso(started + timedelta(milliseconds=1)),
                        "finished_at": iso(started + timedelta(milliseconds=2)),
                        "duration_ms": 1,
                        "attempt": 2,
                        "parent_span_id": None,
                    },
                },
                "second-attempt",
            )
            completed = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S1",
                "--status",
                "completed",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            blocked = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S2",
                "--status",
                "blocked",
            )
            self.assertEqual(blocked.returncode, 0, blocked.stderr)

            compact = render_json(
                mission_dir,
                "--view",
                "compact",
                "--top-cost",
                "0",
            )
            self.assertEqual(compact["visible_node_ids"], ["T1", "S1", "S2"])
            self.assertEqual(compact["trace"]["selection_reasons"]["S1"], ["retry"])
            self.assertEqual(
                compact["trace"]["selection_reasons"]["S2"],
                ["status_signal"],
            )
            self.assertEqual(
                compact["trace"]["selection_reasons"]["T1"],
                ["root", "selected_path"],
            )
            text = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "compact",
                "--top-cost",
                "0",
                "--format",
                "text",
            )
            self.assertEqual(text.returncode, 0, text.stderr)
            self.assertIn("Capture high-cost execution ✅", text.stdout)
            self.assertIn("attempt 2", text.stdout)
            self.assertIn("Optional untouched path ⛔ 受阻", text.stdout)

    def test_legacy_missions_report_partial_or_snapshot_coverage_without_inventing_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            trace_path = mission_dir / "execution_trace.jsonl"
            trace_path.unlink()

            snapshot = render_json(mission_dir, "--view", "audit")
            self.assertEqual(snapshot["trace"]["coverage"], "snapshot_only")
            self.assertIsNone(snapshot["mission"]["elapsed_ms"])
            self.assertTrue(all(node["active_duration_ms"] is None for node in snapshot["nodes"]))
            self.assertEqual(snapshot["mission"]["cost"]["span_count"], 0)

            active = run_script("transition_task.py", str(mission_dir), "--task-id", "S1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)
            partial = render_json(mission_dir, "--view", "audit")
            self.assertEqual(partial["trace"]["coverage"], "partial")
            self.assertIsNone(partial["mission"]["elapsed_ms"])
            self.assertIsNotNone(partial["mission"]["observed_elapsed_ms"])
            partial_node = next(node for node in partial["nodes"] if node["id"] == "S1")
            self.assertIsNone(partial_node["active_duration_ms"])
            self.assertEqual(partial_node["active_duration_source"], "partial")
            self.assertEqual(partial["mission"]["cost"]["span_count"], 0)
            self.assertEqual(partial["timeline"]["offset_origin"], "first_observed_trace")
            self.assertEqual(partial["timeline"]["range_bar_scale"], "linear_observed_window")
            audit = run_script(
                "render_execution_cost_tree.py", str(mission_dir), "--view", "audit"
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("LLM调用累计 未采集 · 脚本累计 未采集", audit.stdout)
            self.assertIn("左侧是已观测相对时间", audit.stdout)
            self.assertIn("观测窗口结束 ≥", audit.stdout)

    def test_privacy_guard_rejects_raw_content_without_appending_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            records_before = read_jsonl(mission_dir / "execution_trace.jsonl")
            started = parse_time(records_before[0]["timestamp"])
            bad = Path(tmp) / "bad-span.json"
            bad.write_text(
                json.dumps(
                    {
                        "task_id": "S1",
                        "span": {
                            "kind": "model",
                            "prompt": "raw prompt must never be stored",
                            "status": "ok",
                            "measurement_source": "platform_reported",
                            "attribution": "exact",
                            "started_at": iso(started),
                            "finished_at": iso(started + timedelta(milliseconds=1)),
                            "duration_ms": 1,
                            "attempt": 1,
                            "parent_span_id": None,
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = run_script("record_execution_span.py", str(mission_dir), "--input", str(bad))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("forbidden raw-content field", result.stderr)
            self.assertEqual(read_jsonl(mission_dir / "execution_trace.jsonl"), records_before)

    def test_unavailable_measurements_render_unknown_instead_of_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            started = parse_time(read_jsonl(mission_dir / "execution_trace.jsonl")[0]["timestamp"])
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "model",
                        "label": "opaque model call",
                        "status": "unknown",
                        "measurement_source": "unavailable",
                        "attribution": "exact",
                        "started_at": iso(started),
                        "finished_at": iso(started),
                        "duration_ms": 0,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                },
                "unavailable",
            )

            report = render_json(mission_dir, "--view", "standard")
            self.assertEqual(report["mission"]["cost"]["usage_coverage"], "unavailable")
            self.assertEqual(
                report["mission"]["cost"]["by_kind_measurement_sources"],
                {"model": {"unavailable": 1}},
            )
            self.assertIn("S1", report["visible_node_ids"])
            markdown = run_script("render_execution_cost_tree.py", str(mission_dir))
            self.assertEqual(markdown.returncode, 0, markdown.stderr)
            self.assertIn("LLM调用累计 未知 · 脚本累计 未采集", markdown.stdout)
            self.assertIn("Token 未知", markdown.stdout)

    def test_inferred_token_usage_is_visibly_marked_as_estimated(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            started = parse_time(read_jsonl(mission_dir / "execution_trace.jsonl")[0]["timestamp"])
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "model",
                        "label": "estimated model usage",
                        "status": "ok",
                        "measurement_source": "inferred",
                        "attribution": "exact",
                        "started_at": iso(started),
                        "finished_at": iso(started + timedelta(milliseconds=10)),
                        "duration_ms": 10,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                    "usage": {"input_tokens": 1200, "output_tokens": 180},
                    "usage_source": "inferred",
                },
                "inferred-usage",
            )

            markdown = run_script("render_execution_cost_tree.py", str(mission_dir))
            self.assertEqual(markdown.returncode, 0, markdown.stderr)
            self.assertIn("LLM调用累计 ≈10ms（估算）", markdown.stdout)
            self.assertIn("Token ≈入 1.2k / 出 180", markdown.stdout)
            self.assertNotIn("墙钟", markdown.stdout)

    def test_traced_command_records_exit_metadata_but_not_command_or_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            result = run_script(
                "run_traced_command.py",
                str(mission_dir),
                "--task-id",
                "S1",
                "--label",
                "safe no-op",
                "--",
                sys.executable,
                "-c",
                "pass",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            records = read_jsonl(mission_dir / "execution_trace.jsonl")
            started, completed = records[-2:]
            self.assertEqual(started["event_type"], "span_started")
            self.assertEqual(completed["event_type"], "span_completed")
            self.assertEqual(started["span"]["span_id"], completed["span"]["span_id"])
            self.assertEqual(completed["span"]["kind"], "script")
            self.assertEqual(completed["metadata"], {"exit_code": 0})
            raw_trace = (mission_dir / "execution_trace.jsonl").read_text(encoding="utf-8")
            self.assertNotIn(sys.executable, raw_trace)
            self.assertNotIn('"command"', raw_trace)
            self.assertNotIn('"stdout"', raw_trace)
            self.assertNotIn('"stderr"', raw_trace)

    def test_model_call_observer_records_paired_host_measurement_and_platform_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            observer = ModelCallObserver(
                mission_dir,
                task_id="S1",
                label="campaign recommendation call",
                provider="example-provider",
                model="example-model",
                operation="recommendation",
            )

            def invoke_model():
                time.sleep(0.003)
                return {
                    "raw_response": "must not enter the trace",
                    "usage": {"input_tokens": 240, "output_tokens": 60},
                }

            result = observer.invoke(
                invoke_model,
                usage_from_result=lambda response: response["usage"],
            )
            self.assertEqual(result["raw_response"], "must not enter the trace")

            records = read_jsonl(mission_dir / "execution_trace.jsonl")
            pair = [
                record
                for record in records
                if record.get("span", {}).get("span_id") == observer.started_record["span"]["span_id"]
            ]
            self.assertEqual([record["event_type"] for record in pair], ["span_started", "span_completed"])
            self.assertNotIn("started_at", pair[0]["span"])
            self.assertEqual(pair[1]["span"]["measurement_source"], "host_measured")
            self.assertGreaterEqual(pair[1]["span"]["duration_ms"], 2)
            self.assertEqual(pair[1]["usage_source"], "platform_reported")
            self.assertEqual(pair[1]["usage"], {"input_tokens": 240, "output_tokens": 60})
            self.assertEqual(
                pair[1]["metadata"],
                {
                    "model": "example-model",
                    "operation": "recommendation",
                    "provider": "example-provider",
                },
            )
            raw_trace = (mission_dir / "execution_trace.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("must not enter the trace", raw_trace)

            report = render_json(mission_dir, "--view", "audit")
            self.assertEqual(report["schema_version"], "tplan.execution_cost_tree.v0.5")
            self.assertEqual(report["trace"]["started_span_count"], 1)
            self.assertEqual(report["trace"]["completed_span_count"], 1)
            self.assertEqual(report["trace"]["open_span_count"], 0)
            markdown = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "audit")
            self.assertEqual(markdown.returncode, 0, markdown.stderr)
            self.assertIn("调用端实测", markdown.stdout)
            self.assertIn("不等于平台内部纯推理时间", markdown.stdout)

    def test_model_call_observer_records_error_before_reraising(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            observer = ModelCallObserver(
                mission_dir,
                task_id="S1",
                label="failing recommendation call",
            )

            def fail_model():
                raise RuntimeError("provider unavailable")

            with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
                observer.invoke(fail_model)

            records = read_jsonl(mission_dir / "execution_trace.jsonl")
            pair = [
                record
                for record in records
                if record.get("span", {}).get("span_id") == observer.started_record["span"]["span_id"]
            ]
            self.assertEqual([record["event_type"] for record in pair], ["span_started", "span_completed"])
            self.assertEqual(pair[1]["span"]["status"], "error")
            self.assertNotIn("provider unavailable", (mission_dir / "execution_trace.jsonl").read_text())

    def test_open_span_is_visible_but_excluded_from_cost_and_mismatched_completion_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            started = start_execution_span(
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "model",
                        "label": "interrupted recommendation call",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                },
            )
            measured_start = parse_time(started["timestamp"]) + timedelta(microseconds=1)
            with self.assertRaisesRegex(TplanError, "task_id mismatch"):
                record_execution_span(
                    mission_dir,
                    {
                        "task_id": "S2",
                        "span": {
                            "span_id": started["span"]["span_id"],
                            "status": "ok",
                            "started_at": iso(measured_start),
                            "finished_at": iso(measured_start + timedelta(milliseconds=1)),
                            "duration_ms": 1,
                        },
                    },
                )

            report = render_json(mission_dir, "--view", "audit")
            self.assertEqual(report["trace"]["started_span_count"], 1)
            self.assertEqual(report["trace"]["completed_span_count"], 0)
            self.assertEqual(report["trace"]["open_span_count"], 1)
            self.assertEqual(report["mission"]["cost"]["span_count"], 0)
            node = next(item for item in report["nodes"] if item["id"] == "S1")
            self.assertEqual(node["direct_open_span_count"], 1)
            audit = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "audit")
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("未结束调用：1 个", audit.stdout)
            self.assertIn("因此不计入累计成本", audit.stdout)

    def test_concurrent_span_processes_do_not_lose_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            started = parse_time(read_jsonl(mission_dir / "execution_trace.jsonl")[0]["timestamp"])
            inputs = []
            for index in range(2):
                path = Path(tmp) / f"concurrent-{index}.json"
                path.write_text(
                    json.dumps(
                        {
                            "task_id": "S1",
                            "span": {
                                "kind": "script",
                                "label": f"concurrent observer {index}",
                                "status": "ok",
                                "measurement_source": "host_measured",
                                "attribution": "exact",
                                "started_at": iso(started),
                                "finished_at": iso(started + timedelta(milliseconds=1)),
                                "duration_ms": 1,
                                "attempt": 1,
                                "parent_span_id": None,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                inputs.append(path)

            processes = [
                subprocess.Popen(
                    [
                        sys.executable,
                        str(REPO / "skills" / "tplan" / "scripts" / "record_execution_span.py"),
                        str(mission_dir),
                        "--input",
                        str(path),
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for path in inputs
            ]
            results = [process.communicate(timeout=5) for process in processes]
            self.assertEqual([process.returncode for process in processes], [0, 0], results)
            records = read_jsonl(mission_dir / "execution_trace.jsonl")
            spans = [record for record in records if record["event_type"] == "span_completed"]
            self.assertEqual(len(spans), 2)
            self.assertEqual(len({record["span"]["span_id"] for record in spans}), 2)


if __name__ == "__main__":
    unittest.main()
