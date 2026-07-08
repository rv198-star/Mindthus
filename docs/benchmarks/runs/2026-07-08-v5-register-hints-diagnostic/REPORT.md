# Mindthus V5 Register-Hint Diagnostic

Status: diagnostic host-hint experiment completed; not a certification candidate.

This run tests whether the V5 target-trigger register can serve as a mechanical
activation carrier without broad prompt expansion. It uses `--v5-register-hints`, which
injects host-style route hints only for registered V5 target cases and records those
hints in response artifacts. Results must not be marketed as natural activation or V5
certification.

## Scope

- Date: 2026-07-08
- Raw answer generation commit: `98aebe65afc6e35523062a164e70622c8c94209b`
- Summary reanalysis commit: `8b803923f986e3a38508db6b3dd0bfc543b1832f`
- Runner SHA-256 prefix: `973b9ae9cbb9`
- Register SHA-256 prefix: `37752d2ece75`
- Fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Model: `gpt-5.5`
- Judge model: `gpt-5.5`
- Diagnostic mode: `--v5-register-hints`

Summary note: after the raw runs completed, summaries were refreshed with cached judge
records under commit `8b803923f986e3a38508db6b3dd0bfc543b1832f` to fix the
machine-field distinction between natural activation and hint-applied activation. Raw
answers were not regenerated during that refresh.

## Runs

| Run | Cases | Positive Mean | Overall Mean | Final False Wake | Runtime False Wake | Expected Owner Loaded | Required Visible Action | H Brake |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `treatment-targets-hint-repeat-1` | 9 | 1.667 | 1.667 | n/a | n/a | 1.000 | 0.778 | 1.000 |
| `treatment-targets-hint-repeat-2` | 9 | 1.778 | 1.778 | n/a | n/a | 1.000 | 0.889 | 1.000 |
| `treatment-targets-hint-repeat-3` | 9 | 1.778 | 1.778 | n/a | n/a | 1.000 | 0.889 | 1.000 |
| `negative-controls-hint-repeat-1` | 12 | n/a | 2.000 | 0.000 | 0.083 | n/a | n/a | n/a |

Target set:

```text
2,3,4,13,17,33,34,48,49
```

Negative-control set:

```text
7,25,28,29,31,32,35,43,44,45,46,47
```

## Target Results

All three target repeats loaded an accepted owner on all 9 registered target cases:

- `using-mindthus`: #2, #3, #4, #13, #48, #49
- `edsp`: #17
- `3l5s`: #33, #34

Case scores across three repeats:

| Case | Repeat 1 | Repeat 2 | Repeat 3 | Owner Loaded | Note |
| ---: | ---: | ---: | ---: | --- | --- |
| #2 | 2 | 2 | 2 | 3/3 | root-cause gate stable |
| #3 | 2 | 2 | 2 | 3/3 | target-function-before-migration stable |
| #4 | 2 | 2 | 2 | 3/3 | release-readiness gate stable |
| #13 | 1 | 2 | 2 | 3/3 | improved after repeat; still watch as Whole Elephant action case |
| #17 | 0 | 0 | 0 | 3/3 | EDSP loaded, but answer collapsed to yes/no in every repeat |
| #33 | 2 | 2 | 2 | 3/3 | Anti-Spiral brake stable |
| #34 | 2 | 2 | 2 | 3/3 | Anti-Spiral brake stable |
| #48 | 2 | 2 | 2 | 3/3 | definition-authority first sentence stable |
| #49 | 2 | 2 | 2 | 3/3 | AQM evidence ceiling stable |

Interpretation:

- The no-load problem is mechanically solved in this diagnostic mode:
  `expected_owner_loaded_rate = 1.000` in all three repeats.
- The H-group brake problem moved in this diagnostic mode: #33 and #34 passed in all
  three repeats.
- #13 is no longer a stable failure, but remains a loaded-action watch case because
  repeat 1 scored only `1`.
- #17 is a stable loaded-but-wrong-action failure: EDSP loads, but the answer still
  accommodates the forced yes/no framing.
- This is still diagnostic host-hint evidence, not natural activation evidence.

## Negative Controls

The negative-control run applied no register hints:

- `activation_hint_applied_count = 0`
- natural Mindthus runtime load: `1/12`
- final-answer false wake-up: `0/12`
- runtime-event false wake-up: `1/12`
- owner-fidelity counts: `direct_stay_asleep = 11`, `runtime_over_wake = 1`

The single runtime over-wake was #25 loading `mpg`, matching a known residual natural
runtime over-wake pattern from earlier diagnostics. It was not caused by a register hint.

## Gate Decision

Do not run a full 50-case certification candidate from this result.

What this run proves:

- A versioned register plus host-style hint can wake the expected owner on the public
  no-load target set with `n = 3` repeat stability.
- The hint mechanism is auditable: manifest records the mode and register SHA, response
  artifacts record applied hints, and summaries expose `activation_hint_applied_count`.
- Negative controls do not receive register hints.

What this run does not prove:

- Natural activation improved.
- All loaded actions are stable under `n >= 3`; #17 is still a stable loaded-action
  failure.
- Shadow controls hold.
- V5 certification is ready.

Next useful work:

1. Repair #17 as a loaded-but-wrong-action case with an EDSP action probe or calibration
   anchor, not a wording clause.
2. Repeat negative controls and compare runtime-event false wake-up against the safe-run
   budget.
3. Obtain or run an externally owned shadow set before any certification claim.
