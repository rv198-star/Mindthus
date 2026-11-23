from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills/codex-dispatch/scripts/dispatch_inbox.py"
)


def run_inbox(base_dir: Path, *args: str, cwd=None, env=None):
    cmd = [sys.executable, str(SCRIPT), *args]
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=30,
        env=merged_env,
    )


def put(base_dir: Path, **overrides):
    args = [
        "put",
        "--task", overrides.get("task", "t1"),
        "--base-dir", str(base_dir),
        "--round", overrides.get("round_id", "r1"),
        "--sender", overrides.get("sender", "B"),
        "--event", overrides.get("kind", "delivery"),
        "--revision", overrides.get("revision", "v1"),
        "--recipient", overrides.get("recipient", "session-A"),
    ]
    if overrides.get("summary"):
        args += ["--summary", overrides["summary"]]
    if overrides.get("payload_file"):
        args += ["--payload-file", str(overrides["payload_file"])]
    return run_inbox(base_dir, *args)


def put_key(base_dir: Path, **overrides) -> str:
    return json.loads(put(base_dir, **overrides).stdout)["key"]


class DispatchInboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_put_registers_event_once(self):
        first = put(self.base, sender="实现会话", revision="abc123", summary="请复审")
        self.assertEqual(first.returncode, 0, first.stderr)
        body = json.loads(first.stdout)
        self.assertEqual(body["status"], "registered")
        self.assertIn("实现会话", body["key"])
        self.assertTrue(Path(body["path"]).exists())
        self.assertIn("dispatch-local", body["path"])
        self.assertIn("inbox", body["path"])
        self.assertIn("pending", body["path"])

    def test_put_requires_recipient(self):
        result = run_inbox(
            self.base,
            "put", "--task", "t1", "--base-dir", str(self.base),
            "--round", "r1", "--sender", "B", "--event", "delivery",
            "--revision", "v1",
        )
        self.assertNotEqual(result.returncode, 0)

    def test_duplicate_put_is_noop(self):
        put(self.base)
        second = put(self.base)
        self.assertEqual(json.loads(second.stdout)["status"], "duplicate")
        listing = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--json")
        self.assertEqual(len(json.loads(listing.stdout)["events"]), 1)

    def test_distinct_events_are_separate(self):
        put(self.base, kind="milestone", revision="v1")
        put(self.base, kind="delivery", revision="v1")
        put(self.base, kind="review", revision="v1", sender="C")
        listing = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--json")
        events = json.loads(listing.stdout)["events"]
        self.assertEqual(len(events), 3)
        self.assertEqual({e["_state"] for e in events}, {"pending"})

    def test_done_processes_exactly_once(self):
        key = put_key(self.base, recipient="session-A")
        first = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--processor", "session-A",
        )
        self.assertEqual(json.loads(first.stdout)["status"], "processed")
        second = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--processor", "session-A",
        )
        self.assertEqual(json.loads(second.stdout)["status"], "already_processed")
        pending = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--json")
        self.assertEqual(json.loads(pending.stdout)["events"], [])
        all_events = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--all", "--json")
        self.assertEqual({e["_state"] for e in json.loads(all_events.stdout)["events"]}, {"processed"})

    def test_done_forbidden_for_wrong_session(self):
        """Only the named recipient may dispose an event."""
        key = put_key(self.base, recipient="session-A")
        wrong = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--processor", "session-stranger",
        )
        body = json.loads(wrong.stdout)
        self.assertEqual(body["status"], "forbidden")
        self.assertIn("session-A", body["reason"])
        self.assertNotEqual(wrong.returncode, 0)
        # Event is still pending for the real recipient.
        pending = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--json")
        self.assertEqual(len(json.loads(pending.stdout)["events"]), 1)

    def test_done_force_overrides_recipient_check(self):
        key = put_key(self.base, recipient="session-A")
        forced = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--processor", "operator", "--force",
        )
        self.assertEqual(json.loads(forced.stdout)["status"], "processed")

    def test_done_defaults_processor_to_session_id(self):
        key = put_key(self.base, recipient="session-A")
        env = {"CODEX_SESSION_ID": "session-A"}
        result = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, env=env,
        )
        self.assertEqual(json.loads(result.stdout)["status"], "processed")

    def test_put_after_process_stays_processed(self):
        key = put_key(self.base, recipient="session-A")
        run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--processor", "session-A",
        )
        again = put(self.base, recipient="session-A")
        self.assertEqual(json.loads(again.stdout)["status"], "already_processed")

    def test_done_unknown_key_reports_not_found(self):
        result = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", "missing", "--processor", "session-A",
        )
        self.assertEqual(json.loads(result.stdout)["status"], "not_found")
        self.assertNotEqual(result.returncode, 0)

    # --- takeover / release -------------------------------------------------

    def test_takeover_and_release_session(self):
        """A repo-wide marker records which session the user holds."""
        taken = run_inbox(
            self.base, "takeover", "--task", "t1", "--base-dir", str(self.base),
            "--session", "sess-A", "--note", "用户在手动排障",
        )
        self.assertEqual(taken.returncode, 0, taken.stderr)
        self.assertEqual(json.loads(taken.stdout)["status"], "taken_over")
        marker = self.base / "dispatch-local" / "takeover.json"
        self.assertTrue(marker.exists())
        state = json.loads(marker.read_text())
        self.assertIn("sess-A", state)
        self.assertEqual(state["sess-A"]["note"], "用户在手动排障")
        # Release clears only that session.
        released = run_inbox(
            self.base, "release", "--task", "t1", "--base-dir", str(self.base),
            "--session", "sess-A",
        )
        self.assertEqual(json.loads(released.stdout)["status"], "released")
        self.assertEqual(json.loads(marker.read_text()), {})

    def test_release_without_marker_reports_cleanly(self):
        result = run_inbox(
            self.base, "release", "--task", "t1", "--base-dir", str(self.base),
            "--session", "sess-nobody",
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "not_taken_over")

    def test_list_human_readable(self):
        put(self.base, sender="实现会话", summary="请复审固定提交")
        result = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base))
        self.assertIn("[pending]", result.stdout)
        self.assertIn("实现会话", result.stdout)
        self.assertIn("请复审固定提交", result.stdout)

    def test_git_common_dir_resolution(self):
        repo = self.base / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        result = run_inbox(
            self.base,
            "put", "--task", "t1", "--round", "r1", "--sender", "B",
            "--event", "delivery", "--revision", "v1",
            "--recipient", "session-A", "--cwd", str(repo),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertTrue(
            body["path"].startswith(str((repo / ".git").resolve())),
            body["path"],
        )

    def test_outside_git_requires_base_dir(self):
        not_repo = self.base / "plain"
        not_repo.mkdir()
        result = run_inbox(
            self.base,
            "list", "--task", "t1", "--cwd", str(not_repo),
            cwd=not_repo,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--base-dir", result.stderr)

    def test_invalid_event_kind_rejected(self):
        result = run_inbox(
            self.base,
            "put", "--task", "t1", "--base-dir", str(self.base),
            "--round", "r1", "--sender", "B", "--event", "bogus",
            "--revision", "v1", "--recipient", "session-A",
        )
        self.assertNotEqual(result.returncode, 0)

    def test_payload_file_merged(self):
        payload_file = self.base / "payload.json"
        payload_file.write_text(json.dumps({"pr": "https://x/1", "tests": "12 passed"}))
        key = put_key(self.base, payload_file=payload_file)
        event_path = self.base / "dispatch-local" / "t1" / "inbox" / "pending" / f"{key}.json"
        event = json.loads(event_path.read_text())
        self.assertEqual(event["payload"]["pr"], "https://x/1")

    def test_task_name_safety(self):
        result = run_inbox(
            self.base,
            "put", "--task", "../escape", "--base-dir", str(self.base),
            "--round", "r1", "--sender", "B", "--event", "delivery",
            "--revision", "v1", "--recipient", "session-A",
        )
        self.assertEqual(result.returncode, 2)

    # --- defer / resume ----------------------------------------------------

    def test_defer_marks_event_deferred(self):
        key = put_key(self.base, recipient="session-A")
        result = run_inbox(
            self.base, "defer", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--reason", "等用户拍板",
        )
        self.assertEqual(json.loads(result.stdout)["status"], "deferred")
        listing = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base))
        self.assertIn("DEFERRED", listing.stdout)

    def test_resume_unmarks(self):
        key = put_key(self.base, recipient="session-A")
        run_inbox(self.base, "defer", "--task", "t1", "--base-dir", str(self.base),
                  "--key", key, "--reason", "x")
        result = run_inbox(self.base, "resume", "--task", "t1", "--base-dir", str(self.base),
                           "--key", key)
        self.assertEqual(json.loads(result.stdout)["status"], "resumed")

    # --- obligations ---------------------------------------------------------

    def test_bind_and_discharge_obligation(self):
        bound = run_inbox(
            self.base, "bind", "--task", "t1", "--base-dir", str(self.base),
            "--round", "r1", "--worker", "session-B", "--recipient", "session-A",
        )
        self.assertEqual(bound.returncode, 0, bound.stderr)
        body = json.loads(bound.stdout)
        self.assertEqual(body["status"], "bound")
        key = body["key"]
        # Duplicate bind is a no-op.
        dup = run_inbox(
            self.base, "bind", "--task", "t1", "--base-dir", str(self.base),
            "--round", "r1", "--worker", "session-B", "--recipient", "session-A",
        )
        self.assertEqual(json.loads(dup.stdout)["status"], "duplicate")
        # Obligations list shows it open.
        listing = run_inbox(self.base, "obligations", "--task", "t1",
                            "--base-dir", str(self.base), "--json")
        open_keys = {o["key"] for o in json.loads(listing.stdout)["obligations"]}
        self.assertIn(key, open_keys)
        # Discharge closes it.
        done = run_inbox(self.base, "discharge", "--task", "t1",
                         "--base-dir", str(self.base), "--key", key,
                         "--evidence", "delivery registered")
        self.assertEqual(json.loads(done.stdout)["status"], "discharged")
        listing2 = run_inbox(self.base, "obligations", "--task", "t1",
                             "--base-dir", str(self.base), "--json")
        self.assertEqual(json.loads(listing2.stdout)["obligations"], [])

    def test_discharge_unknown_key(self):
        result = run_inbox(self.base, "discharge", "--task", "t1",
                           "--base-dir", str(self.base), "--key", "nope")
        self.assertEqual(json.loads(result.stdout)["status"], "not_found")


class DispatchInboxConfirmationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _put(self):
        return put_key(self.base, sender="实现会话", revision="v1", recipient="session-A")

    def _confirm(self, key, outcome, evidence="wait_threads snapshot"):
        return run_inbox(
            self.base, "confirm", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--outcome", outcome, "--evidence", evidence,
        )

    def test_confirm_received_records_evidence(self):
        key = self._put()
        result = self._confirm(key, "received", "wait_threads: new turn started, no failure")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(body["status"], "confirmed")
        event_path = self.base / "dispatch-local" / "t1" / "inbox" / "pending" / f"{key}.json"
        event = json.loads(event_path.read_text())
        self.assertEqual(event["confirmation"]["outcome"], "received")
        self.assertIn("wait_threads", event["confirmation"]["evidence"])

    def test_confirm_unexecuted_marks_failed_delivery(self):
        key = self._put()
        result = self._confirm(key, "unexecuted", "target thread status=systemError; turn failed in 4s")
        body = json.loads(result.stdout)
        self.assertEqual(body["status"], "confirmed")
        self.assertEqual(body["outcome"], "unexecuted")
        event_path = self.base / "dispatch-local" / "t1" / "inbox" / "pending" / f"{key}.json"
        self.assertTrue(event_path.exists())

    def test_confirm_unknown_key_not_found(self):
        result = self._confirm("missing", "received")
        self.assertEqual(json.loads(result.stdout)["status"], "not_found")

    def test_confirm_bad_outcome_rejected(self):
        key = self._put()
        result = run_inbox(
            self.base, "confirm", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--outcome", "delivered",
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
