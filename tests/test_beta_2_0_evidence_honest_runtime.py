import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
STREAM_PATH = BETA_ROOT / "runtime" / "codex_stream_capture.py"
MATERIALIZER_PATH = BETA_ROOT / "runtime" / "materialize-real-codex-arm.py"
RUNNER_PATH = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v04.py"
ANALYZER_PATH = BETA_ROOT / "runtime" / "analyze_codex_evaluation_v04.py"
PROBE_PATH = BETA_ROOT / "runtime" / "probe_codex_hook.py"
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BetaTwoEvidenceHonestRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stream = load_module("beta2_stream_capture_v04", STREAM_PATH)
        cls.probe = load_module("beta2_hook_probe_v04", PROBE_PATH)
        cls.materializer = load_module("beta2_materializer_v04", MATERIALIZER_PATH)
        cls.runner = load_module("beta2_runner_v04", RUNNER_PATH)
        cls.analyzer = load_module("beta2_analyzer_v04", ANALYZER_PATH)
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in matrix["cases"]}

    def test_observable_receipt_rejects_noise_and_accepts_action(self) -> None:
        self.assertIsNone(
            self.stream.observable_action_receipt(
                "not-json\n", arrived_at=1.1, started_at=1.0, stdout_sequence=1
            )
        )
        self.assertIsNone(
            self.stream.observable_action_receipt(
                json.dumps({"type": "thread.started"}) + "\n",
                arrived_at=1.1,
                started_at=1.0,
                stdout_sequence=2,
            )
        )
        receipt = self.stream.observable_action_receipt(
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "secret answer"},
                }
            )
            + "\n",
            arrived_at=1.25,
            started_at=1.0,
            stdout_sequence=3,
        )
        self.assertEqual(receipt["offset_seconds"], 0.25)
        self.assertEqual(receipt["item_type"], "agent_message")
        self.assertFalse(receipt["content_retained"])
        self.assertNotIn("secret answer", json.dumps(receipt))

    def test_stream_capture_timestamps_line_arrival(self) -> None:
        script = (
            "import json,time; "
            "print(json.dumps({'type':'thread.started'}),flush=True); "
            "time.sleep(0.04); "
            "print(json.dumps({'type':'item.completed','item':"
            "{'type':'command_execution','command':'true'}}),flush=True)"
        )
        capture = self.stream.run_streamed(
            [sys.executable, "-c", script],
            input_text="",
            cwd=REPO,
            timeout=2,
        )
        self.assertEqual(capture.returncode, 0)
        self.assertFalse(capture.timed_out)
        self.assertIsNotNone(capture.first_observable_action)
        self.assertGreaterEqual(
            capture.first_observable_action["offset_seconds"], 0.025
        )

    def test_v04_smoke_order_and_startup_scope_are_frozen(self) -> None:
        cells = self.runner.expected_cells(self.protocol, "smoke")
        self.assertEqual(len(cells), 15)
        self.assertEqual(
            cells[0],
            {"case_id": "b2-dev-owner-3l5s", "arm_id": "direct-only", "repeat": 1},
        )
        self.assertEqual(
            self.protocol["execution_design"]["host_lifecycle_scope"][
                "real_model_session_mode"
            ],
            "startup-only",
        )
        self.assertIn(
            "without hook-trust bypass",
            self.protocol["execution_design"]["host_lifecycle_scope"][
                "direct_only_kernel_absence"
            ],
        )

    def test_judge_output_requires_exact_primitive_set(self) -> None:
        case = {"contract": self.cases["b2-dev-owner-3l5s"]}
        valid = {
            "normalized_final_answer_score": 1,
            "observed_execution_owner": "3l5s",
            "primitive_obligation_results": [
                {"primitive_id": "input_framing_audit", "satisfied": True}
            ],
            "unexpected_primitive_actions": [],
            "false_wakeup_final_answer": False,
            "required_visible_action_present": True,
            "authority_or_evidence_regression": False,
            "clarification_turns": 0,
            "rationale": "The answer defines the failure before decomposition.",
        }
        normalized = self.runner.validate_judge_output(valid, case)
        self.assertTrue(normalized["owner_success"])
        self.assertTrue(normalized["joint_owner_primitive_success"])
        invalid = dict(valid)
        invalid["primitive_obligation_results"] = []
        with self.assertRaisesRegex(ValueError, "primitive result ids differ"):
            self.runner.validate_judge_output(invalid, case)
        invalid_score = dict(valid)
        invalid_score["normalized_final_answer_score"] = True
        with self.assertRaisesRegex(ValueError, "quality score"):
            self.runner.validate_judge_output(invalid_score, case)

    def test_injection_fidelity_requires_one_bound_receipt(self) -> None:
        digest = "a" * 64
        cell = {
            "arm_id": "thin-kernel",
            "telemetry": {
                "measurements": {
                    "arm.hook_observation_receipt": {
                        "value": digest,
                        "provenance": "deterministic",
                    },
                    "hook_state": {"value": "fired"},
                    "lifecycle_event": {"value": ["session-start"]},
                }
            },
        }
        self.assertEqual(self.analyzer.injection_fidelity([cell]), (True, 1))
        changed = json.loads(json.dumps(cell))
        changed["telemetry"]["measurements"]["arm.hook_observation_receipt"][
            "value"
        ] = None
        self.assertEqual(self.analyzer.injection_fidelity([changed]), (False, 1))

    def test_required_entry_stratum_can_fail_a_passing_overall_line(self) -> None:
        rows = [
            {
                "entry_mode": "dominant-mode",
                "stable": {"latency": 10.0},
                "thin-kernel": {"latency": 5.0},
            }
            for _ in range(21)
        ]
        rows.append(
            {
                "entry_mode": "failing-mode",
                "stable": {"latency": 10.0},
                "thin-kernel": {"latency": 10.0},
            }
        )
        result = self.analyzer.stratified_latency(
            rows,
            endpoint_id="fixture-latency",
            metric="latency",
            left="thin-kernel",
            right="stable",
        )
        self.assertEqual(result["overall_decision"], "pass")
        self.assertEqual(result["decision"], "fail")
        self.assertEqual(
            next(
                item
                for item in result["entry_mode_results"]
                if item["entry_mode"] == "failing-mode"
            )["decision"],
            "fail",
        )

    def test_retained_cell_revalidates_external_answer_and_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            cell_id = "c" * 64
            attempt_path = out / "generation-attempts" / cell_id / "attempt-01"
            attempt_path.mkdir(parents=True)
            answer = "bounded answer\n"
            answer_path = attempt_path / "answer.txt"
            answer_path.write_text(answer, encoding="utf-8")
            attempt = {
                "counted_tokens": 12,
                "returncode": 0,
                "timed_out": False,
                "answer_present": True,
                "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
            }
            attempt["attempt_digest"] = self.runner.canonical_sha256(attempt)
            (attempt_path / "attempt.json").write_text(
                json.dumps(attempt), encoding="utf-8"
            )
            record = {
                "schema_version": "mindthus-beta2-real-cell-v0.4",
                "cell_id": cell_id,
                "cell_key": {"fixture": True},
                "generation_attempt": {
                    "attempt": 1,
                    "attempt_digest": attempt["attempt_digest"],
                    "path": str(attempt_path),
                },
                "answer_path": str(answer_path),
                "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
                "counted_tokens": 12,
            }
            record["record_digest"] = self.runner.canonical_sha256(record)
            record_path = out / "cells" / cell_id / "record.json"
            record_path.parent.mkdir(parents=True)
            record_path.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(self.runner.completed_cell(out, cell_id)["cell_id"], cell_id)
            answer_path.write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(self.runner.EvaluationStop):
                self.runner.completed_cell(out, cell_id)

    def test_retained_judge_revalidates_output_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            output_id = "d" * 64
            attempt_path = (
                out / "judge-attempts" / output_id / "slot-1" / "attempt-01"
            )
            attempt_path.mkdir(parents=True)
            raw_output = "{}\n"
            output_path = attempt_path / "judge-output.json"
            output_path.write_text(raw_output, encoding="utf-8")
            attempt = {
                "counted_tokens": 8,
                "returncode": 0,
                "timed_out": False,
                "output_present": True,
                "parse_error": None,
                "output_sha256": hashlib.sha256(raw_output.encode("utf-8")).hexdigest(),
            }
            attempt["attempt_digest"] = self.runner.canonical_sha256(attempt)
            (attempt_path / "attempt.json").write_text(
                json.dumps(attempt), encoding="utf-8"
            )
            record = {
                "blinded_output_id": output_id,
                "judge_slot": 1,
                "attempt": 1,
                "attempt_digest": attempt["attempt_digest"],
                "counted_tokens": 8,
            }
            record["record_digest"] = self.runner.canonical_sha256(record)
            record_path = out / "judge-records" / output_id / "judge-1.json"
            record_path.parent.mkdir(parents=True)
            record_path.write_text(json.dumps(record), encoding="utf-8")
            self.assertEqual(
                self.runner.existing_judge_record(out, output_id, 1)["judge_slot"], 1
            )
            output_path.write_text("{\"changed\":true}\n", encoding="utf-8")
            with self.assertRaises(self.runner.EvaluationStop):
                self.runner.existing_judge_record(out, output_id, 1)

    def test_v02_hook_receipt_is_bound_without_model_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            (package / "runtime").mkdir(parents=True)
            kernel = "# Passive Kernel\n\nKeep the boundary.\n"
            (package / "runtime" / "passive-activation-kernel.md").write_text(
                kernel, encoding="utf-8"
            )
            canonical_digest = hashlib.sha256(
                self.probe.canonical_kernel_text(kernel).encode("utf-8")
            ).hexdigest()
            receipt = {
                "schema_version": "mindthus-beta2-host-hook-observation-v0.2",
                "status": "observed-fired",
                "expected_kernel_state": "present",
                "observed_kernel_state": "present",
                "package_tree_sha256": self.materializer.tree_sha256(package),
                "model_execution_performed": False,
                "semantic_output_generated": False,
                "hook_trust_bypassed_for_vetted_package": True,
                "kernel_sha256": hashlib.sha256(kernel.encode("utf-8")).hexdigest(),
                "kernel_canonical_sha256": canonical_digest,
                "captured_kernel_canonical_sha256": canonical_digest,
                "network_scope": "127.0.0.1-only model endpoint",
                "request_content_retained": False,
                "matching_request_count": 1,
            }
            receipt["receipt_digest"] = self.materializer.canonical_sha256(receipt)
            path = root / "receipt.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            validated = self.materializer.validate_thin_receipt(path, package)
            self.assertFalse(validated["model_execution_performed"])
            absent = dict(receipt)
            absent.update(
                {
                    "status": "observed-absent",
                    "expected_kernel_state": "absent",
                    "observed_kernel_state": "absent",
                    "hook_trust_bypassed_for_vetted_package": False,
                    "captured_kernel_canonical_sha256": None,
                }
            )
            absent.pop("receipt_digest")
            absent["receipt_digest"] = self.materializer.canonical_sha256(absent)
            path.write_text(json.dumps(absent), encoding="utf-8")
            validated_absent = self.materializer.validate_direct_absence_receipt(
                path, package
            )
            self.assertEqual(validated_absent["status"], "observed-absent")

    def test_hook_body_fidelity_ignores_only_transport_boundary_newlines(self) -> None:
        kernel = "# Kernel\n\nBody\n"
        captured = "\r\n# Kernel\r\n\r\nBody\r\n"
        self.assertEqual(
            self.probe.canonical_kernel_text(kernel),
            self.probe.canonical_kernel_text(captured),
        )
        self.assertNotEqual(
            self.probe.canonical_kernel_text(kernel),
            self.probe.canonical_kernel_text("\n# Kernel\n\nChanged\n"),
        )


if __name__ == "__main__":
    unittest.main()
