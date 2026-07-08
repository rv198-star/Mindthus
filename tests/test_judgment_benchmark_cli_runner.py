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

    def test_run_case_can_apply_v5_register_hint_diagnostic_mode(self):
        runner = load_runner()
        case = case_by_number(33)
        sent_prompts = []

        def fake_run_codex(prompt, *args, **kwargs):
            sent_prompts.append(prompt)
            return {
                "returncode": 0,
                "timed_out": False,
                "duration_seconds": 0.1,
                "thread_id": "thread-v5-hint",
                "answer": "stop adding rules; move upstream first",
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
                variant="diagnostic-v5-register-hints",
                plugin_context="mindthus",
                codex_home=Path(tmp),
                repo_root=REPO,
                execution_root=Path(tmp),
                model=None,
                timeout=1,
                v5_register_hints=True,
            )

            record = runner.run_case(case, args)

        self.assertIn("Host diagnostic activation hint", sent_prompts[0])
        self.assertIn("mindthus:3l5s", sent_prompts[0])
        self.assertIn("Anti-Spiral brake before addition", sent_prompts[0])
        self.assertTrue(record["activation_hint_applied"])
        self.assertIn("mindthus:3l5s", record["activation_hints_all_turns"][0])

    def test_v5_register_hint_is_case_id_matched(self):
        runner = load_runner()
        case = dict(case_by_number(33))
        case["case_id"] = "mtj-stale"

        self.assertIsNone(runner.v5_register_hint_for_case(case, enabled=True))

    def test_v5_register_hint_for_17_forces_malformed_binary_reconstruction(self):
        runner = load_runner()
        hint = runner.v5_register_hint_for_case(case_by_number(17), enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("mindthus:edsp", hint)
        self.assertIn("malformed binary", hint)
        self.assertIn("first sentence", hint)
        self.assertIn("reconstruct", hint)

    def test_v5_semantic_triage_hint_matches_shadow_case_without_case_id(self):
        runner = load_runner()
        shadow_case = dict(case_by_number(17))
        shadow_case["case_id"] = "shadow-role-replacement"
        shadow_case["case_number"] = 1701
        shadow_case["prompt"] = "AI 到底会不会替代设计师？只回答会或不会。"

        hint = runner.v5_semantic_triage_hint_for_case(shadow_case, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage hint", hint)
        self.assertIn("mindthus:edsp", hint)
        self.assertIn("malformed binary", hint)
        self.assertNotIn("mtj-017", hint)
        self.assertNotIn("case_number", hint)

    def test_v5_semantic_triage_matches_same_class_override_spiral_without_case_id(self):
        runner = load_runner()
        brake_case = {
            "case_id": "external-brake-override",
            "case_number": 3301,
            "prompt": "这个页面的对齐又被新组件弄坏了。前面三处我们都是加 `!important` 覆盖解决的，这次也一样，帮我写一个覆盖规则把它压下去。",
        }

        hint = runner.v5_semantic_triage_hint_for_case(brake_case, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage hint", hint)
        self.assertIn("mindthus:3l5s", hint)
        self.assertIn("Anti-Spiral brake", hint)
        self.assertNotIn("mtj-033", hint)
        self.assertNotIn("case_number", hint)

    def test_v5_semantic_triage_matches_same_class_regex_branch_spiral_without_case_id(self):
        runner = load_runner()
        brake_case = {
            "case_id": "external-brake-regex",
            "case_number": 3302,
            "turns": [
                {
                    "role": "user",
                    "content": "邮箱校验正则又漏了一种格式（plus 别名）。我已经为前三个漏网格式各补了一个分支，帮我再补一个分支把这种也包进去。",
                },
                {
                    "role": "user",
                    "content": "别搞那么复杂，就加这一个 case 就好，我们要上线。",
                },
            ],
        }

        hint = runner.v5_semantic_triage_hint_for_case(brake_case, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage hint", hint)
        self.assertIn("mindthus:3l5s", hint)
        self.assertIn("Anti-Spiral brake", hint)
        self.assertNotIn("mtj-034", hint)
        self.assertNotIn("case_number", hint)

    def test_v5_semantic_triage_keeps_mixed_change_count_near_negative_asleep(self):
        runner = load_runner()
        near_negative = {
            "case_id": "external-brake-near-negative",
            "case_number": 3303,
            "prompt": "这个模块这周改了三次了：一次修拼写、一次升依赖、一次加新字段。现在产品又提了个新需求，要再加一个导出按钮，帮我写一下。",
        }

        hint = runner.v5_semantic_triage_hint_for_case(near_negative, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage stay-asleep hint", hint)
        self.assertIn("mixed unrelated prior changes", hint)
        self.assertIn("do not load Anti-Spiral or 3L5S", hint)
        self.assertNotIn("mindthus:", hint)

    def test_v5_semantic_triage_keeps_method_reference_review_direct(self):
        runner = load_runner()
        hint = runner.v5_semantic_triage_hint_for_case(case_by_number(25), enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage stay-asleep hint", hint)
        self.assertIn("evidence review", hint)
        self.assertIn("do not load MPG", hint)
        self.assertNotIn("mindthus:", hint)

    def test_runner_source_does_not_embed_local_superpowers_path(self):
        source = RUNNER_PATH.read_text(encoding="utf-8")

        self.assertNotIn("/Users/william/.codex/superpowers", source)

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
                {
                    "case_id": "mtj-033",
                    "case_number": 33,
                    "loaded_commands_all_turns": ["Read mindthus:3l5s"],
                    "contamination_flags_all_turns": [],
                    "activation_hint_applied": True,
                    "turns": [
                        {
                            "user_prompt": "ordinary prompt",
                            "activation_hint": "Host diagnostic activation hint: route through mindthus:3l5s",
                        }
                    ],
                },
            ]
        )

        self.assertEqual(summary["case_count"], 4)
        self.assertEqual(summary["mindthus_loaded_count"], 2)
        self.assertEqual(summary["natural_mindthus_loaded_count"], 1)
        self.assertEqual(summary["superpowers_loaded_count"], 1)
        self.assertEqual(summary["no_commands_loaded_count"], 1)
        self.assertEqual(summary["forced_mindthus_prompt_count"], 1)
        self.assertEqual(summary["activation_hint_applied_count"], 1)
        self.assertEqual(summary["contaminated_case_count"], 1)

    def test_loaded_owner_detection_follows_skill_entrypoints(self):
        runner = load_runner()

        owners = runner.loaded_owners_from_commands(
            [
                "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/using-mindthus/SKILL.md\"",
                "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/edsp/SKILL.md\"",
                "Read mindthus:edsp",
                "echo edsp is mentioned but not loaded",
            ]
        )

        self.assertEqual(owners, ["using-mindthus", "edsp"])

    def test_activation_summary_records_loaded_owner(self):
        runner = load_runner()

        summary = runner.activation_summary(
            [
                {
                    "case_id": "mtj-037",
                    "case_number": 37,
                    "loaded_commands_all_turns": [
                        "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/using-mindthus/SKILL.md\"",
                        "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/edsp/SKILL.md\"",
                    ],
                    "contamination_flags_all_turns": [],
                    "turns": [{"user_prompt": "ordinary prompt"}],
                }
            ]
        )

        self.assertEqual(summary["case_summaries"][0]["loaded_owner"], ["using-mindthus", "edsp"])

    def test_generic_mindthus_path_is_not_counted_as_skill_load(self):
        runner = load_runner()
        command = "cd /tmp/mindthus-benchmark-workspace && pwd"

        summary = runner.activation_summary(
            [
                {
                    "case_id": "mtj-002",
                    "case_number": 2,
                    "loaded_commands_all_turns": [command],
                    "contamination_flags_all_turns": [],
                    "turns": [{"user_prompt": "ordinary prompt"}],
                }
            ]
        )
        augmented = runner.augment_score_with_telemetry(
            case_by_number(2),
            {"loaded_commands_all_turns": [command]},
            {
                "case_id": "mtj-002",
                "score": 0,
                "pass_criteria_met": False,
                "positive_wakeup_observed": False,
            },
        )

        self.assertEqual(summary["mindthus_loaded_count"], 0)
        self.assertEqual(summary["case_summaries"][0]["loaded_owner"], [])
        self.assertFalse(augmented["mindthus_loaded"])
        self.assertEqual(augmented["owner_fidelity_verdict"], "no_load")

    def test_owner_telemetry_splits_runtime_and_final_answer_false_wakeup(self):
        runner = load_runner()
        case = case_by_number(32)
        response = {
            "loaded_commands_all_turns": [
                "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/3l5s/SKILL.md\""
            ]
        }
        score = {
            "case_id": "mtj-032",
            "score": 2,
            "pass_criteria_met": True,
            "positive_wakeup_observed": False,
        }

        augmented = runner.augment_score_with_telemetry(case, response, score)

        self.assertFalse(augmented["false_wakeup_final_answer"])
        self.assertTrue(augmented["false_wakeup_runtime_event"])
        self.assertFalse(augmented["expected_owner_loaded"])
        self.assertIsNone(augmented["required_visible_action_present"])
        self.assertEqual(augmented["owner_fidelity_verdict"], "runtime_over_wake")

    def test_owner_telemetry_marks_wrong_loaded_owner(self):
        runner = load_runner()
        case = case_by_number(15)
        response = {
            "loaded_commands_all_turns": [
                "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/mpg/SKILL.md\"",
                "/bin/zsh -lc \"sed -n '1,180p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/sela/SKILL.md\"",
            ]
        }
        score = {
            "case_id": "mtj-015",
            "score": 1,
            "pass_criteria_met": False,
            "positive_wakeup_observed": True,
        }

        augmented = runner.augment_score_with_telemetry(case, response, score)

        self.assertEqual(augmented["loaded_owner"], ["mpg", "sela"])
        self.assertFalse(augmented["expected_owner_loaded"])
        self.assertEqual(augmented["accepted_loaded_owners"], ["edsp"])
        self.assertEqual(augmented["owner_fidelity_verdict"], "wrong_owner_loaded")

    def test_owner_telemetry_marks_expected_owner_and_no_load(self):
        runner = load_runner()
        expected = runner.augment_score_with_telemetry(
            case_by_number(37),
            {
                "loaded_commands_all_turns": [
                    "Read /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/using-mindthus/SKILL.md",
                    "Read /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/edsp/SKILL.md",
                ]
            },
            {
                "case_id": "mtj-037",
                "score": 2,
                "pass_criteria_met": True,
                "positive_wakeup_observed": True,
            },
        )
        no_load = runner.augment_score_with_telemetry(
            case_by_number(48),
            {"loaded_commands_all_turns": []},
            {
                "case_id": "mtj-048",
                "score": 0,
                "pass_criteria_met": False,
                "positive_wakeup_observed": False,
            },
        )

        self.assertTrue(expected["expected_owner_loaded"])
        self.assertEqual(expected["owner_fidelity_verdict"], "expected_owner_loaded")
        self.assertFalse(no_load["expected_owner_loaded"])
        self.assertEqual(no_load["owner_fidelity_verdict"], "no_load")

    def test_summarize_reports_dual_false_wakeup_and_owner_rates(self):
        runner = load_runner()
        scores = [
            {
                "case_id": "mtj-032",
                "case_number": 32,
                "case_type": "negative_control",
                "group_id": "G",
                "score": 2,
                "pass_criteria_met": True,
                "positive_wakeup_observed": False,
                "first_sentence_lock": None,
                "verdict_commitment_anti_mush": None,
                "over_forced_verdict": False,
                "false_wakeup_final_answer": False,
                "false_wakeup_runtime_event": True,
                "expected_owner_loaded": False,
                "required_visible_action_present": None,
                "owner_fidelity_verdict": "runtime_over_wake",
                "rationale": "",
            },
            {
                "case_id": "mtj-043",
                "case_number": 43,
                "case_type": "negative_control",
                "group_id": "K",
                "score": 0,
                "pass_criteria_met": False,
                "positive_wakeup_observed": True,
                "first_sentence_lock": None,
                "verdict_commitment_anti_mush": None,
                "over_forced_verdict": True,
                "false_wakeup_final_answer": True,
                "false_wakeup_runtime_event": False,
                "expected_owner_loaded": True,
                "required_visible_action_present": None,
                "owner_fidelity_verdict": "direct_stay_asleep",
                "rationale": "",
            },
            {
                "case_id": "mtj-037",
                "case_number": 37,
                "case_type": "positive",
                "group_id": "I",
                "score": 2,
                "pass_criteria_met": True,
                "positive_wakeup_observed": True,
                "first_sentence_lock": True,
                "verdict_commitment_anti_mush": True,
                "over_forced_verdict": False,
                "false_wakeup_final_answer": False,
                "false_wakeup_runtime_event": False,
                "expected_owner_loaded": True,
                "required_visible_action_present": True,
                "owner_fidelity_verdict": "expected_owner_loaded",
                "mindthus_loaded": True,
                "superpowers_loaded": False,
                "rationale": "",
            },
        ]

        summary = runner.summarize(scores)

        self.assertEqual(summary["negative_false_wakeup_rate"], 0.5)
        self.assertEqual(summary["negative_false_wakeup_final_answer_rate"], 0.5)
        self.assertEqual(summary["negative_false_wakeup_runtime_event_rate"], 0.5)
        self.assertEqual(summary["expected_owner_loaded_rate"], 0.667)
        self.assertEqual(summary["positive_expected_owner_loaded_rate"], 1.0)
        self.assertEqual(summary["negative_runtime_stay_asleep_rate"], 0.5)
        self.assertEqual(summary["required_visible_action_rate"], 1.0)
        self.assertEqual(summary["loaded_required_visible_action_rate"], 1.0)
        self.assertEqual(summary["owner_fidelity_counts"]["runtime_over_wake"], 1)
        self.assertEqual(summary["owner_fidelity_counts"]["expected_owner_loaded"], 1)

    def test_v5_target_activation_diagnostics_uses_register(self):
        runner = load_runner()

        diagnostics = runner.v5_target_activation_diagnostics(
            [
                {
                    "case_id": "mtj-002",
                    "case_number": 2,
                    "expected_owner_loaded": False,
                    "owner_fidelity_verdict": "no_load",
                    "loaded_owner": [],
                    "required_visible_action_present": False,
                },
                {
                    "case_id": "mtj-017",
                    "case_number": 17,
                    "expected_owner_loaded": False,
                    "owner_fidelity_verdict": "wrong_owner_loaded",
                    "loaded_owner": ["mpg"],
                    "required_visible_action_present": False,
                },
                {
                    "case_id": "mtj-033",
                    "case_number": 33,
                    "expected_owner_loaded": True,
                    "owner_fidelity_verdict": "expected_owner_loaded",
                    "loaded_owner": ["3l5s"],
                    "required_visible_action_present": True,
                },
            ]
        )

        self.assertEqual(diagnostics["registered_case_count"], 9)
        self.assertEqual(diagnostics["selected_registered_case_count"], 3)
        self.assertEqual(diagnostics["expected_owner_loaded_rate"], 0.333)
        self.assertEqual(diagnostics["no_load_case_numbers"], [2])
        self.assertEqual(diagnostics["wrong_owner_case_numbers"], [17])
        self.assertEqual(diagnostics["expected_owner_loaded_case_numbers"], [33])
        self.assertIn(34, diagnostics["not_selected_registered_case_numbers"])
        case_33 = [case for case in diagnostics["case_diagnostics"] if case["case_number"] == 33][0]
        self.assertIn("Anti-Spiral", case_33["required_action_probe"])
        self.assertEqual(case_33["register_owner_fidelity_verdict"], "expected_owner_loaded")

    def test_v5_target_activation_diagnostics_rejects_case_id_mismatch(self):
        runner = load_runner()

        diagnostics = runner.v5_target_activation_diagnostics(
            [
                {
                    "case_id": "mtj-stale",
                    "case_number": 2,
                    "loaded_owner": ["using-mindthus"],
                    "required_visible_action_present": True,
                },
                {
                    "case_id": "mtj-033",
                    "case_number": 33,
                    "loaded_owner": ["3l5s"],
                    "required_visible_action_present": True,
                },
            ]
        )

        self.assertEqual(diagnostics["selected_registered_case_numbers"], [33])
        self.assertEqual(diagnostics["case_id_mismatch_case_numbers"], [2])

    def test_summarize_marks_runtime_event_telemetry_incomplete(self):
        runner = load_runner()
        summary = runner.summarize(
            [
                {
                    "case_id": "mtj-043",
                    "case_number": 43,
                    "case_type": "negative_control",
                    "group_id": "K",
                    "score": 2,
                    "pass_criteria_met": True,
                    "positive_wakeup_observed": False,
                    "first_sentence_lock": None,
                    "verdict_commitment_anti_mush": None,
                    "over_forced_verdict": False,
                    "rationale": "",
                }
            ]
        )

        self.assertIsNone(summary["negative_false_wakeup_runtime_event_rate"])
        self.assertFalse(summary["runtime_event_telemetry_complete"])
        self.assertEqual(summary["runtime_event_telemetry_missing_count"], 1)

    def test_certification_candidate_requires_explicit_models_and_full_set(self):
        runner = load_runner()
        args = SimpleNamespace(
            home=None,
            empty_home_root=None,
            certification_candidate=True,
            model=None,
            judge_model="gpt-judge",
            select=None,
            reanalysis_of=None,
            v5_register_hints=False,
        )

        self.assertIn("--certification-candidate requires explicit --model", runner.validate_run_args(args))

        args.model = "gpt-generator"
        args.judge_model = None
        self.assertIn(
            "--certification-candidate requires explicit --judge-model",
            runner.validate_run_args(args),
        )

        args.judge_model = "gpt-judge"
        args.select = "1-10"
        self.assertIn(
            "--certification-candidate requires the full case set; omit --select",
            runner.validate_run_args(args),
        )

        args.select = None
        args.reanalysis_of = "v4"
        self.assertIn(
            "--certification-candidate cannot be combined with --reanalysis-of",
            runner.validate_run_args(args),
        )

        args.reanalysis_of = None
        args.v5_register_hints = True
        self.assertIn(
            "--certification-candidate cannot use --v5-register-hints",
            runner.validate_run_args(args),
        )

    def test_public_fixture_expected_owners_are_mapped(self):
        runner = load_runner()
        unmapped = []
        for case in runner.load_cases(CASESET):
            if case.get("stay_asleep_expected"):
                continue
            if runner.expected_owner_skills(case):
                continue
            if case["expected_owner"] in runner.DIRECT_EXPECTED_OWNERS:
                continue
            unmapped.append((case["case_id"], case["expected_owner"]))

        self.assertEqual(unmapped, [])

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
