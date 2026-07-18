#!/usr/bin/env python3
"""Build platform-specific Mindthus release packs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


STABLE_VERSION = "1.4.6"
BETA_RELEASE_LINE = "2.0-beta.1"
NATIVE_THIN_ROUTER_RELEASE_LINE = "2.0-next-native-thin-router"
H1_OWNER_METADATA_RELEASE_LINE = "2.0-routing-h1-metadata"
RELEASE_LINES = (
    "stable",
    BETA_RELEASE_LINE,
    NATIVE_THIN_ROUTER_RELEASE_LINE,
    H1_OWNER_METADATA_RELEASE_LINE,
)
EXCLUDED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".tplan",
    ".tvg",
    "artifacts",
    "logs",
    "test",
    "tests",
}
EXCLUDED_SUFFIXES = {".gif", ".jpeg", ".jpg", ".log", ".mov", ".mp4", ".png", ".pyc", ".pyo", ".tmp", ".webp"}
EXCLUDED_NAME_SUBSTRINGS = ("ab_run", "pilot")
JSONL_ALLOWLIST = {Path("tplan/templates/evidence.jsonl")}
TEXT_REWRITE_SUFFIXES = {".md"}
SKILL_NAMES = ("3l5s", "sela", "mpg", "edsp", "wae", "tvg", "tplan", "using-mindthus")
LICENSE_FILES = ("LICENSE", "COMMERCIAL-LICENSE.md")
CODEX_PLUGIN_VISUAL_ASSETS = (
    Path("assets/mindthus-icon.svg"),
    Path("assets/mindthus-logo.svg"),
    Path("assets/mindthus-logo-dark.svg"),
)
RELEASE_SCRIPT_PATHS = (
    Path("run-fidelity-judge.py"),
    Path("log-fidelity-usage.py"),
    Path("log-mindthus-runtime.py"),
    Path("primitives/check.py"),
    Path("primitives/validate_whole_elephant.py"),
    Path("primitives/whole_elephant_validator.py"),
    Path("primitives/manifest.json"),
)
USING_MINDTHUS_CONDITIONAL_PRIMITIVES = (
    "frame-fitness-check.md",
    "entry-triage.md",
    "aspect-ownership.md",
    "decision-context-calibration.md",
    "whole-elephant-protocol.md",
    "expression-pressure-and-gates.md",
    "mpg-scalar-commitment-unpack.md",
)
CLAUDE_ACTIVATION_ROUTER_PROMPT = (
    "遇事不要慌，先搞清楚情况再说。This is a light Mindthus activation router, not a mandatory workflow. "
    "Use mindthus:using-mindthus only at hard judgment points: problem definition, structural ambiguity, "
    "strategic trend/local-advantage tradeoff, path-carrying risk, workflow/agent/evidence control boundary, "
    "thin artifact value, mission drift, or repeated local repair. Clear, low-risk, fact-sufficient tasks "
    "should be done directly; when facts, files, runtime behavior, or platform rules are missing, acquire "
    "evidence first. If an upstream brainstorming/design workflow such as Superpowers Brainstorm is active "
    "or clearly applicable, let it control design discovery and approval; Mindthus should not repeat "
    "brainstorming and should intervene only at remaining hard judgment points."
)
CODEX_ACTIVATION_ROUTER_PROMPT = (
    "Mindthus: hard frame/whole/binary/spiral/no-data -> mindthus:using-mindthus; "
    "method-ref review direct; direct; evidence 1st; defer Superpowers."
)
BETA_CODEX_STARTER_PROMPT = (
    "Route directly to mindthus-beta:<owner>; use mindthus-beta:using-mindthus only for "
    "genuine owner ambiguity."
)
NATIVE_THIN_ROUTER_CODEX_STARTER_PROMPT = "Apply the smallest sufficient Mindthus lens."


@dataclass(frozen=True)
class ReleaseProfile:
    release_line: str
    version: str
    using_skill_dir: Path
    supported_packages: tuple[str, ...]
    supported_surfaces: tuple[str, ...] = ("codex-plugin", "claude-plugin")
    carrier_mode: str = "stable"
    passive_kernel: Path | None = None
    profile_manifest: Path | None = None
    profile_data: dict | None = None
    beta_readme: Path | None = None
    runtime_diagnostic: Path | None = None
    reference_lock: Path | None = None
    reference_lock_data: dict | None = None
    plugin_name: str = "mindthus"
    marketplace_name: str = "mindthus"
    display_name: str = "Mindthus"
    budgets: dict[str, int] | None = None
    profile_guide_package_path: str = "BETA.md"
    runtime_diagnostic_package_path: str = "scripts/check-beta-runtime.py"
    default_prompt: str | None = None
    owner_description_overrides: dict[str, str] | None = None

    @property
    def experimental(self) -> bool:
        return self.release_line != "stable"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _safe_relative_path(value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise SystemExit(f"{label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"{label} must stay inside its declared root: {value}")
    return path


def _contract_tree_digest(source: Path, *, jsonl_allowlist: set[Path] | None = None) -> str:
    """Hash the deterministic, package-eligible contract surface under source."""

    jsonl_allowlist = jsonl_allowlist or set()
    digest = hashlib.sha256()
    for item in sorted(source.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(source)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        lowered = rel.as_posix().lower()
        if any(token in lowered for token in EXCLUDED_NAME_SUBSTRINGS):
            continue
        if item.suffix in EXCLUDED_SUFFIXES:
            continue
        if item.suffix == ".jsonl" and rel not in jsonl_allowlist:
            continue
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _verify_reference_lock(root: Path, lock_path: Path, *, baseline: str) -> dict:
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to load beta reference lock: {exc}") from exc

    if lock.get("schema_version") != "mindthus-reference-lock-v0.1":
        raise SystemExit("unsupported beta reference-lock schema")
    if lock.get("stable_baseline") != baseline:
        raise SystemExit("beta reference lock does not match the declared stable baseline")
    if lock.get("source_path_base") != "repository-root":
        raise SystemExit("beta reference source paths must be relative to repository-root")
    if lock.get("package_path_base") != "plugin-root":
        raise SystemExit("beta reference package paths must be relative to plugin-root")

    trees = lock.get("trees")
    files = lock.get("files")
    if not isinstance(trees, list) or not isinstance(files, list):
        raise SystemExit("beta reference lock must declare trees and files")

    for record in trees:
        if not isinstance(record, dict):
            raise SystemExit("beta reference tree record must be an object")
        source_rel = _safe_relative_path(record.get("source_path"), label="reference source_path")
        package_path = record.get("package_path")
        surface_paths = record.get("package_paths_by_surface")
        if package_path is not None:
            _safe_relative_path(package_path, label="reference package_path")
        elif isinstance(surface_paths, dict) and set(surface_paths) == {
            "codex-plugin",
            "claude-plugin",
        }:
            for surface, value in surface_paths.items():
                _safe_relative_path(value, label=f"reference package path for {surface}")
        else:
            raise SystemExit(
                f"reference tree {source_rel} must declare package_path or both surface paths"
            )
        source = root / source_rel
        if not source.is_dir():
            raise SystemExit(f"locked reference tree not found: {source_rel}")
        allowlist_raw = record.get("jsonl_allowlist", [])
        if not isinstance(allowlist_raw, list):
            raise SystemExit(f"jsonl_allowlist must be a list for {source_rel}")
        allowlist = {
            _safe_relative_path(value, label=f"jsonl allowlist for {source_rel}")
            for value in allowlist_raw
        }
        actual = _contract_tree_digest(source, jsonl_allowlist=allowlist)
        if actual != record.get("sha256"):
            raise SystemExit(
                f"frozen 1.4.6 reference drifted at {source_rel}: {actual} != {record.get('sha256')}"
            )

    for record in files:
        if not isinstance(record, dict):
            raise SystemExit("beta reference file record must be an object")
        source_rel = _safe_relative_path(record.get("source_path"), label="reference source_path")
        _safe_relative_path(record.get("package_path"), label="reference package_path")
        source = root / source_rel
        if not source.is_file():
            raise SystemExit(f"locked reference file not found: {source_rel}")
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != record.get("sha256"):
            raise SystemExit(
                f"frozen 1.4.6 reference drifted at {source_rel}: {actual} != {record.get('sha256')}"
            )
    return lock


def _enforce_text_budget(path: Path, *, max_bytes: int, max_words: int, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    byte_count = len(text.encode("utf-8"))
    word_count = len(text.split())
    if byte_count > max_bytes:
        raise SystemExit(f"{label} exceeds byte budget: {byte_count} > {max_bytes}")
    if word_count > max_words:
        raise SystemExit(f"{label} exceeds word budget: {word_count} > {max_words}")


def _parse_skill_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise SystemExit(f"skill frontmatter is missing at {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise SystemExit(f"skill frontmatter is not closed at {path}") from exc
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            raise SystemExit(f"invalid skill frontmatter line at {path}: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid quoted skill frontmatter at {path}: {exc}") from exc
        if key in data or not isinstance(value, str) or not value:
            raise SystemExit(f"invalid or duplicate skill frontmatter key at {path}: {key}")
        data[key] = value
    if set(data) != {"name", "description"}:
        raise SystemExit(f"skill frontmatter must contain only name and description at {path}")
    return data


def _load_native_thin_router_profile(root: Path) -> ReleaseProfile:
    profile_dir = root / "beta" / "2.0-next-native-thin-router"
    manifest_path = profile_dir / "release-profile.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to load native thin-router profile: {exc}") from exc

    if manifest.get("schema_version") != "mindthus-release-profile-v0.3":
        raise SystemExit("unsupported native thin-router release-profile schema")
    if manifest.get("release_line") != NATIVE_THIN_ROUTER_RELEASE_LINE:
        raise SystemExit("native thin-router profile declares the wrong release line")
    if manifest.get("version") != "2.0.0-next.1":
        raise SystemExit("native thin-router profile must use unpublished version 2.0.0-next.1")
    if manifest.get("path_base") != "plugin-root":
        raise SystemExit("native thin-router package paths must be relative to plugin-root")
    if manifest.get("carrier_mode") != "native-skill-description":
        raise SystemExit("native thin-router profile must use the native Skill description carrier")

    supported_packages = tuple(manifest.get("supported_packages", ()))
    supported_surfaces = tuple(manifest.get("supported_surfaces", ()))
    if supported_packages != ("plugins",):
        raise SystemExit("native thin-router profile must remain plugin-only")
    if supported_surfaces != ("codex-plugin",):
        raise SystemExit("native thin-router profile must remain Codex-only")

    identity = manifest.get("plugin_identity")
    if not isinstance(identity, dict):
        raise SystemExit("native thin-router profile must declare plugin_identity")
    plugin_name = identity.get("name")
    marketplace_name = identity.get("marketplace_name")
    display_name = identity.get("display_name")
    if plugin_name != "mindthus-beta" or marketplace_name != "mindthus-beta":
        raise SystemExit("native thin-router profile must stay isolated from Stable identity")
    if not isinstance(display_name, str) or not display_name:
        raise SystemExit("native thin-router display name must be non-empty")

    namespace_adapter = manifest.get("namespace_adapter")
    if (
        not isinstance(namespace_adapter, dict)
        or namespace_adapter.get("source_prefix") != "mindthus:"
        or namespace_adapter.get("runtime_prefix") != f"{plugin_name}:"
        or namespace_adapter.get("mode") != "package-time-coordinate-only"
    ):
        raise SystemExit("native thin-router profile has an invalid namespace adapter")

    using_skill_dir = profile_dir / str(manifest.get("using_mindthus_overlay", ""))
    using_skill = using_skill_dir / "SKILL.md"
    guide_source = profile_dir / str(manifest.get("profile_guide_source", ""))
    diagnostic_source = profile_dir / str(manifest.get("runtime_diagnostic_source", ""))
    reference_lock = profile_dir / str(manifest.get("reference_lock_source", ""))
    for label, path in (
        ("using-mindthus overlay", using_skill),
        ("profile guide", guide_source),
        ("runtime diagnostic", diagnostic_source),
        ("reference lock", reference_lock),
    ):
        if not path.is_file():
            raise SystemExit(f"native thin-router {label} not found: {path}")

    budgets = manifest.get("budgets")
    required_budgets = {
        "using_mindthus_max_bytes",
        "using_mindthus_max_words",
        "description_max_bytes",
        "default_prompt_max_bytes",
    }
    if not isinstance(budgets, dict) or not required_budgets.issubset(budgets):
        raise SystemExit("native thin-router profile is missing text budgets")
    _enforce_text_budget(
        using_skill,
        max_bytes=int(budgets["using_mindthus_max_bytes"]),
        max_words=int(budgets["using_mindthus_max_words"]),
        label="native thin using-mindthus",
    )
    frontmatter = _parse_skill_frontmatter(using_skill)
    if frontmatter["name"] != "using-mindthus":
        raise SystemExit("native thin entry must keep the using-mindthus name")
    description_bytes = len(frontmatter["description"].encode("utf-8"))
    if description_bytes > int(budgets["description_max_bytes"]):
        raise SystemExit(
            f"native thin description exceeds byte budget: "
            f"{description_bytes} > {budgets['description_max_bytes']}"
        )
    default_prompt = manifest.get("default_prompt")
    if not isinstance(default_prompt, str) or not default_prompt:
        raise SystemExit("native thin-router profile must declare one neutral default prompt")
    default_prompt_bytes = len(default_prompt.encode("utf-8"))
    if default_prompt_bytes > int(budgets["default_prompt_max_bytes"]):
        raise SystemExit(
            f"native thin default prompt exceeds byte budget: "
            f"{default_prompt_bytes} > {budgets['default_prompt_max_bytes']}"
        )

    reference_lock_data = _verify_reference_lock(
        root,
        reference_lock,
        baseline=str(manifest.get("stable_baseline", "")),
    )
    artifact_sources = {
        str(manifest.get("profile_guide", "")): guide_source,
        str(manifest.get("reference_lock", "")): reference_lock,
        str(manifest.get("runtime_diagnostic", "")): diagnostic_source,
        f"{manifest.get('using_mindthus_overlay', '')}/SKILL.md": using_skill,
    }
    artifact_hashes = manifest.get("artifact_sha256")
    if not isinstance(artifact_hashes, dict) or set(artifact_hashes) != set(artifact_sources):
        raise SystemExit("native thin artifact_sha256 must lock every authored runtime artifact")
    for package_path, source in artifact_sources.items():
        _safe_relative_path(package_path, label="native thin artifact path")
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != artifact_hashes.get(package_path):
            raise SystemExit(
                f"native thin runtime artifact drifted at {package_path}: "
                f"{actual} != {artifact_hashes.get(package_path)}"
            )
    generated = manifest.get("generated_artifact_sha256")
    if not isinstance(generated, dict) or set(generated) != {"codex-plugin"}:
        raise SystemExit("native thin profile must lock only Codex generated artifacts")

    return ReleaseProfile(
        release_line=NATIVE_THIN_ROUTER_RELEASE_LINE,
        version="2.0.0-next.1",
        using_skill_dir=using_skill_dir,
        supported_packages=supported_packages,
        supported_surfaces=supported_surfaces,
        carrier_mode="native-skill-description",
        profile_manifest=manifest_path,
        profile_data=manifest,
        beta_readme=guide_source,
        runtime_diagnostic=diagnostic_source,
        reference_lock=reference_lock,
        reference_lock_data=reference_lock_data,
        plugin_name=str(plugin_name),
        marketplace_name=str(marketplace_name),
        display_name=display_name,
        budgets={key: int(value) for key, value in budgets.items()},
        profile_guide_package_path=str(manifest.get("profile_guide", "")),
        runtime_diagnostic_package_path=str(manifest.get("runtime_diagnostic", "")),
        default_prompt=default_prompt,
    )


def _load_h1_owner_metadata_profile(root: Path) -> ReleaseProfile:
    profile_dir = root / "beta" / "2.0-routing-convergence" / "h1-owner-metadata"
    manifest_path = profile_dir / "release-profile.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to load H1 owner-metadata profile: {exc}") from exc

    if manifest.get("schema_version") != "mindthus-release-profile-v0.4":
        raise SystemExit("unsupported H1 owner-metadata release-profile schema")
    if manifest.get("release_line") != H1_OWNER_METADATA_RELEASE_LINE:
        raise SystemExit("H1 owner-metadata profile declares the wrong release line")
    if manifest.get("version") != "2.0.0-next.2":
        raise SystemExit("H1 owner-metadata profile must use unpublished version 2.0.0-next.2")
    if manifest.get("path_base") != "plugin-root":
        raise SystemExit("H1 package paths must be relative to plugin-root")
    if manifest.get("carrier_mode") != "native-skill-description":
        raise SystemExit("H1 must use only the native Skill-description carrier")
    if tuple(manifest.get("supported_packages", ())) != ("plugins",):
        raise SystemExit("H1 must remain plugin-only")
    if tuple(manifest.get("supported_surfaces", ())) != ("codex-plugin",):
        raise SystemExit("H1 must remain Codex-only")

    identity = manifest.get("plugin_identity")
    if not isinstance(identity, dict):
        raise SystemExit("H1 must declare plugin_identity")
    plugin_name = identity.get("name")
    marketplace_name = identity.get("marketplace_name")
    display_name = identity.get("display_name")
    if plugin_name != "mindthus-beta" or marketplace_name != "mindthus-beta":
        raise SystemExit("H1 must stay isolated from Stable identity")
    if not isinstance(display_name, str) or not display_name:
        raise SystemExit("H1 display name must be non-empty")

    adapter = manifest.get("namespace_adapter")
    if (
        not isinstance(adapter, dict)
        or adapter.get("source_prefix") != "mindthus:"
        or adapter.get("runtime_prefix") != "mindthus-beta:"
        or adapter.get("mode") != "package-time-coordinate-only"
    ):
        raise SystemExit("H1 has an invalid namespace adapter")

    source_paths = manifest.get("source_paths")
    if not isinstance(source_paths, dict):
        raise SystemExit("H1 must declare source_paths")
    using_skill_dir = root / _safe_relative_path(
        source_paths.get("using_mindthus_overlay"), label="H1 using-mindthus source"
    )
    guide_source = profile_dir / "STATUS.md"
    diagnostic_source = profile_dir / "runtime" / "check-h1-metadata.py"
    reference_lock = root / _safe_relative_path(
        source_paths.get("reference_lock"), label="H1 reference-lock source"
    )
    for label, path in (
        ("using-mindthus overlay", using_skill_dir / "SKILL.md"),
        ("profile guide", guide_source),
        ("runtime diagnostic", diagnostic_source),
        ("reference lock", reference_lock),
    ):
        if not path.is_file():
            raise SystemExit(f"H1 {label} not found: {path}")

    overrides = manifest.get("owner_description_overrides")
    if not isinstance(overrides, dict) or set(overrides) != {"3l5s", "mpg", "wae"}:
        raise SystemExit("H1 correction must override exactly the 3L5S, MPG, and WAE descriptions")
    if not all(isinstance(value, str) and value for value in overrides.values()):
        raise SystemExit("H1 owner-description overrides must be non-empty strings")

    budgets = manifest.get("budgets")
    required_budgets = {
        "using_mindthus_max_bytes",
        "using_mindthus_max_words",
        "description_max_bytes",
        "owner_description_max_bytes",
        "default_prompt_max_bytes",
    }
    if not isinstance(budgets, dict) or not required_budgets.issubset(budgets):
        raise SystemExit("H1 profile is missing text budgets")
    using_skill = using_skill_dir / "SKILL.md"
    _enforce_text_budget(
        using_skill,
        max_bytes=int(budgets["using_mindthus_max_bytes"]),
        max_words=int(budgets["using_mindthus_max_words"]),
        label="H1 thin using-mindthus",
    )
    frontmatter = _parse_skill_frontmatter(using_skill)
    if frontmatter["name"] != "using-mindthus":
        raise SystemExit("H1 thin entry must keep the using-mindthus name")
    if len(frontmatter["description"].encode("utf-8")) > int(budgets["description_max_bytes"]):
        raise SystemExit("H1 thin-entry description exceeds its byte budget")
    for owner, description in overrides.items():
        if len(description.encode("utf-8")) > int(budgets["owner_description_max_bytes"]):
            raise SystemExit(f"H1 {owner} description exceeds its byte budget")

    default_prompt = manifest.get("default_prompt")
    if not isinstance(default_prompt, str) or not default_prompt:
        raise SystemExit("H1 must declare one neutral default prompt")
    if len(default_prompt.encode("utf-8")) > int(budgets["default_prompt_max_bytes"]):
        raise SystemExit("H1 default prompt exceeds its byte budget")

    reference_lock_data = _verify_reference_lock(
        root, reference_lock, baseline=str(manifest.get("stable_baseline", ""))
    )
    artifact_sources = {
        str(manifest.get("profile_guide")): guide_source,
        str(manifest.get("reference_lock")): reference_lock,
        str(manifest.get("runtime_diagnostic")): diagnostic_source,
        "skills/using-mindthus/SKILL.md": using_skill,
    }
    artifact_hashes = manifest.get("artifact_sha256")
    if not isinstance(artifact_hashes, dict) or set(artifact_hashes) != set(artifact_sources):
        raise SystemExit("H1 artifact_sha256 must lock every authored active artifact")
    for package_path, source in artifact_sources.items():
        _safe_relative_path(package_path, label="H1 artifact path")
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != artifact_hashes.get(package_path):
            raise SystemExit(
                f"H1 runtime artifact drifted at {package_path}: "
                f"{actual} != {artifact_hashes.get(package_path)}"
            )
    generated = manifest.get("generated_artifact_sha256")
    if not isinstance(generated, dict) or set(generated) != {"codex-plugin"}:
        raise SystemExit("H1 must lock only Codex generated artifacts")

    return ReleaseProfile(
        release_line=H1_OWNER_METADATA_RELEASE_LINE,
        version="2.0.0-next.2",
        using_skill_dir=using_skill_dir,
        supported_packages=("plugins",),
        supported_surfaces=("codex-plugin",),
        carrier_mode="native-skill-description",
        profile_manifest=manifest_path,
        profile_data=manifest,
        beta_readme=guide_source,
        runtime_diagnostic=diagnostic_source,
        reference_lock=reference_lock,
        reference_lock_data=reference_lock_data,
        plugin_name=str(plugin_name),
        marketplace_name=str(marketplace_name),
        display_name=display_name,
        budgets={key: int(value) for key, value in budgets.items()},
        profile_guide_package_path=str(manifest.get("profile_guide")),
        runtime_diagnostic_package_path=str(manifest.get("runtime_diagnostic")),
        default_prompt=default_prompt,
        owner_description_overrides={str(key): str(value) for key, value in overrides.items()},
    )


def load_release_profile(root: Path, release_line: str) -> ReleaseProfile:
    if release_line == "stable":
        return ReleaseProfile(
            release_line="stable",
            version=STABLE_VERSION,
            using_skill_dir=root / "skills" / "using-mindthus",
            supported_packages=("all", "plugins", "skills"),
        )

    if release_line == NATIVE_THIN_ROUTER_RELEASE_LINE:
        return _load_native_thin_router_profile(root)

    if release_line == H1_OWNER_METADATA_RELEASE_LINE:
        return _load_h1_owner_metadata_profile(root)

    profile_dir = root / "beta" / "2.0.0-beta.1"
    manifest_path = profile_dir / "release-profile.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to load beta release profile: {exc}") from exc

    if manifest.get("release_line") != release_line:
        raise SystemExit(f"beta release profile must declare release_line {release_line!r}")
    if manifest.get("schema_version") != "mindthus-release-profile-v0.2":
        raise SystemExit("unsupported beta release-profile schema")
    if manifest.get("version") != "2.0.0-beta.1":
        raise SystemExit("2.0-beta.1 release line must build version 2.0.0-beta.1")
    if manifest.get("path_base") != "plugin-root":
        raise SystemExit("2.0.0-beta.1 package paths must be relative to plugin-root")

    using_skill_dir = profile_dir / str(manifest.get("using_mindthus_overlay", ""))
    passive_kernel = profile_dir / str(manifest.get("passive_kernel", ""))
    beta_readme = profile_dir / "BETA.md"
    runtime_diagnostic = profile_dir / "runtime" / "check-beta-runtime.py"
    reference_lock = profile_dir / "reference-lock.json"
    supported_packages = tuple(manifest.get("supported_packages", ()))
    budgets = manifest.get("budgets", {})
    if not (using_skill_dir / "SKILL.md").is_file():
        raise SystemExit(f"beta using-mindthus overlay not found: {using_skill_dir}")
    if not passive_kernel.is_file():
        raise SystemExit(f"beta passive kernel not found: {passive_kernel}")
    if not beta_readme.is_file():
        raise SystemExit(f"beta onboarding guide not found: {beta_readme}")
    if not runtime_diagnostic.is_file():
        raise SystemExit(f"beta runtime diagnostic not found: {runtime_diagnostic}")
    if supported_packages != ("plugins",):
        raise SystemExit("2.0.0-beta.1 must remain plugin-only until skills-only carriers are verified")

    identity = manifest.get("plugin_identity")
    if not isinstance(identity, dict):
        raise SystemExit("beta release profile must declare plugin_identity")
    plugin_name = identity.get("name")
    marketplace_name = identity.get("marketplace_name")
    display_name = identity.get("display_name")
    if plugin_name != "mindthus-beta" or marketplace_name != "mindthus-beta":
        raise SystemExit("2.0.0-beta.1 must use an identity distinct from stable mindthus")
    if not isinstance(display_name, str) or not display_name:
        raise SystemExit("beta plugin_identity.display_name must be non-empty")

    namespace_adapter = manifest.get("namespace_adapter")
    if (
        not isinstance(namespace_adapter, dict)
        or namespace_adapter.get("source_prefix") != "mindthus:"
        or namespace_adapter.get("runtime_prefix") != f"{plugin_name}:"
        or namespace_adapter.get("mode") != "package-time-coordinate-only"
    ):
        raise SystemExit("2.0.0-beta.1 must declare its coordinate-only namespace adapter")

    reference_lock_data = _verify_reference_lock(
        root,
        reference_lock,
        baseline=str(manifest.get("stable_baseline", "")),
    )

    required_budgets = {
        "kernel_max_bytes",
        "kernel_max_words",
        "using_mindthus_max_bytes",
        "using_mindthus_max_words",
    }
    if not isinstance(budgets, dict) or not required_budgets.issubset(budgets):
        raise SystemExit("beta release profile is missing text budgets")
    _enforce_text_budget(
        passive_kernel,
        max_bytes=int(budgets["kernel_max_bytes"]),
        max_words=int(budgets["kernel_max_words"]),
        label="passive activation kernel",
    )
    _enforce_text_budget(
        using_skill_dir / "SKILL.md",
        max_bytes=int(budgets["using_mindthus_max_bytes"]),
        max_words=int(budgets["using_mindthus_max_words"]),
        label="beta using-mindthus",
    )

    artifact_sources = {
        str(manifest.get("passive_kernel", "")): passive_kernel,
        f"{manifest.get('using_mindthus_overlay', '')}/SKILL.md": using_skill_dir / "SKILL.md",
        str(manifest.get("runtime_diagnostic", "")): runtime_diagnostic,
        str(manifest.get("beta_readme", "")): beta_readme,
        str(manifest.get("reference_lock", "")): reference_lock,
    }
    artifact_hashes = manifest.get("artifact_sha256")
    if not isinstance(artifact_hashes, dict) or set(artifact_hashes) != set(artifact_sources):
        raise SystemExit("beta release profile artifact_sha256 must lock every authored beta artifact")
    for package_path, source in artifact_sources.items():
        _safe_relative_path(package_path, label="beta artifact path")
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != artifact_hashes.get(package_path):
            raise SystemExit(
                f"beta runtime artifact drifted at {package_path}: "
                f"{actual} != {artifact_hashes.get(package_path)}"
            )

    return ReleaseProfile(
        release_line=release_line,
        version=str(manifest.get("version", "")),
        using_skill_dir=using_skill_dir,
        supported_packages=supported_packages,
        supported_surfaces=("codex-plugin", "claude-plugin"),
        carrier_mode="session-start-kernel",
        passive_kernel=passive_kernel,
        profile_manifest=manifest_path,
        profile_data=manifest,
        beta_readme=beta_readme,
        runtime_diagnostic=runtime_diagnostic,
        reference_lock=reference_lock,
        reference_lock_data=reference_lock_data,
        plugin_name=str(plugin_name),
        marketplace_name=str(marketplace_name),
        display_name=display_name,
        budgets={key: int(value) for key, value in budgets.items()},
        profile_guide_package_path="BETA.md",
        runtime_diagnostic_package_path=str(manifest.get("runtime_diagnostic", "")),
        default_prompt=BETA_CODEX_STARTER_PROMPT,
    )


def ensure_output_dir(path: Path, force: bool) -> None:
    if path.exists() and not path.is_dir():
        raise SystemExit(f"output path exists and is not a directory: {path}")
    if path.exists():
        if any(path.iterdir()):
            if not force:
                raise SystemExit(f"output directory is not empty: {path}")
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def ensure_safe_output_dir(path: Path, root: Path) -> None:
    protected_sources = [
        root,
        root / "skills",
        root / "docs",
        root / "scripts",
        root / "tests",
        root / ".git",
    ]
    if len(path.parts) <= 2:
        raise SystemExit(f"refusing broad output directory: {path}")
    if path in root.parents:
        raise SystemExit(f"refusing repository parent output directory: {path}")
    if any(path == protected or protected in path.parents for protected in protected_sources):
        raise SystemExit(f"refusing output directory inside protected source tree: {path}")


def rewrite_text(text: str, replacements: dict[str, str]) -> str:
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def copy_file_filtered(source: Path, target: Path, replacements: dict[str, str] | None = None) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if replacements and source.suffix in TEXT_REWRITE_SUFFIXES:
        text = source.read_text(encoding="utf-8")
        target.write_text(rewrite_text(text, replacements), encoding="utf-8")
        return
    shutil.copy2(source, target)


def copy_tree_filtered(
    source: Path,
    target: Path,
    replacements: dict[str, str] | None = None,
    binary_asset_allowlist: set[Path] | None = None,
    jsonl_allowlist: set[Path] | None = None,
) -> None:
    binary_asset_allowlist = binary_asset_allowlist or set()
    jsonl_allowlist = JSONL_ALLOWLIST if jsonl_allowlist is None else jsonl_allowlist
    for item in sorted(source.rglob("*")):
        rel = item.relative_to(source)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        lowered = rel.as_posix().lower()
        if any(token in lowered for token in EXCLUDED_NAME_SUBSTRINGS):
            continue
        dest = target / rel
        if item.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        if item.suffix in EXCLUDED_SUFFIXES and rel not in binary_asset_allowlist:
            continue
        if item.suffix == ".jsonl" and rel not in jsonl_allowlist:
            continue
        copy_file_filtered(item, dest, replacements)


def skill_path_replacements(platform_skill_root: str) -> dict[str, str]:
    return {f"skills/{name}/": f"{platform_skill_root}/{name}/" for name in SKILL_NAMES}


def profile_skill_replacements(
    profile: ReleaseProfile,
    replacements: dict[str, str] | None = None,
) -> dict[str, str] | None:
    merged = dict(replacements or {})
    if profile.experimental:
        assert profile.profile_data is not None
        adapter = profile.profile_data["namespace_adapter"]
        merged[str(adapter["source_prefix"])] = str(adapter["runtime_prefix"])
    return merged or None


def apply_owner_description_override(path: Path, description: str) -> None:
    """Replace only a built Skill's description while preserving its body bytes."""

    payload = path.read_bytes()
    marker = b"---\n"
    if not payload.startswith(marker):
        raise SystemExit(f"cannot override description without Skill frontmatter: {path}")
    end = payload.find(marker, len(marker))
    if end < 0:
        raise SystemExit(f"cannot find Skill frontmatter end for description override: {path}")
    body = payload[end + len(marker) :]
    frontmatter = _parse_skill_frontmatter(path)
    encoded = (
        "---\n"
        f"name: {frontmatter['name']}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "---\n"
    ).encode("utf-8")
    path.write_bytes(encoded + body)


def apply_profile_owner_override(profile: ReleaseProfile, skill_name: str, target: Path) -> None:
    overrides = profile.owner_description_overrides or {}
    description = overrides.get(skill_name)
    if description is not None:
        apply_owner_description_override(target / "SKILL.md", description)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_license_files(root: Path, target: Path) -> None:
    for filename in LICENSE_FILES:
        copy_file_filtered(root / filename, target / filename)


def copy_codex_plugin_visual_assets(repo: Path, plugin_root: Path) -> None:
    for rel_path in CODEX_PLUGIN_VISUAL_ASSETS:
        copy_file_filtered(repo / rel_path, plugin_root / rel_path)


def copy_release_scripts(root: Path, target: Path) -> None:
    for rel_path in RELEASE_SCRIPT_PATHS:
        copy_file_filtered(root / "scripts" / rel_path, target / "scripts" / rel_path)


def copy_locked_reference_material(root: Path, target: Path, profile: ReleaseProfile) -> None:
    assert profile.reference_lock_data is not None
    for record in profile.reference_lock_data["trees"]:
        source_rel = _safe_relative_path(record["source_path"], label="reference source_path")
        package_path = record.get("package_path")
        if package_path is None:
            continue
        package_rel = _safe_relative_path(package_path, label="reference package_path")
        if not package_rel.parts or package_rel.parts[0] != "reference":
            continue
        allowlist = {
            _safe_relative_path(value, label=f"jsonl allowlist for {source_rel}")
            for value in record.get("jsonl_allowlist", [])
        }
        copy_tree_filtered(
            root / source_rel,
            target / package_rel,
            jsonl_allowlist=allowlist,
        )
    for record in profile.reference_lock_data["files"]:
        source_rel = _safe_relative_path(record["source_path"], label="reference source_path")
        package_rel = _safe_relative_path(record["package_path"], label="reference package_path")
        copy_file_filtered(root / source_rel, target / package_rel)


def copy_skills_for_profile(
    skills_dir: Path,
    target: Path,
    profile: ReleaseProfile,
    replacements: dict[str, str] | None = None,
) -> None:
    active_replacements = profile_skill_replacements(profile, replacements)
    copy_tree_filtered(skills_dir, target, active_replacements)
    for skill_name in profile.owner_description_overrides or {}:
        apply_profile_owner_override(profile, skill_name, target / skill_name)
    if not profile.experimental:
        return
    using_target = target / "using-mindthus"
    if using_target.exists():
        shutil.rmtree(using_target)
    copy_tree_filtered(profile.using_skill_dir, using_target, active_replacements)


def copy_profile_runtime(root: Path, profile: ReleaseProfile, target: Path) -> None:
    if not profile.experimental:
        return
    assert profile.profile_manifest is not None
    assert profile.profile_data is not None
    assert profile.beta_readme is not None
    assert profile.runtime_diagnostic is not None
    assert profile.reference_lock is not None
    if profile.passive_kernel is not None:
        copy_file_filtered(
            profile.passive_kernel,
            target / _safe_relative_path(
                profile.profile_data["passive_kernel"],
                label="passive_kernel",
            ),
        )
    copy_file_filtered(
        profile.profile_manifest,
        target / "beta" / "release-profile.json",
    )
    copy_file_filtered(
        profile.beta_readme,
        target / _safe_relative_path(
            profile.profile_guide_package_path,
            label="profile guide package path",
        ),
    )
    diagnostic_target = target / _safe_relative_path(
        profile.runtime_diagnostic_package_path,
        label="runtime_diagnostic",
    )
    copy_file_filtered(profile.runtime_diagnostic, diagnostic_target)
    diagnostic_target.chmod(0o755)
    copy_file_filtered(
        profile.reference_lock,
        target / _safe_relative_path(
            profile.profile_data["reference_lock"],
            label="reference_lock",
        ),
    )
    copy_locked_reference_material(root, target, profile)


def verify_built_beta_runtime(
    profile: ReleaseProfile,
    plugin_root: Path,
    surface: str,
) -> None:
    if not profile.experimental:
        return
    assert profile.profile_data is not None
    expected_by_surface = profile.profile_data.get("generated_artifact_sha256")
    if not isinstance(expected_by_surface, dict):
        raise SystemExit("beta profile must lock generated runtime artifacts by surface")
    expected = expected_by_surface.get(surface)
    if not isinstance(expected, dict) or not expected:
        raise SystemExit(f"beta profile has no generated runtime lock for {surface}")
    for relative, expected_hash in expected.items():
        path = plugin_root / _safe_relative_path(
            relative,
            label=f"generated beta artifact for {surface}",
        )
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise SystemExit(f"generated beta runtime artifact is missing: {relative}") from exc
        if actual != expected_hash:
            raise SystemExit(
                f"generated beta runtime artifact drifted for {surface} at {relative}: "
                f"{actual} != {expected_hash}"
            )


def copy_using_mindthus_conditional_primitives(
    methodologies_dir: Path,
    skill_dir: Path,
    replacements: dict[str, str] | None = None,
) -> None:
    resource_replacements = {
        "../../../skills/using-mindthus/resources/fidelity-contract.md": "../fidelity-contract.md",
        **(replacements or {}),
    }
    source_dir = methodologies_dir / "primitives"
    target_dir = skill_dir / "resources" / "primitives"
    for filename in USING_MINDTHUS_CONDITIONAL_PRIMITIVES:
        copy_file_filtered(
            source_dir / filename,
            target_dir / filename,
            resource_replacements,
        )


def write_claude_activation_hook(plugin_root: Path) -> None:
    write_json(
        plugin_root / "hooks" / "hooks.json",
        {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup|clear|compact",
                        "hooks": [
                            {
                                "type": "command",
                                "command": '"${CLAUDE_PLUGIN_ROOT}/hooks/session-start"',
                                "async": False,
                            }
                        ],
                    }
                ]
            }
        },
    )
    script = f"""#!/usr/bin/env bash
set -euo pipefail

context='<MINDTHUS_ROUTER_CONTEXT>
{CLAUDE_ACTIVATION_ROUTER_PROMPT}
</MINDTHUS_ROUTER_CONTEXT>'

escape_for_json() {{
  local s="$1"
  s="${{s//\\\\/\\\\\\\\}}"
  s="${{s//\\"/\\\\\\"}}"
  s="${{s//$'\\n'/\\\\n}}"
  s="${{s//$'\\r'/\\\\r}}"
  s="${{s//$'\\t'/\\\\t}}"
  printf '%s' "$s"
}}

printf '{{\\n  "hookSpecificOutput": {{\\n    "hookEventName": "SessionStart",\\n    "additionalContext": "%s"\\n  }}\\n}}\\n' "$(escape_for_json "$context")"
"""
    script_path = plugin_root / "hooks" / "session-start"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(script, encoding="utf-8")
    script_path.chmod(0o755)


def write_beta_activation_hook(plugin_root: Path, command_root_variable: str) -> None:
    write_json(
        plugin_root / "hooks" / "hooks.json",
        {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup|resume|clear|compact",
                        "hooks": [
                            {
                                "type": "command",
                                "command": f'"${{{command_root_variable}}}/hooks/session-start"',
                                "async": False,
                            }
                        ],
                    }
                ]
            }
        },
    )
    script = r'''#!/usr/bin/env bash
set -euo pipefail

plugin_root="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
if [[ -z "$plugin_root" ]]; then
  printf '%s\n' 'Mindthus beta hook requires PLUGIN_ROOT or CLAUDE_PLUGIN_ROOT.' >&2
  exit 1
fi

kernel_path="$plugin_root/runtime/passive-activation-kernel.md"
if [[ ! -r "$kernel_path" ]]; then
  printf 'Mindthus beta kernel is not readable: %s\n' "$kernel_path" >&2
  exit 1
fi

context="<MINDTHUS_PASSIVE_KERNEL>
$(cat "$kernel_path")
</MINDTHUS_PASSIVE_KERNEL>"

escape_for_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$(escape_for_json "$context")"
'''
    script_path = plugin_root / "hooks" / "session-start"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(script, encoding="utf-8")
    script_path.chmod(0o755)


def build_claude_code(
    root: Path,
    repo: Path,
    skills_dir: Path,
    methodologies_dir: Path,
    profile: ReleaseProfile,
) -> None:
    platform_root = root / "claude-code"
    plugin_dir_name = profile.plugin_name if profile.experimental else "claude-plugin"
    plugin_root = platform_root / plugin_dir_name

    write_json(
        platform_root / ".claude-plugin" / "marketplace.json",
        {
            "name": profile.marketplace_name,
            "description": (
                "Mindthus 2.0 Beta experimental skills marketplace"
                if profile.experimental
                else "Mindthus public skills marketplace"
            ),
            "owner": {"name": "Mindthus"},
            "plugins": [
                {
                    "name": profile.plugin_name,
                    "source": f"./{plugin_dir_name}",
                }
            ],
        },
    )
    write_json(
        plugin_root / ".claude-plugin" / "plugin.json",
        {
            "name": profile.plugin_name,
            "version": profile.version,
            "description": (
                "Mindthus 2.0 Beta: direct owner routing plus an experimental passive kernel"
                if profile.experimental
                else "Mindthus cognitive judgment skills pack"
            ),
            "author": {"name": "Mindthus"},
        },
    )
    copy_skills_for_profile(skills_dir, plugin_root / "skills", profile)
    if not profile.experimental:
        copy_using_mindthus_conditional_primitives(
            methodologies_dir,
            plugin_root / "skills" / "using-mindthus",
        )
        copy_tree_filtered(methodologies_dir, plugin_root / "docs" / "methodologies")
    copy_license_files(repo, plugin_root)
    if profile.experimental:
        copy_profile_runtime(repo, profile, plugin_root)
    else:
        copy_release_scripts(repo, plugin_root)
    if profile.experimental:
        write_beta_activation_hook(plugin_root, "CLAUDE_PLUGIN_ROOT")
    else:
        write_claude_activation_hook(plugin_root)
    verify_built_beta_runtime(profile, plugin_root, "claude-plugin")


def build_claude_code_skills(root: Path, repo: Path, skills_dir: Path, methodologies_dir: Path) -> None:
    platform_root = root / "claude-code"
    copy_tree_filtered(skills_dir, platform_root / "skills")
    copy_using_mindthus_conditional_primitives(
        methodologies_dir,
        platform_root / "skills" / "using-mindthus",
    )
    copy_tree_filtered(methodologies_dir, platform_root / "docs" / "methodologies")
    copy_license_files(repo, platform_root)
    copy_release_scripts(repo, platform_root)


def build_codex(root: Path, repo: Path, skills_dir: Path, agents_file: Path, methodologies_dir: Path) -> None:
    platform_root = root / "codex"
    replacements = skill_path_replacements("skills/mindthus")
    copy_tree_filtered(skills_dir, platform_root / "skills" / "mindthus", replacements)
    copy_using_mindthus_conditional_primitives(
        methodologies_dir,
        platform_root / "skills" / "mindthus" / "using-mindthus",
        replacements,
    )
    copy_tree_filtered(
        methodologies_dir,
        platform_root / "docs" / "methodologies",
        replacements,
    )
    copy_file_filtered(agents_file, platform_root / "AGENTS.md", replacements)
    copy_license_files(repo, platform_root)
    copy_release_scripts(repo, platform_root)


def build_codex_plugin(
    root: Path,
    repo: Path,
    skills_dir: Path,
    methodologies_dir: Path,
    profile: ReleaseProfile,
) -> None:
    native_thin = profile.carrier_mode == "native-skill-description"
    marketplace_root = root / "codex-plugin"
    plugin_root = marketplace_root / profile.plugin_name
    write_json(
        marketplace_root / ".agents" / "plugins" / "marketplace.json",
        {
            "name": profile.marketplace_name,
            "interface": {"displayName": profile.display_name},
            "plugins": [
                {
                    "name": profile.plugin_name,
                    "source": {"source": "local", "path": f"./{profile.plugin_name}"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Engineering",
                }
            ],
        },
    )
    plugin_manifest = {
        "name": profile.plugin_name,
        "version": profile.version,
        "description": (
            "Experimental Codex-native thin judgment entry with direct owner discovery."
            if native_thin
            else (
                "Experimental two-plane judgment routing with passive cognitive-primitive activation."
                if profile.experimental
                else "Judgment framework skills that help agents choose the right method before acting."
            )
        ),
        "author": {"name": "Mindthus"},
        "homepage": "https://github.com/rv198-star/Mindthus",
        "repository": "https://github.com/rv198-star/Mindthus",
        "license": "AGPL-3.0-only",
        "keywords": [
            "judgment",
            "agent-workflow",
            "skills",
            "decision-making",
            "tplan",
            "sela",
            "mpg",
        ],
        "skills": "./skills/",
        "interface": {
            "displayName": profile.display_name,
            "shortDescription": (
                "Native thin entry with direct owner discovery"
                if native_thin
                else (
                    "Direct owner routing with a thin passive kernel"
                    if profile.experimental
                    else "Choose the right judgment lens before acting"
                )
            ),
            "longDescription": (
                (
                    "Mindthus 2.0 successor tests one natively discoverable thin entry plus direct "
                    "owner discovery on Codex. It has no SessionStart hook and keeps 1.4.6 owner "
                    "contracts as a locked baseline. Native activation and behavior remain unproven. "
                )
                if native_thin
                else (
                    (
                        "Mindthus 2.0 Beta tests direct owner discovery plus a thin passive activation "
                        "kernel. It is an opt-in experiment and keeps 1.4.6 as the stable baseline. "
                        "After installation, review and trust its SessionStart hook with /hooks; "
                        "without that trust, passive recall is not guaranteed. "
                    )
                    if profile.experimental
                    else (
                        "Mindthus is a judgment framework for AI agents. It helps Codex route "
                        "unclear, strategic, path-dependent, evidence-bound, or artifact-quality "
                        "problems to the smallest sufficient method instead of adding process everywhere. "
                    )
                )
            )
            + (
                "The release-pack manifest uses SPDX AGPL-3.0-only for the open-source lane; "
                "separate commercial licensing is documented in the repository license materials."
            ),
            "developerName": "Mindthus",
            "category": "Engineering",
            "capabilities": ["Interactive", "Read"],
            "websiteURL": "https://github.com/rv198-star/Mindthus",
            "privacyPolicyURL": "https://github.com/rv198-star/Mindthus",
            "termsOfServiceURL": "https://github.com/rv198-star/Mindthus",
            "defaultPrompt": [
                profile.default_prompt
                if profile.experimental and profile.default_prompt is not None
                else CODEX_ACTIVATION_ROUTER_PROMPT
            ],
            "brandColor": "#161614",
            "composerIcon": "./assets/mindthus-icon.svg",
            "logo": "./assets/mindthus-logo.svg",
            "logoDark": "./assets/mindthus-logo-dark.svg",
        },
    }
    write_json(plugin_root / ".codex-plugin" / "plugin.json", plugin_manifest)
    for skill_name in SKILL_NAMES:
        jsonl_allowlist = {Path("templates/evidence.jsonl")} if skill_name == "tplan" else set()
        source = (
            profile.using_skill_dir
            if skill_name == "using-mindthus"
            else skills_dir / skill_name
        )
        copy_tree_filtered(
            source,
            plugin_root / "skills" / skill_name,
            profile_skill_replacements(profile),
            jsonl_allowlist=jsonl_allowlist,
        )
        apply_profile_owner_override(profile, skill_name, plugin_root / "skills" / skill_name)
    if not profile.experimental:
        copy_using_mindthus_conditional_primitives(
            methodologies_dir,
            plugin_root / "skills" / "using-mindthus",
        )
    copy_tree_filtered(skills_dir / "_runtime", plugin_root / "_runtime")
    if not profile.experimental:
        copy_tree_filtered(
            methodologies_dir,
            plugin_root / "docs" / "methodologies",
        )
    copy_codex_plugin_visual_assets(repo, plugin_root)
    copy_license_files(repo, plugin_root)
    if profile.experimental:
        copy_profile_runtime(repo, profile, plugin_root)
    else:
        copy_release_scripts(repo, plugin_root)
    if profile.carrier_mode == "session-start-kernel":
        write_beta_activation_hook(plugin_root, "PLUGIN_ROOT")
    verify_built_beta_runtime(profile, plugin_root, "codex-plugin")


def build_opencode(root: Path, repo: Path, skills_dir: Path, agents_file: Path, methodologies_dir: Path) -> None:
    platform_root = root / "opencode"
    replacements = skill_path_replacements(".opencode/skills/mindthus")
    copy_tree_filtered(skills_dir, platform_root / ".opencode" / "skills" / "mindthus", replacements)
    copy_using_mindthus_conditional_primitives(
        methodologies_dir,
        platform_root / ".opencode" / "skills" / "mindthus" / "using-mindthus",
        replacements,
    )
    copy_tree_filtered(
        methodologies_dir,
        platform_root / "docs" / "methodologies",
        replacements,
    )
    copy_file_filtered(agents_file, platform_root / "AGENTS.md", replacements)
    copy_license_files(repo, platform_root)
    copy_release_scripts(repo, platform_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="Output directory for the release pack.")
    parser.add_argument(
        "--package",
        choices=("all", "plugins", "skills"),
        default="all",
        help="Package surface to build. Release assets use plugins and skills; all is for local inspection.",
    )
    parser.add_argument(
        "--release-line",
        choices=RELEASE_LINES,
        default="stable",
        help="Build the stable line or an explicit experimental release profile.",
    )
    parser.add_argument("--force", action="store_true", help="Replace a non-empty output directory.")
    args = parser.parse_args()

    root = repo_root()
    profile = load_release_profile(root, args.release_line)
    if args.package not in profile.supported_packages:
        supported = ", ".join(profile.supported_packages)
        raise SystemExit(
            f"release line {profile.release_line} supports package selection(s): {supported}"
        )
    skills_dir = root / "skills"
    methodologies_dir = root / "docs" / "methodologies"
    agents_file = root / "AGENTS.md"
    if not skills_dir.is_dir():
        raise SystemExit(f"skills directory not found: {skills_dir}")
    if not methodologies_dir.is_dir():
        raise SystemExit(f"methodologies directory not found: {methodologies_dir}")
    if not agents_file.is_file():
        raise SystemExit(f"AGENTS.md not found: {agents_file}")
    for filename in LICENSE_FILES:
        if not (root / filename).is_file():
            raise SystemExit(f"{filename} not found: {root / filename}")
    for rel_path in RELEASE_SCRIPT_PATHS:
        if not (root / "scripts" / rel_path).is_file():
            raise SystemExit(f"{rel_path} not found: {root / 'scripts' / rel_path}")

    output = args.out.resolve()
    ensure_safe_output_dir(output, root)
    ensure_output_dir(output, args.force)
    if args.package in ("all", "plugins"):
        if "claude-plugin" in profile.supported_surfaces:
            build_claude_code(output, root, skills_dir, methodologies_dir, profile)
        if "codex-plugin" in profile.supported_surfaces:
            build_codex_plugin(output, root, skills_dir, methodologies_dir, profile)
    if args.package in ("all", "skills"):
        build_claude_code_skills(output, root, skills_dir, methodologies_dir)
        build_codex(output, root, skills_dir, agents_file, methodologies_dir)
        build_opencode(output, root, skills_dir, agents_file, methodologies_dir)
    if profile.experimental:
        print(
            f"built Mindthus {profile.version} {args.package} release pack "
            f"for {profile.release_line} at {output}"
        )
    else:
        print(f"built Mindthus {args.package} release pack at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
