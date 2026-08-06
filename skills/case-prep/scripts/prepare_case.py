#!/usr/bin/env python3
"""Prepare a review-required Mindthus case, TPlan packet, or case collection."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Sequence

from case_prep_core import (
    CASE_TYPES,
    TPLAN_FOCI,
    CasePrepError,
    _excerpt_arg,
    prepare_benchmark_case,
    prepare_case_collection,
    prepare_judgment_case,
    prepare_tplan_case,
)


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "mindthus-case-exports",
    )
    parser.add_argument("--case-id", default=None)
    parser.add_argument("--excerpt", action="append", type=_excerpt_arg, default=[])
    parser.add_argument("--confirm-excerpts-redacted", action="store_true")
    parser.add_argument("--json", action="store_true")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)

    judgment = sub.add_parser("judgment")
    _common(judgment)
    judgment.add_argument("--trace", type=Path, required=True)
    judgment.add_argument("--summary", type=Path, required=True)
    judgment.add_argument("--case-type", choices=sorted(CASE_TYPES), required=True)
    judgment.add_argument("--source-client", default=None)
    judgment.add_argument("--source-method", default=None)
    judgment.add_argument("--benchmark-case-id", default=None)
    judgment.add_argument("--related-test-id", default=None)
    judgment.add_argument("--related-issue", default=None)

    benchmark = sub.add_parser("benchmark")
    _common(benchmark)
    benchmark.add_argument("--run-dir", type=Path, required=True)
    benchmark.add_argument("--benchmark-case-id", required=True)
    benchmark.add_argument("--case-type", choices=sorted(CASE_TYPES), default=None)

    tplan = sub.add_parser("tplan")
    _common(tplan)
    tplan.add_argument("--mission-dir", type=Path, required=True)
    tplan.add_argument("--focus", choices=sorted(TPLAN_FOCI), default="auto")
    tplan.add_argument("--judgment-trace", type=Path, default=None)

    collection = sub.add_parser("collection")
    collection.add_argument("--out-dir", type=Path, default=Path(tempfile.gettempdir()) / "mindthus-case-exports")
    collection.add_argument("--collection-id", default=None)
    collection.add_argument("--title", default="Current Mindthus Case Collection")
    collection.add_argument("--case-dir", action="append", type=Path, required=True)
    collection.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.mode == "judgment":
            result = prepare_judgment_case(
                trace_path=args.trace,
                summary_path=args.summary,
                case_type=args.case_type,
                output_root=args.out_dir,
                case_id=args.case_id,
                source_client=args.source_client,
                source_method=args.source_method,
                benchmark_case_id=args.benchmark_case_id,
                related_test_id=args.related_test_id,
                related_issue=args.related_issue,
                excerpts=args.excerpt,
                excerpts_confirmed_redacted=args.confirm_excerpts_redacted,
            )
        elif args.mode == "benchmark":
            result = prepare_benchmark_case(
                run_dir=args.run_dir,
                benchmark_case_id=args.benchmark_case_id,
                output_root=args.out_dir,
                case_id=args.case_id,
                case_type=args.case_type,
                excerpts=args.excerpt,
                excerpts_confirmed_redacted=args.confirm_excerpts_redacted,
            )
        elif args.mode == "tplan":
            result = prepare_tplan_case(
                mission_dir=args.mission_dir,
                output_root=args.out_dir,
                focus=args.focus,
                case_id=args.case_id,
                judgment_trace_path=args.judgment_trace,
                excerpts=args.excerpt,
                excerpts_confirmed_redacted=args.confirm_excerpts_redacted,
            )
        else:
            result = prepare_case_collection(
                case_dirs=args.case_dir,
                output_root=args.out_dir,
                collection_id=args.collection_id,
                title=args.title,
            )
    except CasePrepError as exc:
        if args.json:
            print(json.dumps({"status": "invalid", "findings": [item.__dict__ for item in exc.findings]}, ensure_ascii=False, indent=2))
        else:
            for item in exc.findings:
                print(f"{item.severity.upper()} [{item.code}]: {item.message}")
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"mode: {result['mode']}")
        print(f"package_dir: {result['package_dir']}")
        print(f"archive_path: {result['archive_path']}")
        print("review_required_before_share: true")
        print("automatic_upload: false")
        if result.get("item_count") is not None:
            print(f"item_count: {result['item_count']}")
        if result.get("warnings"):
            print("warnings: " + ", ".join(result["warnings"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
