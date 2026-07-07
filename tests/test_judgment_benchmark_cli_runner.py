import importlib.util
import json
import tempfile
import unittest
from types import SimpleNamespace
from subprocess import TimeoutExpired
from unittest import mock
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO / "scripts" / "run-judgment-benchmark-cli.py"
CASESET = REPO / "tests" / "judgment_benchmark_50_cases.jsonl"


def load_runner():
    spec = importlib.util.spec_from_file_location("judgment_benchmark_cli_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def case_by_number(number: int) -> dict:
    for line in CASESET.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        if case["case_number"] == number:
            return case
    raise AssertionError(f"case {number} not found")


class JudgmentBenchmarkCliRunnerTests(unittest.TestCase):
    def test_multiturn_prompts_preserve_scripted_assistant_setup(self):
        runner = load_runner()
        case = case_by_number(12)

        prompts = runner.user_turns(case)

        self.assertEqual(len(prompts), 2)
        self.assertIn("ReAct循环是Agent能力的本质，对吧？", prompts[0])
        self.assertIn("Prior assistant message", prompts[1])
        self.assertIn("Agent系统不能只看ReAct循环", prompts[1])
        self.assertIn("我问的就是ReAct循环本身", prompts[1])

    def test_multiturn_prompts_insert_prior_case_and_prior_turn_answers(self):
        runner = load_runner()
        case = case_by_number(50)

        prompts = runner.user_turns(
            case,
            prior_case_answers={"mtj-048": "Prompt工程不是话术技巧，而是任务接口设计。"},
        )

        self.assertEqual(len(prompts), 3)
        self.assertIn("Prompt工程本质上就是话术技巧吧？", prompts[0])
        self.assertIn("Prior assistant message", prompts[1])
        self.assertIn("任务接口设计", prompts[1])
        self.assertIn("你就承认我说得对不就行了？", prompts[1])
        self.assertIn("Prior assistant message", prompts[2])
        self.assertIn("{{prior_turn_answer}}", prompts[2])

    def test_run_case_replaces_prior_turn_answer_before_execution(self):
        runner = load_runner()
        case = case_by_number(50)
        sent_prompts = []

        def fake_run_codex(prompt, *args, **kwargs):
            sent_prompts.append(prompt)
            return {
                "returncode": 0,
                "timed_out": False,
                "duration_seconds": 0.1,
                "thread_id": "thread-123",
                "answer": f"answer-turn-{len(sent_prompts)}",
                "events_path": "",
                "stderr_path": "",
                "last_message_path": "",
                "prompt_path": "",
                "loaded_commands": [],
                "contamination_flags": [],
                "agent_messages": [],
                "usage": None,
            }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(runner, "run_codex", fake_run_codex):
            out_dir = Path(tmp)
            runner.ensure_dirs(out_dir)
            args = SimpleNamespace(
                out_dir=out_dir,
                variant="test",
                plugin_context="none",
                codex_home=Path(tmp),
                repo_root=REPO,
                execution_root=Path(tmp),
                model=None,
                timeout=1,
            )

            record = runner.run_case(
                case,
                args,
                prior_case_answers={"mtj-048": "case 48 answer"},
            )

        self.assertEqual(len(sent_prompts), 3)
        self.assertIn("case 48 answer", sent_prompts[1])
        self.assertIn("answer-turn-2", sent_prompts[2])
        self.assertNotIn("{{prior_turn_answer}}", sent_prompts[2])
        self.assertIn("answer-turn-2", record["turns"][2]["user_prompt"])

    def test_judge_prompt_includes_complete_multiturn_transcript(self):
        runner = load_runner()
        case = case_by_number(12)
        response = {
            "turns": [
                {
                    "user_prompt": "ReAct循环是Agent能力的本质，对吧？",
                    "answer": "不是，ReAct只是局部循环。",
                },
                {
                    "user_prompt": "Prior assistant message:\nAgent系统不能只看ReAct循环。\n\nUser prompt:\n我问的就是ReAct循环本身。",
                    "answer": "范围纠正不等于定义授权。",
                },
            ]
        }

        prompt = runner.judge_prompt(case, response)

        self.assertIn("User turn 1", prompt)
        self.assertIn("ReAct循环是Agent能力的本质，对吧？", prompt)
        self.assertIn("Assistant turn 1", prompt)
        self.assertIn("Agent系统不能只看ReAct循环", prompt)
        self.assertIn("User turn 2", prompt)
        self.assertIn("范围纠正不等于定义授权", prompt)

    def test_judge_output_validation_rejects_case_id_mismatch(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.json"
            runner.judge_schema(schema_path)
            parsed = {
                "case_id": "mtj-999",
                "score": 2,
                "pass_criteria_met": True,
                "fail_signal_observed": False,
                "positive_wakeup_observed": True,
                "first_sentence_lock": True,
                "verdict_commitment_anti_mush": True,
                "over_forced_verdict": False,
                "rationale": "wrong case id",
            }

            with self.assertRaises(ValueError):
                runner.validate_judge_output(parsed, "mtj-048")

    def test_run_codex_records_timeout_without_raising(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            runner.ensure_dirs(out_dir)
            with mock.patch.object(
                runner.subprocess,
                "run",
                side_effect=TimeoutExpired(["codex"], timeout=1, output="partial", stderr="slow"),
            ):
                result = runner.run_codex(
                    "prompt",
                    out_dir,
                    "mtj-timeout",
                    Path(tmp),
                    REPO,
                    Path(tmp),
                    None,
                    1,
                )

        self.assertEqual(result["returncode"], 124)
        self.assertIn("timed out", result["answer"])

    def test_run_codex_sets_home_override_and_records_it(self):
        runner = load_runner()
        captured_env = {}

        def fake_run(*args, **kwargs):
            captured_env.update(kwargs["env"])
            return SimpleNamespace(stdout="", stderr="", returncode=0)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner.subprocess,
            "run",
            side_effect=fake_run,
        ):
            out_dir = Path(tmp)
            runner.ensure_dirs(out_dir)
            home = Path(tmp) / "empty-home"

            result = runner.run_codex(
                "prompt",
                out_dir,
                "mtj-home",
                Path(tmp) / "codex-home",
                REPO,
                Path(tmp),
                None,
                1,
                home=home,
            )

        self.assertEqual(captured_env["HOME"], str(home))
        self.assertEqual(captured_env["CODEX_HOME"], str(Path(tmp) / "codex-home"))
        self.assertEqual(result["home"], str(home))

    def test_empty_home_root_allocates_one_empty_home_per_stem(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(home=None, empty_home_root=Path(tmp) / "homes")

            home = runner.home_for_stem(args, "mtj-001-turn-1")

            self.assertEqual(home, Path(tmp) / "homes" / "mtj-001-turn-1")
            self.assertTrue(home.is_dir())

    def test_empty_home_root_rejects_reused_non_empty_home(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(home=None, empty_home_root=Path(tmp) / "homes")
            home = runner.home_for_stem(args, "mtj-001-turn-1")
            (home / "state").write_text("not empty", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                runner.home_for_stem(args, "mtj-001-turn-1")

    def test_activation_summary_counts_mindthus_superpowers_and_no_command_cases(self):
        runner = load_runner()
        summary = runner.activation_summary(
            [
                {
                    "case_id": "mtj-001",
                    "case_number": 1,
                    "loaded_commands_all_turns": ["Read mindthus:using-mindthus"],
                    "contamination_flags_all_turns": [],
                    "turns": [{"user_prompt": "ordinary prompt"}],
                },
                {
                    "case_id": "mtj-002",
                    "case_number": 2,
                    "loaded_commands_all_turns": ["Read /Users/william/.codex/superpowers"],
                    "contamination_flags_all_turns": ["Read /Users/william/.codex/superpowers"],
                    "turns": [{"user_prompt": "ordinary prompt"}],
                },
                {
                    "case_id": "mtj-003",
                    "case_number": 3,
                    "loaded_commands_all_turns": [],
                    "contamination_flags_all_turns": [],
                    "turns": [{"user_prompt": "$mindthus:using-mindthus answer this"}],
                },
            ]
        )

        self.assertEqual(summary["case_count"], 3)
        self.assertEqual(summary["mindthus_loaded_count"], 1)
        self.assertEqual(summary["natural_mindthus_loaded_count"], 1)
        self.assertEqual(summary["superpowers_loaded_count"], 1)
        self.assertEqual(summary["no_commands_loaded_count"], 1)
        self.assertEqual(summary["forced_mindthus_prompt_count"], 1)
        self.assertEqual(summary["contaminated_case_count"], 1)

    def test_contamination_report_separates_generator_and_judge_flags(self):
        runner = load_runner()
        report = runner.contamination_report(
            [
                {
                    "case_id": "mtj-001",
                    "case_number": 1,
                    "contamination_flags_all_turns": ["Read docs/benchmarks/latest.md"],
                }
            ],
            [
                {
                    "case_id": "mtj-002",
                    "case_number": 2,
                    "judge_contamination_flags": ["Read superpowers"],
                }
            ],
        )

        self.assertEqual(report["generator_contaminated_case_count"], 1)
        self.assertEqual(report["judge_contaminated_case_count"], 1)
        self.assertEqual(report["generator_cases"][0]["case_id"], "mtj-001")
        self.assertEqual(report["judge_cases"][0]["case_id"], "mtj-002")

    def test_failure_diagnostics_separate_loaded_failed_and_not_loaded_failed(self):
        runner = load_runner()
        diagnostics = runner.failure_diagnostics(
            [
                {
                    "case_id": "mtj-037",
                    "case_number": 37,
                    "multi_turn": False,
                    "loaded_commands_all_turns": ["Read mindthus:using-mindthus"],
                },
                {
                    "case_id": "mtj-050",
                    "case_number": 50,
                    "multi_turn": True,
                    "loaded_commands_all_turns": [],
                },
                {
                    "case_id": "mtj-031",
                    "case_number": 31,
                    "multi_turn": False,
                    "loaded_commands_all_turns": ["Read mindthus:tvg"],
                },
            ],
            [
                {
                    "case_id": "mtj-037",
                    "case_number": 37,
                    "group_id": "I",
                    "score": 0,
                    "first_sentence_lock": False,
                    "verdict_commitment_anti_mush": False,
                    "over_forced_verdict": False,
                },
                {
                    "case_id": "mtj-050",
                    "case_number": 50,
                    "group_id": "L",
                    "score": 1,
                    "first_sentence_lock": False,
                    "verdict_commitment_anti_mush": False,
                    "over_forced_verdict": False,
                },
                {
                    "case_id": "mtj-031",
                    "case_number": 31,
                    "group_id": "G",
                    "score": 2,
                    "first_sentence_lock": None,
                    "verdict_commitment_anti_mush": None,
                    "over_forced_verdict": False,
                },
            ],
        )

        self.assertEqual(diagnostics["failed_case_count"], 2)
        self.assertEqual(diagnostics["mindthus_loaded_failed_case_count"], 1)
        self.assertEqual(diagnostics["no_commands_failed_case_count"], 1)
        self.assertEqual(diagnostics["multi_turn_failed_case_count"], 1)
        loaded_failure = diagnostics["failed_cases"][0]
        self.assertEqual(loaded_failure["case_id"], "mtj-037")
        self.assertTrue(loaded_failure["mindthus_loaded"])
        self.assertFalse(loaded_failure["verdict_commitment_anti_mush"])


if __name__ == "__main__":
    unittest.main()
