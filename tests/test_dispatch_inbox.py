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


def run_inbox(base_dir: Path, *args: str, cwd=None):
    cmd = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=30,
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
    ]
    if overrides.get("summary"):
        args += ["--summary", overrides["summary"]]
    if overrides.get("payload_file"):
        args += ["--payload-file", str(overrides["payload_file"])]
    return run_inbox(base_dir, *args)


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

    def test_duplicate_put_is_noop(self):
        first = put(self.base)
        second = put(self.base)
        self.assertEqual(json.loads(second.stdout)["status"], "duplicate")
        # Same event written twice does not create two pending entries.
        listing = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--json")
        events = json.loads(listing.stdout)["events"]
        self.assertEqual(len(events), 1)

    def test_distinct_events_are_separate(self):
        put(self.base, kind="milestone", revision="v1")
        put(self.base, kind="delivery", revision="v1")
        put(self.base, kind="review", revision="v1", sender="C")
        listing = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--json")
        events = json.loads(listing.stdout)["events"]
        self.assertEqual(len(events), 3)
        states = {e["_state"] for e in events}
        self.assertEqual(states, {"pending"})

    def test_done_processes_exactly_once(self):
        put(self.base)
        key = json.loads(put(self.base).stdout)["key"]
        first = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--processor", "A",
        )
        self.assertEqual(json.loads(first.stdout)["status"], "processed")
        second = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base),
            "--key", key, "--processor", "A",
        )
        self.assertEqual(json.loads(second.stdout)["status"], "already_processed")
        # The event moved to processed and stays visible with --all only.
        pending = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--json")
        self.assertEqual(json.loads(pending.stdout)["events"], [])
        all_events = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base), "--all", "--json")
        states = {e["_state"] for e in json.loads(all_events.stdout)["events"]}
        self.assertEqual(states, {"processed"})

    def test_put_after_process_stays_processed(self):
        put(self.base)
        key = json.loads(put(self.base).stdout)["key"]
        run_inbox(self.base, "done", "--task", "t1", "--base-dir", str(self.base), "--key", key)
        again = put(self.base)
        self.assertEqual(json.loads(again.stdout)["status"], "already_processed")

    def test_done_unknown_key_reports_not_found(self):
        result = run_inbox(
            self.base, "done", "--task", "t1", "--base-dir", str(self.base), "--key", "missing"
        )
        self.assertEqual(json.loads(result.stdout)["status"], "not_found")

    def test_list_human_readable(self):
        put(self.base, sender="实现会话", summary="请复审固定提交")
        result = run_inbox(self.base, "list", "--task", "t1", "--base-dir", str(self.base))
        self.assertIn("[pending]", result.stdout)
        self.assertIn("实现会话", result.stdout)
        self.assertIn("请复审固定提交", result.stdout)

    def test_git_common_dir_resolution(self):
        # In a real git work tree, inbox lands under the common dir.
        repo = self.base / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        result = run_inbox(
            self.base,
            "put", "--task", "t1", "--round", "r1", "--sender", "B",
            "--event", "delivery", "--revision", "v1", "--cwd", str(repo),
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
            "--round", "r1", "--sender", "B", "--event", "bogus", "--revision", "v1",
        )
        self.assertNotEqual(result.returncode, 0)

    def test_payload_file_merged(self):
        payload_file = self.base / "payload.json"
        payload_file.write_text(json.dumps({"pr": "https://x/1", "tests": "12 passed"}))
        result = put(self.base, payload_file=payload_file)
        self.assertEqual(result.returncode, 0, result.stderr)
        key = json.loads(result.stdout)["key"]
        event_path = self.base / "dispatch-local" / "t1" / "inbox" / "pending" / f"{key}.json"
        event = json.loads(event_path.read_text())
        self.assertEqual(event["payload"]["pr"], "https://x/1")

    def test_task_name_safety(self):
        result = run_inbox(
            self.base,
            "put", "--task", "../escape", "--base-dir", str(self.base),
            "--round", "r1", "--sender", "B", "--event", "delivery", "--revision", "v1",
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()

class DispatchInboxConfirmationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _put(self):
        result = put(self.base, sender="实现会话", revision="v1")
        return json.loads(result.stdout)["key"]

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
        # The send tool reported success but the target session errored — the
        # event must not count as delivered.
        key = self._put()
        result = self._confirm(key, "unexecuted", "target thread status=systemError; turn failed in 4s")
        body = json.loads(result.stdout)
        self.assertEqual(body["status"], "confirmed")
        self.assertEqual(body["outcome"], "unexecuted")
        # The event stays pending for A-side collection rather than being
        # silently counted as delivered.
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
