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


class TplanDryRunTests(unittest.TestCase):
    def test_build_tplan_l0_dry_run_defends_four_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            mission_dir = tmp_path / "mission"
            tasks = tmp_path / "tasks.json"
            tasks.write_text(
                json.dumps(
                    [
                        {
                            "id": "T1",
                            "title": "Define L0 schema and lifecycle states",
                            "role": "success-critical",
                            "mission_contribution": "Defines runtime state contract.",
                            "acceptance_evidence": ["A1"],
                        },
                        {
                            "id": "T2",
                            "title": "Implement minimal runtime scripts",
                            "role": "success-critical",
                            "mission_contribution": "Makes Mission runtime executable.",
                            "acceptance_evidence": ["A2"],
                        },
                        {
                            "id": "T3",
                            "title": "Write thin SKILL.md and decision hook routing",
                            "role": "success-critical",
                            "mission_contribution": "Connects runtime to Mindthus skills.",
                            "acceptance_evidence": ["A3"],
                        },
                        {
                            "id": "T4",
                            "title": "Run dry-run Mission validation",
                            "role": "success-critical",
                            "mission_contribution": "Proves the four-failure defense.",
                            "acceptance_evidence": ["A4"],
                        },
                        {
                            "id": "T2.1",
                            "parent_id": "T2",
                            "level": 3,
                            "title": "Prototype transition_task.py state edges",
                            "role": "supporting",
                            "mission_contribution": "Supports script implementation without redefining Mission completion.",
                            "acceptance_evidence": [],
                        },
                    ]
                ),
                encoding="utf-8",
            )
            init = run_script(
                "init_mission.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "build-tplan-l0",
                "--title",
                "Build tplan L0",
                "--objective",
                "Build a usable L0 tplan skill for Mindthus.",
                "--acceptance-evidence",
                "A1:Schema and lifecycle are defined.",
                "--acceptance-evidence",
                "A2:Runtime scripts exist and pass tests.",
                "--acceptance-evidence",
                "A3:SKILL.md routes hooks to Mindthus skills.",
                "--acceptance-evidence",
                "A4:Dry run demonstrates the four-failure defense.",
                "--task-json",
                str(tasks),
                "--human-in-loop",
                "0",
                "--risk-tolerance",
                "50",
                "--resource-sufficiency",
                "60",
            )
            self.assertEqual(init.returncode, 0, init.stderr)

            check = run_script("check_mission.py", str(mission_dir))
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

            active = run_script("transition_task.py", str(mission_dir), "--task-id", "T2.1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)

            evidence = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "feedback",
                "--task-id",
                "T2.1",
                "--summary",
                "Local transition design is expanding beyond Mission leverage.",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)

            packet = tmp_path / "subtraction-packet.json"
            make_packet = run_script(
                "make_decision_packet.py",
                str(mission_dir),
                "--hook",
                "subtraction",
                "--output",
                str(packet),
            )
            self.assertEqual(make_packet.returncode, 0, make_packet.stderr)
            packet_data = json.loads(packet.read_text(encoding="utf-8"))
            self.assertEqual([task["id"] for task in packet_data["parent_chain"]], ["T2", "T2.1"])
            self.assertEqual(packet_data["policy"]["resource_sufficiency"], 60)

            decision = tmp_path / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "subtract",
                        "rationale": "Downgrade the deep transition branch to keep Mission progress focused.",
                        "confidence": 75,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "transition_task", "task_id": "T2.1", "status": "paused"},
                            {"type": "set_active_task", "task_id": "T2"},
                        ],
                        "requires_human": False,
                        "mission_alignment": "Pausing T2.1 reduces low-leverage expansion and refocuses on T2 for Mission progress.",
                    }
                ),
                encoding="utf-8",
            )
            applied = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))
            self.assertEqual(applied.returncode, 0, applied.stderr)

            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            statuses = {task["id"]: task["status"] for task in mission["tasks"]}
            self.assertEqual(statuses["T2.1"], "paused")
            self.assertEqual(statuses["T2"], "active")
            self.assertEqual(mission["active_task_id"], "T2")


if __name__ == "__main__":
    unittest.main()
