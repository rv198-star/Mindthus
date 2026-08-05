#!/usr/bin/env python3
"""Create a local, review-required Mindthus case export package."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from runtime_import import activate_shared_runtime

activate_shared_runtime(__file__)

from _runtime.judgment.case_export import CASE_TYPES, CaseExportError, create_case_package  # noqa: E402


def parse_excerpt(value: str) -> tuple[str, Path]:
    if "=" in value:
        label, raw_path = value.split("=", 1)
        if not label.strip() or not raw_path.strip():
            raise argparse.ArgumentTypeError("excerpt must be LABEL=PATH or PATH")
        return label.strip(), Path(raw_path).expanduser()
    path = Path(value).expanduser()
    return path.stem, path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "This command writes local files only. It does not upload or share the package. "
            "A separate manual review and sharing action is always required."
        ),
    )
    parser.add_argument("--trace", type=Path, required=True, help="Validated Judgment Trace JSON.")
    parser.add_argument("--summary", type=Path, required=True, help="Case summary JSON using mindthus.case-summary.v1.")
    parser.add_argument("--case-type", choices=sorted(CASE_TYPES), required=True)
    parser.add_argument("--out-dir", type=Path, required=True, help="Parent directory for the new package.")
    parser.add_argument("--case-id", default=None)
    parser.add_argument("--source-client", default=None)
    parser.add_argument("--source-method", default=None)
    parser.add_argument("--benchmark-case-id", default=None)
    parser.add_argument("--related-test-id", default=None)
    parser.add_argument("--related-issue", default=None)
    parser.add_argument(
        "--excerpt",
        action="append",
        type=parse_excerpt,
        default=[],
        metavar="LABEL=PATH",
        help="Explicitly include one user-reviewed UTF-8 excerpt. Repeatable.",
    )
    parser.add_argument(
        "--confirm-excerpts-redacted",
        action="store_true",
        help="Required when --excerpt is used; confirms the selected files were reviewed and redacted.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        package_dir = create_case_package(
            output_root=args.out_dir,
            trace_path=args.trace,
            summary_path=args.summary,
            case_type=args.case_type,
            case_id=args.case_id,
            source_client=args.source_client,
            source_method=args.source_method,
            benchmark_case_id=args.benchmark_case_id,
            related_test_id=args.related_test_id,
            related_issue=args.related_issue,
            excerpts=args.excerpt,
            excerpts_confirmed_redacted=args.confirm_excerpts_redacted,
        )
    except CaseExportError as exc:
        for item in exc.findings:
            subject = f" [{item.subject}]" if item.subject else ""
            print(f"{item.severity.upper()} [{item.code}]{subject}: {item.message}")
        return 1

    print(f"created local case package: {package_dir}")
    print("review_required_before_share: true")
    print("automatic_upload: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
