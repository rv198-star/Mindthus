#!/usr/bin/env python3
"""Run the preregistered BSC experiment with the simplified C-lite treatment.

This wrapper intentionally reuses the existing isolated Codex experiment harness. It
only replaces variant C's treatment text; A/B/D execution, blind judge behavior,
fixtures, contamination checks, usage accounting, and output schema remain unchanged.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts" / "run-bidirectional-steelman-experiment.py"

C_LITE_PROTOCOL = """Use current Stable Mindthus normally. Do not create a new route, owner, mandatory question, or mandatory debate flow. Only when a material competing-frame judgment remains after Stable framing/routing, add exactly these support moves:
1. Competitive Steelman / 竞争框架钢人: preserve the strongest defensible active frame and construct the strongest materially relevant counter-frame that could genuinely win under the same judgment object, situated decision context when relevant, Evidence / Claim Ceiling, and active Stable judgment owner. Do not merely list objections. Do not force symmetry after evidence becomes asymmetric; if the offered A/B is malformed, let existing Stable framing/EDSP reframe it first; if a local mechanism already owns the complete target result, do not manufacture a debate.
2. Decisive Discriminator / 决定性判别变量: name the one fact, result-controller difference, target/tradeoff variable, failure prediction, or other observable condition with the highest ability to change verdict, evidence requirement, next action, stopping condition, or handoff. If no difference can change any of those, stop the pressure pass.
Then return immediately to the existing Stable owner. Existing Stable behavior decides whether to acquire evidence, ask for user-owned context, decide now, return conditional/blocked, or stay asleep on direct/deterministic/preference tasks. There is no mandatory question. Do not expose internal protocol names unless the user asks."""


def load_base_runner():
    spec = importlib.util.spec_from_file_location("mindthus_bsc_base_runner", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base runner: {BASE_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_base_runner()
    module.ADAPTED_PROTOCOL = C_LITE_PROTOCOL
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
