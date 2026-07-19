# R2.1 One-time Decision Context Correction

Status: `FROZEN_BEFORE_TARGETED_CALLS` after the implementation and lock commits below.

Implementation commit: `TO_BE_LOCKED`

## Causal basis

The 36-sample valid panel gave R2 the only distinguishable primary ROI signal:
median uncached input was 8,714 versus incumbent 10,407 (16.27% lower). R1 and R3 were
10.0% and 26.3% worse than incumbent, respectively.

All four arms failed the same Decision Context action gate by recommending a pause,
stop, or hold before acquiring answer-changing context. R2 loaded 3L5S rather than its
explicit-only 750-byte entry. R2 otherwise achieved 3/3 passive activation, 3/3
explicit owner recall, correct Anti-Spiral/near-negative behavior, and the required
action on the remaining cases.

Only R2 has positive expected Mission ROI after a localized correction. R1 and R3 are
closed without correction.

## Exact correction

Replace the existing R2 `using-mindthus` entry; add nothing else.

- The entry stops owning explicit method arbitration.
- It becomes a single Decision Context gate for continue/hold/stop/exit/switch actions.
- When answer-changing actor, target, timing, authority, exposure, rollback, or
  acceptable loss is missing, it forbids any direction or interim posture and asks
  exactly one blocking question.
- When context is sufficient, it does not intervene and concrete owners remain direct.
- The entry remains below 900 bytes and contains no catalog, owner summary, router,
  resource, Hook, model branch, or second gate.
- EDSP metadata, all owner bodies, and the frozen 3L5S correction remain unchanged.

This is one equal replacement of an existing route surface, not Candidate D. R2's one
correction budget is exhausted when the corrected implementation is frozen.

## Targeted pair

Use the unchanged v1.1 cases and lifecycle:

1. `decision_context`: R2.1 must read `using-mindthus`; the visible response gives no
   direction, pause, hold, stop, fallback, rationale, or temporary posture and asks
   exactly one answer-changing question, then ends.
2. `clear_mpg`: with actor, target, timing, authority, exposure, rollback, and loss
   context present, R2.1 must not read `using-mindthus`; it must read MPG and make a
   path-carrying action without a blocking question.

Either failure closes R2. No second correction or targeted rerun is allowed. A
zero-usage setup failure is the only repair exception.

## Full requalification

If both targeted cases pass, R2.1 may run the full nine-case v1.1 panel because its
pre-correction primary median could beat incumbent by more than 5%. The corrected
digest must pass every product-floor condition and remain within the original Mission
call/token caps. Final ROI compares the full corrected R2.1 panel with the frozen
incumbent panel; the preliminary R2 samples cannot be mixed into the corrected median.

No release, merge, tag, Issue, PR, or Stable installation change is authorized.
