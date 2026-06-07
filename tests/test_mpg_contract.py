import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MPG_SKILL = REPO / "skills" / "mpg" / "SKILL.md"
MPG_RESOURCE = REPO / "skills" / "mpg" / "resources" / "methodology.md"
MPG_DOC = REPO / "docs" / "methodologies" / "mpg.md"
MPG_PRESSURE = REPO / "tests" / "mpg" / "pressure_tests.md"


class MpgContractTests(unittest.TestCase):
    def test_mpg_skill_and_methodology_define_core_output_contract(self):
        for path in (MPG_SKILL, MPG_RESOURCE, MPG_DOC):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "MPG / Mainline-Path Game",
                "主线-路径博弈",
                "Path-Carrying Strategy / 主线承载方案",
                "qualified_mainline",
                "carrier_vehicle",
                "counter_force_map",
                "exposure_budget",
                "optionality_design",
                "action_posture",
                "trigger_conditions",
                "mainline_challenge",
                "看对主线，不等于穿过路径",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_mpg_qualifies_mainline_and_can_challenge_sela(self):
        text = MPG_RESOURCE.read_text(encoding="utf-8")
        for phrase in (
            "Mainline Qualification / 主趋势限定化",
            "naked mainline",
            "qualified mainline",
            "MPG can challenge",
            "SELA identifies the mainline",
            "MPG qualifies, stress-tests, and carries",
            "return to SELA or EDSP",
            "constrained mainline",
        ):
            self.assertIn(phrase, text)

    def test_mpg_has_boundaries_against_router_overuse(self):
        text = MPG_SKILL.read_text(encoding="utf-8")
        for phrase in (
            "Do not use MPG without a carrier",
            "If the mainline itself is unclear",
            "use EDSP",
            "Evidence / Claim Ceiling",
            "Use SELA",
            "Use WAE",
            "counter-forces are not bad by default",
            "survival alone is not success",
        ):
            self.assertIn(phrase, text)

    def test_mpg_pressure_tests_cover_cases_and_boundaries(self):
        text = MPG_PRESSURE.read_text(encoding="utf-8")
        for phrase in (
            "Scenario 1: AI Stock Carrier Drawdown",
            "Scenario 2: Central-Local Governance",
            "Scenario 3: Company Transformation Cashflow",
            "Scenario 4: Technology Migration Carrier Risk",
            "Scenario 5: Naked Mainline Skips MPG",
            "Scenario 6: Missing Evidence Blocks MPG",
            "Scenario 7: Pure Control Boundary Routes To WAE",
            "Scenario 8: Constrained Mainline Challenge",
            "Expected treatment behavior",
            "Path-Carrying Strategy",
        ):
            self.assertIn(phrase, text)

    def test_using_mindthus_routes_mpg_without_displacing_sela(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "Qualified mainline with path/counter-force exposure",
            "`mpg`",
            "Long-term system efficiency versus local advantage",
            "SELA identifies direction; MPG carries it through path volatility",
            "Do not use MPG when there is no actor, carrier, exposure, or path decision.",
        ):
            self.assertIn(phrase, text)
        for phrase in (
            "MPG",
            "主线-路径博弈",
            "主线承载方案",
            "SELA 看整体趋势",
        ):
            self.assertIn(phrase, agents)


if __name__ == "__main__":
    unittest.main()
