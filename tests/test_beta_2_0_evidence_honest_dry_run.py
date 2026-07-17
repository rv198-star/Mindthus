import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
LOCK_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.lock.json"
BUILDER = BETA_ROOT / "runtime" / "build-dry-run-fixture.py"
ORCHESTRATOR = BETA_ROOT / "runtime" / "dry-run-orchestrator.py"
NEGATIVE_CATALOG = BETA_ROOT / "fixtures" / "dry-run-negative-cases.json"


@unittest.skipUnless(LOCK_PATH.is_file(), "v0.4 dry-run starts only after protocol freeze")
class BetaTwoEvidenceHonestDryRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_temp = tempfile.TemporaryDirectory()
        built = subprocess.run(
            [
                "python3",
                str(BUILDER),
                "--root",
                cls.fixture_temp.name,
                "--protocol-version",
                "0.4",
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        if built.returncode != 0:
            raise AssertionError(built.stderr or built.stdout)
        cls.plan_path = Path(json.loads(built.stdout)["plan"])

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture_temp.cleanup()

    def test_positive_v04_run_uses_observed_timing_without_model_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run(
                [
                    "python3",
                    str(ORCHESTRATOR),
                    "--plan",
                    str(self.plan_path),
                    "--out-dir",
                    tmp,
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(run.stdout)
            self.assertEqual(report["completed_cell_count"], 24)
            self.assertEqual(report["model_calls"], 0)
            record_path = next((Path(tmp) / "cells").glob("*/record.json"))
            record = json.loads(record_path.read_text(encoding="utf-8"))
            measurements = record["telemetry"]["measurements"]
            self.assertEqual(
                measurements["first_observable_action_latency_seconds"]["provenance"],
                "deterministic",
            )
            self.assertEqual(
                measurements["first_useful_action_latency_seconds"]["status"],
                "unavailable",
            )
            thin_record = next(
                json.loads(path.read_text(encoding="utf-8"))
                for path in (Path(tmp) / "cells").glob("*/record.json")
                if json.loads(path.read_text(encoding="utf-8"))["telemetry"]["stratum"][
                    "arm_id"
                ]
                == "thin-kernel"
            )
            hook_receipt = thin_record["telemetry"]["measurements"][
                "arm.hook_observation_receipt"
            ]
            self.assertEqual(hook_receipt["provenance"], "deterministic")
            self.assertRegex(hook_receipt["value"], r"^[0-9a-f]{64}$")

    def test_negative_fixtures_still_fail_closed(self) -> None:
        catalog = json.loads(NEGATIVE_CATALOG.read_text(encoding="utf-8"))
        for fixture in catalog["faults"]:
            with self.subTest(fault=fixture["fault"]), tempfile.TemporaryDirectory() as tmp:
                result = subprocess.run(
                    [
                        "python3",
                        str(ORCHESTRATOR),
                        "--plan",
                        str(self.plan_path),
                        "--out-dir",
                        tmp,
                        "--fault",
                        fixture["fault"],
                    ],
                    cwd=REPO,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    json.loads(result.stdout)["veto_id"], fixture["expected_veto"]
                )


if __name__ == "__main__":
    unittest.main()
