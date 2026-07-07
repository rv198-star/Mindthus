import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CASE_DIR = REPO / "docs" / "cases" / "before-after"


class BeforeAfterCasePageTests(unittest.TestCase):
    def test_five_public_before_after_pages_have_required_sections(self):
        pages = sorted(CASE_DIR.glob("*.md"))

        self.assertEqual(len(pages), 5, [page.name for page in pages])
        for page in pages:
            text = page.read_text(encoding="utf-8")
            for heading in (
                "## User Input",
                "## Baseline-Style Output",
                "## +Mindthus-Style Output",
                "## What Changed",
            ):
                self.assertIn(heading, text, page.name)
            self.assertLessEqual(len(text.split()), 500, page.name)

    def test_readme_links_examples_as_explanatory_not_quantitative_proof(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")

        self.assertIn("docs/cases/before-after/", readme)
        self.assertIn("explanatory examples", readme)
        self.assertIn("not quantitative proof", readme)
        self.assertIn("docs/benchmarks/latest.md", readme)


if __name__ == "__main__":
    unittest.main()
