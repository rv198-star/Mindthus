import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class ReleaseBoundaryContractTests(unittest.TestCase):
    def test_current_release_surface_is_v1_1_0(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        builder = (REPO / "scripts" / "build-release-pack.py").read_text(encoding="utf-8")

        self.assertIn("当前仓库版本：`v1.1.0`", readme)
        self.assertIn("## v1.1.0", changelog)
        self.assertIn("[完整发布日志](docs/releases/v1.1.0.md)", changelog)
        self.assertIn("TVG Value Profile", changelog)
        self.assertIn("TVG 示例 profile", changelog)
        self.assertIn("TPlan Shared Risk Context", changelog)
        self.assertIn("TPlan continuation authorization", changelog)
        self.assertIn("Codex 安装路径", changelog)
        self.assertIn("不会替 agent 判断 profile 是否审美成功", changelog)
        self.assertIn("是否具备稳定视觉泛化能力", changelog)
        self.assertIn('VERSION = "1.1.0"', builder)

        release_log = (REPO / "docs" / "releases" / "v1.1.0.md").read_text(
            encoding="utf-8"
        )
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
        self.assertIn("如果从 `v0.x` 直接升级到 `v1.0.1`", changelog)
        self.assertIn("scripts/log-fidelity-usage.py", changelog)

        for phrase in (
            "如果从 v0.x 升级",
            "`v1.0.1` 包含 `v1.0` 的正式发布面",
            "MPG / 主线-路径博弈",
            "授权口径",
            "忠实度评审自动化入口",
            "退出理由本身是否成立",
            "跨模型小样本",
            "Mindthus v1.0 发布日志",
        ):
            self.assertIn(phrase, text)

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
