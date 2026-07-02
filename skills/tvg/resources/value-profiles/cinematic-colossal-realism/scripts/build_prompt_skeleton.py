#!/usr/bin/env python3
"""Build a deterministic prompt skeleton for TVG/agentic filling."""

from __future__ import annotations

import argparse

from _profile_support import boundary_payload, load_resource, write_json
from classify_subject import classify


def category_record(category_id: str) -> dict:
    taxonomy = load_resource("subject-taxonomy.json")
    for category in taxonomy["categories"]:
        if category["id"] == category_id:
            return category
    return taxonomy["categories"][-1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", nargs="+")
    args = parser.parse_args()
    subject = " ".join(args.subject)
    primary, candidates = classify(subject)
    category = category_record(primary)
    scenes = load_resource("scene-defaults.json")["scenes"]
    camera = load_resource("camera-lighting.json")
    negative = load_resource("negative-constraints.json")
    scene = scenes[category["scene_default"]]

    write_json(
        boundary_payload(
            subject=subject,
            primary_category=primary,
            candidate_categories=candidates,
            skeleton={
                "foreground_scale": scene["foreground"],
                "midground_scale": scene["midground"],
                "background_colossus": scene["background"],
                "physical_feedback": scene["physical_feedback"],
                "camera_defaults": camera["camera_defaults"],
                "lighting_defaults": camera["lighting_defaults"],
                "decisive_pressure_frame": camera["decisive_pressure_frame"],
                "director_shot_spine": camera["director_shot_spine"],
                "director_subtraction_pass": camera["director_subtraction_pass"],
                "controlled_fracture_coherence": camera["controlled_fracture_coherence"],
                "shot_economy_mode": camera["shot_economy_mode"],
                "negative_visual_failure_handles": negative["safe_visual_failure_handles"],
            },
            notes=[
                "Skeleton fields are deterministic support surfaces.",
                "TVG must still choose, fill, and audit the final prompt.",
            ],
        )
    )


if __name__ == "__main__":
    main()
