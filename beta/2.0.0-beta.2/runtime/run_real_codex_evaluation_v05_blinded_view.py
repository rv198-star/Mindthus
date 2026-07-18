#!/usr/bin/env python3
"""Resume v0.5 with deterministic Judge-only candidate de-identification.

This additive wrapper reuses the frozen v0.5 Judge compatibility runner.  It
does not mutate Generator answers or change any budget, scoring, isolation, or
batch-commit contract.  Only the copy embedded in the Judge input and prompt is
transformed, using the already frozen v0.4 deterministic primitive.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Mapping, Sequence


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
COMPAT_RUNNER_PATH = RUNTIME_ROOT / "run_real_codex_evaluation_v05_judge_compat.py"
VIEW_PRIMITIVE_PATH = RUNTIME_ROOT / "blinded_candidate_view_v04.py"
AMENDMENT_PATH = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-blinded-view.1.json"
)
DEFAULT_AUTHORIZATION = (
    BETA_ROOT
    / "authorizations"
    / "issue-119-codex-v0.5-blinded-view.1.pending.json"
)
AMENDMENT_ID = "0.5-blinded-view.1"
SOURCE_RUN = (
    REPO_ROOT
    / ".tplan"
    / "missions"
    / "mindthus-beta2-evaluation"
    / "artifacts"
    / "real-v05-smoke-f9bc7232"
    / "run"
)
SOURCE_ARMS = SOURCE_RUN.parent / "arms"
DEFAULT_MANIFESTS = (
    SOURCE_ARMS / "stable" / "sealed-arm.json",
    SOURCE_ARMS / "direct-only-r2" / "sealed-arm.json",
    SOURCE_ARMS / "thin-kernel" / "sealed-arm.json",
)
SOURCE_SNAPSHOT_ROOT = SOURCE_RUN / "recovery" / AMENDMENT_ID / "pre-amendment"
SOURCE_RECEIPT_PATH = SOURCE_SNAPSHOT_ROOT / "source-receipt.json"
ANALYZER = RUNTIME_ROOT / "analyze_incremental_v05_blinded_view.py"
NO_LABEL_MATCH = re.compile(r"(?!)")


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


COMPAT = _load("mindthus_beta2_v05_blinded_compat", COMPAT_RUNNER_PATH)
VIEW = _load("mindthus_beta2_v05_blinded_primitive", VIEW_PRIMITIVE_PATH)
BASE = COMPAT.BASE
V04 = COMPAT.V04


class BlindedViewStop(COMPAT.CompatibilityStop):
    def __init__(self, veto_id: str, reason: str):
        super().__init__(veto_id, reason)


_ACTIVE_OUT_DIR: Path | None = None
_ACTIVE_AMENDMENT: Mapping[str, Any] | None = None
_ORIGINAL_WRITE_BLINDED_INPUT: Any = None
_ORIGINAL_JUDGE_PROMPT: Any = None


def require(condition: bool, veto_id: str, reason: str) -> None:
    if not condition:
        raise BlindedViewStop(veto_id, reason)


def canonical_sha256(value: object) -> str:
    return V04.canonical_sha256(value)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def repo_path(value: object, label: str) -> Path:
    require(
        isinstance(value, str) and bool(value),
        "blinded-view-source-drift",
        f"{label} must be repository-relative",
    )
    path = (REPO_ROOT / str(value)).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise BlindedViewStop(
            "blinded-view-source-drift", f"{label} leaves repository"
        ) from exc
    return path


def recovery_root(out_dir: Path) -> Path:
    return out_dir / "recovery" / AMENDMENT_ID


def _copy_immutable(source: Path, destination: Path) -> None:
    require(
        source.is_file(),
        "blinded-view-source-drift",
        f"snapshot source is missing: {source}",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        require(
            sha256_file(destination) == sha256_file(source),
            "blinded-view-source-drift",
            f"snapshot already differs: {destination}",
        )
        return
    temporary = destination.with_name(f".{destination.name}.partial")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def _artifact_receipts(paths: Iterable[Path]) -> list[dict[str, str]]:
    receipts = [
        {"path": display(path), "sha256": sha256_file(path)}
        for path in sorted({path.resolve() for path in paths}, key=str)
    ]
    return receipts


def _source_artifact_paths(out_dir: Path) -> list[Path]:
    patterns = (
        "batch-commits/*.json",
        "cells/*/record.json",
        "generation-attempts/**/*",
        "judge-attempts/**/*",
        "judge-inputs/*.json",
        "judge-records/*/*.json",
        "isolation-receipts/generation/**/*",
        "isolation-receipts/judge/**/*",
        "human-judge-failure-packets/*.json",
    )
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(path for path in out_dir.glob(pattern) if path.is_file())
    return sorted(paths, key=str)


def _manifest_context(
    manifests: Sequence[Path],
) -> tuple[list[dict[str, Any]], list[str]]:
    receipts: list[dict[str, Any]] = []
    sensitive: set[str] = set()
    for path in manifests:
        resolved = path.resolve()
        require(
            resolved.is_file(),
            "blinded-view-source-drift",
            f"arm manifest is missing: {resolved}",
        )
        manifest = read_json(resolved)
        receipts.append(
            {
                "arm_id": manifest["arm_id"],
                "path": display(resolved),
                "sha256": sha256_file(resolved),
                "identity_digest": manifest["identity_digest"],
            }
        )
        for section, field in (
            ("host", "home"),
            ("host", "execution_root"),
            ("package", "root"),
        ):
            sensitive.add(str(Path(manifest[section][field]).resolve()))
    receipts.sort(key=lambda item: str(item["arm_id"]))
    require(
        [item["arm_id"] for item in receipts]
        == ["direct-only", "stable", "thin-kernel"],
        "blinded-view-source-drift",
        "source arm set differs",
    )
    return receipts, VIEW.normalized_paths(sensitive)


def _identifier_scan(
    out_dir: Path,
    protocol_sha256: str,
    cell_ids: Iterable[str],
    sensitive_paths: Sequence[str],
) -> list[dict[str, Any]]:
    exposed: list[dict[str, Any]] = []
    for cell_id in sorted(cell_ids):
        record = BASE.completed_cell(out_dir, cell_id)
        require(
            record is not None,
            "blinded-view-source-drift",
            f"source cell disappeared: {cell_id}",
        )
        assert record is not None
        answer = Path(record["answer_path"]).read_text(encoding="utf-8")
        require(
            not any(path in answer for path in sensitive_paths),
            "judge-environment-contamination",
            f"source candidate exposes an exact sensitive path: {cell_id}",
        )
        blinded, transformations = VIEW.transform_candidate(answer, sensitive_paths)
        VIEW.assert_blind(blinded, sensitive_paths)
        if transformations:
            exposed.append(
                {
                    "cell_id": cell_id,
                    "blinded_output_id": BASE.judge_identity(
                        protocol_sha256, cell_id
                    ),
                    "answer_sha256": record["answer_sha256"],
                    "blinded_answer_sha256": VIEW.text_sha256(blinded),
                    "transformations": transformations,
                }
            )
    exposed.sort(key=lambda item: str(item["cell_id"]))
    return exposed


def build_source_snapshot(
    out_dir: Path = SOURCE_RUN,
    manifest_paths: Sequence[Path] = DEFAULT_MANIFESTS,
) -> dict[str, Any]:
    """Materialize and return the zero-model pre-amendment source receipt."""

    out_dir = out_dir.resolve()
    receipt_path = recovery_root(out_dir) / "pre-amendment" / "source-receipt.json"
    if receipt_path.is_file():
        return validate_source_snapshot(
            {
                "snapshot_receipt_path": display(receipt_path),
                "snapshot_receipt_sha256": sha256_file(receipt_path),
                "snapshot_receipt_digest": read_json(receipt_path)["receipt_digest"],
            }
        )

    V04.scan_partial_artifacts(out_dir)
    state_path = out_dir / "recovery" / COMPAT.COMPAT_ID / "run-state.json"
    analysis_path = out_dir / "incremental-analysis-v0.5.json"
    state = read_json(state_path)
    state_unsigned = dict(state)
    state_digest = state_unsigned.pop("state_digest", None)
    require(
        state_digest == canonical_sha256(state_unsigned)
        and state.get("status") == "vetoed"
        and state.get("veto_id") == "judge-environment-contamination",
        "blinded-view-source-drift",
        "v0.5 compatibility stop state differs",
    )
    require(
        (
            state.get("committed_batches"),
            state.get("generation_calls"),
            state.get("judge_calls"),
            state.get("counted_tokens"),
            state.get("active_batch_index"),
        )
        == (1, 6, 10, 274_864, 2),
        "blinded-view-source-drift",
        "v0.5 compatibility stop accounting differs",
    )
    require(
        analysis_path.is_file(),
        "blinded-view-source-drift",
        "committed-batch analysis is missing",
    )

    snapshot_root = receipt_path.parent
    state_copy = snapshot_root / "judge-compatibility-stop-state.json"
    analysis_copy = snapshot_root / "incremental-analysis-v0.5.json"
    _copy_immutable(state_path, state_copy)
    _copy_immutable(analysis_path, analysis_copy)

    protocol_sha256 = str(state["protocol_sha256"])
    protocol = read_json(BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json")
    batches = BASE.batch_plan(protocol, protocol_sha256)
    summary = BASE.committed_summary(out_dir, batches)
    require(
        summary["committed_batches"] == 1,
        "blinded-view-source-drift",
        "source committed-batch count differs",
    )
    generation_calls, judge_calls, counted_tokens = V04.observed_attempt_usage(out_dir)
    require(
        (generation_calls, judge_calls, counted_tokens) == (6, 10, 274_864),
        "blinded-view-source-drift",
        "source attempt accounting differs",
    )

    cell_ids = sorted(path.parent.name for path in out_dir.glob("cells/*/record.json"))
    judge_records = sorted(out_dir.glob("judge-records/*/*.json"), key=str)
    judge_inputs = sorted(out_dir.glob("judge-inputs/*.json"), key=str)
    require(
        len(cell_ids) == 6 and len(judge_records) == 6 and len(judge_inputs) == 3,
        "blinded-view-source-drift",
        "source semantic artifact counts differ",
    )
    commit_path = next(iter(sorted(out_dir.glob("batch-commits/*.json"), key=str)))
    commit = read_json(commit_path)
    committed_cell_ids = {
        str(item["cell_id"]) for item in commit["generation_records"]
    }
    uncommitted_cell_ids = sorted(set(cell_ids) - committed_cell_ids)
    require(
        len(committed_cell_ids) == len(uncommitted_cell_ids) == 3,
        "blinded-view-source-drift",
        "source committed/uncommitted triplets differ",
    )

    manifests, sensitive_paths = _manifest_context(manifest_paths)
    scan = _identifier_scan(out_dir, protocol_sha256, cell_ids, sensitive_paths)
    require(
        len(scan) == 1
        and scan[0]["cell_id"]
        == "11b0c13b639611727b8cfa425feb29263d90d7e7e1e1e332ac4937a82e8fd64b"
        and scan[0]["answer_sha256"]
        == "0747a7cdd5d945643d967204fd7ac17c2e43da20417eadeaffff953ba2aff312",
        "blinded-view-source-drift",
        "identifier exposure set differs",
    )

    artifacts = _artifact_receipts(
        [*_source_artifact_paths(out_dir), state_copy, analysis_copy]
    )
    receipt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-v0.5-blinded-view-source-v0.1",
        "amendment_id": AMENDMENT_ID,
        "source_run_path": display(out_dir),
        "protocol_sha256": protocol_sha256,
        "judge_compatibility_authorization_digest": state["authorization_digest"],
        "usage": {
            "committed_batches": 1,
            "generation_calls": generation_calls,
            "judge_calls": judge_calls,
            "counted_tokens": counted_tokens,
            "generation_outputs": len(cell_ids),
            "valid_judge_records": len(judge_records),
        },
        "remaining_authority": {
            "committed_batches": 4,
            "generation_calls": 11,
            "judge_calls": 24,
            "counted_tokens": 2_725_136,
        },
        "active_batch": {
            "batch_id": state["active_batch_id"],
            "batch_index": 2,
            "retained_uncommitted_cell_ids": uncommitted_cell_ids,
            "batch_judge_calls": 0,
        },
        "committed_batch": {
            "path": display(commit_path),
            "commit_digest": commit["commit_digest"],
            "file_sha256": sha256_file(commit_path),
        },
        "compatibility_stop_state": {
            "path": display(state_copy),
            "state_digest": state_digest,
            "file_sha256": sha256_file(state_copy),
        },
        "committed_analysis": {
            "path": display(analysis_copy),
            "file_sha256": sha256_file(analysis_copy),
        },
        "cell_ids": cell_ids,
        "manifest_receipts": manifests,
        "sensitive_paths": sensitive_paths,
        "sensitive_path_set_digest": canonical_sha256(sensitive_paths),
        "identifier_exposure_scan": {
            "exposed_outputs": len(scan),
            "items": scan,
            "exposed_set_digest": canonical_sha256(scan),
            "exact_sensitive_path_exposures": 0,
        },
        "artifact_receipts": artifacts,
        "artifact_set_digest": canonical_sha256(artifacts),
        "snapshotted_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_digest"] = canonical_sha256(receipt)
    V04.write_atomic_json(receipt_path, receipt)
    return receipt


def validate_source_snapshot(binding: Mapping[str, Any]) -> dict[str, Any]:
    receipt_path = repo_path(
        binding.get("snapshot_receipt_path"), "snapshot_receipt_path"
    )
    require(
        receipt_path.is_file()
        and sha256_file(receipt_path) == binding.get("snapshot_receipt_sha256"),
        "blinded-view-source-drift",
        "source snapshot receipt file differs",
    )
    receipt = read_json(receipt_path)
    unsigned = dict(receipt)
    digest = unsigned.pop("receipt_digest", None)
    require(
        digest == canonical_sha256(unsigned)
        and digest == binding.get("snapshot_receipt_digest"),
        "blinded-view-source-drift",
        "source snapshot receipt digest differs",
    )
    require(
        receipt.get("schema_version")
        == "mindthus-beta2-v0.5-blinded-view-source-v0.1"
        and receipt.get("amendment_id") == AMENDMENT_ID
        and receipt.get("usage")
        == {
            "committed_batches": 1,
            "generation_calls": 6,
            "judge_calls": 10,
            "counted_tokens": 274_864,
            "generation_outputs": 6,
            "valid_judge_records": 6,
        }
        and receipt.get("remaining_authority")
        == {
            "committed_batches": 4,
            "generation_calls": 11,
            "judge_calls": 24,
            "counted_tokens": 2_725_136,
        },
        "blinded-view-source-drift",
        "source snapshot accounting differs",
    )
    artifacts = receipt.get("artifact_receipts")
    require(
        isinstance(artifacts, list)
        and canonical_sha256(artifacts) == receipt.get("artifact_set_digest"),
        "blinded-view-source-drift",
        "source artifact receipt set differs",
    )
    for item in artifacts:
        path = repo_path(item.get("path"), "source artifact path")
        require(
            path.is_file() and sha256_file(path) == item.get("sha256"),
            "blinded-view-source-drift",
            f"source artifact differs: {path}",
        )
    manifests = receipt.get("manifest_receipts")
    require(
        isinstance(manifests, list) and len(manifests) == 3,
        "blinded-view-source-drift",
        "source manifest receipts differ",
    )
    for item in manifests:
        path = repo_path(item.get("path"), "source manifest path")
        require(
            path.is_file() and sha256_file(path) == item.get("sha256"),
            "blinded-view-source-drift",
            f"source manifest differs: {path}",
        )
    sensitive_paths = receipt.get("sensitive_paths")
    require(
        isinstance(sensitive_paths, list)
        and VIEW.normalized_paths(sensitive_paths) == sensitive_paths
        and canonical_sha256(sensitive_paths)
        == receipt.get("sensitive_path_set_digest"),
        "blinded-view-source-drift",
        "source sensitive-path set differs",
    )
    scan = _identifier_scan(
        repo_path(receipt.get("source_run_path"), "source_run_path"),
        str(receipt["protocol_sha256"]),
        receipt["cell_ids"],
        sensitive_paths,
    )
    declared = receipt.get("identifier_exposure_scan")
    require(
        isinstance(declared, Mapping)
        and declared.get("items") == scan
        and declared.get("exposed_outputs") == 1
        and declared.get("exact_sensitive_path_exposures") == 0
        and declared.get("exposed_set_digest") == canonical_sha256(scan),
        "blinded-view-source-drift",
        "source identifier exposure scan differs",
    )
    return receipt


def _active_contract() -> tuple[Path, Mapping[str, Any]]:
    require(
        _ACTIVE_OUT_DIR is not None and _ACTIVE_AMENDMENT is not None,
        "blinded-view-transformation-drift",
        "Judge-only view adapter is inactive",
    )
    assert _ACTIVE_OUT_DIR is not None and _ACTIVE_AMENDMENT is not None
    return _ACTIVE_OUT_DIR, _ACTIVE_AMENDMENT


def _cell_for_output(
    out_dir: Path, output_id: str, protocol_sha256: str
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for path in sorted(out_dir.glob("cells/*/record.json"), key=str):
        cell_id = path.parent.name
        if BASE.judge_identity(protocol_sha256, cell_id) != output_id:
            continue
        record = BASE.completed_cell(out_dir, cell_id)
        if record is not None:
            matches.append(record)
    require(
        len(matches) == 1,
        "blinded-view-transformation-drift",
        f"Judge output cannot be mapped to one Generator cell: {output_id}",
    )
    return matches[0]


def candidate_view(*, out_dir: Path, output_id: str, original: str) -> str:
    _, amendment = _active_contract()
    contract = amendment["blinded_candidate_view"]
    protocol_sha256 = str(amendment["base_binding"]["protocol_sha256"])
    record = _cell_for_output(out_dir, output_id, protocol_sha256)
    cell_id = str(record["cell_id"])
    recorded = Path(record["answer_path"]).read_text(encoding="utf-8")
    require(
        recorded == original
        and VIEW.text_sha256(original) == record["answer_sha256"],
        "blinded-view-transformation-drift",
        f"Judge adapter did not receive the immutable Generator answer: {cell_id}",
    )
    sensitive_paths = contract["sensitive_paths"]
    require(
        not any(path in original for path in sensitive_paths),
        "judge-environment-contamination",
        f"candidate exposes an exact sensitive path: {cell_id}",
    )
    blinded, transformations = VIEW.transform_candidate(original, sensitive_paths)
    try:
        VIEW.assert_blind(blinded, sensitive_paths)
    except VIEW.BlindedViewError as exc:
        raise BlindedViewStop(
            "blinded-view-transformation-drift", str(exc)
        ) from exc
    receipt_path = recovery_root(out_dir) / "candidate-views" / f"{output_id}.json"
    if not transformations:
        require(
            blinded == original and not receipt_path.exists(),
            "blinded-view-transformation-drift",
            f"identity Judge view unexpectedly has a receipt: {output_id}",
        )
        return blinded
    expected = VIEW.view_receipt(
        amendment_id=AMENDMENT_ID,
        output_id=output_id,
        cell_id=cell_id,
        original=original,
        blinded=blinded,
        transformations=transformations,
    )
    if receipt_path.is_file():
        try:
            VIEW.validate_view_receipt(read_json(receipt_path), expected)
        except VIEW.BlindedViewError as exc:
            raise BlindedViewStop(
                "blinded-view-transformation-drift", str(exc)
            ) from exc
    else:
        V04.write_atomic_json(receipt_path, expected)
    return blinded


def _patched_write_blinded_input(
    *,
    out_dir: Path,
    output_id: str,
    prompt: str,
    case: Mapping[str, Any],
    candidate: str,
) -> Path:
    require(
        _ORIGINAL_WRITE_BLINDED_INPUT is not None,
        "blinded-view-transformation-drift",
        "original Judge input writer is unavailable",
    )
    transformed = candidate_view(
        out_dir=out_dir, output_id=output_id, original=candidate
    )
    return _ORIGINAL_WRITE_BLINDED_INPUT(
        out_dir=out_dir,
        output_id=output_id,
        prompt=prompt,
        case=case,
        candidate=transformed,
    )


def _patched_judge_prompt(
    *,
    rubric: Mapping[str, Any],
    case: Mapping[str, Any],
    prompt: str,
    candidate: str,
    blinded_output_id: str,
) -> str:
    out_dir, _ = _active_contract()
    require(
        _ORIGINAL_JUDGE_PROMPT is not None,
        "blinded-view-transformation-drift",
        "original Judge prompt builder is unavailable",
    )
    transformed = candidate_view(
        out_dir=out_dir, output_id=blinded_output_id, original=candidate
    )
    return _ORIGINAL_JUDGE_PROMPT(
        rubric=rubric,
        case=case,
        prompt=prompt,
        candidate=transformed,
        blinded_output_id=blinded_output_id,
    )


def _authorization_context(
    path: Path, *, allow_pending: bool
) -> tuple[dict[str, Any], dict[str, Any]]:
    authorization = read_json(path)
    validator = repo_path(
        authorization.get("authorization_validator_path"),
        "authorization_validator_path",
    )
    command = ["python3", str(validator), "--authorization", str(path)]
    if allow_pending:
        command.append("--allow-pending")
    report = V04.run_json(command, label="v0.5 blinded-view authorization")
    allowed = {"pending", "authorized"} if allow_pending else {"authorized"}
    require(
        report.get("status") in allowed,
        "authority-or-evidence-regression",
        "v0.5 blinded-view authorization is inactive",
    )
    return report, authorization


def preflight(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    auth_report, authorization = _authorization_context(
        args.authorization.resolve(), allow_pending=True
    )
    amendment = read_json(AMENDMENT_PATH)
    source = validate_source_snapshot(amendment["retained_source_run"])
    manifests = V04.verify_arm_set(args.arm_manifest, authorization)
    generation_calls, judge_calls, counted_tokens = V04.observed_attempt_usage(out_dir)
    require(
        (generation_calls, judge_calls, counted_tokens) == (6, 10, 274_864),
        "blinded-view-source-drift",
        "pre-amendment usage differs",
    )
    report = {
        "status": (
            "ready"
            if auth_report["status"] == "authorized"
            else "pending-authorization"
        ),
        "amendment_id": AMENDMENT_ID,
        "protocol_sha256": auth_report["protocol_sha256"],
        "blinded_view_protocol_sha256": sha256_file(AMENDMENT_PATH),
        "authorization_status": auth_report["status"],
        "verified_arm_ids": sorted(manifests),
        "source_receipt_digest": source["receipt_digest"],
        "retained_uncommitted_generation_outputs": 3,
        "remaining_generation_calls": 11,
        "remaining_judge_calls": 24,
        "remaining_counted_tokens": 2_725_136,
        "model_execution_performed": False,
        "semantic_output_generated": False,
    }
    V04.write_atomic_json(recovery_root(out_dir) / "preflight-report.json", report)
    return report, 0


def run_recovery(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    global _ACTIVE_AMENDMENT
    global _ACTIVE_OUT_DIR
    global _ORIGINAL_JUDGE_PROMPT
    global _ORIGINAL_WRITE_BLINDED_INPUT

    out_dir = args.out_dir.resolve()
    auth_report, authorization = _authorization_context(
        args.authorization.resolve(), allow_pending=False
    )
    amendment = read_json(AMENDMENT_PATH)
    validate_source_snapshot(amendment["retained_source_run"])
    generation_calls, judge_calls, counted_tokens = V04.observed_attempt_usage(out_dir)
    require(
        generation_calls >= 6
        and judge_calls >= 10
        and counted_tokens >= 274_864
        and generation_calls <= authorization["maximum_generation_calls"]
        and judge_calls <= authorization["maximum_judge_calls"]
        and counted_tokens <= authorization["token_or_cost_budget"]["maximum"],
        "authority-or-evidence-regression",
        "current recovery usage is outside the frozen cumulative ceilings",
    )

    original_label_pattern = V04.FORBIDDEN_BLINDING_LABEL
    original_analyzer = BASE.ANALYZER_V05
    _ORIGINAL_WRITE_BLINDED_INPUT = V04.write_blinded_input
    _ORIGINAL_JUDGE_PROMPT = V04.judge_prompt
    _ACTIVE_OUT_DIR = out_dir
    _ACTIVE_AMENDMENT = amendment
    V04.FORBIDDEN_BLINDING_LABEL = NO_LABEL_MATCH
    V04.write_blinded_input = _patched_write_blinded_input
    V04.judge_prompt = _patched_judge_prompt
    BASE.ANALYZER_V05 = ANALYZER
    try:
        report, code = COMPAT.run_recovery(args)
    except (
        BlindedViewStop,
        COMPAT.CompatibilityStop,
        BASE.EvaluationStop,
        V04.EvaluationStop,
    ) as exc:
        raise BlindedViewStop(
            getattr(exc, "veto_id", "blinded-view-transformation-drift"),
            str(exc),
        ) from exc
    finally:
        V04.FORBIDDEN_BLINDING_LABEL = original_label_pattern
        V04.write_blinded_input = _ORIGINAL_WRITE_BLINDED_INPUT
        V04.judge_prompt = _ORIGINAL_JUDGE_PROMPT
        BASE.ANALYZER_V05 = original_analyzer
        _ACTIVE_OUT_DIR = None
        _ACTIVE_AMENDMENT = None
        _ORIGINAL_WRITE_BLINDED_INPUT = None
        _ORIGINAL_JUDGE_PROMPT = None
    report.update(
        {
            "blinded_view_amendment_id": AMENDMENT_ID,
            "blinded_view_protocol_sha256": sha256_file(AMENDMENT_PATH),
            "blinded_view_authorization_digest": auth_report[
                "authorization_digest"
            ],
        }
    )
    V04.write_atomic_json(recovery_root(out_dir) / "summary.json", report)
    return report, code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--arm-manifest", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument(
        "--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json"
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report, code = preflight(args) if args.preflight_only else run_recovery(args)
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        report = {
            "status": "vetoed",
            "veto_id": getattr(
                exc, "veto_id", "authority-or-evidence-regression"
            ),
            "reason": str(exc),
        }
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
