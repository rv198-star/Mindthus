import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
PROTOCOL_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.2.json"
LOCK_PATH = BETA_ROOT / "protocols" / "evaluation-protocol-v0.2.lock.json"
BUILDER_PATH = BETA_ROOT / "runtime" / "build-evaluation-protocol-v0.2.py"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.2.py"
V01_VALIDATOR_PATH = BETA_ROOT / "runtime" / "freeze-evaluation-protocol.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoCodexOnlyProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_module("beta2_protocol_v02_builder", BUILDER_PATH)
        cls.validator = load_module("beta2_protocol_v02_validator", VALIDATOR_PATH)
        cls.protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))

    def test_v01_lock_remains_valid_under_its_immutable_validator(self) -> None:
        result = subprocess.run(
            ["python3", str(V01_VALIDATOR_PATH), "validate"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_checked_protocol_matches_v02_builder_except_parent_receipt(self) -> None:
        rebuilt = self.builder.payload()
        rebuilt["freeze"]["source_parent_commit"] = self.protocol["freeze"][
            "source_parent_commit"
        ]
        self.assertEqual(rebuilt, self.protocol)

    def test_v02_is_codex_only_with_frozen_cardinality_and_claim_ceiling(self) -> None:
        report = self.validator.validate_protocol(self.protocol)
        self.assertEqual(report["protocol_version"], "0.2")
        self.assertEqual(report["supported_surfaces"], ["codex-plugin"])
        self.assertEqual(report["planned_generation_cells"], 261)
        self.assertEqual(report["planned_judge_records"], 522)
        self.assertEqual(
            self.protocol["execution_design"]["cross_host_generalization"],
            "forbidden",
        )
        proposed = self.protocol["authorization_parameters"]["proposed_authorization"]
        self.assertEqual(
            proposed["generator_model_by_host"]["codex-plugin"]["model_id"],
            "gpt-5.6-sol",
        )
        self.assertEqual(
            proposed["judge_model_and_reasoning"]["reasoning_effort"],
            "xhigh",
        )
        self.assertEqual(proposed["maximum_generation_calls"], 276)
        self.assertEqual(proposed["maximum_judge_calls"], 552)
        self.assertEqual(proposed["token_or_cost_budget"]["maximum"], 25000000)

    def test_validator_rejects_host_model_budget_or_claim_drift(self) -> None:
        mutations = (
            ("host", lambda item: item["workload"].update(host_surfaces=["codex-plugin", "claude-plugin"])),
            (
                "model",
                lambda item: item["authorization_parameters"]["proposed_authorization"][
                    "generator_model_by_host"
                ]["codex-plugin"].update(model_id="other-model"),
            ),
            (
                "budget",
                lambda item: item["authorization_parameters"]["proposed_authorization"].update(
                    maximum_generation_calls=277
                ),
            ),
            (
                "claim",
                lambda item: item["execution_design"].update(cross_host_generalization="allowed"),
            ),
            (
                "validator-dependency",
                lambda item: item.update(
                    dependencies=[
                        dependency
                        for dependency in item["dependencies"]
                        if dependency["id"] != "base_protocol_validator"
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

    def test_official_v02_lock_validates_after_freeze(self) -> None:
        if not LOCK_PATH.is_file():
            self.skipTest("official v0.2 lock is created only after pre-freeze tests pass")
        result = subprocess.run(
            ["python3", str(VALIDATOR_PATH), "validate"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
