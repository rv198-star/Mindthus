import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "wae" / "scripts" / "delegation_loop.py"
SCHEMA = REPO / "skills" / "wae" / "resources" / "wae-loop-trace.schema.json"


def load_runtime_module():
    spec = importlib.util.spec_from_file_location("wae_delegation_loop_test_runtime", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class WaeDelegationLoopRuntimeTests(unittest.TestCase):
    def run_cli(self, root: Path, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(root), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected,
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def enable(self, root: Path, *, run_id: str = "run-test") -> dict:
        result = self.run_cli(
            root,
            "enable",
            "--activation-id",
            run_id,
            "--scope-id",
            "P2-to-P3",
            "--scope-kind",
            "phase",
            "--enabled-by",
            "user",
            "--project",
            "demo",
            "--host",
            "codex",
            "--model-mode",
            "sol-high",
            "--current-owner",
            "P2 designer",
            "--downstream-owner",
            "P3 implementer",
            "--handoff-purpose",
            "implement the reviewed interaction slice",
            "--current-responsibility",
            "close product interaction semantics",
            "--downstream-freedom",
            "choose implementation structure",
            "--reserved-decision",
            "product-owner-only policy",
        )
        return json.loads(result.stdout)

    def test_default_state_is_disabled_and_does_not_create_runtime_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_cli(root, "status")
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "disabled")
            self.assertFalse((root / ".mindthus" / "wae-loop").exists())

    def test_enable_allows_mechanical_downstream_with_no_agentic_freedom_or_reserved_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_cli(
                root,
                "enable",
                "--activation-id",
                "mechanical-run",
                "--scope-id",
                "render-contract",
                "--current-owner",
                "semantic owner",
                "--downstream-owner",
                "renderer",
                "--handoff-purpose",
                "render determined output",
                "--current-responsibility",
                "determine all result-changing semantics",
            )
            payload = json.loads(result.stdout)
            bundle = json.loads(Path(payload["bundle"]).read_text(encoding="utf-8"))
            self.assertEqual(bundle["activation"]["downstream_freedom"], [])
            self.assertEqual(bundle["activation"]["reserved_decisions"], [])

    def test_enable_creates_fixed_project_local_trace_and_portable_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = self.enable(root)
            self.assertEqual(payload["status"], "active")
            runtime = root / ".mindthus" / "wae-loop"
            run = runtime / "runs" / "run-test"
            for path in (
                runtime / "active.json",
                run / "activation.json",
                run / "trace.jsonl",
                run / "summary.json",
                run / "wae-loop-run.json",
            ):
                self.assertTrue(path.is_file(), path)
            bundle = json.loads((run / "wae-loop-run.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle["activation"]["scope_id"], "P2-to-P3")
            self.assertEqual(bundle["summary"]["checkpoint_count"], 0)
            self.assertEqual(bundle["events"][0]["event_type"], "activation")
            self.assertNotIn(str(root.resolve()), json.dumps(bundle, ensure_ascii=False))
            self.assertFalse(bundle["activation"]["logging"]["private_reasoning_recorded"])
            self.assertFalse(bundle["activation"]["logging"]["raw_artifact_contents_recorded"])

    def test_active_scope_records_refine_work_handoff_outcome_and_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "design.md"
            artifact.write_text("v1 design\n", encoding="utf-8")
            self.enable(root)

            opened = json.loads(self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--artifact",
                "design.md",
                "--blocking-remainder",
                "approval-after-edit remains upstream-owned",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "P3 would invent approval semantics",
                "--next-minimum-work",
                "decide version-bound approval behavior",
                "--unit-kind",
                "semantic_decision",
                "--unit-scope",
                "approval-after-edit semantics and its direct version-binding dependency",
                "--completion-criterion",
                "one canonical approval-after-edit rule is explicit and evidence-bound",
                "--evidence-ref",
                "PRD#approval",
                "--model-requests",
                "1",
                "--elapsed-ms",
                "1200",
            ).stdout)
            self.assertEqual(opened["refinement_unit_id"], "RU-0001")
            self.run_cli(
                root,
                "work",
                "--unit-id",
                "RU-0001",
                "--work-kind",
                "design_decision",
                "--changed-scope",
                "approval-after-edit semantics",
                "--artifact-before-ref",
                "approval-analysis@v1",
                "--artifact-after-ref",
                "approval-analysis@v2",
            )
            self.run_cli(
                root,
                "refine-result",
                "--unit-id",
                "RU-0001",
                "--result-status",
                "resolved",
                "--result-summary",
                "Editing approved content creates a new unapproved revision while preserving the approved snapshot.",
                "--result-artifact-ref",
                "approval-rule@v1",
                "--resolved-remainder",
                "approval-after-edit remains upstream-owned",
                "--evidence-ref",
                "PRD#approval",
            )
            artifact.write_text("v2 design with version-bound approval\n", encoding="utf-8")
            self.run_cli(
                root,
                "absorb",
                "--unit-id",
                "RU-0001",
                "--absorb-mode",
                "update",
                "--parent-after",
                "design.md",
                "--absorbed-scope",
                "approval-after-edit semantics and direct version binding",
            )
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--artifact",
                "design.md",
                "--owner-of-remainder",
                "downstream",
                "--evidence-ref",
                "PRD#approval",
            )
            self.run_cli(
                root,
                "outcome",
                "--handoff-result",
                "downstream_completed",
                "--downstream-invented-upstream-semantics",
                "no",
                "--downstream-requested-missing-upstream-decision",
                "no",
                "--downstream-overrode-handoff",
                "no",
                "--rework-required",
                "no",
                "--rework-owner",
                "none",
                "--acceptance-result",
                "pass",
                "--downstream-outcome-coverage",
                "complete",
            )
            self.run_cli(root, "finish", "--status", "completed")
            self.assertFalse((root / ".mindthus" / "wae-loop" / "active.json").exists())

            validate = json.loads(self.run_cli(root, "validate", "--activation-id", "run-test").stdout)
            self.assertTrue(validate["valid"], validate)
            bundle = json.loads(
                (root / ".mindthus" / "wae-loop" / "runs" / "run-test" / "wae-loop-run.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(bundle["summary"]["checkpoint_count"], 2)
            self.assertEqual(bundle["summary"]["refine_count"], 1)
            self.assertEqual(bundle["summary"]["work_event_count"], 1)
            self.assertEqual(bundle["summary"]["refine_result_count"], 1)
            self.assertEqual(bundle["summary"]["absorb_count"], 1)
            self.assertEqual(bundle["summary"]["refinement_unit_count"], 1)
            self.assertIsNone(bundle["summary"]["active_refinement_unit_id"])
            self.assertEqual(bundle["summary"]["outcome_count"], 1)
            self.assertEqual(bundle["summary"]["status"], "completed")
            checkpoint = next(event for event in bundle["events"] if event["event_type"] == "checkpoint")
            self.assertEqual(checkpoint["artifact"]["ref"], "design.md")
            self.assertEqual(checkpoint["artifact"]["sha256"], hashlib.sha256(b"v1 design\n").hexdigest())

    def test_completed_finish_requires_a_handoff_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            result = self.run_cli(root, "finish", "--status", "completed", expected=2)
            self.assertIn("requires latest checkpoint decision", result.stderr)
            self.assertTrue((root / ".mindthus" / "wae-loop" / "active.json").is_file())

    def test_need_input_requires_external_or_upstream_owned_remainder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            bad = self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "need_input",
                "--blocking-remainder",
                "product policy missing",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "P3 would invent the policy",
                expected=2,
            )
            self.assertIn("upstream/external", bad.stderr)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "need_input",
                "--blocking-remainder",
                "product policy missing",
                "--owner-of-remainder",
                "upstream",
                "--consequence-if-handoff-now",
                "P3 would invent the policy",
            )
            self.run_cli(root, "finish", "--status", "need_input")

    def test_work_requires_latest_checkpoint_to_be_refine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--owner-of-remainder",
                "downstream",
                "--artifact-ref",
                "P2-final",
            )
            result = self.run_cli(
                root,
                "work",
                "--work-kind",
                "correction",
                "--changed-scope",
                "one rule",
                expected=2,
            )
            self.assertIn("requires one open Refinement Unit", result.stderr)

    def test_duplicate_activation_is_rejected_without_overwriting_existing_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            before = (root / ".mindthus" / "wae-loop" / "runs" / "run-test" / "activation.json").read_bytes()
            result = self.run_cli(
                root,
                "enable",
                "--activation-id",
                "other-run",
                "--scope-id",
                "other",
                "--current-owner",
                "A",
                "--downstream-owner",
                "B",
                "--handoff-purpose",
                "x",
                "--current-responsibility",
                "x",
                "--downstream-freedom",
                "x",
                "--reserved-decision",
                "x",
                expected=2,
            )
            self.assertIn("already active", result.stderr)
            self.assertEqual(
                before,
                (root / ".mindthus" / "wae-loop" / "runs" / "run-test" / "activation.json").read_bytes(),
            )

    def test_artifact_paths_must_be_project_local_and_contents_are_not_copied(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as external_tmp:
            root = Path(tmp)
            self.enable(root)
            secretish = root / "artifact.txt"
            secretish.write_text("full artifact body should stay outside trace", encoding="utf-8")
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--owner-of-remainder",
                "downstream",
                "--artifact",
                "artifact.txt",
            )
            bundle_text = (
                root / ".mindthus" / "wae-loop" / "runs" / "run-test" / "wae-loop-run.json"
            ).read_text(encoding="utf-8")
            self.assertNotIn("full artifact body", bundle_text)
            outside = Path(external_tmp) / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            result = self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--owner-of-remainder",
                "downstream",
                "--artifact",
                str(outside),
                expected=2,
            )
            self.assertIn("inside project root", result.stderr)

    def test_guard_handoff_allows_default_off_and_requires_matching_active_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            disabled = json.loads(self.run_cli(root, "guard-handoff").stdout)
            self.assertTrue(disabled["allowed"])
            self.assertEqual(disabled["status"], "disabled")

            artifact = root / "design.md"
            artifact.write_text("v1\n", encoding="utf-8")
            self.enable(root)
            blocked = self.run_cli(root, "guard-handoff", "--artifact", "design.md", expected=2)
            self.assertIn("requires a checkpoint", blocked.stderr)

            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--owner-of-remainder",
                "downstream",
                "--artifact",
                "design.md",
            )
            allowed = json.loads(self.run_cli(root, "guard-handoff", "--artifact", "design.md").stdout)
            self.assertTrue(allowed["allowed"])
            self.assertEqual(allowed["status"], "active")

            artifact.write_text("v2 changed after checkpoint\n", encoding="utf-8")
            mismatch = self.run_cli(root, "guard-handoff", "--artifact", "design.md", expected=2)
            self.assertIn("does not match latest checkpoint", mismatch.stderr)

    def test_outcome_can_be_appended_after_scope_finish_by_activation_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--owner-of-remainder",
                "downstream",
                "--artifact-ref",
                "final-design-v1",
            )
            self.run_cli(root, "finish", "--status", "completed")
            self.run_cli(
                root,
                "outcome",
                "--activation-id",
                "run-test",
                "--handoff-result",
                "returned_upstream",
                "--downstream-requested-missing-upstream-decision",
                "yes",
                "--rework-required",
                "yes",
                "--rework-owner",
                "current",
                "--acceptance-result",
                "fail",
            )
            bundle = json.loads(
                (root / ".mindthus" / "wae-loop" / "runs" / "run-test" / "wae-loop-run.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(bundle["summary"]["status"], "completed")
            self.assertEqual(bundle["summary"]["outcome_count"], 1)
            self.assertEqual(bundle["events"][-1]["event_type"], "outcome")

    def test_validate_detects_trace_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            trace = root / ".mindthus" / "wae-loop" / "runs" / "run-test" / "trace.jsonl"
            rows = trace.read_text(encoding="utf-8").splitlines()
            event = json.loads(rows[0])
            event["scope_id"] = "tampered"
            trace.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")
            result = self.run_cli(root, "validate", "--activation-id", "run-test", expected=1)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertTrue(any("event hash mismatch" in item for item in report["runs"][0]["findings"]))

    def test_guard_handoff_fails_closed_when_trace_integrity_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--owner-of-remainder",
                "downstream",
                "--artifact-ref",
                "P2-final",
            )
            trace = root / ".mindthus" / "wae-loop" / "runs" / "run-test" / "trace.jsonl"
            rows = trace.read_text(encoding="utf-8").splitlines()
            event = json.loads(rows[-1])
            event["blocking_remainder"] = ["tampered after fsync"]
            rows[-1] = json.dumps(event, ensure_ascii=False, sort_keys=True)
            trace.write_text("\n".join(rows) + "\n", encoding="utf-8")
            result = self.run_cli(root, "guard-handoff", "--artifact-ref", "P2-final", expected=2)
            self.assertIn("run integrity invalid", result.stderr)
            self.assertIn("event hash mismatch", result.stderr)

    def test_append_recovers_stale_derived_state_from_valid_fsynced_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            runtime = load_runtime_module()
            runtime_root = runtime.runtime_root(root)
            payload = {
                "event_type": "checkpoint",
                "decision": "handoff",
                "artifact": None,
                "blocking_remainder": [],
                "owner_of_remainder": "downstream",
                "consequence_if_handoff_now": "",
                "next_minimum_work": "",
                "evidence_refs": [],
                "cost": {},
                "refinement_unit": None,
            }
            original_write_derived_state = runtime.write_derived_state
            calls = {"count": 0}

            def fail_after_trace(root_arg, run_id_arg, activation_arg, events_arg):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise RuntimeError("simulated crash after trace fsync")
                return original_write_derived_state(root_arg, run_id_arg, activation_arg, events_arg)

            with mock.patch.object(runtime, "write_derived_state", side_effect=fail_after_trace):
                with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                    runtime.append_event(runtime_root, "run-test", payload)
            stale_summary = json.loads(
                (runtime_root / "runs" / "run-test" / "summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(stale_summary["event_count"], 1)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--owner-of-remainder",
                "downstream",
                "--artifact-ref",
                "P2-final-v2",
            )
            trace = [
                json.loads(line)
                for line in (runtime_root / "runs" / "run-test" / "trace.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([event["sequence"] for event in trace], [1, 2, 3])
            report = json.loads(self.run_cli(root, "validate", "--activation-id", "run-test").stdout)
            self.assertTrue(report["valid"], report)

    def test_activation_agreement_digest_detects_post_enable_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            run = root / ".mindthus" / "wae-loop" / "runs" / "run-test"
            activation_path = run / "activation.json"
            activation = json.loads(activation_path.read_text(encoding="utf-8"))
            activation["reserved_decisions"].append("tampered authority")
            activation_path.write_text(json.dumps(activation, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            report = json.loads(self.run_cli(root, "validate", "--activation-id", "run-test", expected=1).stdout)
            self.assertFalse(report["valid"])
            self.assertTrue(any("activation agreement digest mismatch" in item for item in report["runs"][0]["findings"]))
            blocked = self.run_cli(root, "guard-handoff", expected=2)
            self.assertIn("activation agreement", blocked.stderr)

    def test_persisted_event_shape_is_validated_even_when_hash_chain_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            runtime = load_runtime_module()
            runtime_root = runtime.runtime_root(root)
            with self.assertRaises(runtime.RuntimeErrorMessage):
                runtime.append_event(runtime_root, "run-test", {"event_type": "checkpoint", "decision": "bogus"})
            activation = json.loads((runtime_root / "runs" / "run-test" / "activation.json").read_text(encoding="utf-8"))
            trace_path = runtime_root / "runs" / "run-test" / "trace.jsonl"
            events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
            invalid = {
                "schema_version": runtime.SCHEMA_VERSION,
                "activation_id": "run-test",
                "activation_sha256": activation["activation_sha256"],
                "sequence": 2,
                "logged_at": runtime.now_utc(),
                "prev_event_sha256": events[-1]["event_sha256"],
                "event_type": "checkpoint",
                "decision": "bogus",
                "artifact": None,
                "blocking_remainder": [],
                "owner_of_remainder": "none",
                "consequence_if_handoff_now": "",
                "next_minimum_work": "",
                "evidence_refs": [],
                "cost": {},
                "refinement_unit": None,
            }
            invalid["event_sha256"] = runtime.event_digest(invalid)
            events.append(invalid)
            trace_path.write_text("\n".join(json.dumps(event, ensure_ascii=False, sort_keys=True) for event in events) + "\n", encoding="utf-8")
            runtime.write_derived_state(runtime_root, "run-test", activation, events)
            report = json.loads(self.run_cli(root, "validate", "--activation-id", "run-test", expected=1).stdout)
            self.assertFalse(report["valid"])
            self.assertTrue(any("decision is invalid" in item for item in report["runs"][0]["findings"]))

    def test_refine_requires_one_parent_bound_refinement_unit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "p1.md"
            artifact.write_text("parent-v1\n", encoding="utf-8")
            self.enable(root)
            missing_parent = self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--blocking-remainder",
                "review validity is unresolved",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "P2 would invent review validity",
                "--next-minimum-work",
                "decide review validity",
                "--unit-scope",
                "review validity and its direct completion dependency",
                "--completion-criterion",
                "one canonical review-validity rule exists",
                expected=2,
            )
            self.assertIn("bound Parent Artifact", missing_parent.stderr)
            multiple = self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--artifact",
                "p1.md",
                "--blocking-remainder",
                "review validity is unresolved",
                "--blocking-remainder",
                "another independent policy is unresolved",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "downstream would invent policy",
                "--next-minimum-work",
                "decide both",
                "--unit-scope",
                "review validity",
                "--completion-criterion",
                "rule exists",
                expected=2,
            )
            self.assertIn("exactly one concrete blocking remainder", multiple.stderr)
            opened = json.loads(self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--artifact",
                "p1.md",
                "--blocking-remainder",
                "review validity is unresolved",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "P2 would invent review validity",
                "--next-minimum-work",
                "decide review validity",
                "--unit-kind",
                "semantic_decision",
                "--unit-scope",
                "review validity and its direct completion dependency",
                "--completion-criterion",
                "one canonical review-validity rule exists",
            ).stdout)
            self.assertEqual(opened["refinement_unit_id"], "RU-0001")
            bundle = json.loads(Path(opened["bundle"]).read_text(encoding="utf-8"))
            unit = bundle["events"][-1]["refinement_unit"]
            self.assertEqual(unit["question"], "review validity is unresolved")
            self.assertEqual(unit["parent_artifact"]["ref"], "p1.md")

    def test_parent_cannot_change_before_refine_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "p1.md"
            artifact.write_text("parent-v1\n", encoding="utf-8")
            self.enable(root)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--artifact",
                "p1.md",
                "--blocking-remainder",
                "review validity is unresolved",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "P2 would invent review validity",
                "--next-minimum-work",
                "decide review validity",
                "--unit-scope",
                "review validity only",
                "--completion-criterion",
                "canonical review-validity rule exists",
            )
            artifact.write_text("whole parent rewritten too early\n", encoding="utf-8")
            work = self.run_cli(
                root,
                "work",
                "--work-kind",
                "design_decision",
                "--changed-scope",
                "review validity",
                expected=2,
            )
            self.assertIn("parent changed before Refine Result", work.stderr)
            result = self.run_cli(
                root,
                "refine-result",
                "--result-status",
                "resolved",
                "--result-summary",
                "review may complete when no actionable finding exists",
                "--resolved-remainder",
                "review validity is unresolved",
                expected=2,
            )
            self.assertIn("parent changed before Refine Result", result.stderr)

    def test_resolved_unit_must_be_absorbed_before_handoff_and_keeps_parent_lineage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "p1.md"
            artifact.write_text("parent-v1\n", encoding="utf-8")
            self.enable(root)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--artifact",
                "p1.md",
                "--blocking-remainder",
                "review validity is unresolved",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "P2 would invent review validity",
                "--next-minimum-work",
                "decide review validity",
                "--unit-scope",
                "review validity only",
                "--completion-criterion",
                "canonical review-validity rule exists",
            )
            self.run_cli(
                root,
                "refine-result",
                "--result-status",
                "resolved",
                "--result-summary",
                "A review cycle is valid with zero actionable findings when the declared checks completed.",
                "--resolved-remainder",
                "review validity is unresolved",
            )
            premature = self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--artifact",
                "p1.md",
                "--owner-of-remainder",
                "downstream",
                expected=2,
            )
            self.assertIn("record its result/absorb first", premature.stderr)
            artifact.write_text("parent-v2 with review validity rule\n", encoding="utf-8")
            absorbed = json.loads(self.run_cli(
                root,
                "absorb",
                "--absorb-mode",
                "update",
                "--parent-after",
                "p1.md",
                "--absorbed-scope",
                "review validity and direct completion semantics",
            ).stdout)
            self.assertEqual(absorbed["unit_id"], "RU-0001")
            mismatch = self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--artifact-ref",
                "unrelated-parent",
                "--owner-of-remainder",
                "downstream",
                expected=2,
            )
            self.assertIn("latest absorbed Parent Artifact", mismatch.stderr)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--artifact",
                "p1.md",
                "--owner-of-remainder",
                "downstream",
            )
            bundle = json.loads(Path(absorbed["bundle"]).read_text(encoding="utf-8"))
            self.assertEqual(bundle["summary"]["current_parent_artifact"]["ref"], "p1.md")
            self.assertEqual(bundle["summary"]["refine_result_count"], 1)
            self.assertEqual(bundle["summary"]["absorb_count"], 1)

    def test_blocked_refinement_unit_can_exit_only_through_need_input_or_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--artifact-ref",
                "P1@v1",
                "--blocking-remainder",
                "external approval contract is unclear",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "downstream would overclaim approval guarantees",
                "--next-minimum-work",
                "check available approval evidence",
                "--unit-kind",
                "evidence_gap",
                "--unit-scope",
                "approval guarantee evidence",
                "--completion-criterion",
                "evidence either establishes or blocks the guarantee",
            )
            self.run_cli(
                root,
                "refine-result",
                "--result-status",
                "blocked",
                "--result-summary",
                "Available evidence cannot establish the reserved external approval guarantee.",
                "--introduced-remainder",
                "product owner approval contract is required",
            )
            blocked = self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--artifact-ref",
                "P1@v1",
                "--owner-of-remainder",
                "downstream",
                expected=2,
            )
            self.assertIn("blocked refinement unit only permits need_input or stop", blocked.stderr)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "need_input",
                "--blocking-remainder",
                "product owner approval contract is required",
                "--owner-of-remainder",
                "upstream",
                "--consequence-if-handoff-now",
                "downstream would overclaim approval guarantees",
            )
            self.run_cli(root, "finish", "--status", "need_input")

    def test_confirm_absorb_can_close_unit_without_rewriting_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--artifact-ref",
                "knowledge-package@v1",
                "--blocking-remainder",
                "retry guarantee evidence is unresolved",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "consumer may overclaim exactly-once behavior",
                "--next-minimum-work",
                "inspect the admitted retry evidence",
                "--unit-kind",
                "evidence_gap",
                "--unit-scope",
                "retry guarantee evidence only",
                "--completion-criterion",
                "the existing package is either confirmed sufficient or a concrete change is identified",
            )
            self.run_cli(
                root,
                "refine-result",
                "--result-status",
                "resolved",
                "--result-summary",
                "Existing package already states that remote exactly-once behavior is unknown.",
                "--resolved-remainder",
                "retry guarantee evidence is unresolved",
            )
            self.run_cli(
                root,
                "absorb",
                "--absorb-mode",
                "confirm",
                "--absorbed-scope",
                "retry guarantee evidence boundary",
            )
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--artifact-ref",
                "knowledge-package@v1",
                "--owner-of-remainder",
                "downstream",
            )

    def test_confirm_absorb_rejects_a_changed_live_project_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "p1.md"
            artifact.write_text("parent-v1\n", encoding="utf-8")
            self.enable(root)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "refine",
                "--artifact",
                "p1.md",
                "--blocking-remainder",
                "review validity is unresolved",
                "--owner-of-remainder",
                "current",
                "--consequence-if-handoff-now",
                "P2 would invent review validity",
                "--next-minimum-work",
                "decide review validity",
                "--unit-scope",
                "review validity only",
                "--completion-criterion",
                "canonical review-validity rule exists",
            )
            self.run_cli(
                root,
                "refine-result",
                "--result-status",
                "resolved",
                "--result-summary",
                "The existing Parent already states the correct rule.",
                "--resolved-remainder",
                "review validity is unresolved",
            )
            artifact.write_text("parent changed after result\n", encoding="utf-8")
            rejected = self.run_cli(
                root,
                "absorb",
                "--absorb-mode",
                "confirm",
                "--absorbed-scope",
                "review validity",
                expected=2,
            )
            self.assertIn("live Parent Artifact to remain unchanged", rejected.stderr)

    def test_persisted_contract_rejects_unknown_activation_and_event_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.enable(root)
            runtime = load_runtime_module()
            runtime_root = runtime.runtime_root(root)
            run = runtime_root / "runs" / "run-test"
            activation_path = run / "activation.json"
            activation = json.loads(activation_path.read_text(encoding="utf-8"))
            activation["silent_extension"] = "not admitted"
            activation["activation_sha256"] = runtime.activation_digest(activation)
            findings = runtime.validate_activation_shape(activation, "run-test")
            self.assertTrue(any("unknown fields" in finding for finding in findings), findings)

            # Restore the canonical activation and create a valid handoff event.
            activation.pop("silent_extension")
            activation["activation_sha256"] = runtime.activation_digest(activation)
            activation_path.write_text(json.dumps(activation, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            active_path = runtime_root / "active.json"
            active = json.loads(active_path.read_text(encoding="utf-8"))
            active["activation_sha256"] = activation["activation_sha256"]
            active_path.write_text(json.dumps(active, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            trace_path = run / "trace.jsonl"
            events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
            events[0]["activation_sha256"] = activation["activation_sha256"]
            events[0]["event_sha256"] = runtime.event_digest(events[0])
            trace_path.write_text(json.dumps(events[0], ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            runtime.write_derived_state(runtime_root, "run-test", activation, events)
            self.run_cli(
                root,
                "checkpoint",
                "--decision",
                "handoff",
                "--owner-of-remainder",
                "downstream",
                "--artifact-ref",
                "P1@v1",
            )
            events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
            events[-1]["silent_extension"] = "not admitted"
            events[-1]["event_sha256"] = runtime.event_digest(events[-1])
            trace_path.write_text("\n".join(json.dumps(event, ensure_ascii=False, sort_keys=True) for event in events) + "\n", encoding="utf-8")
            runtime.write_derived_state(runtime_root, "run-test", activation, events)
            report = json.loads(self.run_cli(root, "validate", "--activation-id", "run-test", expected=1).stdout)
            self.assertTrue(any("unknown fields" in item for item in report["runs"][0]["findings"]), report)

    def test_runtime_directory_cannot_escape_project_root(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--project-root",
                    str(root),
                    "--runtime-dir",
                    str(Path(outside_tmp) / "trace"),
                    "status",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            self.assertIn("must stay inside project root", result.stderr)

    def test_trace_schema_is_shipped_as_observable_not_semantic_contract(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "mindthus.wae-loop-trace.v0.3")
        self.assertIn("does not represent private reasoning", schema["description"])
        self.assertIn("checkpoint", schema["$defs"])
        self.assertIn("refinementUnit", schema["$defs"])
        self.assertIn("refineResult", schema["$defs"])
        self.assertIn("absorb", schema["$defs"])
        self.assertIn("outcome", schema["$defs"])

    def test_release_skill_pack_carries_loop_runtime_and_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mindthus-loop-pack"
            result = subprocess.run(
                [sys.executable, str(REPO / "scripts" / "build-release-pack.py"), "--out", str(out), "--package", "skills"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            roots = (
                out / "codex" / "skills" / "mindthus" / "wae",
                out / "claude-code" / "skills" / "wae",
                out / "opencode" / ".opencode" / "skills" / "mindthus" / "wae",
            )
            for root in roots:
                self.assertTrue((root / "scripts" / "delegation_loop.py").is_file(), root)
                self.assertTrue((root / "resources" / "delegation-loop.md").is_file(), root)
                self.assertTrue((root / "resources" / "wae-loop-trace.schema.json").is_file(), root)


if __name__ == "__main__":
    unittest.main()
