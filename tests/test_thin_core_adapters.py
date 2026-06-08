import importlib.util
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def import_tplan_runtime():
    path = REPO / "skills" / "tplan" / "scripts" / "tplan_runtime.py"
    spec = importlib.util.spec_from_file_location("tplan_runtime_for_thin_core_tests", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ThinCoreAdapterTests(unittest.TestCase):
    def test_thin_core_modules_are_adapter_neutral(self):
        shape = REPO / "skills" / "_runtime" / "core" / "shape.py"
        report = REPO / "skills" / "_runtime" / "core" / "report.py"

        for path in (shape, report):
            self.assertTrue(path.exists(), path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("Finding", text)
            self.assertIn("semantic", text)
            for forbidden in (
                "FidelitySpec",
                "applicability",
                "action_posture",
                "required_judgment_moves",
                "validate_mission",
                "human_in_loop",
                "apply_mutation",
            ):
                self.assertNotIn(forbidden, text)

    def test_fidelity_adapter_reuses_thin_core_without_losing_method_contract(self):
        text = (REPO / "skills" / "_runtime" / "fidelity" / "core.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("_runtime.core.report", text)
        self.assertIn("_runtime.core.shape", text)
        self.assertIn("FidelitySpec", text)
        self.assertIn("applicability", text)
        self.assertIn("required_judgment_moves", text)

    def test_tplan_hook_adapter_reuses_thin_core_without_fidelity_adapter(self):
        text = (REPO / "skills" / "tplan" / "scripts" / "tplan_runtime.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("_runtime.core.report", text)
        self.assertIn("_runtime.core.shape", text)
        self.assertIn("validate_hook_output_findings", text)
        self.assertNotIn("_runtime.fidelity.core", text)
        self.assertNotIn("FidelitySpec", text)

    def test_tplan_hook_findings_companion_preserves_legacy_errors(self):
        runtime = import_tplan_runtime()
        decision = {
            "recommendation": "switch",
            "rationale": "Switching active tasks is high-impact.",
            "confidence": 80,
            "evidence_links": [],
            "proposed_mutations": [
                {"type": "set_active_task", "task_id": "T2"},
            ],
            "requires_human": False,
            "mission_alignment": "Switching to T2 advances runtime usability.",
        }

        findings = runtime.validate_hook_output_findings(decision)
        messages = [finding.message for finding in findings]

        self.assertIn("decision missing field: path_assessment", messages)
        self.assertEqual(runtime.validate_hook_output(decision), messages)


if __name__ == "__main__":
    unittest.main()
