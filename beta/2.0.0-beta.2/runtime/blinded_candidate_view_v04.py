#!/usr/bin/env python3
"""Deterministic de-identification for the frozen v0.4 Judge candidate view."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping


LABEL_PATTERN = re.compile(
    r"\b(?:direct-only|thin-kernel|stable\s+arm)\b|mindthus(?:-beta)?:",
    re.IGNORECASE,
)
PATH_REPLACEMENT = "[blinded evaluation path]"
ARM_REPLACEMENT = "[blinded arm]"


class BlindedViewError(ValueError):
    pass


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalized_paths(paths: Iterable[str]) -> list[str]:
    values = sorted(
        {str(Path(value).resolve()) for value in paths},
        key=lambda value: (-len(value), value),
    )
    if not values or any(not value.startswith("/") for value in values):
        raise BlindedViewError("sensitive paths must be non-empty absolute paths")
    return values


def transform_candidate(
    candidate: str, sensitive_paths: Iterable[str]
) -> tuple[str, list[dict[str, Any]]]:
    """Return a Judge-only view and a content-addressed transformation trace."""

    blinded = candidate
    counts: dict[tuple[str, str], int] = {}
    for source in normalized_paths(sensitive_paths):
        occurrences = blinded.count(source)
        if not occurrences:
            continue
        blinded = blinded.replace(source, PATH_REPLACEMENT)
        key = ("sensitive-path", text_sha256(source))
        counts[key] = counts.get(key, 0) + occurrences

    def replace_label(match: re.Match[str]) -> str:
        source = match.group(0)
        namespace = source.lower() in {"mindthus:", "mindthus-beta:"}
        kind = "namespace-prefix" if namespace else "arm-label"
        key = (kind, text_sha256(source))
        counts[key] = counts.get(key, 0) + 1
        return "" if namespace else ARM_REPLACEMENT

    blinded = LABEL_PATTERN.sub(replace_label, blinded)
    trace = [
        {
            "kind": kind,
            "source_sha256": source_sha256,
            "occurrences": counts[(kind, source_sha256)],
        }
        for kind, source_sha256 in sorted(counts)
    ]
    return blinded, trace


def assert_blind(candidate: str, sensitive_paths: Iterable[str]) -> None:
    leaked_paths = [path for path in normalized_paths(sensitive_paths) if path in candidate]
    leaked_labels = [match.group(0) for match in LABEL_PATTERN.finditer(candidate)]
    if leaked_paths or leaked_labels:
        raise BlindedViewError(
            f"blinded candidate still exposes identifiers: "
            f"paths={len(leaked_paths)}, labels={leaked_labels}"
        )


def view_receipt(
    *,
    amendment_id: str,
    output_id: str,
    cell_id: str,
    original: str,
    blinded: str,
    transformations: list[dict[str, Any]],
) -> dict[str, Any]:
    if not transformations or original == blinded:
        raise BlindedViewError("identity candidate views do not receive a receipt")
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-blinded-candidate-view-v0.1",
        "amendment_id": amendment_id,
        "blinded_output_id": output_id,
        "cell_id": cell_id,
        "original_answer_sha256": text_sha256(original),
        "blinded_answer_sha256": text_sha256(blinded),
        "transformations": transformations,
        "original_answer_mutated": False,
        "judge_view_only": True,
    }
    payload["receipt_digest"] = canonical_sha256(payload)
    return payload


def validate_view_receipt(
    receipt: Mapping[str, Any], expected: Mapping[str, Any]
) -> None:
    unsigned = dict(receipt)
    digest = unsigned.pop("receipt_digest", None)
    if digest != canonical_sha256(unsigned) or dict(receipt) != dict(expected):
        raise BlindedViewError("blinded candidate view receipt differs")
