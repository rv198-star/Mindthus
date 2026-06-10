import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "tplan"


class TplanSkillContractTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "SKILL.md",
            "resources/schema.md",
            "resources/lifecycle.md",
            "resources/policy.md",
            "resources/hooks.md",
            "resources/user-output.md",
            "resources/subagents.md",
            "templates/mission.json",
            "templates/mission.md",
            "templates/evidence.jsonl",
            "templates/hook-output.json",
            "scripts/init_lite.py",
            "scripts/checkpoint.py",
            "scripts/render_user_update.py",
        ]
        missing = [path for path in required if not (SKILL / path).exists()]
        self.assertEqual(missing, [])

    def test_skill_frontmatter_and_boundaries(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: tplan", text)
        self.assertIn("description:", text)
        self.assertIn("OKR-Runtime for AI agents", text)
        self.assertIn("Mission", text)
        self.assertIn("acceptance evidence", text)
        self.assertIn("decision hooks", text)
        self.assertIn("It is not a human OKR management system", text)
        self.assertIn("Use OKR language as the primary public explanation", text)
        self.assertIn("unless a schema migration explicitly remaps them", text)
        self.assertIn("reason is runtime precision", text)
        self.assertIn("not existing user familiarity", text)
        self.assertIn("Mission maps to Objective", text)
        self.assertIn("acceptance criteria and acceptance evidence map to Key Results", text)
        self.assertIn("Task, SubTask, and Step map to initiatives and actions", text)
        self.assertIn("Its cycle is shorter than ordinary OKR management", text)
        self.assertIn("dynamic workflow runtime", text)
        self.assertIn("Scripts must not decide semantic truth", text)

    def test_json_templates_are_valid(self):
        mission = json.loads((SKILL / "templates" / "mission.json").read_text(encoding="utf-8"))
        hook = json.loads((SKILL / "templates" / "hook-output.json").read_text(encoding="utf-8"))
        self.assertEqual(mission["schema_version"], "tplan.v0.1")
        self.assertIn("mission", mission)
        self.assertIn("tasks", mission)
        self.assertEqual(hook["recommendation"], "continue")
        self.assertIn("parent_alignment", hook)
        self.assertIn("mission_trace", hook)
        self.assertIn("path_assessment", hook)
        self.assertEqual(hook["path_assessment"]["marginal_roi"], "positive")
        self.assertEqual(hook["path_assessment"]["path_role"], "dominant_path")
        self.assertEqual(hook["path_assessment"]["evidence_delta"], "new_evidence_expected")

    def test_resource_files_name_runtime_contracts(self):
        resources = "\n".join(
            (SKILL / "resources" / name).read_text(encoding="utf-8")
            for name in ("schema.md", "lifecycle.md", "policy.md", "hooks.md")
        )
        for phrase in (
            "human_in_loop",
            "resource_sufficiency",
            "success-critical",
            "observational state",
            "decision state",
            "Mission Review Gate",
            "mission_alignment",
            "parent_alignment",
            "mission_trace",
            "semantic correctness",
            "path_assessment",
            "marginal_roi",
            "path_role",
            "evidence_delta",
            "Elapsed time is not the root criterion",
            "anti_spiral_audit",
            "Anti-Spiral Runtime Gate",
        ):
            self.assertIn(phrase, resources)

    def test_adaptive_runtime_keeps_capabilities_while_reducing_ceremony(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        resources = "\n".join(
            (SKILL / "resources" / name).read_text(encoding="utf-8")
            for name in ("schema.md", "hooks.md")
        )
        methodology = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")

        for phrase in (
            "Adaptive Runtime Policy",
            "runtime level may reduce recording density",
            "must not weaken key risk triggers",
            "`lite`",
            "`normal`",
            "`strict`",
            "Lite mode minimum state",
            "Delayed Step Materialization",
            "Sparse Evidence",
            "Checkpoint Command",
            "Lite Startup Default",
            "checkpoint-first startup",
            "scripts/init_lite.py",
            "Lite Quickstart Recipe",
            "Prefer these recipes over script-help exploration",
            "scripts/init_lite.py --dir",
            "scripts/checkpoint.py",
            "scripts/make_decision_packet.py",
            "thin Mission state machine",
        ):
            self.assertIn(phrase, skill_text)

        for phrase in (
            "inline alignment",
            "light packet",
            "full mission review",
            "high-impact changes still require alignment or review",
            "Promote an action into a Step only when",
            "acceptance passed or failed",
        ):
            self.assertIn(phrase, resources)

        self.assertIn("按风险展开", methodology)
        self.assertIn("不是低配 tplan", methodology)
        self.assertIn("轻启动", methodology)
        self.assertIn("init_lite.py", methodology)
        self.assertIn("checkpoint", methodology)

    def test_adaptive_pressure_tests_cover_lite_and_strict_modes(self):
        text = (REPO / "tests" / "tplan" / "skill_ab_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "Group 3: Adaptive Runtime Levels",
            "lite mode",
            "strict mode",
            "runtime level may reduce recording density",
            "must not weaken key risk triggers",
            "full Mission Review",
            "minimum recovery state",
            "init_lite.py",
            "checkpoint.py",
        ):
            self.assertIn(phrase, text)

    def test_user_facing_output_hides_internal_ids_by_default(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        resource = (SKILL / "resources" / "user-output.md").read_text(encoding="utf-8")
        methodology = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")

        for phrase in (
            "User-Facing Output Adapter",
            "Internal IDs are for runtime stability",
            "User-facing output should lead with meaning",
            "scripts/render_user_update.py",
            "ordinary updates should not lead with raw IDs",
        ):
            self.assertIn(phrase, skill_text)

        for phrase in (
            "当前目标：",
            "当前进展：",
            "已确认：",
            "下一步：",
            "Debug And Audit Mode",
            "Internal recovery references",
            "Stop reports should not lead with raw task or evidence IDs",
            "Internal: active_task_id = T1",
            "User-facing:",
        ):
            self.assertIn(phrase, resource)

        self.assertIn("用户可读输出", methodology)
        self.assertIn("不要把 T1、E2 这类内部编号放在普通回复开头", methodology)

    def test_read_only_subagent_acceleration_keeps_main_agent_in_control(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        resource = (SKILL / "resources" / "subagents.md").read_text(encoding="utf-8")
        methodology = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")

        for phrase in (
            "Read-only SubAgent Acceleration",
            "SubAgents are scouts, not controllers",
            "SubAgent outputs are candidate findings",
            "main agent must verify, merge, decide, and write",
            "must not mutate files, Mission state, evidence, task tree, decisions, or external systems",
        ):
            self.assertIn(phrase, skill_text)

        for phrase in (
            "Allowed Read-only Work",
            "Forbidden Work",
            "read files",
            "search code or docs",
            "write mission.json",
            "write evidence.jsonl",
            "create, close, switch, or mutate Task/SubTask/Step nodes",
            "make final user-facing conclusions",
            "No User-facing Mode Switch",
            "2 or more independent investigation branches",
            "candidate findings",
            "main agent records only verified evidence",
        ):
            self.assertIn(phrase, resource)

        self.assertIn("只读 SubAgent 加速", methodology)
        self.assertIn("SubAgent 是侦察，不是控制器", methodology)

    def test_pressure_tests_cover_read_only_subagent_acceleration(self):
        text = (REPO / "tests" / "tplan" / "skill_ab_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "Group 4: Read-only SubAgent Acceleration",
            "SubAgents are scouts, not controllers",
            "read-only investigation",
            "candidate findings",
            "main agent verifies and records evidence",
            "fails if any SubAgent mutates files, Mission state, evidence, task tree, or decisions",
        ):
            self.assertIn(phrase, text)

    def test_shared_risk_context_contract_is_documented(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        resources = "\n".join(
            (SKILL / "resources" / name).read_text(encoding="utf-8")
            for name in ("schema.md", "hooks.md")
        )
        methodology = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")

        for phrase in (
            "Shared Risk Context",
            "risk-adjusted value",
            "risk_context_update",
            "risk_assessment",
            "execution units do not read each other's task logs",
        ):
            self.assertIn(phrase, skill_text)
            self.assertIn(phrase, resources)

        self.assertIn("共享风险上下文", methodology)
        self.assertIn("风险调整后的行动价值", methodology)


if __name__ == "__main__":
    unittest.main()
