import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SRA_ROOT = REPO / "skills" / "sra"
SRA_SKILL = SRA_ROOT / "SKILL.md"
SRA_RESOURCE = SRA_ROOT / "resources" / "methodology.md"
SRA_CONTEXT = SRA_ROOT / "resources" / "context-isolation.md"
SRA_FIDELITY = SRA_ROOT / "resources" / "fidelity-contract.md"
SRA_TEMPLATE = SRA_ROOT / "templates" / "fidelity-output.json"
SRA_VALIDATOR = SRA_ROOT / "scripts" / "validate_sra_output.py"
SRA_DOMAIN = SRA_ROOT / "scripts" / "sra_domain.py"
SRA_CORE = SRA_ROOT / "scripts" / "sra_runtime_core.py"
SRA_INTEGRITY = SRA_ROOT / "scripts" / "sra_runtime_integrity.py"
SRA_REPAIR = SRA_ROOT / "scripts" / "repair_sra_run.py"
SRA_DOC = REPO / "docs" / "methodologies" / "sra.md"
SRA_PRESSURE = REPO / "tests" / "sra_pressure_tests.md"
FULL_MOVES = (
    "minimum_sufficient_bundle",
    "resource_vector",
    "feasibility_and_dominance",
    "reserve_capacity",
)


def run_validator(payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sra-output.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return subprocess.run(
            ["python3", str(SRA_VALIDATOR), str(path)],
            text=True,
            capture_output=True,
            cwd=REPO,
        )


def run_validator_with_raw_text(raw_text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sra-output.json"
        path.write_text(raw_text, encoding="utf-8")
        return subprocess.run(
            ["python3", str(SRA_VALIDATOR), str(path)],
            text=True,
            capture_output=True,
            cwd=REPO,
        )


def valid_move(name: str) -> dict:
    return {
        "status": "addressed",
        "finding": f"{name} was handled for the current allocation.",
        "failure_criteria_response": f"The {name} failure condition was checked.",
        "evidence_surface": f"Case evidence for {name}.",
    }


def template_payload() -> dict:
    return json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))


def make_full_payload() -> dict:
    payload = template_payload()
    payload["entry_outcome"] = "full"
    payload["runtime_decision_ref"]["mode"] = "full"
    payload["runtime_decision_ref"]["authorization_horizon"] = "bounded_decision_window"
    for move_name in FULL_MOVES:
        payload["required_judgment_moves"][move_name] = valid_move(move_name)
    return payload


class SraContractTests(unittest.TestCase):
    def test_runtime_and_fidelity_files_exist(self):
        for path in (
            SRA_SKILL,
            SRA_RESOURCE,
            SRA_CONTEXT,
            SRA_FIDELITY,
            SRA_TEMPLATE,
            SRA_VALIDATOR,
            SRA_DOMAIN,
            SRA_CORE,
            SRA_INTEGRITY,
            SRA_REPAIR,
            SRA_DOC,
            SRA_PRESSURE,
        ):
            self.assertTrue(path.exists(), path)

    def test_sra_identity_and_core_are_consistent(self):
        for path in (SRA_SKILL, SRA_RESOURCE, SRA_DOC):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "SRA",
                "Scarce Resource Allocation",
                "稀缺资源优先分配",
                "先保护目标成立所必需的投入",
                "风险调整后边际价值最高的用途",
                "下一份资源",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_skill_uses_ordered_method_layers(self):
        text = SRA_SKILL.read_text(encoding="utf-8")
        headers = (
            "## Core Claim",
            "## Mainline",
            "## Guardrails",
            "## Boundaries",
            "## Runtime Support",
        )
        positions = [text.index(header) for header in headers]
        self.assertEqual(positions, sorted(positions))
        other = [
            line
            for line in text.splitlines()
            if line.startswith("## ") and line not in headers
        ]
        self.assertEqual(other, [])

    def test_entry_contract_keeps_direct_lite_full_and_blocked_distinct(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (SRA_SKILL, SRA_RESOURCE, SRA_FIDELITY)
        )
        for phrase in ("`direct`", "`lite`", "`full`", "`blocked`", "Analysis-Cost"):
            self.assertIn(phrase, combined)
        self.assertIn("`auto` starts from Lite", SRA_SKILL.read_text(encoding="utf-8"))

    def test_candidate_horizon_and_priority_order_remain_method_core(self):
        for path in (SRA_SKILL, SRA_RESOURCE):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "Candidate Horizon Probe",
                "current path",
                "hard gate",
                "strongest feasible alternative",
                "risk-adjusted bundle value",
                "reserve",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_runtime_contract_expresses_real_resources_bundles_and_projections(self):
        domain = SRA_DOMAIN.read_text(encoding="utf-8")
        core = SRA_CORE.read_text(encoding="utf-8")
        context = SRA_CONTEXT.read_text(encoding="utf-8")
        for phrase in (
            "quantity_contract",
            "measured",
            "ordinal",
            "indivisible",
            "bundle_decision",
            "selected_bundle_id",
            "challenge_projection",
            "authority_ref",
            "allocation_ledger",
        ):
            self.assertIn(phrase, domain + core + context)
        self.assertIn("bundle members", context)
        self.assertIn("candidate demand", context)

    def test_lite_and_full_share_contraction_replenishment_but_not_output_depth(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (SRA_SKILL, SRA_RESOURCE)
        )
        for phrase in (
            "micro-contraction",
            "micro-replenishment",
            "Resource Contraction",
            "Resource Replenishment",
            "one_tranche",
            "bounded_decision_window",
            "bundle assessments",
        ):
            self.assertIn(phrase, combined)

    def test_method_boundaries_preserve_neighbor_ownership(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (SRA_SKILL, SRA_RESOURCE)
        )
        for phrase in (
            "3L5S",
            "EDSP",
            "SELA",
            "MPG",
            "WAE",
            "TVG",
            "Anti-Spiral",
            "TPlan",
            "Pulse",
            "mutation",
        ):
            self.assertIn(phrase, combined)

    def test_pressure_tests_retain_positive_boundary_and_adversarial_cases(self):
        text = SRA_PRESSURE.read_text(encoding="utf-8")
        for phrase in (
            "Lite Positive Cases",
            "Full Positive Cases",
            "Boundary Cases",
            "Adversarial Cases",
            "Context-Calibration And Dual-View Cases",
            "Scenario 25: No Feasible Bundle",
            "Scenario 29: Reserve Option",
            "Scenario 31: Rich Active Task Versus Terse Blocker",
            "Scenario 32: Previous Agent Already Recommended Continuation",
            "Scenario 40: Coverage Review Finds A Missing Hard-Risk Candidate",
            "Scenario 42: Candidate Order Reversal",
        ):
            self.assertIn(phrase, text)

    def test_validator_imports_canonical_domain_and_template_passes(self):
        script = SRA_VALIDATOR.read_text(encoding="utf-8")
        for phrase in (
            "from sra_domain import",
            "FIDELITY_SCHEMA",
            "FINAL_DECISION_SCHEMA",
            "RECONCILIATION_OUTCOMES",
            "finalization_status_for_outcome",
        ):
            self.assertIn(phrase, script)
        for duplicate in (
            "ALLOCATION_OUTCOMES =",
            "AUTHORIZATION_HORIZONS =",
            "FINALIZATION_STATUSES =",
        ):
            self.assertNotIn(duplicate, script)
        result = run_validator(template_payload())
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("SRA Method-Fidelity & Evidence Risk Report", result.stdout)
        self.assertIn("No shape or evidence risks detected", result.stdout)

    def test_direct_and_blocked_are_accepted_method_exits(self):
        for entry_outcome in ("direct", "blocked"):
            with self.subTest(entry_outcome=entry_outcome):
                result = run_validator(
                    {
                        "schema_version": "sra-fidelity-v0.2",
                        "method": "SRA",
                        "entry_outcome": entry_outcome,
                        "plain_language_conclusion": "Do not run an applicable SRA allocation here.",
                        "exit_reason": "The next action is unique or the allocation frame is incomplete.",
                        "transfer_to": "3L5S" if entry_outcome == "blocked" else "",
                    }
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertIn(f"method exit accepted: {entry_outcome}", result.stdout)

    def test_applicable_fidelity_requires_runtime_decision_reference(self):
        payload = template_payload()
        del payload["runtime_decision_ref"]
        result = run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing field: runtime_decision_ref", result.stdout)

    def test_missing_base_move_fails(self):
        payload = template_payload()
        del payload["required_judgment_moves"]["candidate_horizon_probe"]
        result = run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required judgment move: candidate_horizon_probe", result.stdout)

    def test_lite_requires_contraction_and_replenishment(self):
        for move_name in ("contraction", "replenishment"):
            payload = template_payload()
            del payload["required_judgment_moves"][move_name]
            result = run_validator(payload)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"missing required judgment move: {move_name}", result.stdout)

    def test_full_requires_full_specific_moves(self):
        payload = template_payload()
        payload["entry_outcome"] = "full"
        payload["runtime_decision_ref"]["mode"] = "full"
        result = run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        for move_name in FULL_MOVES:
            self.assertIn(f"missing required judgment move: {move_name}", result.stdout)
        passing = run_validator(make_full_payload())
        self.assertEqual(passing.returncode, 0, passing.stderr + passing.stdout)

    def test_lite_rejects_full_only_authorization_horizon(self):
        payload = template_payload()
        payload["runtime_decision_ref"]["authorization_horizon"] = "bounded_decision_window"
        result = run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("runtime_decision_ref.authorization_horizon unsupported", result.stdout)

    def test_runtime_reference_rejects_mode_mismatch(self):
        payload = template_payload()
        payload["runtime_decision_ref"]["mode"] = "full"
        result = run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must match entry_outcome", result.stdout)

    def test_runtime_reference_rejects_outcome_finalization_mismatch(self):
        payload = template_payload()
        payload["runtime_decision_ref"]["allocation_outcome"] = "blocked"
        result = run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must match allocation_outcome", result.stdout)

    def test_runtime_reference_accepts_missing_context_block(self):
        payload = template_payload()
        payload["runtime_decision_ref"]["allocation_outcome"] = "request_missing_context"
        payload["runtime_decision_ref"]["finalization_status"] = "blocked"
        result = run_validator(payload)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_runtime_reference_rejects_malformed_digest(self):
        payload = template_payload()
        payload["runtime_decision_ref"]["artifact_hash"] = "sha256:nope"
        result = run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lowercase sha256", result.stdout)

    def test_invalid_json_is_reported_without_traceback(self):
        result = run_validator_with_raw_text('{"schema_version": ')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BLOCK:", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr + result.stdout)

    def test_fidelity_contract_has_no_second_allocation_carrier(self):
        text = SRA_FIDELITY.read_text(encoding="utf-8")
        for forbidden in (
            "## Lite Decision Carrier",
            "## Full Decision Carrier",
            "lite_decision",
            "full_decision",
            "selected_main_allocation",
            "minimum_maintenance as a list",
        ):
            self.assertNotIn(forbidden, text)
        for phrase in (
            "does not define a second resource-allocation result",
            "runtime_decision_ref",
            "sra.final-decision.v0.3",
            "does not validate or recreate the runtime allocation carrier",
        ):
            self.assertIn(phrase, text)

    def test_shape_pass_never_claims_priority_correctness(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (SRA_FIDELITY, SRA_VALIDATOR)
        )
        for phrase in (
            "does not prove",
            "correct priority",
            "semantic ROI",
            "bundle sufficiency",
        ):
            self.assertIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
