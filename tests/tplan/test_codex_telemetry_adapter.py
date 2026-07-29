import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from codex_telemetry_adapter import (
    OTEL_EVENT_SCHEMA_VERSION,
    bind_session,
    coverage_path,
    handle_hook,
    ingest_otel_event,
)
from execution_cost_tree import build_execution_cost_tree, render_markdown, render_svg
from tplan_runtime import TplanError, read_execution_trace


def run_script(script_name, *args, input_text=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *args],
        text=True,
        input=input_text,
        capture_output=True,
    )


def create_mission(tmp, *, active=True):
    mission_dir = Path(tmp) / "mission"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Capture Codex telemetry",
                    "role": "success-critical",
                    "mission_contribution": "Captures only exactly bound runtime spans.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2",
                    "title": "Exercise ambiguous binding",
                    "role": "supporting",
                    "mission_contribution": "Proves that attribution is never guessed.",
                    "acceptance_evidence": ["A1"],
                },
            ]
        ),
        encoding="utf-8",
    )
    initialized = run_script(
        "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "codex-telemetry",
        "--title",
        "Codex Telemetry",
        "--objective",
        "Capture honest Codex runtime telemetry.",
        "--acceptance-evidence",
        "A1:Capture is correlated, private, and fail-closed.",
        "--task-json",
        str(tasks),
    )
    if initialized.returncode != 0:
        raise AssertionError(initialized.stderr)
    if active:
        activated = run_script(
            "transition_task.py",
            str(mission_dir),
            "--task-id",
            "T1",
            "--status",
            "active",
        )
        if activated.returncode != 0:
            raise AssertionError(activated.stderr)
    return mission_dir


def at(base, seconds):
    return (base + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def hook(event_name, *, session="session-1", turn="turn-1", **fields):
    return {
        "session_id": session,
        "turn_id": turn,
        "hook_event_name": event_name,
        **fields,
    }


def otel_event(base, event_id, record_type, **overrides):
    value = {
        "schema_version": OTEL_EVENT_SCHEMA_VERSION,
        "event_id": event_id,
        "session_id": "session-1",
        "turn_id": "turn-1",
        "record_type": record_type,
        "started_at": at(base, 10),
        "finished_at": at(base, 12),
        "duration_ms": 2000,
        "status": "ok",
        "source_event": "codex.api_request",
        "usage": {},
    }
    value.update(overrides)
    return value


def corrupt_runtime_fingerprint(mission_dir):
    mission_path = mission_dir / "mission.json"
    mission = json.loads(mission_path.read_text(encoding="utf-8"))
    mission["runtime_provenance"]["fingerprint"]["build_hash"] = "sha256:" + "0" * 64
    mission_path.write_text(
        json.dumps(mission, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def artifact_snapshot(*roots):
    snapshot = {}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.name != ".execution_trace.lock":
                snapshot[str(path)] = path.read_bytes()
    return snapshot


class CodexTelemetryAdapterTests(unittest.TestCase):
    def test_local_tool_pair_is_exact_and_raw_hook_payload_is_not_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)

            started = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    tool_name="Bash",
                    tool_use_id="tool-1",
                    tool_input={"command": "printf super-secret"},
                ),
                observed_at=at(base, 0),
            )
            completed = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PostToolUse",
                    tool_name="Bash",
                    tool_use_id="tool-1",
                    tool_response={"output": "super-secret"},
                ),
                observed_at=at(base, 2),
            )

            self.assertEqual(started["status"], "recorded")
            self.assertEqual(completed["status"], "recorded")
            trace = read_execution_trace(mission_dir)
            span = next(record for record in trace if record["event_type"] == "span_completed")
            self.assertEqual(span["task_id"], "T1")
            self.assertEqual(span["span"]["attribution"], "exact")
            self.assertEqual(span["span"]["kind"], "script")
            self.assertEqual(span["span"]["duration_ms"], 2000)
            persisted = (
                (mission_dir / "execution_trace.jsonl").read_text(encoding="utf-8")
                + next(state_dir.glob("*.json")).read_text(encoding="utf-8")
                + coverage_path(mission_dir).read_text(encoding="utf-8")
            )
            self.assertNotIn("super-secret", persisted)
            state = json.loads(next(state_dir.glob("*.json")).read_text(encoding="utf-8"))
            self.assertNotIn("tool_input", json.dumps(state))
            self.assertNotIn("tool_response", json.dumps(state))
            coverage = json.loads(coverage_path(mission_dir).read_text(encoding="utf-8"))
            self.assertEqual(coverage["channels"]["local_tools"]["status"], "observed")
            self.assertEqual(coverage["channels"]["hosted_tools"]["status"], "not_reported")
            self.assertEqual(coverage["channels"]["model_turns"]["status"], "not_reported")
            self.assertEqual(coverage["channels"]["tokens"]["status"], "not_reported")

    def test_post_tool_status_uses_sanitized_exit_code_and_otherwise_stays_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)

            handle_hook(
                mission_dir,
                state_dir,
                hook("PreToolUse", tool_name="Bash", tool_use_id="tool-failed"),
                observed_at=at(base, 0),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PostToolUse",
                    tool_name="Bash",
                    tool_use_id="tool-failed",
                    tool_response={"exit_code": 17, "output": "must not persist"},
                ),
                observed_at=at(base, 1),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook("PreToolUse", tool_name="apply_patch", tool_use_id="tool-unknown"),
                observed_at=at(base, 2),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook("PostToolUse", tool_name="apply_patch", tool_use_id="tool-unknown"),
                observed_at=at(base, 3),
            )

            completed = [
                record
                for record in read_execution_trace(mission_dir)
                if record["event_type"] == "span_completed"
            ]
            self.assertEqual(completed[0]["span"]["status"], "error")
            self.assertEqual(completed[0]["metadata"]["exit_code"], 17)
            self.assertEqual(completed[1]["span"]["status"], "unknown")
            self.assertNotIn(
                "must not persist",
                (mission_dir / "execution_trace.jsonl").read_text(encoding="utf-8"),
            )

    def test_hook_pair_requires_same_turn_and_tool_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)

            handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    turn="turn-A",
                    tool_name="Bash",
                    tool_use_id="tool-reused",
                ),
                observed_at=at(base, 0),
            )
            mismatched = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PostToolUse",
                    turn="turn-B",
                    tool_name="apply_patch",
                    tool_use_id="tool-reused",
                ),
                observed_at=at(base, 1),
            )
            self.assertEqual(mismatched["status"], "not_reported")
            self.assertEqual(mismatched["reason"], "correlation_identity_mismatch")
            self.assertFalse(
                any(
                    record["event_type"] == "span_completed"
                    for record in read_execution_trace(mission_dir)
                )
            )

            matched = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PostToolUse",
                    turn="turn-A",
                    tool_name="Bash",
                    tool_use_id="tool-reused",
                    tool_response={"exit_code": 0},
                ),
                observed_at=at(base, 2),
            )
            self.assertEqual(matched["status"], "recorded")

    def test_parallel_subagents_overlap_without_creating_synthetic_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)

            for agent_id in ("agent-A", "agent-B"):
                handle_hook(
                    mission_dir,
                    state_dir,
                    hook(
                        "SubagentStart",
                        agent_id=agent_id,
                        agent_type="worker",
                    ),
                    observed_at=at(base, 0),
                )
            handle_hook(
                mission_dir,
                state_dir,
                hook("SubagentStop", agent_id="agent-B", agent_type="worker"),
                observed_at=at(base, 3),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook("SubagentStop", agent_id="agent-A", agent_type="worker"),
                observed_at=at(base, 5),
            )

            report = build_execution_cost_tree(
                mission_dir, view="audit", generated_at=at(base, 6)
            )
            standard = build_execution_cost_tree(
                mission_dir, view="standard", generated_at=at(base, 6)
            )
            self.assertEqual([node["id"] for node in report["nodes"]], ["T1", "T2"])
            self.assertEqual(
                [node["id"] for node in standard["nodes"]], ["T1", "T2"]
            )
            self.assertEqual(standard["trace"]["structure_fidelity"], "one_to_one")
            self.assertIn("TPlan 纵向实际执行时间轴", render_svg(standard))
            self.assertEqual(report["mission"]["cost"]["envelope_span_count"], 2)
            self.assertEqual(report["mission"]["cost"]["observed_interval_union_ms"], 5000)
            self.assertEqual(report["mission"]["cost"]["additive_resource_time_ms"], 0)
            completed = [
                record
                for record in read_execution_trace(mission_dir)
                if record["event_type"] == "span_completed"
                and record["span"]["kind"] == "agent_turn"
            ]
            self.assertEqual(len(completed), 2)
            self.assertNotEqual(
                completed[0]["span"]["span_id"], completed[1]["span"]["span_id"]
            )
            self.assertEqual(
                json.loads(coverage_path(mission_dir).read_text(encoding="utf-8"))[
                    "channels"
                ]["subagents"]["observed_span_count"],
                2,
            )

    def test_subagent_pair_requires_same_turn_and_agent_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)

            handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "SubagentStart",
                    turn="turn-A",
                    agent_id="agent-reused",
                    agent_type="explorer",
                ),
                observed_at=at(base, 0),
            )
            mismatched = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "SubagentStop",
                    turn="turn-B",
                    agent_id="agent-reused",
                    agent_type="reviewer",
                ),
                observed_at=at(base, 1),
            )
            self.assertEqual(mismatched["reason"], "correlation_identity_mismatch")

            matched = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "SubagentStop",
                    turn="turn-A",
                    agent_id="agent-reused",
                    agent_type="explorer",
                ),
                observed_at=at(base, 2),
            )
            self.assertEqual(matched["status"], "recorded")
            completed = [
                record
                for record in read_execution_trace(mission_dir)
                if record["event_type"] == "span_completed"
                and record["span"]["kind"] == "agent_turn"
            ]
            self.assertEqual(len(completed), 1)
            self.assertEqual(completed[0]["metadata"]["agent_role"], "explorer")

    def test_missing_active_node_uses_overhead_and_wrong_session_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, active=False)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)
            before = (mission_dir / "execution_trace.jsonl").read_bytes()

            rejected = handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    session="other-session",
                    tool_name="apply_patch",
                    tool_use_id="tool-wrong",
                ),
                observed_at=at(base, 0),
            )
            self.assertEqual(rejected["reason"], "session_binding_mismatch")
            self.assertEqual((mission_dir / "execution_trace.jsonl").read_bytes(), before)

            handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PreToolUse",
                    tool_name="apply_patch",
                    tool_use_id="tool-overhead",
                ),
                observed_at=at(base, 1),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook(
                    "PostToolUse",
                    tool_name="apply_patch",
                    tool_use_id="tool-overhead",
                ),
                observed_at=at(base, 2),
            )
            completed = read_execution_trace(mission_dir)[-1]
            self.assertIsNone(completed["task_id"])
            self.assertEqual(completed["span"]["attribution"], "mission_overhead")

    def test_otel_is_exact_only_with_unambiguous_turn_and_deduplicates_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)
            handle_hook(
                mission_dir,
                state_dir,
                hook("PreToolUse", tool_name="apply_patch", tool_use_id="tool-1"),
                observed_at=at(base, 0),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook("PostToolUse", tool_name="apply_patch", tool_use_id="tool-1"),
                observed_at=at(base, 1),
            )

            duplicate = ingest_otel_event(
                mission_dir,
                state_dir,
                otel_event(
                    base,
                    "otel-tool-1",
                    "tool",
                    tool_use_id="tool-1",
                    source_event="codex.tool_result",
                ),
            )
            self.assertEqual(duplicate["reason"], "hook_tool_preferred")
            model = ingest_otel_event(
                mission_dir,
                state_dir,
                otel_event(
                    base,
                    "otel-model-1",
                    "model",
                    task_id="T1",
                    model="gpt-5",
                    usage={
                        "input_tokens": 20,
                        "cached_input_tokens": 5,
                        "output_tokens": 7,
                    },
                ),
            )
            self.assertEqual(model["attribution"], "exact")
            self.assertEqual(model["task_id"], "T1")
            envelope = ingest_otel_event(
                mission_dir,
                state_dir,
                otel_event(
                    base,
                    "otel-turn-1",
                    "agent_turn",
                    task_id="T1",
                    source_event="codex.turn.e2e_duration",
                ),
            )
            self.assertEqual(envelope["status"], "recorded")
            report = build_execution_cost_tree(
                mission_dir, view="audit", generated_at=at(base, 20)
            )
            self.assertEqual(report["mission"]["cost"]["usage"]["input_tokens"], 20)
            self.assertEqual(report["mission"]["cost"]["usage"]["output_tokens"], 7)
            self.assertEqual(report["mission"]["cost"]["usage_coverage"], "complete")
            self.assertEqual(report["mission"]["cost"]["envelope_span_count"], 1)
            self.assertEqual(report["telemetry_capture"]["channels"]["tokens"]["status"], "observed")
            markdown = render_markdown(report)
            self.assertIn("## Codex 遥测覆盖", markdown)
            self.assertIn("hosted tools do not currently expose", markdown)

    def test_ambiguous_turn_downgrades_otel_to_mission_overhead(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)
            handle_hook(
                mission_dir,
                state_dir,
                hook("PreToolUse", tool_name="apply_patch", tool_use_id="tool-t1"),
                observed_at=at(base, 0),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook("PostToolUse", tool_name="apply_patch", tool_use_id="tool-t1"),
                observed_at=at(base, 1),
            )
            switched = run_script(
                "transition_task.py",
                str(mission_dir),
                "--task-id",
                "T2",
                "--status",
                "active",
            )
            self.assertEqual(switched.returncode, 0, switched.stderr)
            handle_hook(
                mission_dir,
                state_dir,
                hook("PreToolUse", tool_name="apply_patch", tool_use_id="tool-t2"),
                observed_at=at(base, 2),
            )
            handle_hook(
                mission_dir,
                state_dir,
                hook("PostToolUse", tool_name="apply_patch", tool_use_id="tool-t2"),
                observed_at=at(base, 3),
            )
            result = ingest_otel_event(
                mission_dir,
                state_dir,
                otel_event(
                    base,
                    "otel-model-ambiguous",
                    "model",
                    task_id="T1",
                    usage={"input_tokens": 1, "output_tokens": 1},
                ),
            )
            self.assertEqual(result["attribution"], "mission_overhead")
            self.assertIsNone(result["task_id"])

    def test_otel_rejects_raw_content_and_tokens_on_turn_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            base = datetime.now(timezone.utc) + timedelta(seconds=1)
            raw = otel_event(base, "otel-private", "model", prompt="do not persist")
            with self.assertRaisesRegex(TplanError, "forbidden raw-content"):
                ingest_otel_event(mission_dir, state_dir, raw)
            envelope = otel_event(
                base,
                "otel-turn-tokens",
                "agent_turn",
                source_event="codex.turn.e2e_duration",
                usage={"input_tokens": 5},
            )
            with self.assertRaisesRegex(TplanError, "only Codex model spans"):
                ingest_otel_event(mission_dir, state_dir, envelope)
            secret = otel_event(
                base,
                "otel-secret",
                "model",
                model="sk-abcdefghijklmnopqrstuvwxyz",
            )
            with self.assertRaisesRegex(TplanError, "secret-shaped"):
                ingest_otel_event(mission_dir, state_dir, secret)
            source_injection = otel_event(
                base,
                "otel-source-injection",
                "model",
                source_event="codex.api_request.raw_model_response_alice_example_com",
            )
            with self.assertRaisesRegex(TplanError, "source_event is unsupported"):
                ingest_otel_event(mission_dir, state_dir, source_injection)

    def test_telemetry_writers_fail_closed_on_runtime_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            corrupt_runtime_fingerprint(mission_dir)
            before = artifact_snapshot(mission_dir, state_dir)

            with self.assertRaisesRegex(TplanError, "runtime fingerprint mismatch"):
                bind_session(mission_dir, state_dir, session_id="session-1")

            self.assertEqual(artifact_snapshot(mission_dir, state_dir), before)

        for channel in ("hook", "otel"):
            with self.subTest(channel=channel), tempfile.TemporaryDirectory() as tmp:
                mission_dir = create_mission(tmp)
                state_dir = Path(tmp) / "host-state"
                state_dir.mkdir()
                bind_session(mission_dir, state_dir, session_id="session-1")
                corrupt_runtime_fingerprint(mission_dir)
                before = artifact_snapshot(mission_dir, state_dir)
                base = datetime.now(timezone.utc) + timedelta(seconds=1)

                with self.assertRaisesRegex(TplanError, "runtime fingerprint mismatch"):
                    if channel == "hook":
                        handle_hook(
                            mission_dir,
                            state_dir,
                            hook(
                                "PreToolUse",
                                tool_name="Bash",
                                tool_use_id="tool-provenance",
                            ),
                            observed_at=at(base, 0),
                        )
                    else:
                        ingest_otel_event(
                            mission_dir,
                            state_dir,
                            otel_event(base, "otel-provenance", "model"),
                        )

                self.assertEqual(artifact_snapshot(mission_dir, state_dir), before)

    def test_optional_hook_failure_returns_success_and_tampered_sidecar_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")
            before = (mission_dir / "execution_trace.jsonl").read_bytes()
            malformed = run_script(
                "codex_telemetry_adapter.py",
                "hook",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                input_text=json.dumps(
                    {
                        "session_id": "session-1",
                        "hook_event_name": "PreToolUse",
                    }
                ),
            )
            self.assertEqual(malformed.returncode, 0, malformed.stderr)
            self.assertEqual((mission_dir / "execution_trace.jsonl").read_bytes(), before)

            tampered = json.loads(coverage_path(mission_dir).read_text(encoding="utf-8"))
            tampered["raw_prompt"] = "must not reach renderer"
            coverage_path(mission_dir).write_text(json.dumps(tampered), encoding="utf-8")
            report = build_execution_cost_tree(mission_dir, view="audit")
            self.assertEqual(
                report["telemetry_capture"]["diagnostics"]["last_code"],
                "coverage_sidecar_binding_invalid",
            )
            self.assertNotIn("must not reach renderer", json.dumps(report))

    def test_generator_binds_session_and_emits_all_four_hook_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            result = run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads(result.stdout)
            self.assertEqual(
                set(config["hooks"]),
                {"PreToolUse", "PostToolUse", "SubagentStart", "SubagentStop"},
            )
            self.assertTrue(next(state_dir.glob("*.json")).is_file())
            coverage = json.loads(coverage_path(mission_dir).read_text(encoding="utf-8"))
            self.assertEqual(coverage["channels"]["local_tools"]["status"], "not_reported")
            self.assertIn(
                "preflight_required",
                coverage["channels"]["local_tools"]["reason"],
            )

    def test_subagent_stop_cli_returns_valid_json_on_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-1")

            result = run_script(
                "codex_telemetry_adapter.py",
                "hook",
                str(mission_dir),
                "--state-dir",
                str(state_dir),
                input_text=json.dumps(
                    hook(
                        "SubagentStop",
                        agent_id="agent-without-start",
                        agent_type="worker",
                    )
                ),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {})


if __name__ == "__main__":
    unittest.main()
