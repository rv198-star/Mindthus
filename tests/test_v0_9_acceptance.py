import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class V09AcceptanceTests(unittest.TestCase):
    def test_v0_9_acceptance_records_pre_1_0_scope(self):
        text = (
            REPO / "tests" / "method_fidelity_v0_9_acceptance_2026-06-08.md"
        ).read_text(encoding="utf-8")

        for phrase in (
            "# v0.9 Method Fidelity Harness Acceptance",
            "Status: Pre-1.0 acceptance record",
            "## Scope",
            "## anti-overconstraint audit",
            "does not claim cross-model robustness",
            "## Verification",
            "python3 -m unittest discover -s tests -v",
        ):
            self.assertIn(phrase, text)

    def test_public_docs_preserve_v0_9_history_and_name_v1_0_release_surface(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")

        for phrase in ("当前仓库版本：`v1.4.3`", "GitHub Releases"):
            self.assertIn(phrase, readme)

        for phrase in (
            "## v1.0",
            "v1.0 Method Fidelity Framework",
            "v0.9",
            "约束关键判断动作，不约束判断结论",
        ):
            self.assertIn(phrase, changelog)

        self.assertNotIn("Pre-1.0", readme)


if __name__ == "__main__":
    unittest.main()
