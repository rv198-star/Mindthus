"""Cost-proportionate SRA keeps the existing allocation and integrity guarantees."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/sra/scripts"))
from draft_sra_context import draft_context, write_draft
from prepare_sra_run import prepare
from record_sra_judgment import record_situated, record_challenge, record_reconciliation
from sra_domain import RECONCILIATION_JUDGMENT_SCHEMA, INPUT_SCHEMA, EXTENDED_INPUT_SCHEMA
from render_sra_decision import render
from rerank_sra_context import rerank_draft
from sra_criteria import CATALOG_VERSION, criterion_hash, completion_reference
from sra_io import load_json, SraRuntimeError
from sra_policy import PROPORTIONATE_POLICY, GOAL_GUIDANCE
from sra_runtime import build_packets, validate_context_input, validate_situated_judgment, run_check, repair_run, compare_views
from tests.test_sra_v03_runtime_contract import input_data, situated_judgment, challenge_from_situated


def proportionate_input(mode="full"):
    data = input_data(mode=mode)
    data["schema_version"] = EXTENDED_INPUT_SCHEMA
    data["contamination_signals"] = []
    data["context_items"] = [c for c in data["context_items"] if c["kind"] == "user_constraint"]
    data["execution_policy"] = {
        "version": PROPORTIONATE_POLICY,
        "risk_level": "ordinary_reversible",
        "assessment_basis": "Current request and reversible validation-only tranche; no production mutation.",
    }
    return data


def criteria_input():
    data = proportionate_input("lite")
    data["contamination_signals"] = ["prior_agent_conclusion"]
    item = {"criterion_id": "CR-01", "revision": "1", "subject": "Payment path",
            "observable_result": "A reproducible validation result.",
            "evidence_requirement": "A retained test report records the result.",
            "window": "Current release window.", "source": "Current acceptance checklist"}
    item["content_hash"] = criterion_hash(item)
    data["completion_criteria"] = {"version": CATALOG_VERSION, "items": [item]}
    data["candidates"][1]["completion_criterion_ids"] = ["CR-01"]
    return data


def referenced_judgment(packet):
    judgment = situated_judgment(packet)
    judgment["next_tranche"].pop("completion_signal")
    judgment["next_tranche"]["completion_criterion_ref"] = completion_reference(packet, "CR-01")
    return judgment


class SraProportionateTests(unittest.TestCase):
    def prepare_run(self, data):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        source = root / "input.json"
        source.write_text(json.dumps(data), encoding="utf-8")
        run = root / "run"
        prepare(source, run)
        return run

    def test_depth_and_calibration_matrix(self):
        for mode in ("lite", "full"):
            for risk in ("ordinary_reversible", "consequential", "unknown"):
                for contaminated in (False, True):
                    with self.subTest(mode=mode, risk=risk, contaminated=contaminated):
                        data = proportionate_input(mode)
                        data["execution_policy"]["risk_level"] = risk
                        if contaminated:
                            data["contamination_signals"] = ["sunk_cost_narrative"]
                        built = build_packets(data)
                        self.assertEqual(built["mode"], mode)
                        self.assertEqual(built["view_plan"], "situated_only" if risk == "ordinary_reversible" and not contaminated else "dual_view")

    def test_risk_signals_and_existing_context_cannot_be_washed_by_low_risk_label(self):
        variants = []
        for signal in ("major_commitment", "irreversible_exposure", "material_switching_cost"):
            data = proportionate_input()
            data["escalation_signals"].append(signal)
            variants.append(data)
        data = proportionate_input()
        data["context_items"].append(input_data()["context_items"][-1])
        variants.append(data)
        data = proportionate_input()
        data["coverage_signals"] = ["high_impact"]
        variants.append(data)
        for data in variants:
            with self.subTest(data=data):
                self.assertEqual(build_packets(data)["view_plan"], "dual_view")
                data["view_plan"] = "situated_only"
                self.assertTrue(any("overrides.view_plan" in f for f in validate_context_input(data)))

    def test_legacy_full_stays_dual_and_policy_requires_explicit_assessment(self):
        data = proportionate_input()
        del data["execution_policy"]
        data["schema_version"] = INPUT_SCHEMA
        built = build_packets(data)
        self.assertEqual(built["view_plan"], "dual_view")
        self.assertNotIn("execution_policy", built["base_packet"])
        for policy in (None, {}, {"version": "invented"}, {"version": PROPORTIONATE_POLICY, "risk_level": "ordinary_reversible", "assessment_basis": ""}):
            with self.subTest(policy=policy):
                data["execution_policy"] = policy
                self.assertTrue(validate_context_input(data))

    def test_new_extensions_require_an_explicit_new_input_version(self):
        data = proportionate_input()
        data["schema_version"] = INPUT_SCHEMA
        self.assertTrue(any("extensions require" in f for f in validate_context_input(data)))
        data["schema_version"] = EXTENDED_INPUT_SCHEMA
        data.pop("execution_policy")
        self.assertTrue(any("execution_policy" in f for f in validate_context_input(data)))
        # Intake preserves explicit legacy input instead of silently migrating it.
        legacy = input_data()
        self.assertEqual(draft_context(legacy)["draft"], legacy)

    def test_single_full_records_and_repairs_without_fake_challenge(self):
        run = self.prepare_run(proportionate_input())
        self.assertFalse((run / "challenge-agent-prompt.md").exists())
        self.assertIn(GOAL_GUIDANCE, (run / "situated-agent-prompt.md").read_text())
        judgment = situated_judgment(load_json(run / "situated-packet.json"))
        record_situated(run, judgment, carrier="packet_bound", receipt_path=None)
        self.assertEqual(run_check(run)["status"], "ok")
        final = load_json(run / "final-decision.json")
        self.assertEqual(final["finalization_status"], "finalized")
        self.assertIsNone(final["challenge_judgment_hash"])
        self.assertEqual(final["observed_context_boundary"], "packet_bound_views_only")
        (run / "situated-agent-prompt.md").write_text("changed", encoding="utf-8")
        self.assertEqual(run_check(run)["status"], "blocked")
        repair_run(run)
        self.assertEqual(run_check(run)["status"], "ok")
        raw = load_json(run / "raw-input.json")
        raw["execution_policy"]["risk_level"] = "consequential"
        (run / "raw-input.json").write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaises(SraRuntimeError):
            repair_run(run)

    def test_draft_is_canonical_no_judgment_and_does_not_invent_missing_semantics(self):
        data = proportionate_input("lite")
        original = copy.deepcopy(data)
        report = draft_context(data)
        self.assertEqual(report["status"], "ready_for_prepare")
        self.assertEqual(report["draft"], original)
        self.assertEqual(data, original)
        self.assertEqual(report["authority"], "draft_only")
        missing = copy.deepcopy(data)
        del missing["candidates"][0]["depends_on"]
        del missing["evidence"][0]["observed_at"]
        del missing["allocation_frame"]["decision_owner"]
        draft = draft_context(missing)
        self.assertEqual(draft["status"], "needs_input")
        self.assertIsNone(draft["draft"]["candidates"][0]["depends_on"])
        self.assertNotIn("decision_owner", draft["draft"]["allocation_frame"])
        self.assertNotIn("observed_at", draft["draft"]["evidence"][0])
        self.assertNotIn("allocation_outcome", draft["draft"])

    def test_criteria_bind_scope_content_window_and_each_view_packet(self):
        data = criteria_input()
        self.assertEqual(validate_context_input(data), [])
        built = build_packets(data)
        packet = built["situated_packet"]
        valid = referenced_judgment(packet)
        self.assertEqual(validate_situated_judgment(valid, packet), [])
        mutations = [
            lambda j: j["next_tranche"]["completion_criterion_ref"].update(content_hash="sha256:" + "0" * 64),
            lambda j: j["next_tranche"]["completion_criterion_ref"].update(packet_hash=built["challenge_packet"]["packet_hash"]),
            lambda j: j["next_tranche"].update(target_id="page-polish"),
            lambda j: j["next_tranche"].update(window="Next year"),
            lambda j: j["next_tranche"].update(completion_signal="Contradictory override"),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(valid)
                mutation(value)
                self.assertTrue(validate_situated_judgment(value, packet))
        data["completion_criteria"]["items"][0]["observable_result"] = "Weaker target"
        self.assertTrue(validate_context_input(data))

    def test_same_criterion_different_reason_agrees_real_resource_change_conflicts(self):
        built = build_packets(criteria_input())
        situated = referenced_judgment(built["situated_packet"])
        challenge = challenge_from_situated(built["challenge_packet"], situated, built["challenge_map"])
        challenge["next_tranche"]["completion_criterion_ref"] = completion_reference(built["challenge_packet"], "CR-01")
        challenge["next_tranche"]["reason"] = "Same intended completion, independently worded rationale."
        def compare():
            return compare_views(run_id=built["base_packet"]["run_id"],
                challenge_packet_hash=built["challenge_packet"]["packet_hash"],
                situated_packet_hash=built["situated_packet"]["packet_hash"],
                challenge_judgment=challenge, situated_judgment=situated, challenge_map=built["challenge_map"], detailed=True)
        self.assertEqual(compare()["status"], "agree")
        challenge["next_tranche"]["resource_allocations"][0]["quantity"]["amount"] = 0.8
        result = compare()
        self.assertEqual(result["status"], "conflict")
        self.assertIn("/next_tranche/resource_allocations/0/quantity/amount", result["conflict_paths"])

    def test_referenced_dual_run_replay_and_readonly_card(self):
        run = self.prepare_run(criteria_input())
        state = load_json(run / "run.json")
        situated = referenced_judgment(load_json(run / "situated-packet.json"))
        packet = load_json(run / "challenge-packet.json")
        challenge = challenge_from_situated(packet, situated, state["challenge_map"])
        challenge["next_tranche"]["completion_criterion_ref"] = completion_reference(packet, "CR-01")
        record_challenge(run, challenge, carrier="packet_bound", receipt_path=None)
        record_situated(run, situated, carrier="packet_bound", receipt_path=None)
        self.assertEqual(run_check(run)["status"], "ok")
        before = {str(p.relative_to(run)): p.read_bytes() for p in run.rglob("*") if p.is_file()}
        for view in ("card", "full"):
            final, text = render(run, "zh", view)
            self.assertNotIn("completion_signal", final["decision"]["next_tranche"])
            self.assertIn("CR-01@1", text)
        self.assertEqual(before, {str(p.relative_to(run)): p.read_bytes() for p in run.rglob("*") if p.is_file()})
        (run / "comparison-report.json").write_text("{}", encoding="utf-8")
        repair_run(run)
        self.assertEqual(run_check(run)["status"], "ok")

    def test_free_text_paraphrase_stays_conservative(self):
        built = build_packets(proportionate_input())
        situated = situated_judgment(built["situated_packet"])
        challenge = challenge_from_situated(built["challenge_packet"], situated, built["challenge_map"])
        challenge["next_tranche"]["completion_signal"] = "Produce a reproducible payment result."
        result = compare_views(run_id="probe", challenge_packet_hash=built["challenge_packet"]["packet_hash"],
            situated_packet_hash=built["situated_packet"]["packet_hash"], challenge_judgment=challenge,
            situated_judgment=situated, challenge_map=built["challenge_map"], detailed=True)
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["conflict_paths"], ["/next_tranche/completion_signal"])

    def test_cards_preserve_no_start_and_target_constraints(self):
        for outcome in ("blocked", "infeasible", "conditional"):
            with self.subTest(outcome=outcome):
                data = proportionate_input("lite")
                run = self.prepare_run(data)
                judgment = situated_judgment(load_json(run / "situated-packet.json"))
                judgment["allocation_outcome"] = outcome
                judgment["next_tranche"].update(target_id="none", resource_allocations=[])
                judgment["investment_ceiling"] = []
                judgment["missing_information"] = ["Current acceptance evidence is missing."]
                record_situated(run, judgment, carrier="packet_bound", receipt_path=None)
                _, text = render(run, "zh", "card")
                self.assertNotIn("可立即开始", text)
                self.assertIn(data["allocation_frame"]["risk_floor"], text)
                self.assertIn(judgment["missing_information"][0], text)

    def test_missing_context_reconciliation_card_never_authorizes_start(self):
        data = proportionate_input("lite")
        data["execution_policy"]["risk_level"] = "unknown"
        run = self.prepare_run(data)
        state = load_json(run / "run.json")
        situated = situated_judgment(load_json(run / "situated-packet.json"))
        challenge = challenge_from_situated(load_json(run / "challenge-packet.json"), situated, state["challenge_map"])
        challenge["next_tranche"]["resource_allocations"][0]["quantity"]["amount"] = 0.8
        record_challenge(run, challenge, carrier="packet_bound", receipt_path=None)
        record_situated(run, situated, carrier="packet_bound", receipt_path=None)
        packet = load_json(run / "reconciliation-packet.json")
        judgment = situated_judgment(packet)
        judgment.update(schema_version=RECONCILIATION_JUDGMENT_SCHEMA, stage="reconciliation", allocation_outcome="request_missing_context")
        judgment["next_tranche"].update(target_id="none", resource_allocations=[])
        judgment["investment_ceiling"] = []
        judgment["missing_information"] = ["Need a current capacity observation."]
        judgment["conflict_resolutions"] = [
            {"field": item["field"], "resolution": "Await current evidence.", "evidence_refs": [], "assumption_refs": [], "state_refs": []}
            for item in packet["conflict_fields"]
        ]
        record_reconciliation(run, judgment, carrier="packet_bound", receipt_path=None)
        _, text = render(run, "zh", "card")
        self.assertNotIn("可立即开始", text)
        self.assertIn("需补信息", text)
        self.assertEqual(run_check(run)["status"], "ok")

    def test_rerank_uses_refreshed_context_without_inheriting_parent_judgment(self):
        parent = self.prepare_run(proportionate_input("lite"))
        judgment = situated_judgment(load_json(parent / "situated-packet.json"))
        record_situated(parent, judgment, carrier="packet_bound", receipt_path=None)
        before = {str(p.relative_to(parent)): p.read_bytes() for p in parent.rglob("*") if p.is_file()}
        refreshed = proportionate_input("lite")
        refreshed.pop("run_id")
        refreshed["allocation_frame"]["resource_pools"][0]["capacity"]["amount"] = 2
        result = rerank_draft(parent, refreshed, run_id="sra-rerank-second", reason="Current resource window has one additional day.")
        self.assertEqual(result["status"], "ready_for_prepare")
        child = result["draft"]
        self.assertEqual(validate_context_input(child), [])
        self.assertNotIn("allocation_outcome", child)
        self.assertNotIn("dependency_resolutions", child)
        self.assertEqual(child["allocation_frame"]["resource_pools"][0]["capacity"]["amount"], 2)
        self.assertEqual(before, {str(p.relative_to(parent)): p.read_bytes() for p in parent.rglob("*") if p.is_file()})
        child_run = self.prepare_run(child)
        self.assertFalse((child_run / "final-decision.json").exists())
        self.assertEqual(run_check(child_run)["status"], "ok")
        for packet in ("challenge-packet.json", "situated-packet.json"):
            self.assertNotIn("rerank_lineage", load_json(child_run / packet))
        with self.assertRaises(SraRuntimeError):
            rerank_draft(parent, refreshed, run_id=judgment.get("run_id", "sra-v03-runtime-contract"), reason="same id")
        (parent / "final-decision.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(SraRuntimeError):
            rerank_draft(parent, refreshed, run_id="sra-third", reason="changed parent")

    def test_rerank_refuses_parent_changed_during_assessment(self):
        parent = self.prepare_run(proportionate_input("lite"))
        record_situated(parent, situated_judgment(load_json(parent / "situated-packet.json")), carrier="packet_bound", receipt_path=None)
        refreshed = proportionate_input("lite")
        refreshed.pop("run_id")
        def changed_after_check(path):
            report = run_check(path)
            raw = load_json(path / "raw-input.json")
            raw["allocation_frame"]["parent_objective"] = "Changed during assessment"
            (path / "raw-input.json").write_text(json.dumps(raw), encoding="utf-8")
            return report
        with patch("rerank_sra_context.run_check", side_effect=changed_after_check):
            with self.assertRaisesRegex(SraRuntimeError, "parent changed"):
                rerank_draft(parent, refreshed, run_id="new-current-window", reason="Capacity changed")

    def test_draft_malformed_inputs_and_unknown_risk_do_not_silently_enable_single_view(self):
        for candidates in (None, "not-a-list", [None]):
            with self.subTest(candidates=candidates):
                report = draft_context({"candidates": candidates})
                self.assertEqual(report["status"], "needs_input")
        data = proportionate_input("lite")
        data.pop("execution_policy")
        report = draft_context(data)
        self.assertEqual(report["draft"]["execution_policy"]["risk_level"], "unknown")
        self.assertEqual(build_packets(report["draft"])["view_plan"], "dual_view")
        data["allocation_outcome"] = "allocate"
        self.assertEqual(draft_context(data)["status"], "needs_input")

    def test_draft_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw-input.json"
            path.write_bytes(b"original")
            with self.assertRaises(FileExistsError):
                write_draft(path, proportionate_input())
            self.assertEqual(path.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()
