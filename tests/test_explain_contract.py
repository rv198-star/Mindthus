"""Explain integration contracts; local source and real release-pack checks only."""
import json
import hashlib
import runpy
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EXPLAIN_FILES = (
    "SKILL.md",
    "resources/presentation-contract.md",
    "resources/html-v1.md",
    "resources/tplan-progress.md",
    "resources/expression-modes.md",
    "scripts/prepare_html_delivery.py",
)


class ExplainRoutingContractTests(unittest.TestCase):
    def test_raw_routing_table_has_only_the_eight_judgment_owners(self):
        text = (REPO / "skills/using-mindthus/SKILL.md").read_text(encoding="utf-8")
        section = text.split("### Skill Routing", 1)[1].split("\n### ", 1)[0]
        rows = [
            [cell.strip().strip("`").lower() for cell in line.strip().strip("|").split("|")]
            for line in section.splitlines()
            if line.strip().startswith("|")
        ]
        self.assertGreaterEqual(len(rows), 2, "missing routing table")
        owners = []
        for cells in rows[2:]:
            self.assertEqual(len(cells), 2, "unexpected routing table shape")
            owners.append(cells[1])
        # Inspect every raw row: the older router helper filters unknown names out.
        self.assertEqual(len(owners), 8, owners)
        self.assertEqual(
            set(owners),
            {"3l5s", "sra", "sela", "mpg", "edsp", "wae", "tvg", "tplan"},
        )

    def test_explain_is_not_a_judgment_trace_owner_or_method(self):
        schemas = REPO / "skills/_runtime/judgment/resources"
        for name in ("judgment-trace.schema.json", "judgment-trace-v1.1.schema.json"):
            with self.subTest(schema=name):
                schema = json.loads((schemas / name).read_text(encoding="utf-8"))
                routing = schema["properties"]["routing"]["properties"]
                self.assertNotIn("explain", routing["judgment_owner"]["enum"])
                self.assertNotIn("explain", routing["selected_method"]["enum"])
                self.assertNotIn("explain", routing["loaded_methods"]["items"]["enum"])


class ExplainDefaultDeliveryTests(unittest.TestCase):
    """Instruction and wiring checks, not proof of every model's runtime behavior."""
    METHOD_SKILLS = ("3l5s", "sela", "mpg", "sra", "edsp", "wae", "tvg", "tplan")

    def normalized(self, relative):
        return " ".join((REPO / relative).read_text(encoding="utf-8").split())

    def test_default_is_actual_skill_use_not_only_a_shared_baseline(self):
        skill = self.normalized("skills/explain/SKILL.md")
        contract = self.normalized("skills/explain/resources/presentation-contract.md")
        agents = self.normalized("AGENTS.md")
        router = self.normalized("skills/using-mindthus/SKILL.md")
        self.assertIn("Use by default when Mindthus delivers human-facing", skill)
        self.assertIn("Use this Skill by default for Mindthus human-facing results", skill)
        self.assertIn("Default to clarity; choose transformation intensity inside Explain", skill)
        self.assertIn("default human-facing delivery Skill for Mindthus", contract)
        self.assertIn("It is not a baseline-only alternative", contract)
        self.assertIn("No explicit Explain request is needed", contract)
        self.assertIn("默认由当前 Agent 使用 [Explain](skills/explain/SKILL.md)", agents)
        self.assertIn("当前 Agent 默认使用 [Explain](../explain/SKILL.md)", router)
        for text in (skill, contract, agents, router):
            self.assertNotIn("Full transformation stays on-demand", text)
            self.assertNotIn("完整 Explain transformation 才是按需能力", text)
            self.assertNotIn("The baseline is satisfied when the method can express", text)

    def test_loaded_entry_is_reused_without_extra_model_or_rewrite_pipeline(self):
        skill = self.normalized("skills/explain/SKILL.md")
        contract = self.normalized("skills/explain/resources/presentation-contract.md")
        self.assertIn("If this SKILL.md is absent from effective context, read it before delivery", skill)
        self.assertIn("otherwise reuse it", skill)
        self.assertIn("Load resources only when relevant", skill)
        self.assertIn("Already-clear output may remain unchanged", skill)
        self.assertIn("No separate Agent/model call or mandatory first-draft/rewrite pass", skill)
        self.assertIn("do not reload the full package on every turn", contract)
        self.assertIn("Do not add a call receipt or delivery state machine", contract)

    def test_scope_preserves_machine_formats_internal_records_and_short_notices(self):
        contract = self.normalized("skills/explain/resources/presentation-contract.md")
        for phrase in (
            "JSON, code, commands, verbatim quotations, fixed-format files",
            "Preserve the exact upstream format",
            "Tool returns, internal state, logs, evidence records, machine-to-machine handoffs",
            "no human-facing conversion",
            "Routine acknowledgements, short status notices, heartbeats",
            "do not expand them into a report",
            "Explicit user format or explanation requirements take precedence",
            "keep the machine artifact unchanged",
            "Preserve required artifact links and method-specific evidence/delivery obligations",
        ):
            self.assertIn(phrase, contract)

    def test_modes_are_not_entry_requirements_and_fail_open_is_recovery(self):
        contract = self.normalized("skills/explain/resources/presentation-contract.md")
        for flag in ("--brief", "--eli5", "--audience", "--html"):
            self.assertIn(flag, contract)
        self.assertIn("they are not prerequisites for using Explain", contract)
        self.assertIn("No particular plugin or presentation host is required", contract)
        self.assertIn("is recovery, not the normal baseline-only shortcut", contract)
        self.assertIn("A specifically required artifact remains incomplete until delivered", contract)

    def test_direct_method_entries_resolve_the_official_skill(self):
        canonical = (REPO / "skills/explain/SKILL.md").resolve()
        for name in (*self.METHOD_SKILLS, "using-mindthus"):
            entry = REPO / f"skills/{name}/SKILL.md"
            with self.subTest(skill=name):
                text = entry.read_text(encoding="utf-8")
                links = re.findall(r"\[Explain\]\(([^)]+)\)", text)
                self.assertEqual(len(links), 1, "default delivery must reach the official Skill entry")
                self.assertEqual((entry.parent / links[0]).resolve(), canonical)
                if name != "using-mindthus":
                    self.assertIn("by default", text)
                    self.assertIn("human-facing results", text)
                    self.assertIn("clarity", text)
                self.assertNotIn("[Explain Core Presentation Contract]", text)
        contract = REPO / "skills/explain/resources/presentation-contract.md"
        self.assertIn("[Explain](../SKILL.md)", contract.read_text())

    def test_shared_presentation_does_not_add_explain_to_judgment_routing(self):
        text = (REPO / "skills/using-mindthus/SKILL.md").read_text(encoding="utf-8")
        section = text.split("### Skill Routing", 1)[1].split("\n### ", 1)[0]
        self.assertNotIn("| explain |", section.lower())
        self.assertIn("`explain` 不进入上表的判断 owner 路由", text)


class ExplainHostThemeContractTests(unittest.TestCase):
    """Static instructions and real preparatory markup, not host presentation proof."""

    def test_visualizations_is_mandatory_when_chatgpt_exposes_it(self):
        skill = (REPO / 'skills/explain/SKILL.md').read_text(encoding='utf-8')
        agents = (REPO / 'AGENTS.md').read_text(encoding='utf-8')
        html = (REPO / 'skills/explain/resources/html-v1.md').read_text(encoding='utf-8')
        for phrase in ('Host selection is mandatory', 'Visualizations / app_block',
                       'Codex CLI', 'Other hosts:', 'Only the live host UI'):
            self.assertIn(phrase, skill)
        self.assertIn('required primary HTML adapter whenever exposed', html)
        self.assertIn('Visualizations 则必须在当前对话内直接用', agents)
        self.assertNotIn('prefer **Visualizations / app_block**', skill)

    def test_theme_defaults_to_auto_and_host_override_is_explicit(self):
        from skills.explain.scripts.explain_compiler import compile_source
        sample = (REPO / 'tests/fixtures/explain-v2/showcase.md').read_text(encoding='utf-8')
        output = compile_source(sample, engine='python')['html']
        self.assertIn('data-mode="auto" data-host-theme="auto"', output)
        self.assertIn('prefers-color-scheme: dark', output)
        self.assertIn('[data-host-theme=dark]', output)
        self.assertIn('[data-host-theme=light]', output)
        self.assertIn('data-ex-action="dark"', output)
        self.assertNotIn('data-mode="light"', output)
        inline_css = (REPO / 'docs/internal/explain-v2/prototypes/analysis-layout-r1/inline.css').read_text(encoding='utf-8')
        inline_src = (REPO / 'docs/internal/explain-v2/prototypes/analysis-layout-r1/render_inline.py').read_text(encoding='utf-8')
        self.assertIn('prefers-color-scheme:dark', inline_css)
        self.assertIn('[data-host-theme=dark]', inline_css)
        self.assertIn('data-ex-theme="auto" data-host-theme="auto"', inline_src)


class ExplainSameSourceExampleTests(unittest.TestCase):
    """Fixed synthetic examples check retention, not model-generation quality."""
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((REPO / "tests/fixtures/explain-default-delivery.json").read_text())

    def test_examples_declare_their_limits_and_cover_the_approved_scope(self):
        self.assertEqual(self.fixture["provenance"], "synthetic_development_examples")
        self.assertEqual(self.fixture["comparison_kind"], "constructed_same_source_pairs")
        self.assertIn("not independently sampled", self.fixture["assessment"])
        self.assertEqual({c["id"] for c in self.fixture["cases"]}, {
            "short-clear", "qualified-judgment", "tplan-progress", "exact-json", "exact-command", "short-ack",
        })

    def test_examples_preserve_stated_qualifications_and_exact_payloads(self):
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["source"])
                self.assertTrue(case["review"])
                output = case["explain_output"]
                for phrase in case["required"]:
                    self.assertIn(phrase, output)
                for phrase in case["forbidden"]:
                    self.assertNotIn(phrase, output)
                if case["exact"]:
                    self.assertEqual(output.encode("utf-8"), case["baseline_output"].encode("utf-8"))
                if case["id"] == "exact-json":
                    self.assertEqual(json.loads(output), {"status": "blocked", "count": 0})


class ExplainDeliveryContractTests(unittest.TestCase):
    def test_explicit_inline_html_requires_actual_html_and_observed_acceptance(self):
        skill = " ".join((REPO / "skills/explain/SKILL.md").read_text().split())
        contract = " ".join((REPO / "skills/explain/resources/html-v1.md").read_text().split())
        tplan = " ".join((REPO / "skills/tplan/resources/user-output.md").read_text().split())
        self.assertIn("`--html` selects an **HTML representation**, not a persistence target", skill)
        self.assertIn("Visualizations / app_block", skill)
        self.assertIn("variant=inline", skill)
        self.assertIn("language=html", skill)
        self.assertIn("raw HTML fragment", skill)
        self.assertIn("A previewable `html` code block is **not** an automatic fallback", skill)
        self.assertIn("Do not create or attach a downloadable file merely because `--html` was requested", skill)
        self.assertIn("Visualizations / app_block is the required primary HTML adapter", contract)
        self.assertIn("Code/Preview belongs to the code-block surface, not to Visualizations", contract)
        self.assertIn("explain.inline_html.v1", contract)
        self.assertIn("not the ChatGPT Visualizations trigger", contract)
        self.assertIn("An image is not a substitute for requested interaction", skill)
        self.assertIn("host or user", skill)
        self.assertIn("Do **not** persist a file solely because `--html` was requested", contract)
        self.assertIn("Use an `html` code block only when the user asks", contract)
        self.assertIn("prepared content, not a rendering receipt", contract)
        self.assertIn("no mandatory dependency on any external plugin, app, canvas, or provider", contract)
        self.assertIn("does not need to create an HTML download", tplan)
        self.assertIn("keep that delivery requirement open", tplan)

    def prepare(self, path):
        helper = runpy.run_path(str(REPO / "skills/explain/scripts/prepare_html_delivery.py"))
        return helper["prepare_html_delivery"](path)

    def test_preview_uses_exact_download_source_without_mutation(self):
        raw = '<!doctype html>\r\n<html lang="zh-CN"><details><summary>依据</summary>真实来源</details></html>'.encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.html"
            path.write_bytes(raw)
            result = self.prepare(path)
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(result["html"].encode(), raw)
            self.assertEqual(result["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(result["preview_block"], "```html\n" + raw.decode() + "\n```\n")
            self.assertEqual(result["status"], "prepared_not_verified")
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["progress.html"])

    def test_markdown_examples_cannot_escape_the_html_block(self):
        source = '<html><pre>````html\nexample\n````</pre></html>\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text(source)
            result = self.prepare(path)
            self.assertEqual(result["preview_block"], "`````html\n" + source + "`````\n")

    def test_invalid_file_is_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, raw in (("report.png", b"image"), ("blank.html", b""),
                              ("bad.html", b"\xff"), ("nul.html", b"<html>\x00</html>")):
                with self.subTest(name=name):
                    path = Path(directory) / name
                    path.write_bytes(raw)
                    with self.assertRaises((ValueError, UnicodeError)):
                        self.prepare(path)
                    self.assertEqual(path.read_bytes(), raw)

    def test_cli_submits_html_not_a_file_link_or_success_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.html"
            path.write_text('<html><details><summary>查看</summary>内容</details></html>')
            helper = REPO / "skills/explain/scripts/prepare_html_delivery.py"
            result = subprocess.run([sys.executable, str(helper), str(path)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, self.prepare(path)["preview_block"])
            result = subprocess.run([sys.executable, str(helper), str(path), "--format", "json"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "prepared_not_verified")


class ExplainPackagingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.staging = tempfile.TemporaryDirectory(prefix="mindthus-explain-pack-")
        cls.addClassCleanup(cls.staging.cleanup)
        cls.output = Path(cls.staging.name) / "release"
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/build-release-pack.py"),
                "--package", "all",
                "--out", str(cls.output),
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=60,
        )
        if result.returncode:
            raise AssertionError(result.stderr + result.stdout)

    def test_explain_entry_and_resources_survive_all_five_layouts(self):
        layouts = (
            ("claude-code/claude-plugin", "skills"),
            ("claude-code", "skills"),
            ("codex-plugin/mindthus", "skills"),
            ("codex", "skills/mindthus"),
            ("opencode", ".opencode/skills/mindthus"),
        )
        source_root = REPO / "skills/explain"
        for platform, skill_prefix in layouts:
            platform_root = self.output / platform
            skill_root = platform_root / skill_prefix / "explain"
            for relative in EXPLAIN_FILES:
                with self.subTest(platform=platform, resource=relative):
                    source = source_root / relative
                    packaged = skill_root / relative
                    self.assertTrue(source.is_file(), f"missing Explain source: {relative}")
                    self.assertTrue(packaged.is_file(), f"missing packaged Explain: {packaged}")
                    text = packaged.read_text(encoding="utf-8")
                    canonical = text.replace(f"{skill_prefix}/", "skills/") if skill_prefix != "skills" else text
                    self.assertEqual(canonical, source.read_text(encoding="utf-8"))
                    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                        if target.startswith(("#", "https://", "http://", "mailto:")):
                            continue
                        target = target.split("#", 1)[0]
                        if target:
                            resolved = (packaged.parent / target).resolve()
                            self.assertTrue(
                                resolved.is_relative_to(self.output.resolve()),
                                f"packaged link escapes release: {packaged} -> {target}",
                            )
                            self.assertTrue(resolved.exists(), f"broken packaged link: {packaged} -> {target}")

    def test_default_skill_links_survive_all_five_layouts(self):
        layouts = (
            ("claude-code/claude-plugin", "skills"),
            ("claude-code", "skills"),
            ("codex-plugin/mindthus", "skills"),
            ("codex", "skills/mindthus"),
            ("opencode", ".opencode/skills/mindthus"),
        )
        source = (REPO / "skills/explain/SKILL.md").read_text(encoding="utf-8")
        methods = (*ExplainDefaultDeliveryTests.METHOD_SKILLS, "using-mindthus")
        for platform, prefix in layouts:
            root = self.output / platform / prefix
            expected = (root / "explain/SKILL.md").resolve()
            for name in methods:
                entry = root / name / "SKILL.md"
                with self.subTest(platform=platform, skill=name):
                    links = re.findall(r"\[Explain\]\(([^)]+)\)", entry.read_text(encoding="utf-8"))
                    self.assertEqual(len(links), 1)
                    resolved = (entry.parent / links[0]).resolve()
                    self.assertEqual(resolved, expected)
                    self.assertTrue(resolved.is_relative_to(self.output.resolve()))
                    self.assertTrue(resolved.is_file())
                    self.assertEqual(resolved.read_text(encoding="utf-8"), source)

    def test_namespaced_agents_reference_the_packaged_explain_skill(self):
        for platform, prefix in (
            ("codex", "skills/mindthus"),
            ("opencode", ".opencode/skills/mindthus"),
        ):
            with self.subTest(platform=platform):
                agents = (self.output / platform / "AGENTS.md").read_text(encoding="utf-8")
                self.assertIn(f"`{prefix}/explain/`", agents)
                self.assertNotIn("`skills/explain/`", agents)
                self.assertTrue((self.output / platform / prefix / "explain/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
