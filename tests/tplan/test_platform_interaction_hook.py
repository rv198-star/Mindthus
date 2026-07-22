import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import generate_interaction_hooks
import platform_interaction_hook
import tplan_runtime


EVENTS = {
    "codex-cli": ("UserPromptSubmit", "PreToolUse", "Stop", "Bash", "view_image"),
    "codex-desktop": ("UserPromptSubmit", "PreToolUse", "Stop", "Bash", "view_image"),
    "claude-code": ("UserPromptSubmit", "PreToolUse", "Stop", "Write", "Read"),
    "gemini-cli": ("BeforeAgent", "BeforeTool", "AfterAgent", "run_shell_command", "read_file"),
}


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    mission = tplan_runtime.build_mission(
        mission_id="platform-interaction-hook",
        title="Platform Interaction Hook",
        objective="Keep an active path stable across native platform hooks.",
        acceptance_evidence=[{"id": "A1", "description": "Hook behavior is verified."}],
        human_in_loop=0,
        risk_tolerance=50,
        resource_sufficiency=50,
        tasks=[
            {
                "id": "T1",
                "title": "Protect active path",
                "role": "success-critical",
                "mission_contribution": "Provides the baseline path.",
                "acceptance_evidence": ["A1"],
            }
        ],
    )
    mission_dir.mkdir()
    tplan_runtime.write_mission(mission_dir, mission)
    tplan_runtime.initialize_execution_trace(mission_dir, mission)
    tplan_runtime.transition_task_status(mission_dir, "T1", "active")
    return mission_dir


def event(name, *, session="S1", prompt=None, timestamp="2026-07-22T10:00:00Z", turn_id="T1", tool=None):
    payload = {"hook_event_name": name, "session_id": session, "timestamp": timestamp}
    if prompt is not None:
        payload["prompt"] = prompt
    if turn_id is not None:
        payload["turn_id"] = turn_id
    if tool is not None:
        payload["tool_name"] = tool
        payload["tool_input"] = {}
    return payload


class PlatformInteractionHookTests(unittest.TestCase):
    def test_first_owned_end_directly_releases_guard_without_continuation_on_all_profiles(self):
        for platform, (message_event, tool_event, end_event, mutation_tool, read_tool) in EVENTS.items():
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as tmp:
                mission_dir = create_mission(tmp)
                baseline = tplan_runtime.read_mission(mission_dir)
                self.assertEqual(
                    platform_interaction_hook.handle_hook(platform, mission_dir, event(message_event, prompt="Start.")),
                    {},
                )
                guarded = platform_interaction_hook.handle_hook(
                    platform,
                    mission_dir,
                    event(message_event, prompt="What is the status?", timestamp="2026-07-22T10:00:01Z"),
                )
                self.assertIn("guard", guarded["hookSpecificOutput"]["additionalContext"].lower())
                self.assertIn(
                    "mcp__tplan_guard__stop_fixed",
                    guarded["hookSpecificOutput"]["additionalContext"],
                )
                self.assertIn(
                    "TPLAN_CONTROL guard=",
                    guarded["hookSpecificOutput"]["additionalContext"],
                )
                guard = tplan_runtime.read_interaction_guard(mission_dir)
                self.assertEqual(guard["phase"], "protecting")
                self.assertEqual(guard["schema_version"], "tplan.interaction_guard.v0.2")

                denied = platform_interaction_hook.handle_hook(platform, mission_dir, event(tool_event, tool=mutation_tool))
                if platform == "gemini-cli":
                    self.assertEqual(denied["decision"], "deny")
                else:
                    self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertEqual(platform_interaction_hook.handle_hook(platform, mission_dir, event(tool_event, tool=read_tool)), {})
                self.assertEqual(
                    platform_interaction_hook.handle_hook(
                        platform, mission_dir, event(tool_event, tool="mcp__tplan_guard__stop_fixed")
                    ),
                    {},
                )
                blocked_resume = platform_interaction_hook.handle_hook(
                    platform, mission_dir, event(tool_event, tool="mcp__tplan_guard__resume_unchanged")
                )
                if platform == "gemini-cli":
                    self.assertEqual(blocked_resume["decision"], "deny")
                else:
                    self.assertEqual(blocked_resume["hookSpecificOutput"]["permissionDecision"], "deny")

                ended = platform_interaction_hook.handle_hook(platform, mission_dir, event(end_event))
                self.assertEqual(ended, {})
                self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
                self.assertFalse(platform_interaction_hook._host_state_path(mission_dir).exists())
                self.assertEqual(tplan_runtime.read_mission(mission_dir), baseline)

    def test_awaiting_authority_survives_turn_end_without_recursive_prompt_and_accepts_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Change plan.", timestamp="2026-07-22T10:00:01Z")
            )
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            tplan_runtime.resolve_interaction_guard(
                mission_dir,
                guard_id=guard["guard_id"],
                expected_revision=guard["revision"],
                message_refs=[item["message_ref"] for item in guard["messages"]],
                disposition="await_clarification",
            )
            ended = platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("Stop"))
            self.assertIn("awaiting_authority", ended["systemMessage"])
            self.assertNotIn("TPLAN_CONTINUATION", str(ended))
            current = tplan_runtime.read_interaction_guard(mission_dir)
            self.assertEqual(current["phase"], "awaiting_authority")
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Confirmed.", timestamp="2026-07-22T10:01:00Z")
            )
            current = tplan_runtime.read_interaction_guard(mission_dir)
            self.assertEqual(len([item for item in current["messages"] if item["status"] == "pending"]), 1)

    def test_non_owning_codex_end_orphans_without_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start.", turn_id="A"))
            platform_interaction_hook.handle_hook(
                "codex-desktop",
                mission_dir,
                event("UserPromptSubmit", prompt="Interrupt.", timestamp="2026-07-22T10:00:01Z", turn_id="B"),
            )
            result = platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("Stop", turn_id="A"))
            self.assertIn("non-owning", result["systemMessage"])
            self.assertNotIn("TPLAN_CONTINUATION", str(result))
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            self.assertEqual(guard["phase"], "orphaned")
            self.assertEqual(guard["recovery"]["reason"], "non_owning_turn_end")

    def test_host_event_id_is_preferred_for_duplicate_message_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            interrupted = event("UserPromptSubmit", prompt="Status?", timestamp="2026-07-22T10:00:01Z")
            interrupted["event_id"] = "host-message-42"
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, interrupted)
            duplicate = dict(interrupted)
            duplicate["timestamp"] = "2026-07-22T10:00:02Z"
            duplicate["prompt"] = "Status? (transport retry with changed metadata)"
            result = platform_interaction_hook.handle_hook("codex-desktop", mission_dir, duplicate)
            self.assertIn("duplicate", result["hookSpecificOutput"]["additionalContext"])
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            self.assertEqual(len(guard["messages"]), 1)

    def test_external_host_trace_is_sanitized_append_only_and_captures_guard_transition(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            secret_prompt = "do-not-persist-this-prompt"
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."), state_dir=state_dir
            )
            platform_interaction_hook.handle_hook(
                "codex-desktop",
                mission_dir,
                event("UserPromptSubmit", prompt=secret_prompt, timestamp="2026-07-22T10:00:01Z"),
                state_dir=state_dir,
            )
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("PreToolUse", tool="Bash"), state_dir=state_dir
            )
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("Stop"), state_dir=state_dir
            )
            trace_path = platform_interaction_hook._host_trace_path(mission_dir, state_dir)
            raw_trace = trace_path.read_text(encoding="utf-8")
            records = [json.loads(line) for line in raw_trace.splitlines() if line]
            self.assertEqual([record["trace_seq"] for record in records], [1, 2, 3, 4])
            self.assertNotIn(secret_prompt, raw_trace)
            self.assertNotIn("S1", raw_trace)
            self.assertEqual(records[1]["event_kind"], "message")
            self.assertEqual(records[1]["guard_before"], None)
            self.assertEqual(records[1]["guard_after"]["phase"], "protecting")
            self.assertTrue(records[1]["recorded_at"].endswith("Z"))
            self.assertTrue(records[1]["host"]["profile_digest"].startswith("sha256:"))
            self.assertEqual(records[1]["host"]["build"], "unavailable")
            self.assertEqual(records[2]["result_kind"], "deny_tool")
            self.assertIn("mission", records[2]["boundary_before"])
            self.assertIn("evidence", records[2]["boundary_after"])
            self.assertEqual(records[3]["event_kind"], "turn_end")
            self.assertEqual(records[3]["guard_before"]["phase"], "protecting")
            self.assertIsNone(records[3]["guard_after"])
            self.assertEqual(records[3]["result_kind"], "allow")
            if os.name != "nt":
                self.assertEqual(trace_path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(trace_path.with_suffix(".lock").stat().st_mode & 0o777, 0o600)

    def test_trace_append_failure_never_reintroduces_continuation_or_blocks_direct_release(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            platform_interaction_hook, "_append_host_trace", side_effect=OSError("trace unavailable")
        ):
            mission_dir = create_mission(tmp)
            self.assertEqual(
                platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start.")),
                {},
            )
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Interrupted.", timestamp="2026-07-22T10:00:01Z")
            )
            self.assertIsNotNone(tplan_runtime.read_interaction_guard(mission_dir))
            ended = platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("Stop"))
            self.assertEqual(ended, {})
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
            self.assertNotIn("TPLAN_CONTINUATION", str(ended))

    def test_trace_context_failure_and_unknown_event_never_block_turn_end_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            self.assertEqual(
                platform_interaction_hook.handle_hook(
                    "codex-desktop", mission_dir, event("Unrecognized-secret-event"), state_dir=state_dir
                ),
                {},
            )
            self.assertFalse(platform_interaction_hook._host_trace_path(mission_dir, state_dir).exists())
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."), state_dir=state_dir
            )
            platform_interaction_hook.handle_hook(
                "codex-desktop",
                mission_dir,
                event("UserPromptSubmit", prompt="Interrupted.", timestamp="2026-07-22T10:00:01Z"),
                state_dir=state_dir,
            )
            with mock.patch.object(platform_interaction_hook, "_new_host_trace_context", side_effect=OSError("trace read failed")):
                ended = platform_interaction_hook.handle_hook(
                    "codex-desktop", mission_dir, event("Stop"), state_dir=state_dir
                )
            self.assertEqual(ended, {})
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
            self.assertNotIn("TPLAN_CONTINUATION", str(ended))

    def test_invalid_prior_trace_is_never_silently_extended(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            trace_path = platform_interaction_hook._host_trace_path(mission_dir, state_dir)
            trace_path.write_text('{"schema_version":"wrong","trace_seq":1}\n', encoding="utf-8")
            self.assertEqual(
                platform_interaction_hook.handle_hook(
                    "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."), state_dir=state_dir
                ),
                {},
            )
            self.assertEqual(trace_path.read_text(encoding="utf-8"), '{"schema_version":"wrong","trace_seq":1}\n')

    def test_operator_control_envelope_stops_without_agent_or_hook_disable(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Please stop.", timestamp="2026-07-22T10:00:01Z")
            )
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            result = platform_interaction_hook.handle_hook(
                "codex-desktop",
                mission_dir,
                event(
                    "UserPromptSubmit",
                    prompt=f"TPLAN_CONTROL guard={guard['guard_id']} revision={guard['revision']} action=stop",
                    timestamp="2026-07-22T10:00:02Z",
                ),
            )
            self.assertEqual(result["decision"], "block")
            self.assertIn("safely stopped", result["reason"])
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
            self.assertEqual(tplan_runtime.read_mission(mission_dir)["mission"]["status"], "requires_human")

    def test_operator_control_envelope_resumes_original_baseline_without_agent_unlock(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            baseline = tplan_runtime.read_mission(mission_dir)
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Status?", timestamp="2026-07-22T10:00:01Z")
            )
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            result = platform_interaction_hook.handle_hook(
                "codex-desktop",
                mission_dir,
                event(
                    "UserPromptSubmit",
                    prompt=f"TPLAN_CONTROL guard={guard['guard_id']} revision={guard['revision']} action=resume",
                    timestamp="2026-07-22T10:00:02Z",
                ),
            )
            self.assertEqual(result["decision"], "block")
            self.assertIn("resumed the unchanged", result["reason"])
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
            self.assertEqual(tplan_runtime.read_mission(mission_dir), baseline)

    def test_same_session_operator_resume_recovers_a_guard_orphaned_at_session_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            baseline = tplan_runtime.read_mission(mission_dir)
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Interrupted.", timestamp="2026-07-22T10:00:01Z")
            )
            self.assertEqual(
                platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("SessionStart", prompt=None)),
                {},
            )
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            self.assertEqual(guard["phase"], "orphaned")
            self.assertEqual(guard["recovery"]["reason"], "host_session_restart")
            result = platform_interaction_hook.handle_hook(
                "codex-desktop",
                mission_dir,
                event(
                    "UserPromptSubmit",
                    prompt=f"TPLAN_CONTROL guard={guard['guard_id']} revision={guard['revision']} action=resume",
                    timestamp="2026-07-22T10:00:02Z",
                ),
            )
            self.assertEqual(result["decision"], "block")
            self.assertIn("resumed the unchanged", result["reason"])
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
            self.assertEqual(tplan_runtime.read_mission(mission_dir), baseline)

    def test_safe_control_names_are_exact_and_operator_envelope_cannot_cross_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Interrupt.", timestamp="2026-07-22T10:00:01Z")
            )
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            for alias in ("mcp__tplan_guard__stop-fixed", "MCP__TPLAN_GUARD__STOP_FIXED", "view-image"):
                denied = platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("PreToolUse", tool=alias))
                self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
            blocked = platform_interaction_hook.handle_hook(
                "codex-desktop",
                mission_dir,
                event(
                    "UserPromptSubmit",
                    session="S2",
                    prompt=f"TPLAN_CONTROL guard={guard['guard_id']} revision={guard['revision']} action=resume",
                    timestamp="2026-07-22T10:00:02Z",
                ),
            )
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("guard-owning", blocked["reason"])
            self.assertIsNotNone(tplan_runtime.read_interaction_guard(mission_dir))

    def test_expired_lease_is_orphaned_on_next_host_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Interrupt.", timestamp="2026-07-22T10:00:01Z")
            )
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            guard["lease"]["deadline_at"] = "2000-01-01T00:00:00+00:00"
            tplan_runtime._write_interaction_guard_unlocked(mission_dir, guard)
            result = platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("PreToolUse", tool="view_image"))
            self.assertEqual(result, {})
            current = tplan_runtime.read_interaction_guard(mission_dir)
            self.assertEqual(current["phase"], "orphaned")
            self.assertEqual(current["recovery"]["reason"], "lease_expired")

    def test_session_start_orphans_a_persisted_active_turn_and_stop_exception_never_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Interrupt.", timestamp="2026-07-22T10:00:01Z")
            )
            restarted = platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("SessionStart", prompt=None)
            )
            self.assertEqual(restarted, {})
            self.assertEqual(tplan_runtime.read_interaction_guard(mission_dir)["recovery"]["reason"], "host_session_restart")

        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Start."))
            platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Interrupt.", timestamp="2026-07-22T10:00:01Z")
            )
            guard = tplan_runtime.read_interaction_guard(mission_dir)
            guard["lease"]["deadline_at"] = "not-an-iso-time"
            tplan_runtime._write_interaction_guard_unlocked(mission_dir, guard)
            ended = platform_interaction_hook.handle_hook("codex-desktop", mission_dir, event("Stop"))
            self.assertIn("failed safely", ended["systemMessage"])
            self.assertNotIn("TPLAN_CONTINUATION", str(ended))

    def test_legacy_host_state_is_orphaned_instead_of_reentering_continuation_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="codex-desktop", message_ref="M1", binding_id="S1")
            platform_interaction_hook._host_state_path(mission_dir).write_text(
                """{"schema_version":"tplan.interaction_host_session.v0.1","platform":"codex-desktop","session_id":"S1","first_message_ref":"M0","last_message_ref":"M1","continuation_requested":true,"continuation_token":"nonce","continuation_observed":false,"guard_turn_id":"T1","continuation_turn_id":null}\n""",
                encoding="utf-8",
            )
            result = platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Next message.", timestamp="2026-07-22T10:00:02Z")
            )
            self.assertIn("guard", result["hookSpecificOutput"]["additionalContext"].lower())
            migrated = tplan_runtime.read_interaction_guard(mission_dir)
            self.assertEqual(migrated["phase"], "orphaned")
            self.assertEqual(migrated["recovery"]["reason"], "legacy_continuation_state")
            self.assertNotIn("TPLAN_CONTINUATION", str(result))
            self.assertNotEqual(guard["revision"], migrated["revision"])

    def test_corrupt_host_state_blocks_prompt_instead_of_failing_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            platform_interaction_hook._host_state_path(mission_dir).write_text("{}\n", encoding="utf-8")
            result = platform_interaction_hook.handle_hook(
                "codex-desktop", mission_dir, event("UserPromptSubmit", prompt="Must not proceed.")
            )
            self.assertEqual(result["decision"], "block")
            self.assertIn("fail-closed", result["reason"])


class InteractionHookGeneratorTests(unittest.TestCase):
    def test_uncertified_profile_requires_explicit_experimental_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            with self.assertRaisesRegex(tplan_runtime.TplanError, "no certified"):
                generate_interaction_hooks.hook_config("codex-desktop", mission_dir, state_dir=state_dir)
            config = generate_interaction_hooks.hook_config(
                "codex-desktop", mission_dir, state_dir=state_dir, experimental=True
            )
            self.assertEqual(set(config["hooks"]), {"SessionStart", "UserPromptSubmit", "PreToolUse", "Stop"})
            self.assertIn("codex-desktop@v0.2-unverified", config["description"])

    def test_platform_configs_are_independent_and_use_native_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            for platform, (message, before, end, *_rest) in EVENTS.items():
                with self.subTest(platform=platform):
                    config = generate_interaction_hooks.hook_config(
                        platform, mission_dir, state_dir=state_dir, experimental=True
                    )
                    expected_events = {message, before, end}
                    if platform.startswith("codex-"):
                        expected_events.add("SessionStart")
                    self.assertEqual(set(config["hooks"]), expected_events)
                    self.assertIn(str(state_dir), str(config))
                    self.assertIn("platform_interaction_hook.py", str(config))
                    self.assertIn("hook_supervisor.py", str(config))
            gemini = generate_interaction_hooks.hook_config("gemini-cli", mission_dir, state_dir=state_dir, experimental=True)
            self.assertEqual(gemini["hooks"]["BeforeTool"][0]["hooks"][0]["timeout"], 30_000)

    def test_generated_turn_end_wrapper_never_returns_exit_two_on_supervisor_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-state"
            state_dir.mkdir()
            config = generate_interaction_hooks.hook_config(
                "codex-desktop", mission_dir, state_dir=state_dir, experimental=True
            )
            stop_command = config["hooks"]["Stop"][0]["hooks"][0]["command"]
            prompt_command = config["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
            self.assertIn("failed safely", stop_command)
            self.assertIn("exit 0", stop_command)
            self.assertNotIn("exit 2", stop_command)
            self.assertIn("exit 2", prompt_command)
            failed_child_command = stop_command.replace(
                str(SCRIPTS / "platform_interaction_hook.py"), str(SCRIPTS / "missing_adapter.py")
            )
            completed = subprocess.run(failed_child_command, shell=True, text=True, input="{}", capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("failed safely", completed.stdout)

    def test_generated_command_reaches_adapter_and_uses_external_state_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            state_dir = Path(tmp) / "host-owned-state"
            state_dir.mkdir()
            config = generate_interaction_hooks.hook_config("codex-desktop", mission_dir, state_dir=state_dir, experimental=True)
            command = config["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
            completed = subprocess.run(
                command,
                shell=True,
                text=True,
                input='{"hook_event_name":"UserPromptSubmit","session_id":"S1","turn_id":"T1","prompt":"Start"}',
                capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), "{}")
            state_path = platform_interaction_hook._host_state_path(mission_dir, state_dir)
            self.assertTrue(state_path.exists())
            if os.name != "nt":
                self.assertEqual(state_path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(state_path.with_suffix(".lock").stat().st_mode & 0o777, 0o600)

    def test_generator_rejects_missing_or_mission_local_state_directory_before_profile_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            with self.assertRaisesRegex(tplan_runtime.TplanError, "pre-created"):
                generate_interaction_hooks.hook_config("codex-desktop", mission_dir, state_dir=Path(tmp) / "missing", experimental=True)
            local_state = mission_dir / "host-state"
            local_state.mkdir()
            with self.assertRaisesRegex(tplan_runtime.TplanError, "outside"):
                generate_interaction_hooks.hook_config("codex-desktop", mission_dir, state_dir=local_state, experimental=True)

    def test_hook_supervisor_normalizes_child_failure_and_timeout_to_exit_two(self):
        supervisor = SCRIPTS / "hook_supervisor.py"
        failed = subprocess.run([sys.executable, str(supervisor), "--", sys.executable, "-c", "raise SystemExit(1)"], input=b"{}", capture_output=True)
        self.assertEqual(failed.returncode, 2)
        timed_out = subprocess.run(
            [sys.executable, str(supervisor), "--timeout", "0.01", "--", sys.executable, "-c", "import time; time.sleep(1)"],
            input=b"{}",
            capture_output=True,
        )
        self.assertEqual(timed_out.returncode, 2)


if __name__ == "__main__":
    unittest.main()
