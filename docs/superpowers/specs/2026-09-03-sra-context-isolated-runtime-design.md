# SRA Context-Calibrated Independent Judgment Runtime Design

Status: implemented / deterministic qualification complete; live fresh-carrier semantic qualification pending usable OCI authentication
Date: 2026-09-03
Parent issue: https://github.com/rv198-star/Mindthus/issues/156
Implementation issue: https://github.com/rv198-star/Mindthus/issues/157
Pull request: https://github.com/rv198-star/Mindthus/pull/158

## Decision

Replace the current linear `blind -> state-aware override` design with a context-calibrated
dual-view runtime:

```text
context-rich outer caller
    -> context admission and candidate structural alignment
    -> shared decision base
       -> independent de-anchored challenge
       -> independent situated judgment
    -> typed comparison
       -> agree: finalize situated judgment
       -> conflict: one targeted reconciliation
    -> outer workflow or human executes the decision
```

Core principle:

> SRA is independent from inherited conclusions, not independent from relevant context.
> It isolates narrative authority while retaining facts, constraints, evidence, user
> values, decision authority, and real execution state.

Candidate structure is aligned without flattening evidence differences. The challenge
view calibrates incumbent-context bias. The situated view remains action-bearing because
it includes future switching cost, remaining cost, reusable assets, current commitments,
and path state. Neither view receives the other view's output.

## Why The Previous Topology Was Rejected

The previous runtime improved on ambient-context judgment but introduced a new anchor:

```text
blind judgment locked first
    -> state-aware Agent sees blind conclusion
    -> state-aware Agent must explain whether it changed the blind result
```

That structure implicitly granted the blind judgment default authority. Real execution
state became an exception that had to overturn the baseline, even though switching cost,
path dependency, remaining cost, and commitments are normal parts of allocation.

It also allowed the outer candidate card to include fields such as
`dependency_or_bundle_role`, which could disclose `threshold-essential` or
`value-expanding` before SRA performed its own semantic judgment.

The replacement removes both defects directly. There is no compatibility mode for the
old judgment topology.

## Audit Basis

Two independent audits approved this replacement with mandatory conditions:

- `docs/internal/audits/2026-09-03-sra-dual-view-priority-audit.md`
- `docs/internal/audits/2026-09-03-sra-dual-view-wae-architecture-audit.md`

The first audit evaluated priority quality, omission risk, evidence asymmetry, anchoring,
and analysis cost. The second evaluated Workflow / Agentic / Evidence ownership,
ownership closure, instruction/data separation, TPlan boundaries, and runtime cost.

Both concluded that the topology is sound only when the two judgments are mutually
hidden, input roles are not pre-decided, comparison is mechanical, reconciliation is
bounded, and ordinary Lite does not pay Full runtime cost.

## WAE Diagnosis

SRA occupies:

```text
workflow certainty: high
context certainty: low or mixed
```

Workflow owns:

- context-kind lanes;
- stable packet construction;
- candidate structural alignment;
- deterministic challenge aliases;
- packet-specific output schemas;
- hashes and references;
- view-plan and coverage-plan state;
- typed comparison;
- one-pass reconciliation gating;
- user-facing rendering.

Agentic owns:

- context relevance challenges;
- packet-coverage judgment when requested;
- feasibility and candidate role;
- necessity and minimum sufficient bundle judgment;
- contraction and first break point;
- replenishment and next tranche;
- situated execution-state interpretation;
- conflict reconciliation.

Evidence owns:

- source and observed time;
- claim ceiling;
- explicit assumptions and overturn conditions;
- references supporting load-bearing claims;
- observable carrier receipts.

The outer caller, TPlan, or human owns execution and mutation. SRA does not mutate a
project, task tree, Mission state, or external system.

## Threat Model

The runtime reduces:

- active-task capture;
- prior Agent conclusion inheritance;
- candidate advocacy asymmetry;
- input-order and recency bias;
- sunk-cost continuation pressure;
- cross-project historical leakage;
- unsupported facts hidden inside user preference statements;
- post-hoc completion of a method form after an intuitive decision;
- challenge-view anchoring of the situated judge.

It cannot prove complete candidates, complete facts, correct context classification,
absence of hidden host context, or correct priority.

## Context Admission

Kinds:

```text
current_instruction
user_constraint
authority_decision
observed_fact
runtime_evidence
assumption
historical_context
candidate_advocacy
previous_conclusion
ambient_inference
```

Default lanes:

| Kind | Default |
|---|---|
| current instruction | admitted as current authority |
| user constraint | admitted as a value/target/risk constraint, not factual proof |
| authority decision | admitted inside declared scope and expiry |
| observed fact / runtime evidence | admitted inside source and claim ceiling |
| assumption | admitted with overturn condition |
| historical context | quarantined unless explicitly scoped and evidence/assumption-bound |
| candidate advocacy | quarantined as a claim |
| previous conclusion | quarantined; supporting evidence is extracted separately |
| ambient inference | quarantined unless restated as an assumption |

Protected current instruction, user constraints, and authority decisions cannot be
silently excluded. Quarantine removes inherited authority, not audit visibility.

## Candidate Structural Alignment

Input card:

```text
candidate_id
action_statement
expected_target_effect
resource_demand
depends_on
unlocks
substitutes_for
deadline_or_window
downside
reversibility
evidence_refs
assumption_refs
```

Input rejects semantic result fields, including:

```text
candidate_role
dependency_or_bundle_role
hard_gate
threshold_essential
value_expanding
priority
priority_score
roi_score
```

Workflow aligns fields, IDs, ordering, and references. It does not equalize evidence or
description length. Presentation asymmetry creates a warning, not a verdict.

## View Selection

### Ordinary Lite

Default:

```text
situated_only
```

Use one packet-bound situated judgment when the decision is local, reversible, and free
of material incumbent-context contamination. It still performs one micro-contraction and
one micro-replenishment and authorizes only one action, one tranche, or one checkpoint.

### Contaminated Lite

Use:

```text
dual_view
```

when prior conclusions, active-task richness, advocacy asymmetry, sunk-cost narrative,
presentation order, cross-project context, explicit independent review, or major
redirection can materially distort the result.

### Full

Full defaults to `dual_view`. A conditional packet-coverage review activates when known
omissions or explicit coverage-risk signals could change the candidate surface.

## Packet Coverage Review

Coverage review receives source inventory, candidate cards, evidence, assumptions,
context ledger, and known omissions. It may return only:

```text
packet_ready
packet_ready_with_warning
packet_incomplete
```

It cannot classify SRA roles or choose allocation. `packet_incomplete` blocks the run
and requires a new packet.

## Shared Decision Base

The shared base contains:

- objective, target threshold, time window, risk floor, user values, and authority;
- structurally aligned candidates;
- candidate-linked evidence and explicit assumptions;
- admitted common context;
- known omissions;
- contamination and coverage signals;
- instruction/data boundary.

All packet strings are data. Instruction-like text inside candidate, evidence, history,
or advocacy records cannot change tool or workflow authority.

## Challenge View

The challenge packet hides:

- original candidate IDs;
- active candidate identity;
- switching cost;
- remaining cost;
- reusable assets;
- commitments;
- historical spend;
- prior conclusions and candidate advocacy.

It preserves current objective, values, authority, evidence, assumptions, dependencies,
windows, downside, and reversibility.

The challenge asks what survives contraction when incumbency receives no special
privilege. It is a calibration view, not automatic final authority.

## Situated View

The situated packet includes the common decision base and evidence- or
assumption-bound:

- active candidate identity;
- switching costs;
- remaining costs;
- reusable assets;
- current commitments and authority state;
- historical spend labelled as sunk-cost-only.

It does not include the challenge judgment, prior allocation conclusions, or advocacy.
It independently produces the action-bearing allocation.

## Typed Comparison

Workflow maps challenge aliases to original candidate IDs and compares only:

```text
allocation_outcome
current_floor
next_tranche_candidate
authorization_horizon
reserve
maintenance
defer
stop
```

Workflow does not compare prose semantically and does not choose a winner.

- `agree`: finalize the situated judgment; record challenge corroboration.
- `conflict`: generate a targeted reconciliation packet.

Agreement is not proof of candidate completeness or correct priority.

## Targeted Reconciliation

The reconciliation packet contains:

- common frame and candidates;
- normalized challenge and situated decision cores;
- exact conflict fields;
- evidence, assumptions, and state items cited by either view;
- known omissions.

It excludes ambient conversation, prior conclusions, candidate advocacy, and unrelated
reasoning prose.

Allowed outcomes:

```text
allocate
conditional
infeasible
blocked
request_missing_context
```

The reconciler resolves each conflict field or remains blocked. One packet version
allows one reconciliation only. New material context creates a new run rather than an
Agentic loop.

## Runtime Status Model

```json
{
  "coverage": "not_required | pending | recorded_ready | recorded_warning | recorded_incomplete",
  "challenge": "not_required | pending | recorded",
  "situated": "pending | recorded",
  "comparison": "not_required | pending | agree | conflict",
  "reconciliation": "not_required | pending | recorded",
  "finalization": "pending | finalized | blocked"
}
```

Challenge and situated judgments may be recorded in either order. They are generated
from independent packets before either result exists.

## Runtime Files

```text
raw-input.json
context-admission.json
base-packet.json
coverage-packet.json
challenge-packet.json
situated-packet.json
coverage/challenge/situated prompts and packet-specific schemas
judgments/*.json
comparison-report.json
reconciliation-packet.json       # conflict only
final-decision.json
trace.jsonl
```

## Carrier Boundary

Generated carriers use:

- `fork_context: false` for subagent dispatch;
- no tools;
- read-only authority;
- no file, Mission, task, memory, or external-system mutation;
- ephemeral CLI execution with an empty workspace;
- packet-specific output schemas.

Recorded carrier labels and receipts establish only observable execution facts. They do
not prove that the host supplied no hidden system context.

## Analysis-Cost Boundary

Maximum normal Agentic path:

```text
ordinary Lite:
  situated

contaminated Lite:
  challenge + situated
  + reconciliation only on conflict

Full:
  optional coverage
  + challenge + situated
  + reconciliation only on conflict
```

No recursive loop exists. Another round requires a new material packet and a new run.

## Implementation Surface

Canonical runtime:

```text
skills/sra/resources/context-isolation.md
skills/sra/templates/context-input.json
skills/sra/templates/coverage-judgment.json
skills/sra/templates/challenge-judgment.json
skills/sra/templates/situated-judgment.json
skills/sra/templates/reconciliation-judgment.json
skills/sra/scripts/sra_runtime.py
skills/sra/scripts/prepare_sra_run.py
skills/sra/scripts/record_sra_judgment.py
skills/sra/scripts/check_sra_run.py
skills/sra/scripts/render_sra_decision.py
tests/test_sra_context_isolation.py
```

The resource and design file paths retain their existing branch paths, but their
canonical semantics are context calibration and dual-view judgment. No old runtime
contract remains active.

## Acceptance Criteria

- [x] Two independent audits approve the topology with explicit conditions.
- [x] Input rejects pre-decided SRA role and score fields.
- [x] Candidate structural alignment preserves real evidence asymmetry.
- [x] Current instructions, user constraints, and scoped authority remain admitted.
- [x] Prior conclusions and advocacy remain visible but lack inherited authority.
- [x] Ordinary Lite can use situated-only judgment.
- [x] Full and contaminated cases use dual view by default.
- [x] Challenge and situated packets do not include each other's results.
- [x] Challenge omits active-path identity and state-only costs.
- [x] Situated judgment retains real execution state and rejects sunk-cost authority.
- [x] Comparison is typed and chooses no winner.
- [x] Conflict creates at most one targeted reconciliation.
- [x] Coverage review cannot choose allocation.
- [x] Packet content remains data and cannot alter tool authority.
- [x] Scripts do not compute semantic priority or ROI.
- [x] TPlan hooks, schema, continuation, Pulse, and mutation remain unchanged.
- [x] Full repository regression and release-pack qualification pass after replacement.
- [ ] Live fresh-carrier semantic tests run when a usable credential is available.

## Deterministic Qualification Evidence

```text
SRA context-calibration tests             27 PASS
SRA + method-layering focused suite       50 PASS
Test Lifecycle executable coverage        72 / 72
full unittest suite                       919 PASS, 5 skipped
release-pack build                        PASS across all supported layouts
SRA Skill entry                           10,107 / 10,240 bytes
TPlan hook/schema/runtime diff             EMPTY
```

A generated fresh-context Codex carrier remains blocked by HTTP 401 before model
execution. The deterministic suite therefore supports the workflow and ownership claim,
not natural-model priority accuracy.

## Claim Ceiling

Supported after deterministic qualification:

> SRA can organize relevant context into structurally aligned packets, obtain an
> independent de-anchored challenge and an independent situated allocation, compare
> typed results, and reconcile only material conflicts without giving scripts semantic
> priority authority.

Unsupported:

- dual views guarantee correct priority;
- challenge is objective truth;
- agreement proves complete candidates;
- fresh carriers prove absence of hidden host context;
- the runtime computes optimal ROI;
- SRA replaces human or TPlan execution authority.
