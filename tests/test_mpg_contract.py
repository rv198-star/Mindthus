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

    def test_mpg_output_is_human_readable_before_internal_fields(self):
        for path in (MPG_SKILL, MPG_RESOURCE, MPG_DOC):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "Human-Readable First / 先讲人话",
                "先给人看的判断，再给机器看的字段",
                "Do not expose MPG internal field names before the plain-language conclusion",
                "一句话判断",
                "普通人能复述",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_mpg_scores_reasoning_durability_not_outcome_hindsight(self):
        for path in (MPG_SKILL, MPG_RESOURCE, MPG_DOC):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "Reasoning Durability / 推演耐久性",
                "结果不准不必然失败",
                "信息不全",
                "当时信息面",
                "later outcome is not the score",
                "trigger conditions should explain when a later result changed the judgment",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_mpg_uses_approximate_quantified_mapping_as_visibility_layer(self):
        for path in (MPG_SKILL, MPG_RESOURCE, MPG_DOC):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "MPG-AQM Visibility Layer / 主线-路径显影层",
                "Approximate Quantified Mapping",
                "非精准量化显影",
                "MPG owns the judgment",
                "AQM only makes variables visible",
                "do not calculate the decision",
                "数字是假设，关系才是重点",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

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
            "Scenario 9: War Of Resistance Time-Slice",
            "Scenario 10: Stock Playback Reasoning Durability",
            "exclude future information",
            "plain-language conclusion",
            "later outcome is not the score",
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
            "MPG vs AQM",
            "MPG owns the judgment; Approximate Quantified Mapping only makes variables visible.",
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
