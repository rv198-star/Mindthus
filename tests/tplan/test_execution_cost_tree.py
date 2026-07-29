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
from execution_cost_tree import _counted_tokens, _duration_hotspots, _span_cost, _usage_owner_event_ids
from tplan_runtime import (
    TplanError,
    begin_interaction_guard,
    record_execution_span,
    start_execution_span,
    stop_interaction_guard,
)


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


def svg_card_text(svg_text, task_id):
    root = ET.fromstring(svg_text)
    card = next(
        element
        for element in root.iter()
        if element.attrib.get("data-task-id") == task_id
        and element.attrib.get("class") == "task-card"
    )
    return " ".join(text.strip() for text in card.itertext() if text.strip())


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


def complete_mission_status(tmp, mission_dir):
    decision = Path(tmp) / "complete-mission-decision.json"
    decision.write_text(
        json.dumps(
            {
                "recommendation": "close",
                "rationale": "All execution-tree acceptance work is complete.",
                "confidence": 95,
                "evidence_links": [],
                "proposed_mutations": [
                    {"type": "set_mission_status", "status": "completed"},
                ],
                "requires_human": False,
                "mission_alignment": "Closing preserves the completed execution-tree state.",
                "path_assessment": {
                    "marginal_roi": "positive",
                    "path_role": "dominant_path",
                    "evidence_delta": "new_evidence_expected",
                },
            }
        ),
        encoding="utf-8",
    )
    result = run_script(
        "apply_decision.py",
        str(mission_dir),
        "--decision",
        str(decision),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)


def complete_tree_mission(tmp, mission_dir):
    for task_id in ("S1", "S2", "T1"):
        result = run_script(
            "transition_task.py",
            str(mission_dir),
            "--task-id",
            task_id,
            "--status",
            "completed",
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    complete_mission_status(tmp, mission_dir)


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
    def test_cost_renderer_refuses_pending_transaction_without_recovery_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            transaction = mission_dir / ".mission-transaction.json"
            transaction.write_text("{}", encoding="utf-8")

            result = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--format",
                "json",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pending Mission transaction", result.stderr)
            self.assertEqual(transaction.read_text(encoding="utf-8"), "{}")

    def test_outcome_attribution_is_present_in_json_compact_standard_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            evidence = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "acceptance_passed",
                "--task-id",
                "S1",
                "--summary",
                "A1 passed in the target renderer.",
                "--payload-json",
                '{"acceptance_ids":["A1"]}',
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)

            report = render_json(mission_dir)
            self.assertEqual(report["schema_version"], "tplan.execution_cost_tree.v0.9")
            self.assertEqual(report["mission"]["outcome_attribution"]["yield_class"], "countable_progress")
            by_id = {node["id"]: node for node in report["nodes"]}
            self.assertEqual(by_id["S1"]["outcome_attribution"]["yield_class"], "countable_progress")

            compact = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "compact",
                "--format",
                "text",
            )
            standard = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "standard")
            audit = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "audit")
            self.assertEqual(compact.returncode, 0, compact.stderr)
            self.assertEqual(standard.returncode, 0, standard.stderr)
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("推进", compact.stdout)
            self.assertIn("产出归因", standard.stdout)
            self.assertIn("产出归因审计", audit.stdout)

    def test_audit_includes_mission_level_unclassified_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            evidence = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "key_finding",
                "--summary",
                "Mission-level fact is not progress.",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            event_id = read_jsonl(mission_dir / "evidence.jsonl")[-1]["id"]
            with (mission_dir / "evidence.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "id": "ELEGACY",
                            "timestamp": "2026-07-22T12:00:00Z",
                            "event_type": "acceptance",
                            "summary": "Historical incomplete acceptance.",
                            "task_id": None,
                            "payload": {},
                        }
                    )
                    + "\n"
                )

            audit = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "audit")
            audit_svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "audit",
                "--format",
                "svg",
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertEqual(audit_svg.returncode, 0, audit_svg.stderr)
            self.assertIn(f"Mission (`execution-tree`)", audit.stdout)
            self.assertIn(event_id, audit.stdout)
            self.assertIn(event_id, audit_svg.stdout)
            self.assertIn("legacy_or_invalid_evidence", audit_svg.stdout)

    def test_standard_shows_completion_without_progress_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            transition = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S1",
                "--status",
                "completed",
            )
            self.assertEqual(transition.returncode, 0, transition.stderr)

            standard = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "standard")
            self.assertEqual(standard.returncode, 0, standard.stderr)
            self.assertIn("completion_without_progress_evidence", standard.stdout)

    def test_counted_tokens_do_not_readd_cached_or_reasoning_subsets(self):
        self.assertEqual(
            _counted_tokens(
                {
                    "input_tokens": 100,
                    "cached_input_tokens": 80,
                    "output_tokens": 20,
                    "reasoning_output_tokens": 15,
                }
            ),
            120,
        )

    def test_usage_counts_models_and_independent_turns_but_not_model_envelopes(self):
        def record(kind, span_id, parent_span_id, input_tokens, output_tokens):
            return {
                "event_id": f"event-{span_id}",
                "span": {
                    "kind": kind,
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "duration_ms": 1,
                    "started_at": "2026-01-01T00:00:00Z",
                    "finished_at": "2026-01-01T00:00:00.001000Z",
                    "measurement_source": "platform_reported",
                    "status": "ok",
                },
                "usage_source": "platform_reported",
                "usage": {
                    "input_tokens": input_tokens,
                    "cached_input_tokens": input_tokens // 2,
                    "output_tokens": output_tokens,
                    "reasoning_output_tokens": output_tokens // 2,
                },
            }

        cost = _span_cost(
            [
                record("agent_turn", "envelope", None, 100, 20),
                record("model", "model", "envelope", 100, 20),
                record("agent_turn", "independent", None, 40, 10),
            ]
        )

        self.assertEqual(cost["usage"]["input_tokens"], 140)
        self.assertEqual(cost["usage"]["output_tokens"], 30)
        self.assertEqual(cost["usage_record_count"], 2)
        self.assertEqual(cost["excluded_usage_envelope_count"], 1)

    def test_global_usage_ownership_survives_cross_attribution_projection(self):
        def record(kind, span_id, parent_span_id, tokens):
            return {
                "event_id": f"event-{span_id}",
                "span": {
                    "kind": kind,
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "duration_ms": 1,
                    "started_at": "2026-01-01T00:00:00Z",
                    "finished_at": "2026-01-01T00:00:00.001000Z",
                    "measurement_source": "platform_reported",
                    "status": "ok",
                },
                "usage": tokens,
            }

        exact_turn = record("agent_turn", "turn", None, {"input_tokens": 100, "output_tokens": 20})
        shared_model = record("model", "model", "turn", {"input_tokens": 100, "output_tokens": 20})
        owners = _usage_owner_event_ids([exact_turn, shared_model])

        self.assertEqual(_span_cost([exact_turn], usage_owner_event_ids=owners)["usage"], {})
        self.assertEqual(
            _span_cost([shared_model], usage_owner_event_ids=owners)["usage"]["input_tokens"],
            100,
        )
        self.assertEqual(
            _span_cost([exact_turn, shared_model], usage_owner_event_ids=owners)["usage"]["input_tokens"],
            100,
        )

    def test_nested_agent_turns_count_only_the_leaf_and_partial_usage_stays_partial(self):
        parent = {
            "event_id": "event-parent",
            "span": {
                "kind": "agent_turn",
                "span_id": "parent",
                "parent_span_id": None,
                "duration_ms": 2,
                "started_at": "2026-01-01T00:00:00Z",
                "finished_at": "2026-01-01T00:00:00.002000Z",
                "measurement_source": "host_measured",
                "status": "ok",
            },
            "usage": {"input_tokens": 50, "output_tokens": 10},
        }
        child = {
            "event_id": "event-child",
            "span": {
                "kind": "agent_turn",
                "span_id": "child",
                "parent_span_id": "parent",
                "duration_ms": 1,
                "started_at": "2026-01-01T00:00:00Z",
                "finished_at": "2026-01-01T00:00:00.001000Z",
                "measurement_source": "host_measured",
                "status": "ok",
            },
            "usage": {"input_tokens": 25},
        }

        cost = _span_cost([parent, child])
        self.assertEqual(cost["usage"], {"input_tokens": 25})
        self.assertEqual(cost["usage_coverage"], "partial")
        self.assertNotIn("output_tokens", cost["usage"])
        self.assertEqual(cost["excluded_usage_envelope_count"], 1)

    def test_standard_duration_hotspots_use_smaller_top_three_or_thirty_percent_quota(self):
        def task(index, elapsed_ms):
            return {
                "id": f"T{index}",
                "kind": "task",
                "visited": True,
                "elapsed_ms": elapsed_ms,
                "execution_order": index,
                "plan_index": index,
            }

        eight_tasks = [task(index, index * 100) for index in range(1, 9)]
        hotspots = _duration_hotspots(eight_tasks, view="standard")
        self.assertEqual(hotspots["eligible_task_count"], 8)
        self.assertEqual(hotspots["selected_count"], 2)
        self.assertEqual(
            [item["task_id"] for item in hotspots["tasks"]],
            ["T8", "T7"],
        )

        twenty_tasks = [task(index, index * 100) for index in range(1, 21)]
        capped = _duration_hotspots(twenty_tasks, view="standard")
        self.assertEqual(capped["selected_count"], 3)
        self.assertEqual(
            [item["task_id"] for item in capped["tasks"]],
            ["T20", "T19", "T18"],
        )

        audit = _duration_hotspots(twenty_tasks, view="audit")
        self.assertFalse(audit["enabled"])
        self.assertEqual(audit["tasks"], [])

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
            self.assertIn("层级：[T] Task · [ST] SubTask · [P] Step", compact_text.stdout)
            self.assertIn("└─ [T] Ship execution tree", compact_text.stdout)
            self.assertIn("   └─ [ST] Capture high-cost execution", compact_text.stdout)
            self.assertIn("LLM 2.0s / 脚本 500ms · Tok 1.0k/300", compact_text.stdout)
            self.assertIn("来源：LLM 平台上报 · 脚本 宿主实测", compact_text.stdout)
            self.assertNotIn("（平台上报）", compact_text.stdout)
            self.assertNotIn("（宿主实测）", compact_text.stdout)
            self.assertNotIn("High-cost path measured", compact_text.stdout)

    def test_elapsed_reconciliation_conserves_time_and_agent_turn_is_only_an_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script("transition_task.py", str(mission_dir), "--task-id", "S1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)
            base = parse_time(read_jsonl(mission_dir / "execution_trace.jsonl")[-1]["timestamp"]) + timedelta(
                microseconds=1
            )

            spans = [
                ("model", "model-1", "turn-1", 0, 5, "platform_reported"),
                ("script", "script-1", None, 1, 4, "host_measured"),
                ("agent_turn", "turn-1", None, 0, 6, "host_measured"),
            ]
            for kind, span_id, parent_span_id, start_ms, finish_ms, source in spans:
                raw = {
                    "task_id": "S1",
                    "span": {
                        "kind": kind,
                        "span_id": span_id,
                        "label": f"{kind} coverage",
                        "status": "ok",
                        "measurement_source": source,
                        "attribution": "exact",
                        "started_at": iso(base + timedelta(milliseconds=start_ms)),
                        "finished_at": iso(base + timedelta(milliseconds=finish_ms)),
                        "duration_ms": finish_ms - start_ms,
                        "attempt": 1,
                        "parent_span_id": parent_span_id,
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
            self.assertEqual(compact["top_cost"], 3)
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
            self.assertIn("层级：[T] Task · [ST] SubTask · [P] Step", compact_text.stdout)
            self.assertIn("└─ [T] Ship execution tree", compact_text.stdout)
            self.assertIn("LLM — / 脚本 —", compact_text.stdout)
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
            self.assertEqual(report["schema_version"], "tplan.execution_cost_tree.v0.9")
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

    def test_completion_handoff_writes_default_artifacts_and_prints_final_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            result = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--completion-handoff",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = mission_dir / "reports" / "execution-cost-tree.md"
            graph = mission_dir / "reports" / "execution-cost-tree.svg"
            self.assertTrue(report.is_file())
            self.assertTrue(graph.is_file())
            self.assertIn("TPlan terminal handoff links", result.stdout)
            self.assertIn(f"[TPlan 执行报告](<{report.resolve()}>)", result.stdout)
            self.assertIn(f"[TPlan 执行过程图](<{graph.resolve()}>)", result.stdout)
            self.assertIn(
                "![TPlan 纵向实际执行时间轴](<execution-cost-tree.svg>)",
                report.read_text(encoding="utf-8"),
            )

            invalid = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--completion-handoff",
                "--view",
                "audit",
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("TPlan terminal handoff rendering failed", invalid.stderr)
            self.assertIn("requires the default Standard Markdown", invalid.stderr)

    def test_parent_edges_paint_after_child_edges_at_junctions(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            added = run_script(
                "add_node.py",
                str(mission_dir),
                "--id",
                "P1",
                "--kind",
                "step",
                "--parent-id",
                "S1",
                "--title",
                "Inspect connector junctions",
                "--parent-contribution",
                "Verifies parent branches visually own shared junctions.",
                "--mission-trace",
                "via S1 -> T1 -> A1",
                "--step-action",
                "Render the connector hierarchy.",
                "--done-condition",
                "Parent connectors paint above child connectors.",
            )
            self.assertEqual(added.returncode, 0, added.stderr)

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
            edges = [
                element
                for element in root.iter()
                if element.attrib.get("class") == "tree-edge"
            ]
            kinds = [element.attrib["data-child-kind"] for element in edges]
            paint_order = {"step": 0, "subtask": 1, "task": 2}
            self.assertEqual(kinds, sorted(kinds, key=paint_order.__getitem__))
            self.assertEqual(
                {element.attrib["data-child-kind"]: element.attrib["stroke-width"] for element in edges},
                {"step": "2.0", "subtask": "4.0", "task": "6.0"},
            )
            self.assertEqual(
                {element.attrib["data-child-kind"]: element.attrib["opacity"] for element in edges},
                {"step": "0.84", "subtask": "0.72", "task": "1.0"},
            )
            junction_caps = [
                element
                for element in root.iter()
                if element.attrib.get("class") == "tree-edge junction-cap"
            ]
            self.assertEqual(
                {element.attrib["data-parent-kind"] for element in junction_caps},
                {"task", "subtask"},
            )
            self.assertTrue(all(element.attrib["opacity"] == "1" for element in junction_caps))
            self.assertEqual(
                {element.attrib["data-parent-kind"]: element.attrib["stroke"] for element in junction_caps},
                {"task": "#64748b", "subtask": "#aa88f8"},
            )

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
            self.assertIn("层级：[T] Task · [ST] SubTask · [P] Step", markdown)
            self.assertIn("└─ [T] Ship execution tree", markdown)
            self.assertIn("显示 1/3；省略 2", markdown)
            self.assertIn("来源：本次未采集资源时长", markdown)
            self.assertNotIn("<svg", markdown)

    def test_compact_labels_task_subtask_and_step_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            added = run_script(
                "add_node.py",
                str(mission_dir),
                "--id",
                "P1",
                "--kind",
                "step",
                "--parent-id",
                "S1",
                "--title",
                "Inspect the rendered level labels",
                "--parent-contribution",
                "Makes each runtime node kind visible in Compact.",
                "--mission-trace",
                "via S1 -> T1 -> A1",
                "--step-action",
                "Render and inspect the Compact text tree.",
                "--done-condition",
                "The Step line carries the Step marker.",
            )
            self.assertEqual(added.returncode, 0, added.stderr)
            blocked = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "P1",
                "--status",
                "blocked",
            )
            self.assertEqual(blocked.returncode, 0, blocked.stderr)

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
            self.assertIn("层级：[T] Task · [ST] SubTask · [P] Step", text.stdout)
            self.assertIn("└─ [T] Ship execution tree", text.stdout)
            self.assertIn("└─ [ST] Capture high-cost execution", text.stdout)
            self.assertIn("└─ [P] Inspect the rendered level labels", text.stdout)

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
                "--outcome-summary",
                "Recovered on retry",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            blocked = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S2",
                "--status",
                "blocked",
                "--outcome-summary",
                "Waiting for an external decision",
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
            self.assertIn("[ST] Capture high-cost execution ✅", text.stdout)
            self.assertIn("↻2", text.stdout)
            self.assertIn("→ Recovered on retry", text.stdout)
            self.assertIn("[ST] Optional untouched path ⛔ 受阻", text.stdout)
            self.assertIn("→ Waiting for an external decision", text.stdout)

    def test_completed_snapshot_with_incomplete_trace_renders_full_tree_as_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "active",
            )
            self.assertEqual(active.returncode, 0, active.stderr)

            mission_path = mission_dir / "mission.json"
            mission = json.loads(mission_path.read_text(encoding="utf-8"))
            mission["mission"]["status"] = "completed"
            mission["active_task_id"] = None
            for task in mission["tasks"]:
                task["status"] = "completed"
            mission_path.write_text(
                json.dumps(mission, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            for view in ("standard", "audit"):
                report = render_json(mission_dir, "--view", view)
                self.assertEqual(report["trace"]["coverage"], "partial")
                self.assertFalse(report["trace"]["snapshot_consistent"])
                self.assertIsNone(report["mission"]["elapsed_ms"])
                self.assertIsNone(report["mission"]["finished_at"])
                self.assertIsNotNone(report["mission"]["observed_elapsed_ms"])
                self.assertIsNotNone(report["mission"]["observed_finished_at"])
                self.assertEqual(report["visible_node_ids"], ["T1", "S1", "S2"])
                self.assertEqual(
                    report["tree_edges"],
                    [
                        {"from": "mission", "to": "T1"},
                        {"from": "T1", "to": "S1"},
                        {"from": "T1", "to": "S2"},
                    ],
                )
                self.assertTrue(
                    all(node["elapsed_coverage"] == "partial" for node in report["nodes"])
                )
                diagnostic_codes = {
                    item["code"] for item in report["trace"]["coverage_diagnostics"]
                }
                self.assertIn("trace_task_status_mismatch", diagnostic_codes)
                self.assertIn("trace_active_task_mismatch", diagnostic_codes)
                self.assertIn("trace_mission_status_mismatch", diagnostic_codes)
                self.assertIn("trace_missing_terminal_event", diagnostic_codes)
                self.assertEqual(
                    report["timeline"]["range_bar_scale"],
                    "linear_observed_window",
                )
                self.assertEqual(report["timeline"]["window_kind"], "observed_trace")
                self.assertNotIn("started_at", report["timeline"])
                self.assertNotIn("finished_at", report["timeline"])
                self.assertNotIn("elapsed_ms", report["timeline"])

            handoff = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--completion-handoff",
            )
            self.assertEqual(handoff.returncode, 0, handoff.stderr)
            markdown = (
                mission_dir / "reports" / "execution-cost-tree.md"
            ).read_text(encoding="utf-8")
            svg = (
                mission_dir / "reports" / "execution-cost-tree.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("覆盖告警", markdown)
            self.assertIn("trace_missing_terminal_event", markdown)
            self.assertIn("生命周期告警", svg)
            self.assertIn("已观测窗口", svg)
            self.assertIn("观测窗口结束", svg)
            self.assertNotIn("Mission 结束", svg)
            self.assertNotIn("覆盖 exact", svg)
            self.assertNotIn("实际历时 ≥", svg)
            self.assertNotIn("精确时间", svg)

            root = ET.fromstring(svg)
            task_cards = [
                element
                for element in root.iter()
                if element.attrib.get("class") == "task-card"
            ]
            self.assertEqual(
                [element.attrib["data-task-id"] for element in task_cards],
                ["T1", "S1", "S2"],
            )

    def test_complete_terminal_lifecycle_is_exact_without_cost_spans(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            complete_tree_mission(tmp, mission_dir)

            report = render_json(mission_dir, "--view", "audit")
            terminal_record = next(
                record
                for record in reversed(read_jsonl(mission_dir / "execution_trace.jsonl"))
                if record["event_type"] == "mission_status_changed"
            )
            self.assertEqual(report["trace"]["coverage"], "exact")
            self.assertTrue(report["trace"]["snapshot_consistent"])
            self.assertEqual(report["trace"]["coverage_diagnostics"], [])
            self.assertEqual(
                report["mission"]["finished_at"],
                terminal_record["timestamp"],
            )
            self.assertIsNotNone(report["mission"]["elapsed_ms"])
            self.assertEqual(report["mission"]["cost"]["span_count"], 0)
            self.assertEqual(
                report["mission"]["cost"]["usage_coverage"],
                "not_reported",
            )
            self.assertEqual(
                report["mission"]["elapsed_reconciliation"]["not_exactly_recorded_elapsed_ms"],
                report["mission"]["elapsed_ms"],
            )
            self.assertEqual(report["timeline"]["window_kind"], "mission_lifecycle")
            self.assertEqual(
                report["timeline"]["window_elapsed_ms"],
                report["mission"]["elapsed_ms"],
            )

            standard = render_json(mission_dir, "--view", "standard")
            self.assertEqual(standard["presentation_density"]["mode"], "sparse")
            self.assertEqual(
                standard["presentation_density"]["telemetry_coverage"],
                "not_reported",
            )
            self.assertEqual(
                standard["presentation_density"]["omitted_standard_channels"],
                ["LLM调用", "脚本时长", "工具时长", "等待时长", "Token"],
            )
            standard_svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--format",
                "svg",
            )
            self.assertEqual(standard_svg.returncode, 0, standard_svg.stderr)
            self.assertIn("遥测覆盖：未采集成本通道", standard_svg.stdout)
            for task_id in ("T1", "S1", "S2"):
                card_text = svg_card_text(standard_svg.stdout, task_id)
                self.assertNotIn("LLM调用累计", card_text)
                self.assertNotIn("脚本累计", card_text)
                self.assertNotIn("工具累计", card_text)
                self.assertNotIn("等待累计", card_text)
                self.assertNotIn("Token ", card_text)

            audit = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "audit",
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn(
                "LLM调用累计 未采集 · 脚本累计 未采集",
                audit.stdout,
            )
            self.assertIn("Token 未采集", audit.stdout)

    def test_missing_active_path_events_downgrade_lifecycle_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            for task_id in ("S1", "S2", "T1"):
                active = run_script(
                    "transition_task.py",
                    str(mission_dir),
                    "--task-id",
                    task_id,
                    "--status",
                    "active",
                )
                self.assertEqual(active.returncode, 0, active.stderr)
                completed = run_script(
                    "transition_task.py",
                    str(mission_dir),
                    "--task-id",
                    task_id,
                    "--status",
                    "completed",
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
            complete_tree_mission(tmp, mission_dir)

            trace_path = mission_dir / "execution_trace.jsonl"
            records = [
                record
                for record in read_jsonl(trace_path)
                if record["event_type"] != "active_node_changed"
            ]
            trace_path.write_text(
                "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
                encoding="utf-8",
            )

            report = render_json(mission_dir, "--view", "audit")
            self.assertEqual(report["trace"]["coverage"], "partial")
            self.assertFalse(report["trace"]["snapshot_consistent"])
            self.assertIsNone(report["mission"]["elapsed_ms"])
            diagnostic_codes = {
                item["code"] for item in report["trace"]["coverage_diagnostics"]
            }
            self.assertIn("trace_active_commit_incomplete", diagnostic_codes)

    def test_missing_active_clear_event_downgrades_even_when_snapshot_keeps_stale_cursor(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "active",
            )
            self.assertEqual(active.returncode, 0, active.stderr)
            completed = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "completed",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            for task_id in ("S1", "S2"):
                result = run_script(
                    "transition_task.py",
                    str(mission_dir),
                    "--task-id",
                    task_id,
                    "--status",
                    "completed",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            complete_mission_status(tmp, mission_dir)

            trace_path = mission_dir / "execution_trace.jsonl"
            records = read_jsonl(trace_path)
            completion = next(
                record
                for record in records
                if record["event_type"] == "task_status_changed"
                and record.get("task_id") == "T1"
                and record["payload"].get("to_status") == "completed"
            )
            records = [
                record
                for record in records
                if not (
                    record["event_type"] == "active_node_changed"
                    and record.get("commit_id") == completion.get("commit_id")
                )
            ]
            trace_path.write_text(
                "".join(
                    json.dumps(record, ensure_ascii=False) + "\n"
                    for record in records
                ),
                encoding="utf-8",
            )
            mission_path = mission_dir / "mission.json"
            mission = json.loads(mission_path.read_text(encoding="utf-8"))
            mission["active_task_id"] = "T1"
            mission_path.write_text(
                json.dumps(mission, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            report = render_json(mission_dir, "--view", "audit")
            diagnostic_codes = {
                item["code"] for item in report["trace"]["coverage_diagnostics"]
            }
            self.assertEqual(report["trace"]["coverage"], "partial")
            self.assertIsNone(report["mission"]["elapsed_ms"])
            self.assertIn("trace_active_commit_incomplete", diagnostic_codes)
            self.assertIn("snapshot_active_task_not_active", diagnostic_codes)

    def test_atomic_parent_child_activation_with_one_cursor_event_remains_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            decision = Path(tmp) / "activate-parent-child.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "continue",
                        "rationale": "The parent and selected child form one active path.",
                        "confidence": 95,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_active_task", "task_id": "T1"},
                            {"type": "set_active_task", "task_id": "S1"},
                        ],
                        "requires_human": False,
                        "mission_alignment": "The cursor ends on the selected child.",
                        "path_assessment": {
                            "marginal_roi": "positive",
                            "path_role": "dominant_path",
                            "evidence_delta": "new_evidence_expected",
                        },
                        "continuation_authorization": {
                            "trigger_reasons": ["repeated_same_path_attempt"],
                            "evidence_shape_lint": "pass",
                            "defect_classification": "acceptance_blocking",
                            "expected_evidence_delta": "new_evidence_expected",
                            "authorized_action": "continue_same_path",
                        },
                    }
                ),
                encoding="utf-8",
            )
            activated = run_script(
                "apply_decision.py",
                str(mission_dir),
                "--decision",
                str(decision),
            )
            self.assertEqual(activated.returncode, 0, activated.stderr)
            activation_records = read_jsonl(
                mission_dir / "execution_trace.jsonl"
            )[1:]
            activation_commit = activation_records[0]["commit_id"]
            same_commit = [
                record
                for record in activation_records
                if record.get("commit_id") == activation_commit
            ]
            self.assertEqual(
                len(
                    [
                        record
                        for record in same_commit
                        if record["event_type"] == "task_status_changed"
                        and record["payload"].get("to_status") == "active"
                    ]
                ),
                2,
            )
            self.assertEqual(
                len(
                    [
                        record
                        for record in same_commit
                        if record["event_type"] == "active_node_changed"
                    ]
                ),
                1,
            )

            complete_tree_mission(tmp, mission_dir)
            report = render_json(mission_dir, "--view", "audit")
            self.assertEqual(report["trace"]["coverage"], "exact")
            self.assertEqual(report["trace"]["coverage_diagnostics"], [])
            self.assertIsNotNone(report["mission"]["elapsed_ms"])

    def test_requires_human_stop_keeps_blocked_recovery_cursor_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "active",
            )
            self.assertEqual(active.returncode, 0, active.stderr)
            stopped = run_script(
                "stop_report.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "Need operator input",
                "--current-goal",
                "Render the execution tree",
                "--attempt",
                "Validated the runtime path",
                "--blocking-issue",
                "Operator decision is required",
                "--why-cannot-continue-safely",
                "Continuing would guess the required policy",
                "--need-from-human",
                "Choose the policy",
                "--resume-condition",
                "Resume after the policy is supplied",
            )
            self.assertEqual(stopped.returncode, 0, stopped.stderr)

            report = render_json(mission_dir, "--view", "audit")
            self.assertEqual(report["mission"]["status"], "requires_human")
            self.assertEqual(report["mission"]["active_task_id"], "T1")
            self.assertEqual(
                next(node for node in report["nodes"] if node["id"] == "T1")[
                    "status"
                ],
                "blocked",
            )
            self.assertEqual(report["trace"]["coverage"], "exact")
            self.assertEqual(report["trace"]["coverage_diagnostics"], [])
            self.assertIsNotNone(report["mission"]["elapsed_ms"])
            self.assertIsNotNone(report["mission"]["finished_at"])

    def test_requires_human_decision_cannot_masquerade_as_stop_recovery_cursor(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "active",
            )
            self.assertEqual(active.returncode, 0, active.stderr)
            decision = Path(tmp) / "escalate.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "escalate",
                        "rationale": "Escalate without granting a recovery cursor.",
                        "confidence": 90,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {
                                "type": "transition_task",
                                "task_id": "T1",
                                "status": "blocked",
                            },
                            {
                                "type": "set_mission_status",
                                "status": "requires_human",
                            },
                        ],
                        "requires_human": False,
                        "mission_alignment": "The escalation preserves the Mission boundary.",
                        "path_assessment": {
                            "marginal_roi": "positive",
                            "path_role": "dominant_path",
                            "evidence_delta": "new_evidence_expected",
                        },
                    }
                ),
                encoding="utf-8",
            )
            escalated = run_script(
                "apply_decision.py",
                str(mission_dir),
                "--decision",
                str(decision),
            )
            self.assertEqual(escalated.returncode, 0, escalated.stderr)

            trace_path = mission_dir / "execution_trace.jsonl"
            records = read_jsonl(trace_path)
            blocked = next(
                record
                for record in records
                if record["event_type"] == "task_status_changed"
                and record.get("task_id") == "T1"
                and record["payload"].get("to_status") == "blocked"
            )
            records = [
                record
                for record in records
                if not (
                    record["event_type"] == "active_node_changed"
                    and record.get("commit_id") == blocked.get("commit_id")
                )
            ]
            trace_path.write_text(
                "".join(
                    json.dumps(record, ensure_ascii=False) + "\n"
                    for record in records
                ),
                encoding="utf-8",
            )
            mission_path = mission_dir / "mission.json"
            mission = json.loads(mission_path.read_text(encoding="utf-8"))
            mission["active_task_id"] = "T1"
            mission_path.write_text(
                json.dumps(mission, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            report = render_json(mission_dir, "--view", "audit")
            diagnostic_codes = {
                item["code"] for item in report["trace"]["coverage_diagnostics"]
            }
            self.assertEqual(report["trace"]["coverage"], "partial")
            self.assertIn("trace_active_commit_incomplete", diagnostic_codes)
            self.assertIn("snapshot_active_task_not_active", diagnostic_codes)
            self.assertIsNone(report["mission"]["elapsed_ms"])

    def test_interaction_guard_stop_is_one_monotonic_exact_lifecycle_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            active = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--status",
                "active",
            )
            self.assertEqual(active.returncode, 0, active.stderr)
            guard = begin_interaction_guard(
                mission_dir,
                platform="test-host",
                message_ref="M1",
            )
            stop_interaction_guard(
                mission_dir,
                guard_id=guard["guard_id"],
                expected_revision=guard["revision"],
                message_refs=["M1"],
                task_id="T1",
                summary="Stop at the recovery cursor.",
                payload={
                    "current_goal": "Render the execution tree",
                    "attempts": ["Opened the interaction guard"],
                    "blocking_issue": "Operator decision is required",
                    "why_cannot_continue_safely": "Continuing would guess policy",
                    "need_from_human": "Choose the policy",
                    "resume_condition": "Resume after policy is supplied",
                },
            )

            records = read_jsonl(mission_dir / "execution_trace.jsonl")
            stopped = [
                record
                for record in records
                if record.get("source")
                == {"kind": "interaction_guard", "name": "stop"}
            ]
            self.assertEqual(
                {record["timestamp"] for record in stopped},
                {stopped[0]["timestamp"]},
            )
            self.assertEqual(
                {record["commit_id"] for record in stopped},
                {stopped[0]["commit_id"]},
            )
            self.assertEqual(
                {
                    record["event_type"]
                    for record in stopped
                },
                {
                    "task_status_changed",
                    "mission_status_changed",
                    "interaction_guard_state",
                },
            )

            report = render_json(mission_dir, "--view", "audit")
            self.assertEqual(report["trace"]["coverage"], "exact")
            self.assertEqual(report["trace"]["coverage_diagnostics"], [])
            self.assertEqual(report["mission"]["status"], "requires_human")
            self.assertEqual(report["mission"]["active_task_id"], "T1")

    def test_non_monotonic_lifecycle_timestamps_downgrade_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            complete_tree_mission(tmp, mission_dir)
            trace_path = mission_dir / "execution_trace.jsonl"
            records = read_jsonl(trace_path)
            initialized_at = parse_time(records[0]["timestamp"])
            task_change = next(
                record
                for record in records
                if record["event_type"] == "task_status_changed"
            )
            terminal = next(
                record
                for record in records
                if record["event_type"] == "mission_status_changed"
            )
            task_change["timestamp"] = iso(initialized_at + timedelta(seconds=2))
            terminal["timestamp"] = iso(initialized_at + timedelta(seconds=1))
            trace_path.write_text(
                "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
                encoding="utf-8",
            )

            report = render_json(mission_dir, "--view", "audit")
            self.assertEqual(report["trace"]["coverage"], "partial")
            self.assertIsNone(report["mission"]["elapsed_ms"])
            diagnostic_codes = {
                item["code"] for item in report["trace"]["coverage_diagnostics"]
            }
            self.assertIn("trace_lifecycle_timestamp_non_monotonic", diagnostic_codes)

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
            snapshot_standard = render_json(mission_dir, "--view", "standard")
            self.assertEqual(
                snapshot_standard["timeline"]["window_kind"],
                "snapshot_only",
            )
            self.assertEqual(
                snapshot_standard["timeline"]["range_bar_scale"],
                "not_available",
            )
            self.assertEqual(
                snapshot_standard["timeline"]["row_positioning"],
                "declared_tree_order",
            )
            snapshot_svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--format",
                "svg",
            )
            self.assertEqual(snapshot_svg.returncode, 0, snapshot_svg.stderr)
            self.assertIn("TPlan Mission 结构快照", snapshot_svg.stdout)
            self.assertIn("没有执行时间观测", snapshot_svg.stdout)
            self.assertNotIn("TPlan 纵向实际执行时间轴", snapshot_svg.stdout)
            for task_id in ("T1", "S1", "S2"):
                self.assertNotIn(
                    "实际历时",
                    svg_card_text(snapshot_svg.stdout, task_id),
                )

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
            self.assertEqual(partial["timeline"]["window_kind"], "observed_trace")
            partial_standard = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "standard",
                "--format",
                "svg",
            )
            self.assertEqual(
                partial_standard.returncode,
                0,
                partial_standard.stderr,
            )
            self.assertIn("TPlan 已观测执行窗口", partial_standard.stdout)
            self.assertIn("已观测相对时间", partial_standard.stdout)
            self.assertIn("观测窗口结束", partial_standard.stdout)
            self.assertNotIn(
                "TPlan 纵向实际执行时间轴",
                partial_standard.stdout,
            )
            partial_markdown = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "standard",
            )
            self.assertEqual(
                partial_markdown.returncode,
                0,
                partial_markdown.stderr,
            )
            self.assertTrue(
                partial_markdown.stdout.startswith(
                    "# TPlan 已观测执行窗口与成本树"
                )
            )
            self.assertNotIn(
                "# TPlan 实际执行与成本树",
                partial_markdown.stdout,
            )
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

    def test_standard_sparse_script_coverage_uses_one_mission_note_and_no_empty_node_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            started = parse_time(
                read_jsonl(mission_dir / "execution_trace.jsonl")[0]["timestamp"]
            )
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "script",
                        "label": "focused renderer tests",
                        "status": "ok",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                        "started_at": iso(started),
                        "finished_at": iso(started + timedelta(milliseconds=20)),
                        "duration_ms": 20,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                },
                "sparse-script",
            )

            report = render_json(mission_dir, "--view", "standard")
            profile = report["presentation_density"]
            self.assertEqual(profile["mode"], "sparse")
            self.assertEqual(profile["observed_channels"], ["脚本时长"])
            self.assertEqual(
                profile["standard_note"],
                "遥测覆盖：部分，仅采集脚本时长；未采集：LLM调用、工具时长、等待时长、Token；未显示字段不代表 0。",
            )
            standard_svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--format",
                "svg",
            )
            self.assertEqual(standard_svg.returncode, 0, standard_svg.stderr)
            self.assertEqual(standard_svg.stdout.count("遥测覆盖："), 1)
            for absent_zero in (
                "LLM调用累计 0",
                "工具累计 0",
                "等待累计 0",
                "Token 入 0 / 出 0",
            ):
                self.assertNotIn(absent_zero, standard_svg.stdout)
            s1_text = svg_card_text(standard_svg.stdout, "S1")
            self.assertIn("脚本累计 20ms（宿主实测）", s1_text)
            self.assertNotIn("LLM调用累计", s1_text)
            self.assertNotIn("工具累计", s1_text)
            self.assertNotIn("等待累计", s1_text)
            self.assertNotIn("Token ", s1_text)
            self.assertNotIn("脚本累计", svg_card_text(standard_svg.stdout, "S2"))

            standard_markdown = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
            )
            self.assertEqual(
                standard_markdown.returncode,
                0,
                standard_markdown.stderr,
            )
            self.assertEqual(
                standard_markdown.stdout.count("遥测覆盖："),
                1,
            )
            self.assertNotIn("## Codex 遥测覆盖", standard_markdown.stdout)
            audit = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "audit",
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("## Codex 遥测覆盖", audit.stdout)
            self.assertIn(
                "optional Codex telemetry adapter is not configured for this Mission",
                audit.stdout,
            )

    def test_standard_mixed_telemetry_keeps_observed_fields_and_consolidates_absent_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            started = parse_time(
                read_jsonl(mission_dir / "execution_trace.jsonl")[0]["timestamp"]
            )
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "script",
                        "label": "focused renderer tests",
                        "status": "ok",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                        "started_at": iso(started),
                        "finished_at": iso(started + timedelta(milliseconds=20)),
                        "duration_ms": 20,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                },
                "mixed-script",
            )
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "model",
                        "label": "renderer classification",
                        "status": "ok",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                        "started_at": iso(started),
                        "finished_at": iso(started + timedelta(milliseconds=15)),
                        "duration_ms": 15,
                        "attempt": 1,
                        "parent_span_id": None,
                    },
                    "usage": {"input_tokens": 120, "output_tokens": 30},
                    "usage_source": "platform_reported",
                },
                "mixed-model",
            )

            report = render_json(mission_dir, "--view", "standard")
            profile = report["presentation_density"]
            self.assertEqual(profile["mode"], "mixed")
            self.assertEqual(
                profile["observed_channels"],
                ["LLM调用", "脚本时长", "Token"],
            )
            self.assertEqual(
                profile["omitted_standard_channels"],
                ["工具时长", "等待时长"],
            )
            standard_svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--format",
                "svg",
            )
            self.assertEqual(standard_svg.returncode, 0, standard_svg.stderr)
            s1_text = svg_card_text(standard_svg.stdout, "S1")
            self.assertIn("LLM调用累计 15ms（调用端实测）", s1_text)
            self.assertIn("脚本累计 20ms（宿主实测）", s1_text)
            self.assertIn("Token 入 120 / 出 30", s1_text)
            self.assertNotIn("工具累计", s1_text)
            self.assertNotIn("等待累计", s1_text)
            self.assertIn("未采集：工具时长、等待时长", standard_svg.stdout)

    def test_standard_sparse_mode_preserves_abnormal_signals_and_declared_hierarchy(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_tree_mission(tmp)
            activated = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S1",
                "--status",
                "active",
            )
            self.assertEqual(activated.returncode, 0, activated.stderr)
            blocked = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "S1",
                "--status",
                "blocked",
            )
            self.assertEqual(blocked.returncode, 0, blocked.stderr)
            started = parse_time(
                read_jsonl(mission_dir / "execution_trace.jsonl")[0]["timestamp"]
            )
            record_span(
                tmp,
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "script",
                        "label": "failed renderer test",
                        "status": "error",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                        "started_at": iso(started),
                        "finished_at": iso(started + timedelta(milliseconds=5)),
                        "duration_ms": 5,
                        "attempt": 2,
                        "parent_span_id": None,
                    },
                },
                "abnormal-script",
            )
            start_execution_span(
                mission_dir,
                {
                    "task_id": "S1",
                    "span": {
                        "kind": "model",
                        "label": "interrupted renderer call",
                        "measurement_source": "host_measured",
                        "attribution": "exact",
                        "attempt": 3,
                        "parent_span_id": None,
                    },
                },
            )

            report = render_json(mission_dir, "--view", "standard")
            self.assertEqual(report["trace"]["structure_fidelity"], "one_to_one")
            self.assertEqual(report["visible_node_ids"], ["T1", "S1", "S2"])
            self.assertEqual(
                report["tree_edges"],
                [
                    {"from": "mission", "to": "T1"},
                    {"from": "T1", "to": "S1"},
                    {"from": "T1", "to": "S2"},
                ],
            )
            standard_svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--format",
                "svg",
            )
            self.assertEqual(standard_svg.returncode, 0, standard_svg.stderr)
            s1_text = svg_card_text(standard_svg.stdout, "S1")
            self.assertIn("受阻", s1_text)
            self.assertIn("执行次数 3", s1_text)
            self.assertIn("错误 1", s1_text)
            self.assertIn("未结束调用 1", s1_text)
            root = ET.fromstring(standard_svg.stdout)
            rendered_edges = {
                (element.attrib["data-tree-from"], element.attrib["data-tree-to"])
                for element in root.iter()
                if "data-tree-from" in element.attrib
            }
            self.assertEqual(
                rendered_edges,
                {(edge["from"], edge["to"]) for edge in report["tree_edges"]},
            )

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
            self.assertEqual(report["presentation_density"]["mode"], "sparse")
            self.assertEqual(
                report["presentation_density"]["channels"]["model_duration"]["status"],
                "unavailable",
            )
            self.assertEqual(
                report["presentation_density"]["channels"]["script_duration"]["status"],
                "not_reported",
            )
            self.assertIn("S1", report["visible_node_ids"])
            markdown = run_script("render_execution_cost_tree.py", str(mission_dir))
            self.assertEqual(markdown.returncode, 0, markdown.stderr)
            self.assertIn("LLM调用累计 未知 · Token 未知", markdown.stdout)
            self.assertNotIn("脚本累计 未采集", markdown.stdout)
            self.assertIn("Token 未知", markdown.stdout)
            standard_svg = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--format",
                "svg",
            )
            self.assertEqual(standard_svg.returncode, 0, standard_svg.stderr)
            self.assertIn("LLM调用累计 未知", svg_card_text(standard_svg.stdout, "S1"))
            self.assertNotIn("脚本累计", svg_card_text(standard_svg.stdout, "S1"))
            self.assertNotIn("LLM调用累计", svg_card_text(standard_svg.stdout, "S2"))

            audit = run_script(
                "render_execution_cost_tree.py",
                str(mission_dir),
                "--view",
                "audit",
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn(
                "LLM调用累计 未知 · 脚本累计 未采集",
                audit.stdout,
            )

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
            self.assertEqual(report["schema_version"], "tplan.execution_cost_tree.v0.9")
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
