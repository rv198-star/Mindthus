import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "tplan"


class TplanSkillContractTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "SKILL.md",
            "resources/schema.md",
            "resources/lifecycle.md",
            "resources/policy.md",
            "resources/hooks.md",
            "templates/mission.json",
            "templates/mission.md",
            "templates/evidence.jsonl",
            "templates/hook-output.json",
        ]
        missing = [path for path in required if not (SKILL / path).exists()]
        self.assertEqual(missing, [])

    def test_skill_frontmatter_and_boundaries(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: tplan", text)
        self.assertIn("description:", text)
        self.assertIn("Mission", text)
        self.assertIn("decision hooks", text)
        self.assertIn("Scripts must not decide semantic truth", text)

    def test_json_templates_are_valid(self):
        mission = json.loads((SKILL / "templates" / "mission.json").read_text(encoding="utf-8"))
        hook = json.loads((SKILL / "templates" / "hook-output.json").read_text(encoding="utf-8"))
        self.assertEqual(mission["schema_version"], "tplan.v0.1")
        self.assertIn("mission", mission)
        self.assertIn("tasks", mission)
        self.assertEqual(hook["recommendation"], "continue")

    def test_resource_files_name_runtime_contracts(self):
        resources = "\n".join(
            (SKILL / "resources" / name).read_text(encoding="utf-8")
            for name in ("schema.md", "lifecycle.md", "policy.md", "hooks.md")
        )
        for phrase in (
            "human_in_loop",
            "resource_sufficiency",
            "success-critical",
            "observational state",
            "decision state",
            "semantic correctness",
        ):
            self.assertIn(phrase, resources)


if __name__ == "__main__":
    unittest.main()
