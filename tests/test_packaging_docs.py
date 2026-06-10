import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def parse_frontmatter_mapping(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"frontmatter line is not a key/value pair: {raw_line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"frontmatter key is empty: {raw_line!r}")
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        elif ": " in value:
            raise ValueError(
                "frontmatter values containing ': ' must be quoted for strict YAML compatibility: "
                f"{raw_line!r}"
            )
        parsed[key] = value
    return parsed


class PackagingDocsTests(unittest.TestCase):
    def assert_skill_frontmatter_is_parseable(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"), f"{path} missing frontmatter")
        end = text.find("\n---", 4)
        self.assertGreater(end, 0, f"{path} missing frontmatter terminator")
        frontmatter = text[4:end]
        try:
            parsed = parse_frontmatter_mapping(frontmatter)
        except ValueError as exc:
            self.fail(f"{path} has invalid frontmatter: {exc}")
        self.assertIsInstance(parsed, dict, f"{path} frontmatter must be a mapping")
        self.assertIn("name", parsed, f"{path} frontmatter missing name")
        self.assertIn("description", parsed, f"{path} frontmatter missing description")

    def test_readme_names_current_skill_pack_and_tplan(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("mindthus:tplan", readme)
        self.assertIn("mindthus:*", readme)
        self.assertIn("当前仓库版本：`v1.1.0`", readme)
        self.assertIn("scripts/log-fidelity-usage.py", readme)
        self.assertIn("data/fidelity-usage-log.jsonl", readme)
        self.assertIn("AGPLv3 + commercial dual licensing", readme)
        self.assertIn("SELA", readme)
        self.assertIn("时机检查", readme)
        self.assertIn("docs/methodologies", readme)
        self.assertIn("安装", readme)
        self.assertIn("验证", readme)
        self.assertIn("从哪里开始", readme)
        self.assertIn("可选：记录使用效果", readme)
        self.assertIn("版本与许可", readme)
        self.assertNotIn("维护者需要关注", readme)
        self.assertNotIn("judge JSON", readme)
        self.assertNotIn("not_applicable", readme)
        self.assertNotIn("方法分层纪律", readme)

    def test_readme_keeps_release_details_out_of_new_user_intro(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        intro = readme.split("## 为什么值得试", 1)[0]

        for phrase in (
            "当前仓库版本",
            "v1.0 Method Fidelity Framework",
            "scripts/log-fidelity-usage.py",
            "版本脉络",
            "GitHub Releases",
            "维护者",
            "judge JSON",
        ):
            self.assertNotIn(phrase, intro)

    def test_readme_links_to_chinese_manual(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("SELA / 系统效率碾压局部优势", readme)
        self.assertIn("Mainline-Path Game", readme)
        self.assertIn("3L5S / 三层五步", readme)
        self.assertIn("EDSP / Extreme Deduction + Scenario Projection", readme)
        self.assertIn("WAE / Workflow-Agentic-Evidence", readme)
        self.assertIn("TVG / Thinking Value-Gain", readme)
        self.assertIn("Anti-Spiral / 反螺旋自检", readme)
        self.assertIn("讲清整体与局部", readme)
        self.assertIn("主线承载方案", readme)
        self.assertIn("讲清问题如何从混乱信号走到可执行步骤", readme)
        self.assertIn("脚本、agent、review gate 都在“管事”", readme)
        self.assertIn("死亡螺旋", readme)
        self.assertIn("何时拿起哪把刀", readme)
        self.assertIn("可安装的判断工具箱", readme)
        self.assertIn("你可能见过这些情况", readme)
        self.assertIn("把文本更接近某个“好”的标准", readme)
        self.assertIn("不是季度 OKR 表", readme)
        self.assertIn("长任务执行中的动态工作流", readme)
        self.assertNotIn("实际调用时仍使用", readme)

    def test_public_docs_sync_mpg_unreleased_positioning(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")

        for phrase in (
            "MPG / 主线-路径博弈",
            "先讲人话",
            "推演耐久性",
            "MPG-AQM",
            "非精准量化显影",
        ):
            self.assertIn(phrase, readme)
            self.assertIn(phrase, agents)

        for phrase in (
            "## Unreleased",
            "MPG / 主线-路径博弈",
            "Path-Carrying Strategy / 主线承载方案",
            "Human-Readable First / 先讲人话",
            "Reasoning Durability / 推演耐久性",
            "MPG-AQM Visibility Layer / 主线-路径显影层",
        ):
            self.assertIn(phrase, changelog)

    def test_anti_spiral_methodology_resource_exists(self):
        text = (REPO / "docs" / "methodologies" / "anti-spiral-self-audit.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Anti-Spiral Self-Audit", text)
        self.assertIn("methodology resource", text)
        self.assertIn("tplan", text)
        self.assertIn("Third touch, stop first", text)

    def test_changelog_documents_v0_5_release_in_chinese(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## v0.6.3", changelog)
        self.assertIn("发布日期：2026-06-05", changelog)
        self.assertIn("自适应记录密度", changelog)
        self.assertIn("用户可读输出适配", changelog)
        self.assertIn("SubAgents are scouts, not controllers", changelog)
        self.assertIn("## v0.6", changelog)
        self.assertIn("## v0.6.1", changelog)
        self.assertIn("发布日期：2026-05-27", changelog)
        self.assertIn("release pack builder", changelog)
        self.assertIn("source: \"./claude-plugin\"", changelog)
        self.assertIn("Claude Code marketplace", changelog)
        self.assertIn("OpenCode、Claude Code、Codex", changelog)
        self.assertIn("docs/internal/", changelog)
        self.assertIn("--force", changelog)
        self.assertIn("完整包 validator", changelog)
        self.assertIn("发布日期：2026-05-26", changelog)
        self.assertIn("v0.6 和 v0.5.x 的区别", changelog)
        self.assertIn("认知原语", changelog)
        self.assertIn("还没有完整到能成为方法论或哲学框架", changelog)
        self.assertIn("决定判断质量", changelog)
        self.assertIn("微型控制点", changelog)
        self.assertIn("之所以叫“原语”", changelog)
        self.assertIn("之所以叫“认知”", changelog)
        self.assertIn("如何理解、判断、取舍和表达", changelog)
        self.assertIn("不是代码实现细节", changelog)
        self.assertIn("能力跃迁", changelog)
        self.assertIn("AI 认知体系的底层分析/决策底盘", changelog)
        self.assertIn("底盘能力", changelog)
        self.assertIn("`60-70`", changelog)
        self.assertIn("`90+`", changelog)
        self.assertIn("最小充分镜头", changelog)
        self.assertIn("证据与结论上限", changelog)
        self.assertIn("视角与激励施压", changelog)
        self.assertIn("反螺旋刹车", changelog)
        self.assertIn("不堆抽象术语墙", changelog)
        self.assertIn("判断内核入口层", changelog)
        self.assertIn("介入边界", changelog)
        self.assertIn("判断对象路由", changelog)
        self.assertIn("上下文注入口", changelog)
        self.assertIn("方法仲裁", changelog)
        self.assertIn("执行影响要求", changelog)
        self.assertIn("单模型版本", changelog)
        self.assertIn("不声明跨模型鲁棒性", changelog)
        self.assertIn("## v0.5.2", changelog)
        self.assertIn("发布日期：2026-05-23", changelog)
        self.assertIn("No Abstract Jargon Wall", changelog)
        self.assertIn("单 Agent 多角色压力检查", changelog)
        self.assertIn("单 Agent 多角色挑战", changelog)
        self.assertIn("压线摇摆场景", changelog)
        self.assertIn("## v0.5 + v0.5.1", changelog)
        self.assertIn("GitHub Release 以 `v0.5.1` 发布", changelog)
        self.assertIn("没有单独发布 GitHub Release `v0.5`", changelog)
        self.assertIn("发布日期：2026-05-18", changelog)
        self.assertIn("方法分层纪律", changelog)
        self.assertIn("主思想", changelog)
        self.assertIn("从属补漏", changelog)
        self.assertIn("SELA", changelog)
        self.assertIn("时机检查", changelog)
        self.assertIn("EDSP frontmatter 修复", changelog)
        self.assertIn("python3 -m unittest discover -s tests -v", changelog)

    def test_changelog_release_sections_are_chinese_and_not_duplicated(self):
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        lines = changelog.splitlines()
        self.assertEqual(lines.count("## v1.1.0"), 1)
        self.assertEqual(lines.count("## v1.0.1"), 1)
        self.assertEqual(lines.count("## v1.0"), 1)
        self.assertEqual(lines.count("## v0.6.3"), 1)
        self.assertEqual(lines.count("## v0.6.2"), 1)
        self.assertEqual(lines.count("## v0.6.1"), 1)
        self.assertEqual(lines.count("## v0.6"), 1)
        self.assertEqual(lines.count("## v0.5.2"), 1)
        self.assertEqual(lines.count("## v0.5 + v0.5.1"), 1)
        self.assertEqual(lines.count("## v0.5.1"), 0)
        self.assertEqual(lines.count("## v0.5"), 0)
        self.assertEqual(lines.count("## v0.4"), 1)
        self.assertIn("发布日期：2026-05-09", changelog)
        self.assertNotIn("Release date:", changelog)

    def test_sela_methodology_names_the_overall_local_tradeoff(self):
        text = (REPO / "skills" / "sela" / "resources" / "methodology.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("整体与局部", text)
        self.assertIn("可逆", text)
        self.assertIn("反馈", text)
        self.assertIn("可修正", text)
        self.assertIn("不是一次性静态最优", text)

    def test_methodology_pages_exist_and_cover_their_core_claims(self):
        cases = [
            ("sela.md", "系统效率碾压局部优势"),
            ("mpg.md", "Mainline-Path Game"),
            ("3l5s.md", "三层五步"),
            ("edsp.md", "Extreme Deduction + Scenario Projection"),
            ("wae.md", "Workflow-Agentic-Evidence"),
            ("tvg.md", "Thinking Value-Gain"),
            ("tplan.md", "OKR-Runtime"),
            ("anti-spiral-self-audit.md", "反螺旋自检"),
            ("shared-primitives.md", "Cognitive Primitives"),
        ]
        for name, phrase in cases:
            text = (REPO / "docs" / "methodologies" / name).read_text(encoding="utf-8")
            self.assertIn(phrase, text, name)
            self.assertIn("## 这是什么", text, name)
            self.assertIn("## 解决什么问题", text, name)
            self.assertIn("## 核心判断", text, name)
            self.assertIn("## 怎么用", text, name)
            self.assertIn("## 具体案例", text, name)
            self.assertGreaterEqual(text.count("### 案例"), 2, name)
            self.assertIn("## 常见误用", text, name)
            self.assertIn("## 边界", text, name)
            self.assertIn("## 与其他方法的关系", text, name)
            self.assertIn("## 导航", text, name)

    def test_shared_primitives_is_an_index_not_an_extra_method_layer(self):
        text = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Cognitive Primitives / 认知原语",
            "方法论之外的小而关键的判断碎片",
            "通过横切方式介入不同方法",
            "This is not a new method layer",
            "Cognitive Primitive Index / 认知原语索引",
            "Use cognitive primitives by reference",
            "Primary owner",
            "Do not copy the full definition",
            "Minimal Sufficient Lens",
            "Evidence / Claim Ceiling",
            "Perspective Pressure",
            "Anti-Spiral",
            "No Abstract Jargon Wall",
        ):
            self.assertIn(phrase, text)

    def test_internal_skill_design_patterns_are_not_user_facing(self):
        text = (REPO / "docs" / "internal" / "skill-design-patterns.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Internal maintainer note",
            "not part of the shallow user-facing guide",
            "learn that induction method",
            "Judgment Kernel Skill",
            "Cognitive Control Skill",
            "Runtime Governance Skill",
            "Name the cognitive role before naming the implementation shape",
            "Mindthus pattern",
            "General implementation shapes",
        ):
            self.assertIn(phrase, text)

        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("skill-design-patterns.md", readme)
        self.assertNotIn("Judgment Kernel Skill", readme)

    def test_v0_6_version_acceptance_records_single_model_scope(self):
        text = (
            REPO / "tests" / "mindthus_v0_6_version_acceptance_2026-05-26.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "Mindthus v0.6 Version Acceptance",
            "single-model release-grade acceptance",
            "Cross-model testing is explicitly deferred",
            "Behavior score: `98 / 100`",
            "Conservative effective score: `92 / 100`",
            "v0.6 is accepted",
            "should not say",
            "proven across models",
        ):
            self.assertIn(phrase, text)

    def test_tplan_methodology_shows_execution_driven_adaptive_planning(self):
        text = (REPO / "docs" / "methodologies" / "tplan.md").read_text(encoding="utf-8")
        for phrase in (
            "OKR-Runtime",
            "动态工作流",
            "每次 checkpoint、evidence、blocker 或 decision hook 都能触发任务树调整",
            "把稳定 Mission 转成任务状态、验收证据、决策钩子和可恢复执行",
            "作为对外主口径",
            "`tplan` 的名字不变",
            "不是为了兼容旧用户",
            "状态恢复、证据约束和决策权限语义",
            "作为 schema migration",
            "`Mission` 对齐 `Objective`",
            "`acceptance criteria / acceptance evidence` 对齐 `Key Results`",
            "`Task / SubTask / Step` 对齐 `initiatives / actions`",
            "Mission 接近 Objective",
            "acceptance evidence 接近 Key Results",
            "OKR + dynamic workflow runtime",
            "不替代项目管理工具",
            "不追求人类团队 OKR 管理",
            "执行驱动的自适应规划",
            "Mission 固定",
            "任务树可以在证据、阻碍和决策信号约束下持续演化",
            "### 架构流程图",
            "```mermaid",
            "选择 active leaf",
            "执行反馈",
            "split signal",
            "blocker / stop report",
            "decision packet",
            "Anti-Spiral gate",
            "执行不会随手重写计划",
        ):
            self.assertIn(phrase, text)

    def test_skill_frontmatter_has_required_keys(self):
        for path in sorted((REPO / "skills").glob("*/SKILL.md")):
            self.assert_skill_frontmatter_is_parseable(path)

    def test_skill_frontmatter_parser_rejects_unquoted_nested_colon(self):
        with self.assertRaises(ValueError):
            parse_frontmatter_mapping(
                "name: tplan\n"
                "description: Use when an AI agent needs an OKR-Runtime: a Mission needs state\n"
            )

    def test_codex_install_doc_names_tplan(self):
        install = (REPO / ".codex" / "INSTALL.md").read_text(encoding="utf-8")
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        script = (REPO / "scripts" / "install-skills.sh").read_text(encoding="utf-8")
        self.assertIn("mindthus:tplan", install)
        self.assertIn("scripts/install-skills.sh", install)
        for text in (install, readme, script):
            self.assertIn("CODEX_HOME", text)
            self.assertIn("skills/mindthus", text)
            self.assertNotIn(".agents/skills/mindthus", text)

    def test_install_script_exists_and_has_valid_shell_syntax(self):
        script = REPO / "scripts" / "install-skills.sh"
        self.assertTrue(script.exists())
        result = subprocess.run(["bash", "-n", str(script)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_codex_install_script_links_pack_under_codex_home(self):
        script = REPO / "scripts" / "install-skills.sh"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            home = tmp_dir / "home"
            codex_home = tmp_dir / "codex-home"
            home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["CODEX_HOME"] = str(codex_home)

            result = subprocess.run(
                ["bash", str(script), "codex", "--repo", str(REPO), "--force"],
                text=True,
                capture_output=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            target = codex_home / "skills" / "mindthus"
            self.assertTrue(target.is_symlink(), result.stdout)
            self.assertEqual(target.resolve(), REPO / "skills")
            self.assertTrue((target / "tplan" / "SKILL.md").exists())
            self.assertIn(str(target), result.stdout)

    def test_codex_install_script_defaults_to_home_codex_skills(self):
        script = REPO / "scripts" / "install-skills.sh"
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)
            env.pop("CODEX_HOME", None)

            result = subprocess.run(
                ["bash", str(script), "codex", "--repo", str(REPO), "--force"],
                text=True,
                capture_output=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            target = home / ".codex" / "skills" / "mindthus"
            self.assertTrue(target.is_symlink(), result.stdout)
            self.assertEqual(target.resolve(), REPO / "skills")
            self.assertTrue((target / "tplan" / "SKILL.md").exists())

    def test_release_pack_builder_creates_claude_marketplace_root_layout(self):
        script = REPO / "scripts" / "build-release-pack.py"
        self.assertTrue(script.exists())
        syntax = subprocess.run(
            ["python3", "-m", "py_compile", str(script)],
            text=True,
            capture_output=True,
        )
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        blocked = subprocess.run(
            ["python3", str(script), "--out", str(REPO), "--force"],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("protected source tree", blocked.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "release"
            result = subprocess.run(
                ["python3", str(script), "--out", str(out)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            marketplace_path = out / "claude-code" / ".claude-plugin" / "marketplace.json"
            plugin_path = out / "claude-code" / "claude-plugin" / ".claude-plugin" / "plugin.json"
            self.assertTrue(marketplace_path.exists())
            self.assertTrue(plugin_path.exists())

            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
            plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
            source = marketplace["plugins"][0]["source"]
            self.assertEqual(source, "./claude-plugin")
            self.assertNotIn("..", source)
            self.assertEqual(plugin["version"], "1.1.0")
            self.assertTrue((out / "claude-code" / "claude-plugin" / "skills" / "tplan" / "SKILL.md").exists())
            self.assertTrue((out / "claude-code" / "claude-plugin" / "skills" / "mpg" / "SKILL.md").exists())
            for path in sorted((out / "claude-code" / "claude-plugin" / "skills").glob("*/SKILL.md")):
                self.assert_skill_frontmatter_is_parseable(path)
            self.assertTrue(
                (out / "claude-code" / "claude-plugin" / "scripts" / "run-fidelity-judge.py").exists()
            )
            self.assertTrue(
                (out / "claude-code" / "claude-plugin" / "scripts" / "log-fidelity-usage.py").exists()
            )
            self.assertTrue(
                (
                    out
                    / "claude-code"
                    / "claude-plugin"
                    / "docs"
                    / "methodologies"
                    / "shared-primitives.md"
                ).exists()
            )
            self.assertFalse((out / "claude-code" / "claude-plugin" / "docs" / "internal").exists())
            self.assertFalse((out / "claude-code" / "claude-plugin" / "docs" / "superpowers").exists())

            self.assertTrue((out / "codex" / "skills" / "mindthus" / "tplan" / "SKILL.md").exists())
            self.assertTrue((out / "codex" / "skills" / "mindthus" / "mpg" / "SKILL.md").exists())
            for path in sorted((out / "codex" / "skills" / "mindthus").glob("*/SKILL.md")):
                self.assert_skill_frontmatter_is_parseable(path)
            self.assertTrue((out / "codex" / "AGENTS.md").exists())
            self.assertTrue((out / "codex" / "docs" / "methodologies" / "shared-primitives.md").exists())
            self.assertFalse((out / "codex" / "docs" / "internal").exists())
            self.assertFalse((out / "codex" / "docs" / "superpowers").exists())
            codex_agents = (out / "codex" / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("`skills/mindthus/sela/`", codex_agents)
            self.assertIn("`skills/mindthus/mpg/`", codex_agents)
            self.assertNotIn("`skills/sela/`", codex_agents)
            codex_sela_doc = (out / "codex" / "docs" / "methodologies" / "sela.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("../../skills/mindthus/sela/SKILL.md", codex_sela_doc)
            self.assertNotIn("../../skills/sela/SKILL.md", codex_sela_doc)
            codex_tvg_skill = (out / "codex" / "skills" / "mindthus" / "tvg" / "SKILL.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("python3 skills/mindthus/tvg/scripts/trace/init.py", codex_tvg_skill)
            self.assertNotIn("python3 skills/tvg/scripts/trace/init.py", codex_tvg_skill)
            self.assertTrue(
                (out / "opencode" / ".opencode" / "skills" / "mindthus" / "tplan" / "SKILL.md").exists()
            )
            self.assertTrue(
                (out / "opencode" / ".opencode" / "skills" / "mindthus" / "mpg" / "SKILL.md").exists()
            )
            for path in sorted((out / "opencode" / ".opencode" / "skills" / "mindthus").glob("*/SKILL.md")):
                self.assert_skill_frontmatter_is_parseable(path)
            self.assertTrue((out / "opencode" / "AGENTS.md").exists())
            self.assertTrue((out / "opencode" / "docs" / "methodologies" / "shared-primitives.md").exists())
            self.assertFalse((out / "opencode" / "docs" / "internal").exists())
            self.assertFalse((out / "opencode" / "docs" / "superpowers").exists())
            opencode_agents = (out / "opencode" / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("`.opencode/skills/mindthus/sela/`", opencode_agents)
            self.assertIn("`.opencode/skills/mindthus/mpg/`", opencode_agents)
            self.assertNotIn("`skills/sela/`", opencode_agents)
            opencode_sela_doc = (
                out / "opencode" / "docs" / "methodologies" / "sela.md"
            ).read_text(encoding="utf-8")
            self.assertIn("../../.opencode/skills/mindthus/sela/SKILL.md", opencode_sela_doc)
            self.assertNotIn("../../skills/sela/SKILL.md", opencode_sela_doc)
            opencode_tvg_skill = (
                out / "opencode" / ".opencode" / "skills" / "mindthus" / "tvg" / "SKILL.md"
            ).read_text(encoding="utf-8")
            self.assertIn("python3 .opencode/skills/mindthus/tvg/scripts/trace/init.py", opencode_tvg_skill)
            self.assertNotIn("python3 skills/tvg/scripts/trace/init.py", opencode_tvg_skill)

            skill_names = ("3l5s", "sela", "mpg", "edsp", "wae", "tvg", "tplan", "using-mindthus")
            for platform_dir in (out / "codex", out / "opencode"):
                markdown = "\n".join(
                    path.read_text(encoding="utf-8") for path in sorted(platform_dir.rglob("*.md"))
                )
                for skill_name in skill_names:
                    self.assertNotIn(f"skills/{skill_name}/", markdown)


if __name__ == "__main__":
    unittest.main()
