import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANDIDATE = REPO / "beta" / "2.0-roi-thin-core"
PROFILE = json.loads((CANDIDATE / "profile.json").read_text(encoding="utf-8"))
OVERLAY = CANDIDATE / "skills" / "using-mindthus" / "SKILL.md"
QUALIFICATION_REF = "4ee3e034db6bf8d1e34002d7f162e2b008516490"


class HistoricalRoiThinCoreTests(unittest.TestCase):
    def test_frozen_candidate_identity_is_preserved(self) -> None:
        self.assertEqual(PROFILE["candidate"], "2.0.0-roi.2")
        self.assertEqual(PROFILE["status"], "unpublished-candidate")
        self.assertEqual(PROFILE["baseline"]["version"], "1.4.6")
        self.assertEqual(
            PROFILE["baseline"]["commit"],
            "00da11657bce553cb32e8e90c06ffe959dc08362",
        )
        self.assertFalse(PROFILE["release_preparation"])

    def test_frozen_qualification_tree_is_byte_unchanged(self) -> None:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                QUALIFICATION_REF,
                "--",
                "beta/2.0-roi-thin-core",
            ],
            cwd=REPO,
        )
        self.assertEqual(result.returncode, 0)

    def test_thin_entry_keeps_the_qualified_shape(self) -> None:
        text = OVERLAY.read_text(encoding="utf-8")
        self.assertLessEqual(len(OVERLAY.read_bytes()), 2300)
        for required in (
            "Frame and whole",
            "Decision context",
            "Evidence ceiling",
            "Anti-Spiral",
            "one visible thesis",
            "decision-changing evidence",
        ):
            self.assertIn(required, text)
        lowered = text.lower()
        for method in ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan"):
            self.assertNotIn(method, lowered)
        self.assertNotIn("resources/", text)
        self.assertNotIn("gpt-", lowered)

    def test_frozen_decision_report_keeps_the_claim_ceiling(self) -> None:
        report = (
            CANDIDATE / "qualification" / "DECISION-REPORT.zh-CN.md"
        ).read_text(encoding="utf-8")
        self.assertIn("CONTINUE_2X_ROI_THIN_CORE_AS_EXPERIMENTAL_CANDIDATE", report)
        self.assertIn("这不是发布批准", report)
        self.assertIn("未证明", report)

    def test_historical_builder_rejects_live_shared_core_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mindthus-roi-history-") as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CANDIDATE / "build-candidate.py"),
                    "--out",
                    str(Path(temporary) / "candidate"),
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("declared 1.4.6 baseline", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
