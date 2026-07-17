import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
VALIDATOR_PATH = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.4.py"
AUTHORIZATION_PATH = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    AUTHORIZATION_PATH.is_file(), "v0.4 authorization binds only after protocol freeze"
)
class BetaTwoEvidenceHonestAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_module("beta2_authorization_v04", VALIDATOR_PATH)
        cls.authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))

    def write_fixture(self, root: Path, payload: dict) -> Path:
        path = root / "authorization.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_official_authorization_passes_without_budget_expansion(self) -> None:
        report = self.validator.validate_authorization(AUTHORIZATION_PATH)
        self.assertEqual(report["status"], "authorized")
        self.assertEqual(report["maximum_generation_calls"], 239)
        self.assertEqual(report["maximum_judge_calls"], 480)
        self.assertFalse(report["cumulative_authority"]["budget_expansion"])
        self.assertFalse(report["release_preparation"])

    def test_budget_claim_or_escalation_drift_fails_closed(self) -> None:
        mutations = (
            lambda item: item["cumulative_authority"].update(budget_expansion=True),
            lambda item: item["case_scope"].update(host_session_scope="all-lifecycles"),
            lambda item: item["human_authorization"].update(must_escalate_on=[]),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as tmp:
                changed = copy.deepcopy(self.authorization)
                mutate(changed)
                path = self.write_fixture(Path(tmp), changed)
                with self.assertRaises(self.validator.AuthorizationError):
                    self.validator.validate_authorization(path)


if __name__ == "__main__":
    unittest.main()
