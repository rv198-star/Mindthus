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
PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.json"
LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.lock.json"
AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-blinded-view.1.json"
)
FREEZER = BETA_ROOT / "runtime" / "freeze-evaluation-blinded-view-v0.4.py"
AUTH_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-blinded-view.py"
)
RUNNER = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v04_blinded_view.py"
ANALYZER = BETA_ROOT / "runtime" / "analyze_codex_evaluation_v04_blinded_view.py"
VIEW = BETA_ROOT / "runtime" / "blinded_candidate_view_v04.py"
SOURCE_RUN = (
    REPO
    / ".tplan"
    / "missions"
    / "mindthus-beta2-evaluation"
    / "artifacts"
    / "real-v04-evaluation-a6e9da7e"
    / "run"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BetaTwoV04BlindedViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.view = load_module("beta2_blinded_view_transform", VIEW)
        cls.freezer = load_module("beta2_blinded_view_freezer", FREEZER)
        cls.analyzer = load_module("beta2_blinded_view_analyzer", ANALYZER)
        cls.runner = load_module("beta2_blinded_view_runner", RUNNER)
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        cls.paths = cls.protocol["blinded_candidate_view"]["sensitive_paths"]

    def test_amendment_preserves_answers_scoring_and_cumulative_budget(self) -> None:
        report = self.freezer.validate_protocol(self.protocol)
        self.assertEqual(report["amendment_id"], "0.4-blinded-view.1")
        self.assertEqual(report["retained_judge_records"], 12)
        config = self.protocol["blinded_candidate_view"]
        self.assertFalse(config["original_answer_mutation_allowed"])
        self.assertFalse(config["generation_retry_for_identifier_exposure_allowed"])
        self.assertTrue(config["semantic_scoring_contract_unchanged"])
        budget = self.protocol["budget_accounting"]
        self.assertEqual(
            budget["amended_measured_token_ceiling"]
            + budget["total_unknown_usage_reserved_tokens"],
            21951744,
        )
        self.assertFalse(budget["budget_expansion"])

    def test_transformation_is_deterministic_blind_and_idempotent(self) -> None:
        original = (
            f"cwd={self.paths[-2]} owner=mindthus-beta:wae; "
            "compare direct-only with a stable arm"
        )
        blinded, trace = self.view.transform_candidate(original, self.paths)
        self.view.assert_blind(blinded, self.paths)
        self.assertEqual(
            blinded,
            "cwd=[blinded evaluation path] owner=wae; compare "
            "[blinded arm] with a [blinded arm]",
        )
        self.assertEqual(sum(item["occurrences"] for item in trace), 4)
        second, second_trace = self.view.transform_candidate(blinded, self.paths)
        self.assertEqual(second, blinded)
        self.assertEqual(second_trace, [])

    def test_receipt_contains_hashes_not_original_identifier_text(self) -> None:
        original = f"workspace {self.paths[-2]} and mindthus-beta:wae"
        blinded, trace = self.view.transform_candidate(original, self.paths)
        receipt = self.view.view_receipt(
            amendment_id="0.4-blinded-view.1",
            output_id="o" * 64,
            cell_id="c" * 64,
            original=original,
            blinded=blinded,
            transformations=trace,
        )
        encoded = json.dumps(receipt, ensure_ascii=False)
        self.assertNotIn(self.paths[-2], encoded)
        self.assertNotIn("mindthus-beta:wae", encoded)
        self.view.validate_view_receipt(receipt, receipt)
        tampered = dict(receipt)
        tampered["blinded_answer_sha256"] = "0" * 64
        with self.assertRaises(self.view.BlindedViewError):
            self.view.validate_view_receipt(tampered, receipt)

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "local retained v0.4 evidence is unavailable")
    def test_three_source_exposures_reproduce_exact_blinded_hashes(self) -> None:
        expected = self.protocol["retained_source_run"]["identifier_exposure_scan"]
        snapshot = (
            SOURCE_RUN
            / "recovery"
            / "0.4-blinded-view.1"
            / "pre-amendment"
            / "receipt.json"
        )
        if snapshot.is_file():
            scan = json.loads(snapshot.read_text(encoding="utf-8"))[
                "identifier_exposure_scan"
            ]
        else:
            scan = self.runner.exposure_scan(SOURCE_RUN, self.protocol)
        self.assertEqual(scan, expected["items"])
        self.assertEqual(self.runner.base.canonical_sha256(scan), expected["exposed_set_digest"])

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "local retained v0.4 evidence is unavailable")
    def test_source_judge_sets_bind_pre_amendment_state(self) -> None:
        source = self.protocol["retained_source_run"]
        snapshot = (
            SOURCE_RUN
            / "recovery"
            / "0.4-blinded-view.1"
            / "pre-amendment"
            / "receipt.json"
        )
        if snapshot.is_file():
            receipt = json.loads(snapshot.read_text(encoding="utf-8"))
            attempts = receipt["judge_attempts"]
            records = receipt["judge_records"]
        else:
            attempts = self.runner.attempt_receipts(SOURCE_RUN)
            records = self.runner.record_receipts(SOURCE_RUN)
        self.assertEqual(len(attempts), 17)
        self.assertEqual(len(records), 12)
        self.assertEqual(
            self.runner.base.canonical_sha256(attempts),
            source["judge_attempt_set_digest"],
        )
        self.assertEqual(
            self.runner.base.canonical_sha256(records),
            source["judge_record_set_digest"],
        )

    def test_writer_and_analyzer_reconstruct_same_non_identity_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            original = f"owner mindthus-beta:wae in {self.paths[-2]}"
            blinded = self.runner.write_candidate_view(
                out_dir=out,
                output_id="o" * 64,
                cell_id="c" * 64,
                original=original,
                sensitive_paths=self.paths,
            )
            reconstructed, receipt_path = self.analyzer.validate_candidate_view(
                run_dir=out,
                output_id="o" * 64,
                cell_id="c" * 64,
                original=original,
                sensitive_paths=self.paths,
            )
            self.assertEqual(reconstructed, blinded)
            self.assertIsNotNone(receipt_path)
            self.assertEqual(original, f"owner mindthus-beta:wae in {self.paths[-2]}")

    def test_identity_view_creates_no_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            original = "No evaluation identifiers are present."
            blinded = self.runner.write_candidate_view(
                out_dir=out,
                output_id="o" * 64,
                cell_id="c" * 64,
                original=original,
                sensitive_paths=self.paths,
            )
            self.assertEqual(blinded, original)
            self.assertFalse((out / "blinded-candidate-views").exists())

    def test_judge_loop_uses_blinded_candidate_without_generation_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            answer = out / "answer.txt"
            answer.write_text(
                f"owner mindthus-beta:wae in {self.paths[-2]}", encoding="utf-8"
            )
            record = {
                "cell_id": "c" * 64,
                "cell_key": {"case_id": "case"},
                "answer_path": str(answer),
            }
            case = {
                "source": {"prompt": "fixture"},
                "contract": {
                    "case_type": "positive",
                    "entry_mode": "owner-direct",
                    "accepted_execution_owners": ["wae"],
                    "expected_primitive_obligations": [],
                    "required_visible_action": None,
                    "stay_asleep_expected": False,
                },
            }
            environment = {
                "execution_root": str(out),
                "environment_digest": "environment",
                "env": {},
            }
            calls = []

            def fake_slot(**kwargs):
                calls.append(kwargs)
                return {"fixture": True}, 1, 5

            with mock.patch.object(
                self.runner.base,
                "judge_environment",
                side_effect=lambda **kwargs: {
                    **environment,
                    "environment_digest": f"environment-{kwargs['slot']}",
                },
            ), mock.patch.object(
                self.runner.base, "user_prompt", return_value="fixture prompt"
            ), mock.patch.object(
                self.runner.base, "existing_judge_record", return_value=None
            ), mock.patch.object(
                self.runner.compat, "compatible_standard_slot", side_effect=fake_slot
            ):
                self.runner.judge_cells(
                    args=argparse.Namespace(
                        auth_source=Path(__file__),
                        runtime_root=out,
                        timeout=1800,
                        phase="smoke",
                    ),
                    out_dir=out,
                    auth_report={
                        "protocol_sha256": "p" * 64,
                        "authorization_digest": "a" * 64,
                    },
                    authorization={
                        "maximum_judge_calls": 480,
                        "token_or_cost_budget": {"maximum": 17599744},
                    },
                    protocol={"execution_design": {"order_seed_sha256": "seed"}},
                    manifests={},
                    records=[record],
                    cases={"case": case},
                    generation_calls=16,
                    judge_calls=17,
                    counted_tokens=789490,
                    amendment=self.protocol,
                )
            self.assertEqual(len(calls), 2)
            for call in calls:
                self.assertNotIn("mindthus-beta:", call["prompt"])
                self.assertNotIn(self.paths[-2], call["prompt"])
            self.assertTrue(list((out / "blinded-candidate-views").glob("*.json")))

    def test_preflight_cannot_execute_a_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            auth_report = {
                "blinded_view_protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
            }
            args = argparse.Namespace(
                phase="smoke",
                out_dir=out,
                runtime_root=out / "runtime",
                arm_manifest=[Path("stable"), Path("direct"), Path("thin")],
                authorization=AUTHORIZATION,
                auth_source=out / "auth.json",
                timeout=1800,
                preflight_only=True,
            )
            with mock.patch.object(
                self.runner.base,
                "authorized_context",
                return_value=(auth_report, {"fixture": True}, {"fixture": True}),
            ), mock.patch.object(
                self.runner.base, "verify_arm_set", return_value={}
            ), mock.patch.object(
                self.runner, "ensure_source_snapshot"
            ), mock.patch.object(
                self.runner.compat, "ensure_failed_records"
            ) as ensure:
                report, code = self.runner.run_blinded_view(args)
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "ready")
            self.assertFalse(report["model_execution_performed"])
            self.assertFalse(ensure.call_args.kwargs["allow_model_execution"])

    @unittest.skipUnless(LOCK.is_file(), "blinded-view lock freezes after tests")
    def test_official_blinded_view_lock_validates(self) -> None:
        report = self.freezer.validate_lock(PROTOCOL, LOCK)
        self.assertEqual(report["status"], "frozen")

    @unittest.skipUnless(
        AUTHORIZATION.is_file(), "blinded-view authorization binds after freeze"
    )
    def test_official_blinded_view_authorization_validates(self) -> None:
        validator = load_module("beta2_blinded_view_auth_validator", AUTH_VALIDATOR)
        report = validator.validate_authorization(AUTHORIZATION)
        self.assertEqual(report["status"], "authorized")
        self.assertEqual(report["unknown_usage_reserved_tokens"], 4352000)
        self.assertEqual(report["token_budget"]["maximum"], 17599744)
        self.assertFalse(report["release_preparation"])


if __name__ == "__main__":
    unittest.main()
