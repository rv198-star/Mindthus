import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills"))

from _runtime.judgment.benchmark import (  # noqa: E402
    judgment_trace_from_benchmark,
    write_benchmark_judgment_traces,
)
from _runtime.judgment.trace import (  # noqa: E402
    TraceValidationError,
    load_judgment_trace,
    validate_judgment_trace,
    validate_judgment_trace_or_raise,
)


FIXTURES = REPO / "skills" / "_runtime" / "judgment" / "fixtures" / "traces"
VALIDATOR = REPO / "scripts" / "validate-judgment-trace.py"


class JudgmentTraceTests(unittest.TestCase):
    def test_three_canonical_trace_fixtures_validate(self):
        names = {path.name for path in FIXTURES.glob("*.json")}
        self.assertEqual(
            names,
            {"direct-execution.json", "information-acquisition.json", "intervention.json"},
        )
        for path in sorted(FIXTURES.glob("*.json")):
            with self.subTest(path=path.name):
                trace = load_judgment_trace(path)
                self.assertEqual(trace["schema_version"], "mindthus.judgment-trace.v1")

    def test_validator_rejects_private_transcript_and_malformed_delta(self):
        trace = json.loads((FIXTURES / "intervention.json").read_text(encoding="utf-8"))
        trace["raw_prompt"] = "private prompt"
        trace["decision_delta"]["next_action_changed"] = "yes"

        findings = validate_judgment_trace(trace)
        codes = {item.code for item in findings}

        self.assertIn("unknown-field", codes)
        self.assertIn("prohibited-field", codes)
        self.assertIn("invalid-field", codes)
        with self.assertRaises(TraceValidationError):
            validate_judgment_trace_or_raise(trace)

    def test_tplan_runtime_state_is_not_part_of_judgment_trace(self):
        trace = json.loads((FIXTURES / "intervention.json").read_text(encoding="utf-8"))
        trace["mission"] = {"mission_id": "M1", "tasks": []}

        findings = validate_judgment_trace(trace)
        messages = [item.message for item in findings]

        self.assertTrue(any("mission" in message for message in messages))
        self.assertTrue(any(item.code == "prohibited-field" for item in findings))

    def test_cli_emits_shape_only_report(self):
        result = subprocess.run(
            ["python3", str(VALIDATOR), str(FIXTURES / "direct-execution.json"), "--json"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "valid")
        self.assertIn("does not prove judgment correctness", report["truth_boundary"])

    def test_benchmark_information_acquisition_is_not_hard_judgment(self):
        trace = judgment_trace_from_benchmark(
            {
                "case_id": "mtj-info",
                "case_type": "positive",
                "expected_owner": "information_acquisition",
                "stay_asleep_expected": False,
            },
            {
                "case_id": "mtj-info",
                "variant": "fixture",
                "generated_at_utc": "2026-08-06T00:00:00+00:00",
            },
            {
                "case_id": "mtj-info",
                "score": 2,
                "variant": "fixture",
                "judged_at_utc": "2026-08-06T00:01:00+00:00",
                "loaded_owner": [],
                "required_visible_action_present": True,
            },
        )

        self.assertEqual(trace["routing"]["routing_decision"], "acquire_information")
        self.assertEqual(trace["routing"]["judgment_owner"], "information_acquisition")
        self.assertFalse(trace["input_shape"]["hard_judgment_point"])

    def test_benchmark_adapter_records_observed_method_and_evaluator_boundary(self):
        case = {
            "case_id": "mtj-fixture",
            "case_type": "positive",
            "expected_owner": "whole_elephant",
            "stay_asleep_expected": False,
        }
        response = {
            "case_id": "mtj-fixture",
            "variant": "fixture",
            "generated_at_utc": "2026-08-06T00:00:00+00:00",
        }
        score = {
            "case_id": "mtj-fixture",
            "variant": "fixture",
            "score": 2,
            "loaded_owner": ["using-mindthus"],
            "required_visible_action_present": True,
            "judged_at_utc": "2026-08-06T00:00:01+00:00",
        }

        trace = judgment_trace_from_benchmark(case, response, score)

        self.assertEqual(trace["routing"]["selected_method"], "using-mindthus")
        self.assertEqual(trace["routing"]["routing_decision"], "intervene")
        self.assertTrue(trace["decision_delta"]["next_action_changed"])
        self.assertEqual(trace["provenance"]["source_type"], "mixed")
        self.assertIn("not proof", trace["evidence"]["claim_ceiling"])

    def test_benchmark_writer_emits_one_trace_per_judged_case(self):
        case = {
            "case_id": "mtj-fixture",
            "case_type": "negative_control",
            "expected_owner": "direct_execution",
            "stay_asleep_expected": True,
        }
        response = {
            "case_id": "mtj-fixture",
            "variant": "fixture",
            "generated_at_utc": "2026-08-06T00:00:00+00:00",
        }
        score = {
            "case_id": "mtj-fixture",
            "variant": "fixture",
            "score": 2,
            "loaded_owner": [],
            "required_visible_action_present": None,
            "judged_at_utc": "2026-08-06T00:00:01+00:00",
        }

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            traces = write_benchmark_judgment_traces(out_dir, [case], [response], [score])
            trace_path = out_dir / "judgment-traces" / "mtj-fixture.json"
            index_path = out_dir / "judgment-traces.jsonl"

            self.assertEqual(len(traces), 1)
            self.assertTrue(trace_path.is_file())
            self.assertTrue(index_path.is_file())
            self.assertEqual(load_judgment_trace(trace_path)["routing"]["routing_decision"], "direct_execute")
            self.assertEqual(len(index_path.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
