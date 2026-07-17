import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.json"
LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.lock.json"
AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-recovery.1.json"
)
FREEZER = BETA_ROOT / "runtime" / "freeze-evaluation-recovery-v0.4.py"
AUTH_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-recovery.py"
)
RUNNER = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v04_recovery.py"
ANALYZER = BETA_ROOT / "runtime" / "analyze_codex_evaluation_v04_recovery.py"
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


class BetaTwoV04RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.freezer = load_module("beta2_recovery_freezer", FREEZER)
        cls.runner = load_module("beta2_recovery_runner", RUNNER)
        cls.analyzer = load_module("beta2_recovery_analyzer", ANALYZER)
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def make_attempt(
        self,
        root: Path,
        *,
        number: int,
        returncode: int = 0,
        timed_out: bool = False,
        usage: dict | None = None,
        answer: str = "complete answer\n",
    ):
        path = (
            root
            / "generation-attempts"
            / self.runner.RECOVERY_CELL_ID
            / f"attempt-{number:02d}"
        )
        path.mkdir(parents=True)
        events = json.dumps({"type": "thread.started"}) + "\n"
        stderr = ""
        (path / "events.jsonl").write_text(events, encoding="utf-8")
        (path / "stderr.txt").write_text(stderr, encoding="utf-8")
        (path / "answer.txt").write_text(answer, encoding="utf-8")
        attempt = {
            "schema_version": "mindthus-beta2-generation-attempt-v0.4",
            "cell_id": self.runner.RECOVERY_CELL_ID,
            "attempt": number,
            "started_at_utc": "2026-07-17T00:00:00+00:00",
            "completed_at_utc": "2026-07-17T00:00:01+00:00",
            "returncode": returncode,
            "timed_out": timed_out,
            "wall_time_seconds": 1.0,
            "first_observable_action": {
                "offset_seconds": 0.25,
            },
            "answer_present": bool(answer),
            "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(),
            "events_sha256": hashlib.sha256(events.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
            "usage": usage,
            "counted_tokens": self.runner.base.token_total(usage),
        }
        attempt["attempt_digest"] = self.runner.base.canonical_sha256(attempt)
        (path / "attempt.json").write_text(
            json.dumps(attempt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        attempt["path"] = str(path)
        evidence = {
            "event_types": ["thread.started", "turn.completed"],
            "loaded_commands": [],
            "agent_messages": [answer],
            "usage": usage,
            "native_telemetry": {"lifecycle_event": ["session-start"]},
            "first_native_timestamp": None,
        }
        return attempt, answer, evidence

    def test_amendment_is_narrow_and_budget_balances(self) -> None:
        report = self.freezer.validate_protocol(self.protocol)
        self.assertEqual(report["amendment_id"], "0.4-recovery.1")
        self.assertEqual(report["retained_generation_outputs"], 10)
        budget = self.protocol["budget_accounting"]
        self.assertEqual(
            budget["amended_measured_token_ceiling"]
            + budget["unknown_usage_reserve"]["reserved_tokens"],
            budget["base_v0_4_measured_token_ceiling"],
        )
        attempt = self.protocol["amendment"]["recovery_attempt"]
        self.assertEqual(attempt["attempt_number"], 2)
        self.assertEqual(attempt["additional_recovery_attempts"], 0)
        self.assertEqual(attempt["on_any_failure"], "terminal-stop-v0.4")

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

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "local retained v0.4 evidence is unavailable")
    def test_frozen_source_receipts_match_retained_artifacts(self) -> None:
        self.runner.verify_completed_source_cells(SOURCE_RUN, self.protocol)
        attempt, answer, _evidence = self.runner.verify_incomplete_attempt(
            SOURCE_RUN, self.protocol
        )
        self.assertEqual(attempt["attempt"], 1)
        self.assertTrue(answer)
        self.assertIsNone(attempt["usage"])

    def test_attempt_loader_detects_semantic_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_attempt(root, number=2, usage={"input_tokens": 10})
            loaded, answer, _evidence = self.runner.load_attempt(
                root, self.runner.RECOVERY_CELL_ID, 2
            )
            self.assertEqual(loaded["counted_tokens"], 10)
            self.assertEqual(answer, "complete answer\n")
            (Path(loaded["path"]) / "answer.txt").write_text(
                "tampered\n", encoding="utf-8"
            )
            with self.assertRaises(self.runner.base.EvaluationStop):
                self.runner.load_attempt(root, self.runner.RECOVERY_CELL_ID, 2)

    def test_recovered_record_is_append_only_and_base_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.make_attempt(
                root,
                number=1,
                returncode=-15,
                timed_out=True,
                usage=None,
                answer="partial\n",
            )
            second = self.make_attempt(
                root,
                number=2,
                usage={
                    "input_tokens": 10,
                    "output_tokens": 2,
                    "reasoning_output_tokens": 3,
                },
            )
            telemetry = {
                "measurements": {
                    "failure_count": {},
                    "wall_time_seconds": {},
                    "first_observable_action_latency_seconds": {},
                },
                "evidence_gate": {"status": "pass", "reasons": []},
                "telemetry_digest": "old",
            }
            with mock.patch.object(
                self.runner.base,
                "build_turn_telemetry",
                return_value=telemetry,
            ):
                record = self.runner.build_recovered_record(
                    cell={
                        "case_id": "b2-dev-near-normal-debugging",
                        "arm_id": "direct-only",
                        "repeat": 1,
                    },
                    case={
                        "contract": {
                            "entry_mode": "stay-asleep",
                            "lifecycle_path": "session-start",
                            "source": {"fixture": True},
                        }
                    },
                    manifest={
                        "host": {
                            "execution_root": str(root),
                        },
                        "package": {"root": str(root)},
                    },
                    key={"fixture": True},
                    first=first,
                    second=second,
                    authorization={
                        "recovery_budget": {
                            "unknown_usage_reserved_tokens": 2176000,
                        }
                    },
                    recovery_digest="a" * 64,
                    recovery_lock_digest="b" * 64,
                    out_dir=root,
                )
            self.assertEqual(
                [item["attempt"] for item in record["generation_attempt_history"]],
                [1, 2],
            )
            self.assertEqual(record["counted_tokens"], 15)
            self.assertEqual(
                self.runner.base.completed_cell(root, self.runner.RECOVERY_CELL_ID)[
                    "record_digest"
                ],
                record["record_digest"],
            )

    @unittest.skipUnless(
        SOURCE_RUN.is_dir() and SOURCE_ARMS.is_dir(),
        "local retained v0.4 evidence and arms are unavailable",
    )
    def test_model_free_full_recovery_path_on_source_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            shutil.copytree(SOURCE_RUN, out)
            # SOURCE_RUN is a live retained-evidence directory.  Once the official
            # recovery has completed, reconstruct the frozen pre-recovery state in
            # this disposable copy before exercising the model-free recovery path.
            recovered_cell = out / "cells" / self.runner.RECOVERY_CELL_ID
            recovered_attempt = (
                out
                / "generation-attempts"
                / self.runner.RECOVERY_CELL_ID
                / "attempt-02"
            )
            if recovered_cell.exists():
                shutil.rmtree(recovered_cell)
            if recovered_attempt.exists():
                shutil.rmtree(recovered_attempt)
            recovery_root = out / "recovery" / "0.4-recovery.1"
            if recovery_root.is_dir():
                for path in recovery_root.iterdir():
                    if path.name == "pre-amendment":
                        continue
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            base_authorization = json.loads(
                (
                    BETA_ROOT
                    / "authorizations"
                    / "issue-119-codex-v0.4.json"
                ).read_text(encoding="utf-8")
            )
            base_authorization["recovery_budget"] = {
                "unknown_usage_reserved_tokens": 2176000,
            }
            base_protocol = json.loads(
                (
                    BETA_ROOT
                    / "protocols"
                    / "evaluation-protocol-v0.4.json"
                ).read_text(encoding="utf-8")
            )
            auth_report = {
                "protocol_sha256": self.protocol["base_binding"][
                    "protocol_sha256"
                ],
                "recovery_protocol_sha256": "a" * 64,
                "recovery_lock_digest": "b" * 64,
                "unknown_usage_reserved_tokens": 2176000,
            }

            def synthetic_attempt(**_kwargs):
                attempt, answer, evidence = self.make_attempt(
                    out,
                    number=2,
                    usage={
                        "input_tokens": 10,
                        "output_tokens": 2,
                        "reasoning_output_tokens": 3,
                    },
                )
                return attempt, None, answer, evidence

            retained_ids = {
                item["cell_id"]
                for item in self.protocol["retained_source_run"][
                    "completed_cells"
                ]
            }
            real_completed_cell = self.runner.base.completed_cell

            def copied_completed_cell(run_dir, cell_id):
                if cell_id in retained_ids:
                    return json.loads(
                        (
                            run_dir
                            / "cells"
                            / cell_id
                            / "record.json"
                        ).read_text(encoding="utf-8")
                    )
                return real_completed_cell(run_dir, cell_id)

            arm_paths = [
                SOURCE_ARMS / arm / "sealed-arm.json"
                for arm in ("stable", "direct-only", "thin-kernel")
            ]
            with mock.patch.object(
                self.runner.base,
                "authorized_context",
                return_value=(auth_report, base_authorization, base_protocol),
            ), mock.patch.object(
                self.runner.base,
                "run_generator_attempt",
                side_effect=synthetic_attempt,
            ) as model_call, mock.patch.object(
                self.runner.base,
                "completed_cell",
                side_effect=copied_completed_cell,
            ):
                record, created = self.runner.ensure_recovered_cell(
                    out_dir=out,
                    authorization_path=Path("unused"),
                    arm_paths=arm_paths,
                    timeout=1800,
                    allow_model_execution=True,
                )
            self.assertTrue(created)
            self.assertEqual(model_call.call_count, 1)
            self.assertIsNotNone(record)
            self.assertEqual(record["generation_attempt"]["attempt"], 2)
            self.assertTrue(
                (
                    out
                    / "recovery"
                    / "0.4-recovery.1"
                    / "pre-amendment"
                    / "stop-report.json"
                ).is_file()
            )
            self.assertTrue(
                (
                    out
                    / "generation-attempts"
                    / self.runner.RECOVERY_CELL_ID
                    / "attempt-01"
                    / "answer.txt"
                ).is_file()
            )

    def test_preflight_cannot_execute_a_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            self.runner,
            "ensure_recovered_cell",
            return_value=(None, False),
        ) as ensure:
            args = argparse.Namespace(
                out_dir=Path(tmp),
                authorization=AUTHORIZATION,
                arm_manifest=[Path("stable"), Path("direct"), Path("thin")],
                timeout=1800,
                preflight_only=True,
                phase="smoke",
            )
            report, code = self.runner.run_recovery(args)
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "ready")
            self.assertFalse(report["model_execution_performed"])
            self.assertFalse(ensure.call_args.kwargs["allow_model_execution"])

    def test_efficiency_censoring_removes_exactly_one_pair(self) -> None:
        rows = [
            {"case_id": "other", "repeat": 1},
            {"case_id": "b2-dev-near-normal-debugging", "repeat": 1},
            {"case_id": "b2-dev-near-normal-debugging", "repeat": 2},
        ]
        usable, censored = self.analyzer.filtered_efficiency_rows(rows)
        self.assertEqual(len(usable), 2)
        self.assertEqual(censored, [rows[1]])

    @unittest.skipUnless(LOCK.is_file(), "recovery lock is frozen after code tests pass")
    def test_official_recovery_lock_validates(self) -> None:
        report = self.freezer.validate_lock(PROTOCOL, LOCK)
        self.assertEqual(report["status"], "frozen")

    @unittest.skipUnless(
        AUTHORIZATION.is_file(), "recovery authorization binds after the lock is frozen"
    )
    def test_official_recovery_authorization_validates(self) -> None:
        validator = load_module("beta2_recovery_auth_validator", AUTH_VALIDATOR)
        report = validator.validate_authorization(AUTHORIZATION)
        self.assertEqual(report["status"], "authorized")
        self.assertEqual(report["maximum_generation_calls"], 239)
        self.assertEqual(report["unknown_usage_reserved_tokens"], 2176000)
        self.assertFalse(report["release_preparation"])


if __name__ == "__main__":
    unittest.main()
