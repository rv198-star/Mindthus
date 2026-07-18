# H1 Owner Metadata Precision Result

Terminal H1 outcome: `H1_REJECTED`

This is an architecture-level rejection. It is not the Mission terminal outcome; H2 is
now authorized by the frozen Mission sequence.

## What H1 proved

Package-time metadata can materially improve native Codex owner selection without
changing owner bodies or adding a carrier:

- tightened WAE metadata preserved clear WAE recall and removed the release-readiness
  false positive;
- tightened MPG metadata removed the premature MPG and downstream SELA reads;
- the one correction tightened 3L5S metadata, while the pre-existing WH-X4 holdout still
  directly loaded 3L5S and produced a falsifiable incident investigation;
- ordinary and evidence-first cases loaded only the thin entry; and
- all observed owner loads occurred in the same user turn without routing ceremony.

## Why H1 still failed

Candidate A commit `155648d0fb6ae123e0cb939b97953d0ade1991e5` failed the
missing-context case by loading 3L5S and recommending a reversible pause. The one
authorized correction at commit `24a28c6e1d1479b3fd2279ea01dd99b5e21801e5`
removed that owner false positive.

The corrected case then read only `using-mindthus`, but still answered:

> Decision for now: hold the migration—do not continue yet, but don’t abandon it.

It requested a context snapshot afterward. This violates the frozen criterion: before
any continue/hold/stop advice, the candidate must ask exactly one blocking question that
locks answer-changing actor, target, timing, authority, exposure, rollback, or acceptable
loss. There was no owner left whose metadata could explain or repair this behavior.

The evidence therefore separates two claims:

1. `SUPPORTED`: owner-description precision can remove the observed false owner loads.
2. `REJECTED`: owner-description precision alone cannot guarantee Decision Context
   precedence once the thin entry has been injected.

One critical passive obligation failed, so H1 cannot enter Stable comparison. The
correction budget is exhausted; changing the thin entry, adding another metadata patch,
or weakening the case is forbidden.

## Calls and usage

Nine Generator calls completed; no Judge ran. Cached input is a subset of input and is
not counted twice.

| Phase | Calls | Input | Output | Counted |
| --- | ---: | ---: | ---: | ---: |
| Candidate A kill probes | 3 | 290,731 | 5,198 | 295,929 |
| Correction holdout | 1 | 49,778 | 2,536 | 52,314 |
| Corrected full qualification, stopped at first critical failure | 5 | 468,805 | 5,972 | 474,777 |
| **H1 total** | **9** | **809,314** | **13,706** | **823,020** |

Every call stayed below the 200,000 counted-token limit. The full corrected workload
stopped at the first decision-changing failure; the clear-MPG continuation and
Anti-Spiral turns were not run because they could no longer change H1 eligibility.

## Evidence

Raw JSONL, stderr, final messages, plugin inventory, and static diagnostics are under
`evidence/candidate-a/` and `evidence/correction/`. The controlling corrected failure is
`evidence/correction/full-05.jsonl`.

The profile was installed in a fresh isolated `CODEX_HOME` with only
`mindthus-beta@mindthus-beta` enabled. No Stable installation, long-lived user home,
release, publication, merge, tag, Issue, or PR was changed.

## Consequence

Close H1 and proceed to H2. H2 must remove simultaneous top-level owner discovery and
let the single thin entry read owner resources on demand in the same user turn. It may
not add a second entry, Hook, prompt router, hidden atlas, or visible routing round.
