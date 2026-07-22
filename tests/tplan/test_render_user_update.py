import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def create_lite_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    result = run_script(
        "init_lite.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "m1",
        "--title",
        "User Output Mission",
        "--objective",
        "Make tplan progress readable to ordinary users.",
        "--acceptance-evidence",
        "A1:User-facing output leads with meaning.",
        "--active-task-id",
        "T1",
        "--active-task-title",
        "Render readable progress summary",
        "--active-task-contribution",
        "Turns internal runtime state into user-facing language.",
        "--latest-state",
        "Ready to render a user-facing summary.",
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    evidence = run_script(
        "checkpoint.py",
        str(mission_dir),
        "--task-id",
        "T1",
        "--log-summary",
        "Rendered a readable update.",
        "--evidence-type",
        "acceptance",
        "--evidence-summary",
        "The update explains progress without leading with internal IDs.",
        "--evidence-task-id",
        "T1",
        "--evidence-payload-json",
        '{"acceptance_ids":["A1"]}',
    )
    if evidence.returncode != 0:
        raise AssertionError(evidence.stderr)
    return mission_dir


def render_json(mission_dir, *args):
    result = run_script("render_user_update.py", str(mission_dir), "--json", *args)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def create_pending_transaction(mission_dir):
    transaction = {
        "schema_version": "tplan.mission_transaction.v0.2",
        "mission": json.loads((mission_dir / "mission.json").read_text(encoding="utf-8")),
        "trace_text": (mission_dir / "execution_trace.jsonl").read_text(encoding="utf-8"),
        "evidence_text": (mission_dir / "evidence.jsonl").read_text(encoding="utf-8"),
        "latest_state": "A prepared transaction must be recovered by a writer.",
    }
    path = mission_dir / ".mission-transaction.json"
    path.write_text(json.dumps(transaction), encoding="utf-8")
    return path


class RenderUserUpdateTests(unittest.TestCase):
    def test_user_update_leads_with_meaning_not_internal_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            event_id = json.loads((mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()[0])["id"]

            result = run_script("render_user_update.py", str(mission_dir))

            self.assertEqual(result.returncode, 0, result.stderr)
            output = result.stdout
            self.assertIn("当前目标：", output)
            self.assertIn("Make tplan progress readable to ordinary users.", output)
            self.assertIn("当前进展：", output)
            self.assertIn("Render readable progress summary", output)
            self.assertIn("可计推进：", output)
            self.assertIn("The update explains progress without leading with internal IDs.", output)
            self.assertNotIn("T1", output)
            self.assertNotIn(event_id, output)

    def test_user_update_can_include_internal_refs_as_secondary_debug_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            event_id = json.loads((mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()[0])["id"]

            result = run_script("render_user_update.py", str(mission_dir), "--include-internal")

            self.assertEqual(result.returncode, 0, result.stderr)
            output = result.stdout
            self.assertIn("当前目标：", output)
            self.assertIn("内部恢复引用：", output)
            self.assertIn("active_task_id: T1", output)
            self.assertIn(f"evidence_ids: {event_id}", output)
            self.assertLess(output.index("当前目标："), output.index("内部恢复引用："))

    def test_automatic_delivery_is_quiet_twice_then_emits_a_heartbeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            initial = render_json(mission_dir, "--delivery", "automatic")
            self.assertEqual(initial["update_kind"], "full")

            first = render_json(mission_dir, "--delivery", "automatic", "--cursor", initial["cursor"])
            self.assertEqual(first["update_kind"], "quiet")
            self.assertEqual(first["quiet_streak"], 1)
            self.assertEqual(first["text"], "")

            second = render_json(mission_dir, "--delivery", "automatic", "--cursor", first["cursor"])
            self.assertEqual(second["update_kind"], "quiet")
            self.assertEqual(second["quiet_streak"], 2)
            self.assertEqual(second["text"], "")

            third = render_json(mission_dir, "--delivery", "automatic", "--cursor", second["cursor"])
            self.assertEqual(third["update_kind"], "heartbeat")
            self.assertEqual(third["quiet_streak"], 0)
            self.assertIn("连续 3 次自动检查", third["text"])
            self.assertIn("without leading with internal IDs", third["text"])

            fourth = render_json(mission_dir, "--delivery", "automatic", "--cursor", third["cursor"])
            self.assertEqual(fourth["update_kind"], "quiet")
            self.assertEqual(fourth["quiet_streak"], 1)

            fifth = render_json(mission_dir, "--delivery", "automatic", "--cursor", fourth["cursor"])
            self.assertEqual(fifth["update_kind"], "quiet")
            sixth = render_json(mission_dir, "--delivery", "automatic", "--cursor", fifth["cursor"])
            self.assertEqual(sixth["update_kind"], "heartbeat")

            seventh = render_json(mission_dir, "--delivery", "automatic", "--cursor", sixth["cursor"])
            eighth = render_json(mission_dir, "--delivery", "automatic", "--cursor", seventh["cursor"])
            ninth = render_json(mission_dir, "--delivery", "automatic", "--cursor", eighth["cursor"])
            self.assertEqual([seventh["update_kind"], eighth["update_kind"], ninth["update_kind"]], ["quiet", "quiet", "heartbeat"])

            quiet_text = run_script(
                "render_user_update.py",
                str(mission_dir),
                "--delivery",
                "automatic",
                "--cursor",
                third["cursor"],
            )
            self.assertEqual(quiet_text.returncode, 0, quiet_text.stderr)
            self.assertEqual(quiet_text.stdout, "")

    def test_explicit_delivery_answers_even_when_snapshot_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            initial = render_json(mission_dir, "--delivery", "automatic")
            update = render_json(mission_dir, "--delivery", "explicit", "--cursor", initial["cursor"])

            self.assertFalse(update["changed"])
            self.assertEqual(update["update_kind"], "brief")
            self.assertEqual(update["quiet_streak"], 0)
            self.assertIn("暂无新的可验证变化", update["text"])
            self.assertIn("Render readable progress summary", update["text"])

    def test_evidence_or_mission_change_resets_automatic_quiet_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            initial = render_json(mission_dir, "--delivery", "automatic")
            quiet = render_json(mission_dir, "--delivery", "automatic", "--cursor", initial["cursor"])
            self.assertEqual(quiet["quiet_streak"], 1)

            evidence = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "key_finding",
                "--task-id",
                "T1",
                "--summary",
                "Verified a new user-visible result.",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            changed = render_json(mission_dir, "--delivery", "automatic", "--cursor", quiet["cursor"])

            self.assertTrue(changed["changed"])
            self.assertEqual(changed["update_kind"], "full")
            self.assertEqual(changed["quiet_streak"], 0)
            self.assertIn("Verified a new user-visible result.", changed["text"])

    def test_constraints_and_facts_are_not_rendered_as_countable_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            blocker = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "blocker",
                "--task-id",
                "T1",
                "--summary",
                "Target host is unavailable.",
            )
            finding = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "key_finding",
                "--task-id",
                "T1",
                "--summary",
                "The host uses a different hook carrier.",
            )
            self.assertEqual(blocker.returncode, 0, blocker.stderr)
            self.assertEqual(finding.returncode, 0, finding.stderr)

            output = run_script("render_user_update.py", str(mission_dir)).stdout
            self.assertIn("关键约束：", output)
            self.assertIn("Target host is unavailable.", output)
            self.assertIn("已确认事实：", output)
            self.assertIn("The host uses a different hook carrier.", output)

    def test_task_local_log_does_not_claim_a_user_visible_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            initial = render_json(mission_dir, "--delivery", "automatic")
            log = run_script(
                "checkpoint.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--log-summary",
                "Ran a local inspection without a verified result.",
            )
            self.assertEqual(log.returncode, 0, log.stderr)
            update = render_json(mission_dir, "--delivery", "automatic", "--cursor", initial["cursor"])

            self.assertFalse(update["changed"])
            self.assertEqual(update["update_kind"], "quiet")
            self.assertEqual(update["quiet_streak"], 1)

    def test_mission_state_change_cannot_be_silenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            initial = render_json(mission_dir, "--delivery", "automatic")
            transition = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "completed")
            self.assertEqual(transition.returncode, 0, transition.stderr)

            update = render_json(mission_dir, "--delivery", "automatic", "--cursor", initial["cursor"])

            self.assertTrue(update["changed"])
            self.assertEqual(update["update_kind"], "full")
            self.assertEqual(update["quiet_streak"], 0)

    def test_stop_blocker_and_requires_human_state_cannot_be_silenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            initial = render_json(mission_dir, "--delivery", "automatic")
            stop = run_script(
                "stop_report.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "Need a human authority decision before continuing.",
                "--current-goal",
                "Keep the Mission safe.",
                "--attempt",
                "Inspected the current state.",
                "--blocking-issue",
                "Authority is required.",
                "--why-cannot-continue-safely",
                "The next mutation needs confirmation.",
                "--need-from-human",
                "Confirm the next direction.",
                "--resume-condition",
                "The authority decision is recorded.",
            )
            self.assertEqual(stop.returncode, 0, stop.stderr)

            update = render_json(mission_dir, "--delivery", "automatic", "--cursor", initial["cursor"])

            self.assertTrue(update["changed"])
            self.assertEqual(update["update_kind"], "full")
            self.assertIn("Need a human authority decision before continuing.", update["text"])

    def test_interaction_guard_open_and_close_cannot_be_silenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            initial = render_json(mission_dir, "--delivery", "automatic")
            opened = run_script(
                "interaction_guard.py",
                "begin",
                str(mission_dir),
                "--platform",
                "test-host",
                "--message-ref",
                "M1",
            )
            self.assertEqual(opened.returncode, 0, opened.stderr)
            guard = json.loads(opened.stdout)

            guard_open = render_json(mission_dir, "--delivery", "automatic", "--cursor", initial["cursor"])
            self.assertTrue(guard_open["changed"])
            self.assertEqual(guard_open["update_kind"], "full")
            self.assertIn("写保护已开启", guard_open["text"])
            self.assertIn("修订 1", guard_open["text"])

            awaiting = run_script(
                "interaction_guard.py",
                "await",
                str(mission_dir),
                "--guard-id",
                guard["guard_id"],
                "--expected-revision",
                str(guard["revision"]),
                "--message-ref",
                "M1",
            )
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr)
            awaiting_guard = json.loads(awaiting.stdout)
            guard_awaiting = render_json(mission_dir, "--delivery", "automatic", "--cursor", guard_open["cursor"])
            self.assertTrue(guard_awaiting["changed"])
            self.assertEqual(guard_awaiting["update_kind"], "full")
            self.assertIn("等待授权确认", guard_awaiting["text"])
            self.assertIn(f"修订 {awaiting_guard['revision']}", guard_awaiting["text"])

            closed = run_script(
                "interaction_guard.py",
                "resume",
                str(mission_dir),
                "--guard-id",
                guard["guard_id"],
                "--expected-revision",
                str(awaiting_guard["revision"]),
                "--message-ref",
                "M1",
            )
            self.assertEqual(closed.returncode, 0, closed.stderr)
            guard_closed = render_json(mission_dir, "--delivery", "automatic", "--cursor", guard_awaiting["cursor"])
            self.assertTrue(guard_closed["changed"])
            self.assertEqual(guard_closed["update_kind"], "full")
            self.assertIn("交互保护：已解除", guard_closed["text"])

    def test_invalid_or_cross_mission_cursor_never_becomes_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            invalid = run_script(
                "render_user_update.py",
                str(mission_dir),
                "--delivery",
                "automatic",
                "--cursor",
                "not-a-valid-cursor",
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("cursor", invalid.stderr)

            other_dir = create_lite_mission(Path(tmp) / "other")
            cursor = render_json(mission_dir, "--delivery", "automatic")["cursor"]
            cross = run_script(
                "render_user_update.py",
                str(other_dir),
                "--delivery",
                "automatic",
                "--cursor",
                cursor,
            )
            self.assertNotEqual(cross.returncode, 0)
            self.assertIn("different mission", cross.stderr)

    def test_renderer_refuses_pending_transaction_without_recovering_or_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            transaction_path = create_pending_transaction(mission_dir)
            watched = [
                mission_dir / "mission.json",
                mission_dir / "mission.md",
                mission_dir / "evidence.jsonl",
                mission_dir / "execution_trace.jsonl",
                transaction_path,
            ]
            before = {path: path.read_bytes() for path in watched}

            result = run_script("render_user_update.py", str(mission_dir), "--delivery", "automatic")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pending Mission transaction", result.stderr)
            self.assertEqual({path: path.read_bytes() for path in watched}, before)


if __name__ == "__main__":
    unittest.main()
