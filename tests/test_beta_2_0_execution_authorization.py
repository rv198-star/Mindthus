import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "validate-execution-authorization.py"
PENDING_PATH = BETA_ROOT / "authorizations" / "issue-119-codex-v0.2.pending.json"
SEALED_INDEX = BETA_ROOT / "fixtures" / "sealed-shadow-index.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoExecutionAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module("beta2_execution_authorization", VALIDATOR_PATH)
        cls.pending = json.loads(PENDING_PATH.read_text(encoding="utf-8"))

    def authorized_fixture(self, root: Path) -> tuple[Path, Path]:
        authorization = copy.deepcopy(self.pending)
        authorization["status"] = "authorized"
        authorization["blocking_requirements"] = []
        authorization["human_confirmation"] = {
            "authority": "William",
            "confirmed_protocol_digest": authorization["protocol"]["sha256"],
            "confirmed_at_utc": "2026-07-17T08:01:00+00:00",
            "source_summary": "Synthetic test confirmation.",
        }
        index = json.loads(SEALED_INDEX.read_text(encoding="utf-8"))
        bindings = []
        for item in index["cases"]:
            content_path = root / f"{item['case_id']}.json"
            content_path.write_text(
                json.dumps({"case_id": item["case_id"], "synthetic_test_only": True}) + "\n",
                encoding="utf-8",
            )
            bindings.append(
                {
                    "case_id": item["case_id"],
                    "receipt_sha256": item["receipt_sha256"],
                    "sealed_content_path": str(content_path),
                    "sealed_content_sha256": hashlib.sha256(content_path.read_bytes()).hexdigest(),
                }
            )
        attestation = {
            "schema_version": "mindthus-beta2-sealed-case-attestation-v0.1",
            "custodian_id": "Independent synthetic custodian",
            "independent_from": [
                "arm-implementation",
                "generator-execution",
                "judge-evaluation",
            ],
            "attested_at_utc": "2026-07-17T08:00:00+00:00",
            "content_absent_from_implementation_repository": True,
            "content_not_disclosed_to_arm_implementation": True,
            "same_content_across_arms": True,
            "judge_blinding_preserved": True,
            "case_bindings": bindings,
        }
        attestation["attestation_digest"] = self.validator.canonical_sha256(attestation)
        attestation_path = root / "attestation.json"
        attestation_path.write_text(
            json.dumps(attestation, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        authorization["sealed_case_attestation_path"] = str(attestation_path)
        authorization_path = root / "authorization.json"
        authorization_path.write_text(
            json.dumps(authorization, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return authorization_path, attestation_path

    def test_official_packet_is_blocked_on_exact_digest_confirmation_and_custodian(self) -> None:
        result = subprocess.run(
            ["python3", str(VALIDATOR_PATH)],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "blocked")
        self.assertIn("post-freeze human confirmation", report["reason"])
        self.assertIn("independent custodian", report["reason"])

    def test_complete_external_attestation_and_exact_confirmation_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            authorization_path, _ = self.authorized_fixture(Path(tmp))
            report = self.validator.validate_authorization(authorization_path)
            self.assertEqual(report["status"], "authorized")
            self.assertEqual(report["maximum_generation_calls"], 276)
            self.assertEqual(report["maximum_judge_calls"], 552)
            self.assertEqual(report["sealed_case_attestation"]["sealed_case_count"], 4)

    def test_custodian_cannot_be_the_run_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            authorization_path, attestation_path = self.authorized_fixture(Path(tmp))
            attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
            attestation["custodian_id"] = "William"
            attestation.pop("attestation_digest")
            attestation["attestation_digest"] = self.validator.canonical_sha256(attestation)
            attestation_path.write_text(
                json.dumps(attestation, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.validator.AuthorizationError, "not independent"):
                self.validator.validate_authorization(authorization_path)

    def test_content_digest_or_timestamp_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            authorization_path, attestation_path = self.authorized_fixture(root)
            attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
            content_path = Path(attestation["case_bindings"][0]["sealed_content_path"])
            content_path.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(self.validator.AuthorizationError, "content digest differs"):
                self.validator.validate_authorization(authorization_path)

            authorization_path, attestation_path = self.authorized_fixture(root)
            attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
            attestation["attested_at_utc"] = "2026-07-17T08:02:00+00:00"
            attestation.pop("attestation_digest")
            attestation["attestation_digest"] = self.validator.canonical_sha256(attestation)
            attestation_path.write_text(
                json.dumps(attestation, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.validator.AuthorizationError, "after freeze and before"):
                self.validator.validate_authorization(authorization_path)

    def test_model_budget_or_validator_drift_fails_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            authorization_path, _ = self.authorized_fixture(Path(tmp))
            authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
            authorization["maximum_generation_calls"] = 277
            authorization_path.write_text(
                json.dumps(authorization, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.validator.AuthorizationError, "configuration differs"):
                self.validator.validate_authorization(authorization_path)

            authorization["maximum_generation_calls"] = 276
            authorization["authorization_validator_sha256"] = "0" * 64
            authorization_path.write_text(
                json.dumps(authorization, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(self.validator.AuthorizationError, "validator digest differs"):
                self.validator.validate_authorization(authorization_path)


if __name__ == "__main__":
    unittest.main()
