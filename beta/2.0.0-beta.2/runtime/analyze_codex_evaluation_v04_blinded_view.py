#!/usr/bin/env python3
"""Analyze v0.4 using deterministic de-identified Judge candidate views."""

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

import analyze_codex_evaluation_v04 as base  # noqa: E402
import analyze_codex_evaluation_v04_recovery as recovery  # noqa: E402
import blinded_candidate_view_v04 as view  # noqa: E402
import run_real_codex_evaluation_v04 as runner  # noqa: E402


DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-blinded-view.1.json"
)
AMENDMENT_PATH = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.json"
)
AMENDMENT_ID = "0.4-blinded-view.1"


class BlindedViewAnalysisError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise BlindedViewAnalysisError(reason)


def expected_input(
    *,
    output_id: str,
    raw_prompt: str,
    contract: Mapping[str, Any],
    candidate: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-blinded-judge-input-v0.4",
        "blinded_output_id": output_id,
        "user_prompt": raw_prompt,
        "case_contract": {
            "case_type": contract["case_type"],
            "entry_mode": contract["entry_mode"],
            "accepted_execution_owners": contract["accepted_execution_owners"],
            "expected_primitive_obligations": contract[
                "expected_primitive_obligations"
            ],
            "required_visible_action": contract["required_visible_action"],
            "stay_asleep_expected": contract["stay_asleep_expected"],
        },
        "candidate_final_answer": candidate,
        "arm_label_present": False,
        "generator_path_present": False,
        "runtime_telemetry_present": False,
    }
    payload["input_digest"] = runner.canonical_sha256(payload)
    return payload


def validate_candidate_view(
    *,
    run_dir: Path,
    output_id: str,
    cell_id: str,
    original: str,
    sensitive_paths: Iterable[str],
) -> tuple[str, Path | None]:
    blinded, transformations = view.transform_candidate(original, sensitive_paths)
    view.assert_blind(blinded, sensitive_paths)
    receipt_path = run_dir / "blinded-candidate-views" / f"{output_id}.json"
    if not transformations:
        require(
            blinded == original and not receipt_path.exists(),
            "identity Judge view unexpectedly has a transformation receipt",
        )
        return blinded, None
    expected = view.view_receipt(
        amendment_id=AMENDMENT_ID,
        output_id=output_id,
        cell_id=cell_id,
        original=original,
        blinded=blinded,
        transformations=transformations,
    )
    require(receipt_path.is_file(), f"blinded candidate view receipt is missing: {output_id}")
    try:
        view.validate_view_receipt(runner.read_json(receipt_path), expected)
    except view.BlindedViewError as exc:
        raise BlindedViewAnalysisError(str(exc)) from exc
    return blinded, receipt_path.resolve()


def load_judges(
    run_dir: Path,
    protocol_sha256: str,
    cells: Iterable[Mapping[str, Any]],
    cases: Mapping[str, Mapping[str, Any]],
) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    amendment = runner.read_json(AMENDMENT_PATH)
    sensitive_paths = amendment["blinded_candidate_view"]["sensitive_paths"]
    results: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    expected_record_paths: set[Path] = set()
    expected_view_receipts: set[Path] = set()
    rubric = runner.read_json(runner.JUDGE_RUBRIC)
    for cell in cells:
        cell_id = str(cell["cell_id"])
        output_id = runner.judge_identity(protocol_sha256, cell_id)
        case_id = str(cell["cell_key"]["case_id"])
        case = cases[case_id]
        original = Path(str(cell["answer_path"])).read_text(encoding="utf-8")
        candidate, receipt_path = validate_candidate_view(
            run_dir=run_dir,
            output_id=output_id,
            cell_id=cell_id,
            original=original,
            sensitive_paths=sensitive_paths,
        )
        if receipt_path is not None:
            expected_view_receipts.add(receipt_path)
        raw_prompt = runner.user_prompt(case["source"])
        contract = case["contract"]
        expected = expected_input(
            output_id=output_id,
            raw_prompt=raw_prompt,
            contract=contract,
            candidate=candidate,
        )
        input_path = run_dir / "judge-inputs" / f"{output_id}.json"
        require(
            input_path.is_file() and runner.read_json(input_path) == expected,
            f"blinded Judge input differs: {output_id}",
        )
        prompt_digest = hashlib.sha256(
            runner.judge_prompt(
                rubric=rubric,
                case=case,
                prompt=raw_prompt,
                candidate=candidate,
                blinded_output_id=output_id,
            ).encode("utf-8")
        ).hexdigest()
        records: list[dict[str, Any]] = []
        for slot in (1, 2):
            path = run_dir / "judge-records" / output_id / f"judge-{slot}.json"
            expected_record_paths.add(path.resolve())
            try:
                record = runner.existing_judge_record(run_dir, output_id, slot)
            except runner.EvaluationStop as exc:
                raise BlindedViewAnalysisError(exc.reason) from exc
            require(record is not None, f"missing Judge record: {output_id}/slot-{slot}")
            assert record is not None
            require(
                record.get("blinded_output_id") == output_id
                and record.get("judge_slot") == slot,
                "Judge identity differs",
            )
            environment_path = (
                run_dir / "judge-homes" / f"slot-{slot}" / "environment.json"
            )
            require(environment_path.is_file(), f"Judge environment is missing: slot-{slot}")
            environment = runner.read_json(environment_path)
            base.verify_digest(environment, "environment_digest", "Judge environment")
            require(
                environment.get("slot") == slot
                and environment.get("active_forbidden_plugins") == []
                and environment.get("generator_home_access_granted") is False
                and record.get("environment_digest")
                == environment.get("environment_digest"),
                "Judge environment binding differs",
            )
            require(
                record.get("blinded_input_digest") == expected["input_digest"]
                and record.get("judge_prompt_sha256") == prompt_digest,
                "Judge prompt/input binding differs",
            )
            attempt_number = int(record["attempt"])
            raw_output = runner.read_json(
                run_dir
                / "judge-attempts"
                / output_id
                / f"slot-{slot}"
                / f"attempt-{attempt_number:02d}"
                / "judge-output.json"
            )
            require(
                isinstance(raw_output, Mapping)
                and runner.validate_judge_output(raw_output, case)
                == record.get("verdict"),
                "Judge normalized verdict differs from retained output",
            )
            records.append(record)
        results[cell_id] = (records[0], records[1])
    observed_record_paths = {
        path.resolve() for path in (run_dir / "judge-records").glob("*/*.json")
    }
    require(
        observed_record_paths == expected_record_paths,
        "Judge record set contains missing or unexpected artifacts",
    )
    observed_view_receipts = {
        path.resolve()
        for path in (run_dir / "blinded-candidate-views").glob("*.json")
    }
    require(
        observed_view_receipts == expected_view_receipts,
        "blinded candidate view receipt set differs",
    )
    return results


def analyze(phase: str, run_dir: Path, authorization_path: Path) -> dict[str, Any]:
    base.load_judges = load_judges
    recovery.base.load_judges = load_judges
    report = recovery.analyze(phase, run_dir, authorization_path)
    amendment = runner.read_json(AMENDMENT_PATH)
    receipts = sorted((run_dir / "blinded-candidate-views").glob("*.json"))
    report["blinded_view_amendment_id"] = AMENDMENT_ID
    report["candidate_view_deidentification"] = {
        "non_identity_views": len(receipts),
        "original_answers_mutated": False,
        "generation_retries_for_identifier_exposure": 0,
        "receipt_set_digest": runner.canonical_sha256(
            [
                {
                    "blinded_output_id": runner.read_json(path)["blinded_output_id"],
                    "receipt_digest": runner.read_json(path)["receipt_digest"],
                    "file_sha256": runner.sha256_file(path),
                }
                for path in receipts
            ]
        ),
        "transformation_contract": amendment["blinded_candidate_view"]["scope"],
    }
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
        + "; Judge candidate views deterministically remove evaluation-only identifiers "
        "while original answers remain immutable"
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
            args.run_dir.resolve() / f"{args.phase}-analysis.json", report
        )
        code = 0
    except (
        OSError,
        json.JSONDecodeError,
        BlindedViewAnalysisError,
        view.BlindedViewError,
        recovery.RecoveryAnalysisError,
        base.AnalysisError,
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
