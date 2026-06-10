import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SIMULATOR = REPO / "tests" / "tplan" / "shared_risk_agent_simulator.py"


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


class SharedRiskAgentSimulatorTests(unittest.TestCase):
    def test_new_runtime_simulator_forces_risk_adjusted_health_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "new"

            result = run_simulator(REPO, output_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output_dir / "simulation_result.json").read_text(encoding="utf-8"))
            self.assertEqual(report["runtime_profile"], "shared_risk")
            self.assertEqual(report["mechanical_score"], 8)
            self.assertEqual(report["scripted_agent_score"], 10)
            self.assertTrue(report["can_publish_shared_risk"])
            self.assertIn("risk_context_update", report["event_types"])
            self.assertIn("risk_context_recovery", report["event_types"])
            self.assertEqual(
                report["steps"]["apply_missing_risk_assessment"]["stderr"],
                "decision missing field: risk_assessment",
            )
            self.assertEqual(report["risk_assessment"]["next_gate"], "health_check")
            self.assertEqual(report["risk_assessment"]["risk_adjusted_value"], "weak")
            self.assertEqual(report["stop_latency"]["expensive_rerun_attempts_before_gate"], 0)
            self.assertEqual(report["stop_latency"]["steps_until_first_safe_gate"], 1)
            self.assertEqual(report["stop_latency"]["final_allowed_action"], "health_check")
            self.assertEqual(report["stop_latency"]["blocked_action"], "expensive_full_chain_rerun")

    def test_old_runtime_simulator_reports_missing_shared_risk_capability(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "old_source"
            (source_root / "skills" / "tplan" / "scripts").mkdir(parents=True)
            output_dir = Path(tmp) / "old"

            result = run_simulator(source_root, output_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output_dir / "simulation_result.json").read_text(encoding="utf-8"))
            self.assertEqual(report["runtime_profile"], "pre_shared_risk")
            self.assertEqual(report["mechanical_score"], 0)
            self.assertEqual(report["scripted_agent_score"], 4)
            self.assertFalse(report["can_publish_shared_risk"])
            self.assertIn("record_risk_context.py missing", report["limitations"])
            self.assertEqual(report["next_gate"], "health_check")
            self.assertEqual(report["stop_latency"]["expensive_rerun_attempts_before_gate"], 1)
            self.assertEqual(report["stop_latency"]["steps_until_first_safe_gate"], 2)
            self.assertEqual(report["stop_latency"]["final_allowed_action"], "health_check")
            self.assertIsNone(report["stop_latency"]["blocked_action"])


if __name__ == "__main__":
    unittest.main()
