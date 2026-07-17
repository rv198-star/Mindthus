#!/usr/bin/env python3
"""Analyze v0.4 with the frozen, arm-neutral workspace-evidence view."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import analyze_codex_evaluation_v04 as analysis_base  # noqa: E402
import analyze_codex_evaluation_v04_blinded_view as blinded_analysis  # noqa: E402
import analyze_codex_evaluation_v04_recovery as recovery  # noqa: E402
import blinded_candidate_view_v04 as blinded_view  # noqa: E402
import run_real_codex_evaluation_v04 as runner  # noqa: E402
import run_real_codex_evaluation_v04_judge_compat as compat  # noqa: E402
import workspace_evidence_view_v04 as evidence  # noqa: E402


DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-evidence-view.1.json"
)
AMENDMENT_PATH = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-evidence-view.1.json"
)
BLINDED_AMENDMENT_PATH = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.json"
)
AMENDMENT_ID = "0.4-evidence-view.1"


class EvidenceViewAnalysisError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise EvidenceViewAnalysisError(reason)


def amendment_root(run_dir: Path) -> Path:
    return run_dir / "recovery" / AMENDMENT_ID


def capsule_path(run_dir: Path) -> Path:
    return amendment_root(run_dir) / "workspace-evidence-capsule.json"


def load_capsule(run_dir: Path) -> dict[str, Any]:
    path = capsule_path(run_dir)
    require(path.is_file(), "workspace evidence capsule is missing")
    capsule = runner.read_json(path)
    try:
        evidence.validate_capsule(capsule)
    except evidence.WorkspaceEvidenceError as exc:
        raise EvidenceViewAnalysisError(str(exc)) from exc
    return capsule


def _evidence_candidate_view(
    *,
    run_dir: Path,
    output_id: str,
    cell_id: str,
    original: str,
    sensitive_paths: Iterable[str],
) -> str:
    candidate, transformations = blinded_view.transform_candidate(
        original, sensitive_paths
    )
    blinded_view.assert_blind(candidate, sensitive_paths)
    receipt_path = run_dir / "blinded-candidate-views" / f"{output_id}.json"
    if not transformations:
        require(
            candidate == original and not receipt_path.exists(),
            "identity evidence view unexpectedly has a transformation receipt",
        )
        return candidate
    expected = blinded_view.view_receipt(
        amendment_id=AMENDMENT_ID,
        output_id=output_id,
        cell_id=cell_id,
        original=original,
        blinded=candidate,
        transformations=transformations,
    )
    require(receipt_path.is_file(), f"evidence candidate receipt is missing: {output_id}")
    try:
        blinded_view.validate_view_receipt(runner.read_json(receipt_path), expected)
    except blinded_view.BlindedViewError as exc:
        raise EvidenceViewAnalysisError(str(exc)) from exc
    return candidate


def active_candidate(
    *,
    run_dir: Path,
    protocol_sha256: str,
    amendment_sha256: str,
    cell: Mapping[str, Any],
    sensitive_paths: Iterable[str],
) -> tuple[str, str, bool, str]:
    cell_id = str(cell["cell_id"])
    base_output_id = runner.judge_identity(protocol_sha256, cell_id)
    original = Path(str(cell["answer_path"])).read_text(encoding="utf-8")
    blinded, _trace = blinded_view.transform_candidate(original, sensitive_paths)
    needs_evidence = evidence.requires_workspace_evidence(blinded)
    if needs_evidence:
        output_id = evidence.evidence_identity(amendment_sha256, cell_id)
        candidate = _evidence_candidate_view(
            run_dir=run_dir,
            output_id=output_id,
            cell_id=cell_id,
            original=original,
            sensitive_paths=sensitive_paths,
        )
    else:
        output_id = base_output_id
        candidate, _receipt = blinded_analysis.validate_candidate_view(
            run_dir=run_dir,
            output_id=output_id,
            cell_id=cell_id,
            original=original,
            sensitive_paths=sensitive_paths,
        )
    return output_id, candidate, needs_evidence, base_output_id


def expected_material(
    *,
    output_id: str,
    raw_prompt: str,
    case: Mapping[str, Any],
    candidate: str,
    needs_evidence: bool,
    capsule: Mapping[str, Any],
) -> tuple[dict[str, Any], str]:
    rubric = runner.read_json(runner.JUDGE_RUBRIC)
    if needs_evidence:
        expected = evidence.expected_input(
            output_id=output_id,
            raw_prompt=raw_prompt,
            contract=case["contract"],
            candidate=candidate,
            capsule=capsule,
        )
        prompt = evidence.judge_prompt(
            rubric=rubric,
            case=case,
            prompt=raw_prompt,
            candidate=candidate,
            blinded_output_id=output_id,
            capsule=capsule,
        )
    else:
        expected = blinded_analysis.expected_input(
            output_id=output_id,
            raw_prompt=raw_prompt,
            contract=case["contract"],
            candidate=candidate,
        )
        prompt = runner.judge_prompt(
            rubric=rubric,
            case=case,
            prompt=raw_prompt,
            candidate=candidate,
            blinded_output_id=output_id,
        )
    return expected, prompt


def _environment(run_dir: Path, slot: int) -> dict[str, Any]:
    path = run_dir / "judge-homes" / f"slot-{slot}" / "environment.json"
    require(path.is_file(), f"Judge environment is missing: slot-{slot}")
    environment = runner.read_json(path)
    analysis_base.verify_digest(environment, "environment_digest", "Judge environment")
    require(
        environment.get("slot") == slot
        and environment.get("active_forbidden_plugins") == []
        and environment.get("generator_home_access_granted") is False,
        "Judge environment differs",
    )
    return environment


def _record(
    *,
    run_dir: Path,
    output_id: str,
    slot: int,
    case: Mapping[str, Any],
    expected_input_digest: str,
    expected_prompt_digest: str,
) -> dict[str, Any]:
    environment = _environment(run_dir, slot)
    try:
        record = compat.validate_compatible_record(
            out_dir=run_dir,
            output_id=output_id,
            slot=slot,
            case=case,
            expected_input_digest=expected_input_digest,
            expected_prompt_digest=expected_prompt_digest,
            environment_digest=str(environment["environment_digest"]),
        )
    except runner.EvaluationStop as exc:
        raise EvidenceViewAnalysisError(exc.reason) from exc
    require(record is not None, f"missing Judge record: {output_id}/slot-{slot}")
    assert record is not None
    return record


def load_judges(
    run_dir: Path,
    protocol_sha256: str,
    cells: Iterable[Mapping[str, Any]],
    cases: Mapping[str, Mapping[str, Any]],
) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    amendment = runner.read_json(AMENDMENT_PATH)
    amendment_sha256 = runner.sha256_file(AMENDMENT_PATH)
    sensitive_paths = runner.read_json(BLINDED_AMENDMENT_PATH)[
        "blinded_candidate_view"
    ]["sensitive_paths"]
    capsule = load_capsule(run_dir)
    source_affected = {
        str(item["cell_id"]): str(item["base_blinded_output_id"])
        for item in amendment["diagnosis"]["affected_cells"]
    }
    results: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    expected_records: set[Path] = set()
    expected_inputs: set[Path] = set()
    for cell in cells:
        cell_id = str(cell["cell_id"])
        case = cases[str(cell["cell_key"]["case_id"])]
        output_id, candidate, needs_evidence, base_output_id = active_candidate(
            run_dir=run_dir,
            protocol_sha256=protocol_sha256,
            amendment_sha256=amendment_sha256,
            cell=cell,
            sensitive_paths=sensitive_paths,
        )
        raw_prompt = runner.user_prompt(case["source"])
        expected, prompt = expected_material(
            output_id=output_id,
            raw_prompt=raw_prompt,
            case=case,
            candidate=candidate,
            needs_evidence=needs_evidence,
            capsule=capsule,
        )
        input_path = run_dir / "judge-inputs" / f"{output_id}.json"
        expected_inputs.add(input_path.resolve())
        require(
            input_path.is_file() and runner.read_json(input_path) == expected,
            f"active Judge input differs: {output_id}",
        )
        prompt_digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        records = []
        for slot in (1, 2):
            path = run_dir / "judge-records" / output_id / f"judge-{slot}.json"
            expected_records.add(path.resolve())
            records.append(
                _record(
                    run_dir=run_dir,
                    output_id=output_id,
                    slot=slot,
                    case=case,
                    expected_input_digest=str(expected["input_digest"]),
                    expected_prompt_digest=prompt_digest,
                )
            )
        results[cell_id] = (records[0], records[1])
        if cell_id in source_affected:
            require(
                needs_evidence and source_affected[cell_id] == base_output_id,
                "retrospective paired-unit trigger differs",
            )
            old_input = run_dir / "judge-inputs" / f"{base_output_id}.json"
            expected_inputs.add(old_input.resolve())
            require(old_input.is_file(), "superseded Judge input is missing")
            old_prompt_digest = None
            old_input_digest = str(runner.read_json(old_input)["input_digest"])
            original_candidate = runner.read_json(old_input)["candidate_final_answer"]
            old_prompt = runner.judge_prompt(
                rubric=runner.read_json(runner.JUDGE_RUBRIC),
                case=case,
                prompt=raw_prompt,
                candidate=original_candidate,
                blinded_output_id=base_output_id,
            )
            old_prompt_digest = hashlib.sha256(old_prompt.encode("utf-8")).hexdigest()
            for slot in (1, 2):
                path = run_dir / "judge-records" / base_output_id / f"judge-{slot}.json"
                expected_records.add(path.resolve())
                _record(
                    run_dir=run_dir,
                    output_id=base_output_id,
                    slot=slot,
                    case=case,
                    expected_input_digest=old_input_digest,
                    expected_prompt_digest=old_prompt_digest,
                )
    observed_records = {
        path.resolve() for path in (run_dir / "judge-records").glob("*/*.json")
    }
    observed_inputs = {
        path.resolve() for path in (run_dir / "judge-inputs").glob("*.json")
    }
    require(observed_records == expected_records, "Judge record set contains unexpected artifacts")
    require(observed_inputs == expected_inputs, "Judge input set contains unexpected artifacts")
    return results


def analyze(phase: str, run_dir: Path, authorization_path: Path) -> dict[str, Any]:
    analysis_base.load_judges = load_judges
    recovery.base.load_judges = load_judges
    report = recovery.analyze(phase, run_dir, authorization_path)
    amendment = runner.read_json(AMENDMENT_PATH)
    source_ids = {
        str(item["cell_id"]) for item in amendment["diagnosis"]["affected_cells"]
    }
    active_evidence_records = 0
    for cell_path in (run_dir / "cells").glob("*/record.json"):
        cell_id = cell_path.parent.name
        if cell_id in source_ids:
            active_evidence_records += 2
    report["evidence_view_amendment_id"] = AMENDMENT_ID
    report["original_smoke_veto_retained"] = True
    report["retrospective_paired_unit_rejudged"] = bool(active_evidence_records == 6)
    report["retrospective_rejudge_records"] = active_evidence_records
    report["workspace_evidence_capsule_digest"] = load_capsule(run_dir)[
        "capsule_digest"
    ]
    report["active_record_selection"] = amendment["workspace_evidence_view"][
        "active_record_selection"
    ]
    budget = report.setdefault("budget_accounting", {})
    measured = int(budget.get("measured_counted_tokens") or 0)
    budget.update(
        {
            "unknown_generation_usage_reserved_tokens": 2176000,
            "unknown_judge_usage_reserved_tokens": 2176000,
            "unknown_usage_reserved_tokens": 4352000,
            "conservative_total_for_authority": measured + 4352000,
        }
    )
    report["claim_ceiling"] = (
        str(report.get("claim_ceiling") or "visible-case Codex evidence only")
        + "; post-smoke workspace-evidence correction is explicit and exploratory"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("smoke", "matched"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    args = parser.parse_args()
    try:
        report = analyze(
            args.phase, args.run_dir.resolve(), args.authorization.resolve()
        )
        runner.write_atomic_json(
            amendment_root(args.run_dir.resolve()) / f"{args.phase}-analysis.json",
            report,
        )
        code = 0
    except (
        OSError,
        json.JSONDecodeError,
        EvidenceViewAnalysisError,
        evidence.WorkspaceEvidenceError,
        blinded_view.BlindedViewError,
        recovery.RecoveryAnalysisError,
        analysis_base.AnalysisError,
        ValueError,
    ) as exc:
        report = {
            "status": "blocked",
            "amendment_id": AMENDMENT_ID,
            "reason": str(exc),
        }
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
