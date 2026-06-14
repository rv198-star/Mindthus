import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "primitives" / "check.py"
MANIFEST = ROOT / "scripts" / "primitives" / "manifest.json"
AB_TESTS = ROOT / "tests" / "primitive_activation_ab_behavior_tests.md"
LIVE_RERUN = ROOT / "tests" / "primitive_activation_live_rerun_2026_06_14.md"


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


class PrimitiveActivationTests(unittest.TestCase):
    def test_before_route_includes_context_sufficiency_as_check_not_primitive(self) -> None:
        result = run_check("--event", "before-route", "--method", "using-mindthus", "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)

        primitive_ids = [item["id"] for item in report["active_primitives"]]
        self.assertIn("evidence_claim_ceiling", primitive_ids)
        self.assertIn("context_sufficiency_check", report["required_agent_checks"])
        self.assertNotIn("context_sufficiency_check", primitive_ids)
        self.assertNotIn("failure_smell_scan", report["required_agent_checks"])

    def test_before_freeze_keeps_gate_smells_as_checks_not_primitives(self) -> None:
        result = run_check("--event", "before-freeze", "--method", "tvg", "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)

        self.assertEqual(report["script_verdict"], "shape_only")
        self.assertIs(report["agentic_judgment_required"], True)
        primitive_ids = [item["id"] for item in report["active_primitives"]]
        self.assertEqual(primitive_ids, ["evidence_claim_ceiling", "no_abstract_jargon_wall"])
        self.assertIn("gate_probe_current_position_and_next_action", report["required_agent_checks"])
        self.assertIn("failure_smell_scan", report["required_agent_checks"])
        self.assertNotIn("gate_probes", primitive_ids)
        self.assertNotIn("failure_smells", primitive_ids)
        self.assertIn("gate_success", report["script_must_not_decide"])

    def test_agent_context_output_injects_primitives_as_context_not_verdict(self) -> None:
        result = run_check("--event", "before-freeze", "--method", "tvg", "--agent-context")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

        self.assertIn("BEGIN MINDTHUS PRIMITIVE CONTEXT", result.stdout)
        self.assertIn("injection_layer: primitive_activation", result.stdout)
        self.assertIn("event: before-freeze", result.stdout)
        self.assertIn("method: tvg", result.stdout)
        self.assertIn("evidence_claim_ceiling", result.stdout)
        self.assertIn("no_abstract_jargon_wall", result.stdout)
        self.assertIn("gate_probe_current_position_and_next_action", result.stdout)
        self.assertIn("failure_smell_scan", result.stdout)
        self.assertIn("script_verdict: shape_only", result.stdout)
        self.assertIn("current_user_instruction_priority: true", result.stdout)
        self.assertIn("agentic_judgment_required: true", result.stdout)

    def test_before_continue_keeps_tplan_continuation_authorization_as_check(self) -> None:
        tplan_result = run_check("--event", "before-continue", "--method", "tplan", "--json")
        self.assertEqual(tplan_result.returncode, 0, tplan_result.stderr + tplan_result.stdout)
        tplan_report = json.loads(tplan_result.stdout)
        self.assertNotIn("continuation_authorization", [item["id"] for item in tplan_report["active_primitives"]])
        self.assertIn("mission_roi_or_authority_for_continuation", tplan_report["required_agent_checks"])
        self.assertIn("gate_probe_continue_position", tplan_report["required_agent_checks"])

        tvg_result = run_check("--event", "before-continue", "--method", "tvg", "--json")
        self.assertEqual(tvg_result.returncode, 0, tvg_result.stderr + tvg_result.stdout)
        tvg_report = json.loads(tvg_result.stdout)
        self.assertNotIn(
            "mission_roi_or_authority_for_continuation",
            tvg_report["required_agent_checks"],
        )

    def test_manifest_has_minimal_shape_for_every_primitive(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["script_boundary"], "shape_only_reminder_not_semantic_judgment")
        self.assertEqual(
            set(manifest["primitives"]),
            {
                "evidence_claim_ceiling",
                "perspective_pressure",
                "anti_spiral",
                "no_abstract_jargon_wall",
                "approximate_quantified_mapping",
            },
        )

        for primitive_id, primitive in manifest["primitives"].items():
            self.assertTrue(primitive_id)
            self.assertTrue(primitive["name"])
            self.assertTrue(primitive["short_rule"])
            self.assertTrue(primitive["trigger"])
            self.assertTrue(primitive["action_effect"])
            self.assertTrue(primitive["not_a"])
            self.assertTrue(primitive["owner"])

    def test_manifest_defines_skill_specific_intervention_points(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        method_events = manifest["method_events"]
        expected_methods = {
            "using-mindthus",
            "3l5s",
            "edsp",
            "sela",
            "mpg",
            "wae",
            "tvg",
            "tplan",
        }
        self.assertEqual(set(method_events), expected_methods)

        for method, events in method_events.items():
            self.assertTrue(events, method)
            for event_name, policy in events.items():
                with self.subTest(method=method, event=event_name):
                    self.assertIn(event_name, manifest["events"])
                    self.assertTrue(policy["intervention_points"])
                    self.assertTrue(policy["active_primitives"])
                    self.assertTrue(policy["required_agent_checks"])
                    self.assertTrue(set(policy["active_primitives"]) <= set(manifest["primitives"]))

    def test_cross_section_checks_are_not_mechanically_attached_to_every_surface(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        method_events = manifest["method_events"]
        cross_section_checks = {
            "gate_probe_current_position_and_next_action",
            "gate_probe_continue_position",
            "failure_smell_scan",
            "mission_roi_or_authority_for_continuation",
        }

        self.assertFalse(
            cross_section_checks
            & set(method_events["edsp"]["before-continue"]["required_agent_checks"])
        )
        self.assertFalse(
            cross_section_checks
            & set(method_events["sela"]["before-freeze"]["required_agent_checks"])
        )
        self.assertFalse(
            cross_section_checks
            & set(method_events["mpg"]["before-freeze"]["required_agent_checks"])
        )
        self.assertFalse(
            cross_section_checks
            & set(method_events["wae"]["before-continue"]["required_agent_checks"])
        )
        self.assertIn(
            "failure_smell_scan",
            method_events["tvg"]["before-continue"]["required_agent_checks"],
        )
        self.assertIn(
            "mission_roi_or_authority_for_continuation",
            method_events["tplan"]["before-continue"]["required_agent_checks"],
        )

    def test_method_specific_activation_overrides_generic_event_defaults(self) -> None:
        edsp_result = run_check("--event", "before-freeze", "--method", "edsp", "--json")
        self.assertEqual(edsp_result.returncode, 0, edsp_result.stderr + edsp_result.stdout)
        edsp_report = json.loads(edsp_result.stdout)
        edsp_ids = [item["id"] for item in edsp_report["active_primitives"]]
        self.assertIn("perspective_pressure", edsp_ids)
        self.assertIn("coordinate_system_stability", edsp_report["required_agent_checks"])
        self.assertIn("edsp_output_freeze", edsp_report["intervention_points"])

        tvg_result = run_check("--event", "before-continue", "--method", "tvg", "--json")
        self.assertEqual(tvg_result.returncode, 0, tvg_result.stderr + tvg_result.stdout)
        tvg_report = json.loads(tvg_result.stdout)
        self.assertIn("next_round_positive_value_hypothesis", tvg_report["required_agent_checks"])
        self.assertIn("tvg_next_round", tvg_report["intervention_points"])

    def test_reviewed_intervention_surfaces_keep_delivery_and_loopback_primitives(self) -> None:
        tvg_result = run_check("--event", "before-freeze", "--method", "tvg", "--json")
        self.assertEqual(tvg_result.returncode, 0, tvg_result.stderr + tvg_result.stdout)
        tvg_report = json.loads(tvg_result.stdout)
        self.assertIn(
            "no_abstract_jargon_wall",
            [item["id"] for item in tvg_report["active_primitives"]],
        )

        l5s_result = run_check("--event", "before-continue", "--method", "3l5s", "--json")
        self.assertEqual(l5s_result.returncode, 0, l5s_result.stderr + l5s_result.stdout)
        l5s_report = json.loads(l5s_result.stdout)
        self.assertIn(
            "evidence_claim_ceiling",
            [item["id"] for item in l5s_report["active_primitives"]],
        )

        mpg_result = run_check("--event", "before-freeze", "--method", "mpg", "--json")
        self.assertEqual(mpg_result.returncode, 0, mpg_result.stderr + mpg_result.stdout)
        mpg_report = json.loads(mpg_result.stdout)
        self.assertIn(
            "if_hypothetical_numbers_used_not_decision_calculator",
            mpg_report["required_agent_checks"],
        )

    def test_release_pack_includes_primitive_activation_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "release"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build-release-pack.py"), "--out", str(out)],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            for platform in ("claude-code/claude-plugin", "codex", "opencode"):
                self.assertTrue((out / platform / "scripts" / "primitives" / "check.py").is_file())
                self.assertTrue((out / platform / "scripts" / "primitives" / "manifest.json").is_file())

    def test_ab_behavior_tests_cover_freeze_and_continue_activation(self) -> None:
        text = AB_TESTS.read_text(encoding="utf-8")
        self.assertEqual(text.count("## Scenario "), 2)
        for phrase in (
            "before-freeze",
            "before-continue",
            "--agent-context",
            "BEGIN MINDTHUS PRIMITIVE CONTEXT",
            "injected context layer",
            "shape-only",
            "reminder-only",
            "gate_probe_current_position_and_next_action",
            "failure_smell_scan",
            "evidence_claim_ceiling",
            "anti_spiral",
            "mission_roi_or_authority_for_continuation",
            "does not prove broad agent reliability",
        ):
            self.assertIn(phrase, text)

    def test_live_rerun_records_real_primitive_bearing_context(self) -> None:
        text = LIVE_RERUN.read_text(encoding="utf-8")
        for phrase in (
            "before-continue",
            "before-freeze",
            "--agent-context",
            "mission_roi_or_authority_for_continuation",
            "continuing the same",
            "branch is only justified",
            "changes what the script can produce",
            "method_events",
            "activation_source: method_specific",
            "perspective_pressure",
            "approximate_quantified_mapping",
            "broad agent reliability",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
