import json
import os
import shutil
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
        for phrase in (
            "mindthus:tplan",
            "mindthus:*",
            "当前仓库版本：`v1.4.3`",
            "局部正确",
            "输入定框审计",
            "framing-risk",
            "AGPLv3 + commercial dual licensing",
            "## 安装",
            "## 验证",
            "## 版本与许可",
        ):
            self.assertIn(phrase, readme)
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
        for phrase in (
            "SELA / 系统效率碾压局部优势",
            "MPG / 主线-路径博弈 / Mainline-Path Game",
            "3L5S / 三层五步",
            "EDSP / Extreme Deduction + Scenario Projection",
            "WAE / Workflow-Agentic-Evidence",
            "TVG / Thinking Value-Gain",
            "TPlan / OKR-Runtime",
            "Anti-Spiral / 反螺旋自检",
        ):
            self.assertIn(phrase, readme)
        self.assertNotIn("实际调用时仍使用", readme)

    def test_public_docs_sync_mpg_unreleased_positioning(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("MPG / 主线-路径博弈", readme)
        self.assertIn("MPG / 主线-路径博弈", agents)
        self.assertIn("## Unreleased", changelog)
        self.assertIn("MPG / 主线-路径博弈", changelog)

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
        self.assertEqual(lines.count("## v1.1.2"), 1)
        self.assertEqual(lines.count("## v1.1.1"), 1)
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

    def test_worktree_lifecycle_doc_classifies_cleanup_safely(self):
        text = (REPO / "docs" / "internal" / "worktree-lifecycle.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Worktree Lifecycle",
            "Audit date: `2026-06-28`",
            "git worktree list --porcelain",
            "Do not remove a dirty or detached worktree blind.",
            "### Keep",
            "### Archive Or Review Before Removal",
            "### Removed In This Cleanup",
            "### Remove Candidates",
            "external detached Codex worktree",
            "archive refs only",
            "The only remaining non-main worktree is the external detached Codex",
            "codex/issue-27-thin-core-tplan-adapter",
            "codex/v0.9-method-fidelity-harness",
            "release/v0.6.2-prep",
        ):
            self.assertIn(phrase, text)

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
            "Snapshot / Pulse / Gate",
            "winning_candidate",
            "suppressed_candidates",
            "arbitration_trace",
            "基于 Mission signal 的轻量路由",
            "执行不会随手重写计划",
        ):
            self.assertIn(phrase, text)

    def test_skill_frontmatter_has_required_keys(self):
        for path in sorted((REPO / "skills").glob("*/SKILL.md")):
            self.assert_skill_frontmatter_is_parseable(path)

    def test_mindthus_skill_entrypoints_stay_within_size_budget(self):
        budget_bytes = 10 * 1024
        oversized = {
            path.parent.name: path.stat().st_size
            for path in sorted((REPO / "skills").glob("*/SKILL.md"))
            if path.parent.name != "using-mindthus" and path.stat().st_size > budget_bytes
        }
        self.assertEqual(
            oversized,
            {},
            "Mindthus SKILL.md files should stay thin; move long guidance to resources/ or docs/methodologies/",
        )

    def test_using_mindthus_entrypoint_stays_thin_enough_for_attention(self):
        budget_bytes = 11 * 1024
        path = REPO / "skills" / "using-mindthus" / "SKILL.md"
        self.assertLessEqual(
            path.stat().st_size,
            budget_bytes,
            "using-mindthus is the routing entrypoint; keep it under 11KiB and move long semantics to AOP primitives/scripts.",
        )

    def test_using_mindthus_entrypoint_stays_within_word_attention_budget(self):
        path = REPO / "skills" / "using-mindthus" / "SKILL.md"
        word_count = len(path.read_text(encoding="utf-8").split())
        self.assertLessEqual(
            word_count,
            1100,
            "using-mindthus should stay under 1100 words; move detailed semantics to shared primitives, resources, or validators.",
        )

    def test_using_mindthus_entrypoint_has_no_empty_markdown_headings(self):
        path = REPO / "skills" / "using-mindthus" / "SKILL.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        empty_headings: list[str] = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue
            next_content = next(
                (
                    candidate.strip()
                    for candidate in lines[index + 1 :]
                    if candidate.strip()
                ),
                "",
            )
            if next_content.startswith("#"):
                empty_headings.append(stripped)

        self.assertEqual(
            empty_headings,
            [],
            "using-mindthus should not keep empty routing headings; every heading must carry executable guidance.",
        )

    def test_using_mindthus_entrypoint_limits_marker_chain_density(self):
        path = REPO / "skills" / "using-mindthus" / "SKILL.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        long_lines = [
            (line_number, len(line))
            for line_number, line in enumerate(lines, start=1)
            if len(line) > 420
        ]
        semicolon_chains = [
            (line_number, line.count(";"))
            for line_number, line in enumerate(lines, start=1)
            if line.count(";") > 10
        ]

        self.assertEqual([], long_lines, "using-mindthus has overlong marker lines")
        self.assertEqual([], semicolon_chains, "using-mindthus has dense semicolon marker chains")

    def assert_release_pack_excludes_runtime_artifacts(self, out: Path) -> None:
        forbidden_dirs = {
            ".git",
            ".pytest_cache",
            ".tplan",
            ".tvg",
            "__pycache__",
            "artifacts",
            "logs",
            "test",
            "tests",
        }
        forbidden_suffixes = {
            ".gif",
            ".jpeg",
            ".jpg",
            ".log",
            ".mov",
            ".mp4",
            ".png",
            ".pyc",
            ".pyo",
            ".tmp",
            ".webp",
        }
        jsonl_allowlist = {
            Path("claude-code/skills/tplan/templates/evidence.jsonl"),
            Path("claude-code/claude-plugin/skills/tplan/templates/evidence.jsonl"),
            Path("codex/skills/mindthus/tplan/templates/evidence.jsonl"),
            Path("codex-plugin/mindthus/skills/tplan/templates/evidence.jsonl"),
            Path("opencode/.opencode/skills/mindthus/tplan/templates/evidence.jsonl"),
        }
        jsonl_paths: set[Path] = set()
        binary_asset_paths: set[Path] = set()

        for path in out.rglob("*"):
            rel = path.relative_to(out)
            self.assertFalse(
                any(part in forbidden_dirs for part in rel.parts),
                f"release pack should not include runtime/test directory: {rel}",
            )
            if path.is_file():
                if path.suffix in forbidden_suffixes:
                    binary_asset_paths.add(rel)
                lowered = rel.as_posix().lower()
                self.assertNotIn("ab_run", lowered)
                self.assertNotIn("pilot", lowered)
                if path.suffix == ".jsonl":
                    jsonl_paths.add(rel)

        self.assertTrue(
            jsonl_paths.issubset(jsonl_allowlist),
            f"release pack should only include allowlisted jsonl templates: {jsonl_paths - jsonl_allowlist}",
        )
        self.assertEqual(binary_asset_paths, set(), "release packs should not carry binary images or media")

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

    def test_plugin_mode_docs_cover_codex_claude_and_opencode_boundaries(self):
        install = (REPO / ".codex" / "INSTALL.md").read_text(encoding="utf-8")
        readme = (REPO / "README.md").read_text(encoding="utf-8")

        self.assertIn("Codex plugin mode", install)
        self.assertIn("skills-pack mode", install)
        self.assertIn("~/.codex/skills/mindthus", install)
        self.assertIn("using-mindthus", install)
        self.assertIn("清楚低风险任务直接执行", install)

        self.assertIn("plugin mode", readme)
        self.assertIn("### 选择下载包", readme)
        self.assertIn("优先安装插件包", readme)
        self.assertIn("插件不可用或需要 portable skills", readme)
        self.assertIn("Codex App / Codex CLI / Claude Code 支持插件", readme)
        self.assertIn("不使用插件、需要 OpenCode、或只想复制 skills 目录", readme)
        self.assertIn("不要在同一个 client profile 里同时安装 plugin mode 和 skills-pack mode", readme)
        self.assertIn("插件包，供 Codex App / Codex CLI / Claude Code plugin mode 使用", readme)
        self.assertIn("Skills 包，供 Codex skills-pack / Claude Code personal skills / OpenCode 使用", readme)
        self.assertIn("Codex Plugin Mode（推荐）", readme)
        self.assertIn("codex plugin marketplace add /tmp/mindthus-plugins/codex-plugin", readme)
        self.assertIn("codex plugin add mindthus@mindthus", readme)
        self.assertIn("Claude Code Plugin Mode（推荐）", readme)
        self.assertIn("claude plugin marketplace add /tmp/mindthus-plugins/claude-code", readme)
        self.assertIn("claude plugin install mindthus@mindthus", readme)
        self.assertIn("可直接提到 `mindthus:tplan`", readme)
        self.assertIn("调用 `/mindthus:using-mindthus`", readme)
        self.assertIn("Codex Skills-Pack Mode", readme)
        self.assertIn("Claude Code Personal Skills Mode", readme)
        self.assertIn("/mindthus:using-mindthus", readme)
        self.assertIn("Claude Code", readme)
        self.assertIn("OpenCode", readme)
        self.assertIn("在该 OpenCode project 中使用", readme)

    def test_readme_claude_personal_skills_mode_copies_runtime_support(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        section = readme.split("### Claude Code Personal Skills Mode", 1)[1].split(
            "### OpenCode", 1
        )[0]

        self.assertIn("/tmp/mindthus-skills/claude-code/skills/_runtime", section)
        self.assertIn("$HOME/.claude/skills/_runtime", section)
        self.assertIn("不是可调用 skill", section)

    def test_claude_personal_skills_copy_layout_keeps_validator_runtime_imports_working(self):
        script = REPO / "scripts" / "build-release-pack.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            out = tmp_dir / "release"
            result = subprocess.run(
                ["python3", str(script), "--package", "skills", "--out", str(out)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            home = tmp_dir / "home"
            skills_home = home / ".claude" / "skills"
            skills_home.mkdir(parents=True)

            packaged_skills = out / "claude-code" / "skills"
            shutil.copytree(packaged_skills / "_runtime", skills_home / "_runtime")
            for skill in packaged_skills.iterdir():
                if not (skill / "SKILL.md").is_file():
                    continue
                shutil.copytree(skill, skills_home / skill.name)

            payload = tmp_dir / "sela-output.json"
            payload.write_text(
                json.dumps(
                    {
                        "schema_version": "sela-fidelity-v0.1",
                        "method": "SELA",
                        "applicability": "transfer",
                        "plain_language_conclusion": "SELA is not dominant here.",
                        "exit_reason": "Another method owns the active hard judgment.",
                        "transfer_to": "WAE",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            validator = skills_home / "sela" / "scripts" / "validate_sela_output.py"
            result = subprocess.run(
                ["python3", str(validator), str(payload)],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("method exit accepted: transfer", result.stdout)

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

    def test_claude_install_script_skips_runtime_support_directory(self):
        script = REPO / "scripts" / "install-skills.sh"
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(home)

            result = subprocess.run(
                ["bash", str(script), "claude", "--repo", str(REPO), "--force"],
                text=True,
                capture_output=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((home / ".claude" / "skills" / "_runtime").exists())
            self.assertTrue((home / ".claude" / "skills" / "tplan").is_symlink(), result.stdout)
            self.assertTrue((home / ".claude" / "skills" / "sela").is_symlink(), result.stdout)
            self.assertIn("repo-local _runtime", result.stdout)
            self.assertIn("copy _runtime separately", result.stdout)

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
            self.assert_release_pack_excludes_runtime_artifacts(out)

            marketplace_path = out / "claude-code" / ".claude-plugin" / "marketplace.json"
            plugin_path = out / "claude-code" / "claude-plugin" / ".claude-plugin" / "plugin.json"
            self.assertTrue(marketplace_path.exists())
            self.assertTrue(plugin_path.exists())

            marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
            plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
            source = marketplace["plugins"][0]["source"]
            self.assertEqual(source, "./claude-plugin")
            self.assertNotIn("..", source)
            self.assertEqual(plugin["version"], "1.4.3")
            self.assertTrue((out / "claude-code" / "claude-plugin" / "skills" / "tplan" / "SKILL.md").exists())
            self.assertTrue((out / "claude-code" / "claude-plugin" / "skills" / "mpg" / "SKILL.md").exists())
            claude_hook_config_path = out / "claude-code" / "claude-plugin" / "hooks" / "hooks.json"
            claude_hook_script_path = out / "claude-code" / "claude-plugin" / "hooks" / "session-start"
            self.assertTrue(claude_hook_config_path.exists())
            self.assertTrue(claude_hook_script_path.exists())
            claude_hook_config = json.loads(claude_hook_config_path.read_text(encoding="utf-8"))
            session_start_hooks = claude_hook_config["hooks"]["SessionStart"]
            self.assertEqual(session_start_hooks[0]["matcher"], "startup|clear|compact")
            self.assertEqual(
                session_start_hooks[0]["hooks"][0]["command"],
                '"${CLAUDE_PLUGIN_ROOT}/hooks/session-start"',
            )
            self.assertFalse(session_start_hooks[0]["hooks"][0]["async"])
            claude_hook_script = claude_hook_script_path.read_text(encoding="utf-8")
            self.assertIn("MINDTHUS_ROUTER_CONTEXT", claude_hook_script)
            self.assertIn("mindthus:using-mindthus", claude_hook_script)
            self.assertIn("upstream brainstorming/design workflow", claude_hook_script)
            self.assertIn("Superpowers Brainstorm", claude_hook_script)
            self.assertIn("hard judgment point", claude_hook_script)
            self.assertIn("directly", claude_hook_script)
            self.assertNotIn("v3", claude_hook_script.lower())
            for path in sorted((out / "claude-code" / "claude-plugin" / "skills").glob("*/SKILL.md")):
                self.assert_skill_frontmatter_is_parseable(path)
            self.assertTrue((out / "claude-code" / "skills" / "tplan" / "SKILL.md").exists())
            self.assertTrue((out / "claude-code" / "skills" / "mpg" / "SKILL.md").exists())
            self.assertTrue((out / "claude-code" / "docs" / "methodologies" / "shared-primitives.md").exists())
            self.assertTrue(
                (out / "claude-code" / "claude-plugin" / "scripts" / "run-fidelity-judge.py").exists()
            )
            self.assertTrue(
                (out / "claude-code" / "claude-plugin" / "scripts" / "log-fidelity-usage.py").exists()
            )
            self.assertTrue(
                (out / "claude-code" / "claude-plugin" / "scripts" / "log-mindthus-runtime.py").exists()
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

            codex_plugin_root = out / "codex-plugin" / "mindthus"
            codex_marketplace_path = out / "codex-plugin" / ".agents" / "plugins" / "marketplace.json"
            codex_plugin_manifest_path = codex_plugin_root / ".codex-plugin" / "plugin.json"
            self.assertTrue(codex_marketplace_path.exists())
            self.assertTrue(codex_plugin_manifest_path.exists())
            codex_marketplace = json.loads(codex_marketplace_path.read_text(encoding="utf-8"))
            codex_plugin_manifest = json.loads(codex_plugin_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(codex_marketplace["name"], "mindthus")
            self.assertEqual(codex_marketplace["plugins"][0]["name"], "mindthus")
            self.assertEqual(
                codex_marketplace["plugins"][0]["source"],
                {"source": "local", "path": "./mindthus"},
            )
            self.assertEqual(codex_marketplace["plugins"][0]["policy"]["installation"], "AVAILABLE")
            self.assertEqual(codex_plugin_manifest["name"], "mindthus")
            self.assertEqual(codex_plugin_manifest["version"], "1.4.3")
            self.assertEqual(codex_plugin_manifest["skills"], "./skills/")
            self.assertEqual(codex_plugin_manifest["license"], "AGPL-3.0-only")
            self.assertIn("Judgment framework", codex_plugin_manifest["description"])
            self.assertIn("SPDX AGPL-3.0-only", codex_plugin_manifest["interface"]["longDescription"])
            self.assertIn(
                "commercial licensing is documented",
                codex_plugin_manifest["interface"]["longDescription"],
            )
            self.assertEqual(
                codex_plugin_manifest["interface"]["defaultPrompt"],
                [
                    "Mindthus: hard judgment point -> mindthus:using-mindthus; simple direct; "
                    "evidence first; defer to Superpowers Brainstorm."
                ],
            )
            codex_default_prompt = codex_plugin_manifest["interface"]["defaultPrompt"][0]
            self.assertIn("Superpowers Brainstorm", codex_default_prompt)
            self.assertIn("hard judgment point", codex_default_prompt)
            self.assertLessEqual(len(codex_default_prompt), 128)
            self.assertLessEqual(len(codex_default_prompt.encode("utf-8")), 128)
            self.assertNotIn("v3", codex_default_prompt.lower())
            self.assertTrue((codex_plugin_root / "skills" / "tplan" / "SKILL.md").exists())
            self.assertTrue((codex_plugin_root / "skills" / "mpg" / "SKILL.md").exists())
            self.assertTrue(
                (
                    codex_plugin_root
                    / "skills"
                    / "using-mindthus"
                    / "resources"
                    / "calibration-pairs.yaml"
                ).exists()
            )
            self.assertFalse((codex_plugin_root / "skills" / "_runtime").exists())
            self.assertTrue((codex_plugin_root / "_runtime" / "fidelity" / "core.py").exists())
            for path in sorted((codex_plugin_root / "skills").glob("*/SKILL.md")):
                self.assert_skill_frontmatter_is_parseable(path)
            self.assertTrue((codex_plugin_root / "docs" / "methodologies" / "shared-primitives.md").exists())
            self.assertTrue((codex_plugin_root / "scripts" / "run-fidelity-judge.py").exists())
            self.assertTrue((codex_plugin_root / "scripts" / "log-mindthus-runtime.py").exists())
            self.assertTrue(
                (codex_plugin_root / "scripts" / "primitives" / "whole_elephant_validator.py").exists()
            )
            self.assertFalse((codex_plugin_root / "docs" / "internal").exists())
            self.assertFalse((codex_plugin_root / "docs" / "superpowers").exists())

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
            self.assertFalse((out / "opencode-plugin").exists())

            skill_names = ("3l5s", "sela", "mpg", "edsp", "wae", "tvg", "tplan", "using-mindthus")
            for platform_dir in (out / "codex", out / "opencode"):
                markdown = "\n".join(
                    path.read_text(encoding="utf-8") for path in sorted(platform_dir.rglob("*.md"))
                )
                for skill_name in skill_names:
                    self.assertNotIn(f"skills/{skill_name}/", markdown)

    def test_release_pack_includes_split_primitive_docs(self):
        script = REPO / "scripts" / "build-release-pack.py"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "release"
            result = subprocess.run(
                ["python3", str(script), "--out", str(out)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            primitive_doc = Path("docs") / "methodologies" / "primitives" / "whole-elephant-protocol.md"
            expected_roots = (
                out / "claude-code",
                out / "claude-code" / "claude-plugin",
                out / "codex",
                out / "codex-plugin" / "mindthus",
                out / "opencode",
            )
            for root in expected_roots:
                self.assertTrue((root / primitive_doc).exists(), f"{root} missing {primitive_doc}")

    def test_release_pack_builder_can_split_plugin_and_skills_packages(self):
        script = REPO / "scripts" / "build-release-pack.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            plugins = tmp_dir / "mindthus-plugins-1.4.3"
            skills = tmp_dir / "mindthus-skills-1.4.3"

            plugin_result = subprocess.run(
                ["python3", str(script), "--package", "plugins", "--out", str(plugins)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(plugin_result.returncode, 0, plugin_result.stderr)
            self.assert_release_pack_excludes_runtime_artifacts(plugins)
            self.assertTrue((plugins / "codex-plugin" / "mindthus" / ".codex-plugin" / "plugin.json").exists())
            self.assertTrue((plugins / "claude-code" / ".claude-plugin" / "marketplace.json").exists())
            self.assertFalse((plugins / "codex").exists())
            self.assertFalse((plugins / "opencode").exists())
            self.assertFalse((plugins / "claude-code" / "skills").exists())

            skills_result = subprocess.run(
                ["python3", str(script), "--package", "skills", "--out", str(skills)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(skills_result.returncode, 0, skills_result.stderr)
            self.assert_release_pack_excludes_runtime_artifacts(skills)
            self.assertTrue((skills / "codex" / "skills" / "mindthus" / "tplan" / "SKILL.md").exists())
            self.assertTrue((skills / "claude-code" / "skills" / "tplan" / "SKILL.md").exists())
            self.assertTrue(
                (skills / "opencode" / ".opencode" / "skills" / "mindthus" / "tplan" / "SKILL.md").exists()
            )
            self.assertTrue(
                (
                    skills
                    / "codex"
                    / "skills"
                    / "mindthus"
                    / "using-mindthus"
                    / "resources"
                    / "calibration-pairs.yaml"
                ).exists()
            )
            self.assertTrue(
                (
                    skills
                    / "claude-code"
                    / "skills"
                    / "using-mindthus"
                    / "resources"
                    / "calibration-pairs.yaml"
                ).exists()
            )
            self.assertTrue(
                (
                    skills
                    / "opencode"
                    / ".opencode"
                    / "skills"
                    / "mindthus"
                    / "using-mindthus"
                    / "resources"
                    / "calibration-pairs.yaml"
                ).exists()
            )
            codex_using_validator = (
                skills
                / "codex"
                / "skills"
                / "mindthus"
                / "using-mindthus"
                / "scripts"
                / "validate_using_mindthus_output.py"
            )
            shadow = tmp_dir / "scripts" / "primitives"
            shadow.mkdir(parents=True)
            (shadow / "__init__.py").write_text("", encoding="utf-8")
            (shadow.parent / "__init__.py").write_text("", encoding="utf-8")
            (shadow / "whole_elephant_validator.py").write_text(
                "raise RuntimeError('shadowed ancestor validator')\n",
                encoding="utf-8",
            )
            near_shadow = skills / "codex" / "skills" / "mindthus" / "scripts" / "primitives"
            near_shadow.mkdir(parents=True)
            (near_shadow / "__init__.py").write_text("", encoding="utf-8")
            (near_shadow.parent / "__init__.py").write_text("", encoding="utf-8")
            (near_shadow / "whole_elephant_validator.py").write_text(
                "raise RuntimeError('near ancestor shadow')\n",
                encoding="utf-8",
            )
            validator_help = subprocess.run(
                ["python3", str(codex_using_validator), "--help"],
                cwd=tmp_dir,
                env={**os.environ, "PYTHONPATH": str(tmp_dir)},
                text=True,
                capture_output=True,
            )
            self.assertEqual(validator_help.returncode, 0, validator_help.stderr)
            self.assertIn("Validate using-mindthus fidelity output shape", validator_help.stdout)
            self.assertFalse((skills / "codex-plugin").exists())
            self.assertFalse((skills / "claude-code" / ".claude-plugin").exists())
            self.assertFalse((skills / "claude-code" / "claude-plugin").exists())


if __name__ == "__main__":
    unittest.main()
