import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BENCH = REPO / "tests" / "activation_benchmark"
CASES = BENCH / "cases.jsonl"
SCORER = BENCH / "score_activation.py"
SKILLS = {"3l5s", "edsp", "sela", "wae", "tvg", "tplan"}
AUTO_SKILLS = {"3l5s", "edsp", "sela", "wae"}
MANUAL_ONLY_SKILLS = {"tvg", "tplan"}
FORBIDDEN_PROMPT_TERMS = {"3l5s", "edsp", "sela", "wae", "tvg", "tplan", "mindthus"}


def read_jsonl(path):
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        record["_line"] = line_number
        records.append(record)
    return records


def write_jsonl(path, records):
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


class ActivationBenchmarkTests(unittest.TestCase):
    def test_case_file_has_valid_schema_and_coverage(self):
        cases = read_jsonl(CASES)
        self.assertGreaterEqual(len(cases), 40)
        seen_ids = set()
        skill_counts = Counter()
        negative_count = 0
        manual_only_probe_count = 0

        for case in cases:
            with self.subTest(case=case.get("id", case["_line"])):
                self.assertIsInstance(case.get("id"), str)
                self.assertNotIn(case["id"], seen_ids)
                seen_ids.add(case["id"])

                prompt = case.get("prompt")
                self.assertIsInstance(prompt, str)
                self.assertGreater(len(prompt.strip()), 10)
                lowered = prompt.lower()
                for term in FORBIDDEN_PROMPT_TERMS:
                    self.assertNotIn(term, lowered)

                should_trigger = case.get("should_trigger")
                self.assertIsInstance(should_trigger, bool)
                acceptable = case.get("acceptable_skills")
                self.assertIsInstance(acceptable, list)
                self.assertTrue(all(skill in SKILLS for skill in acceptable))
                self.assertIsInstance(case.get("tags"), list)

                expected = case.get("expected_skill")
                if should_trigger:
                    self.assertIn(expected, AUTO_SKILLS)
                    self.assertIn(expected, acceptable)
                    skill_counts[expected] += 1
                else:
                    self.assertIsNone(expected)
                    self.assertEqual(acceptable, [])
                    negative_count += 1
                    if case["id"].split("-", 1)[0] in MANUAL_ONLY_SKILLS:
                        manual_only_probe_count += 1

        for skill in AUTO_SKILLS:
            self.assertGreaterEqual(skill_counts[skill], 5, skill)
        for skill in MANUAL_ONLY_SKILLS:
            self.assertEqual(skill_counts[skill], 0, skill)
        self.assertGreaterEqual(negative_count, 18)
        self.assertGreaterEqual(manual_only_probe_count, 12)

    def test_scorer_computes_activation_metrics(self):
        cases = [
            {
                "id": "c1",
                "prompt": "问题很乱, 明天不知道先做什么",
                "should_trigger": True,
                "expected_skill": "3l5s",
                "acceptable_skills": ["3l5s"],
                "tags": ["positive"],
            },
            {
                "id": "c2",
                "prompt": "边界不清, 也涉及控制权",
                "should_trigger": True,
                "expected_skill": "edsp",
                "acceptable_skills": ["edsp", "wae"],
                "tags": ["mixed"],
            },
            {
                "id": "c3",
                "prompt": "文档完整但很空",
                "should_trigger": False,
                "expected_skill": None,
                "acceptable_skills": [],
                "tags": ["manual_only_probe"],
            },
            {
                "id": "c4",
                "prompt": "把这句话翻译成英文",
                "should_trigger": False,
                "expected_skill": None,
                "acceptable_skills": [],
                "tags": ["negative"],
            },
            {
                "id": "c5",
                "prompt": "列出当前目录",
                "should_trigger": False,
                "expected_skill": None,
                "acceptable_skills": [],
                "tags": ["negative"],
            },
        ]
        results = [
            {"case_id": "c1", "selected_skill": "3l5s"},
            {"case_id": "c2", "selected_skill": "wae"},
            {"case_id": "c3", "selected_skill": None},
            {"case_id": "c4", "selected_skill": None},
            {"case_id": "c5", "selected_skill": "tplan"},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            cases_path = Path(tmp) / "cases.jsonl"
            results_path = Path(tmp) / "results.jsonl"
            write_jsonl(cases_path, cases)
            write_jsonl(results_path, results)

            run = subprocess.run(
                [sys.executable, str(SCORER), "--cases", str(cases_path), "--results", str(results_path)],
                text=True,
                capture_output=True,
            )

        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertAlmostEqual(report["metrics"]["recall"], 1.0)
        self.assertAlmostEqual(report["metrics"]["precision"], 2 / 3)
        self.assertAlmostEqual(report["metrics"]["route_at_1"], 1 / 2)
        self.assertAlmostEqual(report["metrics"]["over_trigger_rate"], 1 / 3)
        self.assertEqual(report["confusion_matrix"]["edsp"]["wae"], 1)
        self.assertEqual(report["confusion_matrix"]["none"]["tplan"], 1)

    def test_scorer_rejects_missing_results(self):
        cases = [
            {
                "id": "c1",
                "prompt": "问题很乱, 明天不知道先做什么",
                "should_trigger": True,
                "expected_skill": "3l5s",
                "acceptable_skills": ["3l5s"],
                "tags": ["positive"],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            cases_path = Path(tmp) / "cases.jsonl"
            results_path = Path(tmp) / "results.jsonl"
            write_jsonl(cases_path, cases)
            write_jsonl(results_path, [])

            run = subprocess.run(
                [sys.executable, str(SCORER), "--cases", str(cases_path), "--results", str(results_path)],
                text=True,
                capture_output=True,
            )

        self.assertNotEqual(run.returncode, 0)
        self.assertIn("missing result for case c1", run.stderr)


if __name__ == "__main__":
    unittest.main()
