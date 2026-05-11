import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WAE = REPO / "skills" / "wae"


class WaeContractTests(unittest.TestCase):
    def test_skill_names_core_risk_modulators_and_human_escalation(self):
        text = (WAE / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Workflow should control order",
            "Agentic reasoning should resolve uncertainty",
            "Evidence should connect claims to observable proof",
            "Risk Modulators",
            "reversibility",
            "blast radius",
            "Tool Tier",
            "Human Escalation",
            "Human is not a routine control layer",
            "Instruction/Data Boundary",
        ):
            self.assertIn(phrase, text)

    def test_methodology_covers_runtime_governance(self):
        text = (WAE / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Reversibility And Blast Radius",
            "Tool Tier",
            "Invocation Context Tightening",
            "Human Escalation",
            "Human Escalation Packet",
            "Fallback Ladder",
            "Failure Attribution",
            "Promotion And Demotion",
            "Skill Boundary Conflict",
            "Boundary Assumptions And Expiry Signals",
        ):
            self.assertIn(phrase, text)

    def test_worksheet_records_operational_risk_and_fallback(self):
        text = (WAE / "templates" / "control-boundary-worksheet.md").read_text(encoding="utf-8")
        for phrase in (
            "Reversibility",
            "Blast radius",
            "Tool tier",
            "Invocation context",
            "Instruction/data boundary",
            "Human escalation",
            "Fallback path",
            "Promotion or demotion signal",
        ):
            self.assertIn(phrase, text)

    def test_skill_exposes_minimal_check_to_prevent_ceremony(self):
        text = (WAE / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Minimal WAE Check",
            "path or truth",
            "Does the claim need evidence",
            "Is the action reversible",
            "Only enter the full WAE flow",
        ):
            self.assertIn(phrase, text)

    def test_methodology_defines_claim_granularity_and_evidence_reporting(self):
        text = (WAE / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Minimal WAE Check",
            "A `claim` is the smallest statement whose error would change a downstream decision",
            "Evidence Reporting Contract",
            "used tool tiers",
            "fallback layer reached",
            "unresolved uncertainty",
            "side effects not visible to the caller",
        ):
            self.assertIn(phrase, text)

    def test_methodology_attributes_risk_modulator_failures(self):
        text = (WAE / "resources" / "methodology.md").read_text(encoding="utf-8")
        for name in (
            "Reversibility misjudgment",
            "Tool tier misclassification",
            "Context tightening skipped",
            "Instruction/data leak",
        ):
            self.assertGreaterEqual(text.count(f"`{name}`"), 2)

    def test_methodology_bounds_loops_and_records_explicit_relaxation(self):
        text = (WAE / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "explicit resource budgets",
            "iterations, tool calls, time, and retries",
            "Explicit Relaxation",
            "granting authority, scope, and expiry",
            "Default relaxation is not allowed",
        ):
            self.assertIn(phrase, text)

    def test_worksheet_records_nested_reporting_and_loop_budget(self):
        text = (WAE / "templates" / "control-boundary-worksheet.md").read_text(encoding="utf-8")
        for phrase in (
            "Loop budget",
            "iterations",
            "tool calls",
            "Evidence reporting",
            "used tool tiers",
            "fallback layer reached",
            "Explicit relaxation",
            "granting authority",
            "expiry",
        ):
            self.assertIn(phrase, text)

    def test_deep_material_is_not_default_path(self):
        skill = (WAE / "SKILL.md").read_text(encoding="utf-8")
        methodology = (WAE / "resources" / "methodology.md").read_text(encoding="utf-8")
        worksheet = (WAE / "templates" / "control-boundary-worksheet.md").read_text(encoding="utf-8")

        for phrase in (
            "Default path is the Minimal WAE Check",
            "Do not open the worksheet by default",
            "Open the full method only when",
        ):
            self.assertIn(phrase, skill)

        for phrase in (
            "Full Method Is Not The Default Path",
            "Stop after the minimal check",
            "Do not run every section",
        ):
            self.assertIn(phrase, methodology)

        for phrase in (
            "This worksheet is not the default path",
            "Do not fill every field",
            "Fill only fields that can change the control decision",
        ):
            self.assertIn(phrase, worksheet)

    def test_wae_keeps_mainline_clear_and_branches_triggered(self):
        skill = (WAE / "SKILL.md").read_text(encoding="utf-8")
        methodology = (WAE / "resources" / "methodology.md").read_text(encoding="utf-8")
        worksheet = (WAE / "templates" / "control-boundary-worksheet.md").read_text(encoding="utf-8")

        for phrase in (
            "Escalated Flow",
            "Use this only when the Minimal WAE Check is insufficient",
        ):
            self.assertIn(phrase, skill)

        for phrase in (
            "Worksheet Use Is Triggered",
            "Do not copy the whole worksheet into routine answers",
        ):
            self.assertIn(phrase, methodology)

        for phrase in (
            "Required Minimal Fields",
            "Expanded Fields",
            "Skip any expanded field",
            "Expansion trigger",
        ):
            self.assertIn(phrase, worksheet)


if __name__ == "__main__":
    unittest.main()
