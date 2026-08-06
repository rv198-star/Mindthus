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


if __name__ == "__main__":
    unittest.main()
