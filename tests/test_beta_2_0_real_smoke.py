import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
RUNNER_PATH = BETA_ROOT / "runtime" / "run-real-codex-smoke.py"
MATERIALIZER_PATH = BETA_ROOT / "runtime" / "materialize-real-codex-arm.py"
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.3.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoRealSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_module("beta2_real_smoke", RUNNER_PATH)
        cls.materializer = load_module("beta2_real_arm_materializer", MATERIALIZER_PATH)
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    def test_frozen_seed_produces_15_cells_and_expected_first_arm(self) -> None:
        cells = self.runner.smoke_cells(self.protocol)
        self.assertEqual(len(cells), 15)
        self.assertEqual(
            cells[0],
            {"case_id": "b2-dev-owner-3l5s", "arm_id": "direct-only", "repeat": 1},
        )
        for offset in range(0, 15, 3):
            self.assertEqual(
                {cell["arm_id"] for cell in cells[offset : offset + 3]},
                {"stable", "direct-only", "thin-kernel"},
            )

    def test_source_resolution_covers_every_visible_smoke_case(self) -> None:
        matrix = json.loads(self.runner.MATRIX_PATH.read_text(encoding="utf-8"))
        cases = self.runner.source_cases(matrix)
        self.assertTrue(set(self.protocol["workload"]["smoke_case_ids"]).issubset(cases))
        self.assertEqual(
            self.runner.user_prompt(cases["b2-dev-owner-3l5s"]["source"]),
            "一个工单反复被退回，但大家说不清到底失败在哪。先把问题定义成可验证对象，再给最小拆解。",
        )

    def test_event_parser_never_invents_native_first_action_timestamp(self) -> None:
        started = datetime(2026, 7, 17, 8, 0, 0, tzinfo=timezone.utc)
        stream = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "t1"}),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": "answer"},
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 10,
                            "cached_input_tokens": 2,
                            "output_tokens": 3,
                            "reasoning_output_tokens": 4,
                        },
                    }
                ),
            ]
        )
        evidence = self.runner.event_evidence(stream, started)
        self.assertEqual(evidence["native_telemetry"]["lifecycle_event"], ["session-start"])
        self.assertNotIn(
            "first_useful_action_latency_seconds", evidence["native_telemetry"]
        )
        self.assertEqual(self.runner.token_total(evidence["usage"]), 17)

    def test_event_parser_accepts_only_explicit_native_timestamp(self) -> None:
        started = datetime(2026, 7, 17, 8, 0, 0, tzinfo=timezone.utc)
        stream = json.dumps(
            {
                "type": "item.completed",
                "timestamp": "2026-07-17T08:00:01.250000+00:00",
                "item": {"type": "agent_message", "text": "answer"},
            }
        )
        evidence = self.runner.event_evidence(stream, started)
        self.assertEqual(
            evidence["native_telemetry"]["first_useful_action_latency_seconds"],
            1.25,
        )

    def test_thin_kernel_cannot_be_sealed_without_observed_hook_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                self.materializer.MaterializationError,
                "observed host-hook receipt",
            ):
                self.materializer.validate_thin_receipt(
                    Path(tmp) / "missing.json",
                    Path(tmp),
                )


if __name__ == "__main__":
    unittest.main()
