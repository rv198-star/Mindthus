import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class PackagingDocsTests(unittest.TestCase):
    def test_readme_names_current_skill_pack_and_tplan(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("mindthus:tplan", readme)
        self.assertIn("Current release: `v0.4`", readme)
        self.assertIn("Linear Continuation Gate", readme)
        self.assertIn("Premise Calibration", readme)
        self.assertIn("Install", readme)
        self.assertIn("Verify", readme)

    def test_changelog_documents_v0_4_release(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v0.4", changelog)
        self.assertIn("Linear Continuation Gate", changelog)
        self.assertIn("Premise Calibration", changelog)
        self.assertIn("path_assessment", changelog)

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
