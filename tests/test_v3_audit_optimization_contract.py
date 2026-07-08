import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def compact(path: str) -> str:
    return " ".join(read(path).split())


class V3AuditOptimizationContractTests(unittest.TestCase):
    def test_using_mindthus_has_thin_before_route_entry_triage_index(self):
        text = read("skills/using-mindthus/SKILL.md")
        for phrase in (
            "Entry Triage / 入口分诊",
            "semantic families in shared-primitives",
            "not keywords",
        ):
            self.assertIn(phrase, text)

    def test_entry_triage_doc_registers_v3_trigger_families_with_guardrails(self):
        text = compact("docs/methodologies/primitives/entry-triage.md").lower()
        for phrase in (
            "definition authority contest",
            "single-factor attribution",
            "local repair spiral",
            "forced binary prediction",
            "no-data numeric comparison",
            "trend-driven migration",
            "green tests imply release readiness",
            "X is just Y, therefore impossible",
            "business success reduced to one factor",
            "third prompt rule or third fallback",
            "who is right plus active buy or decide context",
            "hypothetical numbers must not decide",
            "negative and shadow controls",
            "v5/#104 no-load stabilization register",
            "authority or tenure used as root-cause proof plus requested incident write-up",
            "trend label used as migration mandate",
            "local green signal treated as release authorization",
            "business/store success reduced to one product attribute before copywriting",
            "forced yes/no replacement prediction over role/task family",
            "third local prompt rule after two failed edits",
            "third fallback branch after two fallbacks or unstable tests",
            "definition/essence reduction to communication/tactic only",
            "no measured data plus concrete numeric risk comparison",
        ):
            self.assertIn(phrase.lower(), text)

    def test_entry_triage_doc_clarifies_edsp_sela_aqm_ownership(self):
        text = compact("docs/methodologies/primitives/entry-triage.md").lower()
        for phrase in (
            "EDSP owns bare A/B structural choice",
            "SELA owns local expertise versus automation scale",
            "if both appear, EDSP exposes the axis before SELA checks system efficiency",
            "AQM stays inside the active judgment owner",
            "invented arithmetic must not become the decision basis",
        ):
            self.assertIn(phrase.lower(), text)

    def test_entry_triage_doc_contains_loaded_behavior_gates(self):
        text = compact("docs/methodologies/primitives/entry-triage.md").lower()
        for phrase in (
            "root-cause evidence gate",
            "timeline and metrics before conclusion",
            "same local repair count >= 3",
            "must stop adding and move upstream or equal-replace",
            "visible consequence probe",
        ):
            self.assertIn(phrase.lower(), text)

    def test_entry_triage_separates_no_load_triggers_from_loaded_action_probes(self):
        entry = compact("docs/methodologies/primitives/entry-triage.md")
        contract = compact("skills/using-mindthus/resources/fidelity-contract.md")

        self.assertIn("third prompt rule, third fallback, or next local patch after instability", entry)
        self.assertIn("Anti-Spiral hard brake", entry)
        self.assertIn("anti_spiral_brake_before_addition", contract)
        self.assertIn("loaded owners must put the case-critical action into visible prose", contract)

    def test_manifest_exposes_entry_triage_to_primitive_activation(self):
        text = read("scripts/primitives/manifest.json")
        for phrase in (
            '"entry_triage"',
            "definition authority contest",
            "single-factor attribution",
            "local repair spiral",
            "forced binary prediction",
            "no-data numeric comparison",
            "trend-driven migration",
            "which_entry_triage_family_if_any",
        ):
            self.assertIn(phrase, text)

    def test_latest_links_external_audit_handoff(self):
        latest = read("docs/benchmarks/latest.md")
        self.assertIn("EXTERNAL_AUDIT_HANDOFF.md", latest)

    def test_external_handoff_records_v4_measurement_follow_up(self):
        handoff = read(
            "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/"
            "EXTERNAL_AUDIT_HANDOFF.md"
        )
        for phrase in (
            "V4 Measurement Follow-Up Requested By Audit",
            "judge calibration examples",
            "Repeat-run moved or borderline cases",
            "fixture diff explanation",
            "judge model and blind-grading setup",
            "baseline loaded command",
            "shadow-set regression as a certification veto",
        ):
            self.assertIn(phrase, handoff)


if __name__ == "__main__":
    unittest.main()
