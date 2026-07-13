import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def compact(path: str) -> str:
    return " ".join(read(path).split())


def read_jsonl(path: str) -> list[dict]:
    return [
        json.loads(line)
        for line in read(path).splitlines()
        if line.strip()
    ]


class V3AuditOptimizationContractTests(unittest.TestCase):
    def test_using_mindthus_has_thin_before_route_entry_triage_index(self):
        text = read("skills/using-mindthus/SKILL.md")
        for phrase in (
            "Entry Triage / 入口分诊",
            "semantic-family index",
            "not keywords",
        ):
            self.assertIn(phrase, text)

    def test_entry_triage_doc_registers_v3_trigger_families_with_guardrails(self):
        text = compact("docs/methodologies/primitives/entry-triage.md").lower()
        for phrase in (
            "definition authority contest",
            "single-factor attribution",
            "local repair spiral",
            "forced binary prediction",
            "no-data numeric comparison",
            "trend-driven migration",
            "green tests imply release readiness",
            "X is just Y, therefore impossible",
            "business success reduced to one factor",
            "third prompt rule or third fallback",
            "who is right plus active buy or decide context",
            "hypothetical numbers must not decide",
            "negative and shadow controls",
            "v5/#104 no-load stabilization register",
            "authority or tenure used as root-cause proof plus requested incident write-up",
            "trend label used as migration mandate",
            "local green signal treated as release authorization",
            "business/store success reduced to one product attribute before copywriting",
            "forced yes/no replacement prediction over role/task family",
            "third local prompt rule after two failed edits",
            "third fallback branch after two fallbacks or unstable tests",
            "definition/essence reduction to communication/tactic only",
            "no measured data plus concrete numeric risk comparison",
        ):
            self.assertIn(phrase.lower(), text)

    def test_entry_triage_doc_clarifies_edsp_sela_aqm_ownership(self):
        text = compact("docs/methodologies/primitives/entry-triage.md").lower()
        for phrase in (
            "EDSP owns bare A/B structural choice",
            "SELA owns local expertise versus automation scale",
            "if both appear, EDSP exposes the axis before SELA checks system efficiency",
            "AQM stays inside the active judgment owner",
            "invented arithmetic must not become the decision basis",
        ):
            self.assertIn(phrase.lower(), text)

    def test_entry_triage_doc_contains_loaded_behavior_gates(self):
        text = compact("docs/methodologies/primitives/entry-triage.md").lower()
        for phrase in (
            "root-cause evidence gate",
            "timeline and metrics before conclusion",
            "same local repair count >= 3",
            "must stop adding and move upstream or equal-replace",
            "visible consequence probe",
        ):
            self.assertIn(phrase.lower(), text)

    def test_entry_triage_separates_no_load_triggers_from_loaded_action_probes(self):
        entry = compact("docs/methodologies/primitives/entry-triage.md")
        contract = compact("skills/using-mindthus/resources/fidelity-contract.md")

        self.assertIn("third prompt rule, third fallback, or next local patch after instability", entry)
        self.assertIn("Anti-Spiral hard brake", entry)
        self.assertIn("anti_spiral_brake_before_addition", contract)
        self.assertIn("loaded owners must put the case-critical action into visible prose", contract)

    def test_v5_target_trigger_register_covers_no_load_cases(self):
        register = json.loads(read("docs/benchmarks/v5-target-trigger-register.json"))
        expected_cases = {2, 3, 4, 8, 13, 17, 33, 34, 37, 48, 49}

        cases = register["cases"]

        self.assertEqual(register["schema_version"], "mindthus-v5-target-trigger-register-v0.1")
        self.assertEqual({case["case_number"] for case in cases}, expected_cases)
        for case in cases:
            self.assertEqual(case["patch_type"], "mechanical_runtime")
            self.assertIn("target_anchor", case)
            self.assertIn("semantic_features", case)
            self.assertGreaterEqual(len(case["semantic_features"]), 1)
            self.assertIn("accepted_runtime_owners", case)
            self.assertIn("preferred_runtime_owner", case)
            self.assertIn(case["preferred_runtime_owner"], case["accepted_runtime_owners"])
            self.assertIn("required_action_probe", case)
            self.assertIn("hint_action", case)
            self.assertIn("negative_boundary", case)
            self.assertNotIn("wording", case["status"])

    def test_v5_issue_108_register_probes_are_not_public_case_keys(self):
        register = json.loads(read("docs/benchmarks/v5-target-trigger-register.json"))
        cases = {case["case_number"]: case for case in register["cases"]}

        def flattened(case_number: int, *keys: str) -> str:
            chunks = []
            for key in keys:
                value = cases[case_number].get(key)
                chunks.append(json.dumps(value, ensure_ascii=False))
            return " ".join(chunks)

        case_8_feature_text = flattened(8, "semantic_features")
        for banned in ("下一个词", "统计预测器", "不可能真正推理", "专栏论证"):
            self.assertNotIn(banned, case_8_feature_text)

        case_13_action_text = flattened(13, "required_action_probe", "hint_action")
        for banned in ("coffee", "bean", "咖啡豆", "location", "repurchase", "floor efficiency", "brand"):
            self.assertNotIn(banned, case_13_action_text)
        self.assertIn("domain-appropriate non-local result controllers", case_13_action_text)

        case_37_action_text = flattened(37, "required_action_probe", "hint_action")
        for banned in ("B has more definition authority", "PPI", "HiDPI"):
            self.assertNotIn(banned, case_37_action_text)
        self.assertIn("active decision", case_37_action_text)

        case_37_features = cases[37]["semantic_features"]
        for feature in case_37_features:
            self.assertNotIn("PPI", feature.get("match_all", []))
            self.assertNotIn("HiDPI", feature.get("match_all", []))

        case_49_features = cases[49]["semantic_features"]
        for feature in case_49_features:
            self.assertNotIn("风险敞口", feature.get("match_all", []))
        self.assertIn("conclusion-like comparison", flattened(49, "required_action_probe", "hint_action"))

    def test_v5_brake_semantic_features_are_disease_level_not_implementation_keys(self):
        register = json.loads(read("docs/benchmarks/v5-target-trigger-register.json"))
        cases = {case["case_number"]: case for case in register["cases"]}
        feature_text = json.dumps(
            {
                "case_33": cases[33]["semantic_features"],
                "case_34": cases[34]["semantic_features"],
            },
            ensure_ascii=False,
        )
        term_text = json.dumps(
            [
                {
                    key: feature.get(key)
                    for key in ("match_all", "match_any", "negative_any", "hint_action")
                    if key in feature
                }
                for case_number in (33, 34)
                for feature in cases[case_number]["semantic_features"]
            ],
            ensure_ascii=False,
        )

        for banned in (
            "prompt",
            "fallback",
            "!important",
            "覆盖",
            "分支",
            "正则",
            "case",
            "邮箱",
            "漏网",
            "兜底",
            "规则",
            "同类",
            "类似",
            "同一类",
            "都是",
            "一样",
        ):
            self.assertNotIn(banned, term_text)

        for required in (
            "same_class_local_patch",
            "count_at_least_three",
            "next_same_class_patch_request",
        ):
            self.assertIn(required, feature_text)

    def test_brake_dev_fixture_contains_non_code_positive_and_near_negative_cases(self):
        cases = read_jsonl("tests/brake_dev_cases.jsonl")
        positives = [case for case in cases if case["case_type"] == "positive"]
        negatives = [case for case in cases if case["case_type"] == "negative_control"]

        self.assertGreaterEqual(len(positives), 2)
        self.assertGreaterEqual(len(negatives), 1)
        for case in positives:
            prompt = case["prompt"]
            self.assertIn("group_id", case)
            self.assertEqual(case["group_id"], "H")
            self.assertEqual(case["expected_owner"], "anti_spiral")
            self.assertRegex(prompt, r"再[加补]一")
            self.assertIn("same-class local repair", case["pass_criteria"])
            self.assertNotIn("prompt", prompt.lower())
            self.assertNotIn("fallback", prompt.lower())
            self.assertNotIn("正则", prompt)
            for marker in ("同类", "类似", "同一类", "都是", "一样"):
                self.assertNotIn(marker, prompt)

        pressure_cases = [
            case
            for case in positives
            if case.get("multi_turn") and len(case.get("turns") or []) >= 2
        ]
        self.assertGreaterEqual(len(pressure_cases), 1)
        for case in pressure_cases:
            contract = case["pass_criteria"]
            for required in ("one-time", "no baseline lift", "structural repair deadline"):
                self.assertIn(required, contract)

        for case in negatives:
            self.assertTrue(case["stay_asleep_expected"])
            self.assertFalse(case["positive_wakeup_expected"])
            self.assertIn("mixed unrelated prior changes", case["pass_criteria"])

    def test_brake_loaded_action_probe_contains_bounded_emergency_pressure_contract(self):
        register = json.loads(read("docs/benchmarks/v5-target-trigger-register.json"))
        cases = {case["case_number"]: case for case in register["cases"]}
        action_text = json.dumps(
            {
                "case_33": {
                    "required_action_probe": cases[33]["required_action_probe"],
                    "hint_action": cases[33]["hint_action"],
                },
                "case_34": {
                    "required_action_probe": cases[34]["required_action_probe"],
                    "hint_action": cases[34]["hint_action"],
                },
            },
            ensure_ascii=False,
        )

        for required in ("bounded emergency", "one-time", "no baseline lift", "structural repair deadline"):
            self.assertIn(required, action_text)

    def test_manifest_exposes_entry_triage_to_primitive_activation(self):
        text = read("scripts/primitives/manifest.json")
        for phrase in (
            '"entry_triage"',
            "definition authority contest",
            "single-factor attribution",
            "local repair spiral",
            "forced binary prediction",
            "no-data numeric comparison",
            "trend-driven migration",
            "which_entry_triage_family_if_any",
        ):
            self.assertIn(phrase, text)

    def test_latest_links_external_audit_handoff(self):
        latest = read("docs/benchmarks/latest.md")
        self.assertIn("EXTERNAL_AUDIT_HANDOFF.md", latest)

    def test_external_handoff_records_v4_measurement_follow_up(self):
        handoff = read(
            "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/"
            "EXTERNAL_AUDIT_HANDOFF.md"
        )
        for phrase in (
            "V4 Measurement Follow-Up Requested By Audit",
            "judge calibration examples",
            "Repeat-run moved or borderline cases",
            "fixture diff explanation",
            "judge model and blind-grading setup",
            "baseline loaded command",
            "shadow-set regression as a certification veto",
        ):
            self.assertIn(phrase, handoff)


if __name__ == "__main__":
    unittest.main()
