#!/usr/bin/env python3
"""Classify a terse subject into deterministic profile support categories."""

from __future__ import annotations

import argparse

from _profile_support import boundary_payload, load_resource, normalize, write_json


def classify(subject: str) -> tuple[str, list[str]]:
    taxonomy = load_resource("subject-taxonomy.json")
    text = normalize(subject)
    scores: list[tuple[int, str]] = []
    for category in taxonomy["categories"]:
        score = sum(1 for keyword in category.get("keywords", []) if keyword in text)
        if score:
            scores.append((score, category["id"]))
    if not scores:
        return "unknown_colossus", ["unknown_colossus"]
    scores.sort(key=lambda item: (-item[0], item[1]))
    candidates = [category_id for _, category_id in scores]
    return candidates[0], candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", nargs="+")
    args = parser.parse_args()
    subject = " ".join(args.subject)
    primary, candidates = classify(subject)
    write_json(
        boundary_payload(
            subject=subject,
            primary_category=primary,
            candidate_categories=candidates,
            notes=[
                "Classification is deterministic support only.",
                "TVG still owns semantic judgment and exit decisions.",
            ],
        )
    )


if __name__ == "__main__":
    main()
