import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "sra" / "scripts"
sys.path.insert(0, str(SCRIPTS.resolve()))

from sra_domain import (  # type: ignore[import-not-found]
    AUTHORIZATION_HORIZONS,
    COMPARISON_FIELDS,
    FINAL_DECISION_SCHEMA,
    INPUT_SCHEMA,
    LITE_AUTHORIZATION_HORIZONS,
    RUN_SCHEMA,
    canonical_bundle_key,
    finalization_status_for_outcome,
    quantity_schema,
    resource_allocation_schema,
    validate_override_record,
    validate_quantity,
    validate_quantity_for_contract,
    validate_resource_allocations,
    validate_resource_envelope,
)


def measured_contract(unit: str = "engineer-day") -> dict:
    return {"family": "measured", "unit": unit}


def ordinal_contract() -> dict:
    return {"family": "ordinal", "scale": ["low", "medium", "high"]}


def indivisible_contract() -> dict:
    return {"family": "indivisible", "blocks": ["slot-a", "slot-b"]}


def exact(amount: float, unit: str = "engineer-day") -> dict:
    return {"quantity_kind": "exact", "amount": amount, "unit": unit}


def bounded(lower: float, upper: float, unit: str = "engineer-day") -> dict:
    return {
        "quantity_kind": "bounded",
        "lower_bound": lower,
        "upper_bound": upper,
        "unit": unit,
    }


def ordinal(level: str) -> dict:
    return {"quantity_kind": "ordinal", "level": level}


def indivisible(*blocks: str) -> dict:
    return {"quantity_kind": "indivisible", "blocks": list(blocks)}


def pool(
    resource_id: str,
    contract: dict,
    capacity: dict,
) -> dict:
    return {
        "resource_id": resource_id,
        "label": resource_id,
        "quantity_contract": contract,
        "capacity": capacity,
        "window": "current window",
    }


def allocation(resource_id: str, quantity: dict) -> dict:
    return {"resource_id": resource_id, "quantity": quantity}


class SraV03DomainTests(unittest.TestCase):
    def test_runtime_contract_versions_are_v03(self):
        self.assertTrue(INPUT_SCHEMA.endswith("v0.3"))
        self.assertTrue(RUN_SCHEMA.endswith("v0.3"))
        self.assertTrue(FINAL_DECISION_SCHEMA.endswith("v0.3"))

    def test_finalization_mapping_is_single_and_explicit(self):
        self.assertEqual(finalization_status_for_outcome("allocate"), "finalized")
        self.assertEqual(finalization_status_for_outcome("conditional"), "conditional")
        self.assertEqual(finalization_status_for_outcome("infeasible"), "finalized")
        self.assertEqual(finalization_status_for_outcome("blocked"), "blocked")
        self.assertEqual(
            finalization_status_for_outcome("request_missing_context"), "blocked"
        )

    def test_lite_authorization_is_a_strict_subset(self):
        self.assertLess(LITE_AUTHORIZATION_HORIZONS, AUTHORIZATION_HORIZONS)
        self.assertNotIn("bounded_decision_window", LITE_AUTHORIZATION_HORIZONS)

    def test_comparison_contract_includes_bundle_and_resource_commitment(self):
        self.assertIn("bundle_decision", COMPARISON_FIELDS)
        self.assertIn("allocation_ledger", COMPARISON_FIELDS)
        self.assertIn("next_tranche", COMPARISON_FIELDS)
        self.assertIn("investment_ceiling", COMPARISON_FIELDS)
        self.assertIn("reserve", COMPARISON_FIELDS)

    def test_measured_quantity_accepts_exact_and_bounded_in_one_unit(self):
        findings: list[str] = []
        validate_quantity_for_contract(
            exact(1), measured_contract(), "quantity", findings
        )
        validate_quantity_for_contract(
            bounded(0.5, 1), measured_contract(), "quantity", findings
        )
        self.assertEqual(findings, [])

    def test_measured_quantity_rejects_unit_drift(self):
        findings: list[str] = []
        validate_quantity_for_contract(
            exact(1, "banana"), measured_contract(), "quantity", findings
        )
        self.assertTrue(any("unit" in item for item in findings))

    def test_ordinal_quantity_rejects_numeric_allocation(self):
        findings: list[str] = []
        validate_quantity_for_contract(
            exact(1, "lawyer-day"), ordinal_contract(), "quantity", findings
        )
        self.assertTrue(findings)

    def test_ordinal_quantity_uses_declared_scale(self):
        findings: list[str] = []
        validate_quantity_for_contract(
            ordinal("urgent"), ordinal_contract(), "quantity", findings
        )
        self.assertTrue(any("scale" in item for item in findings))

    def test_indivisible_quantity_rejects_unknown_blocks(self):
        findings: list[str] = []
        validate_quantity_for_contract(
            indivisible("slot-c"), indivisible_contract(), "quantity", findings
        )
        self.assertTrue(any("block" in item for item in findings))

    def test_dynamic_resource_schema_binds_quantity_to_resource_contract(self):
        pools = [
            pool("engineer-time", measured_contract(), exact(2)),
            pool("attention", ordinal_contract(), ordinal("medium")),
        ]
        schema = resource_allocation_schema(pools)
        variants = schema["items"]["oneOf"]
        by_id = {
            item["properties"]["resource_id"]["const"]: item for item in variants
        }
        measured_quantity = by_id["engineer-time"]["properties"]["quantity"]
        ordinal_quantity = by_id["attention"]["properties"]["quantity"]
        self.assertEqual(len(measured_quantity["oneOf"]), 2)
        self.assertEqual(
            ordinal_quantity["properties"]["quantity_kind"]["const"], "ordinal"
        )

    def test_resource_allocations_require_declared_resource_and_contract(self):
        pools = [pool("engineer-time", measured_contract(), exact(1))]
        findings: list[str] = []
        validate_resource_allocations(
            [allocation("attention", ordinal("low"))],
            "allocations",
            resource_pools=pools,
            findings=findings,
        )
        self.assertTrue(findings)

    def test_bounded_capacity_uses_upper_bound_as_hard_envelope(self):
        pools = [
            pool("engineer-time", measured_contract(), bounded(0.5, 1.0))
        ]
        findings: list[str] = []
        validate_resource_envelope(
            resource_pools=pools,
            current_allocations=[],
            next_allocations=[allocation("engineer-time", exact(5))],
            reserve_allocations=[],
            investment_ceiling=[allocation("engineer-time", exact(5))],
            outcome="allocate",
            findings=findings,
        )
        self.assertTrue(any("capacity" in item for item in findings))

    def test_indivisible_block_cannot_be_double_allocated(self):
        pools = [
            pool(
                "review-slot",
                indivisible_contract(),
                indivisible("slot-a", "slot-b"),
            )
        ]
        findings: list[str] = []
        validate_resource_envelope(
            resource_pools=pools,
            current_allocations=[
                allocation("review-slot", indivisible("slot-a"))
            ],
            next_allocations=[
                allocation("review-slot", indivisible("slot-a"))
            ],
            reserve_allocations=[],
            investment_ceiling=[
                allocation("review-slot", indivisible("slot-a", "slot-b"))
            ],
            outcome="allocate",
            findings=findings,
        )
        self.assertTrue(any("allocated more than once" in item for item in findings))

    def test_override_record_requires_authority_reference(self):
        findings: list[str] = []
        validate_override_record(
            {
                "override_reason": "bounded exception",
                "approved_by": "release-owner",
                "risk_acceptance_scope": "this run",
                "expiry": "end of run",
            },
            "overrides.mode",
            findings,
        )
        self.assertTrue(any("authority_ref" in item for item in findings))

    def test_bundle_identity_is_member_based(self):
        self.assertEqual(
            canonical_bundle_key(["candidate-b", "candidate-a"]),
            canonical_bundle_key(["candidate-a", "candidate-b"]),
        )

    def test_quantity_schema_and_manual_validator_share_field_names(self):
        schema = quantity_schema(measured_contract())
        serialized = str(schema)
        self.assertIn("quantity_kind", serialized)
        self.assertIn("lower_bound", serialized)
        findings: list[str] = []
        validate_quantity(
            {"quantity_kind": "bounded", "lower": 0, "upper": 1},
            "quantity",
            findings,
        )
        self.assertTrue(findings)


if __name__ == "__main__":
    unittest.main()
