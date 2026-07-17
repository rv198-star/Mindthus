import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.1.json"
LOCK_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.1.lock.json"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "freeze-evaluation-protocol.py"
BUILDER_PATH = BETA_ROOT / "runtime" / "build-evaluation-protocol.py"
SCHEMA_PATH = BETA_ROOT / "evaluation-protocol.schema.json"
LOCK_SCHEMA_PATH = BETA_ROOT / "protocol-lock.schema.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoEvaluationProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module("beta2_protocol_validator", VALIDATOR_PATH)
        cls.builder = load_module("beta2_protocol_builder", BUILDER_PATH)
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    def test_checked_protocol_matches_builder_except_frozen_parent_receipt(self) -> None:
        rebuilt = self.builder.payload()
        rebuilt["freeze"]["source_parent_commit"] = self.protocol["freeze"][
            "source_parent_commit"
        ]
        self.assertEqual(rebuilt, self.protocol)

    def test_protocol_resolves_arms_workload_endpoints_and_authorization_gate(self) -> None:
        report = self.validator.validate_protocol(self.protocol)

        self.assertEqual(report["status"], "protocol-valid")
        self.assertEqual(report["dependency_count"], 9)
        self.assertEqual(report["primary_endpoint_count"], 10)
        self.assertEqual(report["secondary_endpoint_count"], 8)
        self.assertEqual(report["matched_case_count"], 29)
        self.assertEqual(report["planned_generation_cells"], 522)
        self.assertEqual(
            {arm["arm_id"] for arm in self.protocol["arms"]},
            {"stable", "direct-only", "thin-kernel"},
        )
        self.assertTrue(all(arm["mutable"] is False for arm in self.protocol["arms"]))
        self.assertFalse(self.protocol["workload"]["repeat_count_is_release_proof"])
        self.assertEqual(self.protocol["authorization_parameters"]["status"], "required-before-issue-119")

    def test_quality_efficiency_and_ux_remain_separate_lines(self) -> None:
        domains = {
            endpoint["domain"]
            for endpoint in [
                *self.protocol["primary_endpoints"],
                *self.protocol["secondary_endpoints"],
            ]
        }
        self.assertIn("quality", domains)
        self.assertIn("efficiency", domains)
        self.assertIn("user-visible-interaction-cost", domains)
        self.assertNotIn("composite", domains)
        for endpoint in self.protocol["primary_endpoints"]:
            self.assertEqual(endpoint["status"], "resolved")
            self.assertIn("margin", endpoint)
            self.assertTrue(endpoint["required_evidence"])
            self.assertEqual(endpoint["missing_policy"], "veto")

    def test_validator_rejects_unresolved_endpoint_missing_margin_or_evidence(self) -> None:
        for mutation, message in (
            (("status", "todo"), "unresolved primary"),
            (("margin", None), "no margin"),
            (("required_evidence", []), "no evidence requirements"),
        ):
            with self.subTest(field=mutation[0]):
                changed = copy.deepcopy(self.protocol)
                field, value = mutation
                if value is None:
                    changed["primary_endpoints"][0].pop(field)
                else:
                    changed["primary_endpoints"][0][field] = value
                with self.assertRaisesRegex(self.validator.ProtocolError, message):
                    self.validator.validate_protocol(changed)

    def test_validator_rejects_mutable_arm_or_unauthorized_replay(self) -> None:
        mutable = copy.deepcopy(self.protocol)
        mutable["arms"][0]["mutable"] = True
        with self.assertRaisesRegex(self.validator.ProtocolError, "marked mutable"):
            self.validator.validate_protocol(mutable)

        unauthorized = copy.deepcopy(self.protocol)
        replay = unauthorized["workload"]["excluded_case_ids"].pop()
        unauthorized["workload"]["matched_case_ids"].append(replay)
        with self.assertRaisesRegex(self.validator.ProtocolError, "unauthorized replay"):
            self.validator.validate_protocol(unauthorized)

    def test_validator_rejects_dependency_drift_or_missing_veto(self) -> None:
        drift = copy.deepcopy(self.protocol)
        drift["dependencies"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(self.validator.ProtocolError, "dependency drift"):
            self.validator.validate_protocol(drift)

        no_veto = copy.deepcopy(self.protocol)
        no_veto["vetoes"] = no_veto["vetoes"][1:]
        with self.assertRaisesRegex(self.validator.ProtocolError, "required veto gaps"):
            self.validator.validate_protocol(no_veto)

    def test_freeze_is_atomic_non_overwritable_and_detects_post_freeze_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            protocol_path = root / "protocol.json"
            lock_path = root / "protocol.lock.json"
            protocol_path.write_text(
                json.dumps(self.protocol, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            frozen = subprocess.run(
                [
                    "python3",
                    str(VALIDATOR_PATH),
                    "freeze",
                    "--protocol",
                    str(protocol_path),
                    "--lock",
                    str(lock_path),
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr)
            self.assertTrue(lock_path.is_file())

            overwrite = subprocess.run(
                [
                    "python3",
                    str(VALIDATOR_PATH),
                    "freeze",
                    "--protocol",
                    str(protocol_path),
                    "--lock",
                    str(lock_path),
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(overwrite.returncode, 2)
            self.assertIn("cannot be overwritten", overwrite.stderr)

            changed = json.loads(protocol_path.read_text(encoding="utf-8"))
            changed["purpose"] += " post-freeze mutation"
            protocol_path.write_text(
                json.dumps(changed, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            detected = subprocess.run(
                [
                    "python3",
                    str(VALIDATOR_PATH),
                    "validate",
                    "--protocol",
                    str(protocol_path),
                    "--lock",
                    str(lock_path),
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertEqual(detected.returncode, 2)
            self.assertIn("post-freeze protocol edit", detected.stderr)

    def test_official_lock_validates_and_attests_no_pre_freeze_model_output(self) -> None:
        result = subprocess.run(
            ["python3", str(VALIDATOR_PATH), "validate"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "frozen-valid")
        self.assertFalse(lock["semantic_model_output_generated_before_freeze"])
        self.assertRegex(report["protocol_sha256"], r"^[0-9a-f]{64}$")

    def test_protocol_and_lock_schemas_are_closed_and_versioned(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        lock_schema = json.loads(LOCK_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(lock_schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "mindthus-beta2-evaluation-protocol-v0.1",
        )
        self.assertEqual(
            lock_schema["properties"]["schema_version"]["const"],
            "mindthus-beta2-protocol-lock-v0.1",
        )


if __name__ == "__main__":
    unittest.main()
