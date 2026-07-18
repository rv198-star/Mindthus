import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json"
LOCK_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.lock.json"
PENDING_AUTH_PATH = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.pending.json"
)
ACTIVE_AUTH_PATH = BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.json"
BUILDER_PATH = BETA_ROOT / "runtime" / "build-evaluation-protocol-v0.5.py"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.5.py"
AUTH_BUILDER_PATH = BETA_ROOT / "runtime" / "build-execution-authorization-v0.5.py"
AUTH_VALIDATOR_PATH = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.5.py"
)
RUNNER_PATH = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v05.py"
ISOLATION_PATH = BETA_ROOT / "runtime" / "filesystem_isolation_v05.py"
MATERIALIZER_PATH = BETA_ROOT / "runtime" / "materialize-real-codex-arm-v05.py"
DRY_RUN_PATH = BETA_ROOT / "runtime" / "dry-run-incremental-v05.py"
ANALYZER_PATH = BETA_ROOT / "runtime" / "analyze_incremental_v05.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BetaTwoIncrementalV05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_module("beta2_protocol_v05_builder", BUILDER_PATH)
        cls.validator = load_module("beta2_protocol_v05_validator", VALIDATOR_PATH)
        cls.runner = load_module("beta2_runner_v05", RUNNER_PATH)
        cls.isolation = load_module("beta2_isolation_v05", ISOLATION_PATH)
        cls.materializer = load_module("beta2_materializer_v05", MATERIALIZER_PATH)
        cls.dry_run = load_module("beta2_dry_run_v05", DRY_RUN_PATH)
        cls.analyzer = load_module("beta2_analyzer_v05", ANALYZER_PATH)
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    def test_checked_protocol_matches_builder_except_parent_receipt(self) -> None:
        rebuilt = self.builder.payload()
        rebuilt["freeze"]["source_parent_commit"] = self.protocol["freeze"][
            "source_parent_commit"
        ]
        self.assertEqual(rebuilt, self.protocol)

    def test_protocol_freezes_incremental_evidence_closure(self) -> None:
        report = self.validator.validate_protocol(self.protocol)
        self.assertEqual(report["planned_batches"], 75)
        self.assertEqual(report["planned_generation_cells"], 225)
        self.assertEqual(report["planned_judge_records"], 450)
        design = self.protocol["execution_design"]
        self.assertEqual(
            design["incremental_batch_control"]["order"],
            [
                "generate-three-arms",
                "verify-three-filesystem-isolation-receipts",
                "judge-each-output-in-two-isolated-sessions",
                "write-one-hash-chained-atomic-batch-commit",
                "advance-to-next-batch",
            ],
        )
        self.assertEqual(
            design["filesystem_isolation"]["command_string_as_access_proof"],
            "forbidden",
        )
        self.assertEqual(
            design["v05_prior_output_accounting"]["v04_valid_comparison_records"],
            0,
        )

    def test_batch_plan_judges_each_triplet_before_advancing(self) -> None:
        batches = self.runner.batch_plan(self.protocol, "f" * 64)
        self.assertEqual(len(batches), 75)
        self.assertTrue(all(batch["gate"] == "smoke" for batch in batches[:5]))
        self.assertTrue(all(batch["gate"] == "matched" for batch in batches[5:]))
        units = {(batch["case_id"], batch["repeat"]) for batch in batches}
        self.assertEqual(len(units), 75)
        for batch in batches:
            self.assertEqual(len(batch["cells"]), 3)
            self.assertEqual(
                {cell["arm_id"] for cell in batch["cells"]},
                {"stable", "direct-only", "thin-kernel"},
            )

    def test_filesystem_profile_denies_absolute_parent_and_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir="/Volumes/Data") as tmp:
            root = Path(tmp)
            allowed = root / "allowed"
            forbidden = root / "forbidden"
            allowed.mkdir()
            forbidden.mkdir()
            own = allowed / "own.txt"
            control = forbidden / "control.txt"
            own.write_text("own", encoding="utf-8")
            control.write_text("control", encoding="utf-8")
            receipt = self.isolation.prepare_verified_profile(
                profile_path=allowed / "profile.sb",
                receipt_path=allowed / "receipt.json",
                protected_roots=[root],
                allowed_read_roots=[allowed],
                allowed_write_roots=[allowed],
                allowed_read_files=[],
                probe_root=allowed,
                allowed_targets=[own],
                forbidden_targets=[control],
            )
            self.assertEqual(receipt["status"], "pass")
            self.assertTrue(receipt["negative_probes"][0]["denied"])
            self.assertTrue(receipt["parent_traversal_probe"]["denied"])
            self.assertTrue(receipt["symlink_escape_probe"]["denied"])

    def test_dry_run_keeps_partial_batch_out_and_resumes_hash_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self.dry_run.rehearse(PROTOCOL_PATH, Path(tmp))
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["committed_before_injected_stop"], 5)
        self.assertEqual(report["committed_generation_outputs_before_stop"], 15)
        self.assertEqual(report["committed_judge_records_before_stop"], 30)
        self.assertIsNone(report["partial_batch"]["commit"])
        self.assertEqual(report["committed_after_resume"], 6)
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(report["judge_model_calls"], 0)

    def test_semantic_command_is_prefixed_by_the_verified_native_profile(self) -> None:
        with tempfile.TemporaryDirectory(dir="/Volumes/Data") as tmp:
            root = Path(tmp)
            package = root / "arm" / "installed"
            execution = root / "arm" / "project"
            codex_home = root / "arm" / "codex-home"
            process_home = root / "arm" / "process-home"
            out = root / "run"
            for path in (package, execution, codex_home, process_home, out):
                path.mkdir(parents=True, exist_ok=True)
            (package / "plugin.txt").write_text("plugin", encoding="utf-8")
            forbidden = root / "control.txt"
            forbidden.write_text("control", encoding="utf-8")
            auth = root / "auth.json"
            auth.write_text("{}", encoding="utf-8")
            answer = (
                out
                / "generation-attempts"
                / ("a" * 64)
                / "attempt-01.partial-fixture"
                / "answer.txt"
            )
            answer.parent.mkdir(parents=True)
            manifest = {
                "arm_id": "stable",
                "host": {
                    "home": str(codex_home),
                    "execution_root": str(execution),
                },
                "package": {"root": str(package)},
            }
            self.runner._CONTEXT = {
                "out_dir": str(out),
                "manifests": {"stable": manifest},
                "auth_source": str(auth),
                "protected_roots": [str(root)],
                "forbidden_targets_by_role": {
                    "generation": [str(forbidden)],
                    "judge": [str(forbidden)],
                },
                "applied_receipts": set(),
            }
            captured = {}

            def fake_stream(command, **kwargs):
                captured["command"] = command
                return "capture"

            command = ["codex", "exec", "-o", str(answer), "-"]
            env = {
                "CODEX_HOME": str(codex_home),
                "HOME": str(process_home),
                "PATH": str(Path("/opt/homebrew/bin")),
            }
            with mock.patch.object(
                self.runner, "ORIGINAL_RUN_STREAMED", side_effect=fake_stream
            ):
                result = self.runner._sandboxed_run_streamed(
                    command,
                    input_text="fixture",
                    cwd=execution,
                    env=env,
                    timeout=1,
                )
            self.assertEqual(result, "capture")
            self.assertEqual(captured["command"][:2], ["/usr/bin/sandbox-exec", "-f"])
            receipt = self.runner._receipt_path(
                out, "generation", "a" * 64, 1, None
            )
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertTrue(payload["semantic_process_profile_applied"])
            self.assertEqual(payload["sandboxed_runtime_probe"]["returncode"], 0)

    def test_materializer_removes_builder_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "arm"
            execution = Path(tmp) / "carrier" / "project"
            staging = execution.parent / "package"
            staging.mkdir(parents=True)
            (staging / "secret.txt").write_text("staging", encoding="utf-8")
            args = types.SimpleNamespace(
                root=root,
                execution_root=execution,
                arm_id="stable",
            )
            base_report = {
                "status": "materialized-and-sealed",
                "package_root": str(root / "codex-home" / "installed"),
            }
            with mock.patch.object(
                self.materializer.V04, "materialize", return_value=base_report
            ):
                report = self.materializer.materialize(args)
            self.assertFalse(staging.exists())
            self.assertTrue(report["staging_root_absent"])
            receipt = json.loads(
                Path(report["layout_receipt_path"]).read_text(encoding="utf-8")
            )
            self.assertFalse(receipt["model_execution_performed"])

    def test_partial_analysis_reports_descriptive_means_without_thresholds(self) -> None:
        rows = [
            {
                arm: {
                    "quality": value,
                    "owner": 1.0,
                    "primitive": value,
                    "joint": value,
                    "false_wakeup": 0.0,
                    "input_tokens": 100.0 + value,
                    "wall_time": 10.0 + value,
                    "first_observable": 1.0 + value,
                }
                for arm, value in (
                    ("stable", 0.5),
                    ("direct-only", 0.75),
                    ("thin-kernel", 1.0),
                )
            }
        ]
        report = self.analyzer.descriptive_rows(rows)
        self.assertEqual(report["paired_triplets"], 1)
        self.assertEqual(report["arm_descriptive_means"]["thin-kernel"]["quality"], 1.0)
        self.assertFalse(report["threshold_decisions_available"])

    def test_validator_rejects_batch_isolation_or_prior_accounting_drift(self) -> None:
        mutations = (
            lambda item: item["execution_design"]["incremental_batch_control"].update(
                judge_records_per_batch=0
            ),
            lambda item: item["execution_design"]["filesystem_isolation"].update(
                command_string_as_access_proof="allowed"
            ),
            lambda item: item["execution_design"]["v05_prior_output_accounting"].update(
                v04_valid_comparison_records=143
            ),
            lambda item: item["authorization_parameters"].update(
                delegated_digest_binding_allowed=True
            ),
        )
        for mutate in mutations:
            changed = copy.deepcopy(self.protocol)
            mutate(changed)
            with self.assertRaises(self.validator.ProtocolError):
                self.validator.validate_protocol(changed)

    def test_pending_authorization_validates_shape_but_blocks_execution(self) -> None:
        if not LOCK_PATH.is_file() or not PENDING_AUTH_PATH.is_file():
            self.skipTest("pending authorization is built only after the v0.5 freeze")
        validator = load_module("beta2_auth_validator_v05", AUTH_VALIDATOR_PATH)
        report = validator.validate_authorization(
            PENDING_AUTH_PATH, require_active=False, check_runtime=False
        )
        self.assertEqual(report["status"], "pending")
        with self.assertRaises(validator.AuthorizationError):
            validator.validate_authorization(
                PENDING_AUTH_PATH, require_active=True, check_runtime=False
            )

    def test_active_authorization_binds_only_the_initial_five_batches(self) -> None:
        validator = load_module("beta2_active_auth_validator_v05", AUTH_VALIDATOR_PATH)
        report = validator.validate_authorization(
            ACTIVE_AUTH_PATH, require_active=True, check_runtime=False
        )
        self.assertEqual(report["status"], "authorized")
        self.assertEqual(report["maximum_committed_batches"], 5)
        self.assertEqual(report["maximum_generation_calls"], 17)
        self.assertEqual(report["maximum_judge_calls"], 34)
        self.assertEqual(report["token_budget"]["maximum"], 3_000_000)
        self.assertFalse(report["release_preparation"])

    def test_prior_official_locks_remain_valid(self) -> None:
        for version in ("", "-v0.2", "-v0.3", "-v0.4"):
            validator = BETA_ROOT / "runtime" / f"freeze-evaluation-protocol{version}.py"
            result = subprocess.run(
                ["python3", str(validator), "validate"],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
