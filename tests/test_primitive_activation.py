import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "primitives" / "check.py"
MANIFEST = ROOT / "scripts" / "primitives" / "manifest.json"


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


class PrimitiveActivationTests(unittest.TestCase):
    def test_before_route_activates_frame_fitness_shape_only_reminder(self) -> None:
        result = run_check("--event", "before-route", "--method", "using-mindthus", "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)

        self.assertEqual(report["script_verdict"], "shape_only")
        self.assertIs(report["agentic_judgment_required"], True)
        self.assertEqual(
            [item["id"] for item in report["active_primitives"]],
            [
                "minimal_sufficient_lens",
                "frame_fitness_check",
                "evidence_claim_ceiling",
            ],
        )
        self.assertIn(
            "is_a_local_frame_claiming_global_authority",
            report["required_agent_checks"],
        )
        frame = next(
            item for item in report["active_primitives"] if item["id"] == "frame_fitness_check"
        )
        self.assertEqual(
            frame["output_shape"],
            [
                "true_question",
                "packed_premises",
                "layer_risks",
                "frame_status",
                "reframed_question",
                "routing_decision",
            ],
        )
        self.assertEqual(frame["frame_status_values"], ["clean", "biased", "overloaded", "malformed"])
        self.assertEqual(
            frame["routing_effect"],
            {
                "clean": "normal-route",
                "biased": "name-bias-then-route",
                "overloaded": "split-propositions-then-route",
                "malformed": "correct-question-before-analysis",
            },
        )
        self.assertIn("frame_correctness", report["script_must_not_decide"])

    def test_frame_fitness_manifest_preserves_shape_only_boundary(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        primitive = manifest["primitives"]["frame_fitness_check"]

        self.assertEqual(primitive["name"], "Frame Fitness Check / 定框适配检查")
        self.assertIn("before-route", primitive["trigger"])
        self.assertIn("preserve-frame", primitive["action_effect"])
        self.assertIn("qualify-frame", primitive["action_effect"])
        self.assertIn("reframe", primitive["action_effect"])
        self.assertIn("block-pending-evidence", primitive["action_effect"])
        self.assertIn("contrarianism-engine", primitive["not_a"])
        self.assertIn("semantic-judge", primitive["not_a"])
        self.assertEqual(
            primitive["output_shape"],
            [
                "true_question",
                "packed_premises",
                "layer_risks",
                "frame_status",
                "reframed_question",
                "routing_decision",
            ],
        )
        self.assertEqual(primitive["frame_status_values"], ["clean", "biased", "overloaded", "malformed"])
        self.assertEqual(
            primitive["routing_effect"],
            {
                "clean": "normal-route",
                "biased": "name-bias-then-route",
                "overloaded": "split-propositions-then-route",
                "malformed": "correct-question-before-analysis",
            },
        )

    def test_routing_effect_keys_must_match_frame_status_values(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        frame = manifest["primitives"]["frame_fitness_check"]
        frame["routing_effect"] = {"clean": "normal-route"}

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_check(
                "--event",
                "before-route",
                "--method",
                "using-mindthus",
                "--manifest",
                str(manifest_path),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("routing_effect keys must match frame_status_values", result.stdout)

    def test_routing_effect_requires_frame_status_values(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        frame = manifest["primitives"]["frame_fitness_check"]
        frame.pop("frame_status_values")

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_check(
                "--event",
                "before-route",
                "--method",
                "using-mindthus",
                "--manifest",
                str(manifest_path),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("routing_effect requires frame_status_values", result.stdout)

    def test_before_freeze_activates_gate_smells_and_claim_ceiling(self) -> None:
        result = run_check("--event", "before-freeze", "--method", "tvg", "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)

        self.assertEqual(report["script_verdict"], "shape_only")
        self.assertIs(report["agentic_judgment_required"], True)
        self.assertEqual(
            [item["id"] for item in report["active_primitives"]],
            [
                "gate_probes",
                "failure_smells",
                "evidence_claim_ceiling",
            ],
        )
        self.assertIn("gate_success", report["script_must_not_decide"])

    def test_before_continue_adds_tplan_continuation_authorization_only_for_tplan(self) -> None:
        tplan_result = run_check("--event", "before-continue", "--method", "tplan", "--json")
        self.assertEqual(tplan_result.returncode, 0, tplan_result.stderr + tplan_result.stdout)
        tplan_report = json.loads(tplan_result.stdout)
        self.assertIn(
            "continuation_authorization",
            [item["id"] for item in tplan_report["active_primitives"]],
        )

        tvg_result = run_check("--event", "before-continue", "--method", "tvg", "--json")
        self.assertEqual(tvg_result.returncode, 0, tvg_result.stderr + tvg_result.stdout)
        tvg_report = json.loads(tvg_result.stdout)
        self.assertNotIn(
            "continuation_authorization",
            [item["id"] for item in tvg_report["active_primitives"]],
        )

    def test_manifest_has_minimal_shape_for_every_primitive(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["script_boundary"], "shape_only_reminder_not_semantic_judgment")

        for primitive_id, primitive in manifest["primitives"].items():
            self.assertTrue(primitive_id)
            self.assertTrue(primitive["name"])
            self.assertTrue(primitive["short_rule"])
            self.assertTrue(primitive["trigger"])
            self.assertTrue(primitive["action_effect"])
            self.assertTrue(primitive["not_a"])
            self.assertTrue(primitive["owner"])

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


if __name__ == "__main__":
    unittest.main()
