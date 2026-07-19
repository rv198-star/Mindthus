import hashlib
import json
import os
import shutil
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
        cls.beta_archive = root / "mindthus-beta-1.5.1-roi-beta.tar.gz"
        cls.beta_checksum = root / "SHA256SUMS"
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
                "--archive",
                str(cls.beta_archive),
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
        self.assertEqual(PROFILE["status"], "beta-prerelease")
        self.assertEqual(PROFILE["version"], "1.5.1-roi-beta")
        self.assertEqual(PROFILE["package_identity"], "mindthus-beta")
        self.assertEqual(PROFILE["shared_core"]["version"], "1.5.1")
        self.assertEqual(
            PROFILE["shared_core"]["ref"],
            "360b3faa3a8d28fbb62fcd342fcdc3e8d5ca4fea",
        )
        self.assertEqual(
            PROFILE["runtime_profile"]["implementation_ref"],
            "493f9520b75f582aa22f6c8647ec08eab3e122d3",
        )
        self.assertEqual(PROFILE["publication"]["status"], "published")
        self.assertEqual(PROFILE["publication"]["source_tag"], "v1.5.1-roi-beta")
        self.assertEqual(
            PROFILE["publication"]["allowed_release_shape_if_separately_authorized"],
            "single-github-release-with-stable-and-experimental-roi-packages",
        )
        self.assertEqual(PROFILE["publication"]["release_train"], "1.5.1")
        self.assertEqual(PROFILE["publication"]["release_asset_channel"], "experimental-roi-beta")
        self.assertTrue(PROFILE["publication"]["github_release"])
        self.assertEqual(
            PROFILE["publication"]["release_url"],
            "https://github.com/rv198-star/Mindthus/releases/tag/v1.5.1",
        )
        self.assertFalse(PROFILE["publication"]["marketplace"])
        self.assertFalse(
            PROFILE["runtime_profile"]["convergence_evidence"]["required_at_build"]
        )
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        notes = (REPO / "docs" / "releases" / "v1.5.1-roi-beta.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("experimental asset", changelog)
        self.assertIn("experimental asset", notes)
        self.assertIn("发布源码 tag", changelog)
        self.assertIn("作为 `v1.5.1` GitHub Release", notes)
        self.assertIn("新增发布包：1.5.1 ROI Beta（GPT/Sol）", changelog)
        self.assertIn("与 1.5.1 Stable 的关系", changelog)
        self.assertIn("不是 `1.5.1 Stable` 的替代版", changelog)
        self.assertIn("不触发用户安装、配置", changelog)
        self.assertIn("或工作流的自动迁移", changelog)
        self.assertNotIn("预发布日期", changelog + notes)

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
                beta_bytes = (beta_tree / relative).read_bytes()
                stable_bytes = (stable_tree / relative).read_bytes()
                self.assertEqual(
                    beta_bytes.replace(b"mindthus-beta:", b"mindthus:"),
                    stable_bytes,
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
        expected_special = {
            Path(".codex-plugin/plugin.json"),
            Path("skills/using-mindthus/SKILL.md"),
            Path("skills/3l5s/SKILL.md"),
            Path("scripts/log-mindthus-runtime.py"),
        }
        self.assertTrue(expected_special.issubset(actual_deltas))
        for relative in actual_deltas - expected_special:
            stable_bytes = (self.stable_plugin / relative).read_bytes()
            beta_bytes = (self.beta_plugin / relative).read_bytes()
            self.assertIn(b"mindthus:", stable_bytes, relative)
            self.assertEqual(
                beta_bytes.replace(b"mindthus-beta:", b"mindthus:"),
                stable_bytes,
                relative,
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
        self.assertEqual(manifest["version"], "1.5.1-roi-beta")
        prompt = "\n".join(manifest["interface"]["defaultPrompt"])
        self.assertIn("mindthus-beta:using-mindthus", prompt)
        self.assertNotIn("mindthus:using-mindthus", prompt)
        self.assertNotIn("hooks", manifest)
        self.assertLessEqual(len(prompt.encode("utf-8")), 128)
        for path in self.beta_plugin.rglob("*"):
            if path.is_file():
                self.assertNotIn(b"mindthus:", path.read_bytes(), path)

    def test_beta_runtime_diagnostics_use_only_beta_coordinates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mindthus-beta-diagnostic-") as temporary:
            codex_home = Path(temporary) / "home"
            cache = (
                codex_home
                / "plugins"
                / "cache"
                / "mindthus-beta"
                / "mindthus-beta"
                / "1.5.1-roi-beta"
            )
            shutil.copytree(self.beta_plugin, cache)
            codex_home.mkdir(exist_ok=True)
            (codex_home / "config.toml").write_text(
                "[marketplaces.mindthus-beta]\n"
                "source_type = \"local\"\n"
                f"source = {json.dumps(str(self.beta_out))}\n",
                encoding="utf-8",
            )
            command = [
                sys.executable,
                str(cache / "scripts" / "log-mindthus-runtime.py"),
                "--codex-home",
                str(codex_home),
                "--json",
                "--strict",
            ]
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["version"], "1.5.1-roi-beta")
            self.assertEqual(report["summary"]["status"], "ok")
            self.assertIn(
                "mindthus-beta/mindthus-beta/1.5.1-roi-beta",
                report["locations"]["cache"]["root"],
            )
            self.assertNotIn("/mindthus/mindthus/", json.dumps(report))

            thin_core = cache / "skills" / "using-mindthus" / "SKILL.md"
            thin_core.write_text(
                thin_core.read_text(encoding="utf-8").replace("Evidence ceiling:", "Evidence limit:"),
                encoding="utf-8",
            )
            mutated = subprocess.run(command[:-1], text=True, capture_output=True)
            self.assertEqual(mutated.returncode, 0, mutated.stderr)
            self.assertEqual(json.loads(mutated.stdout)["summary"]["status"], "mismatch")

    def test_packaged_profile_and_capability_register_are_auditable(self) -> None:
        packaged = json.loads(
            (self.beta_plugin / "beta-profile.json").read_text(encoding="utf-8")
        )
        register = json.loads(
            (self.beta_plugin / "capability-register.json").read_text(encoding="utf-8")
        )
        self.assertEqual(packaged["shared_core"], PROFILE["shared_core"])
        self.assertEqual(packaged["assembly_source_ref"], subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip())
        self.assertEqual(len(packaged["artifact_manifest_sha256"]), 64)
        self.assertEqual(len(packaged["capability_register_sha256"]), 64)
        self.assertEqual(len(packaged["assembly_inputs_sha256"]), 5)
        for digest in packaged["assembly_inputs_sha256"].values():
            self.assertEqual(len(digest), 64)
        manifest = self.beta_plugin / ".codex-plugin" / "plugin.json"
        self.assertEqual(
            packaged["artifact_manifest_sha256"],
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
        )
        register_path = self.beta_plugin / PROFILE["capability_register"]["artifact_path"]
        self.assertTrue(register_path.is_file())
        self.assertEqual(
            packaged["capability_register_sha256"],
            hashlib.sha256(register_path.read_bytes()).hexdigest(),
        )
        states = {
            item["id"]: item["release_roi_beta"]["state"]
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

    def test_archive_is_byte_reproducible_from_the_same_commit(self) -> None:
        second_out = Path(self._tempdir.name) / "beta-second"
        second_archive = Path(self._tempdir.name) / "second-assets" / self.beta_archive.name
        result = subprocess.run(
            [
                sys.executable,
                str(BETA / "build-internal-beta.py"),
                "--out",
                str(second_out),
                "--archive",
                str(second_archive),
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.beta_archive.read_bytes(), second_archive.read_bytes())
        checksum = self.beta_checksum.read_text(encoding="utf-8")
        self.assertEqual(
            checksum,
            f"{hashlib.sha256(self.beta_archive.read_bytes()).hexdigest()}  {self.beta_archive.name}\n",
        )
        self.assertEqual(
            checksum,
            (second_archive.parent / "SHA256SUMS").read_text(encoding="utf-8"),
        )

    def test_archive_rejects_repository_and_output_tree_paths(self) -> None:
        readme = REPO / "README.md"
        readme_digest = hashlib.sha256(readme.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="mindthus-beta-unsafe-archive-") as temporary:
            root = Path(temporary)
            cases = (
                (root / "repo-output", readme, "outside the repository tree"),
                (root / "self-output", root / "self-output" / "self.tar.gz", "outside the assembly output tree"),
            )
            for output, archive, expected in cases:
                with self.subTest(archive=str(archive)):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(BETA / "build-internal-beta.py"),
                            "--out",
                            str(output),
                            "--archive",
                            str(archive),
                            "--force",
                        ],
                        cwd=REPO,
                        text=True,
                        capture_output=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stderr + result.stdout)
                    self.assertFalse(output.exists())
        self.assertEqual(hashlib.sha256(readme.read_bytes()).hexdigest(), readme_digest)

    def test_archive_rejects_checksum_asset_name_collision(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mindthus-beta-asset-collision-") as temporary:
            root = Path(temporary)
            for reserved_name in ("SHA256SUMS", "sha256sums"):
                with self.subTest(reserved_name=reserved_name):
                    output = root / f"output-{reserved_name}"
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(BETA / "build-internal-beta.py"),
                            "--out",
                            str(output),
                            "--archive",
                            str(root / reserved_name),
                            "--force",
                        ],
                        cwd=REPO,
                        text=True,
                        capture_output=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("reserved SHA256SUMS asset", result.stderr + result.stdout)
                    self.assertFalse(output.exists())
                    self.assertFalse((root / reserved_name).exists())

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is required")
    def test_stable_and_beta_install_and_remove_independently(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mindthus-beta-lifecycle-") as temporary:
            codex_home = Path(temporary) / "home"
            codex_home.mkdir()
            env = {**os.environ, "CODEX_HOME": str(codex_home)}

            def run(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["codex", "plugin", *args, "--json"],
                    env=env,
                    text=True,
                    capture_output=True,
                )

            for marketplace in (self.stable_out / "codex-plugin", self.beta_out):
                result = run("marketplace", "add", str(marketplace))
                self.assertEqual(result.returncode, 0, result.stderr)
            for plugin in ("mindthus@mindthus", "mindthus-beta@mindthus-beta"):
                result = run("add", plugin)
                self.assertEqual(result.returncode, 0, result.stderr)

            installed = json.loads(run("list").stdout)["installed"]
            self.assertEqual({item["name"] for item in installed}, {"mindthus", "mindthus-beta"})
            self.assertEqual(run("remove", "mindthus-beta@mindthus-beta").returncode, 0)
            installed = json.loads(run("list").stdout)["installed"]
            self.assertEqual({item["name"] for item in installed}, {"mindthus"})
            self.assertEqual(run("add", "mindthus-beta@mindthus-beta").returncode, 0)
            self.assertEqual(run("remove", "mindthus@mindthus").returncode, 0)
            installed = json.loads(run("list").stdout)["installed"]
            self.assertEqual({item["name"] for item in installed}, {"mindthus-beta"})

    def test_dirty_checkout_is_rejected_before_assembly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mindthus-beta-dirty-") as temporary:
            clone = Path(temporary) / "clone"
            subprocess.run(
                ["git", "clone", "--local", "--no-hardlinks", str(REPO), str(clone)],
                check=True,
                text=True,
                capture_output=True,
            )
            profile = clone / "beta" / "2.0-beta" / "profile.json"
            profile.write_text(profile.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(clone / "beta" / "2.0-beta" / "build-internal-beta.py"),
                    "--out",
                    str(Path(temporary) / "out"),
                ],
                cwd=clone,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires a clean checkout", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
