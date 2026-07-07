import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


SKILLS = {
    "sela": {
        "validator": REPO / "skills" / "sela" / "scripts" / "validate_sela_output.py",
        "template": REPO / "skills" / "sela" / "templates" / "fidelity-output.json",
        "fixture": REPO / "skills" / "sela" / "fixtures" / "fidelity-smoke-pass.json",
        "contract": REPO / "skills" / "sela" / "resources" / "fidelity-contract.md",
    },
    "mpg": {
        "validator": REPO / "skills" / "mpg" / "scripts" / "validate_mpg_output.py",
        "template": REPO / "skills" / "mpg" / "templates" / "fidelity-output.json",
        "fixture": REPO / "skills" / "mpg" / "fixtures" / "fidelity-smoke-pass.json",
        "contract": REPO / "skills" / "mpg" / "resources" / "fidelity-contract.md",
    },
}


def run_validator(skill: dict[str, Path], path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(skill["validator"]), str(path)],
        text=True,
        capture_output=True,
        cwd=REPO,
    )


class SelaMpgSmokeFixtureTests(unittest.TestCase):
    def test_smoke_fixtures_pass_their_validators(self):
        for name, skill in SKILLS.items():
            with self.subTest(skill=name):
                result = run_validator(skill, skill["fixture"])

                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertIn("No shape or evidence risks detected", result.stdout)
                self.assertIn("agentic audit remains required", result.stdout)

    def test_blank_templates_remain_fill_in_skeletons_not_passing_outputs(self):
        for name, skill in SKILLS.items():
            with self.subTest(skill=name):
                result = run_validator(skill, skill["template"])

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("plain_language_conclusion is empty", result.stdout)
                self.assertIn(".finding is empty", result.stdout)

    def test_contracts_explain_template_vs_smoke_fixture_boundary(self):
        for name, skill in SKILLS.items():
            with self.subTest(skill=name):
                contract = skill["contract"].read_text(encoding="utf-8")
                contract_compact = " ".join(contract.split())

                self.assertIn("templates/fidelity-output.json is a fill-in skeleton", contract_compact)
                self.assertIn("not expected to pass as-is", contract_compact)
                self.assertIn("fixtures/fidelity-smoke-pass.json", contract_compact)
                self.assertIn("python3 scripts/validate_", contract_compact)


if __name__ == "__main__":
    unittest.main()
