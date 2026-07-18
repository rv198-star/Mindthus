import argparse
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.json"
)
LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-judge-compat.1.lock.json"
)
PENDING_AUTHORIZATION = (
    BETA_ROOT
    / "authorizations"
    / "issue-119-codex-v0.5-judge-compat.1.pending.json"
)
RUNNER = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v05_judge_compat.py"
FREEZER = BETA_ROOT / "runtime" / "freeze-evaluation-judge-compat-v0.5.py"
AUTH_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.5-judge-compat.py"
)
ORIGINAL_SCHEMA = BETA_ROOT / "fixtures" / "judge-output-v0.4.schema.json"
COMPATIBLE_SCHEMA = (
    BETA_ROOT / "fixtures" / "judge-output-v0.4-openai-compatible.schema.json"
)
SOURCE_RUN = (
    REPO
    / ".tplan"
    / "missions"
    / "mindthus-beta2-evaluation"
    / "artifacts"
    / "real-v05-smoke-f9bc7232"
    / "run"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BetaTwoV05JudgeCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module("beta2_v05_judge_compat_runner", RUNNER)
        cls.freezer = load_module("beta2_v05_judge_compat_freezer", FREEZER)
        cls.auth_validator = load_module(
            "beta2_v05_judge_compat_auth_validator", AUTH_VALIDATOR
        )
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        matrix = cls.runner.BASE.read_json(cls.runner.BASE.MATRIX_PATH)
        cases = cls.runner.V04.source_cases(matrix)
        cls.case = cases["b2-dev-owner-3l5s"]

    def verdict(self):
        contract = self.case["contract"]
        return {
            "normalized_final_answer_score": 1,
            "observed_execution_owner": contract["accepted_execution_owners"][0],
            "primitive_obligation_results": [
                {"primitive_id": primitive, "satisfied": True}
                for primitive in contract["expected_primitive_obligations"]
            ],
            "unexpected_primitive_actions": [],
            "false_wakeup_final_answer": False,
            "required_visible_action_present": (
                None if contract["required_visible_action"] is None else True
            ),
            "authority_or_evidence_regression": False,
            "clarification_turns": 0,
            "rationale": "The answer satisfies the frozen visible-case contract.",
        }

    def capture(self, *, returncode=0, output=True):
        events = [
            {"type": "thread.started", "thread_id": "fixture"},
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 2,
                    "reasoning_output_tokens": 3,
                },
            },
        ]
        return types.SimpleNamespace(
            returncode=returncode,
            timed_out=False,
            stdout="".join(json.dumps(item) + "\n" for item in events),
            stderr="",
            fixture_output=output,
        )

    def environment(self, root: Path, slot: int = 1):
        execution_root = root / f"judge-{slot}"
        execution_root.mkdir(parents=True, exist_ok=True)
        return {
            "execution_root": str(execution_root),
            "environment_digest": f"environment-{slot}",
            "env": {},
        }

    def authorization(self):
        return {
            "judge_model_and_reasoning": {
                "model_id": "gpt-5.6-sol",
                "reasoning_effort": "xhigh",
            }
        }

    def stream_side_effect(self, captures, commands):
        queue = list(captures)

        def run(command, **_kwargs):
            commands.append(command)
            capture = queue.pop(0)
            if capture.fixture_output:
                output_path = Path(command[command.index("-o") + 1])
                output_path.write_text(
                    json.dumps(self.verdict(), ensure_ascii=False), encoding="utf-8"
                )
            return capture

        return run

    def test_transport_view_removes_only_two_unsupported_keywords(self) -> None:
        report = self.runner._validate_transport_schema()
        self.assertEqual(
            report["removed_keyword_paths"],
            [
                "properties.primitive_obligation_results.uniqueItems",
                "properties.unexpected_primitive_actions.uniqueItems",
            ],
        )
        self.assertTrue(report["canonical_local_validation_preserved"])

    def test_local_validator_still_rejects_duplicate_primitives(self) -> None:
        verdict = self.verdict()
        primitive = self.case["contract"]["expected_primitive_obligations"][0]
        verdict["primitive_obligation_results"].append(
            {"primitive_id": primitive, "satisfied": True}
        )
        old = self.runner.V04.JUDGE_SCHEMA
        self.runner.V04.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
        try:
            with self.assertRaises(ValueError):
                self.runner.V04.validate_judge_output(verdict, self.case)
        finally:
            self.runner.V04.JUDGE_SCHEMA = old

    def test_frozen_amendment_preserves_original_ceiling_and_zero_retry(self) -> None:
        report = self.freezer.validate_protocol(
            self.protocol, verify_source_files=SOURCE_RUN.is_dir()
        )
        self.assertFalse(report["budget_expansion"])
        self.assertEqual(report["remaining_judge_calls"], 30)
        budget = self.protocol["budget_accounting"]
        self.assertEqual(budget["original_ceiling"]["maximum_judge_calls"], 34)
        self.assertEqual(budget["future_retry_headroom"], 0)

    def test_official_lock_validates(self) -> None:
        report = self.freezer.validate_lock(PROTOCOL, self.protocol, LOCK)
        self.assertEqual(report["status"], "frozen")
        self.assertFalse(report["budget_expansion"])

    def test_pending_authorization_validates_without_runtime_execution(self) -> None:
        report = self.auth_validator.validate_authorization(
            PENDING_AUTHORIZATION, require_active=False, check_runtime=False
        )
        self.assertEqual(report["status"], "pending")
        self.assertEqual(report["remaining_judge_calls"], 30)
        self.assertFalse(report["release_preparation"])

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "retained v0.5 source run is unavailable")
    def test_retained_source_replays_without_a_model(self) -> None:
        source = self.runner.verify_retained_source(
            SOURCE_RUN,
            self.protocol,
            self.protocol["base_binding"]["protocol_sha256"],
        )
        self.assertEqual(source["generation_outputs"], 3)
        self.assertEqual(source["judge_attempts"], 4)
        self.assertEqual(source["counted_tokens"], 90_100)

    def test_new_compatible_slot_uses_one_attempt_and_writes_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            environment = self.environment(out)
            commands = []
            side_effect = self.stream_side_effect([self.capture()], commands)
            old_schema = self.runner.V04.JUDGE_SCHEMA
            self.runner.V04.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
            self.runner._ACTIVE_AMENDMENT = self.protocol
            try:
                with mock.patch.object(
                    self.runner.V04, "run_streamed", side_effect=side_effect
                ):
                    record, calls, tokens = self.runner.compatible_judge_slot(
                        slot=1,
                        output_id="a" * 64,
                        prompt="frozen prompt",
                        blinded_input_digest="b" * 64,
                        case=self.case,
                        environment=environment,
                        authorization=self.authorization(),
                        out_dir=out,
                        timeout=1800,
                    )
            finally:
                self.runner._ACTIVE_AMENDMENT = None
                self.runner.V04.JUDGE_SCHEMA = old_schema
            self.assertEqual(calls, 1)
            self.assertEqual(tokens, 15)
            self.assertEqual(record["attempt"], 1)
            self.assertEqual(len(commands), 1)
            self.assertIn(str(COMPATIBLE_SCHEMA), commands[0])

    def test_failed_compatible_call_stops_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            environment = self.environment(out)
            commands = []
            side_effect = self.stream_side_effect(
                [self.capture(returncode=1, output=False)], commands
            )
            old_schema = self.runner.V04.JUDGE_SCHEMA
            self.runner.V04.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
            self.runner._ACTIVE_AMENDMENT = self.protocol
            try:
                with mock.patch.object(
                    self.runner.V04, "run_streamed", side_effect=side_effect
                ), self.assertRaises(self.runner.CompatibilityStop) as raised:
                    self.runner.compatible_judge_slot(
                        slot=1,
                        output_id="c" * 64,
                        prompt="frozen prompt",
                        blinded_input_digest="d" * 64,
                        case=self.case,
                        environment=environment,
                        authorization=self.authorization(),
                        out_dir=out,
                        timeout=1800,
                    )
            finally:
                self.runner._ACTIVE_AMENDMENT = None
                self.runner.V04.JUDGE_SCHEMA = old_schema
            self.assertEqual(
                raised.exception.veto_id, "v0.5-judge-compatibility-exhausted"
            )
            self.assertEqual(len(commands), 1)
            attempts = list(out.glob("judge-attempts/**/attempt.json"))
            self.assertEqual(len(attempts), 1)

    def test_finalizable_attempt_does_not_reserve_another_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            output_id = "a" * 64
            attempt = out / "judge-attempts" / output_id / "slot-1" / "attempt-01"
            attempt.mkdir(parents=True)
            self.runner._ACTIVE_AMENDMENT = self.protocol
            try:
                self.assertEqual(
                    self.runner._new_judge_calls_required(out, output_id, [1, 2]),
                    1,
                )
            finally:
                self.runner._ACTIVE_AMENDMENT = None

    def test_preflight_cannot_execute_a_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            args = argparse.Namespace(
                authorization=PENDING_AUTHORIZATION,
                arm_manifest=[Path("stable"), Path("direct"), Path("thin")],
                out_dir=out,
                runtime_root=out / "runtime",
                auth_source=out / "auth.json",
                timeout=1800,
                preflight_only=True,
            )
            authorization = json.loads(PENDING_AUTHORIZATION.read_text(encoding="utf-8"))
            base_protocol = json.loads(
                (BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json").read_text(
                    encoding="utf-8"
                )
            )
            with mock.patch.object(
                self.runner,
                "_authorization_context",
                return_value=(
                    {
                        "status": "pending",
                        "protocol_sha256": self.protocol["base_binding"]["protocol_sha256"],
                    },
                    authorization,
                    base_protocol,
                ),
            ), mock.patch.object(
                self.runner.V04,
                "verify_arm_set",
                return_value={"stable": {}, "direct-only": {}, "thin-kernel": {}},
            ), mock.patch.object(
                self.runner,
                "verify_retained_source",
                return_value={
                    "generation_outputs": 3,
                    "generation_calls": 3,
                    "judge_attempts": 4,
                    "valid_judge_records": 0,
                    "committed_batches": 0,
                    "counted_tokens": 90_100,
                    "failed_output_id": "e" * 64,
                    "source_receipt_digest": "f" * 64,
                },
            ), mock.patch.object(
                self.runner.V04, "observed_attempt_usage", return_value=(3, 4, 90_100)
            ), mock.patch.object(self.runner.V04, "run_streamed") as semantic_call:
                report, code = self.runner.preflight(args)
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "pending-authorization")
            self.assertFalse(report["model_execution_performed"])
            semantic_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
