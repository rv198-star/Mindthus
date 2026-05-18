import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SELA = REPO / "skills" / "sela"


class SelaContractTests(unittest.TestCase):
    def test_skill_exposes_lightweight_timing_check(self):
        text = (SELA / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Timing Check",
            "时机检查",
            "临时保留",
            "锁死未来",
            "行动窗口",
            "not a new top-level principle",
        ):
            self.assertIn(phrase, text)

    def test_methodology_keeps_timing_check_lightweight(self):
        text = (SELA / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "时机检查",
            "不是独立原则",
            "不是补一套人文价值观",
            "临时保留",
            "锁死未来",
            "行动窗口",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
