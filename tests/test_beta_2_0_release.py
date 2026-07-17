import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_packaging_docs import parse_frontmatter_mapping


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.1"
BUILD_SCRIPT = REPO / "scripts" / "build-release-pack.py"
OWNER_SKILLS = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")
BASELINE_COMMIT = "00da11657bce553cb32e8e90c06ffe959dc08362"


class BetaTwoReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tempdir = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tempdir.name) / "release"
        cls.build = subprocess.run(
            [
                "python3",
                str(BUILD_SCRIPT),
                "--release-line",
                "2.0-beta.1",
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
        cls.codex_marketplace = cls.out / "codex-plugin"
        cls.codex = cls.codex_marketplace / "mindthus-beta"
        cls.claude_marketplace = cls.out / "claude-code"
        cls.claude = cls.claude_marketplace / "mindthus-beta"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tempdir.cleanup()

    def test_release_profile_is_honest_explicit_and_plugin_only(self) -> None:
        profile = json.loads((BETA_ROOT / "release-profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["schema_version"], "mindthus-release-profile-v0.2")
        self.assertEqual(profile["version"], "2.0.0-beta.1")
        self.assertEqual(profile["release_preparation"], "not-started")
        self.assertEqual(profile["behavioral_evaluation"], "deferred-to-beta.2")
        self.assertEqual(profile["path_base"], "plugin-root")
        self.assertEqual(profile["stable_baseline"], "1.4.6")
        self.assertEqual(profile["baseline_commit"], BASELINE_COMMIT)
        self.assertEqual(profile["formal_contracts"], "1.4.6-reference-only")
        self.assertEqual(profile["active_runtime_contract"], "2.0.0-beta.1")
        self.assertEqual(profile["supported_packages"], ["plugins"])
        self.assertEqual(profile["plugin_identity"]["name"], "mindthus-beta")
        self.assertEqual(profile["plugin_identity"]["marketplace_name"], "mindthus-beta")
        self.assertTrue(profile["plugin_identity"]["coinstallable_with_stable"])
        self.assertFalse(profile["plugin_identity"]["coenabled_with_stable"])
        self.assertEqual(
            profile["namespace_adapter"],
            {
                "mode": "package-time-coordinate-only",
                "source_prefix": "mindthus:",
                "runtime_prefix": "mindthus-beta:",
            },
        )
        self.assertTrue(profile["codex_hook_trust_required"])
        self.assertEqual(profile["carrier_verification"], "diagnostic-semantic-execution")
        self.assertEqual(
            profile["stable_runtime_state_observability"],
            "optional-host-cli-inspection-or-explicit-state-input",
        )
        self.assertEqual(profile["join_points"]["host_enforced"], ["session-start"])
        self.assertEqual(
            profile["join_points"]["model_obligated"],
            ["before-route", "before-answer"],
        )
        self.assertEqual(profile["join_points"]["before_answer_sentinel"], "not-implemented")
        self.assertEqual(profile["anti_spiral_state"], "model-context-only")
        self.assertEqual(profile["windows_hook_carrier"], "not-implemented")
        self.assertIn("without passive-recall guarantee", profile["hook_unavailable_fallback"])
        self.assertTrue(
            all(value == "unproven-deferred-to-beta.2" for value in profile["behavioral_claims"].values())
        )
        self.assertEqual(
            set(profile["generated_artifact_sha256"]),
            {"codex-plugin", "claude-plugin"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            rejected = subprocess.run(
                [
                    "python3",
                    str(BUILD_SCRIPT),
                    "--release-line",
                    "2.0-beta.1",
                    "--package",
                    "skills",
                    "--out",
                    str(Path(tmp) / "release"),
                ],
                text=True,
                capture_output=True,
            )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("supports package selection(s): plugins", rejected.stderr)

    def test_beta_has_separate_marketplace_and_plugin_identity(self) -> None:
        codex_marketplace = json.loads(
            (self.codex_marketplace / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        claude_marketplace = json.loads(
            (self.claude_marketplace / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        codex_manifest = json.loads(
            (self.codex / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        claude_manifest = json.loads(
            (self.claude / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )

        self.assertEqual(codex_marketplace["name"], "mindthus-beta")
        self.assertEqual(codex_marketplace["interface"]["displayName"], "Mindthus Beta")
        self.assertEqual(codex_marketplace["plugins"][0]["name"], "mindthus-beta")
        self.assertEqual(
            codex_marketplace["plugins"][0]["source"]["path"],
            "./mindthus-beta",
        )
        self.assertEqual(claude_marketplace["name"], "mindthus-beta")
        self.assertEqual(claude_marketplace["plugins"][0]["name"], "mindthus-beta")
        self.assertEqual(claude_marketplace["plugins"][0]["source"], "./mindthus-beta")
        self.assertEqual(codex_manifest["name"], "mindthus-beta")
        self.assertEqual(claude_manifest["name"], "mindthus-beta")
        self.assertEqual(codex_manifest["version"], "2.0.0-beta.1")
        self.assertEqual(claude_manifest["version"], "2.0.0-beta.1")
        self.assertNotIn("hooks", codex_manifest)
        self.assertTrue((self.codex / "hooks" / "hooks.json").is_file())
        self.assertIn("/hooks", codex_manifest["interface"]["longDescription"])
        self.assertFalse((self.codex_marketplace / "mindthus").exists())
        self.assertFalse((self.claude_marketplace / "claude-plugin").exists())

        starter = codex_manifest["interface"]["defaultPrompt"][0]
        self.assertLessEqual(len(starter), 128)
        self.assertLessEqual(len(starter.encode("utf-8")), 128)
        self.assertIn("Route directly to mindthus-beta:<owner>", starter)
        self.assertIn("mindthus-beta:using-mindthus", starter)
        self.assertIn("only for genuine owner ambiguity", starter)
        self.assertNotIn("hard frame/whole", starter)
        self.assertNotIn("mindthus:using-mindthus", starter)

    def test_hooks_use_only_the_verified_session_start_carrier(self) -> None:
        for plugin_root, root_variable in (
            (self.codex, "PLUGIN_ROOT"),
            (self.claude, "CLAUDE_PLUGIN_ROOT"),
        ):
            hooks = json.loads((plugin_root / "hooks" / "hooks.json").read_text(encoding="utf-8"))
            self.assertEqual(set(hooks["hooks"]), {"SessionStart"})
            session_start = hooks["hooks"]["SessionStart"][0]
            self.assertEqual(session_start["matcher"], "startup|resume|clear|compact")
            self.assertIn(root_variable, session_start["hooks"][0]["command"])
            self.assertFalse(session_start["hooks"][0]["async"])
            self.assertNotIn("commandWindows", session_start["hooks"][0])

    def test_kernel_and_arbitrator_stay_thin_and_keep_the_right_boundaries(self) -> None:
        profile = json.loads((BETA_ROOT / "release-profile.json").read_text(encoding="utf-8"))
        budgets = profile["budgets"]
        kernel = self.codex / "runtime" / "passive-activation-kernel.md"
        using = self.codex / "skills" / "using-mindthus" / "SKILL.md"

        kernel_text = kernel.read_text(encoding="utf-8")
        using_text = using.read_text(encoding="utf-8")
        compact_kernel = " ".join(kernel_text.split())
        stable_using_bytes = len((REPO / "skills" / "using-mindthus" / "SKILL.md").read_bytes())
        self.assertLessEqual(len(kernel_text.encode("utf-8")), budgets["kernel_max_bytes"])
        self.assertLessEqual(len(kernel_text.split()), budgets["kernel_max_words"])
        self.assertLessEqual(len(using_text.encode("utf-8")), budgets["using_mindthus_max_bytes"])
        self.assertLessEqual(len(using_text.split()), budgets["using_mindthus_max_words"])
        self.assertLess(len(kernel_text.encode("utf-8")), stable_using_bytes / 2)
        self.assertLess(len(using_text.encode("utf-8")), stable_using_bytes / 2)

        self.assertIn("Route inside the Beta namespace", compact_kernel)
        self.assertIn("mindthus-beta:<owner>", compact_kernel)
        self.assertIn("mindthus-beta:using-mindthus", compact_kernel)
        self.assertIn("Stable `mindthus` must be disabled", compact_kernel)
        self.assertIn("Owner choice and passive obligations are independent", compact_kernel)
        self.assertIn("one visible thesis, not one active primitive", compact_kernel)
        self.assertIn("Continue only when new evidence justifies another local pass", compact_kernel)
        self.assertNotIn("third touch of the same local object, negative feedback", compact_kernel)
        self.assertIn("Arbitration Only", using_text)
        self.assertIn("bounded Kernel action is clear, act directly", using_text)
        self.assertIn("Clear owner means direct Beta owner invocation", using_text)
        for owner in OWNER_SKILLS:
            self.assertIn(f"mindthus-beta:{owner}", using_text)
        self.assertNotIn("`mindthus:", using_text)
        self.assertFalse((using.parent / "resources").exists())
        beta_runtime_text = f"{kernel_text}\n{using_text}".lower()
        self.assertNotIn("gpt-", beta_runtime_text)
        self.assertNotIn(" sol ", beta_runtime_text)

        _, frontmatter, _ = using_text.split("---", 2)
        parsed = parse_frontmatter_mapping(frontmatter)
        self.assertEqual(set(parsed), {"name", "description"})
        self.assertEqual(parsed["name"], "using-mindthus")

    def test_stable_runtime_and_formal_contracts_are_reference_only(self) -> None:
        profile = json.loads((self.codex / "beta" / "release-profile.json").read_text(encoding="utf-8"))
        for relative in profile["active_runtime_paths"]:
            self.assertTrue((self.codex / relative).exists(), relative)
            self.assertTrue((self.claude / relative).exists(), relative)
        for relative in profile["forbidden_active_paths"]:
            self.assertFalse((self.codex / relative).exists(), relative)
            self.assertFalse((self.claude / relative).exists(), relative)
        for relative in profile["reference_only_paths"]:
            self.assertTrue((self.codex / relative).exists(), relative)
            self.assertTrue((self.claude / relative).exists(), relative)

        stable_manifest = REPO / "scripts" / "primitives" / "manifest.json"
        reference_manifest = self.codex / "reference" / "1.4.6" / "scripts" / "primitives" / "manifest.json"
        self.assertEqual(reference_manifest.read_bytes(), stable_manifest.read_bytes())
        self.assertFalse((self.codex / "scripts" / "primitives" / "manifest.json").exists())

    def test_frozen_reference_lock_covers_owners_contracts_and_stable_runtime(self) -> None:
        lock = json.loads((BETA_ROOT / "reference-lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["stable_baseline"], "1.4.6")
        self.assertEqual(lock["baseline_commit"], BASELINE_COMMIT)
        locked_ids = {record["id"] for record in lock["trees"] + lock["files"]}
        self.assertTrue({f"owner-{name}" for name in OWNER_SKILLS}.issubset(locked_ids))
        self.assertIn("owner-shared-runtime", locked_ids)
        self.assertTrue(
            {
                "formal-methodologies",
                "stable-using-mindthus",
                "stable-primitives-runtime",
                "stable-runtime-log",
            }.issubset(locked_ids)
        )
        self.assertTrue(all(len(record["sha256"]) == 64 for record in lock["trees"] + lock["files"]))

        for skill_name in OWNER_SKILLS:
            source = (REPO / "skills" / skill_name / "SKILL.md").read_bytes()
            expected = source.replace(b"mindthus:", b"mindthus-beta:")
            self.assertEqual(
                (self.codex / "skills" / skill_name / "SKILL.md").read_bytes(),
                expected,
            )
            self.assertEqual(
                (self.claude / "skills" / skill_name / "SKILL.md").read_bytes(),
                expected,
            )

        for plugin_root in (self.codex, self.claude):
            for skill_name in (*OWNER_SKILLS, "using-mindthus"):
                for path in (plugin_root / "skills" / skill_name).rglob("*.md"):
                    self.assertNotIn("mindthus:", path.read_text(encoding="utf-8"), path)

        stable_using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_bytes()
        self.assertEqual(
            (self.codex / "reference" / "1.4.6" / "skills" / "using-mindthus" / "SKILL.md").read_bytes(),
            stable_using,
        )
        self.assertNotEqual(
            (self.codex / "skills" / "using-mindthus" / "SKILL.md").read_bytes(),
            stable_using,
        )

    def test_session_start_injects_the_exact_shared_kernel(self) -> None:
        kernel = (BETA_ROOT / "runtime" / "passive-activation-kernel.md").read_text(
            encoding="utf-8"
        )
        expected = f"<MINDTHUS_PASSIVE_KERNEL>\n{kernel.rstrip()}\n</MINDTHUS_PASSIVE_KERNEL>"

        for plugin_root, variable in (
            (self.codex, "PLUGIN_ROOT"),
            (self.claude, "CLAUDE_PLUGIN_ROOT"),
        ):
            env = os.environ.copy()
            env.pop("PLUGIN_ROOT", None)
            env.pop("CLAUDE_PLUGIN_ROOT", None)
            env[variable] = str(plugin_root)
            result = subprocess.run(
                [str(plugin_root / "hooks" / "session-start")],
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
            self.assertEqual(payload["hookSpecificOutput"]["additionalContext"], expected)

    def test_runtime_diagnostic_caps_claims_and_detects_tampering(self) -> None:
        diagnostic = self.codex / "scripts" / "check-beta-runtime.py"
        unknown = subprocess.run(
            ["python3", str(diagnostic), "--json"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(unknown.returncode, 0, unknown.stderr + unknown.stdout)
        unknown_payload = json.loads(unknown.stdout)
        self.assertEqual(unknown_payload["integrity"], "ok")
        self.assertEqual(unknown_payload["carrier_status"], "verified")
        self.assertEqual(unknown_payload["runtime_isolation_status"], "unverified")
        self.assertEqual(unknown_payload["passive_kernel_status"], "degraded")
        self.assertEqual(unknown_payload["direct_owner_status"], "packaged-verified")
        self.assertIn("runtime isolation is unverified", unknown_payload["claim_ceiling"])
        self.assertTrue(any("/hooks" in action for action in unknown_payload["actions"]))

        required = subprocess.run(
            ["python3", str(diagnostic), "--require-passive"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(required.returncode, 2)

        isolated_required = subprocess.run(
            ["python3", str(diagnostic), "--require-isolated"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(isolated_required.returncode, 3)

        fired = subprocess.run(
            [
                "python3",
                str(diagnostic),
                "--hook-state",
                "fired",
                "--stable-state",
                "not-installed",
                "--require-passive",
                "--require-isolated",
                "--json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(fired.returncode, 0, fired.stderr + fired.stdout)
        fired_payload = json.loads(fired.stdout)
        self.assertEqual(
            fired_payload["passive_kernel_status"],
            "reported-fired-carrier-verified",
        )
        self.assertEqual(fired_payload["runtime_isolation_status"], "isolated-reported")
        self.assertIn("remain unproven until Beta.2", fired_payload["claim_ceiling"])

        with tempfile.TemporaryDirectory() as tmp:
            plugin_list = Path(tmp) / "plugins.json"
            plugin_list.write_text(
                json.dumps(
                    {
                        "installed": [
                            {
                                "pluginId": "mindthus-beta@mindthus-beta",
                                "name": "mindthus-beta",
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            observed = subprocess.run(
                [
                    "python3",
                    str(diagnostic),
                    "--host-plugins-json",
                    str(plugin_list),
                    "--require-isolated",
                    "--json",
                ],
                text=True,
                capture_output=True,
            )
        self.assertEqual(observed.returncode, 0, observed.stderr + observed.stdout)
        observed_payload = json.loads(observed.stdout)
        self.assertEqual(observed_payload["runtime_isolation_status"], "isolated-observed")
        self.assertEqual(observed_payload["runtime_isolation_evidence"], "observed")

        conflict = subprocess.run(
            [
                "python3",
                str(diagnostic),
                "--stable-state",
                "enabled",
                "--json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(conflict.returncode, 3)
        conflict_payload = json.loads(conflict.stdout)
        self.assertEqual(conflict_payload["runtime_isolation_status"], "conflict")
        self.assertIn("not isolated", conflict_payload["claim_ceiling"])

        with tempfile.TemporaryDirectory() as tmp:
            tampered_root = Path(tmp) / "mindthus-beta"
            shutil.copytree(self.codex, tampered_root)
            kernel = tampered_root / "runtime" / "passive-activation-kernel.md"
            kernel.write_text(kernel.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
            tampered = subprocess.run(
                ["python3", str(tampered_root / "scripts" / "check-beta-runtime.py"), "--json"],
                text=True,
                capture_output=True,
            )
        self.assertEqual(tampered.returncode, 1)
        tampered_payload = json.loads(tampered.stdout)
        self.assertEqual(tampered_payload["integrity"], "failed")
        self.assertTrue(
            any(
                check["id"] == "artifact:runtime/passive-activation-kernel.md"
                and check["status"] == "failed"
                for check in tampered_payload["checks"]
            )
        )

    def test_runtime_diagnostic_rejects_generated_carrier_manifest_and_runtime_tampering(self) -> None:
        cases = (
            (
                "hook-script",
                "hooks/session-start",
                lambda path: path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        'kernel_path="$plugin_root/runtime/passive-activation-kernel.md"',
                        'kernel_path="$plugin_root/BETA.md"',
                    ),
                    encoding="utf-8",
                ),
                "generated-artifact:hooks/session-start",
            ),
            (
                "hook-config",
                "hooks/hooks.json",
                lambda path: path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "${PLUGIN_ROOT}/hooks/session-start",
                        "/bin/false",
                    ),
                    encoding="utf-8",
                ),
                "generated-artifact:hooks/hooks.json",
            ),
            (
                "manifest",
                ".codex-plugin/plugin.json",
                lambda path: path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        '"version": "2.0.0-beta.1"',
                        '"version": "999.0.0-tampered"',
                    ),
                    encoding="utf-8",
                ),
                "generated-artifact:.codex-plugin/plugin.json",
            ),
            (
                "shared-runtime",
                "_runtime/core/io.py",
                lambda path: path.write_text(
                    path.read_text(encoding="utf-8") + "\n# tampered\n",
                    encoding="utf-8",
                ),
                "locked-tree:owner-shared-runtime",
            ),
        )

        for label, relative, mutate, expected_check in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                tampered_root = Path(tmp) / "mindthus-beta"
                shutil.copytree(self.codex, tampered_root)
                mutate(tampered_root / relative)
                result = subprocess.run(
                    [
                        "python3",
                        str(tampered_root / "scripts" / "check-beta-runtime.py"),
                        "--hook-state",
                        "fired",
                        "--stable-state",
                        "not-installed",
                        "--require-passive",
                        "--require-isolated",
                        "--json",
                    ],
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["integrity"], "failed")
                self.assertEqual(payload["passive_kernel_status"], "degraded")
                self.assertTrue(
                    any(
                        check["id"] == expected_check and check["status"] == "failed"
                        for check in payload["checks"]
                    ),
                    payload,
                )

    def test_formal_methodology_files_remain_exact_reference_copies(self) -> None:
        for filename in ("primitive-activation.md", "shared-primitives.md", "wae.md"):
            source = (REPO / "docs" / "methodologies" / filename).read_bytes()
            for plugin_root in (self.codex, self.claude):
                packaged = (
                    plugin_root
                    / "reference"
                    / "1.4.6"
                    / "docs"
                    / "methodologies"
                    / filename
                )
                self.assertEqual(packaged.read_bytes(), source)
                self.assertFalse((plugin_root / "docs" / "methodologies" / filename).exists())


if __name__ == "__main__":
    unittest.main()
