import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_packaging_docs import parse_frontmatter_mapping


REPO = Path(__file__).resolve().parents[1]
PROFILE_ROOT = REPO / "beta" / "2.0-next-native-thin-router"
BUILD_SCRIPT = REPO / "scripts" / "build-release-pack.py"
OWNER_NAMES = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")


class NativeThinRouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tempdir = tempfile.TemporaryDirectory()
        cls.temp = Path(cls._tempdir.name)
        cls.out = cls.temp / "release"
        cls.build = subprocess.run(
            [
                "python3",
                str(BUILD_SCRIPT),
                "--release-line",
                "2.0-next-native-thin-router",
                "--package",
                "plugins",
                "--out",
                str(cls.out),
            ],
            text=True,
            capture_output=True,
        )
        if cls.build.returncode != 0:
            raise AssertionError(cls.build.stderr + cls.build.stdout)
        cls.marketplace = cls.out / "codex-plugin"
        cls.plugin = cls.marketplace / "mindthus-beta"
        cls.profile = json.loads(
            (PROFILE_ROOT / "release-profile.json").read_text(encoding="utf-8")
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tempdir.cleanup()

    def run_diagnostic(self, plugin: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(plugin / "scripts" / "check-native-router.py"),
                "--plugin-root",
                str(plugin),
                *args,
            ],
            text=True,
            capture_output=True,
        )

    def test_profile_is_unpublished_codex_only_candidate(self) -> None:
        self.assertEqual(self.profile["schema_version"], "mindthus-release-profile-v0.3")
        self.assertEqual(self.profile["version"], "2.0.0-next.1")
        self.assertEqual(self.profile["status"], "static-candidate")
        self.assertEqual(self.profile["live_qualification"], "not-authorized")
        self.assertEqual(self.profile["behavioral_evaluation"], "not-authorized")
        self.assertEqual(self.profile["carrier_mode"], "native-skill-description")
        self.assertEqual(self.profile["supported_surfaces"], ["codex-plugin"])
        self.assertNotIn("beta.3", json.dumps(self.profile).lower())

    def test_build_contains_only_codex_plugin_surface(self) -> None:
        self.assertTrue((self.plugin / ".codex-plugin" / "plugin.json").is_file())
        self.assertFalse((self.out / "claude-code").exists())
        self.assertFalse((self.out / "codex").exists())
        self.assertFalse((self.out / "opencode").exists())

        marketplace = json.loads(
            (self.marketplace / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(marketplace["name"], "mindthus-beta")
        self.assertEqual(marketplace["plugins"][0]["name"], "mindthus-beta")
        self.assertEqual(
            marketplace["plugins"][0]["source"],
            {"source": "local", "path": "./mindthus-beta"},
        )

    def test_manifest_has_neutral_prompt_and_no_hook_contract(self) -> None:
        manifest = json.loads(
            (self.plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "mindthus-beta")
        self.assertEqual(manifest["version"], "2.0.0-next.1")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("hooks", manifest)
        prompt = manifest["interface"]["defaultPrompt"]
        self.assertEqual(prompt, ["Apply the smallest sufficient Mindthus lens."])
        self.assertLessEqual(
            len(prompt[0].encode("utf-8")),
            self.profile["budgets"]["default_prompt_max_bytes"],
        )
        for token in ("route", "owner", "using-mindthus", "mindthus-beta"):
            self.assertNotIn(token, prompt[0].lower())

    def test_thin_entry_is_the_only_active_entry_body(self) -> None:
        skills = sorted(
            path.name
            for path in (self.plugin / "skills").iterdir()
            if (path / "SKILL.md").is_file()
        )
        self.assertEqual(skills, sorted((*OWNER_NAMES, "using-mindthus")))
        using = self.plugin / "skills" / "using-mindthus" / "SKILL.md"
        text = using.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter_mapping(text.split("---", 2)[1])
        budgets = self.profile["budgets"]
        self.assertEqual(set(frontmatter), {"name", "description"})
        self.assertEqual(frontmatter["name"], "using-mindthus")
        self.assertIn("Mandatory thin Mindthus entry for every conversation", frontmatter["description"])
        self.assertLessEqual(len(text.split()), budgets["using_mindthus_max_words"])
        self.assertLessEqual(len(text.encode("utf-8")), budgets["using_mindthus_max_bytes"])
        self.assertLessEqual(
            len(frontmatter["description"].encode("utf-8")),
            budgets["description_max_bytes"],
        )
        for phrase in (
            "**Direct:**",
            "**Evidence first:**",
            "**Hard judgment:**",
            "**Frame:**",
            "**Whole:**",
            "**Decision context:**",
            "**Anti-Spiral:**",
        ):
            self.assertIn(phrase, text)
        for owner in OWNER_NAMES:
            self.assertNotIn(owner, text.lower())
        self.assertFalse(any(path.is_file() for path in using.parent.rglob("*") if path != using))

    def test_no_second_router_or_active_stable_policy_is_packaged(self) -> None:
        for relative in self.profile["forbidden_active_paths"]:
            self.assertFalse((self.plugin / relative).exists(), relative)
        self.assertFalse((self.plugin / "hooks").exists())
        self.assertFalse((self.plugin / "runtime").exists())
        self.assertFalse((self.plugin / "AGENTS.md").exists())
        for relative in self.profile["reference_only_paths"]:
            self.assertTrue((self.plugin / relative).exists(), relative)

    def test_owner_contracts_are_coordinate_only_adaptations(self) -> None:
        for owner in OWNER_NAMES:
            source_root = REPO / "skills" / owner
            built_root = self.plugin / "skills" / owner
            source_files = sorted(
                path.relative_to(source_root)
                for path in source_root.rglob("*")
                if path.is_file()
                and "tests" not in path.relative_to(source_root).parts
                and path.suffix not in {".pyc", ".pyo"}
                and not (
                    path.suffix == ".jsonl"
                    and path.relative_to(source_root) != Path("templates/evidence.jsonl")
                )
            )
            built_files = sorted(
                path.relative_to(built_root) for path in built_root.rglob("*") if path.is_file()
            )
            self.assertEqual(built_files, source_files, owner)
            for relative in source_files:
                source = (source_root / relative).read_bytes()
                built = (built_root / relative).read_bytes()
                if relative.suffix == ".md":
                    source = source.replace(b"mindthus:", b"mindthus-beta:")
                self.assertEqual(built, source, f"{owner}/{relative}")

    def test_authored_and_generated_artifacts_are_locked(self) -> None:
        for relative, expected in self.profile["artifact_sha256"].items():
            actual = hashlib.sha256((self.plugin / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)
        for relative, expected in self.profile["generated_artifact_sha256"][
            "codex-plugin"
        ].items():
            actual = hashlib.sha256((self.plugin / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_diagnostic_proves_only_static_package_and_isolation(self) -> None:
        result = self.run_diagnostic(
            self.plugin,
            "--stable-state",
            "disabled",
            "--require-isolated",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["integrity"], "ok")
        self.assertEqual(payload["native_entry_status"], "packaged-unproven")
        self.assertEqual(payload["direct_owner_status"], "packaged-verified")
        self.assertEqual(payload["runtime_isolation_status"], "isolated-reported")
        for unproven in ("activation", "passive recall", "owner selection", "tokens", "latency"):
            self.assertIn(unproven, payload["claim_ceiling"])

    def test_diagnostic_blocks_stable_coactivation_from_host_inventory(self) -> None:
        inventory = self.temp / "host-plugins.json"
        inventory.write_text(
            json.dumps(
                {
                    "plugins": [
                        {"name": "mindthus", "enabled": True},
                        {"name": "mindthus-beta", "enabled": True},
                    ]
                }
            ),
            encoding="utf-8",
        )
        result = self.run_diagnostic(
            self.plugin,
            "--host-plugins-json",
            str(inventory),
            "--require-isolated",
            "--json",
        )
        self.assertEqual(result.returncode, 3, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runtime_isolation_status"], "conflict")
        self.assertIn("co-enabled", payload["claim_ceiling"])

    def test_diagnostic_fails_closed_after_entry_tamper(self) -> None:
        tampered = self.temp / "tampered-plugin"
        shutil.copytree(self.plugin, tampered)
        using = tampered / "skills" / "using-mindthus" / "SKILL.md"
        using.write_text(using.read_text(encoding="utf-8") + "\nextra policy\n", encoding="utf-8")
        result = self.run_diagnostic(tampered, "--stable-state", "disabled", "--json")
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["integrity"], "failed")
        failed_ids = {check["id"] for check in payload["checks"] if check["status"] == "failed"}
        self.assertIn("artifact:skills/using-mindthus/SKILL.md", failed_ids)

    def test_successor_rejects_non_plugin_package_selections(self) -> None:
        for package in ("all", "skills"):
            out = self.temp / f"rejected-{package}"
            result = subprocess.run(
                [
                    "python3",
                    str(BUILD_SCRIPT),
                    "--release-line",
                    "2.0-next-native-thin-router",
                    "--package",
                    package,
                    "--out",
                    str(out),
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("supports package selection(s): plugins", result.stderr)


if __name__ == "__main__":
    unittest.main()
