import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tests.test_judgment_benchmark_cli_runner import case_by_number, load_runner


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "scripts" / "mindthus_beta2_telemetry.py"
SCHEMA_PATH = REPO / "beta" / "2.0.0-beta.2" / "turn-telemetry.schema.json"


def load_telemetry_module():
    spec = importlib.util.spec_from_file_location("mindthus_beta2_telemetry_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def fixture_manifest(*, arm_id: str = "thin-kernel", host: str = "host-a") -> dict:
    digest = hashlib.sha256(f"{arm_id}:{host}".encode("utf-8")).hexdigest()
    hook_state = "fired" if arm_id == "thin-kernel" else "disabled"
    return {
        "schema_version": "mindthus-beta2-arm-manifest-v0.1",
        "arm_id": arm_id,
        "surface": "codex-plugin",
        "identity_digest": digest,
        "package": {"root": str(REPO)},
        "carrier": {"policy": arm_id, "hook_state": hook_state, "config": None},
        "host": {
            "runtime": {"name": host, "version": "1", "platform": "test"},
            "plugin_list": {
                "active_mindthus_coordinates": [
                    "mindthus@mindthus" if arm_id == "stable" else "mindthus-beta@mindthus-beta"
                ]
            },
        },
        "runtime_diagnostic": {
            "integrity": "ok",
            "carrier_status": "verified",
        },
    }


def complete_turn(resource: Path) -> dict:
    return {
        "usage": {
            "input_tokens": 100,
            "cached_input_tokens": 20,
            "output_tokens": 30,
            "reasoning_output_tokens": 10,
        },
        "duration_seconds": 2.0,
        "native_telemetry": {
            "first_useful_action_latency_seconds": 0.4,
            "lifecycle_event": "before-answer",
        },
        "loaded_commands": [f"Read {resource}"],
        "answer": "A bounded answer without internal terminology.",
        "agent_messages": ["Notice: a visible notice"],
        "returncode": 0,
        "timed_out": False,
    }


class BetaTwoTelemetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.telemetry = load_telemetry_module()

    def test_complete_native_record_passes_and_keeps_schema_handshakes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resource = root / "skills" / "edsp" / "SKILL.md"
            resource.parent.mkdir(parents=True)
            resource.write_text("fixture", encoding="utf-8")
            record = self.telemetry.build_turn_telemetry(
                complete_turn(resource),
                context={
                    "case_id": "beta2-complete",
                    "turn_index": 1,
                    "entry_mode": "owner-direct",
                    "execution_root": root,
                    "allowed_roots": [root],
                    "arm_manifest": fixture_manifest(),
                },
            )

        self.assertEqual(record["schema_version"], "mindthus-beta2-turn-telemetry-v0.1")
        self.assertEqual(record["evidence_gate"]["status"], "pass")
        self.assertEqual(record["measurements"]["tokens.input"]["provenance"], "native")
        self.assertEqual(record["measurements"]["skill_hops"]["value"], ["edsp"])
        resource_receipt = record["measurements"]["resource_reads"]["value"][0]
        self.assertEqual(resource_receipt["resolved_path"], str(resource.resolve()))
        self.assertEqual(record["stratum"]["arm_id"], "thin-kernel")
        self.assertEqual(record["measurements"]["arm_digest"]["value"], fixture_manifest()["identity_digest"])
        self.assertRegex(record["telemetry_digest"], r"^[0-9a-f]{64}$")

    def test_partial_and_missing_records_are_blocked_not_coerced_to_zero(self) -> None:
        partial = self.telemetry.build_turn_telemetry(
            {"duration_seconds": 1.0, "returncode": 0, "loaded_commands": []},
            context={"case_id": "beta2-partial", "entry_mode": "owner-direct"},
        )
        missing = self.telemetry.build_turn_telemetry(
            {},
            context={"case_id": "beta2-missing"},
        )

        for record in (partial, missing):
            self.assertEqual(record["evidence_gate"]["status"], "blocked")
            self.assertIsNone(record["measurements"]["tokens.input"]["value"])
            self.assertEqual(record["measurements"]["tokens.input"]["status"], "unavailable")
        self.assertEqual(
            partial["evidence_gate"]["endpoint_results"]["tokens.input"]["status"],
            "missing",
        )

    def test_runner_observed_latency_is_separate_and_optional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            resource = Path(tmp) / "fixture.md"
            resource.write_text("fixture", encoding="utf-8")
            raw = complete_turn(resource)
            baseline = self.telemetry.build_turn_telemetry(
                raw,
                context={"arm_manifest": fixture_manifest()},
            )
            self.assertNotIn(
                "first_observable_action_latency_seconds", baseline["measurements"]
            )
            raw["first_observable_action_latency_seconds"] = 0.25
            record = self.telemetry.build_turn_telemetry(
                raw,
                context={"arm_manifest": fixture_manifest()},
                required_evidence={
                    "first_observable_action_latency_seconds": ["deterministic"]
                },
            )
        observed = record["measurements"]["first_observable_action_latency_seconds"]
        self.assertEqual(observed["provenance"], "deterministic")
        self.assertEqual(observed["source"], "runner.streaming_jsonl_arrival")
        self.assertEqual(record["evidence_gate"]["status"], "pass")

    def test_thin_manifest_exposes_bound_hook_receipt_only_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            resource = Path(tmp) / "fixture.md"
            resource.write_text("fixture", encoding="utf-8")
            manifest = fixture_manifest()
            manifest["ambient_context"] = {
                "opaque": [
                    {
                        "kind": "host-hook-observation",
                        "id": "passive-kernel-session-start",
                        "sha256": "b" * 64,
                    }
                ]
            }
            record = self.telemetry.build_turn_telemetry(
                complete_turn(resource),
                context={"arm_manifest": manifest},
                required_evidence={
                    "arm.hook_observation_receipt": ["deterministic"]
                },
            )
        receipt = record["measurements"]["arm.hook_observation_receipt"]
        self.assertEqual(receipt["value"], "b" * 64)
        self.assertEqual(receipt["provenance"], "deterministic")
        self.assertEqual(record["evidence_gate"]["status"], "pass")

    def test_contradictory_record_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resource = root / "fixture.md"
            resource.write_text("fixture", encoding="utf-8")
            turn = complete_turn(resource)
            turn["usage"]["cached_input_tokens"] = 120
            turn["native_telemetry"]["first_useful_action_latency_seconds"] = 3.0
            record = self.telemetry.build_turn_telemetry(
                turn,
                context={
                    "case_id": "beta2-contradictory",
                    "entry_mode": "owner-direct",
                    "execution_root": root,
                    "allowed_roots": [root],
                    "arm_manifest": fixture_manifest(),
                },
            )

        self.assertEqual(record["evidence_gate"]["status"], "blocked")
        self.assertEqual(
            record["measurements"]["tokens.cached_input"]["status"],
            "contradictory",
        )
        self.assertEqual(
            record["measurements"]["first_useful_action_latency_seconds"]["status"],
            "contradictory",
        )

    def test_native_requirement_rejects_self_report_or_regex_derivation(self) -> None:
        result = self.telemetry.evaluate_required_evidence(
            {
                "first_useful_action_latency_seconds": {
                    "value": 0.2,
                    "provenance": "self-reported",
                    "status": "observed",
                },
                "hook_state": {
                    "value": "fired",
                    "provenance": "deterministic",
                    "status": "observed",
                },
            },
            {
                "first_useful_action_latency_seconds": ["native"],
                "hook_state": ["native"],
            },
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["endpoint_results"]["first_useful_action_latency_seconds"]["status"],
            "provenance_mismatch",
        )
        self.assertEqual(
            result["endpoint_results"]["hook_state"]["status"],
            "provenance_mismatch",
        )

    def test_summary_exposes_denominators_missing_and_exact_strata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resource = root / "fixture.md"
            resource.write_text("fixture", encoding="utf-8")
            records = []
            for host, entry_mode, duration in (
                ("host-a", "owner-direct", 1.0),
                ("host-a", "owner-direct", 2.0),
                ("host-b", "arbitrator", 9.0),
            ):
                turn = complete_turn(resource)
                turn["duration_seconds"] = duration
                records.append(
                    self.telemetry.build_turn_telemetry(
                        turn,
                        context={
                            "case_id": f"{host}-{duration}",
                            "entry_mode": entry_mode,
                            "execution_root": root,
                            "allowed_roots": [root],
                            "arm_manifest": fixture_manifest(host=host),
                        },
                    )
                )
            records[1]["measurements"]["tokens.output"] = {
                "value": None,
                "provenance": "unavailable",
                "status": "unavailable",
            }
            summary = self.telemetry.summarize_telemetry(records)

        self.assertEqual(summary["stratum_count"], 2)
        self.assertIsNone(summary["cross_stratum_rollup"])
        first = next(item for item in summary["strata"] if item["record_count"] == 2)
        output = first["endpoints"]["tokens.output"]
        self.assertEqual(output["denominator"], 2)
        self.assertEqual(output["observed_count"], 1)
        self.assertEqual(output["missing_count"], 1)
        wall = first["endpoints"]["wall_time_seconds"]
        self.assertEqual(wall["p50"], 1.0)
        self.assertEqual(wall["p95"], 2.0)

    def test_retained_telemetry_excludes_secret_content_and_external_paths(self) -> None:
        secret = "TOP-SECRET-DO-NOT-RETAIN"
        record = self.telemetry.build_turn_telemetry(
            {
                "answer": f"{secret} Mindthus",
                "agent_messages": [f"Notice: {secret}"],
                "loaded_commands": [f"Read /private/{secret}/SKILL.md"],
                "duration_seconds": 0.1,
                "returncode": 0,
            },
            context={
                "case_id": "redaction",
                "entry_mode": "owner-direct",
                "execution_root": REPO,
                "allowed_roots": [REPO],
            },
        )
        serialized = json.dumps(record, ensure_ascii=False)

        self.assertNotIn(secret, serialized)
        receipt = record["measurements"]["resource_reads"]["value"][0]
        self.assertIsNone(receipt["resolved_path"])
        self.assertTrue(record["measurements"]["mindthus_terminology_leakage"]["value"]["observed"])
        self.assertFalse(record["retention"]["raw_commands_retained"])

    def test_schema_declares_provenance_and_closed_envelope(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "mindthus-beta2-turn-telemetry-v0.1",
        )
        self.assertEqual(
            set(schema["$defs"]["provenance"]["enum"]),
            {"native", "deterministic", "judge-inferred", "self-reported", "unavailable"},
        )

    def test_missing_whole_turn_record_is_visible_in_response_summary(self) -> None:
        summary = self.telemetry.summarize_response_telemetry(
            [
                {
                    "turns": [
                        {"telemetry": {"stratum": {}, "measurements": {}, "evidence_gate": {}}},
                        {"answer": "legacy turn without telemetry"},
                    ]
                }
            ]
        )

        self.assertEqual(summary["expected_turn_count"], 2)
        self.assertEqual(summary["record_count"], 1)
        self.assertEqual(summary["missing_record_count"], 1)
        self.assertEqual(summary["record_completeness_gate"], "blocked")

    def test_runner_attaches_telemetry_only_when_arm_manifest_is_supplied(self) -> None:
        runner = load_runner()

        def fake_run_codex(*args, **kwargs):
            return {
                **complete_turn(REPO / "skills" / "edsp" / "SKILL.md"),
                "thread_id": "beta2-thread",
                "events_path": "",
                "stderr_path": "",
                "last_message_path": "",
                "prompt_path": "",
                "contamination_flags": [],
            }

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            runner, "run_codex", fake_run_codex
        ):
            out = Path(tmp)
            runner.ensure_dirs(out)
            args = SimpleNamespace(
                out_dir=out,
                variant="ignored-beta2-label",
                plugin_context="mindthus",
                codex_home=out,
                repo_root=REPO,
                execution_root=out,
                model=None,
                timeout=1,
                entry_mode="owner-direct",
                beta2_arm_manifest=fixture_manifest(),
            )
            response = runner.run_case(case_by_number(1), args)
            summary = runner.write_beta2_telemetry_summary(out, [response])

        self.assertIn("telemetry", response["turns"][0])
        self.assertEqual(response["turns"][0]["telemetry"]["stratum"]["arm_id"], "thin-kernel")
        self.assertEqual(summary["expected_turn_count"], 1)
        self.assertEqual(summary["missing_record_count"], 0)


if __name__ == "__main__":
    unittest.main()
