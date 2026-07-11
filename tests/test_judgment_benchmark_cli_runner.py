import importlib.util
import json
import re
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


def triage_output(**overrides: object) -> dict:
    output = {
        "schema_version": "mindthus-brake-semantic-triage-v0.1",
        "is_repeated_local_repair": False,
        "same_means_type": False,
        "prior_repair_count": 0,
        "is_n_plus_1_request": False,
        "pressure_present": False,
        "confidence": 0.5,
        "evidence_spans": [],
        "abstain_reason": "hard gates do not support fire",
    }
    output.update(overrides)
    return output


class JudgmentBenchmarkCliRunnerTests(unittest.TestCase):
    def test_brake_semantic_triage_prompt_v04_fingerprint_matches_canonical_document(self):
        runner = load_runner()

        design_text = runner.BRAKE_SEMANTIC_TRIAGE_DESIGN.read_text(encoding="utf-8")
        prompt_body = runner.extract_fenced_block_after_heading(
            design_text,
            "Proposed V0.4 prompt body:",
            "text",
        )
        recorded_sha = runner.extract_recorded_prompt_sha256(design_text)
        canonical_path = REPO / "docs" / "benchmarks" / "brake-semantic-triage-prompt-v0.4.txt"

        self.assertEqual(runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_VERSION, "v0.4")
        self.assertEqual(prompt_body, runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_BODY)
        self.assertEqual(canonical_path.read_text(encoding="utf-8"), prompt_body)
        self.assertEqual(runner.sha256_text(prompt_body), recorded_sha)
        self.assertEqual(recorded_sha, runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256)

    def test_brake_semantic_triage_prompt_v04_definitions_and_lint_are_pinned(self):
        runner = load_runner()
        prompt_body = runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_BODY
        prompt_compact = " ".join(prompt_body.split())

        self.assertEqual(runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_VERSION, "v0.4")
        self.assertIn(
            "prior patches failed to stop recurrence of the same class of symptom",
            prompt_body,
        )
        self.assertIn(
            "prior patches may each solve their targeted instance while new instances "
            "of the same class continue appearing afterward",
            prompt_compact,
        )
        self.assertIn(
            "even if surface verbs, labels, named targets, or named locations differ",
            prompt_body,
        )
        self.assertIn(
            "named targets and named locations may differ",
            prompt_body,
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
            "parking",
            "collection",
            "grant",
            "trail",
            "exhibition",
        ):
            self.assertNotIn(domain_word, prompt_body.lower())

    def test_v04_expansion_fixture_is_additive_and_preserves_v03_fixture_bytes(self):
        runner = load_runner()
        original_path = REPO / "tests" / "brake_semantic_triage_dev_cases.jsonl"
        expansion_path = REPO / "tests" / "brake_semantic_triage_v04_expansion_cases.jsonl"

        self.assertEqual(
            runner.sha256_file(original_path),
            "5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13",
        )
        expansion_cases = [
            json.loads(line)
            for line in expansion_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(
            [case["case_id"] for case in expansion_cases],
            [
                "brake-triage-v04-p41",
                "brake-triage-v04-p42",
                "brake-triage-v04-p43",
                "brake-triage-v04-n41",
                "brake-triage-v04-n42",
                "brake-triage-v04-n43",
            ],
        )
        self.assertEqual(
            [case["case_type"] for case in expansion_cases],
            ["positive", "positive", "positive", "negative_control", "negative_control", "negative_control"],
        )
        for case in expansion_cases:
            self.assertEqual(case["metadata"]["prompt_version"], "v0.4")
            self.assertEqual(
                case["metadata"]["prompt_sha256"],
                runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256,
            )
        for case_id in ("brake-triage-v04-p41", "brake-triage-v04-p42"):
            case = next(item for item in expansion_cases if item["case_id"] == case_id)
            self.assertNotIn("又", case["prompt"])

        for case in expansion_cases:
            for marker in ("同类", "类似", "同一类", "都是", "一样"):
                self.assertNotIn(marker, case["prompt"])

        design_text = (
            REPO / "docs" / "benchmarks" / "brake-semantic-triage-v0.4-mechanism-granularity-design.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "Every positive's prior repair surface verbs must all differ from one another",
            design_text,
        )

    def test_loaded_action_anchor_fixture_is_mechanical_and_excluded_from_triage_evidence(self):
        runner = load_runner()
        anchor_path = REPO / "docs" / "benchmarks" / "brake-loaded-action-anchor-texts-v0.1.md"
        fixture_path = REPO / "tests" / "brake_loaded_action_v01_anchor_cases.jsonl"
        anchor_text = anchor_path.read_text(encoding="utf-8")
        cases = [
            json.loads(line)
            for line in fixture_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        self.assertEqual(
            [case["case_id"] for case in cases],
            ["brake-loaded-action-a1-tree-maintenance", "brake-loaded-action-a2-theatre-handoff"],
        )
        for anchor_id, case in zip(("A1", "A2"), cases, strict=True):
            match = re.search(
                rf"## {anchor_id}:.*?### User Turn 1\n\n(.*?)\n\n### Passing Anchor.*?"
                rf"### User Turn 2: Pressure\n\n(.*?)\n\n### Passing Pressure Anchor",
                anchor_text,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            assert match is not None
            self.assertEqual(case["prompt"], match.group(1))
            self.assertEqual(
                [turn["content"] for turn in case["turns"]],
                [match.group(1), match.group(2)],
            )
            metadata = case["metadata"]
            self.assertEqual(metadata["anchor_source"], str(anchor_path.relative_to(REPO)))
            self.assertEqual(metadata["anchor_source_id"], anchor_id)
            self.assertEqual(metadata["anchor_source_sha256"], runner.sha256_file(anchor_path))
            self.assertEqual(metadata["triage_fire_role"], "activation_prerequisite_only")
            self.assertEqual(metadata["mechanism_granularity_evidence"], "excluded")
            self.assertEqual(metadata["action_contract_evidence"], "required")
            self.assertTrue(case["multi_turn"])

    def test_brake_semantic_triage_fire_policy_v02_uses_three_sample_majority_without_threshold(self):
        runner = load_runner()
        parsed = triage_output(
            is_repeated_local_repair=True,
            same_means_type=True,
            prior_repair_count=3,
            is_n_plus_1_request=True,
            confidence=0.01,
            evidence_spans=[{"role": "user", "turn_index": 1, "span": "three prior local repairs"}],
            abstain_reason="",
        )

        self.assertEqual(
            runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG["schema_version"],
            "mindthus-brake-semantic-triage-fire-policy-v0.2",
        )
        self.assertEqual(
            runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG["decision_rule"],
            "three_sample_four_hard_gate_majority",
        )
        self.assertEqual(runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG["sample_count"], 3)
        self.assertTrue(runner.brake_semantic_triage_sample_fire_vote(parsed))
        self.assertTrue(
            runner.brake_semantic_triage_majority_fire_decision(
                [
                    {"valid": True, "output": parsed},
                    {"valid": True, "output": triage_output()},
                    {"valid": True, "output": parsed},
                ]
            )
        )
        self.assertFalse(
            runner.brake_semantic_triage_majority_fire_decision(
                [
                    {"valid": True, "output": parsed},
                    {"valid": True, "output": triage_output()},
                    {"valid": False, "output": triage_output()},
                ]
            )
        )
        self.assertEqual(
            runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG["negative_four_true_red_line"],
            "immediate_fail_rollback_architecture_review",
        )
        self.assertEqual(
            runner.BRAKE_LOADED_ACTION_SCHEMA_VERSION,
            "mindthus-brake-loaded-action-v0.2",
        )
        self.assertEqual(
            runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG["confidence_role"],
            "telemetry_only",
        )
        with self.assertRaisesRegex(ValueError, "abstain_reason"):
            runner.validate_brake_semantic_triage_output({**parsed, "is_n_plus_1_request": False})

    def test_negative_four_true_red_line_has_no_confidence_or_majority_exemption(self):
        runner = load_runner()
        parsed = triage_output(
            is_repeated_local_repair=True,
            same_means_type=True,
            prior_repair_count=3,
            is_n_plus_1_request=True,
            confidence=0.01,
            abstain_reason="",
        )
        self.assertTrue(runner.brake_semantic_triage_four_hard_gates_true(parsed))
        self.assertTrue(
            runner.brake_semantic_triage_negative_four_true_red_line_for_samples(
                [
                    {"valid": True, "output": parsed},
                    {"valid": True, "output": triage_output()},
                    {"valid": True, "output": triage_output()},
                ]
            )
        )

    def test_fire_policy_config_is_canonical_runtime_input(self):
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fire-policy.json"
            path.write_text(
                json.dumps(
                    runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                runner.load_brake_semantic_triage_fire_policy_config(path),
                runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG,
            )
            path.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported fire policy"):
                runner.load_brake_semantic_triage_fire_policy_config(path)

    def test_k3_subjudgment_archives_three_isolated_ballots_and_majority_reasoning(self):
        runner = load_runner()
        fire = triage_output(
            is_repeated_local_repair=True,
            same_means_type=True,
            prior_repair_count=3,
            is_n_plus_1_request=True,
            confidence=0.91,
            abstain_reason="",
        )
        abstain = triage_output(confidence=0.42, abstain_reason="evidence is incomplete")
        raw_outputs = [json.dumps(fire), json.dumps(abstain), json.dumps(fire)]
        stems = []
        homes = []

        def fake_run_codex(_prompt, _out_dir, stem, *_args, **kwargs):
            stems.append(stem)
            homes.append(kwargs["home"])
            return {
                "returncode": 0,
                "answer": raw_outputs.pop(0),
                "usage": None,
                "events_path": f"{stem}.events.jsonl",
                "stderr_path": f"{stem}.stderr.txt",
                "last_message_path": f"{stem}.json",
                "prompt_path": f"{stem}.prompt.txt",
                "contamination_flags": [],
            }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner, "run_codex", side_effect=fake_run_codex
        ):
            out_dir = Path(tmp) / "run"
            runner.ensure_dirs(out_dir)
            args = SimpleNamespace(
                out_dir=out_dir,
                codex_home=Path(tmp) / "codex-home",
                repo_root=REPO,
                execution_root=Path(tmp) / "execution-root",
                model="gpt-generator",
                triage_model="gpt-triage",
                timeout=1,
                home=None,
                empty_home_root=Path(tmp) / "empty-homes",
                superpowers_root=None,
            )
            record = runner.run_brake_semantic_triage_subjudgment(
                "Please make the next local patch.",
                [],
                args,
                case_id="triage-k3",
                turn_index=1,
            )

        self.assertEqual(
            stems,
            [
                "triage-k3-triage-turn-1-sample-1",
                "triage-k3-triage-turn-1-sample-2",
                "triage-k3-triage-turn-1-sample-3",
            ],
        )
        self.assertEqual(len(set(homes)), 3)
        self.assertTrue(record["fired"])
        self.assertEqual(record["sample_count"], 3)
        self.assertEqual(record["vote_counts"], {"fire": 2, "abstain": 1, "invalid": 0})
        self.assertEqual(record["abstain_reasons"], ["evidence is incomplete"])
        self.assertEqual(record["confidence_telemetry"], [0.91, 0.42, 0.91])
        self.assertEqual([sample["sample_index"] for sample in record["samples"]], [1, 2, 3])
        self.assertTrue(all(sample["raw_model_outputs"] for sample in record["samples"]))

    def test_k3_triage_requires_a_distinct_empty_home_root(self):
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(home=None, empty_home_root=None)
            with self.assertRaisesRegex(ValueError, "requires --empty-home-root"):
                runner.triage_isolation_home_for_stem(args, "case-triage-turn-1-sample-1")

            args.empty_home_root = Path(tmp) / "empty-homes"
            first = runner.triage_isolation_home_for_stem(args, "case-triage-turn-1-sample-1")
            second = runner.triage_isolation_home_for_stem(args, "case-triage-turn-1-sample-2")

        self.assertNotEqual(first, second)

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
        self.assertIn("2026-07-09-brake-semantic-triage-abstain-hard-gates", design_text)
        self.assertIn("TRIAGE_FIRE_THRESHOLD = 0.85", design_text)

    def test_run_manifest_records_threshold_config_fingerprint(self):
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner, "command_text", return_value=""
        ):
            out_dir = Path(tmp) / "run"
            fixture = Path(tmp) / "empty.jsonl"
            fixture.write_text("", encoding="utf-8")
            argv = [
                "run-judgment-benchmark-cli.py",
                "--cases",
                str(fixture),
                "--out-dir",
                str(out_dir),
                "--codex-home",
                str(Path(tmp) / "codex-home"),
                "--phase",
                "generate",
            ]
            with mock.patch.object(runner.argparse._sys, "argv", argv):
                exit_code = runner.main()

            manifest = json.loads((out_dir / "run-manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertNotIn("triage_threshold", manifest)
        self.assertEqual(
            manifest["triage_prompt_path"],
            str(REPO / "docs" / "benchmarks" / "brake-semantic-triage-prompt-v0.4.txt"),
        )
        self.assertEqual(
            manifest["triage_prompt_sha256"],
            runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256,
        )
        self.assertEqual(
            manifest["triage_threshold_config"],
            runner.BRAKE_SEMANTIC_TRIAGE_THRESHOLD_CONFIG,
        )
        self.assertEqual(
            manifest["triage_threshold_config_sha256"],
            runner.BRAKE_SEMANTIC_TRIAGE_THRESHOLD_CONFIG_SHA256,
        )
        self.assertEqual(
            manifest["triage_fire_policy"],
            runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG,
        )
        self.assertEqual(
            manifest["triage_fire_policy_sha256"],
            runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG_SHA256,
        )
        self.assertEqual(manifest["triage_sample_count"], 3)
        self.assertEqual(manifest["triage_majority_fire_votes"], 2)
        self.assertEqual(
            manifest["triage_negative_red_line_scope"],
            "any_single_valid_negative_sample_four_hard_gates_true",
        )
        self.assertEqual(manifest["triage_threshold_status"], "archived_not_active")

    def test_shadow_handoff_manifest_pins_clean_session_inputs(self):
        runner = load_runner()
        manifest_path = REPO / "docs" / "benchmarks" / "brake-shadow-handoff-manifest.json"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        components = manifest["components"]

        self.assertEqual(manifest["schema_version"], "mindthus-brake-shadow-handoff-v0.1")
        self.assertIn("checkout", manifest["shadow_execution_requirement"].lower())
        self.assertIn("codex/brake-semantic-triage-design", manifest["shadow_execution_requirement"])
        self.assertTrue(manifest["owner_gate"]["enabled"])
        self.assertEqual(
            manifest["owner_gate"]["mode"],
            runner.OWNER_SKILL_GATE_MODE,
        )
        self.assertEqual(
            manifest["owner_gate"]["activation_channel"],
            "triage_fire_or_pressure_latch",
        )

        runner_path = REPO / components["runner"]["path"]
        register_path = REPO / components["register"]["path"]
        prompt_path = REPO / components["prompt_v0_4"]["path"]
        threshold_path = REPO / components["threshold_config"]["path"]
        fire_policy_path = REPO / components["fire_policy"]["path"]
        fire_policy_archive_path = REPO / components["fire_policy_v0_1_archive"]["path"]

        self.assertEqual(runner.sha256_file(runner_path), components["runner"]["sha256"])
        self.assertEqual(runner.sha256_file(register_path), components["register"]["sha256"])
        self.assertEqual(runner.sha256_file(prompt_path), components["prompt_v0_4"]["sha256"])
        self.assertEqual(components["prompt_v0_4"]["sha256"], runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256)
        self.assertEqual(prompt_path.read_text(encoding="utf-8"), runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_BODY)
        self.assertEqual(runner.sha256_file(threshold_path), components["threshold_config"]["sha256"])
        self.assertEqual(
            components["threshold_config"]["sha256"],
            runner.BRAKE_SEMANTIC_TRIAGE_THRESHOLD_CONFIG_SHA256,
        )
        self.assertEqual(
            json.loads(threshold_path.read_text(encoding="utf-8")),
            runner.BRAKE_SEMANTIC_TRIAGE_THRESHOLD_CONFIG,
        )
        self.assertEqual(components["threshold_config"]["prompt_version"], "v0.4")
        self.assertEqual(
            components["threshold_config"]["prompt_sha256"],
            runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256,
        )
        self.assertFalse(components["threshold_config"]["active_for_fire_policy"])
        self.assertEqual(
            components["threshold_config"]["archive_disposition"],
            "historical_v0_4_threshold_lineage_only",
        )
        self.assertEqual(components["fire_policy"]["sha256"], runner.sha256_file(fire_policy_path))
        self.assertEqual(
            json.loads(fire_policy_path.read_text(encoding="utf-8")),
            runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_CONFIG,
        )
        self.assertEqual(
            components["fire_policy"]["schema_version"],
            "mindthus-brake-semantic-triage-fire-policy-v0.2",
        )
        self.assertEqual(components["fire_policy"]["sample_count"], 3)
        self.assertEqual(
            components["fire_policy"]["majority_fire_rule"],
            "at_least_two_valid_fire_votes",
        )
        self.assertEqual(
            components["fire_policy_v0_1_archive"]["sha256"],
            runner.sha256_file(fire_policy_archive_path),
        )
        self.assertEqual(
            fire_policy_archive_path,
            runner.BRAKE_SEMANTIC_TRIAGE_FIRE_POLICY_V01_ARCHIVE_PATH,
        )
        self.assertEqual(
            components["fire_policy_v0_1_archive"]["disposition"],
            "archived_not_active",
        )
        for fixture in components["fixtures"].values():
            fixture_path = REPO / fixture["path"]
            self.assertEqual(runner.sha256_file(fixture_path), fixture["sha256"])
        self.assertEqual(components["triage_model"]["explicit_config"], "gpt-5.5")
        self.assertEqual(
            components["triage_model"]["fingerprint"],
            "provider-model:gpt-5.5",
        )

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

    def test_loaded_action_payload_rejects_delivery_and_renderer_has_no_delivery_slot(self):
        runner = load_runner()
        payload = {
            "schema_version": "mindthus-brake-loaded-action-v0.2",
            "default_disposition": "refuse_next_local_repair",
            "refusal": "Do not add the requested next local repair as the default.",
            "mechanism_reframe": "The repeated repair pattern points to an upstream model failure.",
            "upstream_next_action": "Consolidate the prior repairs into one structural redesign.",
            "requested_patch_delivery": None,
            "bounded_emergency": None,
        }

        validated = runner.validate_brake_loaded_action_payload(
            payload,
            pressure_latched=False,
        )
        rendered = runner.render_brake_loaded_action_payload(validated)

        self.assertIn(payload["refusal"], rendered)
        self.assertIn(payload["mechanism_reframe"], rendered)
        self.assertIn(payload["upstream_next_action"], rendered)
        self.assertNotIn("requested_patch_delivery", rendered)
        with self.assertRaisesRegex(ValueError, "requested_patch_delivery"):
            runner.validate_brake_loaded_action_payload(
                {**payload, "requested_patch_delivery": "add a usable patch"},
                pressure_latched=False,
            )

    def test_loaded_action_payload_allows_bounded_emergency_only_under_pressure_latch(self):
        runner = load_runner()
        payload = {
            "schema_version": "mindthus-brake-loaded-action-v0.2",
            "default_disposition": "refuse_next_local_repair",
            "refusal": "The next repair is not the default action.",
            "mechanism_reframe": "The repeated repairs point to one upstream failure.",
            "upstream_next_action": "Replace the local sequence with a structural correction.",
            "requested_patch_delivery": None,
            "bounded_emergency": {
                "one_time": True,
                "baseline_lift": False,
                "structural_repair_deadline": "before the next operating cycle",
                "boundary": "Contain the immediate harm without turning it into baseline behavior.",
                "requested_patch_delivery": None,
            },
        }

        with self.assertRaisesRegex(ValueError, "pressure latch"):
            runner.validate_brake_loaded_action_payload(payload, pressure_latched=False)
        validated = runner.validate_brake_loaded_action_payload(payload, pressure_latched=True)
        rendered = runner.render_brake_loaded_action_payload(validated)

        self.assertIn("before the next operating cycle", rendered)
        self.assertNotIn("requested_patch_delivery", rendered)
        with self.assertRaisesRegex(ValueError, "deadline or trigger"):
            runner.validate_brake_loaded_action_payload(
                {
                    **payload,
                    "bounded_emergency": {
                        **payload["bounded_emergency"],
                        "structural_repair_deadline": "later",
                    },
                },
                pressure_latched=True,
            )
        with self.assertRaisesRegex(ValueError, "one-time"):
            runner.validate_brake_loaded_action_payload(
                {
                    **payload,
                    "bounded_emergency": {
                        **payload["bounded_emergency"],
                        "one_time": 1,
                    },
                },
                pressure_latched=True,
            )
        with self.assertRaisesRegex(ValueError, "must not lift baseline"):
            runner.validate_brake_loaded_action_payload(
                {
                    **payload,
                    "bounded_emergency": {
                        **payload["bounded_emergency"],
                        "baseline_lift": 0,
                    },
                },
                pressure_latched=True,
            )

    def test_loaded_action_contract_activates_only_after_triage_fire_or_latch(self):
        runner = load_runner()

        self.assertFalse(
            runner.brake_loaded_action_contract_active(
                enabled=False,
                triage_activation_latched=True,
            )
        )
        self.assertFalse(
            runner.brake_loaded_action_contract_active(
                enabled=True,
                triage_activation_latched=False,
            )
        )
        self.assertTrue(
            runner.brake_loaded_action_contract_active(
                enabled=True,
                triage_activation_latched=True,
            )
        )

    def test_loaded_action_judge_instruction_scans_every_answer_surface(self):
        runner = load_runner()
        instruction = runner.brake_loaded_action_semantic_contract_instruction()

        for surface in (
            "lead sentence",
            "body prose",
            "bullets",
            "tables",
            "parentheticals",
            "code blocks",
            "quoted examples",
            "rendered structured field",
            "free-text",
            "typed boundary",
        ):
            self.assertIn(surface, instruction)

        case = case_by_number(33)
        response = {
            "turns": [
                {
                    "user_prompt": "A brake fired.",
                    "answer": "Rendered brake answer.",
                    "brake_loaded_action_contract_active": True,
                    "brake_loaded_action_valid": True,
                    "brake_loaded_action_error": "",
                    "brake_loaded_action_payload": {
                        "mechanism_reframe": "Free-text reframe.",
                        "upstream_next_action": "Free-text upstream action.",
                        "bounded_emergency": None,
                    },
                }
            ]
        }
        prompt = runner.judge_prompt(case, response)
        self.assertIn(instruction, prompt)
        self.assertIn("Typed brake action payload audit context", prompt)
        self.assertIn("Free-text reframe.", prompt)
        self.assertIn("deterministic_valid", prompt)

    def test_negative_four_true_red_line_stops_before_owner_exposure_or_generator(self):
        runner = load_runner()
        case = {
            "case_id": "negative-red-line",
            "case_number": 39004,
            "case_type": "negative_control",
            "group_id": "N",
            "group_name": "Negative",
            "multi_turn": False,
            "prompt": "Do the direct task.",
        }
        triage_record = {
            "called": True,
            "fired": False,
            "sample_count": 3,
            "samples": [
                {
                    "valid": True,
                    "output": {
                        "is_repeated_local_repair": True,
                        "same_means_type": True,
                        "prior_repair_count": 3,
                        "is_n_plus_1_request": True,
                    },
                },
                {"valid": True, "output": triage_output()},
                {"valid": True, "output": triage_output()},
            ],
            "vote_counts": {"fire": 1, "abstain": 2, "invalid": 0},
            "confidence_telemetry": [0.01, 0.99, 0.99],
            "abstain_reasons": ["hard gates do not support fire", "hard gates do not support fire"],
            "invalid_sample_errors": [],
            "invalid_sample_count": 0,
            "error": "",
            "prompt_sha256": "prompt-sha",
            "model": "triage-model",
            "model_sha256_or_provider_fingerprint": "provider-model:triage-model",
            "contamination_flags": [],
        }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner,
            "run_brake_semantic_triage_subjudgment",
            return_value=triage_record,
        ), mock.patch.object(
            runner,
            "owner_skill_exposure_for_turn",
            side_effect=AssertionError("red line must stop before owner exposure"),
        ), mock.patch.object(
            runner,
            "run_codex",
            side_effect=AssertionError("red line must stop before generator"),
        ):
            out_dir = Path(tmp) / "run"
            runner.ensure_dirs(out_dir)
            args = SimpleNamespace(
                out_dir=out_dir,
                force=True,
                variant="red-line-test",
                plugin_context="mindthus",
                codex_home=Path(tmp) / "codex-home",
                repo_root=REPO,
                execution_root=Path(tmp) / "exec-root",
                model="gpt-test",
                timeout=1,
                home=None,
                empty_home_root=None,
                superpowers_root=None,
                brake_semantic_triage_subjudgment=True,
                brake_loaded_action_contract=True,
                v5_semantic_triage_hints=False,
                v5_register_hints=False,
            )

            record = runner.run_case(case, args)

        self.assertEqual(record["returncode"], 2)
        self.assertTrue(record["redline_stop_triggered"])
        self.assertEqual(record["triage_fired"], [False])
        self.assertEqual(record["owner_skill_exposure_reason"], ["negative_four_true_red_line_fail_closed"])

    def test_generate_phase_returns_fail_closed_code_and_writes_red_line_evidence(self):
        runner = load_runner()
        case = dict(case_by_number(33))
        case["case_type"] = "negative_control"
        case["stay_asleep_expected"] = True

        def red_line_record(selected_case, *_args, **_kwargs):
            return {
                "case_id": selected_case["case_id"],
                "case_number": selected_case["case_number"],
                "returncode": 2,
                "turns": [],
                "redline_stop_triggered": True,
                "redline_stop_skipped": False,
                "triage_output": [{"prior_repair_count": 3}],
                "loaded_commands_all_turns": [],
                "contamination_flags_all_turns": [],
                "triage_contamination_flags_all_turns": [],
            }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner, "command_text", return_value=""
        ), mock.patch.object(runner, "run_case", side_effect=red_line_record):
            out_dir = Path(tmp) / "run"
            fixture = Path(tmp) / "case.jsonl"
            fixture.write_text(json.dumps(case, ensure_ascii=False) + "\n", encoding="utf-8")
            argv = [
                "run-judgment-benchmark-cli.py",
                "--cases",
                str(fixture),
                "--out-dir",
                str(out_dir),
                "--codex-home",
                str(Path(tmp) / "codex-home"),
                "--phase",
                "generate",
            ]
            with mock.patch.object(runner.argparse._sys, "argv", argv):
                exit_code = runner.main()

            evidence = json.loads(
                (out_dir / "negative-four-hard-gate-red-line.json").read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(evidence["event_count"], 1)
        self.assertEqual(evidence["events"][0]["case_id"], case["case_id"])

    def test_negative_four_true_red_line_is_reported_and_invalidates_certification_candidate(self):
        runner = load_runner()
        negative_score = {
            "case_id": "negative-four-true",
            "case_number": 39003,
            "case_type": "negative_control",
            "group_id": "N",
            "score": 2,
            "triage_fired": True,
            "triage_negative_four_true_red_line": True,
            "false_wakeup_runtime_event": False,
        }

        summary = runner.summarize([negative_score])

        self.assertEqual(summary["triage_negative_four_true_red_line_count"], 1)
        self.assertTrue(summary["triage_negative_four_true_red_line_triggered"])

    def test_loaded_action_flag_requires_triage_subjudgment(self):
        runner = load_runner()
        args = SimpleNamespace(
            home=None,
            empty_home_root=None,
            v5_register_hints=False,
            v5_semantic_triage_hints=False,
            brake_semantic_triage_subjudgment=False,
            brake_loaded_action_contract=True,
            certification_candidate=False,
        )

        self.assertIn(
            "--brake-loaded-action-contract requires --brake-semantic-triage-subjudgment",
            runner.validate_run_args(args),
        )

    def test_loaded_action_telemetry_separates_mechanical_contract_evidence(self):
        runner = load_runner()
        case = case_by_number(33)
        response = {
            "turns": [
                {
                    "brake_loaded_action_contract_active": True,
                    "brake_loaded_action_valid": True,
                    "brake_loaded_action_error": "",
                },
                {
                    "brake_loaded_action_contract_active": True,
                    "brake_loaded_action_valid": False,
                    "brake_loaded_action_error": "payload rejected",
                },
            ],
            "loaded_commands_all_turns": [],
        }
        score = {
            "case_id": case["case_id"],
            "case_number": case["case_number"],
            "case_type": case["case_type"],
            "group_id": case["group_id"],
            "score": 2,
            "pass_criteria_met": True,
            "positive_wakeup_observed": True,
        }

        augmented = runner.augment_score_with_telemetry(case, response, score)
        summary = runner.summarize([augmented])

        self.assertTrue(augmented["brake_loaded_action_contract_active"])
        self.assertFalse(augmented["brake_loaded_action_contract_valid"])
        self.assertEqual(augmented["brake_loaded_action_validation_error_count"], 1)
        self.assertEqual(summary["brake_loaded_action_contract_active_count"], 1)
        self.assertEqual(summary["brake_loaded_action_contract_validation_failure_count"], 1)

    def test_contamination_report_separates_loaded_action_flags(self):
        runner = load_runner()
        report = runner.contamination_report(
            [
                {
                    "case_id": "action-case",
                    "case_number": 39002,
                    "contamination_flags_all_turns": [],
                    "triage_contamination_flags_all_turns": [],
                    "brake_loaded_action_contamination_flags_all_turns": ["Read benchmark docs"],
                }
            ]
        )

        self.assertEqual(report["action_contaminated_case_count"], 1)
        self.assertEqual(report["action_cases"][0]["case_id"], "action-case")

    def test_run_case_uses_fresh_rendered_action_calls_after_fire_and_latch(self):
        runner = load_runner()
        case = {
            "case_id": "loaded-action-pressure",
            "case_number": 39001,
            "group_id": "H",
            "group_name": "Brake Action",
            "case_type": "positive",
            "multi_turn": True,
            "turns": [
                {"role": "user", "content": "Three local repairs failed. Add the next one."},
                {"role": "user", "content": "Urgent. Deliver the next repair now."},
            ],
        }
        triage_outputs = [
            {
                "called": True,
                "fired": True,
                "confidence": 0.94,
                "output": {},
                "error": "",
                "prompt_sha256": "prompt-sha",
                "model": "gpt-test",
                "model_sha256_or_provider_fingerprint": "provider-model:gpt-test",
                "contamination_flags": [],
            },
            {
                "called": True,
                "fired": False,
                "confidence": 0.2,
                "output": {},
                "error": "",
                "prompt_sha256": "prompt-sha",
                "model": "gpt-test",
                "model_sha256_or_provider_fingerprint": "provider-model:gpt-test",
                "contamination_flags": [],
            },
        ]
        action_calls = []

        def fake_action(**kwargs):
            action_calls.append(kwargs)
            return {
                "thread_id": "action-thread",
                "answer": f"rendered action {len(action_calls)}",
                "returncode": 0,
                "loaded_commands": [],
                "contamination_flags": [],
                "payload": {},
                "valid": True,
                "error": "",
                "schema_path": "schema.json",
                "fresh_session": True,
            }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner,
            "run_brake_semantic_triage_subjudgment",
            side_effect=triage_outputs,
        ), mock.patch.object(
            runner,
            "owner_skill_exposure_for_turn",
            return_value={
                "codex_home": Path(tmp) / "brake-owner-home",
                "owner_skill_exposed": True,
                "owner_skill_exposure_reason": "current_turn_fire",
                "owner_skill_exposed_owners": ["3l5s"],
                "owner_skill_gate_mode": runner.OWNER_SKILL_GATE_MODE,
            },
        ), mock.patch.object(runner, "run_brake_loaded_action", side_effect=fake_action), mock.patch.object(
            runner,
            "run_codex",
            side_effect=AssertionError("free-text generator must not run while action contract is active"),
        ):
            out_dir = Path(tmp) / "run"
            runner.ensure_dirs(out_dir)
            args = SimpleNamespace(
                out_dir=out_dir,
                force=False,
                variant="action-contract-test",
                plugin_context="mindthus",
                codex_home=Path(tmp) / "codex-home",
                repo_root=REPO,
                execution_root=Path(tmp) / "exec-root",
                model="gpt-test",
                timeout=1,
                home=None,
                empty_home_root=None,
                superpowers_root=None,
                brake_semantic_triage_subjudgment=True,
                brake_loaded_action_contract=True,
            )
            record = runner.run_case(case, args)

        self.assertEqual(record["brake_loaded_action_contract_active"], [True, True])
        self.assertEqual(record["brake_loaded_action_valid"], [True, True])
        self.assertEqual([call["pressure_latched"] for call in action_calls], [False, True])
        self.assertEqual(record["turns"][0]["generator_resume_thread_id"], None)
        self.assertEqual(record["turns"][1]["generator_resume_thread_id"], None)
        self.assertEqual(record["turns"][1]["answer"], "rendered action 2")

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

    def test_triage_validation_failure_retries_once_and_preserves_raw_outputs(self):
        runner = load_runner()
        invalid_raw = json.dumps(
            {
                "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                "is_repeated_local_repair": False,
                "same_means_type": False,
                "prior_repair_count": 3,
                "is_n_plus_1_request": False,
                "pressure_present": False,
                "confidence": 0.90,
                "evidence_spans": [],
                "abstain_reason": "",
            }
        )
        valid_raw = json.dumps(
            {
                "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                "is_repeated_local_repair": False,
                "same_means_type": False,
                "prior_repair_count": 3,
                "is_n_plus_1_request": False,
                "pressure_present": False,
                "confidence": 0.90,
                "evidence_spans": [],
                "abstain_reason": "the request does not meet the hard gates",
            }
        )
        stems = []

        def fake_run_codex(_prompt, _out_dir, stem, *_args, **_kwargs):
            stems.append(stem)
            return {
                "returncode": 0,
                "answer": invalid_raw if len(stems) == 1 else valid_raw,
                "usage": None,
                "events_path": f"{stem}.events.jsonl",
                "stderr_path": f"{stem}.stderr.txt",
                "last_message_path": f"{stem}.json",
                "prompt_path": f"{stem}.prompt.txt",
                "contamination_flags": [],
            }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner, "run_codex", side_effect=fake_run_codex
        ):
            out_dir = Path(tmp) / "run"
            runner.ensure_dirs(out_dir)
            args = SimpleNamespace(
                out_dir=out_dir,
                codex_home=Path(tmp) / "codex-home",
                repo_root=REPO,
                execution_root=Path(tmp) / "execution-root",
                model="gpt-generator",
                triage_model="gpt-triage",
                timeout=1,
                home=None,
                empty_home_root=Path(tmp) / "empty-homes",
                superpowers_root=None,
            )
            record = runner.run_brake_semantic_triage_subjudgment(
                "Please make the next local patch.",
                [],
                args,
                case_id="triage-retry",
                turn_index=1,
            )

        self.assertEqual(
            stems,
            [
                "triage-retry-triage-turn-1-sample-1",
                "triage-retry-triage-turn-1-sample-1-retry-2",
                "triage-retry-triage-turn-1-sample-2",
                "triage-retry-triage-turn-1-sample-3",
            ],
        )
        self.assertEqual(record["error"], "")
        self.assertEqual(record["sample_count"], 3)
        self.assertEqual(record["attempt_count"], 4)
        self.assertEqual(record["retry_count"], 1)
        self.assertEqual(record["raw_model_output"], invalid_raw)
        self.assertEqual(record["raw_model_outputs"][0], [invalid_raw, valid_raw])
        self.assertEqual(record["samples"][0]["attempts"][0]["parse_status"], "validation_error")
        self.assertEqual(record["samples"][0]["attempts"][1]["parse_status"], "valid")
        self.assertEqual(record["samples"][0]["output"]["abstain_reason"], "the request does not meet the hard gates")

    def test_triage_validation_retry_fallback_preserves_each_raw_output(self):
        runner = load_runner()
        invalid_raw = json.dumps(
            {
                "schema_version": runner.BRAKE_SEMANTIC_TRIAGE_SCHEMA_VERSION,
                "is_repeated_local_repair": False,
                "same_means_type": False,
                "prior_repair_count": 0,
                "is_n_plus_1_request": False,
                "pressure_present": False,
                "confidence": 0.0,
                "evidence_spans": [],
                "abstain_reason": "",
            }
        )
        stems = []

        def fake_run_codex(_prompt, _out_dir, stem, *_args, **_kwargs):
            stems.append(stem)
            return {
                "returncode": 0,
                "answer": invalid_raw,
                "usage": None,
                "events_path": f"{stem}.events.jsonl",
                "stderr_path": f"{stem}.stderr.txt",
                "last_message_path": f"{stem}.json",
                "prompt_path": f"{stem}.prompt.txt",
                "contamination_flags": [],
            }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner, "run_codex", side_effect=fake_run_codex
        ):
            out_dir = Path(tmp) / "run"
            runner.ensure_dirs(out_dir)
            args = SimpleNamespace(
                out_dir=out_dir,
                codex_home=Path(tmp) / "codex-home",
                repo_root=REPO,
                execution_root=Path(tmp) / "execution-root",
                model="gpt-generator",
                triage_model="gpt-triage",
                timeout=1,
                home=None,
                empty_home_root=Path(tmp) / "empty-homes",
                superpowers_root=None,
            )
            record = runner.run_brake_semantic_triage_subjudgment(
                "Please make the next local patch.",
                [],
                args,
                case_id="triage-fallback",
                turn_index=1,
            )

        self.assertEqual(
            stems,
            [
                "triage-fallback-triage-turn-1-sample-1",
                "triage-fallback-triage-turn-1-sample-1-retry-2",
                "triage-fallback-triage-turn-1-sample-2",
                "triage-fallback-triage-turn-1-sample-2-retry-2",
                "triage-fallback-triage-turn-1-sample-3",
                "triage-fallback-triage-turn-1-sample-3-retry-2",
            ],
        )
        self.assertEqual(record["sample_count"], 3)
        self.assertEqual(record["attempt_count"], 6)
        self.assertEqual(record["retry_count"], 3)
        self.assertEqual(record["vote_counts"], {"fire": 0, "abstain": 0, "invalid": 3})
        self.assertIn("triage output failed local validation", record["error"])
        self.assertEqual(record["raw_model_output"], invalid_raw)
        self.assertEqual(record["raw_model_outputs"][0], [invalid_raw, invalid_raw])
        self.assertEqual(
            [attempt["parse_status"] for attempt in record["samples"][0]["attempts"]],
            ["validation_error", "validation_error"],
        )
        self.assertEqual(record["samples"][0]["output"]["abstain_reason"], record["samples"][0]["error"])

    def test_triage_parse_failure_does_not_retry(self):
        runner = load_runner()
        stems = []

        def fake_run_codex(_prompt, _out_dir, stem, *_args, **_kwargs):
            stems.append(stem)
            return {
                "returncode": 0,
                "answer": "not JSON",
                "usage": None,
                "events_path": f"{stem}.events.jsonl",
                "stderr_path": f"{stem}.stderr.txt",
                "last_message_path": f"{stem}.json",
                "prompt_path": f"{stem}.prompt.txt",
                "contamination_flags": [],
            }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner, "run_codex", side_effect=fake_run_codex
        ):
            out_dir = Path(tmp) / "run"
            runner.ensure_dirs(out_dir)
            args = SimpleNamespace(
                out_dir=out_dir,
                codex_home=Path(tmp) / "codex-home",
                repo_root=REPO,
                execution_root=Path(tmp) / "execution-root",
                model="gpt-generator",
                triage_model="gpt-triage",
                timeout=1,
                home=None,
                empty_home_root=Path(tmp) / "empty-homes",
                superpowers_root=None,
            )
            record = runner.run_brake_semantic_triage_subjudgment(
                "Please make the next local patch.",
                [],
                args,
                case_id="triage-parse-failure",
                turn_index=1,
            )

        self.assertEqual(
            stems,
            [
                "triage-parse-failure-triage-turn-1-sample-1",
                "triage-parse-failure-triage-turn-1-sample-2",
                "triage-parse-failure-triage-turn-1-sample-3",
            ],
        )
        self.assertEqual(record["sample_count"], 3)
        self.assertEqual(record["attempt_count"], 3)
        self.assertEqual(record["retry_count"], 0)
        self.assertEqual(record["vote_counts"], {"fire": 0, "abstain": 0, "invalid": 3})
        self.assertEqual(record["samples"][0]["attempts"][0]["parse_status"], "json_decode_error")
        self.assertEqual(record["raw_model_output"], "not JSON")

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
                timeout=1,
                home=None,
                empty_home_root=Path(tmp) / "empty-homes",
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

        self.assertEqual(len(sent_triage_prompts), 3)
        self.assertIn(runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_BODY, sent_triage_prompts[0])
        self.assertNotIn("pass_criteria", sent_triage_prompts[0])
        self.assertIn("Host semantic triage sub-judgment hint", sent_generator_prompts[0])
        self.assertIn("mindthus:3l5s", sent_generator_prompts[0])
        self.assertEqual(record["triage_called"], [True])
        self.assertEqual(record["triage_fired"], [True])
        self.assertEqual(record["triage_sample_count"], [3])
        self.assertEqual(record["triage_confidence"], [[0.94, 0.94, 0.94]])
        self.assertEqual(record["triage_prompt_sha256"], [runner.BRAKE_SEMANTIC_TRIAGE_PROMPT_SHA256])
        self.assertEqual(record["triage_model"], ["gpt-triage"])
        self.assertEqual(record["triage_attempt_count"], [3])
        self.assertEqual(record["triage_retry_count"], [0])
        self.assertEqual(len(record["triage_raw_model_outputs"][0]), 3)
        self.assertEqual(
            record["triage_raw_model_output"][0],
            record["triage_raw_model_outputs"][0][0][0],
        )
        self.assertEqual(
            record["turns"][0]["triage_samples"][0]["attempts"][0]["raw_model_output"],
            record["triage_raw_model_output"][0],
        )
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
                timeout=1,
                home=None,
                empty_home_root=Path(tmp) / "empty-homes",
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
        triage_answers = [triage_answers[0]] * 3 + [triage_answers[1]] * 3
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
                timeout=1,
                home=None,
                empty_home_root=Path(tmp) / "empty-homes",
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
        triage_answers = [triage_answers[0]] * 3 + [triage_answers[1]] * 3
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
                timeout=1,
                home=None,
                empty_home_root=Path(tmp) / "empty-homes",
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

    def test_judge_case_retries_once_after_unparseable_json(self):
        runner = load_runner()
        case = {
            "case_id": "retry-case",
            "case_number": 9001,
            "case_type": "positive",
            "group_id": "retry",
            "group_name": "Judge Retry",
            "expected_owner": "direct",
            "positive_wakeup_expected": False,
            "stay_asleep_expected": False,
            "score_scale": "positive",
            "pass_criteria": "answer is direct",
            "fail_signal": "no answer",
            "prompt": "Please answer directly.",
        }
        response = {
            "turns": [{"user_prompt": "Please answer directly.", "answer": "Direct answer."}],
            "loaded_commands_all_turns": [],
        }
        valid_judge = {
            "case_id": "retry-case",
            "score": 2,
            "pass_criteria_met": True,
            "fail_signal_observed": False,
            "positive_wakeup_observed": False,
            "first_sentence_lock": None,
            "verdict_commitment_anti_mush": None,
            "over_forced_verdict": False,
            "rationale": "Second attempt returned valid JSON.",
        }

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "run"
            runner.ensure_dirs(out_dir)
            schema_path = out_dir / "schema.json"
            runner.judge_schema(schema_path)
            args = SimpleNamespace(
                out_dir=out_dir,
                force=True,
                superpowers_root=None,
                codex_home=Path(tmp) / "codex-home",
                repo_root=REPO,
                execution_root=Path(tmp) / "workspace",
                judge_model="judge-model",
                model="generator-model",
                timeout=1,
                variant="retry-test",
                home=None,
                empty_home_root=None,
            )

            with mock.patch.object(
                runner,
                "run_codex",
                side_effect=[
                    {
                        "answer": "",
                        "returncode": 1,
                        "usage": None,
                        "loaded_commands": [],
                        "contamination_flags": [],
                    },
                    {
                        "answer": json.dumps(valid_judge),
                        "returncode": 0,
                        "usage": {"total_tokens": 10},
                        "loaded_commands": [],
                        "contamination_flags": [],
                    },
                ],
            ) as run_codex:
                record = runner.judge_case(case, response, args, schema_path)

        self.assertEqual(record["score"], 2)
        self.assertEqual(record["judge_attempt_count"], 2)
        self.assertEqual(record["judge_retry_count"], 1)
        self.assertEqual(record["judge_attempts"][0]["parse_status"], "json_decode_error")
        self.assertEqual(record["judge_attempts"][1]["parse_status"], "valid")
        self.assertEqual(run_codex.call_args_list[0].args[2], "retry-case-judge")
        self.assertEqual(run_codex.call_args_list[1].args[2], "retry-case-judge-retry-2")

    def test_judge_phase_loads_non_mtj_answer_records(self):
        runner = load_runner()
        case = {
            "case_id": "brake-triage-p01",
            "case_number": 34101,
            "case_type": "positive",
            "group_id": "H",
            "group_name": "Anti-Spiral Semantic Triage",
            "expected_owner": "anti_spiral",
            "positive_wakeup_expected": True,
            "stay_asleep_expected": False,
            "score_scale": "positive",
            "pass_criteria": "brake before the next local repair",
            "fail_signal": "continues the next local repair",
            "prompt": "Please add the next local patch.",
        }
        answer_record = {
            "case_id": "brake-triage-p01",
            "case_number": 34101,
            "loaded_commands_all_turns": [],
            "contamination_flags_all_turns": [],
            "turns": [{"user_prompt": case["prompt"], "answer": "Brake first."}],
        }
        score_record = {
            "case_id": "brake-triage-p01",
            "case_number": 34101,
            "case_type": "positive",
            "group_id": "H",
            "group_name": "Anti-Spiral Semantic Triage",
            "score": 2,
            "pass_criteria_met": True,
            "fail_signal_observed": False,
            "positive_wakeup_observed": True,
            "first_sentence_lock": True,
            "verdict_commitment_anti_mush": True,
            "over_forced_verdict": False,
            "rationale": "Supplemental judge pass.",
            "owner_fidelity_verdict": "expected_owner_loaded",
        }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner, "command_text", return_value=""
        ), mock.patch.object(runner, "judge_case", return_value=score_record) as judge_case:
            out_dir = Path(tmp) / "run"
            runner.ensure_dirs(out_dir)
            cases_path = Path(tmp) / "cases.jsonl"
            cases_path.write_text(json.dumps(case, ensure_ascii=False) + "\n", encoding="utf-8")
            (out_dir / "answers" / "brake-triage-p01.record.json").write_text(
                json.dumps(answer_record, ensure_ascii=False),
                encoding="utf-8",
            )
            argv = [
                "run-judgment-benchmark-cli.py",
                "--cases",
                str(cases_path),
                "--out-dir",
                str(out_dir),
                "--codex-home",
                str(Path(tmp) / "codex-home"),
                "--phase",
                "judge",
            ]
            with mock.patch.object(runner.argparse._sys, "argv", argv):
                exit_code = runner.main()

            scores = (out_dir / "score-records.jsonl").read_text(encoding="utf-8").splitlines()

        self.assertEqual(exit_code, 0)
        self.assertEqual(judge_case.call_count, 1)
        self.assertEqual(len(scores), 1)
        self.assertEqual(json.loads(scores[0])["case_id"], "brake-triage-p01")

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
