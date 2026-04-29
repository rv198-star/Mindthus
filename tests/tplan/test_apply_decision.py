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


def create_mission(tmp, human_in_loop):
    mission_dir = Path(tmp) / "mission"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Define runtime schema",
                    "role": "success-critical",
                    "mission_contribution": "Defines schema.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2",
                    "title": "Write runtime scripts",
                    "role": "success-critical",
                    "mission_contribution": "Implements runtime behavior.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2.1",
                    "parent_id": "T2",
                    "level": 3,
                    "title": "Draft CLI arguments",
                    "role": "supporting",
                    "parent_contribution": "Supplies the CLI argument draft needed by T2.",
                    "parent_acceptance": "T2 can implement script parsing from the draft.",
                    "mission_trace": "via T2 -> A1",
                },
            ]
        ),
        encoding="utf-8",
    )
    result = run_script(
        "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "m1",
        "--title",
        "Authority Mission",
        "--objective",
        "Apply or record decisions.",
        "--acceptance-evidence",
        "A1:Runtime exists.",
        "--task-json",
        str(tasks),
        "--human-in-loop",
        str(human_in_loop),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


def write_decision(tmp, recommendation="switch"):
    decision = Path(tmp) / "decision.json"
    decision.write_text(
        json.dumps(
            {
                "recommendation": recommendation,
                "rationale": "Switch to the script task because it blocks runtime usability.",
                "confidence": 80,
                "evidence_links": [],
                "proposed_mutations": [
                    {"type": "set_active_task", "task_id": "T2"}
                ],
                "requires_human": False,
                "mission_alignment": "Switching to T2 advances the runtime task that blocks Mission usability.",
            }
        ),
        encoding="utf-8",
    )
    return decision


class ApplyDecisionTests(unittest.TestCase):
    def test_autonomous_mode_applies_decision_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = write_decision(tmp)
            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("applied_decision", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["active_task_id"], "T2")
            statuses = {task["id"]: task["status"] for task in mission["tasks"]}
            self.assertEqual(statuses["T2"], "active")

    def test_advisory_mode_records_recommendation_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=100)
            decision = write_decision(tmp)
            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("recorded_recommendation", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])
            events = [
                json.loads(line)
                for line in (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(events[-1]["event_type"], "decision_recommendation")

    def test_requires_human_records_recommendation_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "close",
                        "rationale": "Closure is outside delegated authority.",
                        "confidence": 70,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_mission_status", "status": "abandoned"}
                        ],
                        "requires_human": True,
                        "mission_alignment": "Closure affects Mission status and must remain tied to release viability.",
                    }
                ),
                encoding="utf-8",
            )
            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("recorded_recommendation", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["mission"]["status"], "active")

    def test_malformed_mutation_fails_without_traceback_or_partial_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "switch",
                        "rationale": "Malformed mutation should not partially mutate Mission state.",
                        "confidence": 80,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_active_task"},
                        ],
                        "requires_human": False,
                        "mission_alignment": "The proposed switch claims to advance runtime usability.",
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mutation set_active_task missing field: task_id", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])

    def test_reserved_human_in_loop_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            mission_path = mission_dir / "mission.json"
            mission = json.loads(mission_path.read_text(encoding="utf-8"))
            mission["mission"]["human_in_loop"] = 50
            mission_path.write_text(json.dumps(mission), encoding="utf-8")
            decision = write_decision(tmp)

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("human_in_loop must be 0 or 100 in tplan.v0.1", result.stderr)
            mission = json.loads(mission_path.read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])

    def test_missing_mission_alignment_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "switch",
                        "rationale": "Switch without Mission alignment should be rejected.",
                        "confidence": 80,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_active_task", "task_id": "T2"},
                        ],
                        "requires_human": False,
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("decision missing field: mission_alignment", result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])

    def test_child_level_decision_accepts_parent_alignment_without_mission_alignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "continue",
                        "rationale": "The child draft is ready for parent review.",
                        "confidence": 75,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "transition_task", "task_id": "T2.1", "status": "completed"},
                        ],
                        "requires_human": False,
                        "parent_alignment": "Completing T2.1 gives T2 its CLI argument draft.",
                        "mission_trace": "via T2 -> A1",
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("applied_decision", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            statuses = {task["id"]: task["status"] for task in mission["tasks"]}
            self.assertEqual(statuses["T2.1"], "completed")


if __name__ == "__main__":
    unittest.main()
