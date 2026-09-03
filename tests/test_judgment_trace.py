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
    JUDGMENT_TRACE_SCHEMA_VERSION,
    LEGACY_JUDGMENT_TRACE_SCHEMA_VERSION,
    TraceValidationError,
    load_judgment_trace,
    validate_judgment_trace,
    validate_judgment_trace_or_raise,
)


FIXTURES = REPO / "skills" / "_runtime" / "judgment" / "fixtures" / "traces"
VALIDATOR = REPO / "scripts" / "validate-judgment-trace.py"
SCHEMAS = REPO / "skills" / "_runtime" / "judgment" / "resources"


class JudgmentTraceTests(unittest.TestCase):
    def test_current_and_legacy_trace_fixtures_validate(self):
        names = {path.name for path in FIXTURES.glob("*.json")}
        self.assertEqual(
            names,
            {
                "direct-execution.json",
                "information-acquisition.json",
                "intervention.json",
                "legacy-v1.json",
            },
        )
        for name in ("direct-execution.json", "information-acquisition.json", "intervention.json"):
            with self.subTest(path=name):
                trace = load_judgment_trace(FIXTURES / name)
                self.assertEqual(trace["schema_version"], JUDGMENT_TRACE_SCHEMA_VERSION)
                self.assertIn("field_sources", trace["provenance"])
                self.assertIn("basis", trace["decision_delta"])
                self.assertIn("comparison_ref", trace["decision_delta"])
        legacy = load_judgment_trace(FIXTURES / "legacy-v1.json")
        self.assertEqual(legacy["schema_version"], LEGACY_JUDGMENT_TRACE_SCHEMA_VERSION)

    def test_current_schema_alias_matches_v11_and_legacy_schema_is_preserved(self):
        current = json.loads((SCHEMAS / "judgment-trace.schema.json").read_text(encoding="utf-8"))
        explicit = json.loads((SCHEMAS / "judgment-trace-v1.1.schema.json").read_text(encoding="utf-8"))
        legacy = json.loads((SCHEMAS / "judgment-trace-v1.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(current, explicit)
        self.assertEqual(current["properties"]["schema_version"]["const"], JUDGMENT_TRACE_SCHEMA_VERSION)
        self.assertEqual(
            legacy["properties"]["schema_version"]["const"],
            LEGACY_JUDGMENT_TRACE_SCHEMA_VERSION,
        )

    def test_current_trace_accepts_sra_as_judgment_owner_and_selected_method(self):
        trace = json.loads((FIXTURES / "intervention.json").read_text(encoding="utf-8"))
        trace["routing"]["judgment_owner"] = "sra"
        trace["routing"]["selected_method"] = "sra"
        trace["routing"]["loaded_methods"] = ["using-mindthus", "sra"]
        trace["input_shape"]["judgment_object"] = "decision_context"

        self.assertEqual(validate_judgment_trace(trace), [])

    def test_v11_validator_rejects_private_transcript_and_malformed_delta(self):
        trace = json.loads((FIXTURES / "intervention.json").read_text(encoding="utf-8"))
        trace["raw_prompt"] = "private prompt"
        trace["decision_delta"]["next_action_changed"] = "yes"

        findings = validate_judgment_trace(trace)
        codes = {item.code for item in findings}

        self.assertIn("unknown-field", codes)
        self.assertIn("prohibited-field", codes)
        self.assertIn("invalid-delta-state", codes)
        with self.assertRaises(TraceValidationError):
            validate_judgment_trace_or_raise(trace)

    def test_v11_requires_comparison_reference_for_comparative_basis(self):
        trace = json.loads((FIXTURES / "intervention.json").read_text(encoding="utf-8"))
        trace["decision_delta"]["basis"] = "baseline_comparison"
        trace["decision_delta"]["comparison_ref"] = None

        findings = validate_judgment_trace(trace)

        self.assertTrue(any(item.code == "comparison-ref-required" for item in findings))

    def test_v11_accepts_comparative_basis_with_reference_and_known_source(self):
        trace = json.loads((FIXTURES / "intervention.json").read_text(encoding="utf-8"))
        trace["decision_delta"]["basis"] = "baseline_comparison"
        trace["decision_delta"]["comparison_ref"] = "benchmark-run:baseline-vs-treatment"
        trace["provenance"]["field_sources"]["decision_delta.comparison_ref"] = "author_annotation"

        self.assertEqual(validate_judgment_trace(trace), [])

    def test_v11_requires_sources_for_critical_fields(self):
        trace = json.loads((FIXTURES / "intervention.json").read_text(encoding="utf-8"))
        del trace["provenance"]["field_sources"]["decision_delta.next_action_changed"]

        findings = validate_judgment_trace(trace)

        self.assertTrue(any(item.code == "missing-field-source" for item in findings))

    def test_v11_blocks_assessed_delta_with_unknown_source(self):
        trace = json.loads((FIXTURES / "intervention.json").read_text(encoding="utf-8"))
        trace["provenance"]["field_sources"]["decision_delta.next_action_changed"] = "unknown"

        findings = validate_judgment_trace(trace)

        self.assertTrue(any(item.code == "source-value-mismatch" for item in findings))

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
        self.assertTrue(trace["decision_delta"]["evidence_requirement_changed"])
        self.assertEqual(trace["decision_delta"]["strategy_changed"], "unknown")

    def test_benchmark_adapter_records_observed_method_evaluator_basis_and_unknowns(self):
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

        self.assertEqual(trace["schema_version"], JUDGMENT_TRACE_SCHEMA_VERSION)
        self.assertEqual(trace["routing"]["selected_method"], "using-mindthus")
        self.assertEqual(trace["routing"]["routing_decision"], "intervene")
        self.assertEqual(trace["decision_delta"]["basis"], "single_output_evaluator")
        self.assertIsNone(trace["decision_delta"]["comparison_ref"])
        self.assertTrue(trace["decision_delta"]["next_action_changed"])
        self.assertTrue(trace["decision_delta"]["evidence_requirement_changed"])
        self.assertEqual(trace["decision_delta"]["strategy_changed"], "unknown")
        self.assertEqual(trace["decision_delta"]["handoff_changed"], "unknown")
        self.assertEqual(
            trace["provenance"]["field_sources"]["routing.loaded_methods"],
            "runtime_observation",
        )
        self.assertEqual(
            trace["provenance"]["field_sources"]["decision_delta.strategy_changed"],
            "unknown",
        )
        self.assertIn("not a baseline comparison", trace["evidence"]["claim_ceiling"])

    def test_benchmark_absent_delta_label_stays_unknown_not_false(self):
        trace = judgment_trace_from_benchmark(
            {
                "case_id": "mtj-direct",
                "case_type": "negative_control",
                "expected_owner": "direct_execution",
                "stay_asleep_expected": True,
            },
            {"case_id": "mtj-direct", "variant": "fixture"},
            {
                "case_id": "mtj-direct",
                "score": 2,
                "variant": "fixture",
                "loaded_owner": [],
                "required_visible_action_present": None,
            },
        )

        self.assertTrue(
            all(
                trace["decision_delta"][field] == "unknown"
                for field in (
                    "strategy_changed",
                    "risk_handling_changed",
                    "evidence_requirement_changed",
                    "next_action_changed",
                    "stopping_condition_changed",
                    "handoff_changed",
                )
            )
        )

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
            trace = load_judgment_trace(trace_path)
            self.assertEqual(trace["schema_version"], JUDGMENT_TRACE_SCHEMA_VERSION)
            self.assertEqual(trace["routing"]["routing_decision"], "direct_execute")
            self.assertEqual(len(index_path.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
