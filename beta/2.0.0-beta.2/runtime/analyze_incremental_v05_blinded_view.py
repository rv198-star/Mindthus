#!/usr/bin/env python3
"""Validate v0.5 Judge-only candidate views, then run incremental analysis."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
BASE_ANALYZER_PATH = RUNTIME_ROOT / "analyze_incremental_v05.py"
RUNNER_PATH = RUNTIME_ROOT / "run_real_codex_evaluation_v05_blinded_view.py"
AMENDMENT_PATH = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.5-blinded-view.1.json"
)


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE_ANALYZER = _load(
    "mindthus_beta2_v05_blinded_base_analyzer", BASE_ANALYZER_PATH
)
RUNNER = _load("mindthus_beta2_v05_blinded_analysis_runner", RUNNER_PATH)


class BlindedAnalysisError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise BlindedAnalysisError(reason)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_candidate_views(
    run_dir: Path,
    authorization_path: Path,
) -> dict[str, Any]:
    auth_report, _authorization = RUNNER._authorization_context(
        authorization_path.resolve(), allow_pending=False
    )
    amendment = read_json(AMENDMENT_PATH)
    RUNNER.validate_source_snapshot(amendment["retained_source_run"])
    protocol = read_json(
        RUNNER.repo_path(
            amendment["base_binding"]["protocol_path"], "base protocol path"
        )
    )
    protocol_sha256 = str(auth_report["protocol_sha256"])
    batches = RUNNER.BASE.batch_plan(protocol, protocol_sha256)
    cells, judges, commits = BASE_ANALYZER.committed_evidence(
        run_dir, protocol, protocol_sha256
    )
    sensitive_paths = amendment["blinded_candidate_view"]["sensitive_paths"]
    transformed = 0
    identity = 0
    receipts: list[dict[str, str]] = []
    for cell in cells:
        cell_id = str(cell["cell_id"])
        output_id = RUNNER.BASE.judge_identity(protocol_sha256, cell_id)
        original = Path(cell["answer_path"]).read_text(encoding="utf-8")
        require(
            RUNNER.VIEW.text_sha256(original) == cell["answer_sha256"],
            f"original Generator answer differs: {cell_id}",
        )
        require(
            not any(path in original for path in sensitive_paths),
            f"committed candidate exposes an exact sensitive path: {cell_id}",
        )
        blinded, transformations = RUNNER.VIEW.transform_candidate(
            original, sensitive_paths
        )
        RUNNER.VIEW.assert_blind(blinded, sensitive_paths)
        input_path = run_dir / "judge-inputs" / f"{output_id}.json"
        require(input_path.is_file(), f"Judge input is missing: {output_id}")
        judge_input = read_json(input_path)
        unsigned_input = dict(judge_input)
        input_digest = unsigned_input.pop("input_digest", None)
        require(
            input_digest == RUNNER.canonical_sha256(unsigned_input)
            and judge_input.get("candidate_final_answer") == blinded,
            f"Judge input does not contain the deterministic candidate view: {output_id}",
        )
        first, second = judges[cell_id]
        require(
            first.get("blinded_input_digest")
            == second.get("blinded_input_digest")
            == input_digest,
            f"Judge records do not bind the candidate view: {output_id}",
        )
        receipt_path = (
            RUNNER.recovery_root(run_dir)
            / "candidate-views"
            / f"{output_id}.json"
        )
        if transformations:
            expected = RUNNER.VIEW.view_receipt(
                amendment_id=RUNNER.AMENDMENT_ID,
                output_id=output_id,
                cell_id=cell_id,
                original=original,
                blinded=blinded,
                transformations=transformations,
            )
            require(
                receipt_path.is_file(),
                f"transformed candidate view receipt is missing: {output_id}",
            )
            RUNNER.VIEW.validate_view_receipt(read_json(receipt_path), expected)
            receipts.append(
                {
                    "blinded_output_id": output_id,
                    "receipt_digest": expected["receipt_digest"],
                    "file_sha256": RUNNER.sha256_file(receipt_path),
                }
            )
            transformed += 1
        else:
            require(
                not receipt_path.exists(),
                f"identity candidate view unexpectedly has a receipt: {output_id}",
            )
            identity += 1
    receipts.sort(key=lambda item: item["blinded_output_id"])
    return {
        "amendment_id": RUNNER.AMENDMENT_ID,
        "committed_batches_validated": len(commits),
        "committed_candidate_views_validated": len(cells),
        "transformed_candidate_views": transformed,
        "identity_candidate_views": identity,
        "candidate_view_receipts": receipts,
        "candidate_view_receipt_set_digest": RUNNER.canonical_sha256(receipts),
        "original_answers_mutated": False,
        "exact_sensitive_path_exposures": 0,
    }


def analyze(run_dir: Path, authorization_path: Path) -> dict[str, Any]:
    report = BASE_ANALYZER.analyze(run_dir, authorization_path)
    report["blinded_candidate_view_validation"] = validate_candidate_views(
        run_dir, authorization_path
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = analyze(args.run_dir.resolve(), args.authorization.resolve())
        RUNNER.V04.write_atomic_json(
            args.run_dir.resolve() / "incremental-analysis-v0.5.json", report
        )
        code = 0 if report["status"] != "human-adjudication-required" else 3
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
