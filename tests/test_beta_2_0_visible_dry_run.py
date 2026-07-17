import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
BUILDER = BETA_ROOT / "runtime" / "build-dry-run-fixture.py"
ORCHESTRATOR = BETA_ROOT / "runtime" / "dry-run-orchestrator.py"
PLAN_SCHEMA = BETA_ROOT / "dry-run-plan-v0.3.schema.json"
NEGATIVE_CATALOG = BETA_ROOT / "fixtures" / "dry-run-negative-cases.json"


class BetaTwoVisibleCaseDryRunTests(unittest.TestCase):
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
                "0.3",
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        if built.returncode != 0:
            raise AssertionError(built.stderr or built.stdout)
        cls.plan_path = Path(json.loads(built.stdout)["plan"])
        cls.plan = json.loads(cls.plan_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture_temp.cleanup()

    def test_v03_plan_is_codex_only_and_binds_its_validator(self) -> None:
        self.assertEqual(self.plan["schema_version"], "mindthus-beta2-dry-run-plan-v0.3")
        self.assertEqual(self.plan["supported_surfaces"], ["codex-plugin"])
        self.assertTrue(self.plan["protocol_validator_path"].endswith("v0.3.py"))
        schema = json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "mindthus-beta2-dry-run-plan-v0.3",
        )

    def test_positive_v03_run_has_24_cells_and_zero_model_calls(self) -> None:
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
            self.assertEqual(report["expected_cell_count"], 24)
            self.assertEqual(report["completed_cell_count"], 24)
            self.assertEqual(report["model_calls"], 0)
            self.assertEqual(report["judge_model_calls"], 0)
            self.assertEqual(report["semantic_model_output_count"], 0)

    def test_all_negative_fixtures_fail_closed(self) -> None:
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
                report = json.loads(result.stdout)
                self.assertEqual(report["veto_id"], fixture["expected_veto"])
                self.assertEqual(report["model_calls"], 0)


if __name__ == "__main__":
    unittest.main()
