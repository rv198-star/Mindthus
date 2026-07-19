import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANDIDATE = REPO / "beta" / "2.0-roi-thin-core"
PROFILE = json.loads((CANDIDATE / "profile.json").read_text(encoding="utf-8"))
OVERLAY = CANDIDATE / "skills" / "using-mindthus" / "SKILL.md"
STABLE_USING = REPO / "skills" / "using-mindthus" / "SKILL.md"
OWNERS = tuple(PROFILE["runtime_shape"]["unchanged_owner_skills"])


class RoiThinCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tempdir = tempfile.TemporaryDirectory(prefix="mindthus-roi-test-")
        root = Path(cls._tempdir.name)
        cls.stable_out = root / "stable"
        cls.candidate_out = root / "candidate"

        cls.stable_build = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "build-release-pack.py"),
                "--package",
                "plugins",
                "--out",
                str(cls.stable_out),
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        if cls.stable_build.returncode != 0:
            raise AssertionError(cls.stable_build.stderr + cls.stable_build.stdout)

        cls.candidate_build = subprocess.run(
            [
                sys.executable,
                str(CANDIDATE / "build-candidate.py"),
                "--out",
                str(cls.candidate_out),
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        if cls.candidate_build.returncode != 0:
            raise AssertionError(cls.candidate_build.stderr + cls.candidate_build.stdout)

        cls.stable_plugin = cls.stable_out / "codex-plugin" / "mindthus"
        cls.candidate_plugin = cls.candidate_out / "mindthus"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tempdir.cleanup()

    def test_profile_freezes_the_subtractive_scope(self) -> None:
        self.assertEqual(PROFILE["candidate"], "2.0.0-roi.1")
        self.assertEqual(PROFILE["surface"], "codex-plugin")
        self.assertEqual(
            PROFILE["runtime_shape"]["changed_skill_paths"],
            ["skills/using-mindthus/SKILL.md"],
        )
        self.assertFalse(PROFILE["runtime_shape"]["session_start_hook"])
        self.assertFalse(PROFILE["runtime_shape"]["model_name_routing"])
        self.assertFalse(PROFILE["runtime_shape"]["second_guard"])
        self.assertFalse(PROFILE["runtime_shape"]["default_prompt_delta"])
        self.assertFalse(PROFILE["release_preparation"])

    def test_thin_core_is_materially_smaller_than_stable(self) -> None:
        candidate_bytes = len(OVERLAY.read_bytes())
        baseline_bytes = len(STABLE_USING.read_bytes())
        gates = PROFILE["qualification_gates"]
        self.assertLessEqual(candidate_bytes, gates["using_mindthus_max_bytes"])
        self.assertLessEqual(
            candidate_bytes / baseline_bytes,
            gates["using_mindthus_max_baseline_ratio"],
        )

    def test_thin_core_keeps_only_shared_decision_obligations(self) -> None:
        text = OVERLAY.read_text(encoding="utf-8")
        lowered = text.lower()
        for required in (
            "Frame and whole",
            "Decision context",
            "Evidence ceiling",
            "Anti-Spiral",
            "one visible thesis",
            "decision-changing evidence",
        ):
            self.assertIn(required, text)
        for method in ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan"):
            self.assertNotIn(method, lowered)
        self.assertNotIn("Conditional Resources", text)
        self.assertNotIn("resources/", text)
        self.assertNotIn("scripts/", text)
        self.assertNotIn("gpt-", lowered)

    def test_frontmatter_routes_hard_judgment_without_method_atlas(self) -> None:
        text = OVERLAY.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        _, frontmatter, _ = text.split("---", 2)
        fields = {
            line.split(":", 1)[0].strip()
            for line in frontmatter.splitlines()
            if line.strip()
        }
        self.assertEqual(fields, {"name", "description"})
        self.assertIn("hard judgment point", frontmatter)
        self.assertIn("activate directly", frontmatter)
        self.assertNotIn("any Mindthus judgment lens may apply", frontmatter)

    def test_candidate_build_changes_only_manifest_identity_and_entry(self) -> None:
        stable_files = {
            path.relative_to(self.stable_plugin)
            for path in self.stable_plugin.rglob("*")
            if path.is_file()
        }
        candidate_files = {
            path.relative_to(self.candidate_plugin)
            for path in self.candidate_plugin.rglob("*")
            if path.is_file()
        }
        self.assertEqual(candidate_files - stable_files, {Path("candidate-profile.json")})
        self.assertEqual(stable_files - candidate_files, set())

        allowed_deltas = {
            Path(".codex-plugin/plugin.json"),
            Path("skills/using-mindthus/SKILL.md"),
        }
        actual_deltas = {
            relative
            for relative in stable_files
            if (self.stable_plugin / relative).read_bytes()
            != (self.candidate_plugin / relative).read_bytes()
        }
        self.assertEqual(actual_deltas, allowed_deltas)

    def test_all_owner_trees_and_stable_prompt_are_unchanged(self) -> None:
        for owner in OWNERS:
            stable_tree = self.stable_plugin / "skills" / owner
            candidate_tree = self.candidate_plugin / "skills" / owner
            stable_files = sorted(path.relative_to(stable_tree) for path in stable_tree.rglob("*") if path.is_file())
            candidate_files = sorted(path.relative_to(candidate_tree) for path in candidate_tree.rglob("*") if path.is_file())
            self.assertEqual(candidate_files, stable_files, owner)
            for relative in stable_files:
                self.assertEqual(
                    (candidate_tree / relative).read_bytes(),
                    (stable_tree / relative).read_bytes(),
                    f"{owner}/{relative}",
                )

        stable_manifest = json.loads(
            (self.stable_plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        candidate_manifest = json.loads(
            (self.candidate_plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            candidate_manifest["interface"]["defaultPrompt"],
            stable_manifest["interface"]["defaultPrompt"],
        )
        self.assertNotIn("hooks", candidate_manifest)

    def test_candidate_marketplace_is_isolated_and_unpublished(self) -> None:
        marketplace = json.loads(
            (self.candidate_out / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        manifest = json.loads(
            (self.candidate_plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        packaged_profile = json.loads(
            (self.candidate_plugin / "candidate-profile.json").read_text(encoding="utf-8")
        )
        self.assertEqual(marketplace["name"], "mindthus-roi")
        self.assertEqual(manifest["name"], "mindthus")
        self.assertEqual(manifest["version"], "2.0.0-roi.1")
        self.assertEqual(packaged_profile["status"], "unpublished-candidate")
        self.assertEqual(len(packaged_profile["overlay_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
