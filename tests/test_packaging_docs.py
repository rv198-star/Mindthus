import subprocess
import unittest
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]


class PackagingDocsTests(unittest.TestCase):
    def test_readme_names_current_skill_pack_and_tplan(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("mindthus:tplan", readme)
        self.assertIn("mindthus:*", readme)
        self.assertIn("当前仓库版本：`v0.5.1`", readme)
        self.assertIn("方法分层纪律", readme)
        self.assertIn("SELA", readme)
        self.assertIn("时机检查", readme)
        self.assertIn("docs/methodologies", readme)
        self.assertIn("安装", readme)
        self.assertIn("验证", readme)

    def test_readme_links_to_chinese_manual(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("SELA / 系统效率碾压局部优势", readme)
        self.assertIn("3L5S / 三层五步", readme)
        self.assertIn("EDSP / Extreme Deduction + Scenario Projection", readme)
        self.assertIn("WAE / Workflow-Agentic-Evidence", readme)
        self.assertIn("TVG / Thinking Value-Gain", readme)
        self.assertIn("Anti-Spiral / 反螺旋自检", readme)
        self.assertIn("讲清整体与局部", readme)
        self.assertIn("讲清问题如何从混乱信号走到可执行步骤", readme)
        self.assertIn("脚本、agent、review gate 都在“管事”", readme)
        self.assertIn("死亡螺旋", readme)
        self.assertIn("何时拿起哪把刀", readme)
        self.assertIn("可安装的判断工具箱", readme)
        self.assertIn("你可能见过这些情况", readme)
        self.assertIn("AI 生成的文档、代码或方案看起来完整，却停在表层", readme)

    def test_anti_spiral_methodology_resource_exists(self):
        text = (REPO / "docs" / "methodologies" / "anti-spiral-self-audit.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Anti-Spiral Self-Audit", text)
        self.assertIn("methodology resource", text)
        self.assertIn("tplan", text)
        self.assertIn("Third touch, stop first", text)

    def test_changelog_documents_v0_5_release_in_chinese(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v0.5 + v0.5.1", changelog)
        self.assertIn("GitHub Release 以 `v0.5.1` 发布", changelog)
        self.assertIn("没有单独发布 GitHub Release `v0.5`", changelog)
        self.assertIn("发布日期：2026-05-18", changelog)
        self.assertIn("方法分层纪律", changelog)
        self.assertIn("主思想", changelog)
        self.assertIn("从属补漏", changelog)
        self.assertIn("SELA", changelog)
        self.assertIn("时机检查", changelog)
        self.assertIn("EDSP frontmatter 修复", changelog)
        self.assertIn("python3 -m unittest discover -s tests -v", changelog)

    def test_changelog_release_sections_are_chinese_and_not_duplicated(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        lines = changelog.splitlines()
        self.assertEqual(lines.count("## v0.5 + v0.5.1"), 1)
        self.assertEqual(lines.count("## v0.5.1"), 0)
        self.assertEqual(lines.count("## v0.5"), 0)
        self.assertEqual(lines.count("## v0.4"), 1)
        self.assertIn("发布日期：2026-05-09", changelog)
        self.assertNotIn("Release date:", changelog)

    def test_sela_methodology_names_the_overall_local_tradeoff(self):
        text = (REPO / "skills" / "sela" / "resources" / "methodology.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("整体与局部", text)
        self.assertIn("可逆", text)
        self.assertIn("反馈", text)
        self.assertIn("可修正", text)
        self.assertIn("不是一次性静态最优", text)

    def test_methodology_pages_exist_and_cover_their_core_claims(self):
        cases = [
            ("sela.md", "系统效率碾压局部优势"),
            ("3l5s.md", "三层五步"),
            ("edsp.md", "Extreme Deduction + Scenario Projection"),
            ("wae.md", "Workflow-Agentic-Evidence"),
            ("tvg.md", "Thinking Value-Gain"),
            ("tplan.md", "Mission-oriented project manager"),
            ("anti-spiral-self-audit.md", "反螺旋自检"),
        ]
        for name, phrase in cases:
            text = (REPO / "docs" / "methodologies" / name).read_text(encoding="utf-8")
            self.assertIn(phrase, text, name)
            self.assertIn("## 这是什么", text, name)
            self.assertIn("## 解决什么问题", text, name)
            self.assertIn("## 核心判断", text, name)
            self.assertIn("## 怎么用", text, name)
            self.assertIn("## 具体案例", text, name)
            self.assertGreaterEqual(text.count("### 案例"), 2, name)
            self.assertIn("## 常见误用", text, name)
            self.assertIn("## 边界", text, name)
            self.assertIn("## 与其他方法的关系", text, name)
            self.assertIn("## 导航", text, name)

    def test_skill_frontmatter_is_valid_yaml(self):
        for path in sorted((REPO / "skills").glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), f"{path} missing frontmatter")
            end = text.find("\n---", 4)
            self.assertGreater(end, 0, f"{path} missing frontmatter terminator")
            frontmatter = text[4:end]
            try:
                parsed = yaml.safe_load(frontmatter)
            except yaml.YAMLError as exc:
                self.fail(f"{path} has invalid YAML frontmatter: {exc}")
            self.assertIsInstance(parsed, dict, f"{path} frontmatter must be a mapping")
            self.assertIn("name", parsed, f"{path} frontmatter missing name")
            self.assertIn("description", parsed, f"{path} frontmatter missing description")

    def test_codex_install_doc_names_tplan(self):
        install = (REPO / ".codex" / "INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("mindthus:tplan", install)
        self.assertIn("scripts/install-skills.sh", install)

    def test_install_script_exists_and_has_valid_shell_syntax(self):
        script = REPO / "scripts" / "install-skills.sh"
        self.assertTrue(script.exists())
        result = subprocess.run(["bash", "-n", str(script)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
