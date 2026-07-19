import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA = REPO / "beta" / "2.0-beta"
PROFILE = json.loads((BETA / "profile.json").read_text(encoding="utf-8"))
HISTORICAL = REPO / "beta" / "2.0-roi-thin-core"
HISTORICAL_PROFILE = json.loads(
    (HISTORICAL / "profile.json").read_text(encoding="utf-8")
)


class InternalBetaCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tempdir = tempfile.TemporaryDirectory(prefix="mindthus-internal-beta-test-")
        root = Path(cls._tempdir.name)
        cls.stable_out = root / "stable"
        cls.beta_out = root / "beta"
        stable = subprocess.run(
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
        if stable.returncode != 0:
            raise AssertionError(stable.stderr + stable.stdout)
        beta = subprocess.run(
            [
                sys.executable,
                str(BETA / "build-internal-beta.py"),
                "--out",
                str(cls.beta_out),
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        if beta.returncode != 0:
            raise AssertionError(beta.stderr + beta.stdout)
        cls.stable_plugin = cls.stable_out / "codex-plugin" / "mindthus"
        cls.beta_plugin = cls.beta_out / "mindthus-beta"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tempdir.cleanup()

    def test_internal_identity_and_immutable_refs(self) -> None:
        self.assertEqual(PROFILE["status"], "internal-beta")
        self.assertEqual(PROFILE["version"], "2.0.0-beta.1")
        self.assertEqual(PROFILE["package_identity"], "mindthus-beta")
        self.assertEqual(PROFILE["shared_core"]["version"], "1.5.0")
        self.assertEqual(
            PROFILE["shared_core"]["ref"],
            "2cd323d4875069bef17b137a6c7dd50bb06680f8",
        )
        self.assertEqual(
            PROFILE["runtime_profile"]["implementation_ref"],
            "493f9520b75f582aa22f6c8647ec08eab3e122d3",
        )
        self.assertFalse(PROFILE["publication"]["github_release"])
        self.assertFalse(PROFILE["publication"]["marketplace"])

    def test_shared_1_5_capabilities_are_present_and_identical(self) -> None:
        shared_paths = (
            Path("skills/tplan/scripts/render_execution_cost_tree.py"),
            Path("skills/tplan/resources/execution-trace.md"),
            Path("skills/tvg/resources/atlas-search-contract.json"),
            Path("skills/tvg/scripts/atlas/validate_trace.py"),
            Path(
                "skills/tvg/resources/value-profiles/cinematic-visual-direction/profile.md"
            ),
        )
        for relative in shared_paths:
            self.assertTrue((self.beta_plugin / relative).is_file(), relative)
            self.assertEqual(
                (self.beta_plugin / relative).read_bytes(),
                (self.stable_plugin / relative).read_bytes(),
                relative,
            )

    def test_all_non_corrected_owner_trees_match_stable_1_5(self) -> None:
        for owner in ("edsp", "sela", "mpg", "wae", "tvg", "tplan"):
            stable_tree = self.stable_plugin / "skills" / owner
            beta_tree = self.beta_plugin / "skills" / owner
            stable_files = sorted(
                path.relative_to(stable_tree)
                for path in stable_tree.rglob("*")
                if path.is_file()
            )
            beta_files = sorted(
                path.relative_to(beta_tree)
                for path in beta_tree.rglob("*")
                if path.is_file()
            )
            self.assertEqual(beta_files, stable_files, owner)
            for relative in stable_files:
                self.assertEqual(
                    (beta_tree / relative).read_bytes(),
                    (stable_tree / relative).read_bytes(),
                    f"{owner}/{relative}",
                )

    def test_runtime_delta_is_exactly_roi_2_plus_identity(self) -> None:
        stable_files = {
            path.relative_to(self.stable_plugin)
            for path in self.stable_plugin.rglob("*")
            if path.is_file()
        }
        beta_files = {
            path.relative_to(self.beta_plugin)
            for path in self.beta_plugin.rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            beta_files - stable_files,
            {Path("beta-profile.json"), Path("capability-register.json")},
        )
        self.assertEqual(stable_files - beta_files, set())
        actual_deltas = {
            relative
            for relative in stable_files
            if (self.stable_plugin / relative).read_bytes()
            != (self.beta_plugin / relative).read_bytes()
        }
        self.assertEqual(
            actual_deltas,
            {
                Path(".codex-plugin/plugin.json"),
                Path("skills/using-mindthus/SKILL.md"),
                Path("skills/3l5s/SKILL.md"),
            },
        )
        self.assertEqual(
            (self.beta_plugin / "skills/using-mindthus/SKILL.md").read_bytes(),
            (HISTORICAL / "skills/using-mindthus/SKILL.md").read_bytes(),
        )

    def test_qualified_three_l5s_replacement_applies_to_1_5(self) -> None:
        correction = HISTORICAL_PROFILE["package_time_contract_correction"]
        stable = (self.stable_plugin / correction["path"]).read_text(encoding="utf-8")
        beta = (self.beta_plugin / correction["path"]).read_text(encoding="utf-8")
        self.assertEqual(stable.count(correction["before"]), 1)
        self.assertEqual(beta, stable.replace(correction["before"], correction["after"]))

    def test_beta_namespace_is_isolated_from_stable(self) -> None:
        marketplace = json.loads(
            (
                self.beta_out / ".agents" / "plugins" / "marketplace.json"
            ).read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (
                self.beta_plugin / ".codex-plugin" / "plugin.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(marketplace["name"], "mindthus-beta")
        self.assertEqual(marketplace["plugins"][0]["name"], "mindthus-beta")
        self.assertEqual(
            marketplace["plugins"][0]["source"]["path"], "./mindthus-beta"
        )
        self.assertEqual(manifest["name"], "mindthus-beta")
        self.assertEqual(manifest["version"], "2.0.0-beta.1")
        prompt = "\n".join(manifest["interface"]["defaultPrompt"])
        self.assertIn("mindthus-beta:using-mindthus", prompt)
        self.assertNotIn("mindthus:using-mindthus", prompt)
        self.assertNotIn("hooks", manifest)

    def test_packaged_profile_and_capability_register_are_auditable(self) -> None:
        packaged = json.loads(
            (self.beta_plugin / "beta-profile.json").read_text(encoding="utf-8")
        )
        register = json.loads(
            (self.beta_plugin / "capability-register.json").read_text(encoding="utf-8")
        )
        self.assertEqual(packaged["shared_core"], PROFILE["shared_core"])
        self.assertEqual(len(packaged["runtime_overlay_sha256"]), 64)
        self.assertEqual(len(packaged["historical_profile_sha256"]), 64)
        states = {
            item["id"]: item["release_2x"]["state"]
            for item in register["capabilities"]
        }
        self.assertEqual(
            states,
            {
                "tvg-profile-atlas-v1": "included",
                "tplan-execution-cost-tree-v1": "included",
                "roi.2-thin-core": "included",
            },
        )


if __name__ == "__main__":
    unittest.main()
