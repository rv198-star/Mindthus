import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.json"
LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.lock.json"
AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-evidence-view.1.json"
)
FREEZER = BETA_ROOT / "runtime" / "freeze-evaluation-evidence-view-v0.4.py"
AUTH_VALIDATOR = (
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4-evidence-view.py"
)
RUNNER = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v04_evidence_view.py"
ANALYZER = BETA_ROOT / "runtime" / "analyze_codex_evaluation_v04_evidence_view.py"
EVIDENCE = BETA_ROOT / "runtime" / "workspace_evidence_view_v04.py"
SOURCE_RUN = (
    REPO
    / ".tplan"
    / "missions"
    / "mindthus-beta2-evaluation"
    / "artifacts"
    / "real-v04-evaluation-a6e9da7e"
    / "run"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BetaTwoV04EvidenceViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = load_module("beta2_workspace_evidence", EVIDENCE)
        cls.freezer = load_module("beta2_evidence_view_freezer", FREEZER)
        cls.analyzer = load_module("beta2_evidence_view_analyzer", ANALYZER)
        cls.runner = load_module("beta2_evidence_view_runner", RUNNER)
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def test_protocol_preserves_artifacts_budget_and_post_outcome_label(self) -> None:
        report = self.freezer.validate_protocol(self.protocol)
        self.assertEqual(report["amendment_id"], "0.4-evidence-view.1")
        self.assertEqual(report["retained_judge_records"], 30)
        self.assertEqual(report["retrospective_rejudge_records"], 6)
        config = self.protocol["workspace_evidence_view"]
        self.assertFalse(config["candidate_answer_mutation_allowed"])
        self.assertFalse(config["generator_retry_allowed"])
        self.assertFalse(config["rubric_change_allowed"])
        self.assertTrue(config["prior_judge_records_retained"])
        self.assertTrue(config["post_outcome_amendment"])
        budget = self.protocol["budget_accounting"]
        self.assertEqual(budget["minimum_calls_after_rejudge_and_matched"], 462)
        self.assertEqual(budget["retry_headroom_at_minimum"], 18)
        self.assertFalse(budget["budget_expansion"])

    def test_trigger_is_narrow_deterministic_and_multilingual(self) -> None:
        positives = (
            "当前工作区是空目录，也不是 Git 仓库。",
            "The working directory is read-only.",
            "Please mount the project files.",
        )
        negatives = (
            "直接检查失败测试并修复。",
            "Compare the two strategies and state the trade-off.",
        )
        self.assertTrue(all(self.evidence.requires_workspace_evidence(x) for x in positives))
        self.assertTrue(all(not self.evidence.requires_workspace_evidence(x) for x in negatives))
        self.assertEqual(
            hashlib.sha256(self.evidence.WORKSPACE_CLAIM_PATTERN.pattern.encode()).hexdigest(),
            self.protocol["workspace_evidence_view"]["trigger_pattern_sha256"],
        )

    def test_capsule_is_identical_across_three_empty_non_git_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests = {}
            for arm in ("stable", "direct-only", "thin-kernel"):
                project = root / arm / "project"
                project.mkdir(parents=True)
                manifests[arm] = {"host": {"execution_root": str(project)}}
            capsule = self.evidence.build_capsule(manifests)
            self.evidence.validate_capsule(capsule)
            encoded = json.dumps(capsule, ensure_ascii=False)
            self.assertNotIn("stable", encoded)
            self.assertNotIn("direct-only", encoded)
            self.assertNotIn("thin-kernel", encoded)
            self.assertEqual(capsule["workspace_facts"]["project_entry_count"], 0)
            self.assertFalse(capsule["workspace_facts"]["git_repository"])
            self.assertEqual(capsule["workspace_facts"]["generator_sandbox_access"], "read-only")

    def test_capsule_fails_closed_when_one_arm_workspace_differs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifests = {}
            for arm in ("stable", "direct-only", "thin-kernel"):
                project = root / arm / "project"
                project.mkdir(parents=True)
                manifests[arm] = {"host": {"execution_root": str(project)}}
            (root / "thin-kernel" / "project" / "unexpected.py").write_text("x")
            with self.assertRaises(self.evidence.WorkspaceEvidenceError):
                self.evidence.build_capsule(manifests)

    def test_evidence_input_and_prompt_keep_the_capsule_in_its_lane(self) -> None:
        capsule = {
            "schema_version": "mindthus-beta2-workspace-evidence-v0.4",
            "scope": self.evidence.CAPSULE_SCOPE,
            "workspace_facts": {
                "project_entry_count": 0,
                "git_repository": False,
                "generator_sandbox_access": "read-only",
            },
            "arm_specific_data_present": False,
            "runtime_action_trace_present": False,
            "skill_or_method_trace_present": False,
            "provenance": (
                "runner-verified common execution-root state plus frozen read-only "
                "generator sandbox configuration"
            ),
        }
        capsule["capsule_digest"] = self.evidence.canonical_sha256(capsule)
        contract = {
            "case_type": "negative_control",
            "entry_mode": "stay-asleep",
            "accepted_execution_owners": ["direct_debugging"],
            "expected_primitive_obligations": [],
            "required_visible_action": None,
            "stay_asleep_expected": True,
        }
        candidate = "当前工作区为空，也不是 Git 仓库。"
        payload = self.evidence.expected_input(
            output_id="o" * 64,
            raw_prompt="继续修复",
            contract=contract,
            candidate=candidate,
            capsule=capsule,
        )
        prompt = self.evidence.judge_prompt(
            rubric={"fixture": True},
            case={"contract": contract},
            prompt="继续修复",
            candidate=candidate,
            blinded_output_id="o" * 64,
            capsule=capsule,
        )
        self.assertTrue(payload["workspace_evidence_present"])
        self.assertFalse(payload["runtime_telemetry_present"])
        self.assertIn("Do not use it as evidence of a hidden action", prompt)
        self.assertNotIn("stable", prompt)
        self.assertNotIn("thin-kernel", prompt)

    def test_evidence_identity_is_separate_from_original_judge_identity(self) -> None:
        amendment_sha = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
        cell_id = "c" * 64
        evidence_id = self.evidence.evidence_identity(amendment_sha, cell_id)
        base_id = self.runner.base.judge_identity(
            self.protocol["base_binding"]["protocol_sha256"], cell_id
        )
        self.assertNotEqual(evidence_id, base_id)
        self.assertEqual(evidence_id, self.evidence.evidence_identity(amendment_sha, cell_id))

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "local retained v0.4 evidence is unavailable")
    def test_retained_source_sets_match_the_frozen_pre_amendment_digests(self) -> None:
        source = self.protocol["retained_source_run"]
        snapshot = (
            SOURCE_RUN
            / "recovery"
            / "0.4-evidence-view.1"
            / "pre-amendment"
            / "receipt.json"
        )
        sets = (
            json.loads(snapshot.read_text(encoding="utf-8"))
            if snapshot.is_file()
            else self.runner._source_sets(SOURCE_RUN)
        )
        checks = {
            "cells": (15, source["cell_set_digest"]),
            "generation_attempts": (16, source["generation_attempt_set_digest"]),
            "judge_attempts": (36, source["judge_attempt_set_digest"]),
            "judge_records": (30, source["judge_record_set_digest"]),
            "judge_inputs": (15, source["judge_input_set_digest"]),
            "blinded_views": (3, source["blinded_view_receipt_set_digest"]),
        }
        for name, (count, digest) in checks.items():
            self.assertEqual(len(sets[name]), count)
            self.assertEqual(self.runner.base.canonical_sha256(sets[name]), digest)

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "local retained v0.4 evidence is unavailable")
    def test_diagnosed_three_arm_event_traces_are_still_bound(self) -> None:
        self.runner._validate_diagnosed_events(SOURCE_RUN, self.protocol)
        cells = self.protocol["diagnosis"]["affected_cells"]
        self.assertEqual({item["arm_id"] for item in cells}, {"stable", "direct-only", "thin-kernel"})
        self.assertEqual(
            {tuple(item["prior_authority_regression_votes"]) for item in cells},
            {(True, True), (False, False)},
        )

    def test_preflight_cannot_execute_a_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            auth_report = {
                "evidence_view_protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
            }
            capsule = {
                "capsule_digest": "d" * 64,
            }
            args = argparse.Namespace(
                phase="smoke",
                out_dir=out,
                runtime_root=out / "runtime",
                arm_manifest=[Path("stable"), Path("direct"), Path("thin")],
                authorization=AUTHORIZATION,
                auth_source=out / "auth.json",
                timeout=1800,
                preflight_only=True,
            )
            with mock.patch.object(
                self.runner.base,
                "authorized_context",
                return_value=(auth_report, {"fixture": True}, {"fixture": True}),
            ), mock.patch.object(
                self.runner.base, "verify_arm_set", return_value={}
            ), mock.patch.object(
                self.runner, "ensure_source_snapshot"
            ), mock.patch.object(
                self.runner, "ensure_capsule", return_value=capsule
            ), mock.patch.object(
                self.runner.blinded_runner, "generate_cells"
            ) as generate, mock.patch.object(
                self.runner, "judge_cells"
            ) as judge:
                report, code = self.runner.run_evidence_view(args)
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "ready")
            self.assertFalse(report["model_execution_performed"])
            generate.assert_not_called()
            judge.assert_not_called()

    @unittest.skipUnless(LOCK.is_file(), "evidence-view lock freezes after tests")
    def test_official_evidence_view_lock_validates(self) -> None:
        report = self.freezer.validate_lock(PROTOCOL, LOCK)
        self.assertEqual(report["status"], "frozen")

    @unittest.skipUnless(AUTHORIZATION.is_file(), "authorization binds after freeze")
    def test_official_evidence_view_authorization_validates(self) -> None:
        validator = load_module("beta2_evidence_view_auth_validator", AUTH_VALIDATOR)
        report = validator.validate_authorization(AUTHORIZATION)
        self.assertEqual(report["status"], "authorized")
        self.assertEqual(report["token_budget"]["maximum"], 17599744)
        self.assertFalse(report["release_preparation"])


if __name__ == "__main__":
    unittest.main()
