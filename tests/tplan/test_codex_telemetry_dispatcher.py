import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from codex_telemetry_adapter import bind_session, coverage_path, hook_command
from codex_telemetry_dispatcher import (
    DISPATCHER_VERSION,
    REGISTRY_SCHEMA_VERSION,
    dispatch_hook,
    register_binding,
    register_source_claim,
    registry_path,
    registry_sources,
    unregister_binding,
)
from tests.tplan.test_codex_telemetry_adapter import (
    at,
    create_mission,
    hook,
    run_script,
)
from tplan_runtime import TplanError, read_execution_trace


def create_named_mission(root: Path, name: str) -> Path:
    mission_root = root / name
    mission_root.mkdir()
    return create_mission(mission_root)


class CodexTelemetryDispatcherTests(unittest.TestCase):
    def test_generated_hook_definition_is_stable_across_missions_and_sessions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_one = create_named_mission(root, "one")
            mission_two = create_named_mission(root, "two")
            state_dir = root / "host-state"
            state_dir.mkdir()
            output_one = root / "hooks-one.json"
            output_two = root / "hooks-two.json"

            generated_one = run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_one),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-one",
                "--output",
                str(output_one),
            )
            generated_two = run_script(
                "generate_codex_telemetry_hooks.py",
                str(mission_two),
                "--state-dir",
                str(state_dir),
                "--session-id",
                "session-two",
                "--output",
                str(output_two),
            )
            self.assertEqual(generated_one.returncode, 0, generated_one.stderr)
            self.assertEqual(generated_two.returncode, 0, generated_two.stderr)
            config_one = json.loads(output_one.read_text(encoding="utf-8"))
            config_two = json.loads(output_two.read_text(encoding="utf-8"))
            self.assertEqual(config_one, config_two)
            command = config_one["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
            self.assertIn("codex_telemetry_dispatcher.py", command)
            self.assertNotIn(str(mission_one), command)
            self.assertNotIn(str(mission_two), command)
            self.assertNotIn("session-one", command)
            self.assertNotIn("session-two", command)
            self.assertEqual(
                hook_command(mission_one, state_dir),
                hook_command(mission_two, state_dir),
            )

            registry = json.loads(
                registry_path(state_dir).read_text(encoding="utf-8")
            )
            self.assertEqual(
                set(registry["bindings"]),
                {"session-one", "session-two"},
            )

    def test_dispatcher_routes_two_sessions_to_two_missions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_one = create_named_mission(root, "one")
            mission_two = create_named_mission(root, "two")
            state_dir = root / "host-state"
            state_dir.mkdir()
            for mission, session in (
                (mission_one, "session-one"),
                (mission_two, "session-two"),
            ):
                bind_session(mission, state_dir, session_id=session)
                register_binding(
                    mission,
                    state_dir,
                    session_id=session,
                )

            base = datetime.now(timezone.utc) + timedelta(seconds=1)
            for offset, (mission, session, tool_id) in enumerate(
                (
                    (mission_one, "session-one", "tool-one"),
                    (mission_two, "session-two", "tool-two"),
                )
            ):
                started = dispatch_hook(
                    state_dir,
                    hook(
                        "PreToolUse",
                        session=session,
                        tool_name="Bash",
                        tool_use_id=tool_id,
                    ),
                    observed_at=at(base, offset * 2),
                )
                completed = dispatch_hook(
                    state_dir,
                    hook(
                        "PostToolUse",
                        session=session,
                        tool_name="Bash",
                        tool_use_id=tool_id,
                        tool_response={"exit_code": 0},
                    ),
                    observed_at=at(base, offset * 2 + 1),
                )
                self.assertEqual(started["status"], "recorded")
                self.assertEqual(completed["status"], "recorded")
                completed_spans = [
                    record
                    for record in read_execution_trace(mission)
                    if record["event_type"] == "span_completed"
                ]
                self.assertEqual(len(completed_spans), 1)

    def test_unknown_session_fails_closed_without_mission_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = create_named_mission(root, "one")
            state_dir = root / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-one")
            register_binding(
                mission_dir,
                state_dir,
                session_id="session-one",
            )
            before = read_execution_trace(mission_dir)
            result = dispatch_hook(
                state_dir,
                hook(
                    "PreToolUse",
                    session="session-unknown",
                    tool_name="Bash",
                    tool_use_id="tool-unknown",
                ),
            )
            self.assertEqual(result["status"], "not_reported")
            self.assertEqual(
                result["reason"],
                "dispatcher_session_not_registered",
            )
            self.assertEqual(read_execution_trace(mission_dir), before)

    def test_registry_conflict_requires_previous_mission_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_one = create_named_mission(root, "one")
            mission_two = create_named_mission(root, "two")
            state_dir = root / "host-state"
            state_dir.mkdir()
            bind_session(mission_one, state_dir, session_id="shared-session")
            register_binding(
                mission_one,
                state_dir,
                session_id="shared-session",
            )
            bind_session(mission_two, state_dir, session_id="shared-session")
            with self.assertRaisesRegex(TplanError, "another Mission"):
                register_binding(
                    mission_two,
                    state_dir,
                    session_id="shared-session",
                )
            with self.assertRaisesRegex(TplanError, "clean the previous Mission"):
                register_binding(
                    mission_two,
                    state_dir,
                    session_id="shared-session",
                    replace=True,
                )
            removed_one = unregister_binding(mission_one, state_dir)
            self.assertEqual(removed_one["removed_binding_count"], 1)
            registered_two = register_binding(
                mission_two,
                state_dir,
                session_id="shared-session",
                replace=True,
            )
            self.assertEqual(registered_two["active_binding_count"], 1)
            removed_two = unregister_binding(mission_two, state_dir)
            self.assertEqual(removed_two["removed_binding_count"], 1)
            self.assertEqual(removed_two["active_binding_count"], 0)

    def test_raw_session_ids_stay_in_host_registry_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = create_named_mission(root, "one")
            state_dir = root / "host-state"
            state_dir.mkdir()
            session_id = "session-private-registry-only"
            bind_session(mission_dir, state_dir, session_id=session_id)
            register_binding(
                mission_dir,
                state_dir,
                session_id=session_id,
            )
            self.assertIn(
                session_id,
                registry_path(state_dir).read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                session_id,
                coverage_path(mission_dir).read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                session_id,
                (mission_dir / "execution_trace.jsonl").read_text(encoding="utf-8"),
            )

    def test_subagent_stop_cli_preserves_required_empty_json_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = create_named_mission(root, "one")
            state_dir = root / "host-state"
            state_dir.mkdir()
            bind_session(mission_dir, state_dir, session_id="session-one")
            register_binding(
                mission_dir,
                state_dir,
                session_id="session-one",
            )
            result = run_script(
                "codex_telemetry_dispatcher.py",
                "hook",
                "--state-dir",
                str(state_dir),
                input_text=json.dumps(
                    hook(
                        "SubagentStop",
                        session="session-one",
                        agent_id="agent-without-start",
                        agent_type="worker",
                    )
                ),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {})

    def test_registry_rejects_non_hook_source_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            with self.assertRaisesRegex(TplanError, r"\.codex/hooks\.json"):
                register_source_claim(
                    state_dir,
                    source_path=Path(tmp) / "not-hooks.json",
                    scope="project",
                    created_by_tplan=True,
                )

            registry_path(state_dir).write_text(
                json.dumps(
                    {
                        "schema_version": REGISTRY_SCHEMA_VERSION,
                        "dispatcher_version": DISPATCHER_VERSION,
                        "created_at": "2026-07-30T00:00:00Z",
                        "updated_at": "2026-07-30T00:00:00Z",
                        "bindings": {},
                        "sources": {
                            str((Path(tmp) / "arbitrary.json").resolve()): {
                                "scope": "project",
                                "created_by_tplan": True,
                                "registered_at": "2026-07-30T00:00:00Z",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(TplanError, "source path is invalid"):
                registry_sources(state_dir)


if __name__ == "__main__":
    unittest.main()
