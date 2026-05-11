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


if __name__ == "__main__":
    unittest.main()
