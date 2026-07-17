import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"
DEVELOPMENT_PATH = BETA_ROOT / "fixtures" / "development-cases.jsonl"
SEALED_PATH = BETA_ROOT / "fixtures" / "sealed-shadow-index.json"
REPLAY_PATH = BETA_ROOT / "fixtures" / "real-task-replay-index.json"
PUBLIC_PATH = REPO / "tests" / "judgment_benchmark_50_cases.jsonl"
LINTER_PATH = BETA_ROOT / "runtime" / "lint-case-matrix.py"
BUILDER_PATH = BETA_ROOT / "runtime" / "build-case-matrix.py"
SCHEMA_PATH = BETA_ROOT / "case-matrix.schema.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoCaseMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.linter = load_module("beta2_case_matrix_linter", LINTER_PATH)
        cls.builder = load_module("beta2_case_matrix_builder", BUILDER_PATH)
        cls.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        cls.development_ids = cls.linter.load_jsonl_ids(DEVELOPMENT_PATH)
        cls.public_ids = cls.linter.load_jsonl_ids(PUBLIC_PATH)
        cls.sealed_receipts = cls.linter._index_receipts(
            json.loads(SEALED_PATH.read_text(encoding="utf-8")), "sealed index"
        )
        cls.replay_receipts = cls.linter._index_receipts(
            json.loads(REPLAY_PATH.read_text(encoding="utf-8")), "replay index"
        )

    def validate(self, matrix: dict) -> dict:
        return self.linter.validate(
            matrix,
            development_ids=self.development_ids,
            public_ids=self.public_ids,
            sealed_receipts=self.sealed_receipts,
            replay_receipts=self.replay_receipts,
        )

    def test_checked_matrix_is_deterministically_generated(self) -> None:
        self.assertEqual(self.matrix, self.builder.payload())

    def test_matrix_covers_required_cells_and_positive_3l5s_tplan(self) -> None:
        report = self.validate(self.matrix)

        self.assertEqual(report["status"], "valid")
        self.assertEqual(report["case_count"], 31)
        self.assertGreaterEqual(report["negative_control_count"] / report["case_count"], 0.25)
        self.assertEqual(report["multi_obligation_case_count"], 3)
        for dimension in report["coverage"].values():
            self.assertEqual(dimension["missing"], [])
        positives = {
            case["expected_execution_owner"]
            for case in self.matrix["cases"]
            if case["case_type"] == "positive"
        }
        self.assertIn("3l5s", positives)
        self.assertIn("tplan", positives)

    def test_every_case_declares_scoring_load_lifecycle_and_contamination_fields(self) -> None:
        scoring_fields = {
            "expected_execution_owner",
            "accepted_execution_owners",
            "expected_primitive_obligations",
            "required_visible_action",
            "required_skill_loads",
            "allowed_skill_loads",
            "stay_asleep_expected",
            "expected_lifecycle_events",
            "contamination_risk",
        }
        for case in self.matrix["cases"]:
            with self.subTest(case_id=case["case_id"]):
                self.assertFalse(scoring_fields - case.keys())
                self.assertTrue(
                    set(case["required_skill_loads"]).issubset(case["allowed_skill_loads"])
                )

    def test_public_development_sealed_and_replay_sources_cannot_be_interchanged(self) -> None:
        for case in self.matrix["cases"]:
            source = case["source"]
            with self.subTest(case_id=case["case_id"]):
                if case["provenance"] in {"public-regression", "development"}:
                    self.assertTrue(source["implementation_visible"])
                    self.assertEqual(source["run_eligibility"], "eligible")
                    self.assertIsNone(source["receipt_sha256"])
                else:
                    self.assertFalse(source["implementation_visible"])
                    self.assertIsNotNone(source["receipt_sha256"])

        mutated = copy.deepcopy(self.matrix)
        public = next(case for case in mutated["cases"] if case["provenance"] == "public-regression")
        public["provenance"] = "sealed-shadow"
        public["source"]["implementation_visible"] = False
        public["source"]["run_eligibility"] = "requires-custodian-attestation"
        public["source"]["receipt_sha256"] = "0" * 64
        with self.assertRaisesRegex(self.linter.MatrixError, "sealed receipt"):
            self.validate(mutated)

    def test_linter_rejects_coverage_gaps_and_embedded_restricted_content(self) -> None:
        no_tvg = copy.deepcopy(self.matrix)
        no_tvg["cases"] = [
            case for case in no_tvg["cases"] if case["expected_execution_owner"] != "tvg"
        ]
        with self.assertRaisesRegex(self.linter.MatrixError, "coverage gaps"):
            self.validate(no_tvg)

        exposed = copy.deepcopy(self.matrix)
        sealed = next(case for case in exposed["cases"] if case["provenance"] == "sealed-shadow")
        sealed["source"]["prompt"] = "this must never enter the matrix"
        with self.assertRaisesRegex(self.linter.MatrixError, "embeds source content"):
            self.validate(exposed)

    def test_linter_rejects_invalid_negative_control_or_load_contract(self) -> None:
        invalid = copy.deepcopy(self.matrix)
        negative = next(case for case in invalid["cases"] if case["case_type"] == "negative_control")
        negative["required_skill_loads"] = ["using-mindthus"]
        negative["allowed_skill_loads"] = ["using-mindthus"]
        with self.assertRaisesRegex(self.linter.MatrixError, "must stay asleep"):
            self.validate(invalid)

        invalid = copy.deepcopy(self.matrix)
        invalid["cases"][0]["required_skill_loads"] = ["edsp"]
        invalid["cases"][0]["allowed_skill_loads"] = []
        with self.assertRaisesRegex(self.linter.MatrixError, "subset"):
            self.validate(invalid)

    def test_cli_report_does_not_read_or_claim_sealed_prompt_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            result = subprocess.run(
                ["python3", str(LINTER_PATH), "--report", str(report_path)],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertFalse(report["sealed_or_replay_prompt_content_read"])
        self.assertIn("structural coverage only", report["claim_boundary"])
        self.assertEqual(report["run_eligibility_counts"]["requires-user-authorization"], 2)

    def test_schema_is_closed_and_versions_case_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["$defs"]["case"]["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "mindthus-beta2-case-matrix-v0.1",
        )


if __name__ == "__main__":
    unittest.main()
