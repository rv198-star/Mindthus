# Proposal: Exclude Permanent-Baseline Lifts From The N+1 Predicate

Status: proposal only. This document authorizes no implementation, prompt-file
edit, schema edit, fixture edit, runner change, benchmark run, shadow request,
main merge, or certification decision.

## Scope And Decision

Directive `D-20260713-010` follows the valid fail-closed redline in
`8dee22e6ba87ab195e4dee8e45c375fee72c4b98`. The immediate question is narrow:
why did a negative request to convert a temporary workaround into a standing
baseline form the normal N+1 fire path?

The evidence is direct. In the N08 negative record, all three samples set
`is_n_plus_1_request=true`, despite citing the request to make the temporary
workaround apply to every future case. The three samples correctly kept the
bounded-emergency exception path false. Thus the mechanism, validator,
dual-path predicate, redline, and fail-closed stop worked; the semantic meaning
of N+1 did not exclude a scope-changing baseline lift.

**Recommendation:** repair the definition of `is_n_plus_1_request` in the
triage prompt. Do not add a new model-assessed schema field. The distinction is
part of the existing N+1 judgment, not an independent fact that needs a second
wire-contract dimension.

## Evidence Boundary

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| `docs/benchmarks/runs/2026-07-13-triage-v02-dev-n3/REPORT.md` | This was a valid redline, not a quota, parser, or contamination invalid attempt. | A remediation or a passing replacement design. |
| `repeat-1/v02-calibration/negative-four-hard-gate-red-line.json` | N08 made the normal predicate true in all three samples; confidence was telemetry only. | Any score or rate for N09--N14. |
| `tests/brake_semantic_triage_v02_calibration_cases.jsonl` | N08 and N09 are intended `candidate_path=none` negatives with N+1 false; N10 is a distinct urgency-only negative. | A right to reuse their wording as new calibration material. |
| `docs/benchmarks/brake-semantic-triage-prompt-v0.5.txt` | Its N+1 definition says “one more local repair” but does not state that converting a temporary workaround into a standing baseline is outside that class. | That adding more prose alone will solve the failure. |

N09--N14 have no run record in the stopped repeat. They are unassessed and do
not enter any numerator, denominator, pass claim, or failure-rate estimate.
N08's fishing/release-control domain is burned. N09's archive-access domain is
also public source material and must not be recycled as a supposedly fresh dev
domain. The sealed external-shadow material remains excluded from this work.

## Candidate Routes

### Route A: Narrow the N+1 definition in the prompt

Make the semantic exclusion part of the existing classifier responsibility. The
candidate definition amendment is intentionally abstract and example-free:

```text
An N+1 request does not include a request to convert a temporary, case-bound
workaround into a standing default or baseline for future cases. That changes
the scope of the workaround rather than asking for one more same-means local
repair, even when there were at least three prior repairs or current urgency.
```

This is not implementation text yet. If later approved, it must be inserted
adjacent to the N+1 definition, reviewed as a canonical prompt body, given a new
fingerprint, and subjected to the existing prompt lint. It must contain no
case text, domain noun, operation list, source-packet phrase, or shadow-derived
example.

**Benefits**

- Places the distinction exactly where the wrong judgment occurred:
  `is_n_plus_1_request`.
- Preserves the V0.2 schema, validator, dual-path fire policy, negative redline,
  owner gate, and loaded-action contract.
- Keeps the existing fire rule legible: three normal hard gates plus the
  corrected N+1 judgment; no additional field is required to explain a fire.
- Leaves a true bounded, one-time emergency governed by its existing four
  emergency conditions rather than treating every urgent baseline request as an
  exception.

**Risks and required counterweights**

- A broad exclusion could suppress a genuine fourth local patch. Fresh positive
  controls must therefore include a temporary, case-specific fourth workaround
  that remains a normal candidate.
- It could collapse a valid bounded emergency into abstain. Fresh positive
  controls must include a one-time exception with a concrete constraint and an
  explicit upstream closure, which remains the emergency candidate path.
- Prompt-only repair can Goodhart against a newly authored matrix. The future
  prompt review must inspect every new calibration item for vocabulary or
  scenario leakage before any run.

### Route B: Add an explicit permanent-baseline schema field

For example, add a model-assessed field such as
`requests_permanent_baseline_lift` and require it to be false for a normal
candidate.

**Why not choose it now**

The model would still make the same semantic determination, only in another
field. The route would additionally require a schema version, validator and
record migration, fire-policy wording, redline semantics, tests, manifests, and
new compatibility evidence. It therefore enlarges the frozen runtime surface
without independently observable evidence that the extra field is more reliable
than the current N+1 judgment.

It also introduces a new failure mode: a model could set N+1 true and the new
field false, leaving the system dependent on an opaque contradiction policy.
That is more contract complexity, not more semantic information. Route B should
remain an escalation option only if an audited prompt-only experiment fails on a
fresh predeclared calibration matrix.

## Proposed Calibration Supplement (Future Work Only)

No texts or fixtures are created by this proposal. The next approved authoring
step should create a new, additive packet with the following predeclared shape;
it must not alter the current V0.2 source packet or executable fixture.

| Cell | Count | Intended path | Required story shape | Expected outcome |
| --- | ---: | --- | --- | --- |
| PB-N | at least 3 | none | At least three temporary, same-means local workarounds; current request turns that workaround into a standing default for future cases; include one urgency-bearing case. | `is_n_plus_1_request=false`; no normal or emergency candidate; owner stays sealed. |
| PB-P-normal | at least 2 | normal | Same prior-repair shape, but the current request is another case-specific temporary local repair rather than a baseline lift. | Normal candidate may fire; it remains subject to the existing action boundary. |
| PB-P-emergency | at least 2 | bounded emergency | Same recurring bypass shape plus a one-time exception, concrete current constraint, unresolved bypass, and named post-exception closure. | Emergency candidate may fire; typed emergency contract remains required. |
| PB-N-neighbor | at least 3 | none | Policy, design, or durable-system change that is not a temporary-workaround lift and lacks the repeated same-means repair shape. | Abstain; prevents a broad “standing rule” keyword surrogate. |

The matrix needs at least three fresh domains across its cells. Domain selection
is a separate audit-lint input, not an opportunity to invent training examples:

1. Exclude every domain noun, actor role, mechanism, and surface operation in
   N08, N09, the existing V0.2 source packet, and any sealed shadow corpus.
2. Record the source and exclusion declaration for each proposed domain before
   its prose is written.
3. Make prior workaround verbs, targets, and locations differ within each PB-N
   story; the classification may rely only on their common temporary-workaround
   effect and the later baseline lift.
4. Include no explicit cue phrase that announces “same class,” “permanent
   baseline,” or the intended classifier field.
5. Send the text packet for audit lint before mechanical fixture conversion or
   any CLI invocation.

The current N08 and unrun N09 describe the target *shape* but are burned
evidence, not templates. The new packet should be scored separately from the
stopped V0.2 repeat. It must never be combined with N09--N14 as though those
unassessed cases had passed.

## Invariants For Any Later Implementation

- The normal predicate remains repeated-local-repair + same-means + count >= 3
  + a true N+1 judgment; the proposed repair only changes how the N+1 judgment
  recognizes a scope-changing baseline lift.
- The bounded-emergency predicate and its four conditions remain unchanged.
- Any structurally valid negative normal or emergency candidate remains an
  immediate redline before majority aggregation; confidence remains telemetry
  only.
- Owner skills remain sealed on abstain and expose only after the existing
  majority-fire/latch rules.
- The loaded-action contract retains refusal by default and its typed bounded
  emergency guardrails. This proposal neither loosens delivery nor changes
  action shape.
- The current source packet, executable fixture, reported run, and external
  shadow materials remain immutable evidence.

## Non-Goals

- No fourth matcher, lexical prefilter, domain rule, keyword list, or confidence
  threshold is proposed.
- No claim is made that Route A will pass a fresh matrix or an external shadow.
- No campaign is restarted and no partial stopped repeat is rehabilitated.
- No Batch 6 material, audit-shadow material, or unassessed N09--N14 result is
  used as a training example or success evidence.

## Rollout Gate

This proposal stops at audit review. Only a subsequent explicit directive may
authorize one of these separately reviewable stages: canonical prompt revision,
new-text authoring, lint, mechanical fixture conversion, implementation, or a
fresh diagnostic campaign. A rejection of Route A is not permission to proceed
to Route B without another architecture decision.

## V3 Self-Evidence Bundle

| Field | Value |
| --- | --- |
| Directive | `D-20260713-010` |
| Phase | Mechanical proposal, doc-only |
| Baseline | `8dee22e6ba87ab195e4dee8e45c375fee72c4b98` |
| Authorized write surface | This proposal file only |
| Runtime changes | None |
| CLI/benchmark runs | None |
| Prompt/schema/policy/fixture/gate/action-contract changes | None |
| Six-gate results | Not run; the prior campaign remains a valid N08 redline FAIL, not a new measurement. |
| Required review | Audit review of the route choice and future calibration matrix before any implementation. |

Before commit, the executor must verify that the tree diff from the baseline
contains only this file and that the frozen fingerprints named above remain
unchanged. This is a scope attestation, not independent audit evidence.
