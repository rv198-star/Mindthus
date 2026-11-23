from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = (
    Path(__file__).resolve().parents[1]
    / "skills/codex-dispatch/scripts/dispatch_stop_hook.py"
)
INBOX = (
    Path(__file__).resolve().parents[1]
    / "skills/codex-dispatch/scripts/dispatch_inbox.py"
)


def run_hook(event: dict):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=30,
    )


def inbox_put(repo: Path, task="t1", sender="B", revision="v1"):
    return subprocess.run(
        [
            sys.executable, str(INBOX), "put",
            "--task", task, "--round", "r1", "--sender", sender,
            "--event", "delivery", "--revision", revision, "--cwd", str(repo),
        ],
        capture_output=True, text=True, timeout=30,
    )


def inbox_done(repo: Path, key: str):
    return subprocess.run(
        [sys.executable, str(INBOX), "done", "--task", "t1",
         "--key", key, "--cwd", str(repo)],
        capture_output=True, text=True, timeout=30,
    )


def liveness_path(repo: Path) -> Path:
    return repo / ".git" / "dispatch-local" / "hook-last-run.json"


class DispatchStopHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _event(self, **overrides):
        event = {
            "session_id": "sess-1",
            "cwd": str(self.repo),
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": "做完了，实现了全部功能",
        }
        event.update(overrides)
        return event

    def test_writes_liveness_timestamp(self):
        result = run_hook(self._event())
        self.assertEqual(result.returncode, 0)
        path = liveness_path(self.repo)
        self.assertTrue(path.exists(), "hook must record that it ran")
        record = json.loads(path.read_text())
        self.assertEqual(record["session_id"], "sess-1")
        self.assertIn("ran_at", record)

    def test_stop_hook_active_lets_turn_end(self):
        # Even with an undelivered worker message, an already-continued turn ends.
        result = run_hook(self._event(stop_hook_active=True))
        self.assertEqual(result.stdout.strip(), "{}")

    def test_pending_inbox_blocks_once_for_coordinator(self):
        inbox_put(self.repo)
        result = run_hook(self._event())
        out = json.loads(result.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("收件箱", out["reason"])
        # A second stop with stop_hook_active true ends normally.
        result2 = run_hook(self._event(stop_hook_active=True))
        self.assertEqual(result2.stdout.strip(), "{}")

    def test_worker_without_delivery_or_blocker_is_reminded(self):
        # The repo takes part in dispatch (dispatch-local exists), and the last
        # assistant message neither reports a delivery nor records a blocker.
        (self.repo / ".git" / "dispatch-local" / "t1" / "inbox" / "pending").mkdir(parents=True)
        result = run_hook(self._event(last_assistant_message="做完了，功能都实现了"))
        out = json.loads(result.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("回发", out["reason"])

    def test_worker_that_delivered_is_let_go(self):
        (self.repo / ".git" / "dispatch-local" / "t1" / "inbox" / "pending").mkdir(parents=True)
        result = run_hook(
            self._event(
                last_assistant_message="实现：101 条已导入并复测通过，请复审版本 a1b2c3d。已回发。"
            )
        )
        self.assertEqual(result.stdout.strip(), "{}")

    def test_worker_with_blocker_note_is_let_go(self):
        (self.repo / ".git" / "dispatch-local" / "t1" / "inbox" / "pending").mkdir(parents=True)
        result = run_hook(
            self._event(last_assistant_message="遇到阻塞：无法连接目标主机，等待用户决定。")
        )
        self.assertEqual(result.stdout.strip(), "{}")

    def test_repo_without_dispatch_tree_is_ignored(self):
        result = run_hook(self._event(last_assistant_message="随便聊聊"))
        self.assertEqual(result.stdout.strip(), "{}")

    def test_non_git_cwd_is_ignored(self):
        result = run_hook(self._event(cwd=str(self.repo.parent)))
        self.assertEqual(result.stdout.strip(), "{}")

    def test_processed_inbox_does_not_block(self):
        put_result = inbox_put(self.repo)
        key = json.loads(put_result.stdout)["key"]
        inbox_done(self.repo, key)
        result = run_hook(self._event())
        # No pending inbox falls through to the worker heuristic: the default
        # test message has no delivery/blocker marker, so it is blocked once.
        out = json.loads(result.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertNotIn("收件箱", out["reason"])

    def test_invalid_stdin_still_outputs_json(self):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not-json",
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.stdout.strip(), "{}")


if __name__ == "__main__":
    unittest.main()
