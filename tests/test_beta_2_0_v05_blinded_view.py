import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-blinded-view.1.json"
)
LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-blinded-view.1.lock.json"
)
PENDING_AUTHORIZATION = (
    BETA_ROOT
    / "authorizations"
    / "issue-119-codex-v0.5-blinded-view.1.pending.json"
)
RUNNER = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v05_blinded_view.py"
ANALYZER = BETA_ROOT / "runtime" / "analyze_incremental_v05_blinded_view.py"
FREEZER = BETA_ROOT / "runtime" / "freeze-evaluation-blinded-view-v0.5.py"
AUTH_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.5-blinded-view.py"
)
SOURCE_ROOT = (
    REPO
    / ".tplan"
    / "missions"
    / "mindthus-beta2-evaluation"
    / "artifacts"
    / "real-v05-smoke-f9bc7232"
)
SOURCE_RUN = SOURCE_ROOT / "run"
MANIFESTS = (
    SOURCE_ROOT / "arms" / "stable" / "sealed-arm.json",
    SOURCE_ROOT / "arms" / "direct-only-r2" / "sealed-arm.json",
    SOURCE_ROOT / "arms" / "thin-kernel" / "sealed-arm.json",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BetaTwoV05BlindedViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module("beta2_v05_blinded_runner", RUNNER)
        cls.analyzer = load_module("beta2_v05_blinded_analyzer", ANALYZER)
        cls.freezer = load_module("beta2_v05_blinded_freezer", FREEZER)
        cls.auth_validator = load_module(
            "beta2_v05_blinded_auth_validator", AUTH_VALIDATOR
        )
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def _activate_fixture(self, out: Path, original: str):
        answer = out / "answer.txt"
        answer.write_text(original, encoding="utf-8")
        record = {
            "cell_id": "c" * 64,
            "answer_path": str(answer),
            "answer_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
        }
        self.runner._ACTIVE_OUT_DIR = out
        self.runner._ACTIVE_AMENDMENT = self.protocol
        return record

    def _deactivate_fixture(self):
        self.runner._ACTIVE_OUT_DIR = None
        self.runner._ACTIVE_AMENDMENT = None
        self.runner._ORIGINAL_WRITE_BLINDED_INPUT = None
        self.runner._ORIGINAL_JUDGE_PROMPT = None

    def test_current_source_scan_finds_only_the_namespace_exposure(self) -> None:
        source = self.runner.validate_source_snapshot(
            self.protocol["retained_source_run"]
        )
        scan = source["identifier_exposure_scan"]
        self.assertEqual(scan["exposed_outputs"], 1)
        self.assertEqual(scan["exact_sensitive_path_exposures"], 0)
        self.assertEqual(
            scan["items"][0]["cell_id"],
            "11b0c13b639611727b8cfa425feb29263d90d7e7e1e1e332ac4937a82e8fd64b",
        )
        self.assertEqual(
            scan["items"][0]["transformations"][0]["kind"],
            "namespace-prefix",
        )

    def test_candidate_view_preserves_owner_and_original_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            original = "主导 owner：mindthus-beta:3l5s。"
            record = self._activate_fixture(out, original)
            try:
                with mock.patch.object(
                    self.runner, "_cell_for_output", return_value=record
                ):
                    blinded = self.runner.candidate_view(
                        out_dir=out, output_id="o" * 64, original=original
                    )
                self.assertEqual(blinded, "主导 owner：3l5s。")
                self.assertEqual(
                    Path(record["answer_path"]).read_text(encoding="utf-8"), original
                )
                receipt = (
                    out
                    / "recovery"
                    / "0.5-blinded-view.1"
                    / "candidate-views"
                    / f"{'o' * 64}.json"
                )
                self.assertTrue(receipt.is_file())
                self.assertFalse(json.loads(receipt.read_text())["original_answer_mutated"])
            finally:
                self._deactivate_fixture()

    def test_identity_candidate_view_creates_no_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            original = "Owner 3l5s should handle the problem directly."
            record = self._activate_fixture(out, original)
            try:
                with mock.patch.object(
                    self.runner, "_cell_for_output", return_value=record
                ):
                    self.assertEqual(
                        self.runner.candidate_view(
                            out_dir=out, output_id="i" * 64, original=original
                        ),
                        original,
                    )
                self.assertFalse(
                    (out / "recovery" / "0.5-blinded-view.1" / "candidate-views").exists()
                )
            finally:
                self._deactivate_fixture()

    def test_exact_sensitive_path_remains_a_terminal_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            sensitive = self.protocol["blinded_candidate_view"]["sensitive_paths"][0]
            original = f"Read {sensitive}"
            record = self._activate_fixture(out, original)
            try:
                with mock.patch.object(
                    self.runner, "_cell_for_output", return_value=record
                ), self.assertRaises(self.runner.BlindedViewStop) as raised:
                    self.runner.candidate_view(
                        out_dir=out, output_id="p" * 64, original=original
                    )
                self.assertEqual(
                    raised.exception.veto_id, "judge-environment-contamination"
                )
            finally:
                self._deactivate_fixture()

    def test_both_judge_interfaces_receive_the_same_transformed_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            original = "owner mindthus-beta:wae"
            record = self._activate_fixture(out, original)
            seen = []

            def input_writer(**kwargs):
                seen.append(("input", kwargs["candidate"]))
                return out / "judge-input.json"

            def prompt_writer(**kwargs):
                seen.append(("prompt", kwargs["candidate"]))
                return kwargs["candidate"]

            self.runner._ORIGINAL_WRITE_BLINDED_INPUT = input_writer
            self.runner._ORIGINAL_JUDGE_PROMPT = prompt_writer
            try:
                with mock.patch.object(
                    self.runner, "_cell_for_output", return_value=record
                ):
                    self.runner._patched_write_blinded_input(
                        out_dir=out,
                        output_id="j" * 64,
                        prompt="fixture",
                        case={},
                        candidate=original,
                    )
                    prompt = self.runner._patched_judge_prompt(
                        rubric={},
                        case={},
                        prompt="fixture",
                        candidate=original,
                        blinded_output_id="j" * 64,
                    )
                self.assertEqual(prompt, "owner wae")
                self.assertEqual(seen, [("input", "owner wae"), ("prompt", "owner wae")])
            finally:
                self._deactivate_fixture()

    def test_recovery_wrapper_installs_and_restores_only_the_view_adapters(self) -> None:
        original_label = self.runner.V04.FORBIDDEN_BLINDING_LABEL
        original_input = self.runner.V04.write_blinded_input
        original_prompt = self.runner.V04.judge_prompt
        original_analyzer = self.runner.BASE.ANALYZER_V05

        def inspect_wiring(_args):
            self.assertIs(
                self.runner.V04.write_blinded_input,
                self.runner._patched_write_blinded_input,
            )
            self.assertIs(self.runner.V04.judge_prompt, self.runner._patched_judge_prompt)
            self.assertEqual(self.runner.BASE.ANALYZER_V05, self.runner.ANALYZER)
            self.assertIsNone(
                self.runner.V04.FORBIDDEN_BLINDING_LABEL.search("mindthus-beta:")
            )
            return {"status": "fixture"}, 0

        authorization = json.loads(PENDING_AUTHORIZATION.read_text(encoding="utf-8"))
        with mock.patch.object(
            self.runner,
            "_authorization_context",
            return_value=(
                {
                    "status": "authorized",
                    "protocol_sha256": self.protocol["base_binding"][
                        "protocol_sha256"
                    ],
                    "authorization_digest": "a" * 64,
                },
                authorization,
            ),
        ), mock.patch.object(
            self.runner, "validate_source_snapshot"
        ), mock.patch.object(
            self.runner.V04,
            "observed_attempt_usage",
            return_value=(6, 10, 274_864),
        ), mock.patch.object(
            self.runner.COMPAT, "run_recovery", side_effect=inspect_wiring
        ), mock.patch.object(
            self.runner.V04, "write_atomic_json"
        ):
            report, code = self.runner.run_recovery(
                argparse.Namespace(
                    authorization=PENDING_AUTHORIZATION,
                    out_dir=SOURCE_RUN,
                )
            )
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "fixture")
        self.assertIs(self.runner.V04.FORBIDDEN_BLINDING_LABEL, original_label)
        self.assertIs(self.runner.V04.write_blinded_input, original_input)
        self.assertIs(self.runner.V04.judge_prompt, original_prompt)
        self.assertEqual(self.runner.BASE.ANALYZER_V05, original_analyzer)

    def test_frozen_protocol_and_lock_validate_without_budget_expansion(self) -> None:
        report = self.freezer.validate_lock(PROTOCOL, self.protocol, LOCK)
        self.assertEqual(report["status"], "frozen")
        self.assertEqual(report["remaining_judge_calls"], 24)
        self.assertFalse(report["budget_expansion"])
        self.assertFalse(report["model_execution_performed"])

    def test_pending_authorization_validates_without_runtime_or_model(self) -> None:
        report = self.auth_validator.validate_authorization(
            PENDING_AUTHORIZATION, require_active=False, check_runtime=False
        )
        self.assertEqual(report["status"], "pending")
        self.assertEqual(report["remaining_generation_calls"], 11)
        self.assertEqual(report["remaining_judge_calls"], 24)
        self.assertFalse(report["release_preparation"])

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "retained v0.5 source run is unavailable")
    def test_real_pending_preflight_executes_no_model(self) -> None:
        args = argparse.Namespace(
            authorization=PENDING_AUTHORIZATION,
            arm_manifest=list(MANIFESTS),
            out_dir=SOURCE_RUN,
            runtime_root=BETA_ROOT / "runtime",
            auth_source=Path.home() / ".codex" / "auth.json",
            timeout=1800,
            preflight_only=True,
        )
        with mock.patch.object(self.runner.V04, "run_streamed") as semantic_call:
            report, code = self.runner.preflight(args)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "pending-authorization")
        self.assertFalse(report["model_execution_performed"])
        semantic_call.assert_not_called()

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "retained v0.5 source run is unavailable")
    def test_existing_committed_batch_reconstructs_three_identity_views(self) -> None:
        with mock.patch.object(
            self.analyzer.RUNNER,
            "_authorization_context",
            return_value=(
                {
                    "status": "authorized",
                    "protocol_sha256": self.protocol["base_binding"][
                        "protocol_sha256"
                    ],
                },
                {},
            ),
        ):
            report = self.analyzer.validate_candidate_views(
                SOURCE_RUN, PENDING_AUTHORIZATION
            )
        self.assertEqual(report["committed_batches_validated"], 1)
        self.assertEqual(report["committed_candidate_views_validated"], 3)
        self.assertEqual(report["identity_candidate_views"], 3)
        self.assertEqual(report["transformed_candidate_views"], 0)


if __name__ == "__main__":
    unittest.main()
