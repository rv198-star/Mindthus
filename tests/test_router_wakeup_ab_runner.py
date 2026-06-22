import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "router-wakeup-ab.py"


def scored_record(
    *,
    experiment: str,
    scenario_id: str,
    run_id: int,
    variant: str,
    expected_owner: str,
    selected_owner: str,
    case_type: str,
    correct_owner: bool,
    execution_impact: bool = True,
    skip_correct: bool | None = None,
    evidence_ceiling_respected: bool = True,
    adjacent_absorption: str = "none",
    over_methodized: bool = False,
) -> dict[str, object]:
    return {
        "schema_version": "mindthus-router-wakeup-ab-v0.1",
        "experiment": experiment,
        "scenario_id": scenario_id,
        "run_id": run_id,
        "variant": variant,
        "expected_owner": expected_owner,
        "selected_owner": selected_owner,
        "case_type": case_type,
        "correct_owner": correct_owner,
        "positive_wakeup": correct_owner if case_type == "positive" else None,
        "skip_correct": skip_correct,
        "execution_impact": execution_impact,
        "adjacent_absorption": adjacent_absorption,
        "over_methodized": over_methodized,
        "evidence_ceiling_respected": evidence_ceiling_respected,
        "notes": f"{scenario_id}-{run_id}-{variant}",
    }


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records)
        + "\n",
        encoding="utf-8",
    )


def add_positive_pair(
    records: list[dict[str, object]],
    *,
    experiment: str,
    method: str,
    run_id: int,
    baseline_pass: bool,
    treatment_pass: bool,
) -> None:
    scenario_id = f"{experiment}-{method}-positive"
    records.append(
        scored_record(
            experiment=experiment,
            scenario_id=scenario_id,
            run_id=run_id,
            variant="baseline",
            expected_owner=method,
            selected_owner=method if baseline_pass else "3l5s",
            case_type="positive",
            correct_owner=baseline_pass,
            adjacent_absorption="none" if baseline_pass else "3l5s",
        )
    )
    records.append(
        scored_record(
            experiment=experiment,
            scenario_id=scenario_id,
            run_id=run_id,
            variant="treatment",
            expected_owner=method,
            selected_owner=method if treatment_pass else "3l5s",
            case_type="positive",
            correct_owner=treatment_pass,
            adjacent_absorption="none" if treatment_pass else "3l5s",
        )
    )


def add_skip_pair(
    records: list[dict[str, object]],
    *,
    experiment: str,
    scenario_id: str,
    run_id: int,
    treatment_skip_pass: bool = True,
) -> None:
    records.append(
        scored_record(
            experiment=experiment,
            scenario_id=scenario_id,
            run_id=run_id,
            variant="baseline",
            expected_owner="information_acquisition",
            selected_owner="information_acquisition",
            case_type="skip",
            correct_owner=True,
            skip_correct=True,
        )
    )
    records.append(
        scored_record(
            experiment=experiment,
            scenario_id=scenario_id,
            run_id=run_id,
            variant="treatment",
            expected_owner="information_acquisition",
            selected_owner="information_acquisition" if treatment_skip_pass else "sela",
            case_type="skip",
            correct_owner=treatment_skip_pass,
            skip_correct=treatment_skip_pass,
            over_methodized=not treatment_skip_pass,
        )
    )


class RouterWakeupABRunnerTests(unittest.TestCase):
    def test_repository_documents_executable_runner_and_fixture(self):
        design = (REPO / "tests" / "router_wakeup_ab_experiment_design.md").read_text(
            encoding="utf-8"
        )
        fixture = REPO / "tests" / "router_wakeup_ab_scores.fixture.jsonl"
        weak_cue_cases = REPO / "tests" / "router_wakeup_weak_cue_holdout_cases.md"
        for phrase in (
            "scripts/router-wakeup-ab.py",
            "--scores",
            "--experiment known",
            "--fail-on-uncertified",
            "Discriminability Gate",
            "baseline-ceiling",
            "weak-cue",
            "router_wakeup_weak_cue_holdout_cases.md",
            "router_wakeup_ab_scores.fixture.jsonl",
            "minimum-pairs",
        ):
            self.assertIn(phrase, design)
        self.assertTrue(fixture.is_file())
        self.assertTrue(weak_cue_cases.is_file())

        result = subprocess.run(
            ["python3", str(RUNNER), "--scores", str(fixture), "--experiment", "known", "--json"],
            text=True,
            capture_output=True,
            cwd=REPO,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema_version"], "mindthus-router-wakeup-ab-v0.1")
        self.assertEqual(report["experiment"], "known")

    def test_weak_cue_holdout_cases_are_designed_for_discrimination(self):
        text = (REPO / "tests" / "router_wakeup_weak_cue_holdout_cases.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Weak-Cue Router Wake-Up Holdout Cases",
            "No method names in prompts",
            "baseline-ceiling",
            "WH-S1",
            "WH-S2",
            "WH-M1",
            "WH-M2",
            "WH-E1",
            "WH-E2",
            "Adjacent skip traps",
            "Expected owner: `sela`",
            "Expected owner: `mpg`",
            "Expected owner: `edsp`",
        ):
            self.assertIn(phrase, text)
        prompt_blocks = [line for line in text.splitlines() if line.startswith("Prompt:")]
        forbidden = ("SELA", "MPG", "EDSP", "Wake-Up Probes")
        for line in prompt_blocks:
            for token in forbidden:
                self.assertNotIn(token, line)

    def test_weak_cue_calibration_run_records_baseline_ceiling_failure(self):
        text = (
            REPO / "tests" / "router_wakeup_weak_cue_calibration_2026-06-17.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "Router Wake-Up Weak-Cue Calibration Run",
            "certified=false",
            "baseline-ceiling",
            "Baseline positive wake-up recall: 100%",
            "Treatment positive wake-up recall: 100%",
            "Do not expand this sample",
            "real-use replay",
        ):
            self.assertIn(phrase, text)

    def test_runner_flags_baseline_ceiling_when_known_set_has_no_discriminability(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores.jsonl"
            records: list[dict[str, object]] = []
            for method_index, method in enumerate(("sela", "mpg", "edsp")):
                for run in range(4):
                    add_positive_pair(
                        records,
                        experiment="known",
                        method=method,
                        run_id=method_index * 10 + run,
                        baseline_pass=True,
                        treatment_pass=True,
                    )
            for run in range(12):
                add_skip_pair(
                    records,
                    experiment="known",
                    scenario_id=f"known-skip-{run % 3}",
                    run_id=run,
                )
            write_jsonl(scores, records)

            result = subprocess.run(
                [
                    "python3",
                    str(RUNNER),
                    "--scores",
                    str(scores),
                    "--experiment",
                    "known",
                    "--json",
                    "--fail-on-uncertified",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["certified"])
            self.assertIn("baseline-ceiling", report["failed_checks"])
            self.assertTrue(report["discriminability"]["baseline_ceiling"])
            self.assertEqual(report["discriminability"]["max_baseline_positive_recall"], 0.75)

    def test_known_experiment_certifies_significant_lift_and_skip_noninferiority(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores.jsonl"
            records: list[dict[str, object]] = []
            for method_index, method in enumerate(("sela", "mpg", "edsp")):
                for run in range(10):
                    add_positive_pair(
                        records,
                        experiment="known",
                        method=method,
                        run_id=method_index * 10 + run,
                        baseline_pass=run < 1,
                        treatment_pass=run < 9,
                    )
            for run in range(30):
                add_skip_pair(
                    records,
                    experiment="known",
                    scenario_id=f"known-skip-{run % 3}",
                    run_id=run,
                    treatment_skip_pass=run != 0,
                )
            write_jsonl(scores, records)

            result = subprocess.run(
                [
                    "python3",
                    str(RUNNER),
                    "--scores",
                    str(scores),
                    "--experiment",
                    "known",
                    "--json",
                    "--fail-on-uncertified",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertTrue(report["certified"])
            self.assertEqual(report["experiment"], "known")
            self.assertGreaterEqual(report["positive_wakeup"]["lift"], 0.25)
            self.assertLessEqual(report["positive_wakeup"]["mcnemar_p"], 0.05)
            self.assertIn("confidence_interval_95", report["positive_wakeup"])
            self.assertGreater(report["positive_wakeup"]["confidence_interval_95"]["lower"], 0)
            self.assertTrue(report["skip_precision"]["noninferior"])
            self.assertTrue(report["execution_impact"]["nondecreasing"])

    def test_runner_blocks_unpaired_variant_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores.jsonl"
            write_jsonl(
                scores,
                [
                    scored_record(
                        experiment="known",
                        scenario_id="known-sela-positive",
                        run_id=1,
                        variant="baseline",
                        expected_owner="sela",
                        selected_owner="3l5s",
                        case_type="positive",
                        correct_owner=False,
                    )
                ],
            )

            result = subprocess.run(
                ["python3", str(RUNNER), "--scores", str(scores), "--experiment", "known"],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing-pair", result.stdout)

    def test_holdout_requires_each_low_frequency_method_to_lift(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores.jsonl"
            records: list[dict[str, object]] = []
            for method in ("sela", "mpg"):
                for run in range(20):
                    add_positive_pair(
                        records,
                        experiment="holdout",
                        method=method,
                        run_id=run,
                        baseline_pass=run < 2,
                        treatment_pass=run < 16,
                    )
            for run in range(20):
                add_positive_pair(
                    records,
                    experiment="holdout",
                    method="edsp",
                    run_id=run,
                    baseline_pass=run < 10,
                    treatment_pass=run < 10,
                )
            for run in range(30):
                add_skip_pair(
                    records,
                    experiment="holdout",
                    scenario_id=f"holdout-skip-{run % 6}",
                    run_id=run,
                )
            write_jsonl(scores, records)

            result = subprocess.run(
                [
                    "python3",
                    str(RUNNER),
                    "--scores",
                    str(scores),
                    "--experiment",
                    "holdout",
                    "--json",
                    "--fail-on-uncertified",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["certified"])
            self.assertIn("method-lift-edsp", report["failed_checks"])
            self.assertIn("method-mcnemar-edsp", report["failed_checks"])
            self.assertIn("method_mcnemar", report)
            self.assertIn("holm_adjusted_p", report["method_mcnemar"]["sela"])

    def test_real_use_replay_requires_minimum_routing_moments_before_certification(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores.jsonl"
            records: list[dict[str, object]] = []
            for run in range(10):
                add_positive_pair(
                    records,
                    experiment="real_use",
                    method="sela",
                    run_id=run,
                    baseline_pass=False,
                    treatment_pass=True,
                )
            write_jsonl(scores, records)

            result = subprocess.run(
                [
                    "python3",
                    str(RUNNER),
                    "--scores",
                    str(scores),
                    "--experiment",
                    "real_use",
                    "--json",
                    "--fail-on-uncertified",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["certified"])
            self.assertIn("minimum-pairs", report["failed_checks"])
            self.assertEqual(report["minimums"]["required_pairs"], 50)
            self.assertEqual(report["minimums"]["observed_pairs"], 10)

    def test_markdown_report_states_claim_ceiling(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            scores = tmp_dir / "scores.jsonl"
            report_path = tmp_dir / "report.md"
            records: list[dict[str, object]] = []
            for method_index, method in enumerate(("sela", "mpg", "edsp")):
                for run in range(10):
                    add_positive_pair(
                        records,
                        experiment="known",
                        method=method,
                        run_id=method_index * 10 + run,
                        baseline_pass=False,
                        treatment_pass=True,
                    )
            for run in range(30):
                add_skip_pair(
                    records,
                    experiment="known",
                    scenario_id=f"known-skip-{run % 3}",
                    run_id=run,
                )
            write_jsonl(scores, records)

            result = subprocess.run(
                [
                    "python3",
                    str(RUNNER),
                    "--scores",
                    str(scores),
                    "--experiment",
                    "known",
                    "--write-report",
                    str(report_path),
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("Router Wake-Up A/B Report", report)
            self.assertIn("Minimum Sample Gate", report)
            self.assertIn("Claim Ceiling", report)
            self.assertIn(
                "The router wake-up mechanism works on the designed acceptance scenarios.",
                report,
            )

    def test_schema_validation_blocks_invalid_scored_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores.jsonl"
            invalid_variant = scored_record(
                experiment="known",
                scenario_id="known-invalid-variant",
                run_id=1,
                variant="baseline",
                expected_owner="sela",
                selected_owner="sela",
                case_type="positive",
                correct_owner=True,
            )
            invalid_variant["variant"] = "control"

            invalid_case = scored_record(
                experiment="known",
                scenario_id="known-invalid-case",
                run_id=1,
                variant="baseline",
                expected_owner="sela",
                selected_owner="sela",
                case_type="positive",
                correct_owner=True,
            )
            invalid_case["case_type"] = "mystery"

            bad_absorption = scored_record(
                experiment="known",
                scenario_id="known-bad-absorption",
                run_id=1,
                variant="baseline",
                expected_owner="sela",
                selected_owner="3l5s",
                case_type="positive",
                correct_owner=False,
            )
            bad_absorption["adjacent_absorption"] = "default_sink"

            mismatched_wakeup = scored_record(
                experiment="known",
                scenario_id="known-mismatched-wakeup",
                run_id=1,
                variant="baseline",
                expected_owner="sela",
                selected_owner="3l5s",
                case_type="positive",
                correct_owner=False,
            )
            mismatched_wakeup["positive_wakeup"] = True

            duplicate_a = scored_record(
                experiment="known",
                scenario_id="known-duplicate",
                run_id=1,
                variant="baseline",
                expected_owner="sela",
                selected_owner="sela",
                case_type="positive",
                correct_owner=True,
            )
            duplicate_b = dict(duplicate_a)
            write_jsonl(
                scores,
                [
                    invalid_variant,
                    invalid_case,
                    bad_absorption,
                    mismatched_wakeup,
                    duplicate_a,
                    duplicate_b,
                ],
            )

            result = subprocess.run(
                ["python3", str(RUNNER), "--scores", str(scores), "--experiment", "known"],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertNotEqual(result.returncode, 0)
            for phrase in (
                "invalid-variant",
                "invalid-case-type",
                "invalid-adjacent-absorption",
                "positive-wakeup-mismatch",
                "duplicate-pair",
            ):
                self.assertIn(phrase, result.stdout)

    def test_overuse_stress_certifies_false_positive_guardrail(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores.jsonl"
            records: list[dict[str, object]] = []
            stress_types = ("direct", "missing_evidence", "deterministic", "tvg", "3l5s")
            for index, case_type in enumerate(stress_types):
                for run in range(10):
                    scenario_id = f"overuse-{case_type}"
                    expected = "tvg" if case_type == "tvg" else case_type
                    records.append(
                        scored_record(
                            experiment="overuse",
                            scenario_id=scenario_id,
                            run_id=index * 10 + run,
                            variant="baseline",
                            expected_owner=expected,
                            selected_owner=expected,
                            case_type=case_type,
                            correct_owner=True,
                        )
                    )
                    records.append(
                        scored_record(
                            experiment="overuse",
                            scenario_id=scenario_id,
                            run_id=index * 10 + run,
                            variant="treatment",
                            expected_owner=expected,
                            selected_owner=expected,
                            case_type=case_type,
                            correct_owner=True,
                        )
                    )
            write_jsonl(scores, records)

            result = subprocess.run(
                [
                    "python3",
                    str(RUNNER),
                    "--scores",
                    str(scores),
                    "--experiment",
                    "overuse",
                    "--json",
                    "--fail-on-uncertified",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertTrue(report["certified"])
            self.assertTrue(report["overuse"]["false_positive_noninferior"])
            self.assertTrue(report["overuse"]["direct_route_preserved"])
            self.assertTrue(report["overuse"]["missing_evidence_route_preserved"])

    def test_overuse_stress_requires_each_stress_bucket(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores.jsonl"
            records: list[dict[str, object]] = []
            stress_types = ("direct", "missing_evidence", "tvg", "3l5s")
            for index, case_type in enumerate(stress_types):
                for run in range(10):
                    scenario_id = f"overuse-{case_type}"
                    expected = "tvg" if case_type == "tvg" else case_type
                    records.append(
                        scored_record(
                            experiment="overuse",
                            scenario_id=scenario_id,
                            run_id=index * 10 + run,
                            variant="baseline",
                            expected_owner=expected,
                            selected_owner=expected,
                            case_type=case_type,
                            correct_owner=True,
                        )
                    )
                    records.append(
                        scored_record(
                            experiment="overuse",
                            scenario_id=scenario_id,
                            run_id=index * 10 + run,
                            variant="treatment",
                            expected_owner=expected,
                            selected_owner=expected,
                            case_type=case_type,
                            correct_owner=True,
                        )
                    )
            write_jsonl(scores, records)

            result = subprocess.run(
                [
                    "python3",
                    str(RUNNER),
                    "--scores",
                    str(scores),
                    "--experiment",
                    "overuse",
                    "--json",
                    "--fail-on-uncertified",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["certified"])
            self.assertIn("minimum-deterministic", report["failed_checks"])
            self.assertEqual(report["minimums"]["case_type_counts"]["deterministic"], 0)


if __name__ == "__main__":
    unittest.main()
