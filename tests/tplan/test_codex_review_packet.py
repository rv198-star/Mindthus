import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    result = run_script(
        "init_lite.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "codex-adapter-mission",
        "--title",
        "Codex Adapter Mission",
        "--objective",
        "Verify Codex role-separated review adapter.",
        "--acceptance-evidence",
        "A1:Review packet exists.",
        "--acceptance-evidence",
        "A2:Reviewer output remains candidate finding only.",
        "--active-task-id",
        "T1",
        "--active-task-title",
        "Prepare release review",
        "--active-task-contribution",
        "Creates a reviewable release boundary.",
        "--latest-state",
        "Ready for review packet generation.",
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    evidence = run_script(
        "record_evidence.py",
        str(mission_dir),
        "--event-type",
        "key_finding",
        "--task-id",
        "T1",
        "--summary",
        "Release boundary is ready for independent review.",
    )
    if evidence.returncode != 0:
        raise AssertionError(evidence.stderr)
    return mission_dir


def mission_tree_snapshot(mission_dir):
    return {
        str(path.relative_to(mission_dir)): path.read_bytes()
        for path in sorted(mission_dir.rglob("*"))
        if path.is_file()
    }


class CodexReviewPacketTests(unittest.TestCase):
    def test_codex_grade_packet_generates_actionable_carriers_without_mutating_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            output_dir = Path(tmp) / "codex-review"
            before = mission_tree_snapshot(mission_dir)
            result = run_script(
                "codex_review_packet.py",
                str(mission_dir),
                "--role",
                "grade",
                "--output-dir",
                str(output_dir),
                "--repo-root",
                str(REPO),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            after = mission_tree_snapshot(mission_dir)
            self.assertEqual(after, before)
            manifest = json.loads(result.stdout)
            self.assertEqual(manifest["schema_version"], "tplan.codex_adapter.v0.1")
            self.assertEqual(manifest["platform"], "codex")
            self.assertEqual(manifest["role"], "grade")
            self.assertIsNone(manifest["cli_run"])
            artifacts = manifest["artifacts"]
            for key in (
                "packet_json",
                "subagent_prompt",
                "subagent_dispatch",
                "cli_prompt",
                "cli_command",
                "cli_output",
            ):
                self.assertIn(key, artifacts)

            packet = json.loads(Path(artifacts["packet_json"]).read_text(encoding="utf-8"))
            self.assertTrue(packet["adapter_boundary"]["candidate_findings_only"])
            self.assertTrue(packet["adapter_boundary"]["read_only_reviewer"])
            self.assertTrue(packet["adapter_boundary"]["not_a_four_agent_runtime"])
            self.assertIn("Mission state", packet["adapter_boundary"]["must_not_mutate"])
            self.assertIn("memory", packet["adapter_boundary"]["must_not_mutate"])
            self.assertEqual(packet["review_contract"]["authority_boundary"], "candidate_findings_only")
            self.assertEqual(packet["decision_context"]["hook"], "mission_review")

            dispatch = json.loads(Path(artifacts["subagent_dispatch"]).read_text(encoding="utf-8"))
            self.assertEqual(dispatch["tool"], "multi_agent_v1.spawn_agent")
            self.assertEqual(dispatch["agent_type"], "explorer")
            self.assertFalse(dispatch["fork_context"])
            self.assertIn("candidate_findings_only", dispatch["message"])

            cli_command = Path(artifacts["cli_command"]).read_text(encoding="utf-8")
            self.assertIn("codex -s read-only -a never exec --ephemeral", cli_command)
            self.assertIn("cli-review-output.md", cli_command)
            cli_prompt = Path(artifacts["cli_prompt"]).read_text(encoding="utf-8")
            self.assertIn("ephemeral Codex CLI review session", cli_prompt)
            self.assertIn("You must not edit files", cli_prompt)
            self.assertIn("acceptance-grading", cli_prompt)

    def test_codex_advise_packet_uses_direction_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            output_dir = Path(tmp) / "codex-review"
            before = mission_tree_snapshot(mission_dir)
            result = run_script(
                "codex_review_packet.py",
                str(mission_dir),
                "--role",
                "advise",
                "--output-dir",
                str(output_dir),
                "--repo-root",
                str(REPO),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads(result.stdout)
            packet = json.loads(Path(manifest["artifacts"]["packet_json"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["trigger"], "before_continue")
            self.assertEqual(packet["role_surface"], "direction-checking")
            self.assertEqual(packet["decision_context"]["hook"], "selection")
            self.assertIn("Mission alignment", " ".join(packet["review_questions"]))
            self.assertIn("continue", packet["review_contract"]["allowed_verdicts"])

    def test_codex_recommended_orchestration_makes_grade_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            output_dir = Path(tmp) / "codex-review"
            before = mission_tree_snapshot(mission_dir)
            result = run_script(
                "codex_review_packet.py",
                str(mission_dir),
                "--orchestration-mode",
                "recommended",
                "--output-dir",
                str(output_dir),
                "--repo-root",
                str(REPO),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            after = mission_tree_snapshot(mission_dir)
            self.assertEqual(after, before)
            manifest = json.loads(result.stdout)

            self.assertEqual(manifest["kind"], "codex_orchestration")
            self.assertEqual(manifest["orchestration_mode"], "recommended")
            self.assertEqual(manifest["required_roles"], ["grade"])
            self.assertEqual(manifest["conditional_roles"], ["advise", "dream"])
            self.assertIn("low-risk lite Mission", " ".join(manifest["skip_rules"]))
            plan_path = Path(manifest["artifacts"]["orchestration_plan"])
            plan = json.loads(plan_path.read_text(encoding="utf-8"))

            self.assertEqual(plan["orchestration_policy"], "recommended_codex_tplan_path")
            self.assertEqual(plan["roles"]["grade"]["dispatch_requirement"], "required")
            self.assertEqual(plan["roles"]["advise"]["dispatch_requirement"], "conditional")
            self.assertEqual(plan["roles"]["dream"]["dispatch_requirement"], "conditional")
            self.assertIn("main_agent_verify_then_record", plan["main_agent_responsibilities"])
            for role in ("advise", "grade", "dream"):
                role_artifacts = manifest["role_artifacts"][role]
                self.assertTrue(Path(role_artifacts["subagent_dispatch"]).exists())
                self.assertTrue(Path(role_artifacts["cli_command"]).exists())

    def test_codex_strict_orchestration_requires_advise_and_grade(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            output_dir = Path(tmp) / "codex-review"
            before = mission_tree_snapshot(mission_dir)
            result = run_script(
                "codex_review_packet.py",
                str(mission_dir),
                "--orchestration-mode",
                "strict",
                "--output-dir",
                str(output_dir),
                "--repo-root",
                str(REPO),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            after = mission_tree_snapshot(mission_dir)
            self.assertEqual(after, before)
            manifest = json.loads(result.stdout)
            plan = json.loads(Path(manifest["artifacts"]["orchestration_plan"]).read_text(encoding="utf-8"))

            self.assertEqual(manifest["required_roles"], ["advise", "grade"])
            self.assertEqual(manifest["conditional_roles"], ["dream"])
            self.assertEqual(plan["roles"]["advise"]["dispatch_requirement"], "required")
            self.assertEqual(plan["roles"]["grade"]["dispatch_requirement"], "required")
            self.assertEqual(plan["roles"]["dream"]["dispatch_requirement"], "conditional")
            self.assertIn("not a mandatory four-agent runtime", plan["boundary"])

    def test_codex_run_cli_can_be_verified_with_fake_codex_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            output_dir = Path(tmp) / "codex-review"
            fake_codex = Path(tmp) / "fake-codex"
            fake_codex.write_text(
                """#!/usr/bin/env python3
import json
import pathlib
import sys

output = None
read_only_sandbox = False
for index, arg in enumerate(sys.argv):
    if arg in {"-o", "--output-last-message"} and index + 1 < len(sys.argv):
        output = pathlib.Path(sys.argv[index + 1])
    if arg == "-s" and index + 1 < len(sys.argv):
        read_only_sandbox = sys.argv[index + 1] == "read-only"
prompt = sys.stdin.read()
if output is None:
    raise SystemExit("missing output path")
payload = {
    "role": "grade",
    "verdict": "insufficient_evidence",
    "confidence": 0.5,
    "findings": [],
    "evidence_refs": [],
    "authority_boundary": "candidate_findings_only",
    "state_mutation_attempted": False,
    "recommended_next_surface": "mission_review",
    "learning_candidates": [],
    "read_only_sandbox": read_only_sandbox,
    "prompt_seen": "Codex tplan acceptance-grading packet" in prompt,
}
output.write_text(json.dumps(payload), encoding="utf-8")
print(json.dumps(payload))
""",
                encoding="utf-8",
            )
            fake_codex.chmod(fake_codex.stat().st_mode | 0o111)
            before = mission_tree_snapshot(mission_dir)
            result = run_script(
                "codex_review_packet.py",
                str(mission_dir),
                "--role",
                "grade",
                "--output-dir",
                str(output_dir),
                "--repo-root",
                str(REPO),
                "--run-cli",
                "--codex-bin",
                str(fake_codex),
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            after = mission_tree_snapshot(mission_dir)
            self.assertEqual(after, before)
            manifest = json.loads(result.stdout)
            cli_run = manifest["cli_run"]
            self.assertEqual(cli_run["returncode"], 0)
            output = json.loads(Path(cli_run["output"]).read_text(encoding="utf-8"))
            stdout = json.loads(Path(cli_run["stdout"]).read_text(encoding="utf-8"))

        self.assertTrue(output["prompt_seen"])
        self.assertTrue(output["read_only_sandbox"])
        self.assertEqual(output["authority_boundary"], "candidate_findings_only")
        self.assertFalse(output["state_mutation_attempted"])
        self.assertEqual(stdout["verdict"], "insufficient_evidence")

    def test_run_cli_rejects_orchestration_mode_until_multi_role_execution_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script(
                "codex_review_packet.py",
                str(mission_dir),
                "--orchestration-mode",
                "recommended",
                "--output-dir",
                str(Path(tmp) / "codex-review"),
                "--run-cli",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--run-cli is only supported with --role", result.stderr)

    def test_codex_review_packet_rejects_unknown_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script(
                "codex_review_packet.py",
                str(mission_dir),
                "--role",
                "execute",
                "--output-dir",
                str(Path(tmp) / "codex-review"),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
