#!/usr/bin/env python3
"""Continue frozen v0.4 with deterministic de-identified Judge candidate views."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import analyze_codex_evaluation_v04_blinded_view as blinded_analysis  # noqa: E402
import blinded_candidate_view_v04 as view  # noqa: E402
import run_real_codex_evaluation_v04 as base  # noqa: E402
import run_real_codex_evaluation_v04_judge_compat as compat  # noqa: E402


DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-blinded-view.1.json"
)
AMENDMENT_PATH = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-blinded-view.1.json"
)
ANALYZER = RUNTIME_ROOT / "analyze_codex_evaluation_v04_blinded_view.py"
AMENDMENT_ID = "0.4-blinded-view.1"


def amendment_root(out_dir: Path) -> Path:
    return out_dir / "recovery" / AMENDMENT_ID


def require(condition: bool, veto_id: str, reason: str) -> None:
    if not condition:
        raise base.EvaluationStop(veto_id, reason)


def copy_bound_source(source: Path, destination: Path, expected_sha256: str) -> None:
    require(source.is_file(), "blinded-view-source-drift", f"source is missing: {source}")
    require(
        base.sha256_file(source) == expected_sha256,
        "blinded-view-source-drift",
        f"source differs: {source}",
    )
    if destination.is_file():
        require(
            base.sha256_file(destination) == expected_sha256,
            "blinded-view-source-drift",
            f"source snapshot differs: {destination}",
        )
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.partial")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def attempt_receipts(out_dir: Path) -> list[dict[str, str]]:
    receipts: list[dict[str, str]] = []
    for path in sorted((out_dir / "judge-attempts").glob("**/attempt.json")):
        attempt = base.read_json(path)
        unsigned = dict(attempt)
        digest = unsigned.pop("attempt_digest", None)
        require(
            digest == base.canonical_sha256(unsigned),
            "untraceable-or-partial-artifact",
            f"Judge attempt digest differs: {path}",
        )
        receipts.append(
            {
                "path": str(path.relative_to(out_dir)),
                "attempt_digest": str(digest),
                "file_sha256": base.sha256_file(path),
            }
        )
    return receipts


def record_receipts(out_dir: Path) -> list[dict[str, str]]:
    receipts: list[dict[str, str]] = []
    for path in sorted((out_dir / "judge-records").glob("*/*.json")):
        record = base.read_json(path)
        unsigned = dict(record)
        digest = unsigned.pop("record_digest", None)
        require(
            digest == base.canonical_sha256(unsigned),
            "untraceable-or-partial-artifact",
            f"Judge record digest differs: {path}",
        )
        receipts.append(
            {
                "path": str(path.relative_to(out_dir)),
                "record_digest": str(digest),
                "file_sha256": base.sha256_file(path),
            }
        )
    return receipts


def exposure_scan(
    out_dir: Path, amendment: Mapping[str, Any]
) -> list[dict[str, str]]:
    paths = amendment["blinded_candidate_view"]["sensitive_paths"]
    items: list[dict[str, str]] = []
    for path in sorted((out_dir / "cells").glob("*/record.json")):
        record = base.completed_cell(out_dir, path.parent.name)
        require(
            record is not None,
            "blinded-view-source-drift",
            f"source generation cell disappeared: {path.parent.name}",
        )
        assert record is not None
        original = Path(record["answer_path"]).read_text(encoding="utf-8")
        blinded, transformations = view.transform_candidate(original, paths)
        view.assert_blind(blinded, paths)
        if transformations:
            items.append(
                {
                    "cell_id": str(record["cell_id"]),
                    "answer_sha256": str(record["answer_sha256"]),
                    "blinded_answer_sha256": view.text_sha256(blinded),
                }
            )
    items.sort(key=lambda item: item["cell_id"])
    return items


def validate_receipt_artifacts(
    out_dir: Path, receipts: Iterable[Mapping[str, Any]], digest_field: str
) -> None:
    for item in receipts:
        path = (out_dir / str(item["path"])).resolve()
        try:
            path.relative_to(out_dir.resolve())
        except ValueError as exc:
            raise base.EvaluationStop(
                "blinded-view-source-drift", "source receipt leaves run root"
            ) from exc
        require(
            path.is_file() and base.sha256_file(path) == item["file_sha256"],
            "blinded-view-source-drift",
            f"retained source artifact differs: {path}",
        )
        payload = base.read_json(path)
        unsigned = dict(payload)
        observed = unsigned.pop(digest_field, None)
        require(
            observed == item[digest_field] == base.canonical_sha256(unsigned),
            "blinded-view-source-drift",
            f"retained source digest differs: {path}",
        )


def ensure_source_snapshot(out_dir: Path, amendment: Mapping[str, Any]) -> dict[str, Any]:
    source = amendment["retained_source_run"]
    root = amendment_root(out_dir) / "pre-amendment"
    receipt_path = root / "receipt.json"
    run_state_copy = root / "run-state.json"
    stop_copy = root / "judge-compatibility-stop-report.json"
    if receipt_path.is_file():
        receipt = base.read_json(receipt_path)
        unsigned = dict(receipt)
        digest = unsigned.pop("receipt_digest", None)
        require(
            digest == base.canonical_sha256(unsigned),
            "blinded-view-source-drift",
            "blinded-view source snapshot digest differs",
        )
        require(
            base.sha256_file(run_state_copy) == source["run_state_sha256"]
            and base.sha256_file(stop_copy)
            == source["judge_compatibility_stop_report_sha256"],
            "blinded-view-source-drift",
            "blinded-view source snapshot files differ",
        )
        require(
            len(receipt.get("judge_attempts", [])) == source["judge_attempts"]
            and base.canonical_sha256(receipt["judge_attempts"])
            == source["judge_attempt_set_digest"]
            and len(receipt.get("judge_records", []))
            == source["completed_judge_records"]
            and base.canonical_sha256(receipt["judge_records"])
            == source["judge_record_set_digest"]
            and receipt.get("identifier_exposure_scan")
            == source["identifier_exposure_scan"]["items"],
            "blinded-view-source-drift",
            "blinded-view source snapshot bindings differ",
        )
        validate_receipt_artifacts(
            out_dir, receipt["judge_attempts"], "attempt_digest"
        )
        validate_receipt_artifacts(
            out_dir, receipt["judge_records"], "record_digest"
        )
        return receipt

    state_path = out_dir / "run-state.json"
    stop_path = out_dir / "recovery" / "0.4-judge-compat.1" / "stop-report.json"
    require(
        state_path.is_file()
        and base.sha256_file(state_path) == source["run_state_sha256"]
        and base.read_json(state_path).get("state_digest") == source["run_state_digest"],
        "blinded-view-source-drift",
        "pre-amendment run-state differs",
    )
    require(
        stop_path.is_file()
        and base.sha256_file(stop_path)
        == source["judge_compatibility_stop_report_sha256"],
        "blinded-view-source-drift",
        "pre-amendment stop report differs",
    )
    attempts = attempt_receipts(out_dir)
    records = record_receipts(out_dir)
    require(
        len(attempts) == source["judge_attempts"]
        and base.canonical_sha256(attempts) == source["judge_attempt_set_digest"],
        "blinded-view-source-drift",
        "pre-amendment Judge attempt set differs",
    )
    require(
        len(records) == source["completed_judge_records"]
        and base.canonical_sha256(records) == source["judge_record_set_digest"],
        "blinded-view-source-drift",
        "pre-amendment Judge record set differs",
    )
    scan = exposure_scan(out_dir, amendment)
    declared_scan = source["identifier_exposure_scan"]
    require(
        len(scan) == declared_scan["exposed_generation_outputs"]
        and scan == declared_scan["items"]
        and base.canonical_sha256(scan) == declared_scan["exposed_set_digest"],
        "blinded-view-source-drift",
        "pre-amendment identifier exposure scan differs",
    )
    timeout = source["timed_out_judge_attempt"]
    timeout_path = (
        out_dir
        / "judge-attempts"
        / timeout["blinded_output_id"]
        / f"slot-{timeout['slot']}"
        / f"attempt-{timeout['attempt']:02d}"
        / "attempt.json"
    )
    require(
        base.sha256_file(timeout_path) == timeout["attempt_file_sha256"],
        "blinded-view-source-drift",
        "timed-out Judge attempt differs",
    )
    copy_bound_source(state_path, run_state_copy, source["run_state_sha256"])
    copy_bound_source(
        stop_path, stop_copy, source["judge_compatibility_stop_report_sha256"]
    )
    receipt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-v0.4-blinded-view-source-snapshot-v0.1",
        "amendment_id": AMENDMENT_ID,
        "base_protocol_sha256": amendment["base_binding"]["protocol_sha256"],
        "run_state_sha256": source["run_state_sha256"],
        "stop_report_sha256": source["judge_compatibility_stop_report_sha256"],
        "judge_attempts": attempts,
        "judge_records": records,
        "identifier_exposure_scan": scan,
        "snapshotted_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_digest"] = base.canonical_sha256(receipt)
    base.write_atomic_json(receipt_path, receipt)
    return receipt


def write_candidate_view(
    *,
    out_dir: Path,
    output_id: str,
    cell_id: str,
    original: str,
    sensitive_paths: Iterable[str],
) -> str:
    blinded, transformations = view.transform_candidate(original, sensitive_paths)
    view.assert_blind(blinded, sensitive_paths)
    receipt_path = out_dir / "blinded-candidate-views" / f"{output_id}.json"
    if not transformations:
        require(
            blinded == original and not receipt_path.exists(),
            "blinded-view-transformation-drift",
            "identity Judge view unexpectedly has a receipt",
        )
        return blinded
    expected = view.view_receipt(
        amendment_id=AMENDMENT_ID,
        output_id=output_id,
        cell_id=cell_id,
        original=original,
        blinded=blinded,
        transformations=transformations,
    )
    if receipt_path.is_file():
        try:
            view.validate_view_receipt(base.read_json(receipt_path), expected)
        except view.BlindedViewError as exc:
            raise base.EvaluationStop(
                "blinded-view-transformation-drift", str(exc)
            ) from exc
    else:
        base.write_atomic_json(receipt_path, expected)
    return blinded


def write_blinded_input(
    *,
    out_dir: Path,
    output_id: str,
    raw_prompt: str,
    case: Mapping[str, Any],
    candidate: str,
) -> Path:
    payload = blinded_analysis.expected_input(
        output_id=output_id,
        raw_prompt=raw_prompt,
        contract=case["contract"],
        candidate=candidate,
    )
    path = out_dir / "judge-inputs" / f"{output_id}.json"
    require(
        not path.is_file() or base.read_json(path) == payload,
        "judge-environment-contamination",
        f"blinded Judge input changed: {output_id}",
    )
    if not path.is_file():
        base.write_atomic_json(path, payload)
    return path


def generate_cells(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    auth_report: Mapping[str, Any],
    authorization: Mapping[str, Any],
    protocol: Mapping[str, Any],
    manifests: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], int, int, int]:
    matrix = base.read_json(base.MATRIX_PATH)
    cases = base.source_cases(matrix)
    cells = base.expected_cells(protocol, args.phase)
    require(
        set(str(cell["case_id"]) for cell in cells).issubset(cases),
        "protocol-or-arm-drift",
        "one or more case sources are unavailable",
    )
    generation_calls, judge_calls, counted_tokens = base.observed_attempt_usage(out_dir)
    completed: list[dict[str, Any]] = []
    for cell in cells:
        case = cases[str(cell["case_id"])]
        manifest = manifests[str(cell["arm_id"])]
        forbidden = {
            str(out_dir),
            str(base.MATRIX_PATH.resolve()),
            str(base.DEVELOPMENT_CASES.resolve()),
            str(base.PUBLIC_CASES.resolve()),
            str(compat.COMPATIBLE_SCHEMA.resolve()),
            str(base.JUDGE_RUBRIC.resolve()),
        }
        for other_arm, other_manifest in manifests.items():
            if other_arm == cell["arm_id"]:
                continue
            forbidden.update(
                {
                    str(Path(other_manifest["host"]["home"]).resolve()),
                    str(Path(other_manifest["host"]["execution_root"]).resolve()),
                    str(Path(other_manifest["package"]["root"]).resolve()),
                }
            )
        record, new_calls, new_tokens = base.execute_generator_cell(
            cell=cell,
            case=case,
            manifest=manifest,
            authorization=authorization,
            protocol_sha256=auth_report["protocol_sha256"],
            out_dir=out_dir,
            timeout=args.timeout,
            generation_calls_used=generation_calls,
            forbidden_path_fragments=sorted(forbidden),
        )
        generation_calls += new_calls
        counted_tokens += new_tokens
        completed.append(record)
        require(
            counted_tokens <= authorization["token_or_cost_budget"]["maximum"],
            "authority-or-evidence-regression",
            "v0.4 measured token ceiling reached",
        )
        base.write_atomic_json(
            out_dir / "run-state.json",
            base.state_payload(
                phase=args.phase,
                status="generating",
                authorization_report=auth_report,
                generation_calls=generation_calls,
                judge_calls=judge_calls,
                counted_tokens=counted_tokens,
                generation_outputs=len(completed),
                judge_records=0,
            ),
        )
    return completed, cases, generation_calls, judge_calls, counted_tokens


def judge_cells(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    auth_report: Mapping[str, Any],
    authorization: Mapping[str, Any],
    protocol: Mapping[str, Any],
    manifests: Mapping[str, Mapping[str, Any]],
    records: list[dict[str, Any]],
    cases: Mapping[str, Mapping[str, Any]],
    generation_calls: int,
    judge_calls: int,
    counted_tokens: int,
    amendment: Mapping[str, Any],
) -> tuple[int, int]:
    auth_source = args.auth_source.resolve()
    require(
        auth_source.is_file(),
        "judge-environment-contamination",
        "Codex auth source is unavailable",
    )
    environments = {
        slot: base.judge_environment(
            out_dir=out_dir,
            runtime_root=args.runtime_root.resolve(),
            auth_source=auth_source,
            slot=slot,
        )
        for slot in (1, 2)
    }
    rubric = base.read_json(base.JUDGE_RUBRIC)
    completed_judges = 0
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    sensitive_paths = amendment["blinded_candidate_view"]["sensitive_paths"]
    for record in base.judge_order(records, seed):
        cell_id = str(record["cell_id"])
        case = cases[str(record["cell_key"]["case_id"])]
        original = Path(record["answer_path"]).read_text(encoding="utf-8")
        output_id = base.judge_identity(auth_report["protocol_sha256"], cell_id)
        candidate = write_candidate_view(
            out_dir=out_dir,
            output_id=output_id,
            cell_id=cell_id,
            original=original,
            sensitive_paths=sensitive_paths,
        )
        raw_prompt = base.user_prompt(case["source"])
        input_path = write_blinded_input(
            out_dir=out_dir,
            output_id=output_id,
            raw_prompt=raw_prompt,
            case=case,
            candidate=candidate,
        )
        input_digest = str(base.read_json(input_path)["input_digest"])
        prompt = base.judge_prompt(
            rubric=rubric,
            case=case,
            prompt=raw_prompt,
            candidate=candidate,
            blinded_output_id=output_id,
        )
        needed = sum(
            base.existing_judge_record(out_dir, output_id, slot) is None
            for slot in (1, 2)
        )
        require(
            judge_calls + (2 * needed) <= authorization["maximum_judge_calls"],
            "authority-or-evidence-regression",
            "Judge call ceiling reached",
        )
        futures: list[
            concurrent.futures.Future[tuple[dict[str, Any], int, int]]
        ] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            for slot in (1, 2):
                futures.append(
                    executor.submit(
                        compat.compatible_standard_slot,
                        slot=slot,
                        output_id=output_id,
                        prompt=prompt,
                        blinded_input_digest=input_digest,
                        case=case,
                        environment=environments[slot],
                        authorization=authorization,
                        out_dir=out_dir,
                        timeout=args.timeout,
                    )
                )
            results = [future.result() for future in futures]
        for _judge_record, new_calls, new_tokens in results:
            judge_calls += new_calls
            counted_tokens += new_tokens
        completed_judges += 2
        require(
            counted_tokens <= authorization["token_or_cost_budget"]["maximum"],
            "authority-or-evidence-regression",
            "v0.4 measured token ceiling reached",
        )
        base.write_atomic_json(
            out_dir / "run-state.json",
            base.state_payload(
                phase=args.phase,
                status="judging",
                authorization_report=auth_report,
                generation_calls=generation_calls,
                judge_calls=judge_calls,
                counted_tokens=counted_tokens,
                generation_outputs=len(records),
                judge_records=completed_judges,
            ),
        )
    return judge_calls, counted_tokens


def run_blinded_view(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base.scan_partial_artifacts(out_dir)
    auth_report, authorization, protocol = base.authorized_context(
        args.authorization.resolve()
    )
    amendment = base.read_json(AMENDMENT_PATH)
    require(
        auth_report.get("blinded_view_protocol_sha256")
        == base.sha256_file(AMENDMENT_PATH),
        "authority-or-evidence-regression",
        "blinded-view authorization differs",
    )
    manifests = base.verify_arm_set(
        [path.resolve() for path in args.arm_manifest], authorization
    )
    base.JUDGE_SCHEMA = compat.COMPATIBLE_SCHEMA
    ensure_source_snapshot(out_dir, amendment)
    compat.ensure_failed_records(
        out_dir=out_dir,
        manifests=manifests,
        base_protocol=protocol,
        amendment=base.read_json(compat.COMPAT_PROTOCOL),
        authorization=authorization,
        runtime_root=args.runtime_root.resolve(),
        auth_source=args.auth_source.resolve(),
        timeout=args.timeout,
        allow_model_execution=not args.preflight_only,
    )
    if args.preflight_only:
        return {
            "status": "ready",
            "amendment_id": AMENDMENT_ID,
            "retained_generation_outputs": 15,
            "retained_judge_attempts": 17,
            "retained_judge_records": 12,
            "identifier_exposed_outputs": 3,
            "model_execution_performed": False,
            "next_phase": args.phase,
        }, 0
    records, cases, generation_calls, judge_calls, counted_tokens = generate_cells(
        args=args,
        out_dir=out_dir,
        auth_report=auth_report,
        authorization=authorization,
        protocol=protocol,
        manifests=manifests,
    )
    judge_calls, counted_tokens = judge_cells(
        args=args,
        out_dir=out_dir,
        auth_report=auth_report,
        authorization=authorization,
        protocol=protocol,
        manifests=manifests,
        records=records,
        cases=cases,
        generation_calls=generation_calls,
        judge_calls=judge_calls,
        counted_tokens=counted_tokens,
        amendment=amendment,
    )
    analysis = base.run_json(
        [
            "python3",
            str(ANALYZER),
            "--phase",
            args.phase,
            "--run-dir",
            str(out_dir),
            "--authorization",
            str(args.authorization.resolve()),
        ],
        label=f"{args.phase} blinded-view analysis",
    )
    status = str(analysis["status"])
    base.write_atomic_json(
        out_dir / "run-state.json",
        base.state_payload(
            phase=args.phase,
            status=status,
            authorization_report=auth_report,
            generation_calls=generation_calls,
            judge_calls=judge_calls,
            counted_tokens=counted_tokens,
            generation_outputs=len(records),
            judge_records=len(records) * 2,
            veto_id=analysis.get("veto_id"),
            reason=analysis.get("reason"),
        ),
    )
    completion: dict[str, Any] = {
        "schema_version": "mindthus-beta2-v0.4-blinded-view-completion-v0.1",
        "amendment_id": AMENDMENT_ID,
        "phase": args.phase,
        "analysis_status": status,
        "generation_calls": generation_calls,
        "judge_calls": judge_calls,
        "measured_counted_tokens": counted_tokens,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    completion["completion_digest"] = base.canonical_sha256(completion)
    base.write_atomic_json(
        amendment_root(out_dir) / f"{args.phase}-completion.json", completion
    )
    return analysis, 0 if status in {"passed", "matched-complete"} else 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("smoke", "matched"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--arm-manifest", type=Path, action="append", required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument(
        "--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json"
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.timeout != 1800:
        parser.error("the frozen blinded-view timeout is exactly 1800 seconds")
    return args


def main() -> int:
    args = parse_args()
    try:
        report, code = run_blinded_view(args)
    except base.EvaluationStop as exc:
        report = {
            "status": "stopped",
            "amendment_id": AMENDMENT_ID,
            "veto_id": exc.veto_id,
            "reason": exc.reason,
        }
        code = 2
        if args.out_dir.exists():
            base.write_atomic_json(
                amendment_root(args.out_dir.resolve()) / "stop-report.json", report
            )
    except (OSError, json.JSONDecodeError, ValueError, view.BlindedViewError) as exc:
        report = {"status": "blocked", "amendment_id": AMENDMENT_ID, "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
