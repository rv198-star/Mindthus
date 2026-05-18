import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class PackagingDocsTests(unittest.TestCase):
    def test_readme_names_current_skill_pack_and_tplan(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("mindthus:tplan", readme)
        self.assertIn("当前版本：`v0.5`", readme)
        self.assertIn("方法分层纪律", readme)
        self.assertIn("SELA", readme)
        self.assertIn("时机检查", readme)
        self.assertIn("docs/methodologies", readme)
        self.assertIn("Install", readme)
        self.assertIn("Verify", readme)

    def test_anti_spiral_methodology_resource_exists(self):
        text = (REPO / "docs" / "methodologies" / "anti-spiral-self-audit.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Anti-Spiral Self-Audit", text)
        self.assertIn("methodology resource", text)
        self.assertIn("tplan", text)

    def test_changelog_documents_v0_5_release_in_chinese(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v0.5", changelog)
        self.assertIn("发布日期：2026-05-18", changelog)
        self.assertIn("方法分层纪律", changelog)
        self.assertIn("主思想", changelog)
        self.assertIn("从属补漏", changelog)
        self.assertIn("SELA", changelog)
        self.assertIn("时机检查", changelog)
        self.assertIn("python3 -m unittest discover -s tests -v", changelog)

    def test_changelog_release_sections_are_chinese_and_not_duplicated(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(changelog.count("## v0.5"), 1)
        self.assertEqual(changelog.count("## v0.4"), 1)
        self.assertIn("发布日期：2026-05-09", changelog)
        self.assertNotIn("Release date:", changelog)

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
