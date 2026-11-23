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


def inbox(repo: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(INBOX), *args, "--cwd", str(repo)],
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

    def _event(self, session_id="sess-A", **overrides):
        event = {
            "session_id": session_id,
            "cwd": str(self.repo),
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": None,
        }
        event.update(overrides)
        return event

    def _bind(self, worker="sess-B", recipient="sess-A", round_id="r1", task="t1"):
        return inbox(
            self.repo, "bind", "--task", task, "--round", round_id,
            "--worker", worker, "--recipient", recipient,
        )

    def _put(self, sender="sess-B", recipient="sess-A", kind="delivery",
             round_id="r1", revision="v1", task="t1"):
        return inbox(
            self.repo, "put", "--task", task, "--round", round_id,
            "--sender", sender, "--event", kind, "--revision", revision,
            "--recipient", recipient,
        )

    def test_writes_liveness_timestamp(self):
        result = run_hook(self._event())
        self.assertEqual(result.returncode, 0)
        path = liveness_path(self.repo)
        self.assertTrue(path.exists())
        record = json.loads(path.read_text())
        self.assertEqual(record["session_id"], "sess-A")
        self.assertIn("ran_at", record)

    # --- Coordinator check: only the named recipient is interrupted ---------

    def test_pending_event_blocks_only_its_recipient(self):
        """Reproduction of the R1 bug: an event addressed to sess-A blocks A,
        not an unrelated session ending its turn in the same repo."""
        self._put(recipient="sess-A")
        # Recipient is reminded.
        result_a = run_hook(self._event(session_id="sess-A"))
        self.assertEqual(json.loads(result_a.stdout)["decision"], "block")
        self.assertIn("收件箱", json.loads(result_a.stdout)["reason"])
        # An unrelated session in the same repo is NOT reminded.
        result_other = run_hook(self._event(session_id="sess-unrelated"))
        self.assertEqual(result_other.stdout.strip(), "{}")

    def test_deferred_event_does_not_block(self):
        put_result = self._put(recipient="sess-A")
        key = json.loads(put_result.stdout)["key"]
        inbox(self.repo, "defer", "--task", "t1", "--key", key,
              "--reason", "等用户决定")
        result = run_hook(self._event(session_id="sess-A"))
        self.assertEqual(result.stdout.strip(), "{}")

    def test_processed_event_does_not_block(self):
        put_result = self._put(recipient="sess-A")
        key = json.loads(put_result.stdout)["key"]
        inbox(self.repo, "done", "--task", "t1", "--key", key,
              "--processor", "sess-A")
        result = run_hook(self._event(session_id="sess-A"))
        self.assertEqual(result.stdout.strip(), "{}")

    # --- Worker check: open obligation, deterministic ------------------------

    def test_open_obligation_reminds_only_its_worker(self):
        """A worker with an open obligation and no matching inbox event is
        reminded once — regardless of what its closing message said."""
        self._bind(worker="sess-B", recipient="sess-A")
        # The worker is reminded even when its message contains no markers.
        result_b = run_hook(
            self._event(session_id="sess-B", last_assistant_message="随便聊聊")
        )
        out = json.loads(result_b.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("义务", out["reason"])
        # An unrelated session is not reminded.
        result_other = run_hook(self._event(session_id="sess-other"))
        self.assertEqual(result_other.stdout.strip(), "{}")

    def test_obligation_closed_by_delivery_event(self):
        """Registering a delivery for the round satisfies the obligation."""
        self._bind(worker="sess-B", recipient="sess-A")
        self._put(kind="delivery", recipient="sess-A")
        result = run_hook(self._event(session_id="sess-B"))
        self.assertEqual(result.stdout.strip(), "{}")

    def test_obligation_closed_by_blocker_event(self):
        """A blocker event also satisfies the obligation."""
        self._bind(worker="sess-B", recipient="sess-A")
        self._put(kind="blocker", recipient="sess-A")
        result = run_hook(self._event(session_id="sess-B"))
        self.assertEqual(result.stdout.strip(), "{}")

    def test_obligation_in_other_round_still_owes(self):
        """An obligation for r2 is not satisfied by r1's delivery."""
        self._bind(worker="sess-B", recipient="sess-A", round_id="r2")
        self._put(kind="delivery", round_id="r1", recipient="sess-A")
        result = run_hook(self._event(session_id="sess-B"))
        self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_discharged_obligation_not_reminded(self):
        bound = self._bind(worker="sess-B", recipient="sess-A")
        key = json.loads(bound.stdout)["key"]
        inbox(self.repo, "discharge", "--task", "t1", "--key", key)
        result = run_hook(self._event(session_id="sess-B"))
        self.assertEqual(result.stdout.strip(), "{}")

    # --- General gates --------------------------------------------------------

    def test_stop_hook_active_lets_turn_end(self):
        self._put(recipient="sess-A")
        self._bind(worker="sess-B", recipient="sess-A")
        result = run_hook(self._event(session_id="sess-A", stop_hook_active=True))
        self.assertEqual(result.stdout.strip(), "{}")
        result2 = run_hook(self._event(session_id="sess-B", stop_hook_active=True))
        self.assertEqual(result2.stdout.strip(), "{}")

    def test_repo_without_dispatch_tree_is_ignored(self):
        result = run_hook(self._event(session_id="sess-x",
                                      last_assistant_message="随便聊聊"))
        self.assertEqual(result.stdout.strip(), "{}")

    def test_non_git_cwd_is_ignored(self):
        result = run_hook(self._event(session_id="sess-x", cwd=str(self.repo.parent)))
        self.assertEqual(result.stdout.strip(), "{}")

    def test_missing_session_id_is_ignored(self):
        event = self._event()
        del event["session_id"]
        result = run_hook(event)
        self.assertEqual(result.stdout.strip(), "{}")

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
