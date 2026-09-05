"""TPlan runtime identity and provenance inspection, independent of Mission mutation."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from tplan_errors import TplanError

RUNTIME_MANIFEST_SCHEMA_VERSION = "tplan.runtime_manifest.v0.1"
RUNTIME_FINGERPRINT_SCHEMA_VERSION = "tplan.runtime_fingerprint.v0.1"
RUNTIME_PROVENANCE_SCHEMA_VERSION = "tplan.runtime_provenance.v0.1"
RUNTIME_MANIFEST_RELATIVE_PATH = Path("resources/runtime-manifest.json")


def runtime_skill_root(anchor: str | Path = __file__) -> Path:
    resolved = Path(anchor).resolve()
    if resolved.is_dir():
        return resolved
    return resolved.parents[1]


def _runtime_manifest_path(skill_root: Path) -> Path:
    return skill_root / RUNTIME_MANIFEST_RELATIVE_PATH


def load_runtime_manifest(skill_root: Path | None = None) -> dict[str, Any]:
    root = (skill_root or runtime_skill_root()).resolve()
    path = _runtime_manifest_path(root)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TplanError(f"TPlan runtime manifest is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TplanError(f"TPlan runtime manifest is invalid JSON: {path}") from exc
    if not isinstance(manifest, dict):
        raise TplanError(f"TPlan runtime manifest must be an object: {path}")
    required = {
        "schema_version",
        "package_version",
        "source_id",
        "capability_versions",
        "capabilities",
        "required_scripts",
        "fingerprint_files",
    }
    if set(manifest) != required:
        missing = sorted(required - set(manifest))
        extra = sorted(set(manifest) - required)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unsupported " + ", ".join(extra))
        raise TplanError("TPlan runtime manifest fields invalid: " + "; ".join(details))
    if manifest.get("schema_version") != RUNTIME_MANIFEST_SCHEMA_VERSION:
        raise TplanError(
            f"TPlan runtime manifest schema must be {RUNTIME_MANIFEST_SCHEMA_VERSION}"
        )
    for field in ("package_version", "source_id"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            raise TplanError(f"TPlan runtime manifest {field} must be a non-empty string")
    capability_versions = manifest.get("capability_versions")
    if (
        not isinstance(capability_versions, dict)
        or not capability_versions
        or not all(
            isinstance(key, str)
            and key
            and isinstance(value, str)
            and value
            for key, value in capability_versions.items()
        )
    ):
        raise TplanError(
            "TPlan runtime manifest capability_versions must map names to versions"
        )
    for field in ("capabilities", "required_scripts", "fingerprint_files"):
        values = manifest.get(field)
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(value, str) and value for value in values)
            or len(values) != len(set(values))
        ):
            raise TplanError(
                f"TPlan runtime manifest {field} must be a non-empty unique string list"
            )
        if field != "capabilities" and any(
            Path(value).is_absolute() or ".." in Path(value).parts
            for value in values
        ):
            raise TplanError(
                f"TPlan runtime manifest {field} paths must stay under the skill root"
            )
    return manifest


def runtime_fingerprint(skill_root: Path | None = None) -> dict[str, Any]:
    root = (skill_root or runtime_skill_root()).resolve()
    manifest = load_runtime_manifest(root)
    missing_scripts = [
        relative
        for relative in manifest["required_scripts"]
        if not (root / relative).is_file()
    ]
    if missing_scripts:
        raise TplanError(
            "TPlan runtime required scripts are missing under "
            f"{root}: {', '.join(missing_scripts)}"
        )

    digest = hashlib.sha256()
    for relative in manifest["fingerprint_files"]:
        path = root / relative
        if not path.is_file():
            raise TplanError(f"TPlan runtime fingerprint file is missing: {path}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return {
        "schema_version": RUNTIME_FINGERPRINT_SCHEMA_VERSION,
        "package_version": manifest["package_version"],
        "source_id": manifest["source_id"],
        "skill_root": str(root),
        "script_root": str((root / "scripts").resolve()),
        "build_hash": "sha256:" + digest.hexdigest(),
        "capability_versions": dict(sorted(manifest["capability_versions"].items())),
        "capabilities": sorted(manifest["capabilities"]),
    }


def validate_runtime_fingerprint(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["runtime fingerprint must be an object"]
    required = {
        "schema_version",
        "package_version",
        "source_id",
        "skill_root",
        "script_root",
        "build_hash",
        "capability_versions",
        "capabilities",
    }
    errors: list[str] = []
    if set(value) != required:
        errors.append("runtime fingerprint fields are invalid")
    if value.get("schema_version") != RUNTIME_FINGERPRINT_SCHEMA_VERSION:
        errors.append(
            f"runtime fingerprint schema_version must be {RUNTIME_FINGERPRINT_SCHEMA_VERSION}"
        )
    for field in ("package_version", "source_id", "skill_root", "script_root"):
        if not isinstance(value.get(field), str) or not value[field]:
            errors.append(f"runtime fingerprint {field} must be a non-empty string")
    build_hash = value.get("build_hash")
    if not isinstance(build_hash, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", build_hash) is None:
        errors.append("runtime fingerprint build_hash must be a sha256 digest")
    capability_versions = value.get("capability_versions")
    if (
        not isinstance(capability_versions, dict)
        or not capability_versions
        or not all(
            isinstance(key, str)
            and key
            and isinstance(version, str)
            and version
            for key, version in capability_versions.items()
        )
    ):
        errors.append("runtime fingerprint capability_versions are invalid")
    capabilities = value.get("capabilities")
    if (
        not isinstance(capabilities, list)
        or not capabilities
        or not all(isinstance(item, str) and item for item in capabilities)
        or len(capabilities) != len(set(capabilities or []))
    ):
        errors.append("runtime fingerprint capabilities are invalid")
    return errors


def runtime_fingerprint_compatibility(
    recorded: Any,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current = current or runtime_fingerprint()
    recorded_errors = validate_runtime_fingerprint(recorded)
    current_errors = validate_runtime_fingerprint(current)
    if recorded_errors or current_errors:
        return {
            "status": "incompatible",
            "compatible": False,
            "differences": {
                "recorded_errors": recorded_errors,
                "current_errors": current_errors,
            },
        }
    identity_fields = (
        "package_version",
        "source_id",
        "build_hash",
        "capability_versions",
        "capabilities",
    )
    differences = {
        field: {"recorded": recorded[field], "current": current[field]}
        for field in identity_fields
        if recorded[field] != current[field]
    }
    if differences:
        return {
            "status": "incompatible",
            "compatible": False,
            "differences": differences,
        }
    relocated = any(
        recorded[field] != current[field] for field in ("skill_root", "script_root")
    )
    return {
        "status": "compatible_relocated" if relocated else "exact",
        "compatible": True,
        "differences": (
            {
                field: {"recorded": recorded[field], "current": current[field]}
                for field in ("skill_root", "script_root")
                if recorded[field] != current[field]
            }
            if relocated
            else {}
        ),
    }


def validate_runtime_provenance(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["runtime_provenance must be an object"]
    errors: list[str] = []
    if set(value) != {"schema_version", "origin", "fingerprint"}:
        errors.append("runtime_provenance fields are invalid")
    if value.get("schema_version") != RUNTIME_PROVENANCE_SCHEMA_VERSION:
        errors.append(
            f"runtime_provenance schema_version must be {RUNTIME_PROVENANCE_SCHEMA_VERSION}"
        )
    if value.get("origin") not in {"native", "legacy_adopted"}:
        errors.append("runtime_provenance origin must be native or legacy_adopted")
    errors.extend(validate_runtime_fingerprint(value.get("fingerprint")))
    return errors


def new_runtime_provenance(*, origin: str = "native") -> dict[str, Any]:
    if origin not in {"native", "legacy_adopted"}:
        raise TplanError("runtime provenance origin unsupported")
    return {
        "schema_version": RUNTIME_PROVENANCE_SCHEMA_VERSION,
        "origin": origin,
        "fingerprint": runtime_fingerprint(),
    }


def runtime_provenance_report(
    mission: dict[str, Any],
    *,
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current = current or runtime_fingerprint()
    provenance = mission.get("runtime_provenance")
    if provenance is None:
        return {
            "status": "legacy_unpinned",
            "severity": "warning",
            "compatible": None,
            "origin": None,
            "recorded": None,
            "current": current,
            "diagnostics": [
                {
                    "code": "runtime_provenance_missing",
                    "message": (
                        "Mission predates runtime provenance; the creating runtime "
                        "cannot be verified"
                    ),
                }
            ],
        }
    errors = validate_runtime_provenance(provenance)
    if errors:
        return {
            "status": "incompatible",
            "severity": "error",
            "compatible": False,
            "origin": provenance.get("origin") if isinstance(provenance, dict) else None,
            "recorded": (
                provenance.get("fingerprint") if isinstance(provenance, dict) else None
            ),
            "current": current,
            "diagnostics": [
                {
                    "code": "runtime_provenance_invalid",
                    "message": "; ".join(errors),
                }
            ],
        }
    compatibility = runtime_fingerprint_compatibility(
        provenance["fingerprint"],
        current,
    )
    diagnostics: list[dict[str, str]] = []
    severity = "ok"
    if compatibility["status"] == "compatible_relocated":
        severity = "warning"
        diagnostics.append(
            {
                "code": "runtime_path_relocated",
                "message": (
                    "runtime content is compatible but the selected canonical path "
                    "differs from the recorded path"
                ),
            }
        )
    elif not compatibility["compatible"]:
        severity = "error"
        diagnostics.append(
            {
                "code": "runtime_fingerprint_mismatch",
                "message": (
                    "selected TPlan runtime does not match the Mission runtime fingerprint"
                ),
            }
        )
    if provenance["origin"] == "legacy_adopted":
        if severity == "ok":
            severity = "warning"
        diagnostics.append(
            {
                "code": "runtime_legacy_adopted",
                "message": (
                    "Mission was first pinned by a later runtime; its original creator "
                    "remains unknown"
                ),
            }
        )
    return {
        "status": (
            "legacy_adopted_" + compatibility["status"]
            if provenance["origin"] == "legacy_adopted"
            else compatibility["status"]
        ),
        "severity": severity,
        "compatible": compatibility["compatible"],
        "origin": provenance["origin"],
        "recorded": provenance["fingerprint"],
        "current": current,
        "differences": compatibility["differences"],
        "diagnostics": diagnostics,
    }
