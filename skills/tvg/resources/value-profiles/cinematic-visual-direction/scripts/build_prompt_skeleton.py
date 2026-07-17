#!/usr/bin/env python3
"""Build a general cinematic prompt skeleton with an optional scene adapter."""

from __future__ import annotations

import argparse

from _profile_support import boundary_payload, load_adapter, load_resource, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", nargs="+")
    parser.add_argument("--adapter")
    args = parser.parse_args()

    controls = load_resource("director-controls.json")
    negative = load_resource("negative-constraints.json")
    adapter = load_adapter(args.adapter) if args.adapter else None
    subject = " ".join(args.subject)
    skeleton = {
        "subject_or_event": subject,
        "primary_read": "agentic fill required",
        "scene_relation": "agentic fill required",
        "camera_defaults": controls["camera_defaults"],
        "lighting_defaults": controls["lighting_defaults"],
        "director_shot_spine": controls["director_shot_spine"],
        "director_subtraction_pass": controls["director_subtraction_pass"],
        "controlled_fracture_coherence": controls["controlled_fracture_coherence"],
        "shot_economy_mode": controls["shot_economy_mode"],
        "negative_visual_failure_handles": negative["safe_visual_failure_handles"],
    }
    if adapter:
        skeleton["scene_adapter"] = {
            "name": adapter["adapter"],
            "scope": adapter["scope"],
            "realization_surfaces": adapter["realization_surfaces"],
            "prompt_support": adapter["prompt_support"],
        }

    write_json(
        boundary_payload(
            subject=subject,
            resolved_adapter=adapter["adapter"] if adapter else None,
            skeleton=skeleton,
            notes=[
                "The skeleton exposes deterministic support surfaces only.",
                "The agent must verify adapter scope, fill the prompt, and audit the image.",
            ],
        )
    )


if __name__ == "__main__":
    main()
