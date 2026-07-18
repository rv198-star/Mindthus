#!/usr/bin/env python3
"""Materialize one v0.5 arm and remove builder staging before model execution."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
V04_MATERIALIZER = BETA_ROOT / "runtime" / "materialize-real-codex-arm.py"
DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.pending.json"
)


def load_v04() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mindthus_beta2_v04_materializer", V04_MATERIALIZER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load v0.4 materializer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V04 = load_v04()


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    report = V04.materialize(args)
    execution_root = args.execution_root.resolve()
    staging_root = execution_root.parent / "package"
    if staging_root.exists():
        shutil.rmtree(staging_root)
    if staging_root.exists():
        raise V04.MaterializationError("v0.5 package staging root survived cleanup")

    arm_root = args.root.resolve()
    receipt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-arm-layout-receipt-v0.5",
        "arm_id": args.arm_id,
        "execution_root": str(execution_root),
        "installed_package_root": report["package_root"],
        "removed_staging_root": str(staging_root),
        "staging_root_absent": True,
        "filesystem_enforcement_required_before_model": True,
        "model_execution_performed": False,
        "semantic_output_generated": False,
    }
    receipt["receipt_digest"] = V04.canonical_sha256(receipt)
    receipt_path = arm_root / "evidence" / "v05-layout-receipt.json"
    V04.write_atomic_json(receipt_path, receipt)
    return {
        **report,
        "protocol_runtime": "0.5",
        "staging_root_absent": True,
        "layout_receipt_path": str(receipt_path),
        "layout_receipt_digest": receipt["receipt_digest"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execution-root", type=Path, required=True)
    parser.add_argument(
        "--arm-id", choices=("stable", "direct-only", "thin-kernel"), required=True
    )
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument(
        "--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json"
    )
    parser.add_argument("--thin-hook-observed-receipt", type=Path, default=None)
    parser.add_argument("--auto-probe-thin-hook", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = materialize(args)
        code = 0
    except (
        OSError,
        json.JSONDecodeError,
        RuntimeError,
        V04.MaterializationError,
    ) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
