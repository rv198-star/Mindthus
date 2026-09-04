import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github" / "workflows" / "python-validation.yml"
README = REPO / "README.md"


class CiWorkflowTests(unittest.TestCase):
    def test_python_validation_workflow_runs_documented_release_smokes(self):
        self.assertTrue(WORKFLOW.is_file(), "missing GitHub Actions workflow")
        text = WORKFLOW.read_text(encoding="utf-8")

        for phrase in (
            "actions/checkout",
            "actions/setup-python",
            'python-version: "3.11"',
            "python3 -m unittest tests.test_packaging_docs -v",
            "python3 -m unittest discover -s tests/tplan -v",
            "python3 -m unittest discover -s tests -q",
            "python3 scripts/log-fidelity-usage.py --validate --log data/fidelity-usage-log.jsonl",
            "python3 skills/sela/scripts/validate_sela_output.py skills/sela/fixtures/fidelity-smoke-pass.json",
            "python3 skills/mpg/scripts/validate_mpg_output.py skills/mpg/fixtures/fidelity-smoke-pass.json",
            "unittest is canonical",
        ):
            self.assertIn(phrase, text)

    def test_release_validation_documents_supported_python_floor(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("CPython 3.10+", text)
        self.assertIn("python3 --version", text)
        self.assertIn("export MINDTHUS_PYTHON=python3.11", text)
        self.assertIn('"$MINDTHUS_PYTHON" -m unittest discover -s tests -v', text)
        for interpreter in ("python3.10", "python3.11", "python3.12"):
            self.assertIn(interpreter, text)


if __name__ == "__main__":
    unittest.main()
