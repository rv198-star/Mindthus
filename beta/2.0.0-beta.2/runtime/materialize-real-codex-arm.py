#!/usr/bin/env python3
"""Materialize and seal one real Codex arm for authorized Beta.2 execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

RUNTIME_ROOT = Path(__file__).resolve().parent
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from probe_codex_hook import canonical_kernel_text, probe_hook


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
PACK_BUILDER = REPO_ROOT / "scripts" / "build-release-pack.py"
SEALER = BETA_ROOT / "runtime" / "seal-arm-manifest.py"
DEFAULT_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"


class MaterializationError(RuntimeError):
    pass


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


def write_atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_json(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    label: str,
) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise MaterializationError(f"{label} failed: {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise MaterializationError(f"{label} did not return JSON") from exc
    if not isinstance(payload, dict):
        raise MaterializationError(f"{label} returned a non-object")
    return payload


def discovered_agents_files(host_home: Path, execution_root: Path) -> list[Path]:
    discovered: set[Path] = set()
    home_agents = host_home / "AGENTS.md"
    if home_agents.is_file():
        discovered.add(home_agents.resolve())
    current = execution_root.resolve()
    while True:
        candidate = current / "AGENTS.md"
        if candidate.is_file():
            discovered.add(candidate.resolve())
        parent = current.parent
        if parent == current:
            break
        current = parent
    return sorted(discovered, key=str)


def ambient_entries(host_home: Path, execution_root: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for path in discovered_agents_files(host_home, execution_root):
        entries.append(
            {
                "kind": "agents-file",
                "id": f"agents-{hashlib.sha256(str(path).encode()).hexdigest()[:12]}",
                "path": str(path),
            }
        )
    return entries


def _load_probe_receipt(path: Path, package_root: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise MaterializationError(f"{label} requires an observed host-hook receipt")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") not in {
        "mindthus-beta2-host-hook-observation-v0.1",
        "mindthus-beta2-host-hook-observation-v0.2",
    }:
        raise MaterializationError(f"{label} hook receipt schema differs")
    unsigned = dict(receipt)
    digest = unsigned.pop("receipt_digest", None)
    if digest != canonical_sha256(unsigned):
        raise MaterializationError(f"{label} hook receipt digest differs")
    if receipt.get("package_tree_sha256") != tree_sha256(package_root):
        raise MaterializationError(f"{label} hook receipt package digest differs")
    if receipt.get("schema_version") != "mindthus-beta2-host-hook-observation-v0.2":
        return receipt
    if receipt.get("model_execution_performed") is not False:
        raise MaterializationError(f"{label} hook probe called a model")
    if receipt.get("semantic_output_generated") is not False:
        raise MaterializationError(f"{label} hook probe generated semantic output")
    kernel_path = package_root / "runtime" / "passive-activation-kernel.md"
    if not kernel_path.is_file():
        raise MaterializationError(f"{label} package has no Passive Kernel")
    kernel = kernel_path.read_text(encoding="utf-8")
    raw_digest = hashlib.sha256(kernel.encode("utf-8")).hexdigest()
    canonical_digest = hashlib.sha256(
        canonical_kernel_text(kernel).encode("utf-8")
    ).hexdigest()
    if receipt.get("kernel_sha256") != raw_digest:
        raise MaterializationError(f"{label} hook receipt raw kernel digest differs")
    if receipt.get("kernel_canonical_sha256") != canonical_digest:
        raise MaterializationError(f"{label} hook receipt canonical digest differs")
    if receipt.get("network_scope") != "127.0.0.1-only model endpoint":
        raise MaterializationError(f"{label} hook probe left loopback scope")
    if receipt.get("request_content_retained") is not False:
        raise MaterializationError(f"{label} hook probe retained model request content")
    if int(receipt.get("matching_request_count") or 0) < 1:
        raise MaterializationError(f"{label} hook probe captured no matching request")
    return receipt


def validate_thin_receipt(path: Path, package_root: Path) -> dict[str, Any]:
    receipt = _load_probe_receipt(path, package_root, "thin-kernel")
    if receipt.get("status") != "observed-fired":
        raise MaterializationError("thin-kernel host hook was not observed firing")
    if receipt.get("schema_version") == "mindthus-beta2-host-hook-observation-v0.2":
        if (
            receipt.get("expected_kernel_state") != "present"
            or receipt.get("observed_kernel_state") != "present"
            or receipt.get("hook_trust_bypassed_for_vetted_package") is not True
            or receipt.get("captured_kernel_canonical_sha256")
            != receipt.get("kernel_canonical_sha256")
        ):
            raise MaterializationError("thin-kernel positive hook proof differs")
    return receipt


def validate_direct_absence_receipt(path: Path, package_root: Path) -> dict[str, Any]:
    receipt = _load_probe_receipt(path, package_root, "direct-only")
    if receipt.get("schema_version") != "mindthus-beta2-host-hook-observation-v0.2":
        raise MaterializationError("direct-only absence proof requires receipt v0.2")
    if (
        receipt.get("status") != "observed-absent"
        or receipt.get("expected_kernel_state") != "absent"
        or receipt.get("observed_kernel_state") != "absent"
        or receipt.get("hook_trust_bypassed_for_vetted_package") is not False
        or receipt.get("captured_kernel_canonical_sha256") is not None
    ):
        raise MaterializationError("direct-only negative hook proof differs")
    return receipt


def authorization_validator(path: Path) -> Path:
    packet = json.loads(path.read_text(encoding="utf-8"))
    relative = packet.get("authorization_validator_path")
    if not isinstance(relative, str) or not relative:
        raise MaterializationError("authorization validator path is missing")
    validator = (REPO_ROOT / relative).resolve()
    try:
        validator.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise MaterializationError("authorization validator leaves repository") from exc
    if not validator.is_file():
        raise MaterializationError("authorization validator is unavailable")
    return validator


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise MaterializationError(f"plugin tree contains a symlink: {relative}")
        if path.is_file():
            mode = stat.S_IMODE(path.stat().st_mode)
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(f"{mode:04o}".encode("ascii"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    execution_root = args.execution_root.resolve()
    if root.exists() and any(root.iterdir()):
        raise MaterializationError(f"arm root is not empty: {root}")
    if any((path / "AGENTS.md").is_file() for path in (execution_root, *execution_root.parents)):
        raise MaterializationError("execution root inherits an undeclared AGENTS.md")
    root.mkdir(parents=True, exist_ok=True)
    execution_root.mkdir(parents=True, exist_ok=True)

    authorization = run_json(
        [
            "python3",
            str(authorization_validator(args.authorization)),
            "--authorization",
            str(args.authorization),
        ],
        cwd=REPO_ROOT,
        label="execution authorization",
    )
    if authorization.get("status") != "authorized":
        raise MaterializationError("execution authorization is not active")

    release_line = "stable" if args.arm_id == "stable" else "2.0-beta.1"
    plugin_name = "mindthus" if args.arm_id == "stable" else "mindthus-beta"
    marketplace_name = plugin_name
    pack_root = execution_root.parent / "package"
    if pack_root.exists() and any(pack_root.iterdir()):
        raise MaterializationError(f"package output is not empty: {pack_root}")
    build = subprocess.run(
        [
            "python3",
            str(PACK_BUILDER),
            "--out",
            str(pack_root),
            "--package",
            "plugins",
            "--release-line",
            release_line,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if build.returncode != 0:
        raise MaterializationError(build.stderr.strip() or build.stdout.strip())
    marketplace = pack_root / "codex-plugin"

    host_home = root / "codex-home"
    process_home = root / "process-home"
    host_home.mkdir(parents=True, exist_ok=True)
    process_home.mkdir(parents=True, exist_ok=True)
    if not args.auth_source.is_file():
        raise MaterializationError("Codex auth source is unavailable")
    (host_home / "auth.json").symlink_to(args.auth_source.resolve())
    env = os.environ.copy()
    env["CODEX_HOME"] = str(host_home)
    env["HOME"] = str(process_home)

    run_json(
        ["codex", "plugin", "marketplace", "add", str(marketplace), "--json"],
        cwd=execution_root,
        env=env,
        label="marketplace installation",
    )
    install = run_json(
        ["codex", "plugin", "add", f"{plugin_name}@{marketplace_name}", "--json"],
        cwd=execution_root,
        env=env,
        label="plugin installation",
    )
    package_root = Path(str(install.get("installedPath") or "")).resolve()
    if not package_root.is_dir():
        raise MaterializationError("installed plugin package path is unavailable")

    inventory = run_json(
        ["codex", "plugin", "list", "--json"],
        cwd=execution_root,
        env=env,
        label="plugin inventory",
    )
    inventory_path = root / "evidence" / "plugin-list.json"
    write_atomic_json(inventory_path, inventory)

    prompt_probe = subprocess.run(
        ["codex", "debug", "prompt-input", "Beta.2 identity preflight only."],
        cwd=execution_root,
        env=env,
        text=True,
        capture_output=True,
    )
    if prompt_probe.returncode != 0:
        raise MaterializationError(
            "Codex prompt-input preflight failed: "
            f"{prompt_probe.stderr.strip() or prompt_probe.stdout.strip()}"
        )
    prompt_probe_path = root / "evidence" / "prompt-input.json"
    prompt_probe_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_probe_path.write_text(prompt_probe.stdout, encoding="utf-8")

    diagnostic_path: Path | None = None
    hook_state = "not-applicable"
    hook_receipt: dict[str, Any] | None = None
    hook_receipt_path: Path | None = None
    hook_absence_receipt: dict[str, Any] | None = None
    hook_absence_receipt_path: Path | None = None
    if args.arm_id != "stable":
        hook_state = "disabled" if args.arm_id == "direct-only" else "fired"
        if args.arm_id == "direct-only":
            hook_absence_receipt_path = (
                root / "evidence" / "hook-absence-observation.json"
            )
            observed = probe_hook(
                package_root=package_root,
                codex_home=host_home,
                process_home=process_home,
                execution_root=execution_root,
                expect_kernel=False,
                bypass_hook_trust=False,
            )
            write_atomic_json(hook_absence_receipt_path, observed)
            hook_absence_receipt = validate_direct_absence_receipt(
                hook_absence_receipt_path, package_root
            )
        else:
            if args.thin_hook_observed_receipt is not None:
                hook_receipt_path = args.thin_hook_observed_receipt.resolve()
            elif args.auto_probe_thin_hook:
                hook_receipt_path = root / "evidence" / "hook-observation.json"
                observed = probe_hook(
                    package_root=package_root,
                    codex_home=host_home,
                    process_home=process_home,
                    execution_root=execution_root,
                )
                write_atomic_json(hook_receipt_path, observed)
            else:
                raise MaterializationError(
                    "thin-kernel cannot be sealed before a host-hook observation receipt exists"
                )
            hook_receipt = validate_thin_receipt(
                hook_receipt_path, package_root
            )
        diagnostic_command = [
            "python3",
            str(package_root / "scripts" / "check-beta-runtime.py"),
            "--plugin-root",
            str(package_root),
            "--hook-state",
            hook_state,
            "--inspect-host",
            "--require-isolated",
            "--json",
        ]
        if args.arm_id == "thin-kernel":
            diagnostic_command.append("--require-passive")
        diagnostic = run_json(
            diagnostic_command,
            cwd=execution_root,
            env=env,
            label="Beta runtime diagnostic",
        )
        diagnostic_path = root / "evidence" / "runtime-diagnostic.json"
        write_atomic_json(diagnostic_path, diagnostic)

    spec = {
        "schema_version": "mindthus-beta2-arm-spec-v0.1",
        "arm_id": args.arm_id,
        "surface": "codex-plugin",
        "plugin_root": str(package_root),
        "host_home": str(host_home),
        "execution_root": str(execution_root),
        "host_runtime": {
            "name": "codex-cli",
            "version": "0.144.4",
            "platform": sys.platform,
        },
        "host_cli": {"name": "codex", "version": "0.144.4"},
        "host_config_files": [str(host_home / "config.toml")],
        "plugin_list_evidence": str(inventory_path),
        "runtime_diagnostic_evidence": (
            str(diagnostic_path) if diagnostic_path is not None else None
        ),
        "hook_state": hook_state,
        "model": {"id": "gpt-5.6-sol", "reasoning": "xhigh"},
        "tools": ["shell-read-only"],
        "ambient_context_files": ambient_entries(host_home, execution_root),
        "opaque_context": [
            {
                "kind": "codex-model-input-preflight",
                "id": "prompt-input",
                "sha256": sha256_file(prompt_probe_path),
            }
        ]
        + (
            [
                {
                    "kind": "host-hook-observation",
                    "id": "passive-kernel-session-start",
                    "sha256": str(hook_receipt["receipt_digest"]),
                }
            ]
            if hook_receipt
            else []
        )
        + (
            [
                {
                    "kind": "host-hook-absence-observation",
                    "id": "passive-kernel-session-start-disabled",
                    "sha256": str(hook_absence_receipt["receipt_digest"]),
                }
            ]
            if hook_absence_receipt
            else []
        ),
    }
    spec_path = root / "arm-spec.json"
    manifest_path = root / "sealed-arm.json"
    write_atomic_json(spec_path, spec)
    seal = subprocess.run(
        [
            "python3",
            str(SEALER),
            "seal",
            "--spec",
            str(spec_path),
            "--out",
            str(manifest_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if seal.returncode != 0:
        raise MaterializationError(seal.stderr.strip() or seal.stdout.strip())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    probe_receipt = hook_receipt or hook_absence_receipt
    if probe_receipt and manifest["package"]["tree_sha256"] != probe_receipt.get(
        "package_tree_sha256"
    ):
        raise MaterializationError(
            "sealed Beta package tree differs from the probed package tree"
        )
    return {
        "status": "materialized-and-sealed",
        "arm_id": args.arm_id,
        "manifest_path": str(manifest_path),
        "identity_digest": manifest["identity_digest"],
        "package_root": str(package_root),
        "host_home": str(host_home),
        "process_home": str(process_home),
        "execution_root": str(execution_root),
        "hook_observation_receipt": (
            hook_receipt.get("receipt_digest") if hook_receipt else None
        ),
        "hook_observation_receipt_path": (
            str(hook_receipt_path) if hook_receipt_path else None
        ),
        "hook_absence_receipt": (
            hook_absence_receipt.get("receipt_digest")
            if hook_absence_receipt
            else None
        ),
        "hook_absence_receipt_path": (
            str(hook_absence_receipt_path) if hook_absence_receipt_path else None
        ),
        "authorization_digest": authorization["authorization_digest"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execution-root", type=Path, required=True)
    parser.add_argument(
        "--arm-id", choices=("stable", "direct-only", "thin-kernel"), required=True
    )
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument(
        "--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json"
    )
    parser.add_argument("--thin-hook-observed-receipt", type=Path, default=None)
    parser.add_argument("--auto-probe-thin-hook", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = materialize(args)
        returncode = 0
    except (
        OSError,
        json.JSONDecodeError,
        MaterializationError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        returncode = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
