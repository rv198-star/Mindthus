"""Explain integration contracts; local source and real release-pack checks only."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EXPLAIN_FILES = (
    "SKILL.md",
    "resources/html-v1.md",
    "resources/tplan-progress.md",
    "resources/expression-modes.md",
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


class ExplainDeliveryContractTests(unittest.TestCase):
    def test_html_requires_inline_when_supported_and_downloadable_file_always(self):
        skill = (REPO / "skills/explain/SKILL.md").read_text(encoding="utf-8")
        html_contract = (REPO / "skills/explain/resources/html-v1.md").read_text(encoding="utf-8")
        tplan_output = (REPO / "skills/tplan/resources/user-output.md").read_text(encoding="utf-8")

        self.assertIn("show that artifact directly in the conversation", skill)
        self.assertIn("same self-contained `.html` file for download", skill)
        self.assertIn("Inline conversation view when the host supports native HTML/artifact preview", html_contract)
        self.assertIn("Downloadable file always", html_contract)
        self.assertIn("does not count as inline HTML", html_contract)
        self.assertIn("HTML preview is unavailable in that host", html_contract)
        self.assertIn("should display that same", tplan_output)
        self.assertIn("artifact inline in the conversation", tplan_output)
        self.assertIn("also expose the file for independent download", tplan_output)


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
