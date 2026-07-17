import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.3.py"
AUTHORIZATION_PATH = BETA_ROOT / "authorizations" / "issue-119-codex-v0.3.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BetaTwoVisibleCaseAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module("beta2_visible_authorization", VALIDATOR_PATH)
        cls.authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))

    def write_fixture(self, root: Path, authorization: dict) -> Path:
        path = root / "authorization.json"
        path.write_text(
            json.dumps(authorization, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_official_visible_case_authorization_passes(self) -> None:
        report = self.validator.validate_authorization(AUTHORIZATION_PATH)
        self.assertEqual(report["status"], "authorized")
        self.assertEqual(report["matched_case_count"], 25)
        self.assertEqual(report["included_sealed_case_count"], 0)
        self.assertEqual(report["maximum_generation_calls"], 240)
        self.assertEqual(report["maximum_judge_calls"], 480)
        self.assertEqual(
            report["delegated_digest_binding"]["mode"],
            "delegated-first-valid-frozen-v0.3",
        )

    def test_model_budget_or_protocol_digest_drift_fails_closed(self) -> None:
        mutations = (
            (
                "model",
                lambda item: item["generator_model_by_host"]["codex-plugin"].update(
                    model_id="other-model"
                ),
                "configuration differs",
            ),
            (
                "budget",
                lambda item: item.update(maximum_generation_calls=241),
                "configuration differs",
            ),
            (
                "protocol",
                lambda item: item["protocol"].update(sha256="0" * 64),
                "protocol path or digest differs",
            ),
        )
        for label, mutate, message in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                changed = copy.deepcopy(self.authorization)
                mutate(changed)
                path = self.write_fixture(Path(tmp), changed)
                with self.assertRaisesRegex(self.validator.AuthorizationError, message):
                    self.validator.validate_authorization(path)

    def test_case_scope_or_sealed_attestation_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            changed = copy.deepcopy(self.authorization)
            changed["case_scope"]["included_sealed_case_count"] = 1
            path = self.write_fixture(Path(tmp), changed)
            with self.assertRaisesRegex(self.validator.AuthorizationError, "case scope differs"):
                self.validator.validate_authorization(path)

            changed = copy.deepcopy(self.authorization)
            changed["sealed_case_attestation_path"] = "/tmp/not-used.json"
            path = self.write_fixture(Path(tmp), changed)
            with self.assertRaisesRegex(self.validator.AuthorizationError, "must not bind"):
                self.validator.validate_authorization(path)

    def test_delegated_binding_requires_exact_instruction_digest_and_order(self) -> None:
        mutations = (
            (
                "instruction",
                lambda item: item["human_authorization"].update(source_instruction="继续"),
                "source instruction differs",
            ),
            (
                "configuration-digest",
                lambda item: item["human_authorization"].update(
                    authorized_configuration_digest="0" * 64
                ),
                "configuration digest differs",
            ),
            (
                "binding-time",
                lambda item: item["human_authorization"]["digest_binding"].update(
                    bound_at_utc="2026-07-17T08:30:00+00:00"
                ),
                "must follow user authorization and protocol freeze",
            ),
        )
        for label, mutate, message in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                changed = copy.deepcopy(self.authorization)
                mutate(changed)
                path = self.write_fixture(Path(tmp), changed)
                with self.assertRaisesRegex(self.validator.AuthorizationError, message):
                    self.validator.validate_authorization(path)

    def test_validator_digest_is_bound_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            changed = copy.deepcopy(self.authorization)
            changed["authorization_validator_sha256"] = "0" * 64
            path = self.write_fixture(Path(tmp), changed)
            with self.assertRaisesRegex(self.validator.AuthorizationError, "validator digest differs"):
                self.validator.validate_authorization(path)


if __name__ == "__main__":
    unittest.main()
