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
        "platform-adapter-mission",
        "--title",
        "Platform Adapter Mission",
        "--objective",
        "Verify platform role-separated review adapters.",
        "--acceptance-evidence",
        "A1:Review carrier artifacts exist.",
        "--acceptance-evidence",
        "A2:Reviewer output remains candidate finding only.",
        "--active-task-id",
        "T1",
        "--active-task-title",
        "Prepare platform review",
        "--active-task-contribution",
        "Creates a reviewable platform boundary.",
        "--latest-state",
        "Ready for platform packet generation.",
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
        "Platform adapter boundary is ready for independent review.",
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


class PlatformReviewPacketTests(unittest.TestCase):
    def test_claude_code_grade_packet_generates_read_only_agent_carrier(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            output_dir = Path(tmp) / "claude-review"
            before = mission_tree_snapshot(mission_dir)
            result = run_script(
                "platform_review_packet.py",
                str(mission_dir),
                "--platform",
                "claude-code",
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
            self.assertEqual(manifest["schema_version"], "tplan.claude_code_adapter.v0.1")
            self.assertEqual(manifest["platform"], "claude-code")
            self.assertEqual(manifest["role"], "grade")
            artifacts = manifest["artifacts"]
            for key in ("packet_json", "reviewer_agent", "delegation_prompt", "config_snippet", "install_notes"):
                self.assertTrue(Path(artifacts[key]).exists(), key)

            packet = json.loads(Path(artifacts["packet_json"]).read_text(encoding="utf-8"))
            self.assertEqual(packet["review_contract"]["authority_boundary"], "candidate_findings_only")
            self.assertTrue(packet["adapter_boundary"]["read_only_reviewer"])
            self.assertIn("memory", packet["adapter_boundary"]["must_not_mutate"])
            self.assertIn("https://code.claude.com/docs/en/sub-agents", packet["carrier_options"]["official_docs"])

            agent = Path(artifacts["reviewer_agent"]).read_text(encoding="utf-8")
            self.assertIn("name: tplan-grader", agent)
            self.assertIn("tools: Read, Glob, Grep", agent)
            self.assertIn("permissionMode: plan", agent)
            self.assertIn("candidate finding", agent)
            self.assertIn("You must not edit files", agent)

            config = json.loads(Path(artifacts["config_snippet"]).read_text(encoding="utf-8"))
            self.assertIn("SubagentStart", config["hooks"])
            self.assertIn("^tplan-grader$", config["hooks"]["SubagentStart"][0]["matcher"])

    def test_opencode_grade_packet_generates_read_only_agent_carrier(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            output_dir = Path(tmp) / "opencode-review"
            before = mission_tree_snapshot(mission_dir)
            result = run_script(
                "platform_review_packet.py",
                str(mission_dir),
                "--platform",
                "opencode",
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
            self.assertEqual(manifest["schema_version"], "tplan.opencode_adapter.v0.1")
            self.assertEqual(manifest["platform"], "opencode")
            artifacts = manifest["artifacts"]

            packet = json.loads(Path(artifacts["packet_json"]).read_text(encoding="utf-8"))
            self.assertEqual(packet["agent_name"], "tplan-grader")
            self.assertTrue(packet["adapter_boundary"]["candidate_findings_only"])
            self.assertIn("https://open-code.ai/en/docs/agents", packet["carrier_options"]["official_docs"])

            agent = Path(artifacts["reviewer_agent"]).read_text(encoding="utf-8")
            self.assertIn("mode: subagent", agent)
            self.assertIn("read: allow", agent)
            self.assertIn("glob: allow", agent)
            self.assertIn("grep: allow", agent)
            self.assertIn("list: allow", agent)
            self.assertIn("edit: deny", agent)
            self.assertIn("task: deny", agent)
            self.assertIn("bash: deny", agent)
            self.assertNotIn("git diff", agent)
            self.assertNotIn("rg *", agent)
            self.assertIn("candidate finding", agent)

            config = json.loads(Path(artifacts["config_snippet"]).read_text(encoding="utf-8"))
            reviewer = config["agent"]["tplan-grader"]
            self.assertEqual(reviewer["mode"], "subagent")
            self.assertEqual(reviewer["permission"]["read"], "allow")
            self.assertEqual(reviewer["permission"]["glob"], "allow")
            self.assertEqual(reviewer["permission"]["grep"], "allow")
            self.assertEqual(reviewer["permission"]["list"], "allow")
            self.assertEqual(reviewer["permission"]["edit"], "deny")
            self.assertEqual(reviewer["permission"]["task"], "deny")
            self.assertEqual(reviewer["permission"]["bash"], "deny")

    def test_platform_orchestration_modes_match_codex_review_policy(self):
        for platform, kind in (
            ("claude-code", "claude-code_orchestration"),
            ("opencode", "opencode_orchestration"),
        ):
            with self.subTest(platform=platform):
                with tempfile.TemporaryDirectory() as tmp:
                    mission_dir = create_mission(tmp)
                    output_dir = Path(tmp) / f"{platform}-review"
                    before = mission_tree_snapshot(mission_dir)
                    result = run_script(
                        "platform_review_packet.py",
                        str(mission_dir),
                        "--platform",
                        platform,
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

                    self.assertEqual(manifest["kind"], kind)
                    self.assertEqual(manifest["required_roles"], ["grade"])
                    self.assertEqual(manifest["conditional_roles"], ["advise", "dream"])
                    plan = json.loads(Path(manifest["artifacts"]["orchestration_plan"]).read_text(encoding="utf-8"))
                    self.assertIn("not a mandatory four-agent runtime", plan["boundary"])
                    self.assertEqual(plan["orchestration_policy"], f"recommended_{platform}_tplan_path")
                    self.assertIn("main_agent_verify_then_record", plan["main_agent_responsibilities"])
                    self.assertIn("low-risk lite Mission", " ".join(plan["skip_rules"]))
                    self.assertEqual(plan["roles"]["grade"]["dispatch_requirement"], "required")
                    self.assertEqual(plan["roles"]["advise"]["dispatch_requirement"], "conditional")
                    self.assertEqual(plan["roles"]["dream"]["dispatch_requirement"], "conditional")
                    for role in ("advise", "grade", "dream"):
                        role_artifacts = manifest["role_artifacts"][role]
                        self.assertTrue(Path(role_artifacts["reviewer_agent"]).exists())
                        self.assertTrue(Path(role_artifacts["delegation_prompt"]).exists())

    def test_platform_strict_orchestration_requires_advise_and_grade(self):
        for platform in ("claude-code", "opencode"):
            with self.subTest(platform=platform):
                with tempfile.TemporaryDirectory() as tmp:
                    mission_dir = create_mission(tmp)
                    output_dir = Path(tmp) / f"{platform}-review"
                    before = mission_tree_snapshot(mission_dir)
                    result = run_script(
                        "platform_review_packet.py",
                        str(mission_dir),
                        "--platform",
                        platform,
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

    def test_platform_review_packet_rejects_unknown_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script(
                "platform_review_packet.py",
                str(mission_dir),
                "--platform",
                "unknown",
                "--role",
                "grade",
                "--output-dir",
                str(Path(tmp) / "review"),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
