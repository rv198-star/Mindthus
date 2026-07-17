import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
LOCK_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.lock.json"
BUILDER_PATH = BETA_ROOT / "runtime" / "build-evaluation-protocol-v0.4.py"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.4.py"
PRIOR_VALIDATORS = (
    BETA_ROOT / "runtime" / "freeze-evaluation-protocol.py",
    BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.2.py",
    BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.3.py",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoEvidenceHonestProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_module("beta2_protocol_v04_builder", BUILDER_PATH)
        cls.validator = load_module("beta2_protocol_v04_validator", VALIDATOR_PATH)
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    def test_prior_locks_remain_valid(self) -> None:
        for validator in PRIOR_VALIDATORS:
            with self.subTest(validator=validator.name):
                result = subprocess.run(
                    ["python3", str(validator), "validate"],
                    cwd=REPO,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_checked_protocol_matches_builder_except_parent_receipt(self) -> None:
        rebuilt = self.builder.payload()
        rebuilt["freeze"]["source_parent_commit"] = self.protocol["freeze"][
            "source_parent_commit"
        ]
        self.assertEqual(rebuilt, self.protocol)

    def test_v04_debits_prior_output_and_separates_evidence_classes(self) -> None:
        report = self.validator.validate_protocol(self.protocol)
        self.assertEqual(report["planned_generation_cells"], 225)
        self.assertEqual(report["planned_judge_records"], 450)
        proposed = self.protocol["authorization_parameters"]["proposed_authorization"]
        self.assertEqual(proposed["maximum_generation_calls"], 239)
        self.assertEqual(proposed["maximum_judge_calls"], 480)
        self.assertEqual(proposed["token_or_cost_budget"]["maximum"], 21951744)
        self.assertTrue(
            self.protocol["freeze"]["semantic_model_output_generated_before_freeze"]
        )
        self.assertFalse(
            self.protocol["freeze"][
                "semantic_model_output_generated_under_v0_4_before_freeze"
            ]
        )
        primary = {item["id"]: item for item in self.protocol["primary_endpoints"]}
        self.assertIn("first_observable_action_latency", primary)
        self.assertNotIn("first_useful_action_latency", primary)
        secondary = {item["id"]: item for item in self.protocol["secondary_endpoints"]}
        self.assertEqual(
            secondary["native_first_useful_action_latency"]["missing_policy"],
            "block-endpoint",
        )

    def test_validator_rejects_provenance_lifecycle_or_budget_drift(self) -> None:
        mutations = (
            (
                "timing-provenance",
                lambda item: next(
                    endpoint
                    for endpoint in item["primary_endpoints"]
                    if endpoint["id"] == "first_observable_action_latency"
                )["required_evidence"][0].update(allowed_provenance=["native"]),
            ),
            (
                "lifecycle-claim",
                lambda item: item["execution_design"]["host_lifecycle_scope"].update(
                    nonstartup_host_fidelity_claim="allowed"
                ),
            ),
            (
                "prior-accounting",
                lambda item: item["execution_design"][
                    "prior_protocol_output_accounting"
                ].update(counted_tokens=0),
            ),
            (
                "budget-expansion",
                lambda item: item["authorization_parameters"]["cumulative_authority"].update(
                    budget_expansion=True
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(self.protocol)
                mutate(changed)
                with self.assertRaises(self.validator.ProtocolError):
                    self.validator.validate_protocol(changed)

    def test_freeze_is_non_overwritable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            protocol_path = Path(tmp) / "protocol.json"
            lock_path = Path(tmp) / "lock.json"
            protocol_path.write_text(
                json.dumps(self.protocol, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            first = subprocess.run(
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
            self.assertEqual(first.returncode, 0, first.stderr)
            second = subprocess.run(
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
            self.assertEqual(second.returncode, 2)

    def test_official_lock_validates_after_freeze(self) -> None:
        if not LOCK_PATH.is_file():
            self.skipTest("official v0.4 lock is created only after pre-freeze tests pass")
        result = subprocess.run(
            ["python3", str(VALIDATOR_PATH), "validate"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
