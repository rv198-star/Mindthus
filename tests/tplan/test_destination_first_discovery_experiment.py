import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.tplan.destination_first_discovery_experiment import run_report


REPO = Path(__file__).resolve().parents[2]
SIMULATOR = REPO / "tests" / "tplan" / "destination_first_discovery_experiment.py"
FIXTURE_ROOT = REPO / "tests" / "tplan" / "fixtures" / "issue_109_destination_first"
EXPECTED_RESULT = FIXTURE_ROOT / "expected_result.json"


def result_projection(report):
    return {
        "baseline": {"passed": report["baseline"]["passed"]},
        "core_fixture": {
            "passed": report["core_fixture"]["passed"],
            "frontier": report["core_fixture"]["frontier"],
            "restarted_frontier": report["core_fixture"]["restarted_frontier"],
            "next_gate": report["core_fixture"]["next_gate"],
            "invariant_count": len(report["core_fixture"]["invariants"]),
        },
        "real_mission_replays": [
            {
                "id": replay["id"],
                "vague_region_count": replay["vague_region_count"],
                "current_tplan_can_represent_vague_regions": replay[
                    "current_tplan_can_represent_vague_regions"
                ],
                "beats_eager_materialization": replay["beats_eager_materialization"],
                "unique_value_over_current_tplan": replay["unique_value_over_current_tplan"],
                "observed_missing_additions": replay["comparison"][
                    "current_tplan_correct_use"
                ]["observed_missing_additions"],
            }
            for replay in report["real_mission_replays"]
        ],
        "negative_control": {
            "id": report["negative_control"]["id"],
            "expected_mode": report["negative_control"]["expected_mode"],
            "actual_mode": report["negative_control"]["actual_mode"],
            "passed": report["negative_control"]["passed"],
        },
        "adoption_decision": {
            "recommend_core_runtime_change": report["adoption_decision"][
                "recommend_core_runtime_change"
            ],
            "recommend_task_schema_change": report["adoption_decision"][
                "recommend_task_schema_change"
            ],
            "recommend_new_runtime_node_kind": report["adoption_decision"][
                "recommend_new_runtime_node_kind"
            ],
            "recommended_scope": report["adoption_decision"]["recommended_scope"],
        },
        "evidence_status": report["evidence_status"],
    }


class DestinationFirstDiscoveryExperimentTests(unittest.TestCase):
    def test_fixture_preserves_tplan_control_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_report(REPO, Path(tmp))

        self.assertTrue(report["baseline"]["passed"])
        fixture = report["core_fixture"]
        self.assertTrue(fixture["passed"])
        self.assertEqual(fixture["frontier"], ["T2", "T3"])
        self.assertEqual(fixture["frontier"], fixture["restarted_frontier"])
        self.assertEqual(fixture["next_gate"], "selection")
        self.assertTrue(all(fixture["invariants"].values()))
        self.assertTrue(fixture["invariants"]["fog_never_enters_frontier"])
        self.assertTrue(fixture["invariants"]["fog_does_not_satisfy_completion"])

    def test_real_replays_do_not_prove_unique_runtime_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_report(REPO, Path(tmp))

        replays = {replay["id"]: replay for replay in report["real_mission_replays"]}
        self.assertEqual(
            set(replays),
            {"v5_targeted_stabilization", "issue_31_tvg_value_profiles"},
        )
        self.assertEqual(replays["v5_targeted_stabilization"]["vague_region_count"], 1)
        self.assertTrue(
            replays["v5_targeted_stabilization"]["current_tplan_can_represent_vague_regions"]
        )
        self.assertFalse(replays["v5_targeted_stabilization"]["unique_value_over_current_tplan"])
        self.assertEqual(replays["issue_31_tvg_value_profiles"]["vague_region_count"], 0)
        self.assertEqual(
            replays["issue_31_tvg_value_profiles"]["comparison"]["current_tplan_correct_use"][
                "observed_missing_additions"
            ],
            1,
        )
        self.assertFalse(replays["issue_31_tvg_value_profiles"]["unique_value_over_current_tplan"])
        self.assertEqual(
            report["evidence_status"]["historical_replay_coding"],
            "owner_curated",
        )

        self.assertTrue(report["negative_control"]["passed"])
        decision = report["adoption_decision"]
        self.assertFalse(decision["recommend_core_runtime_change"])
        self.assertFalse(decision["recommend_task_schema_change"])
        self.assertFalse(decision["recommend_new_runtime_node_kind"])
        self.assertEqual(
            decision["recommended_scope"],
            "documentation_pattern_and_prospective_trial_only",
        )

    def test_committed_result_projection_matches_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_report(REPO, Path(tmp))

        expected = json.loads(EXPECTED_RESULT.read_text(encoding="utf-8"))
        self.assertEqual(result_projection(report), expected)

    def test_cli_writes_reproducible_report(self):
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
            file_report = json.loads(report_path.read_text(encoding="utf-8"))
            stdout_report = json.loads(result.stdout)

        self.assertEqual(
            file_report["experiment"], "tplan_destination_first_discovery_issue_109"
        )
        self.assertEqual(
            file_report["core_fixture"]["frontier"],
            stdout_report["core_fixture"]["frontier"],
        )


if __name__ == "__main__":
    unittest.main()
