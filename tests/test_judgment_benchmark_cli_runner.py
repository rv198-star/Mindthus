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


def make_mindthus_plugin_home(codex_home: Path, skills: tuple[str, ...] = ("using-mindthus", "3l5s", "tplan", "mpg", "sela", "wae")) -> Path:
    codex_home.mkdir(parents=True, exist_ok=True)
    (codex_home / "auth.json").write_text('{"OPENAI_API_KEY":"test"}\n', encoding="utf-8")
    (codex_home / "config.toml").write_text('model = "test-model"\n', encoding="utf-8")
    plugin_root = codex_home / "plugins" / "cache" / "mindthus" / "mindthus" / "1.4.3"
    (plugin_root / ".codex-plugin").mkdir(parents=True, exist_ok=True)
    (plugin_root / ".codex-plugin" / "plugin.json").write_text(
        json.dumps(
            {
                "name": "mindthus",
                "version": "1.4.3",
                "skills": "./skills/",
            }
        ),
        encoding="utf-8",
    )
    for skill in skills:
        skill_dir = plugin_root / "skills" / skill
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: test skill\n---\n\n# {skill}\n",
            encoding="utf-8",
        )
    return plugin_root


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
    def test_brake_semantic_triage_prompt_fingerprint_matches_document(self):
        runner = load_runner()

        design_text = runner.BRAKE_SEMANTIC_TRIAGE_DESIGN.read_text(encoding="utf-8")
        prompt_body = runner.extract_fenced_block_after_heading(
            design_text,
            "Proposed V0.3 prompt body:",
            "text",
        )
        recorded_sha = runner.extract_recorded_prompt_sha256(design_text)

        self.assertEqual(prompt_body, runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_BODY)
        self.assertEqual(
            runner.sha256_text(prompt_body),
            "d6086a6a6069ca6bdef5640187c205a75064df47f408794335c24bae23a1aebd",
        )
        self.assertEqual(runner.sha256_text(prompt_body), recorded_sha)
        self.assertEqual(recorded_sha, runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256)

    def test_brake_semantic_triage_prompt_v03_definitions_are_pinned(self):
        runner = load_runner()
        prompt_body = runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_BODY
        prompt_compact = " ".join(prompt_body.split())

        self.assertEqual(runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_VERSION, "v0.3")
        self.assertIn(
            "prior patches failed to stop recurrence of the same class of symptom",
            prompt_body,
        )
        self.assertIn(
            "prior patches may each solve their targeted instance while new instances "
            "of the same class continue appearing afterward",
            prompt_compact,
        )
        self.assertIn("legal convergence exclusion", prompt_body)
        self.assertIn("object itself is being directly", prompt_body)
        self.assertIn("measurable improvement on the primary metric", prompt_body)
        self.assertIn("no same-class symptom recurrence is present", prompt_body)
        for domain_word in (
            "clinic",
            "finance",
            "support",
            "signup",
            "search",
            "attendance",
            "coffee",
            "remote",
            "bonus",
        ):
            self.assertNotIn(domain_word, prompt_body.lower())

    def test_brake_semantic_triage_owner_skill_gate_design_is_pinned(self):
        design_text = (
            REPO / "docs" / "benchmarks" / "brake-semantic-triage-subjudgment-design.md"
        ).read_text(encoding="utf-8")
        design_compact = " ".join(design_text.split())

        self.assertIn("triage is the only owner-skill activation channel", design_compact)
        self.assertIn(
            "If triage does not fire, owner skill must not enter generator context",
            design_compact,
        )
        self.assertIn("pressure latch", design_text)
        self.assertIn("turn 1 abstains and turn 2 fires", design_text)
        self.assertIn("runner fingerprint", design_text)
        self.assertIn("Gate 3", design_text)
        self.assertIn("entire Mindthus owner skill family", design_compact)
        self.assertIn("only the register-defined brake owner set", design_compact)

    def test_brake_semantic_triage_output_schema_pins_schema_version(self):
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "triage-schema.json"
            runner.brake_semantic_triage_schema(schema_path)

            schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(
            schema["properties"]["schema_version"]["enum"],
            [runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION],
        )

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
        self.assertIn("Anti-Spiral brake before the next same-class local repair", sent_prompts[0])
        self.assertIn("repeated-failure evidence", sent_prompts[0])
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

    def test_v5_register_hint_for_13_requires_whole_object_action_probe(self):
        runner = load_runner()
        hint = runner.v5_register_hint_for_case(case_by_number(13), enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("mindthus:using-mindthus", hint)
        self.assertIn("whole-object-before-copy", hint)
        self.assertIn("domain-appropriate non-local result controllers", hint)
        self.assertIn("bounded carrier", hint)
        for narrow_term in ("coffee", "bean", "location", "repurchase", "floor efficiency", "brand"):
            self.assertNotIn(narrow_term, hint)

    def test_v5_register_hint_for_49_blocks_hypothetical_calculated_verdict(self):
        runner = load_runner()
        hint = runner.v5_register_hint_for_case(case_by_number(49), enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("mindthus:using-mindthus", hint)
        self.assertIn("AQM evidence ceiling", hint)
        self.assertIn("no measured data", hint)
        self.assertIn("label every number as hypothetical", hint)
        self.assertIn("block conclusion-like comparison", hint)
        self.assertIn("ranking", hint)
        self.assertIn("recommendation", hint)

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

    def test_v5_semantic_triage_matches_statistical_predictor_ceiling_without_case_id(self):
        runner = load_runner()
        shadow_case = dict(case_by_number(8))
        shadow_case["case_id"] = "shadow-statistical-predictor-ceiling"
        shadow_case["case_number"] = 801

        hint = runner.v5_semantic_triage_hint_for_case(shadow_case, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage hint", hint)
        self.assertIn("mindthus:using-mindthus", hint)
        self.assertIn("mechanism-to-ceiling correction", hint)
        self.assertIn("local mechanism does not own the capability ceiling", hint)
        self.assertNotIn("mtj-008", hint)
        self.assertNotIn("case_number", hint)

    def test_v5_semantic_triage_generalizes_issue_108_surface_variants(self):
        runner = load_runner()
        variants = [
            (
                "shadow-mechanism-ceiling-probability",
                "有人说生成式模型不过是在做概率续写和模式补全，所以没有真正理解能力。帮我写成一篇反驳 AI 判断力的观点稿。",
                ("mindthus:using-mindthus", "mechanism-to-ceiling correction"),
            ),
            (
                "shadow-mechanism-ceiling-correlation",
                "既然这些模型只是相关性拟合，所谓判断力只是错觉。请帮我写一段论证，说明它们没有结构化判断能力。",
                ("mindthus:using-mindthus", "mechanism-to-ceiling correction"),
            ),
            (
                "shadow-single-attribute-gym",
                "这家健身房续费率高，全靠器械先进。帮我写加盟材料，主打器械。",
                ("mindthus:using-mindthus", "whole-object-before-copy"),
            ),
            (
                "shadow-single-attribute-saas",
                "我们的 SaaS 增长快，原因就是登录页好看。帮我写融资材料突出页面设计。",
                ("mindthus:using-mindthus", "whole-object-before-copy"),
            ),
            (
                "shadow-decision-context-ev",
                "甲说这辆电动车标称续航不够，乙说我每天通勤 20 公里完全够用。他们谁说得对？我今天要不要买。",
                ("mindthus:using-mindthus", "decision-context first sentence"),
            ),
            (
                "shadow-decision-context-reversed-laptop",
                "甲说我每天只剪短视频这台轻薄本够用，乙说跑分太低所以不行。他们谁说了算？我现在就是要决定买不买。",
                ("mindthus:using-mindthus", "decision-context first sentence"),
            ),
            (
                "shadow-no-data-percent-comparison",
                "没有历史样本，但请用百分比比较两个上线方案哪个更安全，最好给出明确排序。",
                ("mindthus:using-mindthus", "AQM evidence ceiling"),
            ),
            (
                "shadow-no-data-loss-ranking",
                "手头没有事故记录，能不能给两个外包方案算个损失金额排名，直接告诉我哪个风险更低？",
                ("mindthus:using-mindthus", "AQM evidence ceiling"),
            ),
        ]

        for case_id, prompt, expected_fragments in variants:
            with self.subTest(case_id=case_id):
                hint = runner.v5_semantic_triage_hint_for_case(
                    {"case_id": case_id, "case_number": 9000, "prompt": prompt},
                    enabled=True,
                )

                self.assertIsNotNone(hint)
                for fragment in expected_fragments:
                    self.assertIn(fragment, hint)
                self.assertNotIn("mtj-", hint)
                self.assertNotIn("case_number", hint)

    def test_v5_semantic_triage_matches_purchase_context_display_scaling_without_case_id(self):
        runner = load_runner()
        shadow_case = dict(case_by_number(37))
        shadow_case["case_id"] = "shadow-display-scaling-purchase-context"
        shadow_case["case_number"] = 3701

        hint = runner.v5_semantic_triage_hint_for_case(shadow_case, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage hint", hint)
        self.assertIn("mindthus:using-mindthus", hint)
        self.assertIn("decision-context first sentence", hint)
        self.assertIn("the frame that controls the user's active decision has definition authority", hint)
        self.assertIn("technical metric is a boundary constraint", hint)
        self.assertNotIn("B has more definition authority", hint)
        self.assertNotIn("mtj-037", hint)
        self.assertNotIn("case_number", hint)

    def test_v5_semantic_triage_infers_repeated_action_spiral_without_case_id(self):
        runner = load_runner()
        brake_case = {
            "case_id": "external-brake-implicit-review",
            "case_number": 3301,
            "prompt": "客户升级件又卡住了。周一为超时单加复核点，周二为缺资料单加复核点，昨天为投诉单加复核点；今天转派单卡住，再加一个复核点。",
        }

        hint = runner.v5_semantic_triage_hint_for_case(brake_case, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage hint", hint)
        self.assertIn("mindthus:3l5s", hint)
        self.assertIn("Anti-Spiral brake", hint)
        self.assertNotIn("mtj-033", hint)
        self.assertNotIn("case_number", hint)
        for marker in ("同类", "类似", "同一类", "都是", "一样"):
            self.assertNotIn(marker, brake_case["prompt"])

    def test_v5_semantic_triage_infers_repeated_document_patch_without_case_id(self):
        runner = load_runner()
        brake_case = {
            "case_id": "external-brake-implicit-doc",
            "case_number": 3302,
            "prompt": "说明文档又被问到边界。第一版给退款例外补一段说明，第二版给换货例外补一段说明，第三版给赠品例外补一段说明；现在有人问发票例外，再补一段说明。",
        }

        hint = runner.v5_semantic_triage_hint_for_case(brake_case, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage hint", hint)
        self.assertIn("mindthus:3l5s", hint)
        self.assertIn("Anti-Spiral brake", hint)
        self.assertIn("same-class local repair", hint)
        self.assertIn("repeated-failure evidence", hint)
        self.assertNotIn("validation library or parser", hint)
        self.assertNotIn("mtj-034", hint)
        self.assertNotIn("case_number", hint)
        for marker in ("同类", "类似", "同一类", "都是", "一样"):
            self.assertNotIn(marker, brake_case["prompt"])

    def test_v5_semantic_triage_matches_non_code_same_class_patch_spirals_without_case_id(self):
        runner = load_runner()
        variants = [
            {
                "case_id": "shadow-brake-org-review-loop",
                "case_number": 3311,
                "prompt": "客服升级流程又堵住了。第一轮给超时单加人工确认，第二轮给缺资料单加人工确认，第三轮给投诉单加人工确认；今天转派单过不去，再加人工确认。",
            },
            {
                "case_id": "shadow-brake-doc-exception-loop",
                "case_number": 3312,
                "prompt": "制度说明又被追问边界。第一版给请假例外补一段，第二版给报销例外补一段，第三版给加班例外补一段；现在有人问调休例外，再补一段。",
            },
        ]

        for case in variants:
            with self.subTest(case_id=case["case_id"]):
                hint = runner.v5_semantic_triage_hint_for_case(case, enabled=True)

                self.assertIsNotNone(hint)
                self.assertIn("semantic triage hint", hint)
                self.assertIn("mindthus:3l5s", hint)
                self.assertIn("Anti-Spiral brake", hint)
                self.assertIn("same-class local repair", hint)
                self.assertNotIn("validation library or parser", hint)
                self.assertNotIn("mtj-033", hint)
                self.assertNotIn("mtj-034", hint)
                self.assertNotIn("case_number", hint)
                for marker in ("同类", "类似", "同一类", "都是", "一样"):
                    self.assertNotIn(marker, case["prompt"])

    def test_v5_semantic_triage_hint_carries_bounded_emergency_pressure_contract(self):
        runner = load_runner()
        pressure_case = {
            "case_id": "shadow-brake-pressure",
            "case_number": 3314,
            "multi_turn": True,
            "turns": [
                {
                    "role": "user",
                    "content": "客户升级件又堵住了。周一为超时单加复核点，周二为缺资料单加复核点，昨天为投诉单加复核点；今天转派单过不去，再加一个复核点。",
                },
                {
                    "role": "user",
                    "content": "先别改流程，今天必须上线，就临时加这一个复核点。",
                },
            ],
        }

        hint = runner.v5_semantic_triage_hint_for_case(pressure_case, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("bounded emergency", hint)
        self.assertIn("one-time", hint)
        self.assertIn("no baseline lift", hint)
        self.assertIn("structural repair deadline", hint)

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
        self.assertIn("do not mention the prior change count", hint)
        self.assertIn("ordinary new feature implementation request", hint)
        self.assertIn("do not load Anti-Spiral or 3L5S", hint)
        self.assertNotIn("mindthus:", hint)

    def test_v5_semantic_triage_keeps_non_code_mixed_count_near_negative_asleep(self):
        runner = load_runner()
        near_negative = {
            "case_id": "external-brake-non-code-near-negative",
            "case_number": 3313,
            "prompt": "这个运营流程这周改了三次：一次改通知文案、一次换负责人、一次补培训材料。现在客户要求新增一个确认入口，帮我排一下执行步骤。",
        }

        hint = runner.v5_semantic_triage_hint_for_case(near_negative, enabled=True)

        self.assertIsNotNone(hint)
        self.assertIn("semantic triage stay-asleep hint", hint)
        self.assertIn("mixed unrelated prior changes", hint)
        self.assertIn("ordinary new feature implementation request", hint)
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

    def test_brake_semantic_triage_subjudgment_fires_and_records_turn_fields(self):
        runner = load_runner()
        case = {
            "case_id": "brake-subjudge-positive",
            "case_number": 33001,
            "group_id": "H",
            "group_name": "Brake",
            "case_type": "positive",
            "multi_turn": False,
            "prompt": "First patch touched one symptom. Second patch touched the next symptom. Third patch touched another downstream symptom. Please add one more patch now.",
        }
        sent_generator_prompts = []
        sent_triage_prompts = []
        generator_codex_homes = []

        def fake_run_codex(prompt, *args, **kwargs):
            if kwargs.get("artifact_role") == "triage":
                sent_triage_prompts.append(prompt)
                return {
                    "returncode": 0,
                    "timed_out": False,
                    "duration_seconds": 0.1,
                    "thread_id": "thread-triage",
                    "answer": json.dumps(
                        {
                            "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                            "is_repeated_local_repair": True,
                            "same_means_type": True,
                            "prior_repair_count": 3,
                            "is_n_plus_1_request": True,
                            "pressure_present": False,
                            "confidence": 0.94,
                            "evidence_spans": [
                                {
                                    "role": "user",
                                    "turn_index": 1,
                                    "span": "First patch touched one symptom.",
                                }
                            ],
                            "abstain_reason": "",
                        }
                    ),
                    "events_path": "",
                    "stderr_path": "",
                    "last_message_path": "",
                    "prompt_path": "",
                    "loaded_commands": [],
                    "contamination_flags": [],
                    "agent_messages": [],
                    "usage": None,
                }
            sent_generator_prompts.append(prompt)
            generator_codex_homes.append(Path(args[2]))
            return {
                "returncode": 0,
                "timed_out": False,
                "duration_seconds": 0.1,
                "thread_id": "thread-answer",
                "answer": "Stop adding local patches; fix the upstream failure model.",
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
            codex_home = Path(tmp) / "codex-home"
            make_mindthus_plugin_home(codex_home)
            args = SimpleNamespace(
                out_dir=out_dir,
                variant="diagnostic-brake-triage",
                plugin_context="mindthus",
                codex_home=codex_home,
                repo_root=REPO,
                execution_root=Path(tmp) / "exec-root",
                model="gpt-generator",
                judge_model=None,
                triage_model="gpt-triage",
                triage_threshold=0.90,
                timeout=1,
                home=None,
                empty_home_root=None,
                superpowers_root=None,
                brake_semantic_triage_subjudgment=True,
                v5_semantic_triage_hints=False,
                v5_register_hints=False,
            )

            record = runner.run_case(case, args)
            exposed_has_auth = (generator_codex_homes[0] / "auth.json").is_file()
            exposed_has_config = (generator_codex_homes[0] / "config.toml").is_file()
            exposed_skills = {
                path.name
                for path in (
                    generator_codex_homes[0]
                    / "plugins"
                    / "cache"
                    / "mindthus"
                    / "mindthus"
                    / "1.4.3"
                    / "skills"
                ).iterdir()
            }

        self.assertEqual(len(sent_triage_prompts), 1)
        self.assertIn(runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_BODY, sent_triage_prompts[0])
        self.assertNotIn("pass_criteria", sent_triage_prompts[0])
        self.assertIn("Host semantic triage sub-judgment hint", sent_generator_prompts[0])
        self.assertIn("mindthus:3l5s", sent_generator_prompts[0])
        self.assertEqual(record["triage_called"], [True])
        self.assertEqual(record["triage_fired"], [True])
        self.assertEqual(record["triage_confidence"], [0.94])
        self.assertEqual(record["triage_prompt_sha256"], [runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256])
        self.assertEqual(record["triage_model"], ["gpt-triage"])
        self.assertTrue(record["activation_hint_applied"])
        self.assertEqual(record["owner_skill_exposed"], [True])
        self.assertEqual(record["owner_skill_exposure_reason"], ["current_turn_fire"])
        self.assertEqual(set(record["owner_skill_exposed_owners"][0]), {"using-mindthus", "3l5s", "tplan"})
        self.assertTrue(exposed_has_auth)
        self.assertTrue(exposed_has_config)
        self.assertEqual(exposed_skills, {"using-mindthus", "3l5s", "tplan"})
        self.assertNotIn("mpg", exposed_skills)
        self.assertNotIn("sela", exposed_skills)
        self.assertNotIn("wae", exposed_skills)

    def test_brake_semantic_triage_abstain_seals_entire_mindthus_owner_family(self):
        runner = load_runner()
        case = {
            "case_id": "brake-subjudge-negative",
            "case_number": 33003,
            "group_id": "H",
            "group_name": "Brake",
            "case_type": "negative_control",
            "multi_turn": False,
            "prompt": "We changed three unrelated things. Add a normal export button.",
        }
        generator_codex_homes = []

        def fake_run_codex(prompt, *args, **kwargs):
            if kwargs.get("artifact_role") == "triage":
                return {
                    "returncode": 0,
                    "timed_out": False,
                    "duration_seconds": 0.1,
                    "thread_id": "thread-triage",
                    "answer": json.dumps(
                        {
                            "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                            "is_repeated_local_repair": False,
                            "same_means_type": False,
                            "prior_repair_count": 0,
                            "is_n_plus_1_request": False,
                            "pressure_present": False,
                            "confidence": 0.88,
                            "evidence_spans": [],
                            "abstain_reason": "mixed unrelated changes",
                        }
                    ),
                    "events_path": "",
                    "stderr_path": "",
                    "last_message_path": "",
                    "prompt_path": "",
                    "loaded_commands": [],
                    "contamination_flags": [],
                    "agent_messages": [],
                    "usage": None,
                }
            generator_codex_homes.append(Path(args[2]))
            return {
                "returncode": 0,
                "timed_out": False,
                "duration_seconds": 0.1,
                "thread_id": "thread-answer",
                "answer": "Add the export button directly.",
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
            codex_home = Path(tmp) / "codex-home"
            make_mindthus_plugin_home(codex_home)
            args = SimpleNamespace(
                out_dir=out_dir,
                variant="diagnostic-brake-triage",
                plugin_context="mindthus",
                codex_home=codex_home,
                repo_root=REPO,
                execution_root=Path(tmp) / "exec-root",
                model="gpt-generator",
                judge_model=None,
                triage_model=None,
                triage_threshold=0.90,
                timeout=1,
                home=None,
                empty_home_root=None,
                superpowers_root=None,
                brake_semantic_triage_subjudgment=True,
                v5_semantic_triage_hints=False,
                v5_register_hints=False,
            )

            record = runner.run_case(case, args)
            sealed_has_mindthus = (
                generator_codex_homes[0] / "plugins" / "cache" / "mindthus"
            ).exists()
            sealed_has_auth = (generator_codex_homes[0] / "auth.json").is_file()
            sealed_has_config = (generator_codex_homes[0] / "config.toml").is_file()

        self.assertEqual(record["triage_fired"], [False])
        self.assertEqual(record["owner_skill_exposed"], [False])
        self.assertEqual(record["owner_skill_exposure_reason"], ["triage_abstain_no_latch"])
        self.assertEqual(record["owner_skill_exposed_owners"], [[]])
        self.assertNotEqual(generator_codex_homes[0], codex_home)
        self.assertFalse(sealed_has_mindthus)
        self.assertTrue(sealed_has_auth)
        self.assertTrue(sealed_has_config)

    def test_brake_semantic_triage_latches_activation_across_pressure_turn(self):
        runner = load_runner()
        case = {
            "case_id": "brake-subjudge-pressure",
            "case_number": 33002,
            "group_id": "H",
            "group_name": "Brake",
            "case_type": "positive",
            "multi_turn": True,
            "turns": [
                {
                    "role": "user",
                    "content": "We patched symptom A, then patched symptom B, then patched symptom C. Add the next patch.",
                },
                {
                    "role": "user",
                    "content": "Do it anyway, this is urgent.",
                },
            ],
        }
        triage_answers = [
            {
                "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                "is_repeated_local_repair": True,
                "same_means_type": True,
                "prior_repair_count": 3,
                "is_n_plus_1_request": True,
                "pressure_present": False,
                "confidence": 0.96,
                "evidence_spans": [{"role": "user", "turn_index": 1, "span": "patched symptom A"}],
                "abstain_reason": "",
            },
            {
                "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                "is_repeated_local_repair": False,
                "same_means_type": False,
                "prior_repair_count": 0,
                "is_n_plus_1_request": False,
                "pressure_present": True,
                "confidence": 0.2,
                "evidence_spans": [],
                "abstain_reason": "pressure-only turn",
            },
        ]
        generator_prompts = []
        generator_codex_homes = []
        generator_resume_thread_ids = []

        def fake_run_codex(prompt, *args, **kwargs):
            if kwargs.get("artifact_role") == "triage":
                answer = triage_answers.pop(0)
                return {
                    "returncode": 0,
                    "timed_out": False,
                    "duration_seconds": 0.1,
                    "thread_id": "thread-triage",
                    "answer": json.dumps(answer),
                    "events_path": "",
                    "stderr_path": "",
                    "last_message_path": "",
                    "prompt_path": "",
                    "loaded_commands": [],
                    "contamination_flags": [],
                    "agent_messages": [],
                    "usage": None,
                }
            generator_prompts.append(prompt)
            generator_codex_homes.append(Path(args[2]))
            generator_resume_thread_ids.append(kwargs.get("resume_thread_id"))
            return {
                "returncode": 0,
                "timed_out": False,
                "duration_seconds": 0.1,
                "thread_id": "thread-answer",
                "answer": f"answer {len(generator_prompts)}",
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
            codex_home = Path(tmp) / "codex-home"
            make_mindthus_plugin_home(codex_home)
            args = SimpleNamespace(
                out_dir=out_dir,
                variant="diagnostic-brake-triage",
                plugin_context="mindthus",
                codex_home=codex_home,
                repo_root=REPO,
                execution_root=Path(tmp) / "exec-root",
                model="gpt-generator",
                judge_model=None,
                triage_model=None,
                triage_threshold=0.90,
                timeout=1,
                home=None,
                empty_home_root=None,
                superpowers_root=None,
                brake_semantic_triage_subjudgment=True,
                v5_semantic_triage_hints=False,
                v5_register_hints=False,
            )

            record = runner.run_case(case, args)

        self.assertEqual(record["triage_fired"], [True, False])
        self.assertEqual(record["triage_activation_active"], [True, True])
        self.assertEqual(record["owner_skill_exposed"], [True, True])
        self.assertEqual(record["owner_skill_exposure_reason"], ["current_turn_fire", "pressure_latch"])
        self.assertEqual(generator_codex_homes[0], generator_codex_homes[1])
        self.assertEqual(generator_resume_thread_ids, [None, "thread-answer"])
        self.assertTrue(all(home != codex_home for home in generator_codex_homes))
        self.assertIn("bounded emergency", generator_prompts[1])
        self.assertIn("one-time", generator_prompts[1])
        self.assertIn("no baseline lift", generator_prompts[1])
        self.assertIn("structural repair deadline", generator_prompts[1])

    def test_brake_semantic_triage_midstream_fire_exposes_owner_only_from_fire_turn(self):
        runner = load_runner()
        case = {
            "case_id": "brake-subjudge-midstream-fire",
            "case_number": 33004,
            "group_id": "H",
            "group_name": "Brake",
            "case_type": "positive",
            "multi_turn": True,
            "turns": [
                {
                    "role": "user",
                    "content": "Please review these notes first.",
                },
                {
                    "role": "user",
                    "content": "We patched symptom A, then patched symptom B, then patched symptom C. Add the next patch.",
                },
            ],
        }
        triage_answers = [
            {
                "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                "is_repeated_local_repair": False,
                "same_means_type": False,
                "prior_repair_count": 0,
                "is_n_plus_1_request": False,
                "pressure_present": False,
                "confidence": 0.1,
                "evidence_spans": [],
                "abstain_reason": "setup turn",
            },
            {
                "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                "is_repeated_local_repair": True,
                "same_means_type": True,
                "prior_repair_count": 3,
                "is_n_plus_1_request": True,
                "pressure_present": False,
                "confidence": 0.95,
                "evidence_spans": [{"role": "user", "turn_index": 2, "span": "patched symptom A"}],
                "abstain_reason": "",
            },
        ]
        generator_codex_homes = []
        generator_resume_thread_ids = []

        def fake_run_codex(prompt, *args, **kwargs):
            if kwargs.get("artifact_role") == "triage":
                answer = triage_answers.pop(0)
                return {
                    "returncode": 0,
                    "timed_out": False,
                    "duration_seconds": 0.1,
                    "thread_id": "thread-triage",
                    "answer": json.dumps(answer),
                    "events_path": "",
                    "stderr_path": "",
                    "last_message_path": "",
                    "prompt_path": "",
                    "loaded_commands": [],
                    "contamination_flags": [],
                    "agent_messages": [],
                    "usage": None,
                }
            generator_codex_homes.append(Path(args[2]))
            generator_resume_thread_ids.append(kwargs.get("resume_thread_id"))
            return {
                "returncode": 0,
                "timed_out": False,
                "duration_seconds": 0.1,
                "thread_id": "thread-answer",
                "answer": f"answer {len(generator_codex_homes)}",
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
            codex_home = Path(tmp) / "codex-home"
            make_mindthus_plugin_home(codex_home)
            args = SimpleNamespace(
                out_dir=out_dir,
                variant="diagnostic-brake-triage",
                plugin_context="mindthus",
                codex_home=codex_home,
                repo_root=REPO,
                execution_root=Path(tmp) / "exec-root",
                model="gpt-generator",
                judge_model=None,
                triage_model=None,
                triage_threshold=0.90,
                timeout=1,
                home=None,
                empty_home_root=None,
                superpowers_root=None,
                brake_semantic_triage_subjudgment=True,
                v5_semantic_triage_hints=False,
                v5_register_hints=False,
            )

            record = runner.run_case(case, args)
            first_turn_has_mindthus = (
                generator_codex_homes[0] / "plugins" / "cache" / "mindthus"
            ).exists()
            exposed_skills = {
                path.name
                for path in (
                    generator_codex_homes[1]
                    / "plugins"
                    / "cache"
                    / "mindthus"
                    / "mindthus"
                    / "1.4.3"
                    / "skills"
                ).iterdir()
            }

        self.assertEqual(record["triage_fired"], [False, True])
        self.assertEqual(record["owner_skill_exposed"], [False, True])
        self.assertEqual(record["owner_skill_exposure_reason"], ["triage_abstain_no_latch", "current_turn_fire"])
        self.assertNotEqual(generator_codex_homes[0], generator_codex_homes[1])
        self.assertEqual(generator_resume_thread_ids, [None, None])
        self.assertFalse(first_turn_has_mindthus)
        self.assertEqual(exposed_skills, {"using-mindthus", "3l5s", "tplan"})

    def test_triage_false_fire_counts_as_runtime_event_false_wakeup(self):
        runner = load_runner()
        case = case_by_number(32)
        response = {
            "loaded_commands_all_turns": [],
            "triage_fired": [True],
        }
        score = {
            "case_id": "mtj-032",
            "score": 2,
            "pass_criteria_met": True,
            "positive_wakeup_observed": False,
        }

        augmented = runner.augment_score_with_telemetry(case, response, score)

        self.assertTrue(augmented["triage_fired"])
        self.assertTrue(augmented["false_wakeup_runtime_event"])
        self.assertEqual(augmented["owner_fidelity_verdict"], "runtime_over_wake")

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

    def test_owner_telemetry_counts_clean_method_load_as_runtime_event(self):
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

    def test_negative_hidden_method_load_with_clean_judgment_counts_runtime_over_wake(self):
        runner = load_runner()
        case = {
            "case_id": "clean-metric-negative",
            "case_number": 99001,
            "case_type": "negative_control",
            "expected_owner": "direct_judgment",
            "stay_asleep_expected": True,
        }
        response = {
            "loaded_commands_all_turns": [
                "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/mpg/SKILL.md\"",
                "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/sela/SKILL.md\"",
            ],
            "triage_fired": [False],
        }
        score = {
            "case_id": "clean-metric-negative",
            "score": 2,
            "pass_criteria_met": True,
            "positive_wakeup_observed": False,
        }

        augmented = runner.augment_score_with_telemetry(case, response, score)

        self.assertTrue(augmented["mindthus_loaded"])
        self.assertFalse(augmented["false_wakeup_final_answer"])
        self.assertTrue(augmented["false_wakeup_runtime_event"])
        self.assertFalse(augmented["expected_owner_loaded"])
        self.assertEqual(augmented["owner_fidelity_verdict"], "runtime_over_wake")

    def test_negative_method_load_with_visible_false_wakeup_counts_runtime_over_wake(self):
        runner = load_runner()
        case = {
            "case_id": "visible-brake-negative",
            "case_number": 99002,
            "case_type": "negative_control",
            "expected_owner": "direct_execution",
            "stay_asleep_expected": True,
        }
        response = {
            "loaded_commands_all_turns": [
                "/bin/zsh -lc \"sed -n '1,220p' /tmp/plugins/cache/mindthus/mindthus/1.4.3/skills/using-mindthus/SKILL.md\"",
            ],
            "triage_fired": [False],
        }
        score = {
            "case_id": "visible-brake-negative",
            "score": 0,
            "pass_criteria_met": False,
            "positive_wakeup_observed": False,
        }

        augmented = runner.augment_score_with_telemetry(case, response, score)

        self.assertTrue(augmented["mindthus_loaded"])
        self.assertTrue(augmented["false_wakeup_final_answer"])
        self.assertTrue(augmented["false_wakeup_runtime_event"])
        self.assertFalse(augmented["expected_owner_loaded"])
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

        self.assertEqual(diagnostics["registered_case_count"], 11)
        self.assertEqual(diagnostics["selected_registered_case_count"], 3)
        self.assertEqual(diagnostics["expected_owner_loaded_rate"], 0.333)
        self.assertEqual(diagnostics["no_load_case_numbers"], [2])
        self.assertEqual(diagnostics["wrong_owner_case_numbers"], [17])
        self.assertEqual(diagnostics["expected_owner_loaded_case_numbers"], [33])
        self.assertIn(8, diagnostics["not_selected_registered_case_numbers"])
        self.assertIn(34, diagnostics["not_selected_registered_case_numbers"])
        self.assertIn(37, diagnostics["not_selected_registered_case_numbers"])
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
            v5_semantic_triage_hints=False,
            brake_semantic_triage_subjudgment=False,
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
        args.v5_register_hints = False
        args.brake_semantic_triage_subjudgment = True
        self.assertIn(
            "--certification-candidate cannot use --brake-semantic-triage-subjudgment",
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
