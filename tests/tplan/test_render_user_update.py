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
            self.assertIn("已确认：", output)
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


if __name__ == "__main__":
    unittest.main()
