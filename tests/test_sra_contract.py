import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SRA = REPO / "skills" / "sra"
DESIGN = REPO / "docs" / "superpowers" / "specs" / "2026-09-03-sra-scarce-resource-allocation-design.md"
PUBLIC_METHOD = REPO / "docs" / "methodologies" / "sra.md"
PRESSURE_CASES = REPO / "tests" / "sra_pressure_tests.md"
VALIDATOR = SRA / "scripts" / "validate_sra_output.py"
TEMPLATE = SRA / "templates" / "fidelity-output.json"


class SraContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_data = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def run_validator(self, data):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sra-output.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(path)],
                cwd=REPO,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_phase1_surface_exists(self):
        expected = (
            SRA / "SKILL.md",
            SRA / "resources" / "methodology.md",
            SRA / "resources" / "fidelity-contract.md",
            SRA / "templates" / "fidelity-output.json",
            SRA / "scripts" / "validate_sra_output.py",
            PUBLIC_METHOD,
            DESIGN,
            PRESSURE_CASES,
        )
        for path in expected:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"missing SRA Phase 1 surface: {path}")

    def test_canonical_surfaces_share_the_contraction_replenishment_core(self):
        design = DESIGN.read_text(encoding="utf-8")
        skill = (SRA / "SKILL.md").read_text(encoding="utf-8")
        methodology = (SRA / "resources" / "methodology.md").read_text(encoding="utf-8")
        public = PUBLIC_METHOD.read_text(encoding="utf-8")

        for name, text in (
            ("design", design),
            ("skill", skill),
            ("methodology", methodology),
            ("public", public),
        ):
            with self.subTest(surface=name):
                self.assertIn("收缩找底座，回补定增量", text)
                self.assertNotIn("## Lite Mode", text)
                self.assertNotIn("## Full Mode", text)
                self.assertNotIn("## Priority Order", text)

        self.assertLess(design.index("### 2. Contraction"), design.index("### 4. Replenishment"))
        self.assertLess(skill.index("4. **Contract.**"), skill.index("7. **Replenish.**"))
        self.assertLess(
            methodology.index("## 第四步：资源收缩"),
            methodology.index("## 第六步：资源回补"),
        )
        self.assertLess(public.index("### 4. 做资源收缩"), public.index("### 6. 做资源回补"))

    def test_minimum_is_discovered_only_after_contraction(self):
        contract = (SRA / "resources" / "fidelity-contract.md").read_text(encoding="utf-8")
        validator = VALIDATOR.read_text(encoding="utf-8")
        skill = (SRA / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "target-reaching bundle hypothesis",
            "current floor bundle",
            "post_contraction",
        ):
            self.assertTrue(
                phrase in contract or phrase in skill,
                f"missing canonical floor-discovery phrase: {phrase}",
            )
        self.assertIn('floor_bundle_basis") != "post_contraction"', validator)
        self.assertIn('target_held_constant") is not True', validator)

    def test_logical_layers_are_not_one_universal_priority_ladder(self):
        skill = (SRA / "SKILL.md").read_text(encoding="utf-8")
        design = DESIGN.read_text(encoding="utf-8")
        for text in (skill, design):
            for phrase in (
                "qualify",
                "sequence",
                "describe",
                "select",
                "allocates the next tranche",
            ):
                self.assertIn(phrase, text)
        self.assertIn("Do not collapse these into one score", skill)
        self.assertIn("must not be flattened into one priority score", design)

    def test_passing_template_validates_with_explicit_truth_boundary(self):
        result = self.run_validator(self.template_data)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SRA Shape & Evidence Risk Report", result.stdout)
        self.assertIn("No shape or evidence risks detected.", result.stdout)
        self.assertIn("does not validate allocation semantic truth", result.stdout)

    def test_direct_execution_uses_an_accepted_method_exit(self):
        data = {
            "schema_version": "sra-fidelity-v0.1",
            "method": "SRA",
            "applicability": "not_applicable",
            "plain_language_conclusion": "Execute the only known release blocker directly.",
            "exit_reason": "There is no competing use of the same scarce resource.",
        }
        result = self.run_validator(data)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("method exit accepted: not_applicable", result.stdout)

    def test_missing_contraction_is_blocked(self):
        data = copy.deepcopy(self.template_data)
        del data["allocation_trace"]["contraction"]
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing-contraction", result.stdout)

    def test_missing_replenishment_is_blocked(self):
        data = copy.deepcopy(self.template_data)
        del data["allocation_trace"]["replenishment"]
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing-replenishment", result.stdout)

    def test_predeclared_floor_basis_is_blocked(self):
        data = copy.deepcopy(self.template_data)
        data["allocation_trace"]["contraction"]["floor_bundle_basis"] = "predeclared_minimum"
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid-floor-bundle-basis", result.stdout)

    def test_target_change_during_contraction_is_blocked(self):
        data = copy.deepcopy(self.template_data)
        data["allocation_trace"]["contraction"]["target_held_constant"] = False
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target-not-held-constant", result.stdout)

    def test_bundle_hypothesis_cannot_call_itself_minimum(self):
        data = copy.deepcopy(self.template_data)
        data["allocation_trace"]["bundle_hypotheses"][0]["label"] = "minimum sufficient bundle"
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("predeclared-minimum-bundle", result.stdout)

    def test_action_posture_and_trace_outcome_must_match(self):
        data = copy.deepcopy(self.template_data)
        data["action_posture"] = "conditional"
        result = self.run_validator(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outcome-posture-mismatch", result.stdout)

    def test_pressure_surface_covers_positive_boundary_adversarial_and_regression_cases(self):
        text = PRESSURE_CASES.read_text(encoding="utf-8")
        expected_ids = (
            "SRA-P01",
            "SRA-P02",
            "SRA-P03",
            "SRA-P04",
            "SRA-P05",
            "SRA-B01",
            "SRA-B02",
            "SRA-B03",
            "SRA-B04",
            "SRA-B05",
            "SRA-B06",
            "SRA-B07",
            "SRA-B08",
            "SRA-B09",
            "SRA-B10",
            "SRA-A01",
            "SRA-A02",
            "SRA-A03",
            "SRA-A04",
            "SRA-A05",
            "SRA-A06",
            "SRA-A07",
            "SRA-A08",
            "SRA-A09",
            "SRA-A10",
            "SRA-R01",
            "SRA-R02",
            "SRA-R03",
            "SRA-R04",
            "SRA-R05",
            "SRA-R06",
        )
        for case_id in expected_ids:
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, text)

    def test_shape_validation_never_claims_allocation_quality(self):
        contract = (SRA / "resources" / "fidelity-contract.md").read_text(encoding="utf-8")
        validator = VALIDATOR.read_text(encoding="utf-8")
        pressure = PRESSURE_CASES.read_text(encoding="utf-8")
        self.assertRegex(contract, r"does\s+not prove")
        self.assertIn("cannot decide", validator)
        self.assertIn("do not prove universally correct priority", pressure)
        self.assertNotIn("optimal allocation approval", validator)

    def test_tplan_integration_remains_outside_phase1(self):
        design = DESIGN.read_text(encoding="utf-8")
        skill = (SRA / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("separate follow-up", design)
        self.assertIn("does not replace TPlan `selection`", design)
        self.assertIn("TPlan owns Mission state", skill)


if __name__ == "__main__":
    unittest.main()
