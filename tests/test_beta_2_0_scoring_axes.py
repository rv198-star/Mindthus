import json
import unittest
from pathlib import Path

from tests.test_judgment_benchmark_cli_runner import CASESET, load_runner


REPO = Path(__file__).resolve().parents[1]
CASE_SCHEMA = REPO / "beta" / "2.0.0-beta.2" / "evaluation-case.schema.json"


def load_command(skill: str) -> str:
    return f"Read /tmp/plugins/cache/mindthus/mindthus/2.0.0-beta.1/skills/{skill}/SKILL.md"


def beta2_case(
    case_id: str,
    *,
    expected_owner: str,
    execution_owner: str,
    primitives: list[str] | None = None,
    required_loads: list[str] | None = None,
    allowed_loads: list[str] | None = None,
    stay_asleep: bool = False,
    lifecycle: list[str] | None = None,
) -> dict:
    return {
        "schema_version": "mindthus-beta2-evaluation-case-v0.1",
        "case_id": case_id,
        "case_number": int(case_id.rsplit("-", 1)[-1]),
        "case_type": "negative_control" if stay_asleep else "positive",
        "group_id": "B2",
        "group_name": "Beta.2 axis fixture",
        "expected_owner": expected_owner,
        "expected_execution_owner": execution_owner,
        "accepted_execution_owners": [] if stay_asleep else [execution_owner],
        "expected_primitive_obligations": primitives or [],
        "required_visible_action": "Expose the required bounded action." if primitives else None,
        "required_skill_loads": required_loads or [],
        "allowed_skill_loads": allowed_loads or [],
        "positive_wakeup_expected": not stay_asleep,
        "stay_asleep_expected": stay_asleep,
        "expected_lifecycle_events": lifecycle or [],
        "prompt": "fixture",
        "pass_criteria": "fixture pass",
        "fail_signal": "fixture fail",
        "score_scale": "0/1/2",
    }


def score_for(
    case: dict,
    *,
    behavior: bool,
    observed_owner: str | None = None,
    primitive_results: dict[str, bool] | None = None,
    unexpected_primitive: bool | None = None,
    lifecycle_events: list[str] | None = None,
) -> dict:
    score = {
        "case_id": case["case_id"],
        "case_number": case["case_number"],
        "case_type": case["case_type"],
        "group_id": case["group_id"],
        "score": 2 if behavior else 0,
        "pass_criteria_met": behavior,
        "positive_wakeup_observed": False if case["stay_asleep_expected"] else behavior,
        "rationale": "fixture",
    }
    if observed_owner is not None:
        score["observed_execution_owner"] = observed_owner
    if primitive_results is not None:
        score["primitive_obligation_results"] = primitive_results
        score["required_visible_action_present"] = all(primitive_results.values())
    if unexpected_primitive is not None:
        score["unexpected_primitive_action_observed"] = unexpected_primitive
    if lifecycle_events is not None:
        score["observed_lifecycle_events"] = lifecycle_events
    return score


class BetaTwoScoringAxesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def augment(self, case: dict, score: dict, commands: list[str] | None = None) -> dict:
        response = {} if commands is None else {"loaded_commands_all_turns": commands}
        return self.runner.augment_score_with_telemetry(case, response, score)

    def test_correct_kernel_only_action_passes_without_using_mindthus_load(self) -> None:
        case = beta2_case(
            "beta2-101",
            expected_owner="input_framing_audit",
            execution_owner="direct_answer",
            primitives=["input_framing_audit"],
            required_loads=[],
            allowed_loads=[],
            lifecycle=["before-answer"],
        )
        score = score_for(
            case,
            behavior=True,
            observed_owner="direct_answer",
            primitive_results={"input_framing_audit": True},
            unexpected_primitive=False,
            lifecycle_events=["before-answer"],
        )

        result = self.augment(case, score, [])

        self.assertTrue(result["owner_semantic_success"])
        self.assertTrue(result["execution_owner_fidelity"])
        self.assertTrue(result["primitive_action_recall"])
        self.assertTrue(result["primitive_action_precision"])
        self.assertTrue(result["lifecycle_fidelity"])
        self.assertEqual(result["actual_skill_load_path"], [])
        self.assertEqual(result["skill_load_verdict"], "no_load_required")
        self.assertTrue(result["skill_load_contract_satisfied"])
        self.assertFalse(result["expected_owner_loaded"])
        self.assertEqual(
            result["owner_fidelity_verdict_semantics"], "legacy-load-compatibility"
        )

    def test_direct_owner_and_genuine_arbitration_have_independent_success_axes(self) -> None:
        fixtures = [
            ("beta2-102", "edsp", "edsp"),
            ("beta2-103", "using-mindthus", "using-mindthus"),
        ]
        for case_id, owner, skill in fixtures:
            with self.subTest(owner=owner):
                case = beta2_case(
                    case_id,
                    expected_owner=owner,
                    execution_owner=owner,
                    required_loads=[skill],
                    allowed_loads=[skill],
                )
                result = self.augment(
                    case,
                    score_for(case, behavior=True, observed_owner=owner),
                    [load_command(skill)],
                )
                self.assertTrue(result["owner_semantic_success"])
                self.assertTrue(result["execution_owner_fidelity"])
                self.assertTrue(result["required_skill_loads_satisfied"])
                self.assertEqual(result["skill_load_verdict"], "required_load_observed")

    def test_wrong_owner_and_missed_passive_obligation_are_separate_failures(self) -> None:
        wrong_owner = beta2_case(
            "beta2-104",
            expected_owner="edsp",
            execution_owner="edsp",
            required_loads=["edsp"],
            allowed_loads=["edsp"],
        )
        wrong = self.augment(
            wrong_owner,
            score_for(wrong_owner, behavior=False, observed_owner="mpg"),
            [load_command("mpg")],
        )
        self.assertFalse(wrong["execution_owner_fidelity"])
        self.assertEqual(wrong["execution_owner_fidelity_verdict"], "wrong_owner_observed")
        self.assertEqual(wrong["skill_load_verdict"], "unexpected_load")

        missed_case = beta2_case(
            "beta2-105",
            expected_owner="input_framing_audit",
            execution_owner="direct_answer",
            primitives=["input_framing_audit"],
        )
        missed = self.augment(
            missed_case,
            score_for(
                missed_case,
                behavior=False,
                observed_owner="direct_answer",
                primitive_results={"input_framing_audit": False},
            ),
            [],
        )
        self.assertTrue(missed["execution_owner_fidelity"])
        self.assertFalse(missed["primitive_action_recall"])
        self.assertEqual(missed["primitive_action_recall_verdict"], "missed")
        self.assertEqual(missed["skill_load_verdict"], "no_load_required")

    def test_unnecessary_using_load_and_stay_asleep_are_visible_without_overwriting_behavior(self) -> None:
        kernel_case = beta2_case(
            "beta2-106",
            expected_owner="input_framing_audit",
            execution_owner="direct_answer",
            primitives=["input_framing_audit"],
        )
        unnecessary = self.augment(
            kernel_case,
            score_for(
                kernel_case,
                behavior=True,
                observed_owner="direct_answer",
                primitive_results={"input_framing_audit": True},
            ),
            [load_command("using-mindthus")],
        )
        self.assertTrue(unnecessary["owner_semantic_success"])
        self.assertTrue(unnecessary["primitive_action_recall"])
        self.assertEqual(unnecessary["skill_load_verdict"], "unexpected_load")
        self.assertFalse(unnecessary["skill_load_contract_satisfied"])

        asleep_case = beta2_case(
            "beta2-107",
            expected_owner="direct_answer",
            execution_owner="direct_answer",
            stay_asleep=True,
        )
        asleep = self.augment(asleep_case, score_for(asleep_case, behavior=True), [])
        self.assertTrue(asleep["owner_semantic_success"])
        self.assertIsNone(asleep["execution_owner_fidelity"])
        self.assertTrue(asleep["primitive_action_precision"])
        self.assertFalse(asleep["runtime_false_wakeup"])
        self.assertEqual(asleep["skill_load_verdict"], "stay_asleep")

    def test_missing_load_telemetry_is_unknown_not_pass_or_fail(self) -> None:
        case = beta2_case(
            "beta2-108",
            expected_owner="edsp",
            execution_owner="edsp",
            required_loads=["edsp"],
            allowed_loads=["edsp"],
        )
        result = self.augment(
            case,
            score_for(case, behavior=True, observed_owner="edsp"),
            None,
        )
        self.assertTrue(result["owner_semantic_success"])
        self.assertEqual(result["skill_load_telemetry_status"], "missing")
        self.assertIsNone(result["actual_skill_load_path"])
        self.assertIsNone(result["required_skill_loads_satisfied"])
        self.assertIsNone(result["runtime_false_wakeup"])
        self.assertIsNone(result["expected_owner_loaded"])
        self.assertEqual(result["skill_load_verdict"], "unknown_missing_telemetry")

    def test_public_v5_cases_use_compatibility_adapter_without_losing_legacy_loads(self) -> None:
        cases = [json.loads(line) for line in CASESET.read_text(encoding="utf-8").splitlines()]
        for case in cases:
            contract = self.runner.normalized_case_evaluation_contract(case)
            self.assertEqual(contract["contract_source"], "v5-legacy-adapter")
            self.assertTrue(
                set(contract["required_skill_loads"]).issubset(contract["allowed_skill_loads"])
            )
            self.assertEqual(
                set(contract["allowed_skill_loads"]),
                self.runner.expected_owner_skills(case),
            )

    def test_summary_never_substitutes_load_success_for_semantic_success(self) -> None:
        kernel_case = beta2_case(
            "beta2-109",
            expected_owner="input_framing_audit",
            execution_owner="direct_answer",
            primitives=["input_framing_audit"],
        )
        kernel = self.augment(
            kernel_case,
            score_for(
                kernel_case,
                behavior=True,
                observed_owner="direct_answer",
                primitive_results={"input_framing_audit": True},
            ),
            [],
        )
        arbitration_case = beta2_case(
            "beta2-110",
            expected_owner="using-mindthus",
            execution_owner="using-mindthus",
            required_loads=["using-mindthus"],
            allowed_loads=["using-mindthus"],
        )
        arbitration = self.augment(
            arbitration_case,
            score_for(arbitration_case, behavior=False, observed_owner="using-mindthus"),
            [load_command("using-mindthus")],
        )

        summary = self.runner.summarize([kernel, arbitration])

        self.assertEqual(summary["schema_version"], "mindthus-judgment-cli-summary-v0.3")
        self.assertEqual(summary["behavior_axes"]["owner_semantic_success_rate"], 0.5)
        self.assertEqual(summary["behavior_axes"]["primitive_action_recall_rate"], 1.0)
        self.assertEqual(summary["runtime_load_axes"]["required_skill_load_success_rate"], 1.0)
        self.assertEqual(summary["legacy_compatibility"]["expected_owner_loaded_rate"], 0.5)
        self.assertEqual(
            summary["legacy_compatibility"]["semantics"],
            "load-path compatibility only; not a behavior-success axis",
        )

    def test_case_schema_versions_the_new_fields(self) -> None:
        schema = json.loads(CASE_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["$id"],
            "https://mindthus.dev/schemas/beta2-evaluation-case-v0.1.json",
        )
        self.assertIn("expected_primitive_obligations", schema["required"])
        self.assertIn("required_skill_loads", schema["required"])
        self.assertIn("expected_lifecycle_events", schema["required"])


if __name__ == "__main__":
    unittest.main()
