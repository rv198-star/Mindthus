#!/usr/bin/env python3
"""Run the preregistered BSC experiment with the simplified C-lite treatment.

This wrapper intentionally reuses the existing isolated Codex experiment harness. It
replaces variant C's treatment text and extends the shared blind-judge rubric with one
user-visible translation dimension; A/B/D execution, fixtures, contamination checks,
usage accounting, and output schema mechanics remain unchanged.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_RUNNER = ROOT / "scripts" / "run-bidirectional-steelman-experiment.py"

C_LITE_PROTOCOL = """Use current Stable Mindthus normally. Do not create a new route, owner, mandatory question, or mandatory debate flow. Only when a material competing-frame judgment remains after Stable framing/routing, add exactly these support moves:
1. Competitive Steelman / 竞争框架钢人: preserve the strongest defensible active frame and construct the strongest materially relevant counter-frame that could genuinely win under the same judgment object, situated decision context when relevant, Evidence / Claim Ceiling, and active Stable judgment owner. Do not merely list objections. Do not force symmetry after evidence becomes asymmetric; if the offered A/B is malformed, let existing Stable framing/EDSP reframe it first; if a local mechanism already owns the complete target result, do not manufacture a debate.
2. Decisive Discriminator / 决定性判别变量: identify the one fact, result-controller difference, target/tradeoff variable, failure prediction, or other observable condition with the highest ability to change verdict, evidence requirement, next action, stopping condition, or handoff. If no difference can change any of those, stop the pressure pass.
Then return immediately to the existing Stable owner. Existing Stable behavior decides whether to acquire evidence, ask for user-owned context, decide now, return conditional/blocked, or stay asleep on direct/deterministic/preference tasks. There is no mandatory question.
Visible Translation Boundary / 可见表达翻译边界: the discriminator is an internal judgment representation, not user-facing wording. Before answering, translate abstractions into the user's concrete choice, loss, evidence condition, or action. Prefer forms such as 'is X worth Y?', 'which loss would you rather accept?', 'first verify Z; if it fails, do not switch/delete/ship', or an equally natural sentence in the user's language. Unless the user asks about methodology, avoid exposing internal labels such as decisive discriminator, target function, relative weight, definition authority, result controller, or Evidence / Claim Ceiling when a concrete sentence carries the same judgment. This translation boundary is not a third reasoning move.
Do not expose internal protocol names unless the user asks."""

VISIBLE_TRANSLATION_GUIDANCE = (
    "Internal analytical abstractions are translated into concrete user-facing choices, "
    "losses, evidence conditions, consequences, or actions. The answer should sound natural "
    "for the user's task rather than exposing method jargon such as target function, relative "
    "weight, decisive discriminator, definition authority, result controller, or evidence ceiling "
    "unless the user explicitly asks about methodology."
)


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
    if "visible_translation" not in module.DIMENSIONS:
        module.DIMENSIONS = tuple(module.DIMENSIONS) + ("visible_translation",)
    module.DIMENSION_GUIDANCE["visible_translation"] = VISIBLE_TRANSLATION_GUIDANCE
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
