import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


METHODS = {
    "3l5s": {
        "method": "3L5S",
        "schema_version": "3l5s-fidelity-v0.1",
        "validator": REPO / "skills" / "3l5s" / "scripts" / "validate_3l5s_output.py",
        "template": REPO / "skills" / "3l5s" / "templates" / "fidelity-output.json",
        "skill": REPO / "skills" / "3l5s" / "SKILL.md",
        "missing_move": "loopback_trigger",
        "transfer_to": "EDSP",
    },
    "edsp": {
        "method": "EDSP",
        "schema_version": "edsp-fidelity-v0.1",
        "validator": REPO / "skills" / "edsp" / "scripts" / "validate_edsp_output.py",
        "template": REPO / "skills" / "edsp" / "templates" / "fidelity-output.json",
        "skill": REPO / "skills" / "edsp" / "SKILL.md",
        "missing_move": "overturn_conditions",
        "transfer_to": "3L5S",
    },
    "wae": {
        "method": "WAE",
        "schema_version": "wae-fidelity-v0.1",
        "validator": REPO / "skills" / "wae" / "scripts" / "validate_wae_output.py",
        "template": REPO / "skills" / "wae" / "templates" / "fidelity-output.json",
        "skill": REPO / "skills" / "wae" / "SKILL.md",
        "missing_move": "schema_judgment_boundary",
        "transfer_to": "SELA",
    },
    "tvg": {
        "method": "TVG",
        "schema_version": "tvg-fidelity-v0.1",
        "validator": REPO / "skills" / "tvg" / "scripts" / "validate_tvg_output.py",
        "template": REPO / "skills" / "tvg" / "templates" / "fidelity-output.json",
        "skill": REPO / "skills" / "tvg" / "SKILL.md",
        "missing_move": "blocked_input_gate",
        "transfer_to": "WAE",
    },
    "using-mindthus": {
        "method": "using-mindthus",
        "schema_version": "using-mindthus-fidelity-v0.1",
        "validator": REPO
        / "skills"
        / "using-mindthus"
        / "scripts"
        / "validate_using_mindthus_output.py",
        "template": REPO / "skills" / "using-mindthus" / "templates" / "fidelity-output.json",
        "skill": REPO / "skills" / "using-mindthus" / "SKILL.md",
        "missing_move": "execution_impact",
        "transfer_to": "MPG",
    },
}


def run_validator(script: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fidelity-output.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return subprocess.run(
            ["python3", str(script), str(path)],
            text=True,
            capture_output=True,
            cwd=REPO,
        )


class RemainingSkillFidelityTests(unittest.TestCase):
    def test_remaining_skills_have_core_validators_templates_and_skill_links(self):
        for slug, spec in METHODS.items():
            with self.subTest(skill=slug):
                script = spec["validator"]
                template = spec["template"]
                skill = spec["skill"]

                self.assertTrue(script.exists(), script)
                self.assertTrue(template.exists(), template)

                script_text = script.read_text(encoding="utf-8")
                self.assertIn("_runtime.fidelity.core", script_text)
                self.assertIn("FidelitySpec", script_text)
                self.assertNotIn("@dataclass", script_text)

                skill_text = skill.read_text(encoding="utf-8")
                self.assertIn("fidelity contract", skill_text)
                self.assertIn("templates/fidelity-output.json", skill_text)
                self.assertIn(script.name, skill_text)

    def test_remaining_skill_templates_pass_shape_validation(self):
        for slug, spec in METHODS.items():
            with self.subTest(skill=slug):
                payload = json.loads(spec["template"].read_text(encoding="utf-8"))

                result = run_validator(spec["validator"], payload)

                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertIn(f"{spec['method']} Shape & Evidence Risk Report", result.stdout)
                self.assertIn("No shape or evidence risks detected", result.stdout)
                self.assertIn("agentic audit remains required", result.stdout)
                self.assertNotIn("semantic approval", result.stdout)

    def test_missing_required_move_fails_for_each_remaining_skill(self):
        for slug, spec in METHODS.items():
            with self.subTest(skill=slug):
                payload = json.loads(spec["template"].read_text(encoding="utf-8"))
                del payload["required_judgment_moves"][spec["missing_move"]]

                result = run_validator(spec["validator"], payload)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    f"missing required judgment move: {spec['missing_move']}",
                    result.stdout,
                )
                self.assertIn("agentic audit remains required", result.stdout)

    def test_method_exit_is_allowed_without_required_moves_for_each_remaining_skill(self):
        for slug, spec in METHODS.items():
            with self.subTest(skill=slug):
                result = run_validator(
                    spec["validator"],
                    {
                        "schema_version": spec["schema_version"],
                        "method": spec["method"],
                        "applicability": "transfer",
                        "plain_language_conclusion": f"{spec['method']} is not dominant here.",
                        "exit_reason": "Another method owns the active hard judgment.",
                        "transfer_to": spec["transfer_to"],
                    },
                )

                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertIn("method exit accepted: transfer", result.stdout)
                self.assertIn("agentic audit remains required", result.stdout)


if __name__ == "__main__":
    unittest.main()
