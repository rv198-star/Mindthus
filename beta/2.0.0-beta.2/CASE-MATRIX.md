# Beta.2 owner × primitive × lifecycle case matrix

The matrix is a coverage inventory, not a result set. It makes benefit cases, harm
controls, lifecycle paths, and evidence provenance explicit before #117 freezes a
workload mix. No case is executed by this issue.

## What is covered

`fixtures/evaluation-case-matrix.json` contains 31 case contracts. Together they cover:

- positive owner cases for `3l5s`, `edsp`, `sela`, `mpg`, `wae`, `tvg`, and `tplan`;
- genuine owner overlap routed to the thin `using-mindthus` arbitrator;
- direct-owner intersections with Frame, Whole, Decision Context, and Anti-Spiral;
- one answer carrying multiple passive obligations without multiple visible theses;
- evidence-first behavior and explicit stay-asleep controls;
- startup, resume, clear, and compact lifecycle paths;
- same-object third touch, renamed same object, distinct objects, and repeated work
  supported by decision-changing evidence;
- legitimate local scope, sufficient evidence, an explicit user-owned trade-off, and
  normal iterative debugging as near negatives.

At least one quarter of the current inventory is a negative control. That is a
structural harm-detection floor, not the final workload weight. #117 must freeze the
actual mix before any semantic output is inspected.

## Provenance is not interchangeable

| Provenance | Content visibility | Permitted claim |
| --- | --- | --- |
| `public-regression` | Visible in the repository | Compatibility only; never blind evidence |
| `development` | Visible in `development-cases.jsonl` | Harness and behavior-contract development only |
| `sealed-shadow` | Content absent; receipt only | Eligible only after independent custodian attestation |
| `real-task-replay` | Restricted external content | Ineligible until the user authorizes its consent scope |

`sealed-shadow-index.json` does not itself prove that a meaningful independent prompt
exists or remained blind. It proves only that the implementation repository has an
opaque receipt slot and contains no prompt content. The frozen protocol must require a
case custodian to bind and attest those receipts before a run. Likewise,
`real-task-replay-index.json` records no task content and grants no execution authority.

Public and development cases therefore cannot be relabeled as sealed evidence. The
linter checks visibility, locator type, run eligibility, and receipt matching for every
case.

## Case contract

Each matrix cell declares the #114 behavior fields directly:

- execution owner and accepted owners;
- primitive obligations and required visible action;
- required and allowed skill loads;
- stay-asleep expectation and lifecycle events.

It also declares provenance, source receipt, entry mode, lifecycle path, evidence-first
expectation, contamination risk, and machine-readable coverage tags. Prompt or
conversation content is forbidden in the matrix itself.

## Deterministic checks

Regenerate and lint the metadata with:

```bash
python3 beta/2.0.0-beta.2/runtime/build-case-matrix.py
python3 beta/2.0.0-beta.2/runtime/lint-case-matrix.py
```

The linter fails on a missing coverage cell, duplicate case, load-contract mismatch,
negative control that wakes a skill, provenance relabeling, receipt mismatch, or prompt
content leaking into the matrix or restricted indexes. Its report deliberately states
that it establishes structural coverage only; it cannot establish semantic quality,
blindness, consent, or model behavior.
