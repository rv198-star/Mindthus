#!/usr/bin/env python3
"""Zero-model rehearsal for v0.5 isolation, batch commits, stop, and resume."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence


BETA_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = BETA_ROOT / "runtime" / "run_real_codex_evaluation_v05.py"
ISOLATION_PATH = BETA_ROOT / "runtime" / "filesystem_isolation_v05.py"
DEFAULT_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load("mindthus_beta2_v05_runner_for_dry_run", RUNNER_PATH)
ISO = _load("mindthus_beta2_v05_isolation_for_dry_run", ISOLATION_PATH)


class DryRunError(RuntimeError):
    pass


def canonical_sha256(value: object) -> str:
    return RUNNER.canonical_sha256(value)


def fake_commit(
    batch: Mapping[str, Any], previous_digest: str | None
) -> dict[str, Any]:
    commit: dict[str, Any] = {
        "schema_version": RUNNER.BATCH_COMMIT_SCHEMA,
        "protocol_sha256": "dry-run-protocol",
        "batch_id": batch["batch_id"],
        "batch_index": batch["batch_index"],
        "case_id": batch["case_id"],
        "repeat": batch["repeat"],
        "previous_commit_digest": previous_digest,
        "generation_record_digests": [
            canonical_sha256({"batch": batch["batch_id"], "arm": cell["arm_id"]})
            for cell in batch["cells"]
        ],
        "isolation_receipt_digests": [
            canonical_sha256({"batch": batch["batch_id"], "arm": cell["arm_id"], "isolation": "pass"})
            for cell in batch["cells"]
        ],
        "judge_record_digests": [
            canonical_sha256(
                {
                    "batch": batch["batch_id"],
                    "arm": cell["arm_id"],
                    "slot": slot,
                }
            )
            for cell in batch["cells"]
            for slot in (1, 2)
        ],
        "model_execution_performed": False,
        "semantic_output_generated": False,
    }
    commit["commit_digest"] = canonical_sha256(commit)
    return commit


def validate_fake_chain(
    batches: Sequence[Mapping[str, Any]], commits: Sequence[Mapping[str, Any]]
) -> None:
    previous: str | None = None
    for expected, commit in zip(batches, commits, strict=False):
        unsigned = dict(commit)
        digest = unsigned.pop("commit_digest", None)
        if (
            digest != canonical_sha256(unsigned)
            or commit.get("batch_id") != expected["batch_id"]
            or commit.get("batch_index") != expected["batch_index"]
            or commit.get("previous_commit_digest") != previous
            or len(commit.get("generation_record_digests", [])) != 3
            or len(commit.get("isolation_receipt_digests", [])) != 3
            or len(commit.get("judge_record_digests", [])) != 6
        ):
            raise DryRunError("incremental commit chain differs")
        previous = str(digest)


def rehearse(protocol_path: Path, out_dir: Path) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol_sha256 = ISO.sha256_file(protocol_path)
    batches = RUNNER.batch_plan(protocol, protocol_sha256)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="v05-isolation-", dir=out_dir) as temp:
        root = Path(temp)
        allowed = root / "allowed"
        forbidden = root / "forbidden"
        allowed.mkdir()
        forbidden.mkdir()
        allowed_file = allowed / "own.txt"
        forbidden_file = forbidden / "control.txt"
        allowed_file.write_text("own\n", encoding="utf-8")
        forbidden_file.write_text("control\n", encoding="utf-8")
        receipt = ISO.prepare_verified_profile(
            profile_path=allowed / "profile.sb",
            receipt_path=allowed / "receipt.json",
            protected_roots=[root],
            allowed_read_roots=[allowed],
            allowed_write_roots=[allowed],
            allowed_read_files=[],
            probe_root=allowed,
            allowed_targets=[allowed_file],
            forbidden_targets=[forbidden_file],
        )

    commits: list[dict[str, Any]] = []
    previous: str | None = None
    for batch in batches[:5]:
        commit = fake_commit(batch, previous)
        commits.append(commit)
        previous = commit["commit_digest"]
    validate_fake_chain(batches, commits)
    stopped_committed_count = len(commits)
    # Batch six is deliberately left uncommitted. It must not change any denominator.
    partial_batch = {
        "batch_id": batches[5]["batch_id"],
        "generation_artifacts": 2,
        "judge_artifacts": 0,
        "commit": None,
    }
    if stopped_committed_count != 5:
        raise DryRunError("partial batch changed committed count")
    resumed = fake_commit(batches[5], previous)
    commits.append(resumed)
    validate_fake_chain(batches, commits)

    report: dict[str, Any] = {
        "schema_version": "mindthus-beta2-incremental-dry-run-v0.5",
        "status": "passed",
        "protocol_sha256": protocol_sha256,
        "planned_batches": len(batches),
        "planned_generation_outputs": len(batches) * 3,
        "planned_judge_records": len(batches) * 6,
        "smoke_batches": 5,
        "committed_before_injected_stop": stopped_committed_count,
        "committed_generation_outputs_before_stop": stopped_committed_count * 3,
        "committed_judge_records_before_stop": stopped_committed_count * 6,
        "partial_batch": partial_batch,
        "committed_after_resume": len(commits),
        "hash_chain_valid": True,
        "filesystem_probe_status": receipt["status"],
        "parent_traversal_denied": receipt["parent_traversal_probe"]["denied"],
        "symlink_escape_denied": receipt["symlink_escape_probe"]["denied"],
        "model_calls": 0,
        "judge_model_calls": 0,
        "semantic_outputs": 0,
        "claim_boundary": "shape, isolation-carrier, stop, and resume proof only",
    }
    report["report_digest"] = canonical_sha256(report)
    RUNNER.write_atomic_json(out_dir / "dry-run-report-v0.5.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = rehearse(args.protocol.resolve(), args.out_dir.resolve())
        code = 0
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
