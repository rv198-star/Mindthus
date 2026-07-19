import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MPG_SKILL = REPO / "skills" / "mpg" / "SKILL.md"
MPG_RESOURCE = REPO / "skills" / "mpg" / "resources" / "methodology.md"
MPG_DOC = REPO / "docs" / "methodologies" / "mpg.md"
MPG_PRESSURE = REPO / "tests" / "mpg" / "pressure_tests.md"
MPG_TWIN_LENS_BEHAVIOR = REPO / "tests" / "mpg" / "twin_lens_behavior_acceptance_cases.md"


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
            "SELA and MPG are sibling strategic lenses",
            "Common order: SELA calibrates direction before MPG tests carrier/path",
            "sequence, not hierarchy",
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

    def test_mpg_aqm_outputs_visible_snapshot_for_dominant_variable_requests(self):
        for path in (MPG_SKILL, MPG_RESOURCE, MPG_DOC):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "visible AQM snapshot / 显影快照",
                "variables are many",
                "not generic balance",
                "dominant factor",
                "after the one-sentence thesis",
                "mainline strength",
                "path resistance",
                "carrier fragility",
                "information gap",
                "trigger strength",
                "stage/probe, not commit",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_mpg_direct_load_runs_sela_support_check_for_trend_based_mainlines(self):
        for path in (MPG_SKILL, MPG_RESOURCE):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "SELA ↔ MPG Twin-Lens Handshake",
                "MPG direct-load companion check",
                "SELA support check",
                "must read `mindthus:sela`",
                "Do not treat this as an internal memory-only check",
                "system-efficiency/trend-based mainline",
                "SELA support + MPG dominate",
                "MPG still owns the action posture",
                "If the direction check fails, return to SELA or EDSP before path strategy",
                "include a short AQM visibility map or say why it",
                "Direct-load output obligation",
                "do not wait for using-mindthus to carry this handoff",
                "first visible sentence must be a plain-language thesis",
                "Default answer must not start",
                "debug/audit support",
                "ordinary language",
                "evidence-limited",
                "carrier/path",
                "visibly pull in different directions",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_public_methodology_explains_twin_lens_without_runtime_commands(self):
        text = MPG_DOC.read_text(encoding="utf-8")
        for phrase in (
            "SELA 先校准方向压力，MPG 再判断当前载体、暴露和路径动作",
            "姐妹镜头",
            "MPG 仍然拥有最终行动姿态",
            "supported、failed 还是",
            "MPG runtime surface",
        ):
            self.assertIn(phrase, text)
        for runtime_phrase in (
            "must read `mindthus:sela`",
            "Direct-load output obligation",
            "first visible sentence must",
            "Default answer must not start",
        ):
            self.assertNotIn(runtime_phrase, text)

    def test_mpg_discovers_proxy_carrier_concentrated_exposure_structure(self):
        for path in (MPG_SKILL, MPG_RESOURCE, MPG_DOC):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "mainline + proxy/carrier + concentrated exposure + now/continue/commit decision",
                "scarce resource",
                "purest carrier",
                "稀缺资源",
                "最纯载体",
                "not domain-specific",
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

    def test_sela_mpg_twin_lens_acceptance_is_behavioral_not_label_based(self):
        text = MPG_TWIN_LENS_BEHAVIOR.read_text(encoding="utf-8")
        for phrase in (
            "SELA-MPG Twin-Lens Behavior Acceptance Cases",
            "Behavior target, not dual skill discovery",
            "Do not judge by whether the answer names both skills",
            "SELA surface",
            "MPG dominate",
            "direction_calibration",
            "path_carrying_action",
            "support_lens_present",
            "execution_impact",
            "Twin Positives",
            "SELA-Only Controls",
            "MPG-Only Controls",
            "Skip Traps",
            "SubAgent smoke batch",
            "Open-source models keep improving",
            "internal model platform",
            "platform burns a full year of budget",
        ):
            self.assertIn(phrase, text)

    def test_using_mindthus_routes_mpg_as_sibling_to_sela(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        compact = " ".join(text.split())
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "Long-term system efficiency versus local advantage",
            "carrier/path action defers to MPG",
            "Mainline plus carrier, exposure, path volatility, and commitment",
            "no carrier/exposure/path, no MPG",
            "SELA owns direction pressure; MPG owns path-carrying action",
            "Approximate Quantified Mapping / 非精准量化显影",
            "must not prove facts or compute decisions",
        ):
            self.assertIn(phrase, compact)
        for phrase in (
            "MPG",
            "主线-路径博弈",
            "主线承载方案",
            "SELA 看整体趋势",
            "direction + carrier + visibility",
        ):
            self.assertIn(phrase, agents)


if __name__ == "__main__":
    unittest.main()
