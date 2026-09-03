# SRA Dual-View Priority-Effectiveness Audit

Date: 2026-09-03
Scope: proposed replacement of `blind -> state-aware override` with independent `challenge || situated -> compare -> reconcile-on-conflict`
Issue: #157
Verdict: **PASS — CONDITIONS IMPLEMENTED AND REGRESSION-QUALIFIED**

## Audit Question

Will the proposed dual-view architecture improve SRA's ability to allocate scarce resources without replacing incumbent-context bias with a new blind-judgment bias or omitting real execution constraints?

This audit is independent from the WAE architecture audit. It evaluates decision quality, omission risk, anchoring, evidence asymmetry, and analysis cost. It does not use the WAE ownership verdict as evidence.

## Core Finding

The replacement direction is sound:

```text
shared decision base
    -> de-anchored challenge judgment
    -> situated judgment
    -> deterministic comparison
    -> targeted reconciliation only on material conflict
```

It is more defensible than the current linear design because neither judgment is required to treat the other as the baseline. The challenge view can expose incumbent capture; the situated view can retain real switching cost, commitments, remaining cost, path dependency, and reusable assets.

The architecture passes only if the following conditions are implemented directly.

## Mandatory Conditions

### 1. Independent Means Independent Outputs

The challenge judge and situated judge must not receive each other's output. They may share the same decision-base packet, but their prompts, output schemas, and carrier artifacts must remain separate.

Failure signal: the situated judge is asked whether it should overturn, preserve, or modify the challenge result.

### 2. Challenge Is A Calibration View, Not The Default Decision

The challenge judgment removes active-path identity, historical spend, incumbent advocacy, and prior conclusions. It is intentionally incomplete with respect to execution state. It can challenge capture but cannot own the final allocation by default.

The situated judgment is the action-bearing view because it includes real future consequences. Agreement with challenge strengthens confidence; disagreement opens reconciliation.

### 3. Candidate Inputs Must Not Pre-Decide SRA Roles

The outer caller may provide observable relations and claims, including target effect, resource demand, dependencies, unlocks, substitutes, deadlines, downside, reversibility, evidence, and assumptions.

The input must not pre-label candidates as:

- `hard_gate`
- `threshold_essential`
- `value_expanding`
- `enabler_or_bottleneck`
- `maintenance_or_option`
- `defer_or_stop`

Those are SRA outputs. Allowing them in the input would let the caller silently perform the core judgment before the independent judge runs.

### 4. Structural Alignment Must Preserve Real Evidence Asymmetry

Every candidate should expose the same fields. The runtime must not equalize evidence quantity, confidence, or descriptive length. One candidate may have a reproducible failing test while another has only an assumption; that difference is decision-relevant.

The runtime may warn about presentation asymmetry. It must not reward the richer candidate or penalize the terser candidate mechanically.

### 5. User Values And Authority Belong In Both Views

A de-anchored challenge must still respect the current objective, target threshold, user values, risk tolerance, authority, and hard constraints. Removing those would produce abstract rather than situated priority.

Unsupported factual claims embedded in a user preference remain assumptions or unverified claims; the preference itself remains a legitimate constraint.

### 6. Conflict Comparison Uses Stable Decision Fields

Workflow may compare only mechanically stable fields such as:

- decision outcome
- selected candidate or bundle IDs
- current floor IDs
- next-tranche candidate ID
- authorization horizon
- reserve posture
- defer and stop sets

Workflow must not decide semantic equivalence from prose.

### 7. Reconciliation Is Targeted And May Refuse To Decide

When challenge and situated outputs materially conflict, the reconciliation packet contains:

- the common decision base;
- the conflicting fields;
- each judgment's cited evidence and assumptions;
- admitted state items that could explain the difference;
- known omissions.

It must not expose prior ambient conversation, advocacy, or unrelated reasoning prose.

Allowed reconciliation outcomes include:

- `allocate`
- `conditional`
- `blocked`
- `request_missing_context`

The reconciler is not a majority-vote or forced-closure mechanism.

### 8. Agreement Does Not Prove Correctness

Two views can agree because they share an incomplete candidate packet. The runtime must retain `known_omissions` and support a conditional packet-coverage review for Full, high-impact, or low-confidence cases.

Coverage review checks candidate and evidence completeness only. It must not choose the allocation.

### 9. Lite Retains The Analysis-Cost Gate

Ordinary reversible Lite decisions default to one packet-bound situated judgment. A challenge view activates only under material contamination signals or an explicit independent-review request.

Full defaults to both views. Reconciliation runs only on material conflict. The maximum normal semantic sequence is therefore:

```text
Lite ordinary: situated
Lite contaminated: challenge + situated [+ reconciliation on conflict]
Full: challenge + situated [+ reconciliation on conflict]
```

There is no recursive loop.

## Adversarial Cases Required

1. Challenge prefers switching; real non-interruptible migration state supports waiting until a checkpoint.
2. Challenge and situated both select the same threshold-essential blocker.
3. Prior conclusion is quarantined while its reproducible test evidence remains admitted.
4. One candidate has strong evidence and another has only an assumption; structural alignment preserves the difference.
5. Input attempts to pre-label a candidate `threshold_essential`; validation rejects it.
6. Ordinary Lite decision has no contamination signal and uses one situated judgment only.
7. Full decision uses two mutually hidden judgments.
8. Conflict lacks sufficient evidence and ends `blocked` or `request_missing_context`.
9. Candidate packet omits an obvious hard-risk alternative and coverage review reports incomplete rather than allocating.
10. Reversing candidate input order does not alter packet identities or comparison result.

## Claim Ceiling

Supported claim after implementation and tests:

> SRA can use an independent challenge view and an independent situated view to expose incumbent-context bias while preserving real execution-state constraints, with targeted reconciliation on material conflict.

Unsupported claims:

- two views guarantee the correct priority;
- challenge judgment is objective truth;
- agreement proves candidate coverage;
- fresh context proves absence of hidden host context;
- the runtime computes optimal ROI.

## Implementation Verification

The replacement was implemented directly on `feat/sra-context-isolated-runtime`:

- candidate input rejects pre-decided SRA role and score fields;
- challenge and situated packets are generated before either judgment exists;
- neither packet contains the other judgment;
- ordinary uncontaminated Lite uses `situated_only`;
- contaminated Lite and Full use `dual_view`;
- challenge aliases are input-order-independent;
- real evidence asymmetry remains visible;
- typed comparison chooses no winner;
- agreement finalizes the situated judgment without another Agent;
- conflict generates one bounded reconciliation packet;
- packet coverage review can block but cannot allocate;
- old `blind_result_changed` and linear override semantics are absent from the active
  runtime and method contract.

Deterministic evidence:

```text
SRA context-calibration tests             27 PASS
SRA + method-layering focused suite       50 PASS
Test Lifecycle executable coverage        72 / 72
full unittest suite                       919 PASS, 5 skipped
release-pack build                        PASS across all supported layouts
SRA Skill entry                           10,107 / 10,240 bytes
TPlan hook/schema/runtime diff             EMPTY
```

The tests include agreement, material conflict, unresolved conflict, coverage blocking,
role-prejudgment rejection, evidence asymmetry, candidate order reversal, challenge
identity isolation, situated state retention, sunk-cost rejection, single-view Lite,
read-only carriers, packet tampering, and one-pass reconciliation.

Live fresh-carrier semantic qualification remains unavailable while the OCI Codex
endpoint returns HTTP 401. No claim of natural-model priority accuracy is made from the
deterministic suite.

## Final Verdict

The priority-effectiveness architecture passes. The nine conditions are implemented in
the canonical runtime, not left as documentation-only guardrails. The supported claim is
limited to a context-calibrated, action-bearing allocation process with explicit
challenge, situated state, typed disagreement, and bounded reconciliation. It does not
prove universally correct priority or optimal ROI.
