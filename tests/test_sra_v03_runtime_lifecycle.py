import copy
import json
import os
import stat
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "sra" / "scripts"
sys.path.insert(0, str(SCRIPTS.resolve()))

from prepare_sra_run import prepare
from record_sra_judgment import record_challenge, record_coverage, record_situated
from render_sra_decision import render
from sra_runtime import (
    SraRuntimeError,
    expected_runtime_event_id,
    load_json,
    repair_run,
    run_check,
)
from tests.test_sra_v03_runtime_contract import (
    challenge_from_situated,
    input_data,
    situated_judgment,
)


class SraV03RuntimeLifecycleTests(unittest.TestCase):
    def prepare_run(self, data: dict | None = None) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        payload = copy.deepcopy(data if data is not None else input_data())
        input_path = root / "input.json"
        input_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        run_dir = root / "run"
        prepare(input_path, run_dir)
        return run_dir

    def test_dependency_block_and_valid_dual_view_replay(self):
        data = input_data()
        data["candidates"][1]["depends_on"] = ["page-polish"]
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        judgment = situated_judgment(packet)
        judgment["dependency_resolutions"] = [{
            "dependent_id": "payment-validation", "prerequisite_id": "page-polish",
            "status": "unknown", "evidence_refs": [], "reason": "Missing prerequisite evidence.",
        }]
        before = {str(p.relative_to(run_dir)): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}
        with self.assertRaises(SraRuntimeError):
            record_situated(run_dir, judgment, carrier="packet_bound", receipt_path=None)
        self.assertEqual(before, {str(p.relative_to(run_dir)): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()})
        judgment["dependency_resolutions"][0].update(status="satisfied", evidence_refs=["E-page"])
        state = load_json(run_dir / "run.json")
        challenge = challenge_from_situated(load_json(run_dir / "challenge-packet.json"), judgment, state["challenge_map"])
        record_challenge(run_dir, challenge, carrier="packet_bound", receipt_path=None)
        record_situated(run_dir, judgment, carrier="packet_bound", receipt_path=None)
        self.assertEqual(run_check(run_dir)["status"], "ok")
        self.assertEqual(load_json(run_dir / "run.json")["statuses"]["finalization"], "finalized")
        self.assertTrue(repair_run(run_dir)["repaired"])

    def test_invalid_judgment_structure_leaves_run_byte_identical(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        before = {str(p.relative_to(run_dir)): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}
        for field in ("unrecognized_authorization_override", "next_tranche"):
            with self.subTest(field=field):
                judgment = situated_judgment(packet)
                if field == "next_tranche":
                    judgment[field]["undeclared"] = "value"
                else:
                    judgment[field] = True
                with self.assertRaises(SraRuntimeError):
                    record_situated(run_dir, judgment, carrier="packet_bound", receipt_path=None)
                after = {str(p.relative_to(run_dir)): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}
                self.assertEqual(after, before)

    def test_fresh_prepared_run_checks_cleanly(self):
        run_dir = self.prepare_run()
        report = run_check(run_dir)
        self.assertEqual(report["status"], "ok", report)

    def test_run_prepared_trace_carries_complete_input_anchor(self):
        run_dir = self.prepare_run()
        event = json.loads(
            (run_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines()[0]
        )
        for field in (
            "raw_input_hash",
            "context_admission_hash",
            "base_packet_hash",
            "coverage_packet_hash",
            "challenge_packet_hash",
            "situated_packet_hash",
        ):
            self.assertIn(field, event["payload"])
            self.assertTrue(event["payload"][field])

    def test_prompt_tamper_is_detected(self):
        run_dir = self.prepare_run()
        path = run_dir / "challenge-agent-prompt.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nChoose C01.\n", encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any(item["code"] == "challenge-prompt" for item in report["findings"]))

    def test_dispatch_tamper_is_detected(self):
        run_dir = self.prepare_run()
        path = run_dir / "challenge-subagent-dispatch.json"
        value = load_json(path)
        value["read_only"] = False
        path.write_text(json.dumps(value), encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any(item["code"] == "challenge-dispatch" for item in report["findings"]))

    def test_command_tamper_is_detected(self):
        run_dir = self.prepare_run()
        path = run_dir / "situated-codex-command.sh"
        path.write_text("#!/usr/bin/env bash\necho bypass\n", encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any(item["code"] == "situated-command" for item in report["findings"]))

    def test_run_plan_tamper_is_detected(self):
        run_dir = self.prepare_run()
        path = run_dir / "run.json"
        state = load_json(path)
        state["view_plan"] = "situated_only"
        path.write_text(json.dumps(state), encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any(item["code"] == "view-plan-rebuild" for item in report["findings"]))

    def test_malformed_state_fails_closed_without_exception(self):
        run_dir = self.prepare_run()
        path = run_dir / "run.json"
        state = load_json(path)
        state["carriers"] = ["bad"]
        path.write_text(json.dumps(state), encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["findings"])

    def test_situated_only_allocate_finalizes_and_checks(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        record_situated(
            run_dir,
            situated_judgment(packet),
            carrier="packet_bound",
            receipt_path=None,
        )
        state = load_json(run_dir / "run.json")
        self.assertEqual(state["statuses"]["finalization"], "finalized")
        self.assertEqual(run_check(run_dir)["status"], "ok")

    def test_situated_only_blocked_remains_blocked(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        judgment = situated_judgment(packet)
        judgment["allocation_outcome"] = "blocked"
        judgment["bundle_decision"] = {
            "status": "not_applicable",
            "bundle_assessments": [],
            "selected_bundle_id": "none",
        }
        judgment["allocation_ledger"] = [
            {**item, "posture": "candidate", "current_allocations": []}
            for item in judgment["allocation_ledger"]
        ]
        judgment["next_tranche"] = {
            "target_id": "none",
            "resource_allocations": [],
            "window": "Current release window.",
            "completion_signal": "Missing evidence is supplied.",
            "start_condition": "",
            "reason": "A load-bearing fact is missing.",
        }
        judgment["investment_ceiling"] = []
        judgment["reserve"]["status"] = "none"
        judgment["reserve"]["resource_allocations"] = []
        judgment["missing_information"] = ["A load-bearing fact is missing."]
        record_situated(
            run_dir,
            judgment,
            carrier="packet_bound",
            receipt_path=None,
        )
        state = load_json(run_dir / "run.json")
        self.assertEqual(state["statuses"]["finalization"], "blocked")
        self.assertEqual(run_check(run_dir)["status"], "ok")

    def test_dual_views_agree_and_finalize(self):
        run_dir = self.prepare_run()
        state = load_json(run_dir / "run.json")
        situated_packet = load_json(run_dir / "situated-packet.json")
        challenge_packet = load_json(run_dir / "challenge-packet.json")
        situated = situated_judgment(situated_packet)
        challenge = challenge_from_situated(
            challenge_packet, situated, state["challenge_map"]
        )
        record_challenge(
            run_dir, challenge, carrier="packet_bound", receipt_path=None
        )
        record_situated(
            run_dir, situated, carrier="packet_bound", receipt_path=None
        )
        state = load_json(run_dir / "run.json")
        self.assertEqual(state["statuses"]["comparison"], "agree")
        self.assertEqual(state["statuses"]["finalization"], "finalized")
        self.assertEqual(run_check(run_dir)["status"], "ok")

    def test_typed_conflict_creates_reconciliation_surface(self):
        run_dir = self.prepare_run()
        state = load_json(run_dir / "run.json")
        situated_packet = load_json(run_dir / "situated-packet.json")
        challenge_packet = load_json(run_dir / "challenge-packet.json")
        situated = situated_judgment(situated_packet)
        challenge = challenge_from_situated(
            challenge_packet, situated, state["challenge_map"]
        )
        challenge["next_tranche"]["resource_allocations"][0]["quantity"]["amount"] = 0.1
        challenge["investment_ceiling"][0]["quantity"]["amount"] = 0.1
        record_challenge(
            run_dir, challenge, carrier="packet_bound", receipt_path=None
        )
        record_situated(
            run_dir, situated, carrier="packet_bound", receipt_path=None
        )
        state = load_json(run_dir / "run.json")
        self.assertEqual(state["statuses"]["comparison"], "conflict")
        self.assertEqual(state["statuses"]["reconciliation"], "pending")
        self.assertTrue((run_dir / "reconciliation-agent-prompt.md").is_file())
        self.assertEqual(run_check(run_dir)["status"], "ok")

    def test_coverage_blocked_final_copy_tamper_is_detected(self):
        data = input_data()
        data["coverage_review"] = "required"
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "coverage-packet.json")
        judgment = {
            "schema_version": "sra.coverage-judgment.v0.3",
            "stage": "coverage",
            "packet_hash": packet["packet_hash"],
            "outcome": "packet_incomplete",
            "missing_candidate_classes": ["A compliance candidate is missing."],
            "missing_evidence": [],
            "classification_challenges": [],
            "warnings": [],
            "evidence_refs": [],
            "assumption_refs": [],
            "claim_ceiling": "Coverage review only.",
        }
        record_coverage(
            run_dir, judgment, carrier="packet_bound", receipt_path=None
        )
        path = run_dir / "final-decision.json"
        final = load_json(path)
        final["decision"]["allocation_outcome"] = "allocate"
        path.write_text(json.dumps(final), encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any(item["code"] == "final-rebuild" for item in report["findings"]))

    def test_trace_payload_tamper_is_detected(self):
        run_dir = self.prepare_run()
        path = run_dir / "trace.jsonl"
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        events[0]["payload"]["view_plan"] = "situated_only"
        path.write_text(
            "\n".join(json.dumps(item) for item in events) + "\n",
            encoding="utf-8",
        )
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(
            any(item["code"] in {"trace-event-id", "trace-payload"} for item in report["findings"])
        )

    def test_repair_rebuilds_tampered_derived_surfaces(self):
        run_dir = self.prepare_run()
        prompt_path = run_dir / "challenge-agent-prompt.md"
        prompt_path.write_text("tampered", encoding="utf-8")
        state_path = run_dir / "run.json"
        state = load_json(state_path)
        state["warnings"] = ["tampered"]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        result = repair_run(run_dir)
        self.assertTrue(result["repaired"], result)
        self.assertEqual(run_check(run_dir)["status"], "ok")
        self.assertNotEqual(prompt_path.read_text(encoding="utf-8"), "tampered")

    def test_repair_preserves_recorded_agentic_judgment(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        judgment = situated_judgment(packet)
        record_situated(
            run_dir, judgment, carrier="packet_bound", receipt_path=None
        )
        judgment_path = run_dir / "judgments" / "situated.json"
        before = judgment_path.read_bytes()
        final_path = run_dir / "final-decision.json"
        final_path.write_text("{}", encoding="utf-8")
        result = repair_run(run_dir)
        self.assertTrue(result["repaired"], result)
        self.assertEqual(judgment_path.read_bytes(), before)
        self.assertEqual(run_check(run_dir)["status"], "ok")

    def test_blocked_render_never_says_immediate_start(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        judgment = situated_judgment(packet)
        judgment["allocation_outcome"] = "blocked"
        judgment["allocation_ledger"] = [
            {**item, "posture": "candidate", "current_allocations": []}
            for item in judgment["allocation_ledger"]
        ]
        judgment["next_tranche"] = {
            "target_id": "none",
            "resource_allocations": [],
            "window": "Current release window.",
            "completion_signal": "Missing evidence is supplied.",
            "start_condition": "",
            "reason": "A load-bearing fact is missing.",
        }
        judgment["investment_ceiling"] = []
        judgment["missing_information"] = ["A load-bearing fact is missing."]
        record_situated(
            run_dir, judgment, carrier="packet_bound", receipt_path=None
        )
        _, text = render(run_dir, "zh")
        self.assertIn("当前未授权启动", text)
        self.assertNotIn("可立即开始", text)

    def test_allocate_render_preserves_typed_resource_quantity(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        record_situated(
            run_dir,
            situated_judgment(packet),
            carrier="packet_bound",
            receipt_path=None,
        )
        _, text = render(run_dir, "zh")
        self.assertIn("0.9 engineer-day", text)
        self.assertIn("可立即开始", text)

    def test_repair_refuses_changed_raw_input_anchor(self):
        run_dir = self.prepare_run()
        raw_path = run_dir / "raw-input.json"
        raw = load_json(raw_path)
        raw["allocation_frame"]["parent_objective"] = (
            "A different still-valid objective."
        )
        raw_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(run_check(run_dir)["status"], "blocked")
        with self.assertRaises(SraRuntimeError):
            repair_run(run_dir)

    def test_repair_refuses_changed_agentic_judgment_anchor(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        record_situated(
            run_dir,
            situated_judgment(packet),
            carrier="packet_bound",
            receipt_path=None,
        )
        judgment_path = run_dir / "judgments" / "situated.json"
        judgment = load_json(judgment_path)
        judgment["claim_ceiling"] = (
            "A different but still shape-valid claim ceiling."
        )
        judgment_path.write_text(
            json.dumps(judgment, ensure_ascii=False), encoding="utf-8"
        )
        self.assertEqual(run_check(run_dir)["status"], "blocked")
        with self.assertRaises(SraRuntimeError):
            repair_run(run_dir)

    def test_repair_uses_trace_over_conflicting_carrier_cache(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        record_situated(
            run_dir,
            situated_judgment(packet),
            carrier="packet_bound",
            receipt_path=None,
        )
        state_path = run_dir / "run.json"
        state = load_json(state_path)
        state["carriers"]["situated"] = "fresh_subagent"
        state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(run_check(run_dir)["status"], "blocked")
        result = repair_run(run_dir)
        self.assertTrue(result["repaired"], result)
        repaired_state = load_json(state_path)
        self.assertEqual(repaired_state["carriers"]["situated"], "packet_bound")
        self.assertEqual(run_check(run_dir)["status"], "ok")

    def test_receipt_path_is_stage_bound_inside_run_directory(self):
        with tempfile.TemporaryDirectory() as receipt_tmp:
            receipt_source = Path(receipt_tmp) / "source-receipt.json"
            receipt_source.write_text('{"carrier":"fresh"}', encoding="utf-8")
            data = input_data()
            data["contamination_signals"] = []
            run_dir = self.prepare_run(data)
            packet = load_json(run_dir / "situated-packet.json")
            record_situated(
                run_dir,
                situated_judgment(packet),
                carrier="fresh_subagent",
                receipt_path=str(receipt_source),
            )
            state_path = run_dir / "run.json"
            final_path = run_dir / "final-decision.json"
            state = load_json(state_path)
            final = load_json(final_path)
            state["carrier_receipts"]["situated"]["stored_path"] = str(
                receipt_source
            )
            final["carrier_receipts"]["situated"]["stored_path"] = str(
                receipt_source
            )
            state_path.write_text(
                json.dumps(state, ensure_ascii=False), encoding="utf-8"
            )
            final_path.write_text(
                json.dumps(final, ensure_ascii=False), encoding="utf-8"
            )
            report = run_check(run_dir)
            self.assertEqual(report["status"], "blocked", report)
            self.assertTrue(
                any(item["code"] == "receipt-path" for item in report["findings"])
            )

    def test_trace_timestamp_requires_parseable_utc_time(self):
        run_dir = self.prepare_run()
        trace_path = run_dir / "trace.jsonl"
        event = json.loads(trace_path.read_text(encoding="utf-8").strip())
        event["recorded_at"] = "not-a-time"
        event["event_id"] = expected_runtime_event_id(event)
        trace_path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(item["code"] == "trace-time" for item in report["findings"])
        )

    def _finalize_with_receipt(self) -> tuple[Path, Path]:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        data = input_data()
        data["contamination_signals"] = []
        input_path = root / "input.json"
        input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        run_dir = root / "run"
        prepare(input_path, run_dir)
        receipt = root / "receipt.json"
        receipt.write_text('{"carrier":"fresh"}', encoding="utf-8")
        packet = load_json(run_dir / "situated-packet.json")
        record_situated(
            run_dir,
            situated_judgment(packet),
            carrier="fresh_subagent",
            receipt_path=str(receipt),
        )
        return root, run_dir

    def test_receipt_boundary_metadata_is_canonical(self):
        _, run_dir = self._finalize_with_receipt()
        state_path = run_dir / "run.json"
        final_path = run_dir / "final-decision.json"
        state = load_json(state_path)
        final = load_json(final_path)
        state["carrier_receipts"]["situated"]["boundary"] = (
            "This proves the model had no hidden host context."
        )
        final["carrier_receipts"]["situated"]["boundary"] = (
            "This proves the model had no hidden host context."
        )
        state_path.write_text(json.dumps(state), encoding="utf-8")
        final_path.write_text(json.dumps(final), encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(item["code"] == "receipt-boundary" for item in report["findings"])
        )

    def test_receipt_file_cannot_be_symlinked_outside_run(self):
        root, run_dir = self._finalize_with_receipt()
        stored = run_dir / "receipts" / "situated.receipt"
        external = root / "external-receipt.json"
        external.write_bytes(stored.read_bytes())
        stored.unlink()
        stored.symlink_to(external)
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(item["code"] == "receipt-path" for item in report["findings"])
        )

    def test_run_claim_ceiling_is_reconstructed(self):
        run_dir = self.prepare_run()
        state_path = run_dir / "run.json"
        state = load_json(state_path)
        state["claim_ceiling"] = "Workflow proves the allocation is correct."
        state_path.write_text(json.dumps(state), encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(
                item["code"] == "claim-ceiling-rebuild"
                for item in report["findings"]
            )
        )

    def test_unknown_run_state_fields_are_rejected(self):
        run_dir = self.prepare_run()
        state_path = run_dir / "run.json"
        state = load_json(state_path)
        state["allocation_authorized"] = True
        state_path.write_text(json.dumps(state), encoding="utf-8")
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(item["code"] == "run-state-shape" for item in report["findings"])
        )

    def test_prepared_run_keeps_agent_output_directory_available(self):
        run_dir = self.prepare_run()
        judgments = run_dir / "judgments"
        judgments.rmdir()
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(item["code"] == "output-directory" for item in report["findings"])
        )
        result = repair_run(run_dir)
        self.assertTrue(result["repaired"], result)
        self.assertTrue(judgments.is_dir())

    def test_repair_requires_a_prepared_input_anchor(self):
        run_dir = self.prepare_run()
        (run_dir / "run.json").unlink()
        (run_dir / "trace.jsonl").unlink()
        raw_path = run_dir / "raw-input.json"
        raw = load_json(raw_path)
        raw["allocation_frame"]["parent_objective"] = "A replacement objective."
        raw_path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(SraRuntimeError):
            repair_run(run_dir)

    def test_repair_rejects_incomplete_state_anchor_when_trace_is_missing(self):
        run_dir = self.prepare_run()
        (run_dir / "trace.jsonl").unlink()
        state_path = run_dir / "run.json"
        state = load_json(state_path)
        for field in (
            "raw_input_hash",
            "context_admission_hash",
            "base_packet_hash",
            "coverage_packet_hash",
            "challenge_packet_hash",
            "situated_packet_hash",
        ):
            state.pop(field, None)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        raw_path = run_dir / "raw-input.json"
        raw = load_json(raw_path)
        raw["allocation_frame"]["parent_objective"] = "A replacement objective."
        raw_path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(SraRuntimeError, "prepared-input anchor"):
            repair_run(run_dir)

    def test_repair_accepts_complete_state_anchor_when_trace_is_missing(self):
        run_dir = self.prepare_run()
        (run_dir / "trace.jsonl").unlink()
        prompt_path = run_dir / "situated-agent-prompt.md"
        prompt_path.write_text("tampered", encoding="utf-8")
        result = repair_run(run_dir)
        self.assertTrue(result["repaired"], result)
        self.assertEqual(run_check(run_dir)["status"], "ok")
        self.assertNotEqual(prompt_path.read_text(encoding="utf-8"), "tampered")

    def test_repair_accepts_complete_trace_anchor_when_state_is_missing(self):
        run_dir = self.prepare_run()
        (run_dir / "run.json").unlink()
        prompt_path = run_dir / "situated-agent-prompt.md"
        prompt_path.write_text("tampered", encoding="utf-8")
        result = repair_run(run_dir)
        self.assertTrue(result["repaired"], result)
        self.assertEqual(run_check(run_dir)["status"], "ok")
        self.assertNotEqual(prompt_path.read_text(encoding="utf-8"), "tampered")

    def test_repair_rejects_changed_raw_input_with_state_only_anchor(self):
        run_dir = self.prepare_run()
        (run_dir / "trace.jsonl").unlink()
        raw_path = run_dir / "raw-input.json"
        raw = load_json(raw_path)
        raw["allocation_frame"]["parent_objective"] = "A replacement objective."
        raw_path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(SraRuntimeError, "run state raw_input_hash"):
            repair_run(run_dir)

    def test_raw_input_must_be_regular_in_run_file(self):
        run_dir = self.prepare_run()
        raw_path = run_dir / "raw-input.json"
        external = run_dir.parent / "raw-external.json"
        external.write_bytes(raw_path.read_bytes())
        raw_path.unlink()
        raw_path.symlink_to(external)
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(item["code"] == "authoritative-path" for item in report["findings"])
        )
        with self.assertRaises(SraRuntimeError):
            repair_run(run_dir)

    def test_recorded_judgment_must_be_regular_in_run_file(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        record_situated(
            run_dir,
            situated_judgment(packet),
            carrier="packet_bound",
            receipt_path=None,
        )
        judgment_path = run_dir / "judgments" / "situated.json"
        external = run_dir.parent / "situated-external.json"
        external.write_bytes(judgment_path.read_bytes())
        judgment_path.unlink()
        judgment_path.symlink_to(external)
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(item["code"] == "authoritative-path" for item in report["findings"])
        )
        with self.assertRaises(SraRuntimeError):
            repair_run(run_dir)

    def test_repair_refuses_symlinked_judgments_directory(self):
        run_dir = self.prepare_run()
        judgments = run_dir / "judgments"
        judgments.rmdir()
        external = run_dir.parent / "external-judgments"
        external.mkdir()
        judgments.symlink_to(external, target_is_directory=True)
        with self.assertRaises(SraRuntimeError):
            repair_run(run_dir)
        self.assertEqual(list(external.iterdir()), [])

    def test_generated_command_must_remain_executable(self):
        run_dir = self.prepare_run()
        command_path = run_dir / "situated-codex-command.sh"
        command_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(
                item["code"] == "situated-command-mode"
                for item in report["findings"]
            )
        )
        repaired = repair_run(run_dir)
        self.assertTrue(repaired["repaired"], repaired)
        self.assertTrue(os.access(command_path, os.X_OK))

    def test_trace_timestamps_are_nondecreasing(self):
        data = input_data()
        data["contamination_signals"] = []
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        record_situated(
            run_dir,
            situated_judgment(packet),
            carrier="packet_bound",
            receipt_path=None,
        )
        trace_path = run_dir / "trace.jsonl"
        events = [
            json.loads(line)
            for line in trace_path.read_text(encoding="utf-8").splitlines()
        ]
        first = datetime.fromisoformat(events[0]["recorded_at"])
        events[-1]["recorded_at"] = (
            first - timedelta(seconds=1)
        ).astimezone(timezone.utc).isoformat()
        events[-1]["event_id"] = expected_runtime_event_id(events[-1])
        trace_path.write_text(
            "\n".join(json.dumps(event) for event in events) + "\n",
            encoding="utf-8",
        )
        report = run_check(run_dir)
        self.assertEqual(report["status"], "blocked", report)
        self.assertTrue(
            any(item["code"] == "trace-time" for item in report["findings"])
        )

    def test_governed_override_remains_visible_in_terminal_output(self):
        data = input_data()
        data["contamination_signals"] = []
        data["escalation_signals"] = ["major_commitment"]
        data["context_items"].append(
            {
                "context_id": "AUTH-release",
                "kind": "authority_decision",
                "authority_holder": "Release owner",
                "authority_scope": "May approve one run's analysis-depth downgrade.",
                "authority_expiry": "End of this run.",
                "statement": "Release owner authorizes a bounded Lite downgrade.",
                "challenge_projection": "The decision owner authorizes a bounded analysis-depth downgrade.",
                "projection_basis": "Preserves authority without candidate identity.",
                "source": "current authority record",
                "decision_relevance": "Controls downgrade authority.",
                "requested_disposition": "admit",
                "candidate_ids": [],
                "evidence_refs": [],
                "assumption_refs": [],
            }
        )
        data["overrides"]["mode"] = {
            "override_reason": "Only one reversible tranche is authorized.",
            "approved_by": "Release owner",
            "authority_ref": "AUTH-release",
            "risk_acceptance_scope": "This run only.",
            "expiry": "End of this run.",
        }
        run_dir = self.prepare_run(data)
        packet = load_json(run_dir / "situated-packet.json")
        record_situated(
            run_dir,
            situated_judgment(packet),
            carrier="packet_bound",
            receipt_path=None,
        )
        final = load_json(run_dir / "final-decision.json")
        self.assertIn("mode", final["governance_overrides"])
        _, text = render(run_dir, "zh")
        self.assertIn("治理覆盖", text)
        self.assertIn("Release owner", text)


if __name__ == "__main__":
    unittest.main()
