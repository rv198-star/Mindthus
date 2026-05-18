import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SKILL_FILES = sorted((REPO / "skills").glob("*/SKILL.md"))


class MethodLayeringContractTests(unittest.TestCase):
    def test_project_docs_define_method_layering_discipline(self):
        for path in (REPO / "README.md", REPO / "AGENTS.md"):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "Method Layering Discipline",
                "方法分层纪律",
                "`core`",
                "`mainline`",
                "`guardrail`",
                "`boundary`",
                "`example`",
                "`runtime support`",
                "guardrail must not become a new judgment center",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_skill_entrypoints_use_ordered_method_layers(self):
        required_headers = (
            "## Core Claim",
            "## Mainline",
            "## Guardrails",
            "## Boundaries",
        )

        for path in SKILL_FILES:
            text = path.read_text(encoding="utf-8")
            positions = []
            for header in required_headers:
                position = text.find(header)
                self.assertGreaterEqual(position, 0, f"{path} missing {header!r}")
                positions.append(position)
            self.assertEqual(positions, sorted(positions), f"{path} method layers are out of order")

    def test_skill_entrypoints_do_not_add_unlayered_h2_sections(self):
        allowed_prefixes = (
            "## Core Claim",
            "## Mainline",
            "## Guardrails",
            "## Boundaries",
            "## Runtime Support",
        )

        for path in SKILL_FILES:
            text = path.read_text(encoding="utf-8")
            unlayered = [
                line
                for line in text.splitlines()
                if line.startswith("## ") and not line.startswith(allowed_prefixes)
            ]
            self.assertEqual(unlayered, [], f"{path} has unlayered H2 sections")


if __name__ == "__main__":
    unittest.main()
