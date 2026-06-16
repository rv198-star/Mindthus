import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SIMULATOR = REPO / "tests" / "tplan" / "mission_shared_context_agent_simulator.py"


def run_simulator(source_root, output_dir):
    return subprocess.run(
        [
            sys.executable,
            str(SIMULATOR),
            "--source-root",
            str(source_root),
            "--output-dir",
            str(output_dir),
        ],
        text=True,
        capture_output=True,
    )


class MissionSharedContextAgentSimulatorTests(unittest.TestCase):
    def test_new_runtime_preserves_mission_memory_across_interruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "new"

            result = run_simulator(REPO, output_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output_dir / "simulation_result.json").read_text(encoding="utf-8"))
            self.assertEqual(report["runtime_profile"], "mission_shared_context")
            self.assertEqual(report["mechanical_score"], 6)
            self.assertEqual(report["scripted_agent_score"], 6)
            self.assertTrue(report["can_load_mission_memory"])
            self.assertEqual(report["preflight"]["matching_action"], "continue_existing")
            self.assertEqual(report["preflight"]["conflict_action"], "needs_agentic_selection")
            self.assertEqual(report["lineage"]["source_contexts"], ["interrupted-validation"])
            self.assertEqual(report["lineage"]["new_acceptance_evidence"], ["A1"])
            self.assertIn("R1: fsync_unreliable (high, active)", report["shared_context_markdown"])
            self.assertIn("risk_context_update", report["event_types"])

    def test_old_runtime_reports_missing_mission_memory_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "old_source"
            (source_root / "skills" / "tplan" / "scripts").mkdir(parents=True)
            output_dir = Path(tmp) / "old"

            result = run_simulator(source_root, output_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output_dir / "simulation_result.json").read_text(encoding="utf-8"))
            self.assertEqual(report["runtime_profile"], "pre_mission_shared_context")
            self.assertEqual(report["mechanical_score"], 0)
            self.assertEqual(report["scripted_agent_score"], 2)
            self.assertFalse(report["can_load_mission_memory"])
            self.assertIn("preflight_mission.py missing", report["limitations"])
            self.assertIn("project-level Mission shared context unavailable", report["limitations"])


if __name__ == "__main__":
    unittest.main()
