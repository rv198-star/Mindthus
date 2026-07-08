# Mindthus V4 Diagnostic Run: External Audit Handoff

Status: ready for external audit as a diagnostic run; not certified as passing.

This handoff packages the V4 machine results plus three independent read-only SubAgent
human-review passes. The machine summary files remain unchanged; human review findings
are recorded as interpretation and certification risk, not as silent score edits.

## What To Review First

Primary report:

- `REPORT.md`
- `HUMAN_REVIEW_PACKET.md`
- `runtime-fingerprint-strict.json`
- `baseline-cli-clean-v4-empty-home/summary.json`
- `treatment-cli-clean-v4-empty-home/summary.json`
- `treatment-cli-clean-v4-empty-home/score-records.jsonl`

Core result:

- Baseline positive mean: `1.184`
- Treatment positive mean: `1.447`
- Public positive target: `>= 1.5`
- Treatment negative false wake-up rate by final-answer judge field: `0.000`
- Treatment event-level caveat: #32 loaded Mindthus/3L5S and leaked method language, so
  `0.000` should not be read as "runtime never over-woke."

## SubAgent Review Summary

### P0 Core Disputes

Independent review of #32, #13, #48, #50, #37, and #8:

| Case | Machine score | Human read | Audit implication |
| --- | ---: | --- | --- |
| #32 | 1 | `needs-rubric-fix` / uncertain | Final answer did not blindly rewrite, but rubric may over-require first asking what "not good" means. Event trace still shows Mindthus/3L5S over-wake. |
| #13 | 0 | agree, `0` | True product/skill failure: answer accepted beans as the business explanation and did not reconstruct shop economics. |
| #48 | 1 | agree, `1` | Direction is right, but first sentence is too soft; output-shape discipline gap rather than full conceptual failure. |
| #50 | 2 | disagree, suggested `1` | Machine judge likely too generous; third turn partly concedes "daily context/core judgment" while retaining boundaries. |
| #37 | 0 | disagree, suggested `1` | Machine judge likely too strict; first sentence fails, but later advice does give a buying decision and demotes PPI to boundary evidence. |
| #8 | 0 | agree, `0` | True product/skill failure: loaded EDSP but accepted the next-token frame instead of challenging definition authority. |

Net effect if reviewers apply only #50 `2 -> 1` and #37 `0 -> 1`: treatment positive
mean stays approximately unchanged. The bigger issue is not headline score movement; it
is explaining which failures are real skill failures versus rubric strictness.

### P1/P2 Failure Attribution

Independent review of #2, #10, #33, #15, #19, #49, #3, #4, #17, #18, and #34:

| Case | Review classification | Suggested action |
| --- | --- | --- |
| #2 | no-load | Entry Triage/root-cause evidence gate should trigger before RCA drafting. |
| #10 | loaded-behavior-gap | Whole Elephant consequence probe must visibly name the optimization drift. |
| #33 | no-load | Anti-Spiral trigger for third prompt-rule loop. |
| #15 | loaded-behavior-gap / wrong owner | Should route to EDSP-style 100% vs 10% extreme comparison, not just MPG/SELA utilization framing. |
| #19 | loaded-behavior-gap | SELA should visibly state order-of-magnitude cost/throughput/scale contrast. |
| #49 | no-load | AQM evidence ceiling should stop hypothetical arithmetic from becoming conclusion. |
| #3 | no-load | Trend-framed migration needs Input Framing Audit before migration checklist. |
| #4 | no-load | Green-tests release readiness needs evidence gates before launch announcement. |
| #17 | no-load | Malformed yes/no replacement frame should be challenged. |
| #18 | real-pass | Keep as positive sentinel; consider owner-fidelity telemetry. |
| #34 | no-load | Anti-Spiral/systematic-debugging brake should stop third fallback layering. |

Main audit takeaway: this slice is mostly no-load, followed by loaded-but-wrong-action.
Do not over-focus on rubric changes here.

### Guardrail Review

Independent review of negative controls:

- Clear final-answer pass: #7, #25, #28, #29, #31, #35, #44, #45, #46.
- #32: final answer is not a false wake-up, but event trace shows Mindthus/3L5S loading
  and method-language leakage. Treat as runtime/event-level over-wake.
- #43: full score is questionable because the answer includes a `sort` command after
  asking for CSV, while baseline-like behavior was scored harshly elsewhere.
- #47: full score is acceptable but should not be described as "successful debug"; the
  prompt had no attached stack/code, so asking for them is reasonable.

Goodhart signal: no broad evidence of overfitting across negative controls. The risk is
narrower: final-answer metrics hide event-level over-wake, and judge/rubric strictness is
not fully stable for #32, #37, #43, #47, and #50.

## Certification Boundary

This V4 run should not be certified as passing because:

1. Treatment positive mean is `1.447`, below the `1.5` target.
2. `--model` and `--judge-model` were inherited from Codex home config rather than passed
   explicitly; the config snapshot records `gpt-5.5`/medium, but the runner manifests
   contain `null` for model fields.
3. Generation and judging were run in one `--phase all` command for V3 comparability,
   not as a frozen generate phase followed by a separate judge phase.
4. Human review found at least one likely over-generous machine score (#50), one likely
   over-strict machine score (#37), and one runtime/event-level negative-control over-wake
   hidden by the final-answer false-wakeup metric (#32).

## Suggested Next Changes

Prioritize these in order:

1. Add owner-fidelity diagnostics: `loaded_owner`, `expected_owner_loaded`, and
   `required_visible_action_present` so "Mindthus loaded" does not hide wrong-lens loads.
2. Improve Entry Triage activation for no-load cases #2, #3, #4, #13, #17, #33, #34,
   #48, and #49 without increasing negative-control false wake-up.
3. Fix loaded-behavior gaps for #8, #10, #15, #19, #32, and #37: first-sentence lock,
   visible consequence probe, evidence gate, EDSP extreme comparison, and decision-context
   definition authority.
4. Calibrate rubric/judge examples for #32, #37, #43, #47, and #50 before using the
   benchmark as a release gate.
5. Rerun certification with explicit generator and judge models, split generate/judge
   phases, and repeat runs for moved or disputed cases.

## Audit-Friendly Quote

Use this wording externally:

> V4 is a clean diagnostic run with meaningful treatment lift and preserved final-answer
> negative-control behavior, but it is not a passing certification. Human review found
> the remaining work is split between no-load activation misses, loaded-but-wrong-action
> behavior gaps, and a small number of rubric/judge calibration issues.
