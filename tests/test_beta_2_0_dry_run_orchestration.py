import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
BUILDER = BETA_ROOT / "runtime" / "build-dry-run-fixture.py"
ORCHESTRATOR = BETA_ROOT / "runtime" / "dry-run-orchestrator.py"
PLAN_SCHEMA = BETA_ROOT / "dry-run-plan.schema.json"
CELL_SCHEMA = BETA_ROOT / "dry-run-cell.schema.json"
REPORT_SCHEMA = BETA_ROOT / "dry-run-report.schema.json"
NEGATIVE_CATALOG = BETA_ROOT / "fixtures" / "dry-run-negative-cases.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BetaTwoDryRunOrchestrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_temp = tempfile.TemporaryDirectory()
        cls.fixture_root = Path(cls.fixture_temp.name)
        built = subprocess.run(
            ["python3", str(BUILDER), "--root", str(cls.fixture_root)],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        if built.returncode != 0:
            raise AssertionError(built.stderr or built.stdout)
        cls.plan_path = Path(json.loads(built.stdout)["plan"])
        cls.plan = json.loads(cls.plan_path.read_text(encoding="utf-8"))
        cls.positive_temp = tempfile.TemporaryDirectory()
        cls.positive_out = Path(cls.positive_temp.name)
        run = subprocess.run(
            [
                "python3",
                str(ORCHESTRATOR),
                "--plan",
                str(cls.plan_path),
                "--out-dir",
                str(cls.positive_out),
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        if run.returncode != 0:
            raise AssertionError(run.stderr or run.stdout)
        cls.report = json.loads(run.stdout)
        cls.orchestrator = load_module("beta2_dry_run_orchestrator", ORCHESTRATOR)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.positive_temp.cleanup()
        cls.fixture_temp.cleanup()

    def run_fault(self, fault: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = subprocess.run(
                [
                    "python3",
                    str(ORCHESTRATOR),
                    "--plan",
                    str(self.plan_path),
                    "--out-dir",
                    str(out),
                    "--fault",
                    fault,
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            report = json.loads((out / "dry-run-report.json").read_text(encoding="utf-8"))
        return result, report

    def test_fixture_covers_all_three_arms_on_both_supported_package_shapes(self) -> None:
        manifests = [json.loads(Path(path).read_text(encoding="utf-8")) for path in self.plan["arm_manifests"]]
        observed = {(item["surface"], item["arm_id"]) for item in manifests}
        self.assertEqual(
            observed,
            {
                (surface, arm)
                for surface in ("codex-plugin", "claude-plugin")
                for arm in ("stable", "direct-only", "thin-kernel")
            },
        )
        self.assertTrue(all(item["model"]["id"] == "deterministic-mock" for item in manifests))
        self.assertTrue(all(item["tools"] == ["deterministic-mock"] for item in manifests))

    def test_positive_dry_run_completes_atomic_cells_without_model_calls(self) -> None:
        report = self.report
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["expected_cell_count"], 48)
        self.assertEqual(report["completed_cell_count"], 48)
        self.assertEqual(report["new_cell_count"], 48)
        self.assertEqual(report["skipped_completed_cell_count"], 0)
        self.assertEqual(set(report["arms"]), {"stable", "direct-only", "thin-kernel"})
        self.assertEqual(set(report["surfaces"]), {"codex-plugin", "claude-plugin"})
        self.assertEqual(set(report["lifecycle_paths"]), {"startup", "resume", "clear", "compact"})
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(report["judge_model_calls"], 0)
        self.assertEqual(report["semantic_model_output_count"], 0)
        self.assertEqual(report["semantic_claims_available"], [])
        self.assertEqual(report["release_readiness"], "not-assessed")
        self.assertGreaterEqual(len(report["claims_unavailable_until_real_model_execution"]), 8)
        unsigned = dict(report)
        digest = unsigned.pop("report_digest")
        self.assertEqual(digest, self.orchestrator.canonical_sha256(unsigned))

        cells = sorted((self.positive_out / "cells").glob("*/record.json"))
        judges = sorted((self.positive_out / "judge-records").glob("*/*.json"))
        homes = sorted((self.positive_out / "materialized-homes").glob("*/*/home-receipt.json"))
        self.assertEqual(len(cells), 48)
        self.assertEqual(len(judges), 96)
        self.assertEqual(len(homes), 6)
        self.assertEqual(list(self.positive_out.rglob("*.partial")), [])
        for path in cells:
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(record["telemetry"]["evidence_gate"]["status"], "pass")
            self.assertFalse(record["synthetic_generation"]["model_call_performed"])
            self.assertFalse(record["synthetic_generation"]["semantic_output"])
            self.assertEqual(record["semantic_claims_available"], [])

    def test_materialized_homes_preserve_receipts_and_never_enable_execution(self) -> None:
        receipts = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(
                (self.positive_out / "materialized-homes").glob("*/*/home-receipt.json")
            )
        ]
        self.assertEqual(len({item["arm_digest"] for item in receipts}), 6)
        for receipt in receipts:
            self.assertFalse(receipt["model_execution_allowed"])
            unsigned = dict(receipt)
            observed = unsigned.pop("home_receipt_digest")
            self.assertEqual(observed, self.orchestrator.canonical_sha256(unsigned))
            for item in [*receipt["config_receipts"], *receipt["context_receipts"]]:
                path = Path(item["path"])
                self.assertTrue(path.is_file())
                self.assertEqual(sha256_file(path), item["sha256"])

    def test_judge_inputs_are_arm_blind_and_judge_records_are_plumbing_only(self) -> None:
        forbidden_values = [
            *[json.loads(Path(path).read_text(encoding="utf-8"))["identity_digest"] for path in self.plan["arm_manifests"]],
            *self.plan["arm_manifests"],
        ]
        for path in sorted((self.positive_out / "judge-inputs").glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            serialized = json.dumps(payload, ensure_ascii=False)
            self.assertFalse(payload["contains_arm_label"])
            self.assertFalse(payload["contains_runtime_telemetry"])
            self.assertFalse(payload["contains_generator_path"])
            self.assertFalse(payload["semantic_judgment_allowed"])
            self.assertNotIn("direct-only", serialized)
            self.assertNotIn("thin-kernel", serialized)
            for value in forbidden_values:
                self.assertNotIn(value, serialized)
        for path in sorted((self.positive_out / "judge-records").glob("*/*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "plumbing-only")
            self.assertIsNone(payload["semantic_score"])
            self.assertEqual(payload["provenance"], "deterministic-fixture")
            self.assertFalse(payload["model_call_performed"])

    def test_all_preregistered_negative_fixtures_fire_their_named_veto(self) -> None:
        catalog = json.loads(NEGATIVE_CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["faults"]), 8)
        for fixture in catalog["faults"]:
            with self.subTest(fault=fixture["fault"]):
                result, report = self.run_fault(fixture["fault"])
                self.assertEqual(result.returncode, 2)
                self.assertEqual(report["status"], "vetoed")
                self.assertEqual(report["veto_id"], fixture["expected_veto"])
                self.assertEqual(report["model_calls"], 0)
                self.assertEqual(report["judge_model_calls"], 0)
                self.assertEqual(report["semantic_model_output_count"], 0)

    def test_interrupted_run_resumes_without_overwriting_or_double_counting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            interrupted = subprocess.run(
                [
                    "python3",
                    str(ORCHESTRATOR),
                    "--plan",
                    str(self.plan_path),
                    "--out-dir",
                    str(out),
                    "--interrupt-after",
                    "5",
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(interrupted.returncode, 75)
            first_report = json.loads(interrupted.stdout)
            self.assertEqual(first_report["status"], "interrupted")
            self.assertEqual(first_report["completed_cell_count"], 5)
            completed_paths = sorted((out / "cells").glob("*/record.json"))
            before = {
                str(path): (path.read_bytes(), path.stat().st_mtime_ns) for path in completed_paths
            }

            resumed = subprocess.run(
                [
                    "python3",
                    str(ORCHESTRATOR),
                    "--plan",
                    str(self.plan_path),
                    "--out-dir",
                    str(out),
                    "--resume",
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            final_report = json.loads(resumed.stdout)
            self.assertEqual(final_report["status"], "passed")
            self.assertEqual(final_report["completed_cell_count"], 48)
            self.assertEqual(final_report["new_cell_count"], 43)
            self.assertEqual(final_report["skipped_completed_cell_count"], 5)
            self.assertEqual(len(list((out / "cells").glob("*/record.json"))), 48)
            for path_text, (content, mtime) in before.items():
                path = Path(path_text)
                self.assertEqual(path.read_bytes(), content)
                self.assertEqual(path.stat().st_mtime_ns, mtime)

    def test_resume_fails_closed_if_a_completed_cell_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            interrupted = subprocess.run(
                [
                    "python3",
                    str(ORCHESTRATOR),
                    "--plan",
                    str(self.plan_path),
                    "--out-dir",
                    str(out),
                    "--interrupt-after",
                    "1",
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(interrupted.returncode, 75)
            record_path = next((out / "cells").glob("*/record.json"))
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["arm_digest"] = "0" * 64
            record_path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            resumed = subprocess.run(
                [
                    "python3",
                    str(ORCHESTRATOR),
                    "--plan",
                    str(self.plan_path),
                    "--out-dir",
                    str(out),
                    "--resume",
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(resumed.returncode, 2)
            report = json.loads(resumed.stdout)
            self.assertEqual(report["status"], "vetoed")
            self.assertIn(report["veto_id"], {"protocol-or-arm-drift", "untraceable-or-partial-artifact"})

    def test_dry_run_source_has_no_real_executor_path(self) -> None:
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        self.assertNotIn("codex exec", source)
        self.assertNotIn("claude --", source)
        self.assertNotIn("subprocess.Popen", source)
        self.assertIn("deterministic-mock-only", source)

    def test_plan_cell_and_report_schemas_are_closed_and_versioned(self) -> None:
        expected = {
            PLAN_SCHEMA: "mindthus-beta2-dry-run-plan-v0.1",
            CELL_SCHEMA: "mindthus-beta2-dry-run-cell-v0.1",
            REPORT_SCHEMA: "mindthus-beta2-dry-run-report-v0.1",
        }
        for path, version in expected.items():
            with self.subTest(path=path.name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(schema["properties"]["schema_version"]["const"], version)


if __name__ == "__main__":
    unittest.main()
