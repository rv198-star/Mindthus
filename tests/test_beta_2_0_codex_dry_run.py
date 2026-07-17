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
PLAN_SCHEMA = BETA_ROOT / "dry-run-plan-v0.2.schema.json"
NEGATIVE_CATALOG = BETA_ROOT / "fixtures" / "dry-run-negative-cases.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoCodexOnlyDryRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_temp = tempfile.TemporaryDirectory()
        cls.fixture_root = Path(cls.fixture_temp.name)
        built = subprocess.run(
            [
                "python3",
                str(BUILDER),
                "--root",
                str(cls.fixture_root),
                "--protocol-version",
                "0.2",
            ],
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
        cls.orchestrator = load_module("beta2_codex_dry_run_orchestrator", ORCHESTRATOR)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.positive_temp.cleanup()
        cls.fixture_temp.cleanup()

    def test_plan_binds_v02_protocol_validator_and_exact_codex_arm_set(self) -> None:
        self.assertEqual(self.plan["schema_version"], "mindthus-beta2-dry-run-plan-v0.2")
        self.assertEqual(self.plan["supported_surfaces"], ["codex-plugin"])
        self.assertRegex(self.plan["protocol_validator_sha256"], r"^[0-9a-f]{64}$")
        manifests = [
            json.loads(Path(path).read_text(encoding="utf-8"))
            for path in self.plan["arm_manifests"]
        ]
        self.assertEqual(
            {(item["surface"], item["arm_id"]) for item in manifests},
            {
                ("codex-plugin", "stable"),
                ("codex-plugin", "direct-only"),
                ("codex-plugin", "thin-kernel"),
            },
        )

    def test_positive_codex_dry_run_has_24_cells_and_zero_model_calls(self) -> None:
        self.assertEqual(self.report["status"], "passed")
        self.assertEqual(self.report["expected_cell_count"], 24)
        self.assertEqual(self.report["completed_cell_count"], 24)
        self.assertEqual(self.report["new_cell_count"], 24)
        self.assertEqual(self.report["surfaces"], ["codex-plugin"])
        self.assertEqual(self.report["model_calls"], 0)
        self.assertEqual(self.report["judge_model_calls"], 0)
        self.assertEqual(self.report["semantic_model_output_count"], 0)
        self.assertEqual(len(list((self.positive_out / "cells").glob("*/record.json"))), 24)
        self.assertEqual(len(list((self.positive_out / "judge-records").glob("*/*.json"))), 48)
        self.assertEqual(
            len(list((self.positive_out / "materialized-homes").glob("*/*/home-receipt.json"))),
            3,
        )

    def test_interrupted_codex_run_resumes_without_rewriting_first_five_cells(self) -> None:
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
            self.assertEqual(interrupted.returncode, 75, interrupted.stderr)
            before = {
                str(path): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in sorted((out / "cells").glob("*/record.json"))
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
            report = json.loads(resumed.stdout)
            self.assertEqual(report["completed_cell_count"], 24)
            self.assertEqual(report["new_cell_count"], 19)
            self.assertEqual(report["skipped_completed_cell_count"], 5)
            for path_text, (content, mtime) in before.items():
                path = Path(path_text)
                self.assertEqual(path.read_bytes(), content)
                self.assertEqual(path.stat().st_mtime_ns, mtime)

    def test_all_negative_fixtures_still_fail_closed_for_one_host(self) -> None:
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

    def test_validator_digest_tamper_fires_protocol_drift_veto(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            changed = dict(self.plan)
            changed["protocol_validator_sha256"] = "0" * 64
            changed.pop("plan_digest")
            changed["plan_digest"] = self.orchestrator.canonical_sha256(changed)
            changed_path = root / "plan.json"
            changed_path.write_text(
                json.dumps(changed, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "python3",
                    str(ORCHESTRATOR),
                    "--plan",
                    str(changed_path),
                    "--out-dir",
                    str(root / "out"),
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            self.assertEqual(report["veto_id"], "protocol-or-arm-drift")

    def test_codex_plan_schema_is_closed_and_requires_three_manifests(self) -> None:
        schema = json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "mindthus-beta2-dry-run-plan-v0.2",
        )
        self.assertEqual(schema["properties"]["arm_manifests"]["minItems"], 3)
        self.assertEqual(schema["properties"]["arm_manifests"]["maxItems"], 3)
        self.assertEqual(schema["properties"]["supported_surfaces"]["const"], ["codex-plugin"])

    def test_fixture_built_inside_repository_seals_inherited_root_agents_context(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO) as tmp:
            result = subprocess.run(
                [
                    "python3",
                    str(BUILDER),
                    "--root",
                    tmp,
                    "--protocol-version",
                    "0.2",
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            plan_path = Path(json.loads(result.stdout)["plan"])
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            root_agents = str((REPO / "AGENTS.md").resolve())
            for manifest_path in plan["arm_manifests"]:
                manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
                self.assertIn(root_agents, manifest["ambient_context"]["discovered_agents_files"])
                self.assertIn(
                    root_agents,
                    [item["path"] for item in manifest["ambient_context"]["files"]],
                )


if __name__ == "__main__":
    unittest.main()
