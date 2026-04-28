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


class InitMissionTests(unittest.TestCase):
    def test_init_mission_creates_runtime_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            tasks = Path(tmp) / "tasks.json"
            tasks.write_text(
                json.dumps(
                    [
                        {
                            "id": "T1",
                            "title": "Define runtime schema",
                            "role": "success-critical",
                            "mission_contribution": "Defines the contract scripts enforce.",
                            "acceptance_evidence": ["A1"],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "mission-tplan-l0",
                "--title",
                "Build tplan L0",
                "--objective",
                "Build a usable L0 tplan skill for Mindthus.",
                "--acceptance-evidence",
                "A1:Runtime files exist and validate.",
                "--task-json",
                str(tasks),
                "--human-in-loop",
                "0",
                "--risk-tolerance",
                "50",
                "--resource-sufficiency",
                "60",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("initialized_mission:", result.stdout)
            self.assertTrue((mission_dir / "mission.json").exists())
            self.assertTrue((mission_dir / "mission.md").exists())
            self.assertTrue((mission_dir / "evidence.jsonl").exists())
            self.assertTrue((mission_dir / "archive").is_dir())

            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["schema_version"], "tplan.v0.1")
            self.assertEqual(mission["mission"]["human_in_loop"], 0)
            self.assertEqual(mission["mission"]["resource_sufficiency"], 60)
            self.assertEqual(mission["tasks"][0]["parent_id"], None)
            self.assertEqual(mission["tasks"][0]["level"], 2)

    def test_init_mission_rejects_out_of_range_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            result = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "bad",
                "--title",
                "Bad Mission",
                "--objective",
                "Invalid policy input.",
                "--acceptance-evidence",
                "A1:Evidence.",
                "--human-in-loop",
                "101",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("human_in_loop must be between 0 and 100", result.stderr)


if __name__ == "__main__":
    unittest.main()
