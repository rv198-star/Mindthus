import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "sra" / "scripts"
sys.path.insert(0, str(SCRIPTS.resolve()))

from prepare_sra_run import prepare
from record_sra_judgment import record_challenge, record_coverage, record_situated
from render_sra_decision import render
from sra_runtime import load_json, repair_run, run_check
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

    def test_fresh_prepared_run_checks_cleanly(self):
        run_dir = self.prepare_run()
        report = run_check(run_dir)
        self.assertEqual(report["status"], "ok", report)

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
