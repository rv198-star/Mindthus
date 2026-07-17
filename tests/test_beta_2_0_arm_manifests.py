import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BETA_ROOT = REPO / "beta" / "2.0.0-beta.2"
SEALER = BETA_ROOT / "runtime" / "seal-arm-manifest.py"
MATRIX = BETA_ROOT / "fixtures" / "arm-matrix.json"
SCHEMA = BETA_ROOT / "arm-manifest.schema.json"


class BetaTwoArmManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name)
        self.cases = json.loads(MATRIX.read_text(encoding="utf-8"))["cases"]
        self.specs: dict[str, Path] = {}
        self.manifests: dict[str, Path] = {}
        self.packages: dict[tuple[str, str], Path] = {}
        self.hosts: dict[str, Path] = {}
        self.case_files: dict[str, dict[str, Path]] = {}
        self._prepare_fixture_matrix()

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    @staticmethod
    def _write_json(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _run(self, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SEALER), *[str(arg) for arg in args]],
            cwd=REPO,
            text=True,
            capture_output=True,
        )

    def _make_package(self, surface: str, package_kind: str) -> Path:
        key = (surface, package_kind)
        if key in self.packages:
            return self.packages[key]
        root = self.root / "packages" / surface / package_kind
        name = "mindthus" if package_kind == "stable" else "mindthus-beta"
        version = "1.4.6" if package_kind == "stable" else "2.0.0-beta.1"
        if surface == "codex-plugin":
            manifest_path = root / ".codex-plugin" / "plugin.json"
            manifest = {
                "name": name,
                "version": version,
                "interface": {
                    "defaultPrompt": [
                        "Use mindthus:using-mindthus when needed."
                        if package_kind == "stable"
                        else "Route directly to mindthus-beta:<owner>."
                    ]
                },
            }
        else:
            manifest_path = root / ".claude-plugin" / "plugin.json"
            manifest = {"name": name, "version": version}
        self._write_json(manifest_path, manifest)

        skill = root / "skills" / "example" / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        prefix = "mindthus:" if package_kind == "stable" else "mindthus-beta:"
        skill.write_text(f"---\nname: example\n---\nRoute through {prefix}example.\n", encoding="utf-8")
        if package_kind == "beta":
            self._write_json(
                root / "hooks" / "hooks.json",
                {"hooks": {"SessionStart": [{"matcher": "startup|resume|clear|compact"}]}},
            )
            kernel = root / "runtime" / "passive-activation-kernel.md"
            kernel.parent.mkdir(parents=True, exist_ok=True)
            kernel.write_text("Passive primitive obligations.\n", encoding="utf-8")
        self.packages[key] = root
        return root

    def _plugin_list(self, surface: str, arm_id: str) -> object:
        stable_enabled = arm_id == "stable"
        entries = [
            {
                "pluginId": "mindthus@mindthus",
                "name": "mindthus",
                "enabled": stable_enabled,
            },
            {
                "pluginId": "mindthus-beta@mindthus-beta",
                "name": "mindthus-beta",
                "enabled": not stable_enabled,
            },
            {"pluginId": "unrelated@example", "name": "unrelated", "enabled": True},
        ]
        return {"installed": entries} if surface == "codex-plugin" else entries

    def _runtime_diagnostic(self, surface: str, arm_id: str) -> dict[str, object]:
        hook_state = "disabled" if arm_id == "direct-only" else "fired"
        passive = "degraded" if arm_id == "direct-only" else "reported-fired-carrier-verified"
        return {
            "schema_version": "mindthus-beta-runtime-diagnostic-v0.2",
            "release_line": "2.0-beta.1",
            "version": "2.0.0-beta.1",
            "plugin_name": "mindthus-beta",
            "surface": surface,
            "integrity": "ok",
            "carrier_status": "verified",
            "hook_state": hook_state,
            "stable_runtime_state": "disabled",
            "runtime_isolation_evidence": "observed",
            "host_plugin_observation": (
                "observed plugins=['mindthus@mindthus', "
                "'mindthus-beta@mindthus-beta', 'unrelated@example']"
            ),
            "runtime_isolation_status": "isolated-observed",
            "passive_kernel_status": passive,
            "direct_owner_status": "packaged-verified",
            "claim_ceiling": "fixture",
            "checks": [],
            "actions": [],
        }

    def _prepare_fixture_matrix(self) -> None:
        for case in self.cases:
            case_id = case["id"]
            surface = case["surface"]
            arm_id = case["arm_id"]
            case_root = self.root / "cases" / case_id
            host_home = case_root / "host-home"
            execution_parent = case_root / "workspace"
            execution_root = execution_parent / "project"
            execution_root.mkdir(parents=True)
            host_home.mkdir(parents=True)
            host_agents = host_home / "AGENTS.md"
            workspace_agents = execution_parent / "AGENTS.md"
            host_agents.write_text(f"Host policy for {case_id}.\n", encoding="utf-8")
            workspace_agents.write_text(f"Workspace policy for {case_id}.\n", encoding="utf-8")
            config = host_home / ("config.toml" if surface == "codex-plugin" else "settings.json")
            config.write_text(f"host = {case_id!r}\n", encoding="utf-8")

            plugin_list = case_root / "evidence" / "plugin-list.json"
            self._write_json(plugin_list, self._plugin_list(surface, arm_id))
            diagnostic: Path | None = None
            if arm_id != "stable":
                diagnostic = case_root / "evidence" / "runtime-diagnostic.json"
                self._write_json(diagnostic, self._runtime_diagnostic(surface, arm_id))

            package_kind = "stable" if arm_id == "stable" else "beta"
            plugin_root = self._make_package(surface, package_kind)
            spec = {
                "schema_version": "mindthus-beta2-arm-spec-v0.1",
                "arm_id": arm_id,
                "surface": surface,
                "plugin_root": str(plugin_root),
                "host_home": str(host_home),
                "execution_root": str(execution_root),
                "host_runtime": {
                    "name": "fixture-host",
                    "version": "fixture-host-1.0",
                    "platform": "fixture-platform",
                },
                "host_cli": {
                    "name": "codex" if surface == "codex-plugin" else "claude",
                    "version": "fixture-cli-1.0",
                },
                "host_config_files": [str(config)],
                "plugin_list_evidence": str(plugin_list),
                "runtime_diagnostic_evidence": str(diagnostic) if diagnostic else None,
                "hook_state": (
                    "not-applicable"
                    if arm_id == "stable"
                    else "disabled"
                    if arm_id == "direct-only"
                    else "fired"
                ),
                "model": {"id": "fixture-model", "reasoning": "fixture-reasoning"},
                "tools": ["read", "shell"],
                "ambient_context_files": [
                    {"kind": "agents-file", "id": "host-agents", "path": str(host_agents)},
                    {
                        "kind": "agents-file",
                        "id": "workspace-agents",
                        "path": str(workspace_agents),
                    },
                ],
                "opaque_context": [
                    {
                        "kind": "system-context",
                        "id": "fixture-system-context",
                        "sha256": hashlib.sha256(b"fixture-system-context").hexdigest(),
                    }
                ],
            }
            spec_path = case_root / "arm-spec.json"
            manifest_path = case_root / "sealed-arm.json"
            self._write_json(spec_path, spec)
            self.specs[case_id] = spec_path
            self.manifests[case_id] = manifest_path
            self.hosts[case_id] = host_home
            self.case_files[case_id] = {
                "config": config,
                "host_agents": host_agents,
                "workspace_agents": workspace_agents,
                "plugin_list": plugin_list,
                **({"diagnostic": diagnostic} if diagnostic else {}),
            }

    def _seal_all(self) -> None:
        for case in self.cases:
            case_id = case["id"]
            result = self._run(
                "seal",
                "--spec",
                self.specs[case_id],
                "--out",
                self.manifests[case_id],
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_fixture_matrix_covers_and_verifies_all_arms_on_both_surfaces(self) -> None:
        observed = {(case["surface"], case["arm_id"]) for case in self.cases}
        self.assertEqual(
            observed,
            {
                (surface, arm)
                for surface in ("codex-plugin", "claude-plugin")
                for arm in ("stable", "direct-only", "thin-kernel")
            },
        )
        self._seal_all()
        result = self._run("verify-set", *self.manifests.values())
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "verified-set")

    def test_resealing_identical_arm_produces_the_same_identity_digest(self) -> None:
        case_id = "codex-thin-kernel"
        first = self._run("seal", "--spec", self.specs[case_id], "--out", self.manifests[case_id])
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        second_path = self.manifests[case_id].with_name("sealed-arm-second.json")
        second = self._run("seal", "--spec", self.specs[case_id], "--out", second_path)
        self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
        first_payload = json.loads(self.manifests[case_id].read_text(encoding="utf-8"))
        second_payload = json.loads(second_path.read_text(encoding="utf-8"))
        self.assertEqual(first_payload["identity_digest"], second_payload["identity_digest"])
        self.assertEqual(first_payload, second_payload)

    def test_changed_package_host_namespace_context_or_hook_evidence_fails_closed(self) -> None:
        self._seal_all()
        cases = [
            (
                "codex-stable",
                self.packages[("codex-plugin", "stable")] / "skills" / "example" / "SKILL.md",
                "\npackage drift\n",
            ),
            ("codex-stable", self.case_files["codex-stable"]["config"], "\nhost drift\n"),
            (
                "codex-stable",
                self.case_files["codex-stable"]["workspace_agents"],
                "\ncontext drift\n",
            ),
        ]
        for case_id, path, suffix in cases:
            with self.subTest(case_id=case_id, path=path.name):
                original = path.read_bytes()
                path.write_bytes(original + suffix.encode("utf-8"))
                failed = self._run("verify", self.manifests[case_id])
                self.assertEqual(failed.returncode, 2)
                path.write_bytes(original)
                repaired = self._run("verify", self.manifests[case_id])
                self.assertEqual(repaired.returncode, 0, repaired.stderr + repaired.stdout)

        plugin_list = self.case_files["codex-stable"]["plugin_list"]
        original_plugin_list = plugin_list.read_bytes()
        self._write_json(plugin_list, self._plugin_list("codex-plugin", "thin-kernel"))
        namespace_failed = self._run("verify", self.manifests["codex-stable"])
        self.assertEqual(namespace_failed.returncode, 2)
        plugin_list.write_bytes(original_plugin_list)

        diagnostic = self.case_files["codex-direct-only"]["diagnostic"]
        original_diagnostic = diagnostic.read_bytes()
        changed = json.loads(original_diagnostic)
        changed["hook_state"] = "fired"
        self._write_json(diagnostic, changed)
        hook_failed = self._run("verify", self.manifests["codex-direct-only"])
        self.assertEqual(hook_failed.returncode, 2)
        diagnostic.write_bytes(original_diagnostic)

    def test_undeclared_agents_context_is_rejected_before_sealing(self) -> None:
        case_id = "codex-stable"
        spec = json.loads(self.specs[case_id].read_text(encoding="utf-8"))
        spec["ambient_context_files"] = spec["ambient_context_files"][:1]
        self._write_json(self.specs[case_id], spec)
        result = self._run("seal", "--spec", self.specs[case_id], "--out", self.manifests[case_id])
        self.assertEqual(result.returncode, 2)
        self.assertIn("AGENTS context ledger mismatch", result.stderr)

    def test_complete_set_rejects_a_host_home_shared_across_arms(self) -> None:
        self._seal_all()
        thin_id = "codex-thin-kernel"
        direct_id = "codex-direct-only"
        spec = json.loads(self.specs[thin_id].read_text(encoding="utf-8"))
        spec["host_home"] = str(self.hosts[direct_id])
        spec["host_config_files"] = [str(self.case_files[direct_id]["config"])]
        spec["ambient_context_files"][0]["path"] = str(self.case_files[direct_id]["host_agents"])
        alternate_spec = self.specs[thin_id].with_name("shared-home-spec.json")
        alternate_manifest = self.manifests[thin_id].with_name("shared-home-manifest.json")
        self._write_json(alternate_spec, spec)
        sealed = self._run("seal", "--spec", alternate_spec, "--out", alternate_manifest)
        self.assertEqual(sealed.returncode, 0, sealed.stderr + sealed.stdout)
        result = self._run(
            "verify-set",
            self.manifests["codex-stable"],
            self.manifests[direct_id],
            alternate_manifest,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("host_home is shared", result.stderr)

    def test_manifest_schema_and_fixture_contract_are_versioned(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "mindthus-beta2-arm-manifest-v0.1",
        )
        self.assertEqual(matrix["schema_version"], "mindthus-beta2-arm-fixtures-v0.1")
        self.assertTrue(schema["additionalProperties"] is False)


if __name__ == "__main__":
    unittest.main()
