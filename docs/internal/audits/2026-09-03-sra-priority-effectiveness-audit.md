# SRA Priority-Effectiveness Implementation Audit

Date: 2026-09-03  
Issue: #156  
Canonical branch: `feat/sra-implementation`  
Reviewed commit: `4f79446b`  
Verdict: **PASS WITH CLAIM CEILING**  
Live semantic qualification: **NOT RUN — OCI Codex returned HTTP 401 before model execution**

## Audit Question

Can the implemented SRA contract help an agent identify what should receive scarce
resources now, while protecting necessary work, high-value work, and the cost of the
judgment itself?

This pass reviews allocation effectiveness only. Method ownership and integration are
covered by the separate architecture audit.

## Evidence Boundary

This audit verifies repository contracts, the deterministic validator, pressure-case
coverage, and regression state. It cannot prove that a model will always discover the
true best alternative or choose the objectively correct real-world priority.

A separate read-only Codex review was attempted during the implementation work. The OCI
node returned `401 Unauthorized` before model execution, so that attempt is recorded as
an environment limitation and is not counted as independent model evidence.

## Cross-Session Reconciliation

Two parallel implementations appeared during development:

1. one preserved the approved `Lite / Full` split, but Lite could degrade into a generic
   current-task-versus-alternative comparison;
2. one forced contraction and replenishment in every SRA use, but removed the explicit
   Lite/Full contract approved by the maintainer.

The canonical implementation combines the valid parts of both:

- Lite remains the default fast mode;
- Full remains the expanded mode;
- both preserve one semantic core;
- Lite executes one bounded `micro-contraction` and one `micro-replenishment`;
- Full expands the same operations across bundles, resource channels, realistic pressure
  scenarios, and decision lifetimes.

This prevents Lite from becoming ordinary priority ranking while keeping the analysis
cost proportionate to the decision.

## Required Priority Mechanisms

The implementation applies this order before ROI-style comparison:

```text
hard gate
-> feasible bundle
-> threshold-essential work
-> direction / bottleneck / opportunity window
-> risk-adjusted bundle value
-> marginal meaningful tranche
-> reserve
```

It also contains:

- `direct / lite / full / blocked` entry outcomes;
- an analysis-cost gate that starts from Lite;
- a Candidate Horizon Probe that scans beyond the active task;
- evidence-bounded current minimum sufficient bundles;
- separate resource channels and fixed-threshold investments;
- meaningful resource tranches rather than arbitrary tiny units;
- sunk-cost, switching-cost, reusable-asset, and remaining-cost separation;
- explicit maintenance, defer, stop, and reserve postures;
- bounded Lite authorization;
- Full feasibility, dominance, contraction, replenishment, and stop conditions;
- an explicit claim ceiling.

## Findings And Remediation

### P1 — Lite Could Lose SRA Method Identity

The first Lite contract compared the current path with the strongest alternative and
selected the next tranche, but it did not require the resource floor to be discovered by
contraction. That allowed an answer to look like SRA while performing only generic
prioritization.

Remediation:

- every applicable SRA artifact now requires `contraction` and `replenishment` moves;
- Lite records one micro-contraction, its `current_floor`, and one
  micro-replenishment;
- the validator rejects Lite artifacts missing either move or the current floor;
- pressure Scenario 30 rejects generic prioritization presented as Lite SRA;
- Full keeps the expanded bundle-level loop.

Status: **FIXED**.

### P1 — Lite Candidate Horizon Was Not Structurally Recoverable

The initial decision carrier recorded a prose Candidate Horizon move but did not require
the actual candidates or postures considered.

Remediation:

- `lite_decision.considered_candidates` is required;
- it contains two to four non-empty labels;
- the template records current path, strongest alternative, and maintenance posture;
- a negative test rejects a one-item candidate horizon.

This does not prove that the strongest real alternative was found. It prevents the
artifact from hiding the absence of a comparison set.

Status: **FIXED**.

### P1 — Full Result Could Contradict Its Own Action

The initial validator allowed `allocation_action` and
`full_decision.allocation_outcome` to disagree, and candidate bundles could be malformed.

Remediation:

- Full action uses the Full outcome vocabulary;
- `allocation_action` must equal `allocation_outcome`;
- each candidate bundle requires a non-empty `bundle_id`;
- bundle status is restricted to `feasible`, `infeasible`, `dominated`, or
  `conditional`;
- negative tests cover contradictory outcomes and malformed bundles.

Status: **FIXED**.

### No Unresolved High- Or Medium-Severity Contract Finding

Remaining limits are semantic:

- a recorded candidate horizon may still omit the real best alternative;
- necessity may still be judged incorrectly;
- qualitative risk-adjusted value may still be biased;
- pressure-case definitions do not equal natural host/model behavior.

The claim ceiling and validator truth boundary state these limits explicitly.

## Pressure Coverage

The pressure surface contains 30 cases:

- 5 Lite positive cases;
- 5 Full positive cases;
- 9 direct-execution or neighboring-method boundary cases;
- 11 adversarial cases, including candidate omission, granularity manipulation, sunk
  cost, fixed thresholds, multiple resource channels, infeasibility,
  contraction-replenishment conflict, low-direct-ROI hard gates, analysis overkill,
  reserve capacity, and Lite degeneration into generic prioritization.

Applicable cases require an observable allocation change: next tranche, current floor,
investment ceiling, displaced work, stop/defer, reserve, or reranking trigger. A generic
balanced answer does not pass.

## Mechanical Evidence

Final checks at reviewed commit plus the thin-entry repair:

```text
git diff --check                         PASS
python3 -m compileall -q skills scripts PASS
Test Lifecycle executable coverage      71 / 71
SRA contract tests                      20 / 20 PASS
python3 -m unittest discover -s tests -q
Ran 892 tests                           OK
Skipped                                 5
```

The SRA template passes `validate_sra_output.py` with:

```text
No shape or evidence risks detected.
agentic audit remains required
```

## Claim Ceiling

Supported conclusion:

> SRA provides lightweight and expanded, evidence-bounded allocation contracts that make
> candidate comparison, contraction, replenishment, necessity, resource contention,
> bounded commitment, defer/stop, reserve, and reranking explicit.

Unsupported conclusions:

- SRA always finds the correct priority;
- SRA maximizes ROI;
- SRA computes an optimal allocation;
- the 30 case contracts prove real-world business value;
- a validator pass proves semantic correctness.

## Final Verdict

- Standalone allocation contract: **PASS**.
- Lite/Full shared method identity: **PASS**.
- Phase 2 integration candidate, from an allocation-mechanics perspective: **PASS**.
- Live host/model pressure qualification: **PENDING**.
- Merge or release may claim contract and boundary completion only; it must not claim
  universally correct prioritization or proven business ROI.
