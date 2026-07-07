import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CASESET = REPO / "tests" / "judgment_benchmark_50_cases.jsonl"
BENCHMARK_DOC = REPO / "docs" / "benchmarks" / "judgment-50.md"
LATEST_DOC = REPO / "docs" / "benchmarks" / "latest.md"


class JudgmentBenchmarkCaseTests(unittest.TestCase):
    def load_cases(self) -> list[dict[str, object]]:
        self.assertTrue(CASESET.is_file(), "missing 50-case benchmark JSONL fixture")
        cases: list[dict[str, object]] = []
        for line_number, line in enumerate(CASESET.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                self.fail(f"invalid JSON on line {line_number}: {exc}")
            self.assertIsInstance(case, dict, f"line {line_number} must be an object")
            cases.append(case)
        return cases

    def test_judgment_benchmark_fixture_contains_audited_50_case_set(self):
        cases = self.load_cases()
        self.assertEqual(len(cases), 50)
        self.assertEqual([case["case_number"] for case in cases], list(range(1, 51)))
        self.assertEqual(len({case["case_id"] for case in cases}), 50)

        negative_cases = [case for case in cases if case["case_type"] == "negative_control"]
        self.assertEqual(len(negative_cases), 12)
        self.assertEqual(
            [case["case_number"] for case in negative_cases],
            [7, 25, 28, 29, 31, 32, 35, 43, 44, 45, 46, 47],
        )

        for case in cases:
            for field in (
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
            ):
                self.assertIn(field, case, f"{case.get('case_id')} missing {field}")
            self.assertEqual(case["schema_version"], "mindthus-judgment-benchmark-case-v0.1")
            self.assertEqual(case["benchmark_id"], "mindthus-judgment-50-v1")
            self.assertIsInstance(case["positive_wakeup_expected"], bool)
            self.assertIsInstance(case["stay_asleep_expected"], bool)
            self.assertIsInstance(case["multi_turn"], bool)
            self.assertTrue(str(case["prompt"]).strip())
            self.assertTrue(str(case["pass_criteria"]).strip())
            self.assertTrue(str(case["fail_signal"]).strip())

    def test_multiturn_cases_are_scriptable(self):
        cases = {case["case_number"]: case for case in self.load_cases()}
        for case_number in (12, 35, 50):
            case = cases[case_number]
            self.assertTrue(case["multi_turn"], f"case {case_number} must be marked multi-turn")
            turns = case.get("turns")
            self.assertIsInstance(turns, list, f"case {case_number} must include scripted turns")
            self.assertGreaterEqual(len(turns), 2)
            for turn in turns:
                self.assertIsInstance(turn, dict)
                self.assertIn("role", turn)
                self.assertIn("content", turn)

    def test_benchmark_docs_define_execution_and_reporting_contract(self):
        for path in (BENCHMARK_DOC, LATEST_DOC):
            self.assertTrue(path.is_file(), f"{path.relative_to(REPO)} should exist")

        benchmark = BENCHMARK_DOC.read_text(encoding="utf-8")
        latest = LATEST_DOC.read_text(encoding="utf-8")
        readme = (REPO / "README.md").read_text(encoding="utf-8")

        for phrase in (
            "independent SubAgent or CLI harness",
            "hot-updated Mindthus",
            "loaded_files",
            "shadow set",
            "positive mean >= 1.5 / 2",
            "negative false wake-up rate <= 10%",
            "first-sentence lock rate",
            "verdict-commitment / anti-mush rate",
            "over-forced verdict rate",
            "shadow set must not regress",
            "multi-turn",
            "raw responses",
        ):
            self.assertIn(phrase, benchmark)

        for phrase in (
            "Not yet certified",
            "baseline",
            "baseline+Mindthus",
            "treatment - baseline",
            "installed-code fingerprint",
            "first-sentence lock rate",
            "verdict-commitment / anti-mush rate",
            "over-forced verdict rate",
        ):
            self.assertIn(phrase, latest)

        self.assertIn("docs/benchmarks/latest.md", readme)


if __name__ == "__main__":
    unittest.main()
