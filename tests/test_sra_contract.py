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
SRA_FIDELITY = SRA_ROOT / "resources" / "fidelity-contract.md"
SRA_TEMPLATE = SRA_ROOT / "templates" / "fidelity-output.json"
SRA_VALIDATOR = SRA_ROOT / "scripts" / "validate_sra_output.py"
SRA_DOC = REPO / "docs" / "methodologies" / "sra.md"
SRA_PRESSURE = REPO / "tests" / "sra_pressure_tests.md"
THREEL5S_SKILL = REPO / "skills" / "3l5s" / "SKILL.md"
SELA_SKILL = REPO / "skills" / "sela" / "SKILL.md"
MPG_SKILL = REPO / "skills" / "mpg" / "SKILL.md"
TVG_SKILL = REPO / "skills" / "tvg" / "SKILL.md"
TPLAN_SKILL = REPO / "skills" / "tplan" / "SKILL.md"
ANTI_SPIRAL_DOC = REPO / "docs" / "methodologies" / "anti-spiral-self-audit.md"


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


def make_full_payload() -> dict:
    payload = json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))
    payload["entry_outcome"] = "full"
    payload["allocation_action"] = "allocate"
    payload.pop("lite_decision")
    for move_name in FULL_MOVES:
        payload["required_judgment_moves"][move_name] = valid_move(move_name)
    payload["full_decision"] = {
        "allocation_outcome": "allocate",
        "allocation_scope": "execution_portfolio",
        "contested_resources": ["backend engineer-days", "security specialist-days"],
        "dominant_constraint": "Security specialist capacity before the compliance date.",
        "candidate_bundles": [
            {"bundle_id": "A", "status": "feasible"},
            {"bundle_id": "B", "status": "dominated"},
        ],
        "contraction_findings": [
            "Compliance verification and the production defect remain threshold-essential."
        ],
        "replenishment_findings": [
            "The next backend tranche goes to the production defect after compliance coverage is secured."
        ],
        "selected_main_allocation": "Protect compliance and production stability in parallel resource channels.",
        "necessary_support": ["Rollback verification"],
        "minimum_maintenance": ["Feature branch security updates only"],
        "explicit_defer": ["Performance debt"],
        "explicit_stop": [],
        "reserved_capacity": {
            "status": "reserved",
            "reason": "Preserve incident response capacity.",
            "release_trigger": "Compliance verification completes without new findings.",
            "review_time": "Mid-Sprint checkpoint.",
        },
        "next_tranche": "One security specialist-day for compliance verification.",
        "authorization_boundary": "Current Sprint allocation only.",
        "decision_lifetime": "Until the compliance checkpoint or a new production incident.",
        "rerank_triggers": [
            "Compliance verification result",
            "New production incident",
            "Specialist availability change",
        ],
    }
    return payload


class SraContractTests(unittest.TestCase):
    def test_phase_one_files_exist(self):
        for path in (
            SRA_SKILL,
            SRA_RESOURCE,
            SRA_FIDELITY,
            SRA_TEMPLATE,
            SRA_VALIDATOR,
            SRA_DOC,
            SRA_PRESSURE,
        ):
            self.assertTrue(path.exists(), path)

    def test_sra_identity_and_core_allocation_contract_are_consistent(self):
        for path in (SRA_SKILL, SRA_RESOURCE, SRA_DOC):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "SRA",
                "Scarce Resource Allocation",
                "稀缺资源优先分配",
                "先排除不可行",
                "达标必要项",
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
        self.assertEqual(
            [
                line
                for line in text.splitlines()
                if line.startswith("## ")
                and not line.startswith(
                    (
                        "## Core Claim",
                        "## Mainline",
                        "## Guardrails",
                        "## Boundaries",
                        "## Runtime Support",
                    )
                )
            ],
            [],
        )

    def test_entry_contract_keeps_direct_lite_full_and_blocked_distinct(self):
        for path in (SRA_SKILL, SRA_RESOURCE, SRA_FIDELITY):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "`direct`",
                "`lite`",
                "`full`",
                "`blocked`",
                "Analysis-Cost",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")
        skill = SRA_SKILL.read_text(encoding="utf-8")
        self.assertIn("`auto` starts from Lite", skill)
        self.assertIn("not a third reasoning mode", skill)

    def test_candidate_horizon_and_priority_order_protect_real_priority(self):
        for path in (SRA_SKILL, SRA_RESOURCE):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "Candidate Horizon Probe",
                "current path",
                "hard gate",
                "strongest feasible alternative",
                "reserve",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

        public_text = SRA_DOC.read_text(encoding="utf-8")
        for phrase in (
            "Candidate Horizon Probe / 候选视野探针",
            "当前路径",
            "硬 Gate",
            "最强的可行替代项",
            "保留",
        ):
            self.assertIn(phrase, public_text, f"{SRA_DOC} missing {phrase!r}")

        skill = SRA_SKILL.read_text(encoding="utf-8")
        positions = [
            skill.index(f"{index}. `{name}`")
            for index, name in enumerate(
                (
                    "hard_gate",
                    "feasible_bundle",
                    "threshold_essential",
                    "direction_or_bottleneck",
                    "risk_adjusted_bundle_value",
                    "marginal_tranche_value",
                    "reserve",
                ),
                start=1,
            )
        ]
        self.assertEqual(positions, sorted(positions))

    def test_sra_models_bundles_resources_thresholds_and_future_costs(self):
        for path in (SRA_SKILL, SRA_RESOURCE):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "current minimum sufficient bundle",
                "infeasible",
                "resource",
                "meaningful",
                "fixed threshold",
                "switching_cost",
                "sunk_cost",
                "reusable_asset",
                "remaining_cost",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

        public_text = SRA_DOC.read_text(encoding="utf-8")
        for phrase in (
            "Current Minimum Sufficient Bundle / 当前最小充分组合",
            "当前无可行组合",
            "下一投入批次",
            "固定门槛",
            "切换成本",
            "沉没成本",
            "可复用资产",
            "剩余成本",
        ):
            self.assertIn(phrase, public_text, f"{SRA_DOC} missing {phrase!r}")

    def test_lite_and_full_share_contraction_replenishment_core(self):
        skill = " ".join(SRA_SKILL.read_text(encoding="utf-8").split())
        for phrase in (
            "one_action",
            "one_tranche",
            "until_named_checkpoint",
            "investment ceiling",
            "reranking trigger",
            "micro-contraction",
            "micro-replenishment",
            "Resource Contraction And Replenishment",
            "partial or conditional order",
        ):
            self.assertIn(phrase, skill)

        resource = SRA_RESOURCE.read_text(encoding="utf-8")
        for phrase in (
            "Lite Mode",
            "Full Mode",
            "Micro Contraction",
            "Micro Replenishment",
            "Resource Contraction",
            "Resource Replenishment",
            "Feasibility And Dominance",
            "Full Stop",
        ):
            self.assertIn(phrase, resource)

    def test_method_boundaries_preserve_neighbor_ownership(self):
        skill = SRA_SKILL.read_text(encoding="utf-8")
        for phrase in (
            "Use `3l5s`",
            "Use `edsp`",
            "Use `sela`",
            "Use `mpg`",
            "Use `wae`",
            "Use `tvg`",
            "Anti-Spiral supplies a brake",
            "`tplan` owns Mission state",
            "Pulse arbitration",
            "continuation",
            "task mutation",
        ):
            self.assertIn(phrase, skill)

        resource = SRA_RESOURCE.read_text(encoding="utf-8")
        for phrase in (
            "minimum comparable candidate card",
            "Do not oscillate between methods without new evidence",
            "SRA does not redesign the carrier",
            "narrow `allocation_review` hook",
        ):
            self.assertIn(phrase, resource)

    def test_neighbor_surfaces_preserve_bidirectional_sra_handshakes(self):
        checks = {
            THREEL5S_SKILL: (
                "multiple sufficiently defined problems or tasks compete",
                "3L5S makes candidates judgeable, SRA allocates them",
            ),
            SELA_SKILL: (
                "long-term direction is already sufficiently accepted",
                "use SRA for that current allocation",
            ),
            MPG_SKILL: (
                "multiple problems, tasks, objectives, or bundles compete",
                "MPG owns carrier and path posture for one selected mainline",
            ),
            TVG_SKILL: (
                "TVG owns value gain inside one bounded artifact",
                "use SRA for the cross-task allocation",
            ),
            TPLAN_SKILL: (
                "SRA may judge cross-task resource allocation",
                "TPlan retains state, Pulse, continuation, authority, recovery, and mutation",
            ),
            ANTI_SPIRAL_DOC: (
                "`SRA` 在刹车释放出资源",
                "这是一次交接，不形成相互递归调用",
            ),
        }
        for path, phrases in checks.items():
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_pressure_tests_cover_positive_boundary_and_adversarial_cases(self):
        text = SRA_PRESSURE.read_text(encoding="utf-8")
        for phrase in (
            "Lite Positive Cases",
            "Full Positive Cases",
            "Boundary Cases",
            "Adversarial Cases",
            "Scenario 1: Release Threshold Versus Visual Polish",
            "Scenario 6: Sprint Across Defects, Compliance, Debt, And Features",
            "Scenario 11: One Known Release Blocker",
            "Scenario 15: Selected Mainline Carrier Routes To MPG",
            "Scenario 18: Pulse Gate Arbitration Remains TPlan",
            "Scenario 20: Candidate Omission",
            "Scenario 25: No Feasible Bundle",
            "Scenario 28: Analysis Overkill",
            "Scenario 29: Reserve Option",
            "First-Release Claim Ceiling",
        ):
            self.assertIn(phrase, text)

    def test_validator_uses_shared_runtime_and_template_passes(self):
        script = SRA_VALIDATOR.read_text(encoding="utf-8")
        self.assertIn("_runtime.fidelity.core", script)
        self.assertIn("_runtime.core.report", script)
        self.assertNotIn("@dataclass", script)

        payload = json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))
        result = run_validator(payload)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("SRA Shape & Evidence Risk Report", result.stdout)
        self.assertIn("No shape or evidence risks detected", result.stdout)
        self.assertIn("agentic audit remains required", result.stdout)
        self.assertIn("does not validate priority quality", result.stdout)

    def test_direct_and_blocked_are_accepted_explicit_exits(self):
        for entry_outcome in ("direct", "blocked"):
            with self.subTest(entry_outcome=entry_outcome):
                result = run_validator(
                    {
                        "schema_version": "sra-fidelity-v0.1",
                        "method": "SRA",
                        "entry_outcome": entry_outcome,
                        "plain_language_conclusion": "Do not run an applicable SRA allocation here.",
                        "exit_reason": "The next action is unique or the allocation frame is incomplete.",
                        "transfer_to": "3L5S" if entry_outcome == "blocked" else "",
                    }
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertIn(f"method exit accepted: {entry_outcome}", result.stdout)
                self.assertIn("agentic audit remains required", result.stdout)

    def test_missing_base_move_fails_lite_validation(self):
        payload = json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))
        del payload["required_judgment_moves"]["candidate_horizon_probe"]

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "missing required judgment move: candidate_horizon_probe", result.stdout
        )

    def test_lite_requires_micro_contraction_and_replenishment(self):
        for move_name in ("contraction", "replenishment"):
            with self.subTest(move_name=move_name):
                payload = json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))
                del payload["required_judgment_moves"][move_name]

                result = run_validator(payload)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    f"missing required judgment move: {move_name}", result.stdout
                )

        payload = json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))
        del payload["lite_decision"]["current_floor"]
        result = run_validator(payload)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing field: lite_decision.current_floor", result.stdout)

    def test_full_requires_full_specific_moves_and_decision_carrier(self):
        payload = json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))
        payload["entry_outcome"] = "full"
        payload["allocation_action"] = "allocate"
        payload.pop("lite_decision")

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "missing required judgment move: minimum_sufficient_bundle", result.stdout
        )
        self.assertIn("missing required judgment move: resource_vector", result.stdout)
        self.assertIn("missing field: full_decision", result.stdout)

        passing = run_validator(make_full_payload())
        self.assertEqual(passing.returncode, 0, passing.stderr + passing.stdout)

    def test_lite_rejects_open_ended_authorization_enum(self):
        payload = json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))
        payload["lite_decision"]["authorization_horizon"] = "until_done"

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lite_decision.authorization_horizon unsupported", result.stdout)

    def test_lite_requires_bounded_candidate_horizon_carrier(self):
        payload = json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))
        payload["lite_decision"]["considered_candidates"] = ["Current path only"]

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "lite_decision.considered_candidates must be a list of two to four non-empty strings",
            result.stdout,
        )

    def test_full_rejects_inconsistent_outcome_and_malformed_bundle(self):
        payload = make_full_payload()
        payload["allocation_action"] = "conditional"
        payload["full_decision"]["candidate_bundles"][0]["status"] = "unknown"
        payload["full_decision"]["candidate_bundles"][1] = {}

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("allocation_action must match full_decision.allocation_outcome", result.stdout)
        self.assertIn("full_decision.candidate_bundles[0].status unsupported", result.stdout)
        self.assertIn("missing field: full_decision.candidate_bundles[1].bundle_id", result.stdout)
        self.assertIn("missing field: full_decision.candidate_bundles[1].status", result.stdout)

    def test_full_rejects_empty_recoverability_carriers(self):
        payload = make_full_payload()
        payload["full_decision"]["rerank_triggers"] = []
        payload["full_decision"]["decision_lifetime"] = ""

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("full_decision.rerank_triggers must be a non-empty list", result.stdout)
        self.assertIn("full_decision.decision_lifetime must be a non-empty string", result.stdout)

    def test_invalid_json_is_reported_without_traceback(self):
        result = run_validator_with_raw_text('{"schema_version": ')

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid JSON at", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr + result.stdout)

    def test_shape_pass_never_claims_priority_correctness(self):
        fidelity = SRA_FIDELITY.read_text(encoding="utf-8")
        for phrase in (
            "shape pass is not semantic approval",
            "cannot judge priority quality",
            "does not support claims that SRA always finds the correct priority",
        ):
            self.assertIn(phrase, fidelity)

        result = run_validator(copy.deepcopy(json.loads(SRA_TEMPLATE.read_text(encoding="utf-8"))))
        self.assertNotIn("semantic approval", result.stdout)
        self.assertNotIn("priority is correct", result.stdout)


if __name__ == "__main__":
    unittest.main()
