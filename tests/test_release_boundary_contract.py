import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class ReleaseBoundaryContractTests(unittest.TestCase):
    def test_v0_6_2_release_surface_is_declared(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        builder = (REPO / "scripts" / "build-release-pack.py").read_text(encoding="utf-8")

        self.assertIn("当前仓库版本：`v0.6.2`", readme)
        self.assertIn("## v0.6.2", changelog)
        self.assertIn("TVG 从扩厚度升级为 grounded insight value-gain", changelog)
        self.assertIn("public skills release boundary", changelog)
        self.assertIn('VERSION = "0.6.2"', builder)

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
