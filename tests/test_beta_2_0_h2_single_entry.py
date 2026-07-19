import json
import os
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PROFILE_ROOT = REPO / "beta" / "2.0-routing-convergence" / "h2-single-entry-topology"
H21_ROOT = REPO / "beta" / "2.0-routing-convergence" / "h2.1-companion-gate"
BUILD_SCRIPT = REPO / "scripts" / "build-release-pack.py"
OWNERS = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")


class H2SingleEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._temp.name) / "release"
        result = subprocess.run(
            [
                "python3",
                str(BUILD_SCRIPT),
                "--release-line",
                "2.0-routing-h2-single-entry",
                "--package",
                "plugins",
                "--out",
                str(cls.out),
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode:
            raise AssertionError(result.stderr + result.stdout)
        cls.plugin = cls.out / "codex-plugin" / "mindthus-beta"
        cls.profile = json.loads((PROFILE_ROOT / "release-profile.json").read_text())

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp.cleanup()

    def test_profile_is_distinct_unpublished_codex_only_candidate(self) -> None:
        self.assertEqual(self.profile["release_line"], "2.0-routing-h2-single-entry")
        self.assertEqual(self.profile["version"], "2.0.0-next.4")
        self.assertEqual(self.profile["candidate_revision"], "h2.1-companion-gate")
        self.assertEqual(self.profile["supported_surfaces"], ["codex-plugin"])
        self.assertEqual(self.profile["release_preparation"], "forbidden")
        self.assertIsNone(self.profile["default_prompt"])
        self.assertNotIn("beta.3", json.dumps(self.profile).lower())

    def test_only_mpg_companion_gate_is_subtractively_replaced(self) -> None:
        correction = self.profile["package_time_owner_correction"]
        self.assertEqual(correction["id"], "mpg-sela-companion-conjunction")
        self.assertEqual(correction["mode"], "exact-subtractive-replace")
        self.assertEqual(correction["owner"], "mpg")
        self.assertEqual(
            {item["path"] for item in correction["targets"]},
            {"SKILL.md", "resources/methodology.md"},
        )
        owner_root = self.plugin / "skills" / "using-mindthus" / "references" / "owners"
        after_count = 0
        total_delta = 0
        for item in correction["targets"]:
            target = owner_root / "mpg" / (
                "OWNER.md" if item["path"] == "SKILL.md" else item["path"]
            )
            text = target.read_text()
            sela_path = Path(os.path.relpath(owner_root / "sela" / "OWNER.md", target.parent)).as_posix()
            after = correction["after"].replace("mindthus:sela", sela_path)
            before = item["before"].replace("mindthus:sela", sela_path)
            self.assertEqual(text.count(after), 1)
            self.assertNotIn(before, text)
            after_count += text.count(after)
            total_delta += len(correction["after"].encode()) - len(item["before"].encode())
        self.assertEqual(after_count, 2)
        self.assertEqual(total_delta, -102)

    def test_exactly_one_skill_and_seven_resource_owners(self) -> None:
        skills = sorted(path.relative_to(self.plugin).as_posix() for path in (self.plugin / "skills").rglob("SKILL.md"))
        self.assertEqual(skills, ["skills/using-mindthus/SKILL.md"])
        owner_root = self.plugin / "skills" / "using-mindthus" / "references" / "owners"
        self.assertEqual(
            sorted(path.parent.name for path in owner_root.glob("*/OWNER.md")),
            sorted(OWNERS),
        )
        self.assertFalse(list(owner_root.rglob("SKILL.md")))
        self.assertFalse(list((self.plugin / "reference").rglob("SKILL.md")))
        self.assertFalse((self.plugin / "reference" / "1.4.6" / "docs" / "methodologies").exists())

    def test_owner_companion_paths_resolve_at_every_declaring_depth(self) -> None:
        owner_root = self.plugin / "skills" / "using-mindthus" / "references" / "owners"
        declarations = []
        for markdown in owner_root.rglob("*.md"):
            text = markdown.read_text()
            declaring_owner = markdown.relative_to(owner_root).parts[0]
            for companion in ("sela", "mpg"):
                if companion == declaring_owner:
                    continue
                target = owner_root / companion / "OWNER.md"
                relative = os.path.relpath(target, markdown.parent)
                if relative in text:
                    declarations.append((markdown, relative))
                    self.assertTrue((markdown.parent / relative).resolve().is_file())
        self.assertEqual(
            {
                (markdown.relative_to(owner_root).as_posix(), relative)
                for markdown, relative in declarations
            },
            {
                ("mpg/OWNER.md", "../sela/OWNER.md"),
                ("mpg/resources/methodology.md", "../../sela/OWNER.md"),
                ("sela/OWNER.md", "../mpg/OWNER.md"),
                ("sela/resources/methodology.md", "../../mpg/OWNER.md"),
            },
        )

    def test_manifest_and_carriers_are_native_and_thin(self) -> None:
        manifest = json.loads((self.plugin / ".codex-plugin" / "plugin.json").read_text())
        self.assertNotIn("hooks", manifest)
        self.assertNotIn("defaultPrompt", manifest.get("interface", {}))
        for relative in self.profile["forbidden_active_paths"]:
            self.assertFalse((self.plugin / relative).exists(), relative)
        entry = self.plugin / "skills" / "using-mindthus" / "SKILL.md"
        index = entry.parent / "references" / "owner-index.md"
        budgets = self.profile["budgets"]
        self.assertLessEqual(len(entry.read_bytes()), budgets["using_mindthus_max_bytes"])
        self.assertLessEqual(len(entry.read_text().split()), budgets["using_mindthus_max_words"])
        self.assertLessEqual(len(index.read_bytes()), budgets["owner_index_max_bytes"])
        self.assertLessEqual(len(index.read_text().split()), budgets["owner_index_max_words"])

    def test_live_fixtures_are_frozen_before_candidate_execution(self) -> None:
        qualification = PROFILE_ROOT / "qualification" / "h2-20260719"
        lock = json.loads((qualification / "fixture-lock.json").read_text())
        for relative, expected in lock["files"].items():
            actual = hashlib.sha256((qualification / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)
        cases = (qualification / "FROZEN-CASES.md").read_text()
        self.assertEqual(sum(f"## Q{number} " in cases for number in range(1, 8)), 7)
        runbook = (qualification / "RUNBOOK.md").read_text()
        self.assertIn("codex exec resume <q1-thread-uuid>", runbook)
        self.assertIn("/usr/bin/perl -e 'alarm shift; exec @ARGV' 900", runbook)
        self.assertIn("200000 * remaining_H2_calls", runbook)

        anti_spiral = qualification / "fixtures" / "anti-spiral"
        with tempfile.TemporaryDirectory() as directory:
            current = Path(directory) / "incident-plan.md"
            shutil.copyfile(anti_spiral / "history" / "plan-v0.md", current)
            for patch_name, expected in (
                ("edit-01.patch", anti_spiral / "history" / "plan-v1.md"),
                ("edit-02.patch", anti_spiral / "incident-plan.md"),
            ):
                replay = subprocess.run(
                    ["patch", "-p1", "-i", str(anti_spiral / patch_name)],
                    cwd=directory,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)
                self.assertEqual(current.read_bytes(), expected.read_bytes())

    def test_h21_causal_and_comparison_protocols_are_frozen(self) -> None:
        lock = json.loads(
            (H21_ROOT / "qualification" / "h2.1-20260719" / "fixture-lock.json").read_text()
        )
        for relative, expected in lock["files"].items():
            actual = hashlib.sha256((H21_ROOT / relative).resolve().read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)
        cases = (
            H21_ROOT / "qualification" / "h2.1-20260719" / "FROZEN-CASES.md"
        ).read_text()
        self.assertEqual(cases.count("## C1 / Q"), 2)
        self.assertEqual(sum(f"## Q{number} " in cases for number in range(3, 8)), 5)
        self.assertEqual(cases.count("## C2 "), 1)
        self.assertEqual(cases.count("## C3 "), 1)
        causal_prompts = []
        for start, end in (("## C2 ", "## C3 "), ("## C3 ", "## Q3 ")):
            section = cases.split(start, 1)[1].split(end, 1)[0]
            causal_prompts.append(
                " ".join(
                    line[2:].strip()
                    for line in section.splitlines()
                    if line.startswith("> ")
                )
            )
        self.assertEqual(
            causal_prompts[0].replace(" superior ", " equivalent "),
            causal_prompts[1],
        )
        self.assertEqual(causal_prompts[0].count(" superior "), 1)
        self.assertEqual(causal_prompts[1].count(" equivalent "), 1)
        comparison = (
            H21_ROOT / "qualification" / "h2.1-20260719" / "COMPARISON-PROTOCOL.md"
        ).read_text()
        for contract in (
            "Q4/Q5/Q7",
            "at least 50%",
            "at least 10%",
            "candidate = A",
            "Stable = A",
            "One noise review",
        ):
            self.assertIn(contract, comparison)

    def test_packaged_diagnostic_locks_owner_trees_and_limits_claims(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(self.plugin / "scripts" / "check-h2-topology.py"),
                "--plugin-root",
                str(self.plugin),
                "--stable-state",
                "not-installed",
                "--require-isolated",
                "--json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["integrity"], "ok")
        self.assertTrue(all(item["status"] == "ok" for item in payload["checks"]))
        for word in ("activation", "owner reads", "passive obligations", "tokens", "usability"):
            self.assertIn(word, payload["claim_ceiling"])

    def test_packaged_diagnostic_fails_closed_on_companion_gate_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin = Path(directory) / "mindthus-beta"
            shutil.copytree(self.plugin, plugin)
            owner = (
                plugin
                / "skills"
                / "using-mindthus"
                / "references"
                / "owners"
                / "mpg"
                / "OWNER.md"
            )
            text = owner.read_text()
            self.assertEqual(text.count("A bare trend or accepted mainline does not qualify."), 1)
            owner.write_text(
                text.replace(
                    "A bare trend or accepted mainline does not qualify.",
                    "A bare trend may qualify.",
                )
            )
            result = subprocess.run(
                [
                    "python3",
                    str(plugin / "scripts" / "check-h2-topology.py"),
                    "--plugin-root",
                    str(plugin),
                    "--stable-state",
                    "not-installed",
                    "--require-isolated",
                    "--json",
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["integrity"], "failed")
            self.assertEqual(
                next(item for item in payload["checks"] if item["id"] == "owner-lock:mpg")["status"],
                "failed",
            )

    def test_packaged_diagnostic_rejects_duplicate_correction_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin = Path(directory) / "mindthus-beta"
            shutil.copytree(self.plugin, plugin)
            profile_path = plugin / "beta" / "release-profile.json"
            profile = json.loads(profile_path.read_text())
            profile["package_time_owner_correction"]["targets"].append(
                dict(profile["package_time_owner_correction"]["targets"][0])
            )
            profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
            result = subprocess.run(
                [
                    "python3",
                    str(plugin / "scripts" / "check-h2-topology.py"),
                    "--plugin-root",
                    str(plugin),
                    "--stable-state",
                    "not-installed",
                    "--require-isolated",
                    "--json",
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["integrity"], "failed")
            self.assertEqual(
                next(
                    item
                    for item in payload["checks"]
                    if item["id"] == "h2.1-companion-correction"
                )["status"],
                "failed",
            )


if __name__ == "__main__":
    unittest.main()
