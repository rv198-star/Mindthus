import importlib.util
import json
import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "tplan"


def load_tplan_runtime():
    spec = importlib.util.spec_from_file_location(
        "tplan_runtime_for_contract_tests",
        SKILL / "scripts" / "tplan_runtime.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TplanSkillContractTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "SKILL.md",
            "resources/schema.md",
            "resources/lifecycle.md",
            "resources/policy.md",
            "resources/hooks.md",
            "resources/user-output.md",
            "resources/execution-trace.md",
            "resources/subagents.md",
            "templates/mission.json",
            "templates/mission.md",
            "templates/evidence.jsonl",
            "templates/hook-output.json",
            "scripts/init_lite.py",
            "scripts/checkpoint.py",
            "scripts/mission_pulse.py",
            "scripts/render_user_update.py",
            "scripts/record_execution_span.py",
            "scripts/observe_model_call.py",
            "scripts/run_traced_command.py",
            "scripts/render_execution_cost_tree.py",
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

    def test_skill_entrypoint_stays_light_for_app_discovery(self):
        size = (SKILL / "SKILL.md").stat().st_size
        self.assertLess(
            size,
            8_000,
            "SKILL.md should stay a thin discovery entrypoint; put long runtime details in resources/",
        )

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
            "scripts/mission_pulse.py",
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
            "--completion-handoff",
            "include both emitted links",
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
            "Terminal Mission Delivery Contract",
            "--completion-handoff",
            "Copy both into the terminal user",
            "execution graph is unavailable",
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

    def test_role_separated_review_policy_stays_lightweight(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        policy = (SKILL / "resources" / "policy.md").read_text(encoding="utf-8")
        hooks = (SKILL / "resources" / "hooks.md").read_text(encoding="utf-8")
        subagents = (SKILL / "resources" / "subagents.md").read_text(encoding="utf-8")
        codex_adapter = (SKILL / "resources" / "platforms" / "codex.md").read_text(encoding="utf-8")
        claude_adapter = (SKILL / "resources" / "platforms" / "claude-code.md").read_text(encoding="utf-8")
        opencode_adapter = (SKILL / "resources" / "platforms" / "opencode.md").read_text(encoding="utf-8")
        codex_script = (SKILL / "scripts" / "codex_review_packet.py").read_text(encoding="utf-8")
        platform_script = (SKILL / "scripts" / "platform_review_packet.py").read_text(encoding="utf-8")
        methodology = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")
        compact_policy = re.sub(r"\s+", " ", policy)
        hooks_lower = hooks.lower()

        for phrase in (
            "Role-Separated Review Policy",
            "responsibility separation, not reviewer isolation",
            "not a new runtime role model",
            "does not require SubAgents, clean sessions, extra gates, or new schema",
            "doing, direction-checking, acceptance, and learning",
            "Task/SubTask/Step",
            "Pulse/hooks/Mission Review",
            "acceptance evidence",
            "Mission Shared Context / Shared Risk Context",
            "same-agent phase separation",
            "Low-risk reversible work stays lightweight",
        ):
            self.assertIn(phrase, compact_policy)

        self.assertIn("Role-Separated Review Policy", skill_text)
        self.assertIn("responsibility separation", skill_text)
        self.assertIn("SubAgents are optional carriers", subagents)
        self.assertIn("`advise` or `grade`", subagents)
        self.assertIn("candidate findings", subagents)
        self.assertIn("direction-checking", hooks_lower)
        self.assertIn("acceptance grading", hooks_lower)
        self.assertIn("mission_review.acceptance_gap", hooks_lower)
        self.assertIn("resources/platforms/*.md", skill_text)
        self.assertIn("scripts/*review_packet.py", skill_text)
        self.assertIn("codex -s read-only -a never exec --ephemeral", codex_adapter)
        self.assertIn("--run-cli", codex_adapter)
        self.assertIn("--orchestration-mode recommended", codex_adapter)
        self.assertIn("Codex Review Orchestration Mode", codex_adapter)
        self.assertIn("recommended Codex tplan path", codex_adapter)
        self.assertIn("not a mandatory four-agent runtime", codex_adapter)
        self.assertIn("subagent-dispatch.json", codex_adapter)
        self.assertIn("candidate_findings_only", codex_script)
        self.assertIn("multi_agent_v1.spawn_agent", codex_script)
        self.assertIn("--run-cli", codex_script)
        self.assertIn("--orchestration-mode", codex_script)
        self.assertIn("recommended_codex_tplan_path", codex_script)
        self.assertIn("Claude Code Role-Separated Review Adapter", claude_adapter)
        self.assertIn("https://code.claude.com/docs/en/sub-agents", claude_adapter)
        self.assertIn("permissionMode: plan", claude_adapter)
        self.assertIn("OpenCode Role-Separated Review Adapter", opencode_adapter)
        self.assertIn("https://open-code.ai/en/docs/agents", opencode_adapter)
        self.assertIn("edit: deny", opencode_adapter)
        self.assertIn("deny `bash`", opencode_adapter)
        self.assertIn("tplan.claude_code_adapter.v0.1", platform_script)
        self.assertIn("tplan.opencode_adapter.v0.1", platform_script)
        self.assertIn("permissionMode: plan", platform_script)
        self.assertIn('"read": "allow"', platform_script)
        self.assertIn('"bash": "deny"', platform_script)
        self.assertIn('"edit": "deny"', platform_script)
        self.assertNotIn('"git diff*": "allow"', platform_script)
        self.assertIn("generated_platform_carrier_artifacts_only", platform_script)
        self.assertIn("重要任务不要让同一股惯性同时负责做、判断方向、给自己验收和沉淀经验", methodology)
        self.assertIn("不是四个常驻 agent", methodology)

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

    def test_pressure_tests_cover_role_separated_review_policy(self):
        text = (REPO / "tests" / "tplan" / "skill_ab_pressure_tests.md").read_text(encoding="utf-8")
        compact_text = re.sub(r"\s+", " ", text)
        for phrase in (
            "Group 5: Role-Separated Review Policy",
            "doing, direction-checking, acceptance, and learning",
            "not a four-agent workflow",
            "low-risk reversible work stays lightweight",
            "same-agent phase separation",
            "Mission Shared Context",
            "Shared Risk Context",
            "fails if it requires SubAgents, clean sessions, new gates, or new schema",
            "Codex Adapter Implementation",
            "codex_review_packet.py",
            "Codex Review Orchestration Mode",
            "--orchestration-mode recommended",
            "grade required",
            "strict",
            "codex -s read-only -a never exec --ephemeral",
            "Claude Code Adapter Implementation",
            "--platform claude-code",
            "permissionMode: plan",
            "OpenCode Adapter Implementation",
            "--platform opencode",
            "mode: subagent",
            "edit: deny",
            "task: deny",
            "bash: deny",
            "candidate findings",
        ):
            self.assertIn(phrase, compact_text)

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
        self.assertIn("如果某个子任务发现的问题只影响自己，就留在本地任务里", methodology)
        self.assertIn("如果它会影响其他子任务对“还值不值得继续”的判断，就上浮成共享风险", methodology)
        self.assertIn("普通进展、局部日志、一次性失败和已经被局部修掉的小问题", methodology)

    def test_mission_shared_context_memory_contract_is_documented(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        resources = "\n".join(
            (SKILL / "resources" / name).read_text(encoding="utf-8")
            for name in ("schema.md", "hooks.md")
        )
        methodology = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")

        for phrase in (
            ".tplan/shared_contexts",
            "tplan_mission_shared_context-<mission_id>.md",
            "Mission identity",
            "preflight_mission.py",
            "source_contexts",
        ):
            self.assertIn(phrase, skill_text)
            self.assertIn(phrase, resources)

        self.assertIn("Mission 级共享记忆", methodology)
        self.assertIn("不是一个独立的派生状态", methodology)
        self.assertIn("继续旧 Mission", methodology)
        self.assertIn("新建 Mission", methodology)

    def test_continuation_authorization_contract_is_documented(self):
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        resources = "\n".join(
            (SKILL / "resources" / name).read_text(encoding="utf-8")
            for name in ("schema.md", "hooks.md")
        )
        methodology = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")
        pressure_text = (REPO / "tests" / "tplan" / "long_task_ab_tests.md").read_text(encoding="utf-8")
        hook = json.loads((SKILL / "templates" / "hook-output.json").read_text(encoding="utf-8"))

        for phrase in (
            "Continuation Authorization",
            "continuation_authorization",
            "evidence_shape_lint",
            "defect_classification",
            "acceptance_blocking",
            "batchable_detail",
            "count-based reminders are triggers, not decisions",
            "shape-only evidence",
            "repeated_same_path_attempt",
            "post_continuation_defect",
            "high_cost_or_high_blast_radius_continuation",
        ):
            self.assertIn(phrase, skill_text)
            self.assertIn(phrase, resources)

        self.assertIn("继续授权", methodology)
        self.assertIn("次数提醒只负责叫醒，不负责判停", methodology)
        self.assertIn("继续同一路径前", methodology)
        self.assertIn("阻止 agent 把“看起来只差一点”误当成继续理由", methodology)
        self.assertIn("下一步会带来什么新的验收证据", methodology)
        self.assertIn("Continuation Authorization Pressure", pressure_text)
        self.assertIn("placeholder/sample red-team anchors", pressure_text)
        self.assertIn("continuation_authorization", hook)
        self.assertIn("evidence_shape_lint", hook["continuation_authorization"])

    def test_mission_health_pulse_contract_is_documented(self):
        resources = "\n".join(
            (SKILL / "resources" / name).read_text(encoding="utf-8")
            for name in ("schema.md", "hooks.md")
        )
        methodology = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")
        pressure_text = (REPO / "tests" / "tplan" / "mission_health_pulse_ab_tests.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Snapshot / Pulse / Gate",
            "Scripts observe. Pulse routes. Gates decide.",
            "mission_pulse",
            "tplan.pulse.v0.2",
            "Candidate Collection",
            "Gate Arbitration",
            "review_trigger_candidates",
            "winning_candidate",
            "suppressed_candidates",
            "arbitration_trace",
            "priority_class",
            "freshness",
            "Snapshot reports observable state",
            "Pulse routes observable signals to an existing Gate",
            "Gate makes the semantic decision",
            "next_gate=continue",
            "next_gate=health_check",
            "not a standalone undefined gate",
            "not a new judgment center",
            "not decide Mission ROI",
            "not decide semantic truth",
            "scripts/consume_pulse.py",
            "pulse_state.consumed_candidates",
            "pulse_consumed",
            "candidate_state=stale",
            "remain active by design",
            "fresh acceptance evidence movement",
            "scripts/mission_pulse.py",
            "survey --pulse",
        ):
            self.assertIn(phrase, resources)

        for phrase in (
            "普通低风险推进",
            "同一路径准备继续",
            "第三次局部修补",
            "共享风险影响后续任务",
            "多分支开始膨胀",
            "Mission 目标、验收面或权限不清",
            "只有出现事件信号时才进入 Pulse",
            "显式记录消费",
            "stale",
            "shared risk、same-path continuation",
        ):
            self.assertIn(phrase, methodology)

        for phrase in (
            "Scenario A: Routine Checkpoint Must Stay Light",
            "Scenario B: Same-path Continue Needs Authorization",
            "Scenario C: Repeated Local Repair Routes To Anti-Spiral Or Subtraction",
            "Scenario D: Shared Risk Must Not Stay Buried",
            "Scenario E: Branch Cleanup Must Use Existing Gates",
            "Scenario F: Mission Drift Or Authority Gap Stops The Path",
            "Hard failure",
        ):
            self.assertIn(phrase, pressure_text)

    def test_mission_pulse_priority_classes_are_schema_documented(self):
        runtime = load_tplan_runtime()
        schema = (SKILL / "resources" / "schema.md").read_text(encoding="utf-8")

        for priority_class in sorted(runtime.MISSION_PULSE_CANDIDATE_PRIORITIES):
            self.assertIn(f"`{priority_class}`", schema)

    def test_mission_pulse_hooks_example_is_internally_consistent(self):
        hooks = (SKILL / "resources" / "hooks.md").read_text(encoding="utf-8")
        match = re.search(r"```json\n(.*?)\n```", hooks, flags=re.DOTALL)
        self.assertIsNotNone(match, "hooks.md should include a JSON mission_pulse example")
        example = json.loads(match.group(1))
        candidates = example["review_trigger_candidates"]

        if not candidates:
            self.assertIsNone(example["winning_candidate"])
            self.assertEqual(example["suppressed_candidates"], [])
            self.assertEqual(example["arbitration_trace"], [])
            return

        self.assertIsNotNone(example["winning_candidate"])
        self.assertEqual(
            example["winning_candidate"]["signal"],
            candidates[0]["signal"],
        )
        self.assertEqual(example["suppressed_candidates"], [])
        self.assertEqual(len(example["arbitration_trace"]), len(candidates))
        self.assertEqual(example["arbitration_trace"][0]["decision"], "selected")

    def test_shared_risk_context_has_reproducible_ab_simulator_contract(self):
        pressure_text = (REPO / "tests" / "tplan" / "long_task_ab_tests.md").read_text(encoding="utf-8")
        simulator = REPO / "tests" / "tplan" / "shared_risk_agent_simulator.py"
        simulator_test = REPO / "tests" / "tplan" / "test_shared_risk_agent_simulator.py"

        for phrase in (
            "Shared Risk Context Late Stop Pressure",
            "invalid_evidence_risk",
            "failure_risk",
            "risk_adjusted_value",
            "health_check",
            "Hard failure: continues an expensive full-chain rerun",
        ):
            self.assertIn(phrase, pressure_text)

        self.assertTrue(simulator.exists(), "missing shared-risk scripted agent simulator")
        self.assertTrue(simulator_test.exists(), "missing shared-risk simulator test")
        combined = simulator.read_text(encoding="utf-8") + "\n" + simulator_test.read_text(encoding="utf-8")
        for phrase in (
            "shared_risk_agent_simulator.py",
            "scripted_agent_score",
            "stop_latency",
            "expensive_rerun_attempts_before_gate",
            "steps_until_first_safe_gate",
            "active_shared_risk_blocks_ungated_continuation",
            "record_risk_context.py",
            "risk_assessment_required",
            "invalid_environment_evidence",
            "mechanical_score",
        ):
            self.assertIn(phrase, combined)

    def test_continuation_authorization_has_reproducible_ab_simulator_contract(self):
        simulator = REPO / "tests" / "tplan" / "continuation_authorization_ab_simulator.py"
        simulator_test = REPO / "tests" / "tplan" / "test_continuation_authorization_ab_simulator.py"

        self.assertTrue(simulator.exists(), "missing continuation-authorization scripted A/B simulator")
        self.assertTrue(simulator_test.exists(), "missing continuation-authorization simulator test")

        combined = simulator.read_text(encoding="utf-8") + "\n" + simulator_test.read_text(encoding="utf-8")
        for phrase in (
            "placeholder/sample",
            "red-team anchor defects",
            "continuation_authorization_ab_simulator.py",
            "pre_continuation_authorization",
            "continuation_authorization",
            "authorization_latency",
            "expensive_same_path_continue_attempts_before_gate",
            "continuation_authorization_blocks_ungated_same_path",
            "targeted_fix",
            "mechanical_score",
        ):
            self.assertIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
