import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class ReleaseBoundaryContractTests(unittest.TestCase):
    def test_current_release_log_does_not_record_exact_suite_count(self):
        release_log = (REPO / "docs" / "releases" / "v1.4.3.md").read_text(
            encoding="utf-8"
        )
        self.assertIsNone(re.search(r"\b\d+\s+tests\s+OK\b", release_log))

    def test_current_release_surface_is_v1_4_3(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        builder = (REPO / "scripts" / "build-release-pack.py").read_text(encoding="utf-8")

        self.assertIn("当前仓库版本：`v1.4.3`", readme)
        self.assertEqual(readme.count("当前仓库版本："), 1)
        self.assertNotIn("当前仓库版本：`v1.4.2`", readme)
        self.assertNotIn("当前仓库版本：`v1.4.1`", readme)
        self.assertNotIn("## 版本与开发状态", readme)
        self.assertNotIn("当前开发分支同步", readme)
        self.assertIn("局部正确", readme)
        self.assertIn("带有倾向性的输入", readme)
        self.assertIn("输入定框审计", readme)
        self.assertIn("framing-risk", readme)
        self.assertIn("用户价值、偏好、审美和风险姿态", readme)
        self.assertIn("mindthus-plugins-1.4.3.tar.gz", readme)
        self.assertIn("mindthus-skills-1.4.3.tar.gz", readme)
        self.assertIn(
            "github.com/rv198-star/Mindthus/releases/download/v1.4.3/mindthus-plugins-1.4.3.tar.gz",
            readme,
        )
        self.assertIn(
            "github.com/rv198-star/Mindthus/releases/download/v1.4.3/mindthus-skills-1.4.3.tar.gz",
            readme,
        )
        self.assertIn("codex plugin marketplace add /tmp/mindthus-plugins/codex-plugin", readme)
        self.assertIn("claude plugin marketplace add /tmp/mindthus-plugins/claude-code", readme)
        self.assertIn("cp -R /tmp/mindthus-skills/opencode/.opencode", readme)
        self.assertIn("## v1.4.3", changelog)
        self.assertIn("[完整发布日志](docs/releases/v1.4.3.md)", changelog)
        self.assertIn("Method Reference Boundary", changelog)
        self.assertIn("MPG-AQM 会话取证负测", changelog)
        self.assertIn("TVG 外部审查边界", changelog)
        self.assertIn('VERSION = "1.4.3"', builder)

        release_log = (REPO / "docs" / "releases" / "v1.4.3.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "# Mindthus v1.4.3 发布日志",
            "发布日期：2026-07-06",
            "## 版本定位",
            "## 主要变化",
            "## 边界",
            "## 验证",
            "Method Reference Boundary / 方法引用边界",
            "method name in an inspection request is evidence scope, not route ownership",
            "019f359a-6aa2-78c0-9ac5-822abae99495",
            "TVG 外部审查防回归",
            "skills/mpg/SKILL.md",
            "本版不关闭 #85",
            "本版不新增独立 skill",
            "不声称解决所有 discovery 层误触",
            "python3 scripts/build-release-pack.py",
            "python3 -m pytest -q",
        ):
            self.assertIn(phrase, release_log)

        self.assertNotIn("Release date:", release_log)

    def test_v1_1_2_release_surface_is_preserved(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v1.1.2", changelog)
        self.assertIn("[完整发布日志](docs/releases/v1.1.2.md)", changelog)
        self.assertIn("Snapshot / Pulse / Gate", changelog)
        self.assertIn("Mission Pulse", changelog)
        self.assertIn("minimum-pairs", changelog)
        self.assertIn("不声明低频方法 wake-up lift 已被真实 replay 证明", changelog)

        release_log = (REPO / "docs" / "releases" / "v1.1.2.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "# Mindthus v1.1.2 发布日志",
            "发布日期：2026-06-23",
            "Snapshot -> Pulse -> Gate",
            "Scripts observe. Pulse routes. Gates decide.",
            "mission_pulse.py",
            "winning candidate",
            "suppressed candidates",
            "arbitration trace",
            "anti_spiral_audit",
            "minimum-pairs",
            "1.1.2",
            "python3 scripts/build-release-pack.py",
        ):
            self.assertIn(phrase, release_log)

        self.assertNotIn("Release date:", release_log)

    def test_v1_1_1_release_surface_is_preserved(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v1.1.1", changelog)
        self.assertIn("[完整发布日志](docs/releases/v1.1.1.md)", changelog)
        self.assertIn("TPlan Mission Shared Context Memory", changelog)
        self.assertIn("Router wake-up canary", changelog)
        self.assertIn("preflight_mission.py", changelog)
        self.assertIn("不声明已经证明低频方法唤醒率显著提升", changelog)
        self.assertIn("不继承旧 Mission 的 acceptance authority", changelog)

        release_log = (REPO / "docs" / "releases" / "v1.1.1.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "# Mindthus v1.1.1 发布日志",
            "发布日期：2026-06-17",
            "TPlan Mission Shared Context Memory",
            ".tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md",
            "preflight_mission.py",
            "source_contexts",
            "Router wake-up canary",
            "baseline-ceiling",
            "不声明已经证明低频方法唤醒率显著提升",
            "不继承旧 Mission 的 acceptance authority",
            "python3 -m unittest discover -s tests -v",
            "python3 scripts/build-release-pack.py",
        ):
            self.assertIn(phrase, release_log)

        self.assertNotIn("Release date:", release_log)

    def test_v1_1_0_release_surface_is_preserved(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")

        release_log = (REPO / "docs" / "releases" / "v1.1.0.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## v1.1.0", changelog)
        self.assertIn("[完整发布日志](docs/releases/v1.1.0.md)", changelog)
        for phrase in (
            "TVG Value Profile",
            "TVG 示例 profile",
            "TPlan Shared Risk Context",
            "TPlan continuation authorization",
            "Codex 安装路径",
            "不会替 agent 判断 profile 是否审美成功",
            "是否具备稳定视觉泛化能力",
        ):
            self.assertIn(phrase, changelog)
        for phrase in (
            "两个影视提示词 / 分镜方向的示范 profile",
            "邵氏清水湾棚拍时代武侠 / 神怪",
            "胡金铨武侠电影",
            "有明确审美目标的 profile",
            "价值定义、输出形态和扩写策略",
            "不是电影史分类结论",
            "如何编写和使用 TVG profile",
            "输出厚度落在哪些可审查单位上",
            "把剧本文字扩成可审查的多镜头提示词",
        ):
            self.assertIn(phrase, release_log)

    def test_v1_0_1_release_surface_is_preserved(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        text = (REPO / "docs" / "releases" / "v1.0.1.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## v1.0.1", changelog)
        self.assertIn("[完整发布日志](docs/releases/v1.0.1.md)", changelog)
        self.assertIn("当时的 1.0 系列推荐安装版本", changelog)
        self.assertIn("MPG、授权口径、忠实度评审自动化、退出审查和跨模型小样本", changelog)
        self.assertIn("scripts/log-fidelity-usage.py", changelog)
        self.assertNotIn("当前推荐的 1.0 系列安装版本", changelog)

        for phrase in (
            "当时的 1.0 系列推荐安装版本",
            "提供第一版正式可用的判断框架",
            "v1.0 正式能力",
            "`v1.0.1` 同时包含 `v1.0` 的这些更新",
            "MPG / 主线-路径博弈",
            "授权口径",
            "忠实度评审自动化入口",
            "退出审查",
            "跨模型小样本",
            "v1.0.1 补丁能力",
            "Mindthus v1.0 发布日志",
            "https://github.com/rv198-star/Mindthus/blob/v1.0/docs/releases/v1.0.md",
        ):
            self.assertIn(phrase, text)
        self.assertNotIn("当前推荐的 1.0 系列安装版本", text)
        self.assertNotIn("](v1.0.md)", text)
        self.assertNotIn("v0.9", text)
        self.assertNotIn("v0.x", text)

    def test_v1_0_release_surface_is_preserved(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("## v1.0", changelog)
        self.assertIn("[完整发布日志](docs/releases/v1.0.md)", changelog)
        self.assertIn("LICENSE blocker closed", changelog)
        self.assertIn("judge automation blocker closed", changelog)
        self.assertIn("challenge_premise escape blocker closed", changelog)
        self.assertIn("cross-model baseline blocker closed", changelog)

    def test_v1_0_release_log_is_chinese_and_release_ready(self):
        text = (REPO / "docs" / "releases" / "v1.0.md").read_text(encoding="utf-8")

        for phrase in (
            "# Mindthus v1.0 发布日志",
            "发布日期：2026-06-08",
            "版本定位",
            "LICENSE blocker closed",
            "Judge automation blocker closed",
            "challenge_premise escape blocker closed",
            "Cross-model baseline blocker closed",
            "AGPLv3",
            "COMMERCIAL-LICENSE.md",
            "scripts/run-fidelity-judge.py",
            "escape_review",
            "opencode/deepseek-v4-flash-free",
            "不声明所有模型、所有方法的普适鲁棒性",
            "验证结果",
            "python3 -m unittest discover -s tests -v",
            "python3 scripts/build-release-pack.py",
        ):
            self.assertIn(phrase, text)

        self.assertNotIn("Release date:", text)

    def test_v0_6_3_release_log_is_chinese_and_release_ready(self):
        text = (REPO / "docs" / "releases" / "v0.6.3.md").read_text(encoding="utf-8")

        for phrase in (
            "# Mindthus v0.6.3 发布日志",
            "发布日期：2026-06-05",
            "版本定位",
            "这次解决了什么",
            "自适应运行",
            "轻，但不降级",
            "runtime level may reduce recording density",
            "must not weaken key risk triggers",
            "init_lite.py",
            "checkpoint.py",
            "用户可读输出",
            "render_user_update.py",
            "只读 SubAgent 加速",
            "SubAgents are scouts, not controllers",
            "candidate findings",
            "#11",
            "#12",
            "#13",
            "验证结果",
            "不声明跨模型鲁棒性",
            "不声称已经给出干净性能证明",
        ):
            self.assertIn(phrase, text)

        self.assertNotIn("Release date:", text)
        self.assertNotIn("Summary", text)

    def test_v0_6_2_release_log_is_chinese_and_release_ready(self):
        text = (REPO / "docs" / "releases" / "v0.6.2.md").read_text(encoding="utf-8")

        for phrase in (
            "# Mindthus v0.6.2 发布日志",
            "发布日期：2026-05-31",
            "版本定位",
            "这次解决了什么",
            "TVG",
            "厚度闸门",
            "输出档位",
            "`insight_dense`",
            "`balanced`",
            "`coverage_rich`",
            "公开技能包发布边界",
            "#9",
            "#10",
            "验证结果",
            "100/100",
            "不声明跨模型鲁棒性",
            "发布后再关闭 #10",
        ):
            self.assertIn(phrase, text)

        self.assertNotIn("Release date:", text)
        self.assertNotIn("Summary", text)

    def test_public_skills_release_boundary_doc_covers_issue_9_contract(self):
        text = (
            REPO / "docs" / "internal" / "public-skills-release-boundary.md"
        ).read_text(encoding="utf-8")

        for phrase in (
            "Private Repository / Public Skills Release Boundary",
            "allowlist-generated release pack",
            "Included file classes",
            "Excluded file classes",
            "Cleanliness validation",
            "Follow-up work orders",
            "scripts/build-release-pack.py",
            "docs/internal/",
            "docs/superpowers/",
            "GitHub Release assets",
            "LICENSE",
            "OpenCode",
            "Claude Code marketplace",
            "Codex",
            "install from the release pack",
        ):
            self.assertIn(phrase, text)

    def test_release_boundary_doc_keeps_current_checkout_install_flow_intact(self):
        text = (
            REPO / "docs" / "internal" / "public-skills-release-boundary.md"
        ).read_text(encoding="utf-8")

        self.assertIn("scripts/install-skills.sh remains the development checkout installer", text)
        self.assertIn("The release installer must operate on the sanitized package", text)
        self.assertIn("Do not make repository privacy, license change, or destructive cleanup part of v0.6.2", text)


if __name__ == "__main__":
    unittest.main()
