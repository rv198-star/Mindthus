import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.tplan.mission_health_pulse_experiment import run_report


REPO = Path(__file__).resolve().parents[2]
SIMULATOR = REPO / "tests" / "tplan" / "mission_health_pulse_experiment.py"


class MissionHealthPulseExperimentTests(unittest.TestCase):
    def test_multi_scenario_experiment_routes_to_existing_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_report(REPO, Path(tmp))

        self.assertEqual(report["runtime_profile"], "mission_health_pulse_documented")
        self.assertTrue(report["surface"]["present"])
        self.assertEqual(report["scenario_count"], 6)
        self.assertEqual(report["scenario_pass_count"], 6)
        self.assertEqual(report["mechanical_score"], report["max_mechanical_score"])
        self.assertTrue(report["development_gate"]["ready_for_runtime_development"])

        scenarios = {scenario["id"]: scenario for scenario in report["scenarios"]}
        self.assertEqual(
            set(scenarios),
            {
                "routine_checkpoint",
                "same_path_continue",
                "repeated_local_repair",
                "shared_risk",
                "branch_cleanup",
                "mission_drift_or_authority_gap",
            },
        )
        self.assertEqual(scenarios["routine_checkpoint"]["pulse"]["next_gate"], "continue")
        self.assertFalse(scenarios["routine_checkpoint"]["pulse_invoked"])
        self.assertFalse(scenarios["routine_checkpoint"]["requires_full_review"])
        self.assertEqual(
            scenarios["same_path_continue"]["pulse"]["next_gate"],
            "continuation_authorization",
        )
        self.assertEqual(
            scenarios["repeated_local_repair"]["pulse"]["next_gate"],
            "anti_spiral_audit",
        )
        self.assertEqual(scenarios["shared_risk"]["pulse"]["next_gate"], "health_check")
        self.assertEqual(
            scenarios["shared_risk"]["gate_owner"],
            "shared_risk_mission_health_route",
        )
        self.assertEqual(scenarios["branch_cleanup"]["pulse"]["next_gate"], "selection")
        self.assertEqual(
            scenarios["mission_drift_or_authority_gap"]["pulse"]["next_gate"],
            "mission_review",
        )
        self.assertTrue(scenarios["mission_drift_or_authority_gap"]["requires_full_review"])

        for scenario in report["scenarios"]:
            self.assertTrue(scenario["scenario_passed"])
            self.assertTrue(scenario["invariants"]["pulse_does_not_mutate"])
            self.assertTrue(scenario["invariants"]["pulse_has_no_health_verdict"])
            self.assertTrue(scenario["invariants"]["route_is_existing_gate"])
            self.assertIsInstance(scenario["pre_pulse_failure_mode"], str)
            self.assertGreater(len(scenario["pre_pulse_failure_mode"]), 0)

    def test_cli_writes_simulation_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SIMULATOR),
                    "--source-root",
                    str(REPO),
                    "--output-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report_path = output_dir / "simulation_result.json"
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            stdout_report = json.loads(result.stdout)

        self.assertEqual(report["experiment"], "mission_health_pulse_multi_scenario")
        self.assertEqual(stdout_report["scenario_count"], 6)
        self.assertTrue(report["development_gate"]["ready_for_runtime_development"])


if __name__ == "__main__":
    unittest.main()
