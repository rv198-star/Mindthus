import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class ReleaseBoundaryContractTests(unittest.TestCase):
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
