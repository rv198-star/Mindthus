import copy
import json
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "sra" / "scripts"
sys.path.insert(0, str(SCRIPTS.resolve()))

from sra_domain import (  # type: ignore[import-not-found]
    CHALLENGE_JUDGMENT_SCHEMA,
    INPUT_SCHEMA,
    SITUATED_JUDGMENT_SCHEMA,
)
from sra_runtime import (  # type: ignore[import-not-found]
    build_packets,
    compare_views,
    situated_output_schema,
    validate_context_input,
    validate_situated_judgment,
)


def exact(amount: float, unit: str = "engineer-day") -> dict:
    return {"quantity_kind": "exact", "amount": amount, "unit": unit}


def allocation(resource_id: str, amount: float, unit: str = "engineer-day") -> dict:
    return {"resource_id": resource_id, "quantity": exact(amount, unit)}


def input_data(*, mode: str = "lite") -> dict:
    return {
        "schema_version": INPUT_SCHEMA,
        "run_id": "sra-v03-runtime-contract",
        "decision_question": {
            "situated_question": "Should the release engineer continue page polish or validate payment?",
            "challenge_projection": "Which eligible release action should receive the next engineer-day?",
            "source": "current user request",
            "projection_basis": "Removes active-path identity, prior conclusions, and historical spend.",
        },
        "mode": mode,
        "view_plan": "auto",
        "coverage_review": "auto",
        "overrides": {},
        "escalation_signals": ["multiple_feasible_bundles"] if mode == "full" else [],
        "contamination_signals": ["prior_agent_conclusion"],
        "coverage_signals": [],
        "allocation_frame": {
            "parent_objective": "Launch a purchasable product page.",
            "target_threshold": "Usable page and validated payment path.",
            "time_window": "Current release window.",
            "risk_floor": "No launch with an unvalidated payment path.",
            "decision_owner": "Release owner",
            "resource_pools": [
                {
                    "resource_id": "engineer-time",
                    "label": "Backend engineer time",
                    "quantity_contract": {
                        "family": "measured",
                        "aggregation": "sum",
                        "unit": "engineer-day",
                    },
                    "capacity": exact(1),
                    "window": "Current release window.",
                },
                {
                    "resource_id": "review-slot",
                    "label": "Compliance review slot",
                    "quantity_contract": {
                        "family": "indivisible",
                        "aggregation": "set",
                        "blocks": ["slot-a"],
                    },
                    "capacity": {
                        "quantity_kind": "indivisible",
                        "blocks": ["slot-a"],
                    },
                    "window": "Current release window.",
                },
            ],
            "evidence_ceiling": "Current release-window evidence only.",
        },
        "active_candidate_id": "page-polish",
        "candidates": [
            {
                "candidate_id": "page-polish",
                "action_statement": "Improve animation polish.",
                "expected_target_effect": "Improves presentation beyond launch threshold.",
                "resource_demand": [allocation("engineer-time", 1)],
                "depends_on": [],
                "unlocks": [],
                "substitutes_for": [],
                "deadline_or_window": "Can wait until after launch.",
                "downside": "Consumes the only engineer-day.",
                "reversibility": "High.",
                "evidence_refs": ["E-page"],
                "assumption_refs": [],
            },
            {
                "candidate_id": "payment-validation",
                "action_statement": "Validate the payment path.",
                "expected_target_effect": "Closes an unresolved launch requirement.",
                "resource_demand": [allocation("engineer-time", 1)],
                "depends_on": [],
                "unlocks": [],
                "substitutes_for": [],
                "deadline_or_window": "Needed in the current release window.",
                "downside": "May reveal a larger defect.",
                "reversibility": "High for the validation action.",
                "evidence_refs": ["E-payment"],
                "assumption_refs": [],
            },
        ],
        "evidence": [
            {
                "evidence_id": "E-page",
                "kind": "acceptance_status",
                "source": "release checklist",
                "statement": "The page meets the usability threshold.",
                "observed_at": "2026-09-04T00:00:00Z",
                "claim_ceiling": "Current page acceptance only.",
            },
            {
                "evidence_id": "E-payment",
                "kind": "acceptance_status",
                "source": "release checklist",
                "statement": "Payment validation has not passed.",
                "observed_at": "2026-09-04T00:00:00Z",
                "claim_ceiling": "Current payment acceptance only.",
            },
        ],
        "assumptions": [],
        "context_items": [
            {
                "context_id": "CTX-quality",
                "kind": "user_constraint",
                "statement": "Release quality matters more than optional polish in this window.",
                "challenge_projection": "The release threshold takes precedence over optional improvement.",
                "projection_basis": "Preserves the value constraint without naming a candidate.",
                "source": "current user constraint",
                "decision_relevance": "Constrains the trade-off.",
                "requested_disposition": "consider",
                "candidate_ids": [],
                "evidence_refs": [],
                "assumption_refs": [],
            },
            {
                "context_id": "CTX-prior",
                "kind": "previous_conclusion",
                "statement": "A prior agent recommended continuing page-polish.",
                "source": "prior response",
                "decision_relevance": "Potential anchoring only.",
                "requested_disposition": "consider",
                "candidate_ids": ["page-polish"],
                "evidence_refs": [],
                "assumption_refs": [],
            },
        ],
        "state_context": {
            "switching_costs": [],
            "reusable_assets": [],
            "remaining_costs": [],
            "historical_spend": [],
            "commitments": [],
        },
        "source_inventory": [],
        "known_omissions": [],
    }


def assessment(candidate_id: str, *, feasibility: str = "feasible") -> dict:
    return {
        "candidate_id": candidate_id,
        "feasibility": feasibility,
        "candidate_role": (
            "threshold_essential"
            if candidate_id == "payment-validation"
            else "value_expanding"
        ),
        "contraction_result": "retained" if candidate_id == "payment-validation" else "removed",
        "first_break_point": "Named break point.",
        "evidence_refs": [],
        "assumption_refs": [],
    }


def bundle_decision(mode: str) -> dict:
    if mode == "lite":
        return {
            "status": "not_applicable",
            "bundle_assessments": [],
            "selected_bundle_id": "none",
        }
    return {
        "status": "assessed",
        "bundle_assessments": [
            {
                "bundle_id": "B-launch",
                "member_ids": ["payment-validation"],
                "feasibility": "feasible",
                "dominance_status": "non_dominated",
                "dominated_by": [],
                "resource_requirements": [allocation("engineer-time", 0.9)],
                "contraction_result": "retained",
                "target_support": "Closes the remaining launch requirement.",
                "evidence_refs": ["E-payment"],
                "assumption_refs": [],
            },
            {
                "bundle_id": "B-polish",
                "member_ids": ["page-polish"],
                "feasibility": "infeasible",
                "dominance_status": "infeasible",
                "dominated_by": [],
                "resource_requirements": [allocation("engineer-time", 1)],
                "contraction_result": "removed",
                "target_support": "Does not close payment acceptance.",
                "evidence_refs": ["E-page"],
                "assumption_refs": [],
            },
        ],
        "selected_bundle_id": "B-launch",
    }


def situated_judgment(packet: dict) -> dict:
    mode = packet["mode"]
    return {
        "schema_version": SITUATED_JUDGMENT_SCHEMA,
        "stage": "situated",
        "packet_hash": packet["packet_hash"],
        "allocation_outcome": "allocate",
        "candidate_assessments": [
            assessment("page-polish"),
            assessment("payment-validation"),
        ],
        "bundle_decision": bundle_decision(mode),
        "state_considerations": [],
        "allocation_ledger": [
            {
                "candidate_id": "page-polish",
                "posture": "defer",
                "current_allocations": [],
                "reason": "Optional polish is outside the current launch floor.",
            },
            {
                "candidate_id": "payment-validation",
                "posture": "candidate",
                "current_allocations": [],
                "reason": "Eligible for the next replenishment tranche.",
            },
        ],
        "next_tranche": {
            "target_id": "payment-validation",
            "resource_allocations": [allocation("engineer-time", 0.9)],
            "window": "Current release window.",
            "completion_signal": "A reproducible payment validation result.",
            "start_condition": "",
            "reason": "Payment remains the launch blocker.",
        },
        "investment_ceiling": [allocation("engineer-time", 0.9)],
        "authorization_horizon": "one_tranche",
        "reserve": {
            "status": "none",
            "resource_allocations": [],
            "reason": "No observed incident requires reserve.",
            "release_trigger": "Not applicable.",
            "review_time": "At the payment checkpoint.",
        },
        "rerank_triggers": ["Payment validation completes or reveals a blocker."],
        "missing_information": [],
        "state_refs": [],
        "evidence_refs": ["E-page", "E-payment"],
        "assumption_refs": [],
        "sunk_cost_used_as_reason": False,
        "claim_ceiling": "Current release-window allocation only.",
    }


def challenge_from_situated(challenge_packet: dict, situated: dict, mapping: dict) -> dict:
    original_to_alias = {candidate_id: alias for alias, candidate_id in mapping.items()}
    result = copy.deepcopy(situated)
    result["schema_version"] = CHALLENGE_JUDGMENT_SCHEMA
    result["stage"] = "challenge"
    result["packet_hash"] = challenge_packet["packet_hash"]
    result.pop("state_considerations", None)
    result.pop("state_refs", None)
    result.pop("sunk_cost_used_as_reason", None)
    for item in result["candidate_assessments"]:
        item["challenge_id"] = original_to_alias[item.pop("candidate_id")]
    for item in result["allocation_ledger"]:
        item["challenge_id"] = original_to_alias[item.pop("candidate_id")]
    result["next_tranche"]["target_id"] = original_to_alias[
        result["next_tranche"]["target_id"]
    ]
    for bundle in result["bundle_decision"]["bundle_assessments"]:
        bundle["member_ids"] = [original_to_alias[item] for item in bundle["member_ids"]]
    return result


class SraV03RuntimeContractTests(unittest.TestCase):
    def test_valid_v03_input_passes(self):
        self.assertEqual(validate_context_input(input_data()), [])

    def test_challenge_receives_projection_not_situated_question_or_prior_conclusion(self):
        packet = build_packets(input_data())["challenge_packet"]
        text = json.dumps(packet, ensure_ascii=False)
        self.assertIn("Which eligible release action", text)
        self.assertNotIn("Should the release engineer continue page polish", text)
        self.assertNotIn("prior agent recommended", text.casefold())

    def test_challenge_projection_rejects_original_candidate_identifier(self):
        data = input_data()
        data["decision_question"]["challenge_projection"] = (
            "Should page-polish continue or should another action receive the resource?"
        )
        findings = validate_context_input(data)
        self.assertTrue(any("challenge_projection" in item for item in findings))

    def test_context_projection_is_required_for_admitted_context(self):
        data = input_data()
        del data["context_items"][0]["challenge_projection"]
        findings = validate_context_input(data)
        self.assertTrue(any("challenge_projection" in item for item in findings))

    def test_shared_resource_contention_is_required(self):
        data = input_data()
        data["candidates"][0]["resource_demand"] = [
            {
                "resource_id": "review-slot",
                "quantity": {
                    "quantity_kind": "indivisible",
                    "blocks": ["slot-a"],
                },
            }
        ]
        findings = validate_context_input(data)
        self.assertTrue(any("contested" in item for item in findings))

    def test_override_must_bind_declared_authority_holder(self):
        data = input_data()
        data["mode"] = "lite"
        data["escalation_signals"] = ["major_commitment"]
        data["context_items"].append(
            {
                "context_id": "AUTH-release",
                "kind": "authority_decision",
                "authority_holder": "Release owner",
                "authority_scope": "May approve this run's analysis-depth downgrade.",
                "authority_expiry": "End of this run.",
                "statement": "Release owner may approve a bounded downgrade.",
                "challenge_projection": "The decision owner permits a bounded analysis-depth downgrade.",
                "projection_basis": "Retains authority without candidate identity.",
                "source": "current authority record",
                "decision_relevance": "Controls downgrade authority.",
                "requested_disposition": "admit",
                "candidate_ids": [],
                "evidence_refs": [],
                "assumption_refs": [],
            }
        )
        data["overrides"]["mode"] = {
            "override_reason": "One reversible tranche only.",
            "approved_by": "Someone else",
            "authority_ref": "AUTH-release",
            "risk_acceptance_scope": "This run only.",
            "expiry": "End of this run.",
        }
        findings = validate_context_input(data)
        self.assertTrue(any("approved_by" in item for item in findings))

    def test_lite_schema_marks_bundle_decision_not_applicable(self):
        packet = build_packets(input_data())["situated_packet"]
        schema = situated_output_schema(packet)
        bundle_schema = schema["properties"]["bundle_decision"]
        self.assertEqual(
            bundle_schema["properties"]["status"]["const"], "not_applicable"
        )

    def test_full_schema_requires_bundle_assessments(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        schema = situated_output_schema(packet)
        bundle_schema = schema["properties"]["bundle_decision"]
        self.assertEqual(bundle_schema["properties"]["status"]["const"], "assessed")
        self.assertGreaterEqual(
            bundle_schema["properties"]["bundle_assessments"]["minItems"], 1
        )

    def test_schema_vocabulary_and_json_type_boundaries(self):
        from sra_structure import validate_structure
        probes = [
            (True, {"type": "number"}),
            (True, {"enum": [1]}),
            (float("nan"), {"type": "number"}),
            (float("inf"), {"type": "number"}),
            ({}, {"type": "object", "properties": {"unused": {"unsupportedKeyword": True}}}),
            ([], {"type": ["array", "null"]}),
            ("x", {"oneOf": [{"type": "string"}, {"type": "string"}]}),
            ([1, 1.0], {"type": "array", "uniqueItems": True}),
        ]
        for value, schema in probes:
            with self.subTest(value=value, schema=schema):
                self.assertTrue(validate_structure(value, schema))
        self.assertEqual(validate_structure([True, 1], {"type": "array", "uniqueItems": True}), [])
        self.assertEqual(validate_structure(1.0, {"type": "integer"}), [])

    def test_closed_schema_rejects_unknown_fields_at_each_object_boundary(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        paths = [(), ("allocation_ledger", 0), ("candidate_assessments", 0),
                 ("next_tranche",), ("reserve",), ("bundle_decision",),
                 ("bundle_decision", "bundle_assessments", 0),
                 ("next_tranche", "resource_allocations", 0, "quantity")]
        for path in paths:
            with self.subTest(path=path):
                judgment = situated_judgment(packet)
                target = judgment
                for key in path:
                    target = target[key]
                target["unrecognized_authorization_override"] = True
                findings = validate_situated_judgment(judgment, packet)
                self.assertTrue(any("unrecognized_authorization_override" in x for x in findings), findings)

    def test_closed_schema_rejects_missing_and_malformed_nested_fields(self):
        packet = build_packets(input_data())["situated_packet"]
        for field in ("evidence_refs", "assumption_refs", "missing_information"):
            with self.subTest(missing=field):
                judgment = situated_judgment(packet)
                del judgment[field]
                self.assertTrue(validate_situated_judgment(judgment, packet))
        for value in (None, "not-an-object", [], True):
            with self.subTest(tranche=value):
                judgment = situated_judgment(packet)
                judgment["next_tranche"] = value
                self.assertTrue(validate_situated_judgment(judgment, packet))

    def test_valid_full_bundle_judgment_passes(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        self.assertEqual(validate_situated_judgment(situated_judgment(packet), packet), [])

    def test_full_without_bundle_surface_is_rejected(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        judgment = situated_judgment(packet)
        judgment["bundle_decision"] = {
            "status": "not_applicable",
            "bundle_assessments": [],
            "selected_bundle_id": "none",
        }
        self.assertTrue(validate_situated_judgment(judgment, packet))

    def test_infeasible_candidate_cannot_receive_resource(self):
        packet = build_packets(input_data())["situated_packet"]
        judgment = situated_judgment(packet)
        judgment["candidate_assessments"][1]["feasibility"] = "infeasible"
        self.assertTrue(validate_situated_judgment(judgment, packet))

    def test_candidate_cannot_receive_resource_not_declared_in_its_demand(self):
        packet = build_packets(input_data())["situated_packet"]
        judgment = situated_judgment(packet)
        judgment["next_tranche"] = {
            "target_id": "payment-validation",
            "resource_allocations": [
                {
                    "resource_id": "review-slot",
                    "quantity": {
                        "quantity_kind": "indivisible",
                        "blocks": ["slot-a"],
                    },
                }
            ],
            "window": "Current release window.",
            "completion_signal": "Review completed.",
            "start_condition": "",
            "reason": "Attempt to allocate an unrelated resource.",
        }
        judgment["investment_ceiling"] = copy.deepcopy(
            judgment["next_tranche"]["resource_allocations"]
        )
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(any("resource demand" in item for item in findings))

    def test_lite_cumulative_candidate_commitment_cannot_exceed_demand(self):
        data = input_data()
        engineer_pool = next(
            item
            for item in data["allocation_frame"]["resource_pools"]
            if item["resource_id"] == "engineer-time"
        )
        engineer_pool["capacity"] = exact(2)
        packet = build_packets(data)["situated_packet"]
        judgment = situated_judgment(packet)
        payment_row = next(
            item
            for item in judgment["allocation_ledger"]
            if item["candidate_id"] == "payment-validation"
        )
        payment_row["posture"] = "floor"
        payment_row["current_allocations"] = [allocation("engineer-time", 0.6)]
        judgment["investment_ceiling"] = [allocation("engineer-time", 1.5)]
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("cumulative" in item and "candidate resource demand" in item for item in findings),
            findings,
        )

    def test_lite_cumulative_candidate_commitment_equal_to_demand_passes(self):
        data = input_data()
        engineer_pool = next(
            item
            for item in data["allocation_frame"]["resource_pools"]
            if item["resource_id"] == "engineer-time"
        )
        engineer_pool["capacity"] = exact(2)
        packet = build_packets(data)["situated_packet"]
        judgment = situated_judgment(packet)
        payment_row = next(
            item
            for item in judgment["allocation_ledger"]
            if item["candidate_id"] == "payment-validation"
        )
        payment_row["posture"] = "floor"
        payment_row["current_allocations"] = [allocation("engineer-time", 0.1)]
        judgment["investment_ceiling"] = [allocation("engineer-time", 1)]
        self.assertEqual(validate_situated_judgment(judgment, packet), [])

    def test_lite_bounded_demand_applies_to_cumulative_commitment(self):
        data = input_data()
        engineer_pool = next(
            item
            for item in data["allocation_frame"]["resource_pools"]
            if item["resource_id"] == "engineer-time"
        )
        engineer_pool["capacity"] = exact(2)
        payment = next(
            item
            for item in data["candidates"]
            if item["candidate_id"] == "payment-validation"
        )
        payment["resource_demand"] = [
            {
                "resource_id": "engineer-time",
                "quantity": {
                    "quantity_kind": "bounded",
                    "lower_bound": 0,
                    "upper_bound": 1,
                    "unit": "engineer-day",
                },
            }
        ]
        packet = build_packets(data)["situated_packet"]
        judgment = situated_judgment(packet)
        payment_row = next(
            item
            for item in judgment["allocation_ledger"]
            if item["candidate_id"] == "payment-validation"
        )
        payment_row["posture"] = "floor"
        payment_row["current_allocations"] = [allocation("engineer-time", 0.2)]
        judgment["investment_ceiling"] = [allocation("engineer-time", 1.1)]
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("cumulative" in item and "candidate resource demand" in item for item in findings),
            findings,
        )

    def test_selected_full_bundle_must_contain_next_candidate(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        judgment = situated_judgment(packet)
        judgment["bundle_decision"]["selected_bundle_id"] = "B-polish"
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(any("selected bundle" in item for item in findings))

    def test_different_resource_commitments_are_a_conflict(self):
        built = build_packets(input_data())
        situated = situated_judgment(built["situated_packet"])
        challenge = challenge_from_situated(
            built["challenge_packet"], situated, built["challenge_map"]
        )
        challenge["next_tranche"]["resource_allocations"] = [
            allocation("engineer-time", 0.1)
        ]
        comparison = compare_views(
            run_id=input_data()["run_id"],
            challenge_packet_hash=built["challenge_packet"]["packet_hash"],
            situated_packet_hash=built["situated_packet"]["packet_hash"],
            challenge_judgment=challenge,
            situated_judgment=situated,
            challenge_map=built["challenge_map"],
        )
        self.assertEqual(comparison["status"], "conflict")
        self.assertIn(
            "next_tranche",
            {item["field"] for item in comparison["conflict_fields"]},
        )

    def test_bundle_comparison_uses_members_not_local_bundle_id(self):
        built = build_packets(input_data(mode="full"))
        situated = situated_judgment(built["situated_packet"])
        challenge = challenge_from_situated(
            built["challenge_packet"], situated, built["challenge_map"]
        )
        challenge["bundle_decision"]["bundle_assessments"][0]["bundle_id"] = "X1"
        challenge["bundle_decision"]["bundle_assessments"][1]["bundle_id"] = "X2"
        challenge["bundle_decision"]["selected_bundle_id"] = "X1"
        comparison = compare_views(
            run_id=input_data(mode="full")["run_id"],
            challenge_packet_hash=built["challenge_packet"]["packet_hash"],
            situated_packet_hash=built["situated_packet"]["packet_hash"],
            challenge_judgment=challenge,
            situated_judgment=situated,
            challenge_map=built["challenge_map"],
        )
        self.assertNotIn(
            "bundle_decision",
            {item["field"] for item in comparison["conflict_fields"]},
        )

    def test_infeasible_outcome_cannot_coexist_with_feasible_nondominated_bundle(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        judgment = situated_judgment(packet)
        judgment["allocation_outcome"] = "infeasible"
        judgment["bundle_decision"]["selected_bundle_id"] = "none"
        judgment["next_tranche"] = {
            "target_id": "none",
            "resource_allocations": [],
            "window": "Current release window.",
            "completion_signal": "No target-reaching allocation exists.",
            "start_condition": "",
            "reason": "Declared infeasible for the contract probe.",
        }
        judgment["investment_ceiling"] = []
        for row in judgment["allocation_ledger"]:
            row["posture"] = "defer"
            row["current_allocations"] = []
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("feasible" in item and "infeasible" in item for item in findings),
            findings,
        )

    def test_selected_bundle_cannot_include_stopped_or_deferred_member(self):
        for posture in ("stop", "defer"):
            packet = build_packets(input_data(mode="full"))["situated_packet"]
            judgment = situated_judgment(packet)
            selected = judgment["bundle_decision"]["bundle_assessments"][0]
            selected["member_ids"] = ["page-polish", "payment-validation"]
            selected["resource_requirements"] = [allocation("engineer-time", 0.9)]
            judgment["bundle_decision"]["bundle_assessments"] = [selected]
            page_row = next(
                row for row in judgment["allocation_ledger"]
                if row["candidate_id"] == "page-polish"
            )
            page_row["posture"] = posture
            findings = validate_situated_judgment(judgment, packet)
            self.assertTrue(
                any("selected bundle" in item and posture in item for item in findings),
                (posture, findings),
            )

    def test_bundle_dominance_cycle_is_rejected(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        judgment = situated_judgment(packet)
        bundles = judgment["bundle_decision"]["bundle_assessments"]
        bundles[0]["dominance_status"] = "dominated"
        bundles[0]["dominated_by"] = [bundles[1]["bundle_id"]]
        bundles[1]["feasibility"] = "feasible"
        bundles[1]["dominance_status"] = "dominated"
        bundles[1]["dominated_by"] = [bundles[0]["bundle_id"]]
        judgment["allocation_outcome"] = "blocked"
        judgment["bundle_decision"]["selected_bundle_id"] = "none"
        judgment["next_tranche"]["target_id"] = "none"
        judgment["next_tranche"]["resource_allocations"] = []
        judgment["investment_ceiling"] = []
        judgment["missing_information"] = ["Dominance relation cannot be resolved."]
        for row in judgment["allocation_ledger"]:
            row["posture"] = "defer"
            row["current_allocations"] = []
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(any("cycle" in item for item in findings), findings)

    def test_allocate_rejects_conditional_or_unclear_next_candidate(self):
        for feasibility in ("conditional", "unclear"):
            packet = build_packets(input_data())["situated_packet"]
            judgment = situated_judgment(packet)
            target = next(
                item for item in judgment["candidate_assessments"]
                if item["candidate_id"] == "payment-validation"
            )
            target["feasibility"] = feasibility
            findings = validate_situated_judgment(judgment, packet)
            self.assertTrue(
                any("next-tranche candidate" in item and feasibility in item for item in findings),
                (feasibility, findings),
            )

    def test_selected_bundle_requirements_must_fit_resource_capacity(self):
        data = input_data(mode="full")
        payment = next(
            item for item in data["candidates"]
            if item["candidate_id"] == "payment-validation"
        )
        payment["resource_demand"] = [allocation("engineer-time", 3)]
        packet = build_packets(data)["situated_packet"]
        judgment = situated_judgment(packet)
        judgment["bundle_decision"]["bundle_assessments"][0][
            "resource_requirements"
        ] = [allocation("engineer-time", 2)]
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("bundle" in item and "capacity" in item for item in findings),
            findings,
        )

    @staticmethod
    def _remove_full_authorization(judgment: dict) -> None:
        judgment["bundle_decision"]["selected_bundle_id"] = "none"
        judgment["next_tranche"] = {
            "target_id": "none",
            "resource_allocations": [],
            "window": "Current release window.",
            "completion_signal": "No allocation starts.",
            "start_condition": "",
            "reason": "Contract probe.",
        }
        judgment["investment_ceiling"] = []
        for row in judgment["allocation_ledger"]:
            row["posture"] = "defer"
            row["current_allocations"] = []

    def test_infeasible_rejects_any_bundle_coded_feasible_even_if_dominated(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        judgment = situated_judgment(packet)
        bundles = judgment["bundle_decision"]["bundle_assessments"]
        bundles[0]["dominance_status"] = "dominated"
        bundles[0]["dominated_by"] = [bundles[1]["bundle_id"]]
        bundles[1]["feasibility"] = "infeasible"
        bundles[1]["dominance_status"] = "infeasible"
        bundles[1]["dominated_by"] = []
        judgment["allocation_outcome"] = "infeasible"
        self._remove_full_authorization(judgment)
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("infeasible" in item and "feasible" in item for item in findings),
            findings,
        )

    def test_dominator_must_not_be_infeasible_or_unclear(self):
        for feasibility in ("infeasible", "unclear"):
            packet = build_packets(input_data(mode="full"))["situated_packet"]
            judgment = situated_judgment(packet)
            bundles = judgment["bundle_decision"]["bundle_assessments"]
            bundles[0]["dominance_status"] = "dominated"
            bundles[0]["dominated_by"] = [bundles[1]["bundle_id"]]
            bundles[1]["feasibility"] = feasibility
            bundles[1]["dominance_status"] = (
                "infeasible" if feasibility == "infeasible" else "unclear"
            )
            bundles[1]["dominated_by"] = []
            judgment["allocation_outcome"] = "blocked"
            judgment["missing_information"] = ["Dominance evidence is incomplete."]
            self._remove_full_authorization(judgment)
            findings = validate_situated_judgment(judgment, packet)
            self.assertTrue(
                any("dominated_by" in item and feasibility in item for item in findings),
                (feasibility, findings),
            )

    def test_selected_bundle_resource_vector_bounds_actual_commitment(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        judgment = situated_judgment(packet)
        judgment["bundle_decision"]["bundle_assessments"][0][
            "resource_requirements"
        ] = [allocation("engineer-time", 0.1)]
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("selected bundle" in item and "resource" in item for item in findings),
            findings,
        )

    def test_floor_allocation_outside_selected_bundle_is_rejected(self):
        data = input_data(mode="full")
        data["allocation_frame"]["resource_pools"][0]["capacity"]["amount"] = 1.1
        packet = build_packets(data)["situated_packet"]
        judgment = situated_judgment(packet)
        page = next(
            row for row in judgment["allocation_ledger"]
            if row["candidate_id"] == "page-polish"
        )
        page["posture"] = "floor"
        page["current_allocations"] = [allocation("engineer-time", 0.1)]
        judgment["investment_ceiling"] = [allocation("engineer-time", 1.1)]
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("outside selected bundle" in item for item in findings),
            findings,
        )

    def test_reserve_can_receive_next_tranche_without_double_counting_capacity(self):
        packet = build_packets(input_data())["situated_packet"]
        judgment = situated_judgment(packet)
        for row in judgment["allocation_ledger"]:
            row["posture"] = "defer"
            row["current_allocations"] = []
        reserved = [allocation("engineer-time", 1)]
        judgment["next_tranche"] = {
            "target_id": "reserve",
            "resource_allocations": copy.deepcopy(reserved),
            "window": "Current release window.",
            "completion_signal": "Capacity remains available for the named trigger.",
            "start_condition": "",
            "reason": "Option value exceeds immediate allocation.",
        }
        judgment["reserve"] = {
            "status": "reserved",
            "resource_allocations": copy.deepcopy(reserved),
            "reason": "Preserve response capacity.",
            "release_trigger": "A production incident or confirmed opportunity appears.",
            "review_time": "End of current release window.",
        }
        judgment["investment_ceiling"] = copy.deepcopy(reserved)
        self.assertEqual(validate_situated_judgment(judgment, packet), [])

    def test_reserve_target_and_reserve_record_must_name_same_resources(self):
        packet = build_packets(input_data())["situated_packet"]
        judgment = situated_judgment(packet)
        for row in judgment["allocation_ledger"]:
            row["posture"] = "defer"
            row["current_allocations"] = []
        judgment["next_tranche"] = {
            "target_id": "reserve",
            "resource_allocations": [allocation("engineer-time", 1)],
            "window": "Current release window.",
            "completion_signal": "Capacity remains available.",
            "start_condition": "",
            "reason": "Reserve the tranche.",
        }
        judgment["reserve"] = {
            "status": "reserved",
            "resource_allocations": [allocation("engineer-time", 0.5)],
            "reason": "Preserve response capacity.",
            "release_trigger": "A production incident appears.",
            "review_time": "End of current release window.",
        }
        judgment["investment_ceiling"] = [allocation("engineer-time", 1)]
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("reserve target" in item and "same" in item for item in findings),
            findings,
        )

    def test_full_infeasible_is_valid_when_every_bundle_is_infeasible(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        judgment = situated_judgment(packet)
        judgment["allocation_outcome"] = "infeasible"
        judgment["bundle_decision"]["selected_bundle_id"] = "none"
        for bundle in judgment["bundle_decision"]["bundle_assessments"]:
            bundle["feasibility"] = "infeasible"
            bundle["dominance_status"] = "infeasible"
            bundle["dominated_by"] = []
            bundle["resource_requirements"] = []
        for assessment in judgment["candidate_assessments"]:
            assessment["feasibility"] = "infeasible"
        for row in judgment["allocation_ledger"]:
            row["posture"] = "defer"
            row["current_allocations"] = []
        judgment["next_tranche"] = {
            "target_id": "none",
            "resource_allocations": [],
            "window": "Current release window.",
            "completion_signal": "No target-reaching bundle exists.",
            "start_condition": "",
            "reason": "All declared bundles violate current feasibility.",
        }
        judgment["investment_ceiling"] = []
        self.assertEqual(validate_situated_judgment(judgment, packet), [])

    def test_candidate_ids_cannot_collide_with_runtime_sentinels(self):
        for reserved in ("none", "reserve"):
            data = input_data()
            original = data["candidates"][0]["candidate_id"]
            data["candidates"][0]["candidate_id"] = reserved
            if data.get("active_candidate_id") == original:
                data["active_candidate_id"] = reserved
            for candidate in data["candidates"]:
                for field in ("depends_on", "unlocks", "substitutes_for"):
                    candidate[field] = [
                        reserved if item == original else item
                        for item in candidate.get(field, [])
                    ]
            for item in data["context_items"]:
                item["candidate_ids"] = [
                    reserved if candidate_id == original else candidate_id
                    for candidate_id in item.get("candidate_ids", [])
                ]
            findings = validate_context_input(data)
            self.assertTrue(
                any("reserved" in item and "candidate" in item for item in findings),
                (reserved, findings),
            )

    def test_bundle_id_cannot_use_none_sentinel(self):
        packet = build_packets(input_data(mode="full"))["situated_packet"]
        judgment = situated_judgment(packet)
        bundle = judgment["bundle_decision"]["bundle_assessments"][0]
        old_id = bundle["bundle_id"]
        bundle["bundle_id"] = "none"
        judgment["bundle_decision"]["selected_bundle_id"] = "none"
        for other in judgment["bundle_decision"]["bundle_assessments"]:
            other["dominated_by"] = [
                "none" if item == old_id else item
                for item in other["dominated_by"]
            ]
        findings = validate_situated_judgment(judgment, packet)
        self.assertTrue(
            any("bundle_id" in item and "reserved" in item for item in findings),
            findings,
        )

    def test_evidence_time_is_parseable_utc_or_timeless(self):
        for observed_at in (
            "yesterday",
            "2026-09-04",
            "2026-09-04T08:00:00+08:00",
        ):
            data = input_data()
            data["evidence"][0]["observed_at"] = observed_at
            findings = validate_context_input(data)
            self.assertTrue(
                any("observed_at" in item and "UTC" in item for item in findings),
                (observed_at, findings),
            )
        data = input_data()
        data["evidence"][0]["observed_at"] = "timeless"
        self.assertFalse(
            any("observed_at" in item for item in validate_context_input(data))
        )

    def test_override_expiry_cannot_extend_authority_expiry(self):
        data = input_data()
        data["escalation_signals"] = ["major_commitment"]
        data["mode"] = "lite"
        data["context_items"].append(
            {
                "context_id": "AUTH-mode",
                "kind": "authority_decision",
                "authority_holder": "Release owner",
                "authority_scope": "May approve one run's depth downgrade.",
                "authority_expiry": "End of this run.",
                "statement": "Release owner authorizes one bounded downgrade.",
                "challenge_projection": "The decision owner authorizes one bounded downgrade.",
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
            "authority_ref": "AUTH-mode",
            "risk_acceptance_scope": "This run only.",
            "expiry": "Never expires.",
        }
        findings = validate_context_input(data)
        self.assertTrue(
            any("expiry" in item and "authority" in item for item in findings),
            findings,
        )

    def test_candidate_cannot_depend_on_itself(self):
        data = input_data()
        candidate_id = data["candidates"][0]["candidate_id"]
        data["candidates"][0]["depends_on"] = [candidate_id]
        findings = validate_context_input(data)
        self.assertTrue(
            any("self" in item and "depends_on" in item for item in findings),
            findings,
        )


if __name__ == "__main__":
    unittest.main()
