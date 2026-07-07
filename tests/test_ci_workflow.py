import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github" / "workflows" / "python-validation.yml"


class CiWorkflowTests(unittest.TestCase):
    def test_python_validation_workflow_runs_documented_release_smokes(self):
        self.assertTrue(WORKFLOW.is_file(), "missing GitHub Actions workflow")
        text = WORKFLOW.read_text(encoding="utf-8")

        for phrase in (
            "actions/checkout",
            "actions/setup-python",
            "python3 -m unittest tests.test_packaging_docs -v",
            "python3 -m unittest discover -s tests/tplan -v",
            "python3 -m unittest discover -s tests -q",
            "python3 scripts/log-fidelity-usage.py --validate --log data/fidelity-usage-log.jsonl",
            "python3 skills/sela/scripts/validate_sela_output.py skills/sela/fixtures/fidelity-smoke-pass.json",
            "python3 skills/mpg/scripts/validate_mpg_output.py skills/mpg/fixtures/fidelity-smoke-pass.json",
            "unittest is canonical",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
