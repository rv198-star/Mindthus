#!/usr/bin/env python3
"""Build isolated, sealed, deterministic Beta.2 dry-run fixture homes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
SEALER = BETA_ROOT / "runtime" / "seal-arm-manifest.py"
PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.1.json"
PROTOCOL_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.1.lock.json"
CASE_MATRIX = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"
NEGATIVE_CATALOG = BETA_ROOT / "fixtures" / "dry-run-negative-cases.json"
OWNERS = ("using-mindthus", "3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")
DRY_RUN_CASE_IDS = (
    "b2-dev-owner-3l5s",
    "b2-dev-arbitrator-overlap",
    "b2-dev-multi-primitive",
    "b2-dev-near-normal-debugging",
    "b2-dev-evidence-first",
    "b2-dev-lifecycle-resume",
    "b2-dev-lifecycle-clear",
    "b2-dev-lifecycle-compact",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_package(root: Path, surface: str, kind: str) -> Path:
    package = root / "packages" / surface / kind
    name = "mindthus" if kind == "stable" else "mindthus-beta"
    version = "1.4.6" if kind == "stable" else "2.0.0-beta.1"
    namespace = "mindthus:" if kind == "stable" else "mindthus-beta:"
    if surface == "codex-plugin":
        write_json(
            package / ".codex-plugin" / "plugin.json",
            {
                "name": name,
                "version": version,
                "interface": {
                    "defaultPrompt": [
                        "Deterministic dry-run fixture; no model execution is permitted."
                    ]
                },
            },
        )
    else:
        write_json(
            package / ".claude-plugin" / "plugin.json",
            {"name": name, "version": version},
        )
    for owner in OWNERS:
        skill = package / "skills" / owner / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(
            f"---\nname: {owner}\n---\nDry-run coordinate {namespace}{owner}.\n",
            encoding="utf-8",
        )
    if kind == "beta":
        write_json(
            package / "hooks" / "hooks.json",
            {"hooks": {"SessionStart": [{"matcher": "startup|resume|clear|compact"}]}},
        )
        kernel = package / "runtime" / "passive-activation-kernel.md"
        kernel.parent.mkdir(parents=True, exist_ok=True)
        kernel.write_text(
            "Deterministic fixture Kernel. No semantic claim.\n",
            encoding="utf-8",
        )
    return package


def plugin_list(surface: str, arm_id: str) -> object:
    entries = [
        {
            "pluginId": "mindthus@mindthus",
            "name": "mindthus",
            "enabled": arm_id == "stable",
        },
        {
            "pluginId": "mindthus-beta@mindthus-beta",
            "name": "mindthus-beta",
            "enabled": arm_id != "stable",
        },
        {"pluginId": "unrelated@example", "name": "unrelated", "enabled": True},
    ]
    return {"installed": entries} if surface == "codex-plugin" else entries


def runtime_diagnostic(surface: str, arm_id: str) -> dict[str, Any]:
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
        "claim_ceiling": "deterministic fixture only",
        "checks": [],
        "actions": [],
    }


def seal(spec_path: Path, manifest_path: Path) -> None:
    result = subprocess.run(
        ["python3", str(SEALER), "seal", "--spec", str(spec_path), "--out", str(manifest_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def build(root: Path) -> Path:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    packages = {
        (surface, kind): make_package(root, surface, kind)
        for surface in ("codex-plugin", "claude-plugin")
        for kind in ("stable", "beta")
    }
    manifest_paths: list[Path] = []
    observations: list[dict[str, Any]] = []
    for surface in ("codex-plugin", "claude-plugin"):
        for arm_id in ("stable", "direct-only", "thin-kernel"):
            case_root = root / "arms" / surface / arm_id
            home = case_root / "source-home"
            execution_root = case_root / "workspace" / "project"
            home.mkdir(parents=True, exist_ok=True)
            execution_root.mkdir(parents=True, exist_ok=True)
            home_agents = home / "AGENTS.md"
            workspace_agents = execution_root.parent / "AGENTS.md"
            home_agents.write_text(f"Fixture host policy: {surface}/{arm_id}.\n", encoding="utf-8")
            workspace_agents.write_text(
                f"Fixture workspace policy: {surface}/{arm_id}.\n",
                encoding="utf-8",
            )
            config = home / ("config.toml" if surface == "codex-plugin" else "settings.json")
            if surface == "codex-plugin":
                config.write_text(
                    f"fixture = {json.dumps(f'{surface}/{arm_id}')}\n",
                    encoding="utf-8",
                )
            else:
                write_json(config, {"fixture": f"{surface}/{arm_id}"})

            evidence_root = case_root / "evidence"
            inventory = evidence_root / "plugin-list.json"
            write_json(inventory, plugin_list(surface, arm_id))
            diagnostic: Path | None = None
            if arm_id != "stable":
                diagnostic = evidence_root / "runtime-diagnostic.json"
                write_json(diagnostic, runtime_diagnostic(surface, arm_id))

            package_kind = "stable" if arm_id == "stable" else "beta"
            package = packages[(surface, package_kind)]
            hook_state = (
                "not-applicable"
                if arm_id == "stable"
                else "disabled"
                if arm_id == "direct-only"
                else "fired"
            )
            spec = {
                "schema_version": "mindthus-beta2-arm-spec-v0.1",
                "arm_id": arm_id,
                "surface": surface,
                "plugin_root": str(package),
                "host_home": str(home),
                "execution_root": str(execution_root),
                "host_runtime": {
                    "name": "deterministic-dry-run-host",
                    "version": "1.0",
                    "platform": f"fixture-{surface}",
                },
                "host_cli": {
                    "name": "codex" if surface == "codex-plugin" else "claude",
                    "version": "deterministic-fixture-1.0",
                },
                "host_config_files": [str(config)],
                "plugin_list_evidence": str(inventory),
                "runtime_diagnostic_evidence": str(diagnostic) if diagnostic else None,
                "hook_state": hook_state,
                "model": {"id": "deterministic-mock", "reasoning": "none"},
                "tools": ["deterministic-mock"],
                "ambient_context_files": [
                    {"kind": "agents-file", "id": "host-agents", "path": str(home_agents)},
                    {
                        "kind": "agents-file",
                        "id": "workspace-agents",
                        "path": str(workspace_agents),
                    },
                ],
                "opaque_context": [
                    {
                        "kind": "system-context",
                        "id": "deterministic-dry-run-context",
                        "sha256": hashlib.sha256(
                            f"{surface}/{arm_id}/system-context".encode("utf-8")
                        ).hexdigest(),
                    }
                ],
            }
            spec_path = case_root / "arm-spec.json"
            manifest_path = case_root / "sealed-arm.json"
            write_json(spec_path, spec)
            seal(spec_path, manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_paths.append(manifest_path)
            observations.append(
                {
                    "manifest_path": str(manifest_path),
                    "identity_digest": manifest["identity_digest"],
                    "active_mindthus_coordinates": manifest["host"]["plugin_list"][
                        "active_mindthus_coordinates"
                    ],
                    "hook_state": manifest["carrier"]["hook_state"],
                    "package_tree_sha256": manifest["package"]["tree_sha256"],
                    "ambient_context_sha256": canonical_sha256(manifest["ambient_context"]),
                    "resource_probe_path": manifest["package"]["manifest"]["path"],
                }
            )

    judge_home = root / "judge" / "home"
    judge_home.mkdir(parents=True, exist_ok=True)
    judge_environment = {
        "schema_version": "mindthus-beta2-dry-run-judge-environment-v0.1",
        "home": str(judge_home),
        "executor": "deterministic-mock-judge",
        "active_mindthus_coordinates": [],
        "superpowers_enabled": False,
        "plugin_inventory": ["unrelated@example"],
        "generator_home_access": False,
    }
    judge_environment["environment_digest"] = canonical_sha256(judge_environment)
    judge_path = root / "judge" / "judge-environment.json"
    write_json(judge_path, judge_environment)

    plan = {
        "schema_version": "mindthus-beta2-dry-run-plan-v0.1",
        "executor": "deterministic-mock-only",
        "model_execution_allowed": False,
        "protocol_path": str(PROTOCOL.resolve()),
        "protocol_sha256": sha256_file(PROTOCOL),
        "protocol_lock_path": str(PROTOCOL_LOCK.resolve()),
        "case_matrix_path": str(CASE_MATRIX.resolve()),
        "case_matrix_sha256": sha256_file(CASE_MATRIX),
        "arm_manifests": [str(path) for path in manifest_paths],
        "host_observations": observations,
        "judge_environment_path": str(judge_path),
        "judge_environment_sha256": sha256_file(judge_path),
        "dry_run_case_ids": list(DRY_RUN_CASE_IDS),
        "required_lifecycle_paths": ["startup", "resume", "clear", "compact"],
        "supported_surfaces": ["codex-plugin", "claude-plugin"],
        "negative_fixture_catalog": str(NEGATIVE_CATALOG.resolve()),
    }
    plan["plan_digest"] = canonical_sha256(plan)
    plan_path = root / "dry-run-plan.json"
    write_json(plan_path, plan)
    return plan_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan_path = build(args.root)
    except (OSError, json.JSONDecodeError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"dry-run fixture build failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "built", "plan": str(plan_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
