import json
import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CASESET = REPO / "tests" / "judgment_benchmark_50_cases.jsonl"
BRAKE_TRIAGE_DEV_FIXTURE = REPO / "tests" / "brake_semantic_triage_dev_cases.jsonl"
BRAKE_TRIAGE_TEXT_PACKET = REPO / "docs" / "benchmarks" / "brake-semantic-triage-calibration-dev-texts-v0.2.md"
BRAKE_TRIAGE_PROMPT_SHA256 = "e237bd69fe4d247017acc8b9f6dad31068d55925be369230862c4f0ddd772b9d"
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

    def load_jsonl(self, path: Path) -> list[dict[str, object]]:
        self.assertTrue(path.is_file(), f"missing fixture {path.relative_to(REPO)}")
        records: list[dict[str, object]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                self.fail(f"invalid JSON on line {line_number}: {exc}")
            self.assertIsInstance(record, dict, f"line {line_number} must be an object")
            records.append(record)
        return records

    def packet_items(self) -> dict[str, dict[str, str]]:
        self.assertTrue(BRAKE_TRIAGE_TEXT_PACKET.is_file())
        packet = BRAKE_TRIAGE_TEXT_PACKET.read_text(encoding="utf-8")
        items: dict[str, dict[str, str]] = {}
        current: str | None = None
        for line in packet.splitlines():
            header = re.match(r"^([PNS][0-9]{2})\s+(.+)$", line)
            if header:
                current = header.group(1)
                items[current] = {"slug": header.group(2)}
                continue
            if current is None:
                continue
            field = re.match(r"^- (Text|Turn 1|Turn 2|Family|Negative type): (.+)$", line)
            if field:
                items[current][field.group(1)] = field.group(2)
        return items

    def test_brake_semantic_triage_dev_fixture_matches_review_packet(self):
        cases = self.load_jsonl(BRAKE_TRIAGE_DEV_FIXTURE)
        packet = self.packet_items()
        by_id = {case["case_id"]: case for case in cases}

        self.assertEqual(len(cases), 31)
        self.assertEqual(sum(1 for case in cases if case["case_type"] == "positive" and not case["multi_turn"]), 12)
        self.assertEqual(sum(1 for case in cases if case["case_type"] == "negative_control"), 15)
        self.assertEqual(sum(1 for case in cases if case["case_type"] == "positive" and case["multi_turn"]), 4)
        self.assertEqual({case["metadata"]["prompt_sha256"] for case in cases}, {BRAKE_TRIAGE_PROMPT_SHA256})
        self.assertEqual({case["metadata"]["triage_threshold"] for case in cases}, {0.90})
        self.assertEqual({case["metadata"]["triage_certification_mode"] for case in cases}, {"diagnostic_only"})

        family_counts: dict[str, int] = {}
        for case in cases:
            if case["case_type"] == "positive" and not case["multi_turn"]:
                family = case["metadata"]["means_type_family"]
                family_counts[family] = family_counts.get(family, 0) + 1
        self.assertEqual(
            family_counts,
            {
                "A information overlay layer": 3,
                "B manual verification gate": 3,
                "C routing or queue split": 3,
                "D form or template capture field": 3,
            },
        )

        for idx in range(1, 13):
            key = f"P{idx:02d}"
            case = by_id[f"brake-triage-{key.lower()}"]
            self.assertEqual(case["prompt"], packet[key]["Text"])
            self.assertEqual(case["metadata"]["source_packet_id"], key)
            self.assertEqual(case["metadata"]["means_type_family"], packet[key]["Family"])

        for idx in range(1, 16):
            key = f"N{idx:02d}"
            case = by_id[f"brake-triage-{key.lower()}"]
            self.assertEqual(case["prompt"], packet[key]["Text"])
            self.assertEqual(case["metadata"]["source_packet_id"], key)
            self.assertEqual(case["metadata"]["negative_type"], packet[key]["Negative type"])

        for idx in range(1, 5):
            key = f"S{idx:02d}"
            case = by_id[f"brake-triage-{key.lower()}"]
            self.assertTrue(case["multi_turn"])
            self.assertEqual(case["turns"][0]["content"], packet[key]["Turn 1"])
            self.assertEqual(case["turns"][1]["content"], packet[key]["Turn 2"])
            self.assertEqual(case["metadata"]["source_packet_id"], key)

        for key in ("N13", "N14", "N15"):
            case = by_id[f"brake-triage-{key.lower()}"]
            self.assertEqual(case["case_type"], "negative_control")
            self.assertEqual(case["metadata"]["negative_type"], "legal-convergence-sn3")
            self.assertTrue(case["stay_asleep_expected"])

    def test_post_v2_fixture_edges_are_explicit(self):
        cases = {case["case_number"]: case for case in self.load_cases()}

        case_30 = cases[30]
        self.assertIn("技术风险", case_30["prompt"])
        self.assertIn("市场风险", case_30["prompt"])
        self.assertIn("只有风险类别没有决策信息", case_30["pass_criteria"])

        case_48 = cases[48]
        self.assertIn("定义权归属", case_48["pass_criteria"])
        self.assertIn("soft denial", case_48["score_scale"])

        case_49 = cases[49]
        self.assertIn("没有实测数据", case_49["pass_criteria"])
        self.assertIn("不得用假设数字计算最终结论", case_49["pass_criteria"])
        self.assertIn("invented numbers", case_49["score_scale"])

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
