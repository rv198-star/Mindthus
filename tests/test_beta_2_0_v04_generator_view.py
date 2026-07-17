import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-generator-view.1.json"
)
LOCK = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-generator-view.1.lock.json"
)
AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-generator-view.1.json"
)
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
BASE_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-evidence-view.1.json"
)
FREEZER = RUNTIME_ROOT / "freeze-evaluation-generator-view-v0.4.py"
AUTHORIZATION_VALIDATOR = (
    RUNTIME_ROOT / "validate-execution-authorization-v0.4-generator-view.py"
)
RESOURCE_VIEW = RUNTIME_ROOT / "generator_resource_view_v04.py"
RUNNER = RUNTIME_ROOT / "run_real_codex_evaluation_v04_generator_view.py"
SOURCE_RUN = (
    REPO
    / ".tplan"
    / "missions"
    / "mindthus-beta2-evaluation"
    / "artifacts"
    / "real-v04-evaluation-a6e9da7e"
    / "run"
)
SOURCE_ARMS = SOURCE_RUN.parent / "arms"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BetaTwoV04GeneratorViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resource = load_module("beta2_generator_resource_view", RESOURCE_VIEW)
        cls.freezer = load_module("beta2_generator_view_freezer", FREEZER)
        cls.authorization_validator = load_module(
            "beta2_generator_view_authorization_validator", AUTHORIZATION_VALIDATOR
        )
        cls.runner = load_module("beta2_generator_view_runner", RUNNER)
        cls.protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))

    def classify(self, command: str) -> list[str]:
        return self.resource.command_violations(
            command,
            active_package_root="/run/arms/stable/package",
            active_execution_root="/run/arms/stable/project",
            forbidden_path_fragments=(
                "/run",
                "/run/arms/direct-only",
                "/control/judge-rubric.json",
            ),
        )

    def test_protocol_is_narrow_and_preserves_budget(self) -> None:
        report = self.freezer.validate_protocol(self.protocol)
        self.assertEqual(report["amendment_id"], "0.4-generator-view.1")
        self.assertEqual(report["retained_cells"], 73)
        self.assertEqual(report["retained_generation_attempts"], 75)
        self.assertEqual(report["promotion_model_calls"], 0)
        self.assertEqual(report["measured_token_ceiling"], 17_599_744)
        config = self.protocol["generator_resource_view"]
        self.assertFalse(config["answer_mutation_allowed"])
        self.assertFalse(config["target_retry_allowed"])
        self.assertFalse(config["workload_change_allowed"])
        self.assertFalse(config["threshold_change_allowed"])
        self.assertFalse(config["budget_expansion_allowed"])

    def test_official_lock_and_authorization_validate(self) -> None:
        frozen = self.freezer.validate_lock(PROTOCOL, LOCK)
        authorized = self.authorization_validator.validate_authorization(
            AUTHORIZATION, check_runtime=False
        )
        self.assertEqual(frozen["status"], "frozen")
        self.assertEqual(authorized["status"], "authorized")
        self.assertEqual(authorized["generator_view_lock_digest"], frozen["lock_digest"])
        self.assertFalse(authorized["release_preparation"])

    def test_active_roots_and_negative_selectors_are_not_reads(self) -> None:
        safe = (
            "sed -n '1,40p' /run/arms/stable/package/skills/tplan/SKILL.md",
            "cd /run/arms/stable/project && pwd",
            "rg --files -g '!*Superpowers*' -g '!**/judge*'",
            "find . -iname '*superpowers*' -prune -o -print",
        )
        for command in safe:
            with self.subTest(command=command):
                self.assertEqual(self.classify(command), [])

    def test_real_forbidden_reads_and_lookalike_roots_remain_blocked(self) -> None:
        unsafe = (
            "cat /run/arms/direct-only/package/skills/3l5s/SKILL.md",
            "cat /control/judge-rubric.json",
            "cat ../evaluation-case-matrix.json",
            "cat /run/arms/stable/package-copy/skills/tplan/SKILL.md",
            "rg --files -g '*Superpowers*'",
            "find . -iname '*superpowers*' -print",
            "find . -iname '*superpowers*' -prune -exec cat '{}' ';'",
            "rg --files -g '!Superpowers*' | xargs cat Superpowers/secret.md",
        )
        for command in unsafe:
            with self.subTest(command=command):
                self.assertTrue(self.classify(command))

    def test_find_prune_exception_is_conservative(self) -> None:
        self.assertEqual(
            self.classify("find . -iname '*superpowers*' -prune -o -print"), []
        )
        self.assertIn(
            "forbidden-resource-reference",
            self.classify("find . -iname '*superpowers*' -prune -exec cat '{}' ';'"),
        )
        self.assertIn(
            "forbidden-resource-reference",
            self.classify("tool -g '!Superpowers*'"),
        )

    def test_findings_disclose_hashes_not_command_text(self) -> None:
        secret = "cat /control/judge-rubric.json"
        findings = self.resource.contaminated_commands(
            [secret],
            active_package_root="/run/arms/stable/package",
            active_execution_root="/run/arms/stable/project",
            forbidden_path_fragments=("/run", "/control/judge-rubric.json"),
        )
        self.assertEqual(len(findings), 1)
        self.assertNotIn(secret, json.dumps(findings))
        self.assertEqual(len(findings[0]["command_sha256"]), 64)

    @unittest.skipUnless(
        SOURCE_RUN.is_dir() and SOURCE_ARMS.is_dir(),
        "local retained v0.4 evidence and arms are unavailable",
    )
    def test_diagnosed_commands_are_safe_under_corrected_view(self) -> None:
        manifests = {
            arm: json.loads(
                (SOURCE_ARMS / arm / "sealed-arm.json").read_text(encoding="utf-8")
            )
            for arm in ("stable", "direct-only", "thin-kernel")
        }
        attempt = (
            SOURCE_RUN
            / "generation-attempts"
            / self.runner.TARGET_CELL_ID
            / "attempt-01"
            / "events.jsonl"
        )
        commands = self.runner.base.event_evidence(
            attempt.read_text(encoding="utf-8")
        )["loaded_commands"]
        forbidden = self.runner._forbidden_fragments(SOURCE_RUN, manifests, "stable")
        original_hits = [
            command
            for command in commands
            if self.runner.base.FORBIDDEN_GENERATOR_COMMAND.search(command)
            or "../" in command
            or any(fragment in command for fragment in forbidden)
        ]
        corrected = self.resource.contaminated_commands(
            commands,
            active_package_root=manifests["stable"]["package"]["root"],
            active_execution_root=manifests["stable"]["host"]["execution_root"],
            forbidden_path_fragments=forbidden,
        )
        self.assertEqual(len(original_hits), 2)
        self.assertEqual(corrected, [])

    @unittest.skipUnless(
        SOURCE_RUN.is_dir() and SOURCE_ARMS.is_dir(),
        "local retained v0.4 evidence and arms are unavailable",
    )
    def test_bound_attempt_promotes_once_without_a_model_call(self) -> None:
        authorization = json.loads(BASE_AUTHORIZATION.read_text(encoding="utf-8"))
        protocol = json.loads(BASE_PROTOCOL.read_text(encoding="utf-8"))
        manifests = {
            arm: json.loads(
                (SOURCE_ARMS / arm / "sealed-arm.json").read_text(encoding="utf-8")
            )
            for arm in ("stable", "direct-only", "thin-kernel")
        }
        auth_report = {
            "protocol_sha256": authorization["protocol"]["sha256"],
            "generator_view_protocol_sha256": "a" * 64,
            "generator_view_lock_digest": "b" * 64,
        }
        source_receipt = {"receipt_digest": "c" * 64}
        source_attempt = (
            SOURCE_RUN / "generation-attempts" / self.runner.TARGET_CELL_ID
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            destination = out / "generation-attempts" / self.runner.TARGET_CELL_ID
            destination.parent.mkdir(parents=True)
            shutil.copytree(source_attempt, destination)
            first = self.runner.promote_target_attempt(
                out_dir=out,
                amendment=self.protocol,
                auth_report=auth_report,
                protocol=protocol,
                manifests=manifests,
                source_receipt=source_receipt,
            )
            second = self.runner.promote_target_attempt(
                out_dir=out,
                amendment=self.protocol,
                auth_report=auth_report,
                protocol=protocol,
                manifests=manifests,
                source_receipt=source_receipt,
            )
            self.assertEqual(first, second)
            self.assertEqual(first["counted_tokens"], 72_889)
            self.assertEqual(
                first["generator_resource_view_amendment"]["model_calls_added"], 0
            )
            self.assertEqual(
                sorted(path.name for path in destination.glob("attempt-*")),
                ["attempt-01"],
            )
            self.assertIsNotNone(
                self.runner.base.completed_cell(out, self.runner.TARGET_CELL_ID)
            )

    @unittest.skipUnless(SOURCE_RUN.is_dir(), "local retained v0.4 evidence is unavailable")
    def test_retained_source_sets_match_frozen_receipts(self) -> None:
        source = self.protocol["retained_source_run"]
        snapshot = (
            SOURCE_RUN
            / "recovery"
            / "0.4-generator-view.1"
            / "pre-amendment"
            / "receipt.json"
        )
        sets = (
            json.loads(snapshot.read_text(encoding="utf-8"))
            if snapshot.is_file()
            else self.runner._source_sets(SOURCE_RUN)
        )
        for name in (
            "cells",
            "generation_attempts",
            "judge_attempts",
            "judge_records",
            "judge_inputs",
            "blinded_views",
        ):
            self.assertEqual(len(sets[name]), source[f"{name}_count"])
            self.assertEqual(
                self.runner.base.canonical_sha256(sets[name]),
                source[f"{name}_set_digest"],
            )


if __name__ == "__main__":
    unittest.main()
