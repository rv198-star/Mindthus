import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.3.json"
LOCK_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.3.lock.json"
BUILDER_PATH = BETA_ROOT / "runtime" / "build-evaluation-protocol-v0.3.py"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.3.py"
V01_VALIDATOR_PATH = BETA_ROOT / "runtime" / "freeze-evaluation-protocol.py"
V02_VALIDATOR_PATH = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.2.py"
SEALED_CASE_IDS = {
    "b2-shadow-owner-overlap",
    "b2-shadow-passive-intersection",
    "b2-shadow-anti-rename",
    "b2-shadow-near-negative",
}
REPLAY_CASE_IDS = {
    "b2-replay-architecture-review",
    "b2-replay-debugging-session",
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoVisibleCaseProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_module("beta2_protocol_v03_builder", BUILDER_PATH)
        cls.validator = load_module("beta2_protocol_v03_validator", VALIDATOR_PATH)
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    def test_prior_protocol_locks_remain_valid(self) -> None:
        for validator in (V01_VALIDATOR_PATH, V02_VALIDATOR_PATH):
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

    def test_v03_is_exactly_25_visible_cases_with_conservative_ceiling(self) -> None:
        report = self.validator.validate_protocol(self.protocol)
        self.assertEqual(report["protocol_version"], "0.3")
        self.assertEqual(report["matched_case_count"], 25)
        self.assertEqual(report["planned_generation_cells"], 225)
        self.assertEqual(report["planned_judge_records"], 450)
        self.assertEqual(report["claim_ceiling"], "visible-case exploratory evidence only")
        workload = self.protocol["workload"]
        self.assertFalse(SEALED_CASE_IDS & set(workload["matched_case_ids"]))
        self.assertEqual(
            set(workload["excluded_case_ids"]),
            SEALED_CASE_IDS | REPLAY_CASE_IDS,
        )
        self.assertEqual(workload["hidden_generalization_claim"], "forbidden")
        proposed = self.protocol["authorization_parameters"]["proposed_authorization"]
        self.assertEqual(proposed["maximum_generation_calls"], 240)
        self.assertEqual(proposed["maximum_judge_calls"], 480)
        self.assertEqual(proposed["token_or_cost_budget"]["maximum"], 22000000)

    def test_validator_rejects_case_visibility_budget_or_claim_drift(self) -> None:
        mutations = (
            (
                "sealed-case-included",
                lambda item: item["workload"]["matched_case_ids"].append(
                    "b2-shadow-owner-overlap"
                ),
            ),
            (
                "sealed-exclusion-missing",
                lambda item: item["workload"].update(
                    excluded_case_ids=[
                        case_id
                        for case_id in item["workload"]["excluded_case_ids"]
                        if case_id != "b2-shadow-owner-overlap"
                    ]
                ),
            ),
            (
                "blindness-claim",
                lambda item: item["workload"].update(hidden_generalization_claim="allowed"),
            ),
            (
                "custodian-restored",
                lambda item: item["execution_design"].update(
                    sealed_case_custodian_attestation_required=True
                ),
            ),
            (
                "budget",
                lambda item: item["authorization_parameters"]["proposed_authorization"].update(
                    maximum_generation_calls=241
                ),
            ),
            (
                "validator-dependency",
                lambda item: item.update(
                    dependencies=[
                        dependency
                        for dependency in item["dependencies"]
                        if dependency["id"] != "codex_protocol_v02_validator"
                    ]
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                changed = copy.deepcopy(self.protocol)
                mutate(changed)
                with self.assertRaises(self.validator.ProtocolError):
                    self.validator.validate_protocol(changed)

    def test_freeze_is_non_overwritable_and_detects_protocol_edit(self) -> None:
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
            changed = json.loads(protocol_path.read_text(encoding="utf-8"))
            changed["purpose"] += " changed"
            protocol_path.write_text(
                json.dumps(changed, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            validation = subprocess.run(
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
            self.assertEqual(validation.returncode, 2)
            self.assertIn("post-freeze protocol edit", validation.stderr)

    def test_official_v03_lock_validates_after_freeze(self) -> None:
        if not LOCK_PATH.is_file():
            self.skipTest("official v0.3 lock is created only after pre-freeze tests pass")
        result = subprocess.run(
            ["python3", str(VALIDATOR_PATH), "validate"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
