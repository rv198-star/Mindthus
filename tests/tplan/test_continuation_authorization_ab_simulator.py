import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SIMULATOR = REPO / "tests" / "tplan" / "continuation_authorization_ab_simulator.py"
OLD_BASELINE = "be25f48"


def extract_old_source(target_dir):
    archive = subprocess.run(
        ["git", "archive", "--format=tar", OLD_BASELINE],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
        if sys.version_info >= (3, 12):
            tar.extractall(target_dir, filter="data")
        else:
            tar.extractall(target_dir)


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


class ContinuationAuthorizationABSimulatorTests(unittest.TestCase):
    def test_old_vs_new_runtime_blocks_ungated_expensive_continuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            old_source = tmp_dir / "old_source"
            old_output = tmp_dir / "old"
            new_output = tmp_dir / "new"
            old_source.mkdir()
            extract_old_source(old_source)

            old_result = run_simulator(old_source, old_output)
            new_result = run_simulator(REPO, new_output)

            self.assertEqual(old_result.returncode, 0, old_result.stderr)
            self.assertEqual(new_result.returncode, 0, new_result.stderr)
            old_report = json.loads((old_output / "simulation_result.json").read_text(encoding="utf-8"))
            new_report = json.loads((new_output / "simulation_result.json").read_text(encoding="utf-8"))

            self.assertEqual(old_report["runtime_profile"], "pre_continuation_authorization")
            self.assertTrue(old_report["ungated_continue_allowed"])
            self.assertEqual(
                old_report["authorization_latency"]["expensive_same_path_continue_attempts_before_gate"],
                1,
            )
            self.assertEqual(old_report["authorization_latency"]["final_allowed_action"], "continue_same_path")
            self.assertIsNone(old_report["authorization_latency"]["blocked_action"])

            self.assertEqual(new_report["runtime_profile"], "continuation_authorization")
            self.assertFalse(new_report["ungated_continue_allowed"])
            self.assertEqual(new_report["mechanical_score"], 6)
            self.assertEqual(
                new_report["steps"]["apply_missing_continuation_authorization"]["stderr"],
                "decision missing field: continuation_authorization",
            )
            self.assertEqual(
                new_report["authorization_latency"]["expensive_same_path_continue_attempts_before_gate"],
                0,
            )
            self.assertEqual(
                new_report["authorization_latency"]["blocked_action"],
                "expensive_same_path_continue",
            )
            self.assertEqual(
                new_report["authorization_latency"]["final_allowed_action"],
                "targeted_fix",
            )
            self.assertEqual(
                new_report["continuation_authorization"]["authorized_action"],
                "targeted_fix",
            )


if __name__ == "__main__":
    unittest.main()
