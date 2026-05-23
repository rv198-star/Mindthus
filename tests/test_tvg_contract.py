import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TVG = REPO / "skills" / "tvg"


class TvgContractTests(unittest.TestCase):
    def test_skill_names_veto_constraints_and_auditor_separation(self):
        text = (TVG / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "veto_constraints",
            "explicit unacceptable states",
            "They are not value-gain axes",
            "must not exit as `freeze`",
            "independent_auditor",
            "separate generator work from the exit auditor",
            "create, waive, or satisfy veto constraints",
            "decide whether independent auditor separation is required",
        ):
            self.assertIn(phrase, text)

    def test_methodology_keeps_veto_constraints_outside_value_axes(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Thinking Value-Gain Methodology — Value-Oriented Deep Thinking（v0.3）",
            "not a generic improvement pass",
            "Veto Constraints",
            "not ordinary value-gain axes",
            "block exit even when the module has improved",
            "must not exit as `freeze`",
            "Do not turn broad good practice into a veto constraint",
            "independent auditor separation",
            "auditor` reads only the final module",
            "must not rewrite the module as part of the same audit",
        ):
            self.assertIn(phrase, text)

    def test_exit_audit_template_records_veto_and_independence(self):
        text = (TVG / "resources" / "exit-audit-template.md").read_text(encoding="utf-8")
        for phrase in (
            "Thinking Value-Gain Agentic Exit Audit Template（v0.3）",
            "audit_role",
            "auditor_independence",
            "Veto Constraints",
            "veto_constraint_result",
            "triggered_veto_constraints",
            "veto_resolution",
            "whether the audit was independent when independence was required",
        ):
            self.assertIn(phrase, text)

    def test_trace_init_accepts_veto_constraints_and_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            result = subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "release-note",
                    "--module-title",
                    "Release note",
                    "--module-type",
                    "review",
                    "--downstream-consumer",
                    "release reviewer",
                    "--freeze-granularity",
                    "section",
                    "--veto-constraint",
                    "must not claim production readiness without runtime proof",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            data = json.loads(trace.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "tvg-trace-v0.3")
            self.assertEqual(data["method_version"], "Thinking Value-Gain Methodology v0.3")
            self.assertEqual(
                data["value_gain"]["veto_constraints"],
                ["must not claim production readiness without runtime proof"],
            )
            self.assertIn("audit_role", data["agentic_exit_audit"])
            self.assertIn("auditor_independence", data["agentic_exit_audit"])
            self.assertIn("veto_constraint_result", data["agentic_exit_audit"])
            self.assertIn("veto_constraints", data["script_support"]["script_cannot_decide"])
            self.assertIn(
                "auditor_independence_requirement",
                data["script_support"]["script_cannot_decide"],
            )

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            self.assertIn("agentic audit is still required", validation.stdout)

    def test_trace_validation_rejects_invalid_audit_role_and_veto_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "handoff",
                    "--module-title",
                    "Handoff",
                    "--module-type",
                    "handoff",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            data = json.loads(trace.read_text(encoding="utf-8"))
            data["agentic_exit_audit"]["audit_role"] = "self-certified"
            data["agentic_exit_audit"]["veto_constraint_result"] = "passed"
            trace.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 1)
            self.assertIn("unsupported value 'self-certified'", validation.stdout)
            self.assertIn("unsupported value 'passed'", validation.stdout)

    def test_ab_pressure_tests_document_expected_before_after_failures(self):
        text = (REPO / "tests" / "tvg_ab_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "TVG A/B Pressure Tests",
            "A / baseline",
            "B / treatment",
            "Veto Constraint Blocks A Cleaner But Unsafe Freeze",
            "Independent Auditor Prevents Generator Self-Justification",
            "Expected baseline failure",
            "Expected v0.3 behavior",
            "must not exit if the handoff leaves blocking clients",
        ):
            self.assertIn(phrase, text)

    def test_ab_run_record_captures_mechanical_and_live_results(self):
        text = (REPO / "tests" / "tvg_ab_run_2026-05-23.md").read_text(encoding="utf-8")
        for phrase in (
            "TVG v0.2 -> v0.3 A/B Run Record",
            "Mechanical A/B",
            "Live Agent A/B",
            "Scenario 1 is useful as a regression check",
            "Scenario 2 confirms the intended behavioral difference",
            "audit_role=independent-auditor",
            "auditor_independence=separated-from-generator",
            "unacceptable states must be named and checked as veto constraints",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
