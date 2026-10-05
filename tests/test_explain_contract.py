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


class ExplainDeliveryContractTests(unittest.TestCase):
    def test_explicit_inline_html_requires_actual_html_and_observed_acceptance(self):
        skill = " ".join((REPO / "skills/explain/SKILL.md").read_text().split())
        contract = " ".join((REPO / "skills/explain/resources/html-v1.md").read_text().split())
        tplan = " ".join((REPO / "skills/tplan/resources/user-output.md").read_text().split())
        self.assertIn("An image is not a substitute for requested inline HTML", skill)
        self.assertIn("host or user confirms", skill)
        self.assertIn("actual source as an `html` code block", contract)
        self.assertIn("prepared content, not a rendering receipt", contract)
        self.assertIn("same HTML file for independent download", tplan)
        self.assertIn("delivery requirement open", tplan)

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
