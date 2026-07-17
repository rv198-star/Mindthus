import argparse
import copy
import hashlib
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
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.json"
)
LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.lock.json"
)
AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-judge-compat.1.json"
)
FREEZER = BETA_ROOT / "runtime" / "freeze-evaluation-judge-compat-v0.4.py"
AUTH_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-judge-compat.py"
)
RUNNER = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v04_judge_compat.py"
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
    / "real-v04-evaluation-a6e9da7e"
    / "run"
)
SOURCE_ARMS = SOURCE_RUN.parent / "arms"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BetaTwoV04JudgeCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freezer = load_module("beta2_judge_compat_freezer", FREEZER)
        cls.runner = load_module("beta2_judge_compat_runner", RUNNER)
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        matrix = cls.runner.base.read_json(cls.runner.base.MATRIX_PATH)
        cls.case = next(iter(cls.runner.base.source_cases(matrix).values()))

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
            "rationale": "The visible answer satisfies the frozen contract.",
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

    def original_attempts(self, environment, prompt, input_digest):
        prompt_digest = hashlib.sha256(prompt.encode()).hexdigest()
        return [
            {
                "attempt": number,
                "attempt_digest": str(number) * 64,
                "returncode": 1,
                "timed_out": False,
                "output_present": False,
                "parse_error": "empty",
                "environment_digest": environment["environment_digest"],
                "blinded_input_digest": input_digest,
                "judge_prompt_sha256": prompt_digest,
            }
            for number in (1, 2)
        ]

    def test_amendment_changes_only_api_schema_compatibility(self) -> None:
        report = self.freezer.validate_protocol(self.protocol)
        self.assertEqual(report["amendment_id"], "0.4-judge-compat.1")
        self.assertEqual(report["retained_zero_output_judge_attempts"], 4)
        self.assertEqual(
            self.protocol["budget_accounting"]["judge_calls_remaining"], 476
        )
        self.assertFalse(self.protocol["budget_accounting"]["budget_expansion"])
        self.assertFalse(
            self.protocol["schema_compatibility"]["semantic_contract_relaxation"]
        )

    def test_compatible_schema_is_exact_two_keyword_removal(self) -> None:
        original = json.loads(ORIGINAL_SCHEMA.read_text(encoding="utf-8"))
        compatible = json.loads(COMPATIBLE_SCHEMA.read_text(encoding="utf-8"))
        expected = copy.deepcopy(original)
        self.assertTrue(
            expected["properties"]["primitive_obligation_results"].pop(
                "uniqueItems"
            )
        )
        self.assertTrue(
            expected["properties"]["unexpected_primitive_actions"].pop(
                "uniqueItems"
            )
        )
        self.assertEqual(compatible, expected)

    def test_local_validator_still_rejects_duplicate_primitives(self) -> None:
        verdict = self.verdict()
        expected = self.case["contract"]["expected_primitive_obligations"]
        if not expected:
            self.skipTest("selected fixture has no primitive obligation")
        verdict["primitive_obligation_results"].append(
            {"primitive_id": expected[0], "satisfied": True}
        )
        old_schema = self.runner.base.JUDGE_SCHEMA
        self.runner.base.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
        try:
            with self.assertRaises(ValueError):
                self.runner.base.validate_judge_output(verdict, self.case)
        finally:
            self.runner.base.JUDGE_SCHEMA = old_schema

    def test_original_v04_runner_and_analyzer_remain_frozen(self) -> None:
        self.assertEqual(
            hashlib.sha256(
                (BETA_ROOT / "runtime" / "run_real_codex_evaluation_v04.py").read_bytes()
            ).hexdigest(),
            "349614d7a6f9984c1f96fdb1207ad075f941be109f1a53b0679f3ab695c68162",
        )
        self.assertEqual(
            hashlib.sha256(
                (BETA_ROOT / "runtime" / "analyze_codex_evaluation_v04.py").read_bytes()
            ).hexdigest(),
            "5ee6a73d7f85cf50b54accf8680dafb6f2c06daf210a475bd8ec0b4df729959a",
        )

    @unittest.skipUnless(
        SOURCE_RUN.is_dir() and SOURCE_ARMS.is_dir(),
        "local retained v0.4 evidence and arms are unavailable",
    )
    def test_frozen_source_receipts_replay_without_a_model(self) -> None:
        recovery_auth = json.loads(
            (
                BETA_ROOT
                / "authorizations"
                / "issue-119-codex-v0.4-recovery.1.json"
            ).read_text(encoding="utf-8")
        )
        base_protocol = json.loads(
            (
                BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
            ).read_text(encoding="utf-8")
        )
        arm_paths = [
            SOURCE_ARMS / arm / "sealed-arm.json"
            for arm in ("stable", "direct-only", "thin-kernel")
        ]
        manifests = self.runner.base.verify_arm_set(arm_paths, recovery_auth)
        receipts = self.runner.verify_generation_source(
            SOURCE_RUN, manifests, base_protocol, self.protocol
        )
        attempts = self.runner.verify_original_failures(SOURCE_RUN, self.protocol)
        self.assertEqual(len(receipts), 15)
        self.assertEqual([len(attempts[slot]) for slot in (1, 2)], [2, 2])

    def test_failed_slot_appends_attempt_three_and_keeps_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            parent = (
                out
                / "judge-attempts"
                / self.runner.FAILED_OUTPUT_ID
                / "slot-1"
            )
            (parent / "attempt-01").mkdir(parents=True)
            (parent / "attempt-02").mkdir()
            environment = self.environment(out)
            prompt = "frozen prompt"
            input_digest = "i" * 64
            original = self.original_attempts(environment, prompt, input_digest)
            commands = []
            side_effect = self.stream_side_effect(
                [self.capture(returncode=0, output=True)], commands
            )
            old_schema = self.runner.base.JUDGE_SCHEMA
            self.runner.base.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
            try:
                with mock.patch.object(
                    self.runner.base, "run_streamed", side_effect=side_effect
                ):
                    record, calls, tokens = self.runner.ensure_failed_slot(
                        out_dir=out,
                        slot=1,
                        original_attempts=original,
                        prompt=prompt,
                        blinded_input_digest=input_digest,
                        case=self.case,
                        environment=environment,
                        authorization=self.authorization(),
                        timeout=1800,
                        allow_model_execution=True,
                    )
            finally:
                self.runner.base.JUDGE_SCHEMA = old_schema
            self.assertEqual(calls, 1)
            self.assertEqual(tokens, 15)
            self.assertEqual(record["attempt"], 3)
            self.assertEqual(
                [item["attempt"] for item in record["judge_attempt_history"]],
                [1, 2, 3],
            )
            self.assertIn(str(COMPATIBLE_SCHEMA), commands[0])

    def test_failed_attempt_three_allows_exactly_attempt_four(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            parent = (
                out
                / "judge-attempts"
                / self.runner.FAILED_OUTPUT_ID
                / "slot-1"
            )
            (parent / "attempt-01").mkdir(parents=True)
            (parent / "attempt-02").mkdir()
            environment = self.environment(out)
            prompt = "frozen prompt"
            input_digest = "i" * 64
            original = self.original_attempts(environment, prompt, input_digest)
            commands = []
            side_effect = self.stream_side_effect(
                [
                    self.capture(returncode=1, output=False),
                    self.capture(returncode=0, output=True),
                ],
                commands,
            )
            old_schema = self.runner.base.JUDGE_SCHEMA
            self.runner.base.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
            try:
                with mock.patch.object(
                    self.runner.base, "run_streamed", side_effect=side_effect
                ):
                    record, calls, _tokens = self.runner.ensure_failed_slot(
                        out_dir=out,
                        slot=1,
                        original_attempts=original,
                        prompt=prompt,
                        blinded_input_digest=input_digest,
                        case=self.case,
                        environment=environment,
                        authorization=self.authorization(),
                        timeout=1800,
                        allow_model_execution=True,
                    )
            finally:
                self.runner.base.JUDGE_SCHEMA = old_schema
            self.assertEqual(calls, 2)
            self.assertEqual(record["attempt"], 4)
            self.assertEqual(
                [item["attempt"] for item in record["judge_attempt_history"]],
                [1, 2, 3, 4],
            )
            self.assertEqual(len(commands), 2)

    def test_remaining_judge_stops_after_two_compatible_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            environment = self.environment(out)
            commands = []
            side_effect = self.stream_side_effect(
                [
                    self.capture(returncode=1, output=False),
                    self.capture(returncode=1, output=False),
                ],
                commands,
            )
            old_schema = self.runner.base.JUDGE_SCHEMA
            self.runner.base.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
            try:
                with mock.patch.object(
                    self.runner.base, "run_streamed", side_effect=side_effect
                ), self.assertRaises(self.runner.base.EvaluationStop) as raised:
                    self.runner.compatible_standard_slot(
                        slot=1,
                        output_id="o" * 64,
                        prompt="frozen prompt",
                        blinded_input_digest="i" * 64,
                        case=self.case,
                        environment=environment,
                        authorization=self.authorization(),
                        out_dir=out,
                        timeout=1800,
                    )
            finally:
                self.runner.base.JUDGE_SCHEMA = old_schema
            self.assertEqual(
                raised.exception.veto_id, "v0.4-judge-compatibility-exhausted"
            )
            self.assertEqual(len(commands), 2)
            self.assertTrue(
                (
                    out
                    / "human-judge-failure-packets"
                    / f"{'o' * 64}-slot-1.json"
                ).is_file()
            )

    def test_preflight_cannot_execute_a_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            auth_report = {
                "judge_compatibility_protocol_sha256": hashlib.sha256(
                    PROTOCOL.read_bytes()
                ).hexdigest()
            }
            authorization = {"fixture": True}
            base_protocol = {"fixture": True}
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
                return_value=(auth_report, authorization, base_protocol),
            ), mock.patch.object(
                self.runner.base, "verify_arm_set", return_value={}
            ), mock.patch.object(
                self.runner, "ensure_failed_records", return_value=(0, 0, 0)
            ) as ensure:
                report, code = self.runner.run_compatibility(args)
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "ready")
            self.assertFalse(report["model_execution_performed"])
            self.assertFalse(ensure.call_args.kwargs["allow_model_execution"])

    @unittest.skipUnless(LOCK.is_file(), "Judge compatibility lock freezes after tests")
    def test_official_compatibility_lock_validates(self) -> None:
        report = self.freezer.validate_lock(PROTOCOL, LOCK)
        self.assertEqual(report["status"], "frozen")

    @unittest.skipUnless(
        AUTHORIZATION.is_file(), "Judge compatibility authorization binds after freeze"
    )
    def test_official_compatibility_authorization_validates(self) -> None:
        validator = load_module("beta2_judge_compat_auth_validator", AUTH_VALIDATOR)
        report = validator.validate_authorization(AUTHORIZATION)
        self.assertEqual(report["status"], "authorized")
        self.assertEqual(report["maximum_judge_calls"], 480)
        self.assertFalse(report["release_preparation"])


if __name__ == "__main__":
    unittest.main()
