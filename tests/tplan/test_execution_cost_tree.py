import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


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

    def test_wall_time_conserves_elapsed_and_agent_turn_is_only_an_envelope(self):
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
            wall = node["subtree_wall_time"]
            self.assertEqual(wall["attributed_wall_ms"], 5)
            self.assertEqual(wall["excluded_envelope_span_count"], 1)
            self.assertEqual(node["elapsed_ms"], wall["attributed_wall_ms"] + wall["unattributed_elapsed_ms"])
            mission_wall = report["mission"]["wall_time"]
            self.assertEqual(
                report["mission"]["elapsed_ms"],
                mission_wall["attributed_wall_ms"] + mission_wall["unattributed_elapsed_ms"],
            )
            self.assertEqual(node["inclusive_cost"]["by_kind_resource_ms"]["model"], 5)
            self.assertEqual(node["inclusive_cost"]["additive_resource_time_ms"], 8)
            self.assertEqual(node["inclusive_cost"]["usage"]["input_tokens"], 100)
            self.assertEqual(node["inclusive_cost"]["usage"]["output_tokens"], 20)

            standard = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "standard")
            self.assertEqual(standard.returncode, 0, standard.stderr)
            self.assertIn("LLM 5ms · 脚本 3ms", standard.stdout)
            self.assertNotIn("Agent turn 包络", standard.stdout)
            audit = run_script("render_execution_cost_tree.py", str(mission_dir), "--view", "audit")
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("Agent turn 包络：1 个 span，6ms", audit.stdout)

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
            audit = run_script(
                "render_execution_cost_tree.py", str(mission_dir), "--view", "audit"
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            self.assertIn("LLM 未采集 · 脚本 未采集", audit.stdout)

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
            self.assertIn("LLM 未知 · 脚本 未采集", markdown.stdout)
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
            span = records[-1]
            self.assertEqual(span["event_type"], "span_completed")
            self.assertEqual(span["span"]["kind"], "script")
            self.assertEqual(span["metadata"], {"exit_code": 0})
            raw_trace = (mission_dir / "execution_trace.jsonl").read_text(encoding="utf-8")
            self.assertNotIn(sys.executable, raw_trace)
            self.assertNotIn('"command"', raw_trace)
            self.assertNotIn('"stdout"', raw_trace)
            self.assertNotIn('"stderr"', raw_trace)

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
