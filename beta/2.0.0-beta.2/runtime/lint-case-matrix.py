#!/usr/bin/env python3
"""Lint Beta.2 case coverage and provenance without reading sealed prompt content."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
DEFAULT_MATRIX = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"
DEFAULT_DEVELOPMENT = BETA_ROOT / "fixtures" / "development-cases.jsonl"
DEFAULT_SEALED = BETA_ROOT / "fixtures" / "sealed-shadow-index.json"
DEFAULT_REPLAY = BETA_ROOT / "fixtures" / "real-task-replay-index.json"
DEFAULT_PUBLIC = REPO_ROOT / "tests" / "judgment_benchmark_50_cases.jsonl"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_CONTENT_KEYS = {"prompt", "turns", "messages", "conversation", "content"}


class MatrixError(ValueError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        case_id = payload.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise MatrixError(f"{path}:{number} has no case_id")
        if case_id in ids:
            raise MatrixError(f"{path}:{number} duplicates {case_id}")
        ids.add(case_id)
    return ids


def _content_keys(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if key in FORBIDDEN_CONTENT_KEYS:
                found.append(path)
            found.extend(_content_keys(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_content_keys(child, f"{prefix}[{index}]"))
    return found


def _index_receipts(payload: Mapping[str, Any], label: str) -> dict[str, str]:
    if payload.get("content_retained_in_repository") is not False:
        raise MatrixError(f"{label} must declare content_retained_in_repository=false")
    exposed = _content_keys(payload)
    if exposed:
        raise MatrixError(f"{label} exposes forbidden content keys: {exposed}")
    receipts: dict[str, str] = {}
    for item in payload.get("cases", []):
        case_id = item.get("case_id")
        receipt = item.get("receipt_sha256")
        if not isinstance(case_id, str) or not SHA256_RE.fullmatch(str(receipt)):
            raise MatrixError(f"{label} has an invalid case receipt")
        if case_id in receipts:
            raise MatrixError(f"{label} duplicates {case_id}")
        receipts[case_id] = str(receipt)
    return receipts


def _tag_values(cases: Iterable[Mapping[str, Any]], prefix: str) -> set[str]:
    return {
        tag.removeprefix(prefix)
        for case in cases
        for tag in case.get("coverage_tags", [])
        if isinstance(tag, str) and tag.startswith(prefix)
    }


def _coverage(
    matrix: Mapping[str, Any],
    cases: list[Mapping[str, Any]],
) -> dict[str, dict[str, list[str]]]:
    requirements = matrix.get("coverage_requirements", {})
    observed = {
        "owners": {
            str(case.get("expected_execution_owner"))
            for case in cases
            if case.get("case_type") == "positive"
        },
        "primitives": {
            str(primitive)
            for case in cases
            for primitive in case.get("expected_primitive_obligations", [])
        },
        "lifecycle_paths": {str(case.get("lifecycle_path")) for case in cases},
        "near_negatives": _tag_values(cases, "near-negative:"),
        "anti_spiral_sequences": _tag_values(cases, "anti-spiral:"),
        "provenance_classes": {str(case.get("provenance")) for case in cases},
        "entry_modes": {str(case.get("entry_mode")) for case in cases},
    }
    report: dict[str, dict[str, list[str]]] = {}
    for dimension, required_values in requirements.items():
        required = {str(value) for value in required_values}
        actual = observed.get(dimension, set())
        report[dimension] = {
            "required": sorted(required),
            "observed": sorted(actual),
            "missing": sorted(required - actual),
        }
    return report


def validate(
    matrix: Mapping[str, Any],
    *,
    development_ids: set[str],
    public_ids: set[str],
    sealed_receipts: Mapping[str, str],
    replay_receipts: Mapping[str, str],
) -> dict[str, Any]:
    if matrix.get("schema_version") != "mindthus-beta2-case-matrix-v0.1":
        raise MatrixError("unsupported matrix schema_version")
    exposed = _content_keys(matrix)
    if exposed:
        raise MatrixError(f"matrix embeds source content instead of a locator: {exposed}")
    raw_cases = matrix.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise MatrixError("matrix.cases must be a non-empty array")
    cases: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    required_case_fields = {
        "case_id",
        "case_type",
        "provenance",
        "source",
        "entry_mode",
        "lifecycle_path",
        "expected_execution_owner",
        "accepted_execution_owners",
        "expected_primitive_obligations",
        "required_visible_action",
        "required_skill_loads",
        "allowed_skill_loads",
        "stay_asleep_expected",
        "expected_lifecycle_events",
        "evidence_first_expected",
        "contamination_risk",
        "coverage_tags",
    }
    for raw in raw_cases:
        if not isinstance(raw, Mapping):
            raise MatrixError("every matrix case must be an object")
        missing_fields = sorted(required_case_fields - raw.keys())
        case_id = str(raw.get("case_id") or "<missing>")
        if missing_fields:
            raise MatrixError(f"{case_id} misses fields: {missing_fields}")
        if case_id in seen:
            raise MatrixError(f"duplicate matrix case_id: {case_id}")
        seen.add(case_id)
        cases.append(raw)

        required_loads = set(raw.get("required_skill_loads", []))
        allowed_loads = set(raw.get("allowed_skill_loads", []))
        if not required_loads.issubset(allowed_loads):
            raise MatrixError(f"{case_id} required loads are not a subset of allowed loads")
        if raw.get("case_type") == "negative_control":
            if raw.get("stay_asleep_expected") is not True or required_loads:
                raise MatrixError(
                    f"{case_id} negative control must stay asleep with no required load"
                )
        if raw.get("evidence_first_expected") and "evidence_first" not in raw.get(
            "expected_primitive_obligations", []
        ):
            raise MatrixError(f"{case_id} evidence-first behavior lacks its obligation")

        source = raw.get("source")
        if not isinstance(source, Mapping):
            raise MatrixError(f"{case_id} source must be an object")
        locator = str(source.get("locator") or "")
        source_id = locator.rsplit("#", 1)[-1] if "#" in locator else ""
        provenance = raw.get("provenance")
        visible = source.get("implementation_visible")
        eligibility = source.get("run_eligibility")
        receipt = source.get("receipt_sha256")
        if provenance == "public-regression":
            if source_id not in public_ids or visible is not True or receipt is not None:
                raise MatrixError(f"{case_id} has an invalid public-regression source")
            if eligibility != "eligible":
                raise MatrixError(f"{case_id} public source must be eligible")
        elif provenance == "development":
            if source_id not in development_ids or visible is not True or receipt is not None:
                raise MatrixError(f"{case_id} has an invalid development source")
            if eligibility != "eligible":
                raise MatrixError(f"{case_id} development source must be eligible")
        elif provenance == "sealed-shadow":
            if visible is not False or eligibility != "requires-custodian-attestation":
                raise MatrixError(f"{case_id} sealed source visibility/eligibility is invalid")
            if sealed_receipts.get(source_id) != receipt:
                raise MatrixError(f"{case_id} sealed receipt does not match its external index")
        elif provenance == "real-task-replay":
            if visible is not False or eligibility != "requires-user-authorization":
                raise MatrixError(f"{case_id} replay source visibility/eligibility is invalid")
            if replay_receipts.get(source_id) != receipt:
                raise MatrixError(f"{case_id} replay receipt does not match its restricted index")
        else:
            raise MatrixError(f"{case_id} has unsupported provenance {provenance!r}")

    coverage = _coverage(matrix, cases)
    missing_coverage = {
        dimension: values["missing"]
        for dimension, values in coverage.items()
        if values["missing"]
    }
    if missing_coverage:
        raise MatrixError(f"coverage gaps: {missing_coverage}")
    if not any(
        len(case.get("expected_primitive_obligations", [])) > 1 for case in cases
    ):
        raise MatrixError("matrix has no multi-obligation case")
    if "genuine" not in _tag_values(cases, "owner-overlap:"):
        raise MatrixError("matrix has no genuine owner-overlap case")
    if not any("direct-owner-passive-intersection" in case.get("coverage_tags", []) for case in cases):
        raise MatrixError("matrix has no direct-owner/passive intersection")
    for owner in ("3l5s", "tplan"):
        if not any(
            case.get("case_type") == "positive"
            and case.get("expected_execution_owner") == owner
            for case in cases
        ):
            raise MatrixError(f"matrix lacks a positive {owner} owner case")

    provenance_counts = Counter(str(case.get("provenance")) for case in cases)
    eligibility_counts = Counter(
        str(case.get("source", {}).get("run_eligibility")) for case in cases
    )
    return {
        "schema_version": "mindthus-beta2-case-matrix-lint-report-v0.1",
        "status": "valid",
        "case_count": len(cases),
        "provenance_counts": dict(sorted(provenance_counts.items())),
        "run_eligibility_counts": dict(sorted(eligibility_counts.items())),
        "coverage": coverage,
        "multi_obligation_case_count": sum(
            1 for case in cases if len(case.get("expected_primitive_obligations", [])) > 1
        ),
        "negative_control_count": sum(
            1 for case in cases if case.get("case_type") == "negative_control"
        ),
        "sealed_or_replay_prompt_content_read": False,
        "claim_boundary": (
            "structural coverage only; sealed blindness and replay consent require external "
            "attestation before an authorized run"
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--development", type=Path, default=DEFAULT_DEVELOPMENT)
    parser.add_argument("--sealed-index", type=Path, default=DEFAULT_SEALED)
    parser.add_argument("--replay-index", type=Path, default=DEFAULT_REPLAY)
    parser.add_argument("--public-cases", type=Path, default=DEFAULT_PUBLIC)
    parser.add_argument("--report", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = validate(
            load_json(args.matrix),
            development_ids=load_jsonl_ids(args.development),
            public_ids=load_jsonl_ids(args.public_cases),
            sealed_receipts=_index_receipts(load_json(args.sealed_index), "sealed index"),
            replay_receipts=_index_receipts(load_json(args.replay_index), "replay index"),
        )
    except (OSError, json.JSONDecodeError, MatrixError) as exc:
        print(f"case-matrix lint failed: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
