import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SELA = REPO / "skills" / "sela"


class SelaContractTests(unittest.TestCase):
    def test_skill_exposes_lightweight_timing_check(self):
        text = (SELA / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Timing Check",
            "时机检查",
            "临时保留",
            "锁死未来",
            "行动窗口",
            "not a new top-level principle",
        ):
            self.assertIn(phrase, text)

    def test_skill_exposes_single_agent_multi_role_sela(self):
        text = (SELA / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Multi-Role Check",
            "single-agent multi-role",
            "System Advocate",
            "Local Defender",
            "Timing Auditor",
            "separate agents are an escalation option, not the default",
            "efficiency judgment into an immediate action",
        ):
            self.assertIn(phrase, text)

    def test_methodology_keeps_timing_check_lightweight(self):
        text = (SELA / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "时机检查",
            "不是独立原则",
            "不是补一套人文价值观",
            "临时保留",
            "锁死未来",
            "行动窗口",
        ):
            self.assertIn(phrase, text)

    def test_timing_check_does_not_absorb_mpg_ready_path_questions(self):
        skill = (SELA / "SKILL.md").read_text(encoding="utf-8")
        methodology = (SELA / "resources" / "methodology.md").read_text(encoding="utf-8")

        for phrase in (
            "Timing Check is not a substitute for MPG",
            "carrier, exposure, path volatility, or concrete commitment",
            "transfer/degrade to MPG",
            "SELA must not absorb MPG-ready questions",
        ):
            self.assertIn(phrase, skill)

        for phrase in (
            "时机检查不能替代 MPG",
            "承载者、路径波动、暴露预算或具体承诺",
            "交给 MPG",
            "不能让 SELA 吞掉 MPG-ready 问题",
        ):
            self.assertIn(phrase, methodology)

    def test_sela_direct_load_runs_mpg_companion_check_for_path_commitments(self):
        for path in (
            SELA / "SKILL.md",
            SELA / "resources" / "methodology.md",
        ):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "SELA ↔ MPG Twin-Lens Handshake",
                "SELA direct-load companion check",
                "MPG companion check",
                "must read `mindthus:mpg`",
                "Do not treat this as an internal memory-only check",
                "carrier, exposure, path volatility, or continue/exit commitment",
                "SELA calibrates direction; MPG owns path-carrying action",
                "first visible sentence must be a plain-language thesis",
                "Default answer must not start",
                "debug/audit support",
                "ordinary language",
                "SELA dominate + MPG not yet",
                "carrier commitment",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_public_methodology_explains_handshake_without_runtime_commands(self):
        text = (REPO / "docs" / "methodologies" / "sela.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "SELA calibrates direction; MPG owns path-carrying action",
            "承载者、暴露",
            "SELA 说明方向压力，MPG 决定如何穿过路径",
            "不能从“方向可能正确”直接推出",
            "SELA runtime surface",
        ):
            self.assertIn(phrase, text)
        for runtime_phrase in (
            "must read `mindthus:mpg`",
            "first visible sentence must",
            "Default answer must not start",
            "debug labels",
        ):
            self.assertNotIn(runtime_phrase, text)

    def test_methodology_adds_role_pressure_without_efficiency_dogma(self):
        text = (SELA / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "单 Agent 多角色",
            "System Advocate",
            "Local Defender",
            "Timing Auditor",
            "效率至上主义",
            "commit / trial / hold / wait",
            "不默认拆成多个 Agent",
        ):
            self.assertIn(phrase, text)

    def test_public_methodology_mentions_three_role_pressure(self):
        text = (REPO / "docs" / "methodologies" / "sela.md").read_text(encoding="utf-8")
        for phrase in (
            "单 Agent 多角色",
            "System Advocate",
            "Local Defender",
            "Timing Auditor",
            "默认不拆成多个 Agent",
            "长期方向正确",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
