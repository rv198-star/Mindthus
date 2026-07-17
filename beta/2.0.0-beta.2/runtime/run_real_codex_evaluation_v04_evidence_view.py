#!/usr/bin/env python3
"""Continue v0.4 with a frozen arm-neutral workspace-evidence Judge view."""

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
import analyze_codex_evaluation_v04_evidence_view as evidence_analysis  # noqa: E402
import blinded_candidate_view_v04 as blinded_view  # noqa: E402
import run_real_codex_evaluation_v04 as base  # noqa: E402
import run_real_codex_evaluation_v04_blinded_view as blinded_runner  # noqa: E402
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
ANALYZER = RUNTIME_ROOT / "analyze_codex_evaluation_v04_evidence_view.py"
AMENDMENT_ID = "0.4-evidence-view.1"


def amendment_root(out_dir: Path) -> Path:
    return out_dir / "recovery" / AMENDMENT_ID


def require(condition: bool, veto_id: str, reason: str) -> None:
    if not condition:
        raise base.EvaluationStop(veto_id, reason)


def artifact_receipts(
    out_dir: Path, pattern: str, digest_field: str
) -> list[dict[str, str]]:
    receipts: list[dict[str, str]] = []
    for path in sorted(out_dir.glob(pattern)):
        payload = base.read_json(path)
        observed = payload.get(digest_field)
        if digest_field != "input_digest":
            unsigned = dict(payload)
            unsigned.pop(digest_field, None)
            require(
                observed == base.canonical_sha256(unsigned),
                "evidence-view-source-drift",
                f"source digest differs: {path}",
            )
        receipts.append(
            {
                "path": str(path.relative_to(out_dir)),
                digest_field: str(observed),
                "file_sha256": base.sha256_file(path),
            }
        )
    return receipts


def _validate_receipts(
    out_dir: Path, receipts: Iterable[Mapping[str, Any]], digest_field: str
) -> None:
    for item in receipts:
        path = (out_dir / str(item["path"])).resolve()
        try:
            path.relative_to(out_dir.resolve())
        except ValueError as exc:
            raise base.EvaluationStop(
                "evidence-view-source-drift", "source receipt leaves run root"
            ) from exc
        require(
            path.is_file() and base.sha256_file(path) == item["file_sha256"],
            "evidence-view-source-drift",
            f"retained source artifact differs: {path}",
        )
        payload = base.read_json(path)
        require(
            payload.get(digest_field) == item[digest_field],
            "evidence-view-source-drift",
            f"retained source digest differs: {path}",
        )


def _copy_bound(source: Path, destination: Path, expected_sha256: str) -> None:
    require(
        source.is_file() and base.sha256_file(source) == expected_sha256,
        "evidence-view-source-drift",
        f"source snapshot input differs: {source}",
    )
    if destination.is_file():
        require(
            base.sha256_file(destination) == expected_sha256,
            "evidence-view-source-drift",
            f"source snapshot copy differs: {destination}",
        )
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.partial")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def _source_sets(out_dir: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "cells": artifact_receipts(out_dir, "cells/*/record.json", "record_digest"),
        "generation_attempts": artifact_receipts(
            out_dir, "generation-attempts/**/attempt.json", "attempt_digest"
        ),
        "judge_attempts": artifact_receipts(
            out_dir, "judge-attempts/**/attempt.json", "attempt_digest"
        ),
        "judge_records": artifact_receipts(
            out_dir, "judge-records/*/*.json", "record_digest"
        ),
        "judge_inputs": artifact_receipts(
            out_dir, "judge-inputs/*.json", "input_digest"
        ),
        "blinded_views": artifact_receipts(
            out_dir, "blinded-candidate-views/*.json", "receipt_digest"
        ),
    }


def _validate_diagnosed_events(
    out_dir: Path, amendment: Mapping[str, Any]
) -> None:
    for item in amendment["diagnosis"]["affected_cells"]:
        record = base.completed_cell(out_dir, str(item["cell_id"]))
        require(
            record is not None
            and record.get("answer_sha256") == item["answer_sha256"]
            and record.get("generation_attempt", {}).get("attempt_digest")
            == item["generation_attempt_digest"],
            "evidence-view-source-drift",
            f"diagnosed cell differs: {item['cell_id']}",
        )
        assert record is not None
        attempt_path = Path(str(record["generation_attempt"]["path"]))
        attempt = base.read_json(attempt_path / "attempt.json")
        require(
            attempt.get("events_sha256") == item["events_sha256"]
            and base.sha256_file(attempt_path / "events.jsonl")
            == item["events_sha256"],
            "evidence-view-source-drift",
            f"diagnosed event trace differs: {item['cell_id']}",
        )


def ensure_source_snapshot(
    out_dir: Path, amendment: Mapping[str, Any]
) -> dict[str, Any]:
    source = amendment["retained_source_run"]
    root = amendment_root(out_dir) / "pre-amendment"
    receipt_path = root / "receipt.json"
    copies = {
        "run-state.json": source["run_state_sha256"],
        "smoke-analysis.json": source["smoke_analysis_sha256"],
        "smoke-completion.json": source["smoke_completion_sha256"],
    }
    if receipt_path.is_file():
        receipt = base.read_json(receipt_path)
        unsigned = dict(receipt)
        digest = unsigned.pop("receipt_digest", None)
        require(
            digest == base.canonical_sha256(unsigned),
            "evidence-view-source-drift",
            "source snapshot receipt differs",
        )
        for name, expected in copies.items():
            require(
                (root / name).is_file()
                and base.sha256_file(root / name) == expected,
                "evidence-view-source-drift",
                f"source snapshot copy differs: {name}",
            )
        for name, digest_field in (
            ("cells", "record_digest"),
            ("generation_attempts", "attempt_digest"),
            ("judge_attempts", "attempt_digest"),
            ("judge_records", "record_digest"),
            ("judge_inputs", "input_digest"),
            ("blinded_views", "receipt_digest"),
        ):
            _validate_receipts(out_dir, receipt[name], digest_field)
        _validate_diagnosed_events(out_dir, amendment)
        return receipt

    run_state = out_dir / "run-state.json"
    smoke_analysis = out_dir / "smoke-analysis.json"
    smoke_completion = (
        out_dir / "recovery" / "0.4-blinded-view.1" / "smoke-completion.json"
    )
    require(
        run_state.is_file()
        and base.sha256_file(run_state) == source["run_state_sha256"]
        and base.read_json(run_state).get("state_digest")
        == source["run_state_digest"],
        "evidence-view-source-drift",
        "source run-state differs",
    )
    require(
        smoke_analysis.is_file()
        and base.sha256_file(smoke_analysis) == source["smoke_analysis_sha256"],
        "evidence-view-source-drift",
        "source smoke analysis differs",
    )
    require(
        smoke_completion.is_file()
        and base.sha256_file(smoke_completion) == source["smoke_completion_sha256"]
        and base.read_json(smoke_completion).get("completion_digest")
        == source["smoke_completion_digest"],
        "evidence-view-source-drift",
        "source smoke completion differs",
    )
    sets = _source_sets(out_dir)
    expectations = {
        "cells": (source["completed_generation_outputs"], source["cell_set_digest"]),
        "generation_attempts": (
            source["generation_attempts"],
            source["generation_attempt_set_digest"],
        ),
        "judge_attempts": (source["judge_attempts"], source["judge_attempt_set_digest"]),
        "judge_records": (
            source["completed_judge_records"],
            source["judge_record_set_digest"],
        ),
        "judge_inputs": (source["judge_inputs"], source["judge_input_set_digest"]),
        "blinded_views": (
            source["blinded_candidate_view_receipts"],
            source["blinded_view_receipt_set_digest"],
        ),
    }
    for name, (count, digest) in expectations.items():
        require(
            len(sets[name]) == count
            and base.canonical_sha256(sets[name]) == digest,
            "evidence-view-source-drift",
            f"source {name} set differs",
        )
    _validate_diagnosed_events(out_dir, amendment)
    _copy_bound(run_state, root / "run-state.json", source["run_state_sha256"])
    _copy_bound(
        smoke_analysis,
        root / "smoke-analysis.json",
        source["smoke_analysis_sha256"],
    )
    _copy_bound(
        smoke_completion,
        root / "smoke-completion.json",
        source["smoke_completion_sha256"],
    )
    receipt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-v0.4-evidence-view-source-snapshot-v0.1",
        "amendment_id": AMENDMENT_ID,
        "base_protocol_sha256": amendment["base_binding"]["protocol_sha256"],
        **sets,
        "snapshotted_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_digest"] = base.canonical_sha256(receipt)
    base.write_atomic_json(receipt_path, receipt)
    return receipt


def ensure_capsule(
    out_dir: Path, manifests: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    capsule = evidence.build_capsule(manifests)
    path = evidence_analysis.capsule_path(out_dir)
    require(
        not path.is_file() or base.read_json(path) == capsule,
        "workspace-evidence-drift",
        "workspace evidence capsule differs",
    )
    if not path.is_file():
        base.write_atomic_json(path, capsule)
    return capsule


def write_candidate_view(
    *,
    out_dir: Path,
    output_id: str,
    cell_id: str,
    original: str,
    sensitive_paths: Iterable[str],
    evidence_view: bool,
) -> str:
    if not evidence_view:
        return blinded_runner.write_candidate_view(
            out_dir=out_dir,
            output_id=output_id,
            cell_id=cell_id,
            original=original,
            sensitive_paths=sensitive_paths,
        )
    candidate, transformations = blinded_view.transform_candidate(
        original, sensitive_paths
    )
    blinded_view.assert_blind(candidate, sensitive_paths)
    receipt_path = out_dir / "blinded-candidate-views" / f"{output_id}.json"
    if not transformations:
        require(
            candidate == original and not receipt_path.exists(),
            "blinded-view-transformation-drift",
            "identity evidence view unexpectedly has a receipt",
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
    if receipt_path.is_file():
        try:
            blinded_view.validate_view_receipt(
                base.read_json(receipt_path), expected
            )
        except blinded_view.BlindedViewError as exc:
            raise base.EvaluationStop(
                "blinded-view-transformation-drift", str(exc)
            ) from exc
    else:
        base.write_atomic_json(receipt_path, expected)
    return candidate


def write_judge_input(
    *,
    out_dir: Path,
    output_id: str,
    raw_prompt: str,
    case: Mapping[str, Any],
    candidate: str,
    capsule: Mapping[str, Any],
    evidence_view: bool,
) -> tuple[Path, str]:
    if evidence_view:
        payload = evidence.expected_input(
            output_id=output_id,
            raw_prompt=raw_prompt,
            contract=case["contract"],
            candidate=candidate,
            capsule=capsule,
        )
        prompt = evidence.judge_prompt(
            rubric=base.read_json(base.JUDGE_RUBRIC),
            case=case,
            prompt=raw_prompt,
            candidate=candidate,
            blinded_output_id=output_id,
            capsule=capsule,
        )
    else:
        payload = blinded_analysis.expected_input(
            output_id=output_id,
            raw_prompt=raw_prompt,
            contract=case["contract"],
            candidate=candidate,
        )
        prompt = base.judge_prompt(
            rubric=base.read_json(base.JUDGE_RUBRIC),
            case=case,
            prompt=raw_prompt,
            candidate=candidate,
            blinded_output_id=output_id,
        )
    path = out_dir / "judge-inputs" / f"{output_id}.json"
    require(
        not path.is_file() or base.read_json(path) == payload,
        "judge-environment-contamination",
        f"Judge input changed: {output_id}",
    )
    if not path.is_file():
        base.write_atomic_json(path, payload)
    return path, prompt


def judge_cells(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    auth_report: Mapping[str, Any],
    authorization: Mapping[str, Any],
    protocol: Mapping[str, Any],
    records: list[dict[str, Any]],
    cases: Mapping[str, Mapping[str, Any]],
    generation_calls: int,
    judge_calls: int,
    counted_tokens: int,
    amendment: Mapping[str, Any],
    capsule: Mapping[str, Any],
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
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    sensitive_paths = base.read_json(BLINDED_AMENDMENT_PATH)[
        "blinded_candidate_view"
    ]["sensitive_paths"]
    amendment_sha256 = base.sha256_file(AMENDMENT_PATH)
    completed_active_records = 0
    for record in base.judge_order(records, seed):
        cell_id = str(record["cell_id"])
        case = cases[str(record["cell_key"]["case_id"])]
        original = Path(str(record["answer_path"])).read_text(encoding="utf-8")
        blinded, _trace = blinded_view.transform_candidate(original, sensitive_paths)
        needs_evidence = evidence.requires_workspace_evidence(blinded)
        output_id = (
            evidence.evidence_identity(amendment_sha256, cell_id)
            if needs_evidence
            else base.judge_identity(auth_report["protocol_sha256"], cell_id)
        )
        candidate = write_candidate_view(
            out_dir=out_dir,
            output_id=output_id,
            cell_id=cell_id,
            original=original,
            sensitive_paths=sensitive_paths,
            evidence_view=needs_evidence,
        )
        raw_prompt = base.user_prompt(case["source"])
        input_path, prompt = write_judge_input(
            out_dir=out_dir,
            output_id=output_id,
            raw_prompt=raw_prompt,
            case=case,
            candidate=candidate,
            capsule=capsule,
            evidence_view=needs_evidence,
        )
        input_digest = str(base.read_json(input_path)["input_digest"])
        needed = sum(
            base.existing_judge_record(out_dir, output_id, slot) is None
            for slot in (1, 2)
        )
        require(
            judge_calls + (2 * needed) <= authorization["maximum_judge_calls"],
            "authority-or-evidence-regression",
            "Judge call ceiling cannot preserve one retry per missing slot",
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
        completed_active_records += 2
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
                judge_records=completed_active_records,
            ),
        )
    return judge_calls, counted_tokens


def run_evidence_view(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base.scan_partial_artifacts(out_dir)
    auth_report, authorization, protocol = base.authorized_context(
        args.authorization.resolve()
    )
    amendment = base.read_json(AMENDMENT_PATH)
    require(
        auth_report.get("evidence_view_protocol_sha256")
        == base.sha256_file(AMENDMENT_PATH),
        "authority-or-evidence-regression",
        "evidence-view authorization differs",
    )
    manifests = base.verify_arm_set(
        [path.resolve() for path in args.arm_manifest], authorization
    )
    base.JUDGE_SCHEMA = compat.COMPATIBLE_SCHEMA
    ensure_source_snapshot(out_dir, amendment)
    capsule = ensure_capsule(out_dir, manifests)
    if args.preflight_only:
        return {
            "status": "ready",
            "amendment_id": AMENDMENT_ID,
            "retained_generation_outputs": 15,
            "retained_judge_attempts": 36,
            "retained_judge_records": 30,
            "retrospective_triggered_outputs": 3,
            "retrospective_rejudge_records": 6,
            "workspace_evidence_capsule_digest": capsule["capsule_digest"],
            "model_execution_performed": False,
            "next_phase": args.phase,
        }, 0
    records, cases, generation_calls, judge_calls, counted_tokens = (
        blinded_runner.generate_cells(
            args=args,
            out_dir=out_dir,
            auth_report=auth_report,
            authorization=authorization,
            protocol=protocol,
            manifests=manifests,
        )
    )
    judge_calls, counted_tokens = judge_cells(
        args=args,
        out_dir=out_dir,
        auth_report=auth_report,
        authorization=authorization,
        protocol=protocol,
        records=records,
        cases=cases,
        generation_calls=generation_calls,
        judge_calls=judge_calls,
        counted_tokens=counted_tokens,
        amendment=amendment,
        capsule=capsule,
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
        label=f"{args.phase} workspace-evidence analysis",
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
        "schema_version": "mindthus-beta2-v0.4-evidence-view-completion-v0.1",
        "amendment_id": AMENDMENT_ID,
        "phase": args.phase,
        "analysis_status": status,
        "generation_calls": generation_calls,
        "judge_calls": judge_calls,
        "measured_counted_tokens": counted_tokens,
        "active_judge_records": len(records) * 2,
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
        parser.error("the frozen evidence-view timeout is exactly 1800 seconds")
    return args


def main() -> int:
    args = parse_args()
    try:
        report, code = run_evidence_view(args)
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
    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
        blinded_view.BlindedViewError,
        evidence.WorkspaceEvidenceError,
    ) as exc:
        report = {"status": "blocked", "amendment_id": AMENDMENT_ID, "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
