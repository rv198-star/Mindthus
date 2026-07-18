#!/usr/bin/env python3
"""Filesystem-enforced resource isolation for Beta.2 evaluation protocol v0.5.

The v0.4 runner inferred contamination from command strings after a model process had
already run.  v0.5 instead executes every generator and Judge process under a macOS
Sandbox profile.  User-data roots are denied by default and only the current process'
declared roots are reopened.  A positive/negative/symlink/parent-traversal probe binds
the exact profile digest before a semantic call may start.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
PYTHON = Path("/usr/bin/python3")
PROFILE_SCHEMA = "mindthus-beta2-filesystem-profile-v0.5"
RECEIPT_SCHEMA = "mindthus-beta2-filesystem-isolation-receipt-v0.5"


class IsolationError(RuntimeError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def write_atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _resolved(paths: Iterable[Path]) -> list[Path]:
    return sorted({path.expanduser().resolve() for path in paths}, key=str)


def _sbpl_string(path: Path) -> str:
    value = str(path)
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _ancestors(path: Path) -> list[Path]:
    current = path.resolve()
    parents: list[Path] = []
    while current.parent != current:
        current = current.parent
        parents.append(current)
    return parents


def build_profile(
    *,
    protected_roots: Sequence[Path],
    allowed_read_roots: Sequence[Path],
    allowed_write_roots: Sequence[Path],
    allowed_read_files: Sequence[Path] = (),
) -> tuple[str, dict[str, Any]]:
    """Return an SBPL profile and its canonical, pre-execution contract."""

    if platform.system() != "Darwin" or not SANDBOX_EXEC.is_file():
        raise IsolationError("v0.5 requires macOS /usr/bin/sandbox-exec")
    protected = _resolved(protected_roots)
    readable = _resolved(allowed_read_roots)
    writable = _resolved(allowed_write_roots)
    files = _resolved(allowed_read_files)
    if not protected:
        raise IsolationError("at least one protected user-data root is required")
    for allowed in [*readable, *writable]:
        if allowed in protected:
            raise IsolationError("an allowed root cannot equal a protected root")
        if any(root.is_relative_to(allowed) for root in protected):
            raise IsolationError("an allowed root cannot contain a protected root")

    metadata_ancestors = _resolved(
        ancestor
        for path in [*readable, *writable, *files]
        for ancestor in _ancestors(path)
    )
    lines = ["(version 1)", "(allow default)"]
    for root in protected:
        lines.append(f"(deny file-read* (subpath {_sbpl_string(root)}))")
        lines.append(f"(deny file-write* (subpath {_sbpl_string(root)}))")
    for ancestor in metadata_ancestors:
        lines.append(
            f"(allow file-read-metadata (literal {_sbpl_string(ancestor)}))"
        )
    for path in readable:
        lines.append(f"(allow file-read* (subpath {_sbpl_string(path)}))")
    for path in writable:
        lines.append(f"(allow file-read* (subpath {_sbpl_string(path)}))")
        lines.append(f"(allow file-write* (subpath {_sbpl_string(path)}))")
    for path in files:
        lines.append(f"(allow file-read* (literal {_sbpl_string(path)}))")
    profile = "\n".join(lines) + "\n"
    contract: dict[str, Any] = {
        "schema_version": PROFILE_SCHEMA,
        "enforcement": "macos-sandbox-exec",
        "sandbox_exec": str(SANDBOX_EXEC),
        "protected_roots": [str(path) for path in protected],
        "allowed_read_roots": [str(path) for path in readable],
        "allowed_write_roots": [str(path) for path in writable],
        "allowed_read_files": [str(path) for path in files],
        "metadata_only_ancestors": [str(path) for path in metadata_ancestors],
        "default_user_data_access": "denied",
        "system_and_network_policy": "host-default",
    }
    contract["contract_digest"] = canonical_sha256(contract)
    return profile, contract


def sandboxed_command(profile_path: Path, command: Sequence[str]) -> list[str]:
    return [str(SANDBOX_EXEC), "-f", str(profile_path.resolve()), *map(str, command)]


def _read_probe(
    *, profile_path: Path, target: str, cwd: Path
) -> dict[str, Any]:
    script = (
        "import pathlib,sys; "
        "p=pathlib.Path(sys.argv[1]); "
        "data=p.read_bytes(); "
        "print(len(data))"
    )
    result = subprocess.run(
        sandboxed_command(profile_path, [str(PYTHON), "-c", script, target]),
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    return {
        "target": target,
        "returncode": result.returncode,
        "stdout_sha256": hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode("utf-8")).hexdigest(),
        "denied": result.returncode != 0,
    }


def verify_profile(
    *,
    profile_path: Path,
    contract: Mapping[str, Any],
    receipt_path: Path,
    probe_root: Path,
    allowed_targets: Sequence[Path],
    forbidden_targets: Sequence[Path],
) -> dict[str, Any]:
    """Run native access probes and bind the result to the exact profile digest."""

    if not profile_path.is_file():
        raise IsolationError("sandbox profile is missing")
    allowed = _resolved(allowed_targets)
    forbidden = _resolved(forbidden_targets)
    if not allowed or not forbidden:
        raise IsolationError("positive and negative isolation probes are both required")
    probe_root = probe_root.resolve()
    probe_root.mkdir(parents=True, exist_ok=True)

    positive = [
        _read_probe(profile_path=profile_path, target=str(path), cwd=probe_root)
        for path in allowed
    ]
    negative = [
        _read_probe(profile_path=profile_path, target=str(path), cwd=probe_root)
        for path in forbidden
    ]

    traversal_target = forbidden[0]
    relative = os.path.relpath(traversal_target, probe_root)
    parent_traversal = _read_probe(
        profile_path=profile_path,
        target=relative,
        cwd=probe_root,
    )

    symlink_path = probe_root / ".v05-forbidden-symlink-probe"
    if symlink_path.exists() or symlink_path.is_symlink():
        symlink_path.unlink()
    symlink_path.symlink_to(traversal_target)
    try:
        symlink_escape = _read_probe(
            profile_path=profile_path,
            target=str(symlink_path),
            cwd=probe_root,
        )
    finally:
        symlink_path.unlink(missing_ok=True)

    passed = (
        all(not item["denied"] for item in positive)
        and all(item["denied"] for item in negative)
        and parent_traversal["denied"]
        and symlink_escape["denied"]
    )
    receipt: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA,
        "status": "pass" if passed else "fail",
        "profile_path": str(profile_path.resolve()),
        "profile_sha256": sha256_file(profile_path),
        "profile_contract_digest": contract.get("contract_digest"),
        "positive_probes": positive,
        "negative_probes": negative,
        "parent_traversal_probe": parent_traversal,
        "symlink_escape_probe": symlink_escape,
        "model_execution_performed": False,
        "semantic_output_generated": False,
    }
    receipt["receipt_digest"] = canonical_sha256(receipt)
    write_atomic_json(receipt_path, receipt)
    if not passed:
        raise IsolationError("filesystem isolation probe failed closed")
    return receipt


def prepare_verified_profile(
    *,
    profile_path: Path,
    receipt_path: Path,
    protected_roots: Sequence[Path],
    allowed_read_roots: Sequence[Path],
    allowed_write_roots: Sequence[Path],
    allowed_read_files: Sequence[Path],
    probe_root: Path,
    allowed_targets: Sequence[Path],
    forbidden_targets: Sequence[Path],
) -> dict[str, Any]:
    profile, contract = build_profile(
        protected_roots=protected_roots,
        allowed_read_roots=allowed_read_roots,
        allowed_write_roots=allowed_write_roots,
        allowed_read_files=allowed_read_files,
    )
    write_atomic_text(profile_path, profile)
    return verify_profile(
        profile_path=profile_path,
        contract=contract,
        receipt_path=receipt_path,
        probe_root=probe_root,
        allowed_targets=allowed_targets,
        forbidden_targets=forbidden_targets,
    )
