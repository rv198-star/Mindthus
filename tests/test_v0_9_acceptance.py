import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class V09AcceptanceTests(unittest.TestCase):
    def test_v0_9_acceptance_records_pre_1_0_scope(self):
        text = (
            REPO / "tests" / "method_fidelity_v0_9_acceptance_2026-06-08.md"
        ).read_text(encoding="utf-8")

        for phrase in (
            "v0.9 Method Fidelity Harness Acceptance",
            "Pre-1.0",
            "SELA and MPG pilots",
            "3L5S and TVG validator alignment",
            "fidelity core",
            "anti-overconstraint audit",
            "shape pass is not semantic approval",
            "validator semantic approval forbidden",
            "v1.0 readiness: not yet",
            "does not claim cross-model robustness",
            "python3 -m unittest discover -s tests -v",
        ):
            self.assertIn(phrase, text)

    def test_readme_and_changelog_name_v0_9_as_pre_1_0(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")

        for phrase in (
            "v0.9 Method Fidelity Harness",
            "Pre-1.0",
            "v1.0",
            "约束关键判断动作，不约束判断结论",
        ):
            self.assertIn(phrase, readme)
            self.assertIn(phrase, changelog)


if __name__ == "__main__":
    unittest.main()
