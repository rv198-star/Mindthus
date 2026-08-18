import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANDIDATE = REPO / "docs" / "internal" / "research" / "bidirectional-steelman-convergence.md"
SHARED = REPO / "docs" / "methodologies" / "shared-primitives.md"
USING = REPO / "skills" / "using-mindthus" / "SKILL.md"
PRESSURE = REPO / "tests" / "bidirectional_steelman_pressure_tests.md"
HOLDOUT = REPO / "tests" / "bidirectional_steelman_p2_holdout_cases.jsonl"
CLITE_RUNNER = REPO / "scripts" / "run-bidirectional-steelman-clite-experiment.py"
PILOT_WORKFLOW = REPO / ".github" / "workflows" / "bidirectional-steelman-pilot.yml"


class BidirectionalSteelmanContractTests(unittest.TestCase):
    def test_candidate_exposes_simplified_clite_boundaries(self):
        text = CANDIDATE.read_text(encoding="utf-8")
        for phrase in (
            "Status: experimental **C-lite** research candidate",
            "Bidirectional Steelman Convergence / 双向钢人收敛",
            "not a standalone method",
            "Competitive Steelman / 竞争框架钢人",
            "Decisive Discriminator / 决定性判别变量",
            "Visible Translation Boundary / 可见表达翻译边界",
            "internal judgment representation",
            "X 值不值得换 Y",
            "5K 多花的钱，值不值得换更锐的文字？",
            "same judgment object",
            "same Evidence / Claim Ceiling",
            "Do not force symmetry after evidence becomes asymmetric",
            "There is no mandatory question",
            "direct/deterministic/preference task -> stay asleep",
            "Return To Stable Owner",
            "P2 Treatment Contract",
            "The retired larger C adaptation",
        ):
            self.assertIn(phrase, text)

        for retired_marker in (
            "### 1. Steelman A",
            "### 2. Steelman B",
            "### 4. One Information-Gain Move",
        ):
            self.assertNotIn(retired_marker, text)

    def test_candidate_is_not_promoted_to_stable_surfaces_before_behavior_evidence(self):
        shared = SHARED.read_text(encoding="utf-8")
        using = USING.read_text(encoding="utf-8")
        for text in (shared, using):
            self.assertNotIn("Bidirectional Steelman Convergence / 双向钢人收敛", text)
            self.assertNotIn("Competitive Steelman / 竞争框架钢人", text)
            self.assertNotIn("Decisive Discriminator / 决定性判别变量", text)
            self.assertNotIn("Visible Translation Boundary / 可见表达翻译边界", text)
        self.assertIn("Pressure Surface Check / 施压面检查", using)
        self.assertIn("pressure is not a route", using)
        self.assertIn("assign its owner", using)

    def test_preregistered_pressure_surface_targets_clite_p2(self):
        text = PRESSURE.read_text(encoding="utf-8")
        for phrase in (
            "A / current Mindthus",
            "B / source protocol",
            "C / C-lite Mindthus adaptation",
            "Competitive Steelman / 竞争框架钢人",
            "Decisive Discriminator / 决定性判别变量",
            "Visible Translation Boundary",
            "visible_translation",
            "5K 多花的钱，值不值得换更锐的",
            "SKILLS / Prompt Carrier Multi-turn",
            "27-inch 4K / 5K / BetterDisplay",
            "Malformed Binary Escape",
            "One User-owned Variable Missing",
            "Decisive Variable Is Externally Verifiable",
            "Negative Controls",
            "C-lite should be rejected",
            "visible-language",
            "Contaminated-session P0/P1/C-lite runs are protocol-debug evidence only",
        ):
            self.assertIn(phrase, text)

    def test_p2_surface_changed_holdouts_are_frozen_before_independent_run(self):
        rows = [
            json.loads(line)
            for line in HOLDOUT.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(rows), 7)
        self.assertEqual(
            {row["case_id"] for row in rows},
            {"bsc-h01", "bsc-h02", "bsc-h03", "bsc-h04", "bsc-h05", "bsc-h06", "bsc-h07"},
        )
        self.assertEqual(sum(row["case_type"] == "positive" for row in rows), 5)
        self.assertEqual(sum(row["case_type"] == "negative_control" for row in rows), 2)
        text = HOLDOUT.read_text(encoding="utf-8")
        for phrase in (
            "RAG 本质上不就是",
            "所有发布要么一次性全量上线",
            "故障域更集中",
            "新搜索索引看起来已经",
            "checksum verifier",
            "按钮我就是想改成红色",
            "翻译成英文",
        ):
            self.assertIn(phrase, text)

    def test_independent_runner_changes_only_variant_c_treatment_and_shared_expression_score(self):
        text = CLITE_RUNNER.read_text(encoding="utf-8")
        for phrase in (
            "Run the preregistered BSC experiment with the simplified C-lite treatment",
            "run-bidirectional-steelman-experiment.py",
            "Competitive Steelman / 竞争框架钢人",
            "Decisive Discriminator / 决定性判别变量",
            "Visible Translation Boundary / 可见表达翻译边界",
            "There is no mandatory question",
            "visible_translation",
            "module.ADAPTED_PROTOCOL = C_LITE_PROTOCOL",
            "module.DIMENSIONS = tuple(module.DIMENSIONS) + (\"visible_translation\",)",
            "module.DIMENSION_GUIDANCE[\"visible_translation\"]",
            "return int(module.main())",
        ):
            self.assertIn(phrase, text)

        workflow = PILOT_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Run preregistered A/B/C-lite pilot", workflow)
        self.assertIn("run-bidirectional-steelman-clite-experiment.py", workflow)
        self.assertIn('"candidate": "C-lite"', workflow)


if __name__ == "__main__":
    unittest.main()
