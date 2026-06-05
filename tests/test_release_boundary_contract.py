import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class ReleaseBoundaryContractTests(unittest.TestCase):
    def test_v0_6_3_release_surface_is_declared(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        builder = (REPO / "scripts" / "build-release-pack.py").read_text(encoding="utf-8")

        self.assertIn("当前仓库版本：`v0.6.3`", readme)
        self.assertIn("## v0.6.3", changelog)
        self.assertIn("[完整发布日志](docs/releases/v0.6.3.md)", changelog)
        self.assertIn("tplan 运行时优化", changelog)
        self.assertIn("SubAgents are scouts, not controllers", changelog)
        self.assertIn('VERSION = "0.6.3"', builder)

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
