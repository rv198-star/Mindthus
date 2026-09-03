import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CASES = REPO / "tests" / "sra_wakeup_holdout_cases.jsonl"
DESIGN = REPO / "tests" / "sra_wakeup_experiment_design.md"
SRA_SKILL = REPO / "skills" / "sra" / "SKILL.md"
USING = REPO / "skills" / "using-mindthus" / "SKILL.md"
EDSP_SKILL = REPO / "skills" / "edsp" / "SKILL.md"
ENTRY_TRIAGE = REPO / "docs" / "methodologies" / "primitives" / "entry-triage.md"
RUNNER = REPO / "scripts" / "run-judgment-benchmark-cli.py"


class SraWakeupAndBoundaryAuditTests(unittest.TestCase):
    def load_cases(self) -> list[dict[str, object]]:
        self.assertTrue(CASES.is_file(), CASES)
        cases: list[dict[str, object]] = []
        for line_number, line in enumerate(CASES.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                self.fail(f"invalid JSON at {CASES}:{line_number}: {exc}")
            self.assertIsInstance(value, dict)
            cases.append(value)
        return cases

    def test_holdout_has_balanced_sra_positive_and_control_surfaces(self):
        cases = self.load_cases()
        self.assertEqual(len(cases), 24)
        self.assertEqual([case["case_number"] for case in cases], list(range(1, 25)))
        self.assertEqual(len({case["case_id"] for case in cases}), 24)

        sra_positive = [case for case in cases if case["expected_owner"] == "sra"]
        controls = [case for case in cases if case["expected_owner"] != "sra"]
        self.assertEqual(len(sra_positive), 12)
        self.assertEqual(len(controls), 12)
        self.assertTrue(all(case["case_type"] == "positive" for case in sra_positive))

        adjacent = {
            case["expected_owner"]
            for case in controls
            if case["router_case_type"] == "adjacent_control"
        }
        self.assertEqual(
            adjacent,
            {"3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan", "anti_spiral"},
        )
        direct = [case for case in controls if case["stay_asleep_expected"]]
        self.assertEqual(len(direct), 4)

    def test_holdout_schema_and_prompts_do_not_reveal_method_names(self):
        required = {
            "schema_version",
            "benchmark_id",
            "case_id",
            "case_number",
            "group_id",
            "group_name",
            "case_type",
            "router_case_type",
            "expected_owner",
            "positive_wakeup_expected",
            "stay_asleep_expected",
            "multi_turn",
            "prompt",
            "pass_criteria",
            "fail_signal",
            "score_scale",
        }
        forbidden_prompt_names = (
            "mindthus",
            "sra",
            "3l5s",
            "edsp",
            "sela",
            "mpg",
            "wae",
            "tvg",
            "tplan",
            "anti-spiral",
        )
        for case in self.load_cases():
            self.assertEqual(case["schema_version"], "mindthus-judgment-benchmark-case-v0.1")
            self.assertEqual(case["benchmark_id"], "sra-independent-wakeup-v1")
            self.assertTrue(required.issubset(case))
            self.assertFalse(case["multi_turn"])
            prompt = str(case["prompt"]).casefold()
            for name in forbidden_prompt_names:
                self.assertNotIn(name, prompt, f"{case['case_id']} reveals {name}")

    def test_sra_can_be_loaded_directly_without_3l5s_or_tplan_prerequisite(self):
        text = SRA_SKILL.read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        self.assertIn("Use directly when", frontmatter)
        self.assertIn("already-judgeable actions or bundles", frontmatter)
        self.assertIn("one named scarce resource", frontmatter)
        self.assertIn("missing comparison facts/resource", frontmatter)
        self.assertIn("one selected mainline's carrier, exposure, timing, or exit", frontmatter)
        for forbidden in (
            "must use 3l5s",
            "requires 3l5s",
            "must use tplan",
            "requires tplan",
            "must use using-mindthus",
            "requires using-mindthus",
        ):
            self.assertNotIn(forbidden, text.lower())

    def test_sra_is_packaged_as_a_direct_skill_in_every_supported_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pack"
            result = subprocess.run(
                [
                    "python3",
                    str(REPO / "scripts" / "build-release-pack.py"),
                    "--out",
                    str(out),
                    "--package",
                    "all",
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            skill_paths = (
                out / "claude-code" / "claude-plugin" / "skills" / "sra" / "SKILL.md",
                out / "claude-code" / "skills" / "sra" / "SKILL.md",
                out / "codex-plugin" / "mindthus" / "skills" / "sra" / "SKILL.md",
                out / "codex" / "skills" / "mindthus" / "sra" / "SKILL.md",
                out / "opencode" / ".opencode" / "skills" / "mindthus" / "sra" / "SKILL.md",
            )
            for path in skill_paths:
                self.assertTrue(path.is_file(), path)
                text = path.read_text(encoding="utf-8")
                self.assertIn("Use directly when", text)
                self.assertIn("already-judgeable actions or bundles", text)

    def test_passive_descriptions_reject_missing_inputs_and_single_mainline_carriers(self):
        using_frontmatter = USING.read_text(encoding="utf-8").split("---", 2)[1]
        sra = SRA_SKILL.read_text(encoding="utf-8")

        self.assertIn("Never load for an ordinary request lacking facts", using_frontmatter)
        self.assertIn("ask directly", using_frontmatter)
        self.assertIn(
            "SRA only after multiple judgeable candidates share a scarce resource",
            using_frontmatter,
        )

    def test_edsp_forced_binary_withholds_winner_until_structure_is_stable(self):
        text = " ".join(EDSP_SKILL.read_text(encoding="utf-8").split())
        for phrase in (
            "first sentence must diagnose the malformed binary and withhold a winner",
            "Do not name a provisional winner",
            "operating default follows the structural diagnosis",
            "is not the answer to which side is right",
        ):
            self.assertIn(phrase, text)

    def test_router_and_entry_triage_expose_the_same_sra_signature(self):
        using = USING.read_text(encoding="utf-8")
        using_compact = " ".join(using.split())
        triage = ENTRY_TRIAGE.read_text(encoding="utf-8")
        for phrase in (
            "Multiple valid candidates share a common scarce resource",
            "are judgeable",
            "choose next tranche, ceiling, defer/stop, reserve, or rerank",
            "SRA owns allocation",
            "3L5S/EDSP definition/structure",
            "WAE control",
            "TPlan runtime",
            "SELA owns direction pressure",
            "MPG owns path-carrying action",
        ):
            self.assertIn(phrase, using_compact)
        for phrase in (
            "multiple valid actions competing for one constrained resource",
            "current work versus another valid action for one constrained tranche",
            "several judgeable actions compete for one constrained time, money, person, attention, or risk tranche",
            "SRA must change the next allocation",
        ):
            self.assertIn(phrase, triage)

        runner = RUNNER.read_text(encoding="utf-8")
        self.assertRegex(runner, re.compile(r'"sra"\s*:\s*\{"sra"\}'))
        self.assertIn("|sra|", runner)

    def test_sra_method_relationships_are_bidirectional_on_skill_surfaces(self):
        checks = {
            REPO / "skills" / "3l5s" / "SKILL.md": (
                "same scarce resource",
                "3L5S makes candidates judgeable, SRA allocates them",
            ),
            REPO / "skills" / "edsp" / "SKILL.md": (
                "candidate structure is already stable",
                "use SRA for allocation",
                "EDSP only stabilizes",
            ),
            REPO / "skills" / "sela" / "SKILL.md": (
                "multiple candidates share one scarce resource",
                "use SRA for that current allocation",
            ),
            REPO / "skills" / "mpg" / "SKILL.md": (
                "multiple problems, tasks, objectives, or bundles compete",
                "use SRA",
                "MPG owns carrier and path posture",
            ),
            REPO / "skills" / "wae" / "SKILL.md": (
                "valid actions compete for one scarce resource",
                "use SRA",
                "does not allocate",
            ),
            REPO / "skills" / "tvg" / "SKILL.md": (
                "competes with external work for the same scarce resource",
                "use SRA for the cross-task allocation",
            ),
            REPO / "skills" / "tplan" / "SKILL.md": (
                "SRA may judge cross-task resource allocation",
                "TPlan retains state, Pulse, continuation, authority, recovery, and mutation",
            ),
        }
        for path, phrases in checks.items():
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{path.relative_to(REPO)} missing {phrase!r}")

        anti_spiral = (
            REPO / "docs" / "methodologies" / "anti-spiral-self-audit.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`SRA` 在刹车释放出资源", anti_spiral)
        self.assertIn("不形成相互递归调用", anti_spiral)

    def test_public_method_docs_preserve_sra_handoffs(self):
        checks = {
            REPO / "docs" / "methodologies" / "3l5s.md": "让候选可判断并落实选定工作",
            REPO / "docs" / "methodologies" / "edsp.md": "候选结构已经稳定",
            REPO / "docs" / "methodologies" / "sela.md": "交给 `SRA` 做本轮分配",
            REPO / "docs" / "methodologies" / "mpg.md": "多个问题、任务、目标或行动组合争夺同一资源池时由 SRA 分配",
            REPO / "docs" / "methodologies" / "wae.md": "多个有效行动争夺同一稀缺资源，用 `SRA` 做分配",
            REPO / "docs" / "methodologies" / "tvg.md": "交给 `SRA` 做跨任务资源分配",
            REPO / "docs" / "methodologies" / "tplan.md": "一般跨候选资源分配由 SRA 负责",
        }
        for path, phrase in checks.items():
            self.assertIn(phrase, path.read_text(encoding="utf-8"), path)

    def test_experiment_design_separates_availability_from_behavioral_rate(self):
        text = DESIGN.read_text(encoding="utf-8")
        for phrase in (
            "Independent invocation",
            "Natural wake-up",
            "Static contracts and package presence can prove independent availability",
            "Only completed host/model runs can establish a behavioral wake-up rate",
            "SRA positive wake-up recall >= 80%",
            "SRA false activation rate <= 10%",
            "Authentication failures",
            "infrastructure failures, not wake-up misses",
            "baseline: commit `b497ee380fb275727f1ba715f8035f17327a7efe`",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
