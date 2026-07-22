import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
ADAPTER = SCRIPTS / "codex_interaction_adapter.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tplan_runtime


def run_script(script, *args, env=None):
    return subprocess.run(
        [sys.executable, str(script), *args],
        text=True,
        capture_output=True,
        env=env,
    )


def adapter(*args, env=None):
    result = run_script(ADAPTER, *args, env=env)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Protect original path",
                    "role": "success-critical",
                    "mission_contribution": "Keeps the Mission on its intended path.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2",
                    "title": "Apply confirmed change",
                    "role": "success-critical",
                    "mission_contribution": "Applies a host-confirmed change.",
                    "acceptance_evidence": ["A1"],
                },
            ]
        ),
        encoding="utf-8",
    )
    initialized = run_script(
        SCRIPTS / "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "codex-interaction",
        "--title",
        "Codex Interaction Mission",
        "--objective",
        "Verify host-controlled interruption handling.",
        "--acceptance-evidence",
        "A1:Adapter flow is verified.",
        "--task-json",
        str(tasks),
    )
    if initialized.returncode != 0:
        raise AssertionError(initialized.stderr)
    activated = run_script(SCRIPTS / "transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "active")
    if activated.returncode != 0:
        raise AssertionError(activated.stderr)
    return mission_dir


class CodexInteractionAdapterTests(unittest.TestCase):
    def test_capability_report_does_not_claim_current_desktop_prevention(self):
        capabilities = adapter("capabilities")
        self.assertEqual(capabilities["current_desktop_claim"], "advisory_only")
        self.assertEqual(capabilities["enforcement_level_if_host_wired"], "tplan_api_mutation_prevention")

    def test_read_only_user_message_round_trips_back_to_original_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            opened = adapter("message-arrived", str(mission_dir), "--thread-id", "thread-1", "--message-ref", "M1")
            result = adapter(
                "response-resume-original",
                str(mission_dir),
                "--thread-id",
                "thread-1",
                "--guard-id",
                opened["guard_id"],
                "--expected-revision",
                str(opened["revision"]),
                "--message-ref",
                "M1",
            )
            self.assertEqual(result["resumed_task_id"], "T1")
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["active_task_id"], "T1")
            self.assertFalse((mission_dir / ".interaction-guard.json").exists())

    def test_cross_thread_completion_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            opened = adapter("message-arrived", str(mission_dir), "--thread-id", "thread-A", "--message-ref", "M1")
            rejected = run_script(
                ADAPTER,
                "response-resume-original",
                str(mission_dir),
                "--thread-id",
                "thread-B",
                "--guard-id",
                opened["guard_id"],
                "--expected-revision",
                str(opened["revision"]),
                "--message-ref",
                "M1",
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("thread_id does not match", rejected.stderr)
            self.assertTrue((mission_dir / ".interaction-guard.json").exists())
