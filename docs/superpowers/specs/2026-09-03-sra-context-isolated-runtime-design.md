# SRA Context-Isolated Hybrid Runtime Design

Status: implemented / deterministic qualification complete; live fresh-carrier model execution blocked by OCI authentication
Date: 2026-09-03
Parent issue: https://github.com/rv198-star/Mindthus/issues/156
Implementation issue: https://github.com/rv198-star/Mindthus/issues/157

## Decision

Extend `SRA / Scarce Resource Allocation / 稀缺资源优先分配` from a prompt-led
judgment Skill with a final shape validator into a hybrid Skill:

```text
context-rich outer caller
    -> scripted context admission and candidate normalization
    -> sealed allocation packet
    -> relatively independent Agentic allocation judgment
    -> scripted packet-bound validation and user-facing rendering
    -> outer workflow or human executes the decision
```

The goal is not context-free judgment. SRA needs the current objective, user constraints,
evidence, candidates, resource boundaries, and decision authority. The goal is
`relative independence`:

> The allocation owner receives only decision-relevant, explicitly classified,
> provenance-bearing context; ambient conversation, prior conclusions, advocacy,
> current-task richness, and sunk-cost narrative do not silently gain evidential or
> decision authority.

SRA remains the semantic allocation owner. Scripts own deterministic workflow,
normalization, hashes, state transitions, reference checks, and rendering. Evidence
constrains claims. The outer caller or TPlan retains execution and mutation authority.

## WAE Diagnosis

SRA currently occupies this WAE quadrant:

```text
workflow certainty: high
context certainty: low or mixed
```

The method order is stable:

1. define the allocation frame;
2. scan the candidate horizon;
3. contract current allocation or bundle hypotheses;
4. identify the current floor;
5. replenish the next meaningful tranche;
6. bound the commitment and reranking trigger.

The semantic answers remain contextual and uncertain:

- which candidate is truly threshold-essential;
- which evidence is strong enough;
- which unknown can change direction;
- which bundle is currently sufficient;
- where the next tranche creates the most value;
- whether switching cost changes the result.

The current implementation leaves both the deterministic order and semantic judgment to
the same Agent, then validates only the final artifact. This creates two control
mismatches:

- `Workflow underreach`: stable method order and recoverable state remain implicit in
  Agent memory;
- `Agentic contamination risk`: the same context that generated or defended current
  work also decides whether that work should continue receiving resources.

The repair is a fixed workflow shell around a packet-bound Agentic core.

## Threat Model

The runtime should reduce these common allocation distortions.

### Active-task capture

The current task has more detail, emotional salience, and implementation history than
alternatives. Richness is mistaken for priority.

### Prior-conclusion authority

A previous Agent or stakeholder conclusion appears in the context and is silently reused
as evidence rather than treated as a claim to review.

### Advocacy asymmetry

One candidate is described by its advocate while alternatives are represented by terse
labels or objections.

### Recency and presentation-order bias

The last-mentioned or first-listed candidate receives more attention without a valid
resource reason.

### Sunk-cost narrative

Historical effort is presented as a reason to continue, while future switching cost,
remaining cost, and reusable assets are not separated.

### Cross-project or historical leakage

Older goals, preferences, unresolved tasks, or another project's context influence the
current allocation without being admitted as relevant inputs.

### User-frame overreach

Current user values and explicit constraints should influence the allocation. User or
stakeholder factual claims still require evidence and must not become facts merely
because they are strongly framed.

### Packet omission

The outer caller can still omit a real candidate or relevant fact. The runtime cannot
prove complete world coverage, but it can require a candidate-horizon declaration,
known omissions, source inventory, and a blocked result when the comparison surface is
not credible.

## Definition Of Relative Independence

SRA supports three isolation profiles.

### `packet_bound`

The current Agent judges from a sealed packet and must cite packet IDs only. This is the
minimum supported profile and the lowest-cost default for ordinary Lite decisions.

It provides logical isolation and traceability. It does not prove that the model has
forgotten ambient context. Explicitly retaining `packet_bound` under Full or declared
contamination pressure requires an `isolation_override_reason`; the runtime preserves a
degraded-isolation warning rather than silently treating the weaker profile as equivalent.

### `fresh_context`

A fresh subagent or ephemeral CLI receives the sealed packet and SRA judge contract
without the surrounding task conversation. The generated carrier is read-only and may
not mutate files, tasks, Mission state, or external systems.

This is preferred when:

- SRA is explicitly asked for an independent judgment;
- a previous Agent conclusion or strong candidate advocacy exists;
- one candidate has materially richer context;
- the decision will stop or redirect heavily invested work;
- the commitment is major or hard to reverse.

The runtime records the requested carrier and persists any supplied receipt. A fresh
carrier without a receipt remains a declared claim and produces a warning. A receipt is
still only an observable artifact; it does not prove the host supplied no hidden
context.

### `blind_then_state`

Use two packet-bound Agentic passes:

1. `blind`: compare normalized candidates without active-path identity, historical
   spend, switching cost, reusable assets, remaining-cost state, or evidence and
   assumptions used only by those state records;
2. `state_aware`: reconcile the blind result with current-path identity, real switching
   cost, reusable assets, remaining cost, commitments, and authority.

When the host supports fresh contexts, each pass should run in a separate fresh context.
This is the strongest initial profile and the default target for Full or high-contamination
cases.

The second pass must state whether state information changed the blind result and why.
Each adjustment cites registered `state_id` values; changing the blind result without
cited admitted state fails closed. Every state item must itself cite admitted evidence
or an explicit assumption. Structured state prose without provenance cannot influence
reconciliation. Sunk cost is visible only as a rejected continuation basis; it cannot
justify the adjustment.

## Control Ownership

| Surface | Owner | Boundary |
|---|---|---|
| Raw context and candidate collection | Outer caller | Supplies claims and sources; does not decide final allocation |
| Context-kind policy and admission mechanics | Workflow | Classifies allowed lanes, quarantines default-risk kinds, records overrides |
| Context relevance and candidate sufficiency | Agentic SRA | May challenge admission, request missing candidate data, or return blocked |
| Candidate normalization and ordering | Workflow | Stable IDs, equal fields, deterministic order, blind aliases, packet-specific output schemas |
| Necessity, feasibility, contraction, replenishment | Agentic SRA | Semantic allocation judgment |
| Evidence references and claim ceilings | Evidence bridge | Claims cite admitted evidence or explicit assumptions |
| Packet hashes, stage order, ID/reference validation | Workflow | Deterministic and fail-closed |
| Final execution or task mutation | Outer workflow, TPlan, or human | SRA provides the decision; it does not mutate Mission/task state |

## Context Admission Ledger

Every supplied context item uses one semantic kind:

- `current_instruction`
- `user_constraint`
- `authority_decision`
- `observed_fact`
- `runtime_evidence`
- `assumption`
- `historical_context`
- `candidate_advocacy`
- `previous_conclusion`
- `ambient_inference`

Deterministic default policy:

| Kind | Default treatment |
|---|---|
| current instruction | admitted as current authority |
| user constraint | admitted as a value/risk/target constraint, not factual proof |
| authority decision | admitted inside its declared scope and expiry |
| observed fact / runtime evidence | admitted with source and claim ceiling |
| assumption | admitted as assumption with overturn condition |
| historical context | quarantined by default; requires explicit scoped admission plus evidence/assumption support; never inherits current authority |
| candidate advocacy | quarantined as a candidate claim, not evidence |
| previous conclusion | quarantined; may be inspected as a claim, not reused as proof |
| ambient inference | quarantined unless explicitly restated as an assumption |

The ledger retains admitted, quarantined, and excluded items. Nothing disappears silently.
Every applicable run contains at least one `current_instruction`. Current instructions,
current user constraints, and authority decisions cannot be silently excluded by the
outer caller. Historical context uses `requested_disposition: admit` only after the outer
caller binds it to current decision relevance and admitted evidence or an explicit
assumption. An override requires an explicit rationale and does not convert advocacy or
a previous conclusion into observed fact.

## Candidate Normalization

Every candidate must use the same minimum card:

```text
candidate_id
title
objective_contribution
resource_demand
dependency_or_bundle_role
delay_cost_or_opportunity_window
irreversibility_or_downside
evidence_refs
assumption_refs
```

Workflow rules:

- candidate IDs are stable;
- blind aliases are generated deterministically from a content-derived ordering, not
  current task order;
- every candidate exposes the same fields;
- missing fields remain explicit;
- evidence and assumption references must resolve;
- large description/evidence asymmetry produces a warning;
- row count never creates a stronger resource claim;
- the blind packet excludes active candidate identity and state-only fields.

The Agentic judge may still conclude that the candidate surface is insufficient. The
script does not decide that the strongest alternative has truly been found.

## Sealed Allocation Packet

`prepare_sra_run.py` creates a run directory containing:

```text
run.json
raw-input.json
context-admission.json
sealed-packet.json
blind-packet.json
blind-agent-prompt.md
blind-output-schema.json
blind-subagent-dispatch.json
blind-codex-command.sh
fresh-context-workspace/
trace.jsonl
```

The sealed packet contains only:

- the allocation frame;
- normalized candidates;
- admitted constraints, evidence, assumptions, and scoped history;
- declared contamination signals;
- known omissions;
- packet and context-manifest hashes.

The packet excludes raw ambient conversation and quarantined conclusions from the
judgment surface.

## Blind Judgment

The blind judge receives aliases and normalized cards, not original titles or current
path identity. It must return:

```text
packet_hash
candidate assessments
feasibility / role / contraction result
first break point
current floor
provisional next tranche
missing information
evidence and assumption references
claim ceiling
```

Every candidate must appear in the assessment. References outside the sealed packet are
rejected.

The blind result is itself hashed and locked before state-aware information is exposed.

## State-Aware Reconciliation

After a valid blind result is recorded, the runtime produces:

```text
state-packet.json
state-aware-agent-prompt.md
state-aware-output-schema.json
state-aware-subagent-dispatch.json
state-aware-codex-command.sh
```

The state packet adds only:

- blind-to-original candidate mapping;
- current candidate identity;
- switching costs;
- reusable assets;
- remaining costs;
- current commitments and authority boundaries;
- historical spend labelled as sunk-cost-only;
- the locked blind judgment and its hash.

The final Agentic judgment must state:

- whether the blind result changed;
- which admitted state facts caused the change;
- why sunk cost did not control the result;
- current floor;
- next tranche;
- investment ceiling and authorization horizon;
- maintenance, reserve, defer, and stop lanes;
- reranking triggers;
- evidence/assumption references and claim ceiling.

## Runtime State Machine

```text
prepared
    -> blind_recorded
    -> finalized
```

Scripts fail closed when:

- a packet or judgment hash does not match;
- a stage is skipped or repeated inconsistently;
- candidate/evidence/assumption references are unknown;
- a blind judgment uses original candidate IDs or state-only information;
- a state judgment omits the blind hash;
- the final decision authorizes an unbounded Lite continuation;
- state adjustment cites historical spend as a continuation reason;
- a state adjustment cites an unknown or wrong-kind `state_id`;
- the blind result changes without cited admitted state;
- a packet claims stronger isolation than its observable carrier supports.

## Script Surface

### `sra_runtime.py`

Shared deterministic helpers for canonical JSON, hashes, admission policy, packet
construction, packet-specific Agent output schemas, run state, trace events, prompt
generation, and validation.

### `prepare_sra_run.py`

Validates raw input, applies deterministic context-admission policy, normalizes
candidates, seals the packet, creates blind aliases, generates a packet-bound output
schema, and creates logical/fresh-context carrier artifacts.

### `record_sra_judgment.py`

Records and validates `blind` or `state-aware` Agentic output. Recording the blind result
generates the state-aware packet and its output schema. Recording the state-aware result
finalizes the run.

### `check_sra_run.py`

Validates run files, hashes, stage order, reference integrity, context isolation claims,
and recoverability. It does not judge semantic priority.

### `render_sra_decision.py`

Renders the final decision in a short user-facing form without exposing the entire
internal packet.

## Agentic Contract

The SRA judge owns semantic allocation inside the packet boundary.

It must:

- use packet IDs for factual and assumption support;
- challenge an incomplete or asymmetric candidate surface;
- run contraction before naming the current floor;
- run replenishment from that floor;
- preserve target and risk floor;
- distinguish switching cost, reusable assets, remaining cost, and sunk cost;
- return `blocked` rather than invent missing priority;
- keep claims below the admitted evidence ceiling.

It must not:

- import ambient facts or prior conclusions without packet admission;
- treat user values as factual proof;
- compute a universal weighted priority score;
- mutate project or Mission state;
- claim optimal ROI or universally correct prioritization.

## Lite And Full

Both modes use the context-admission and sealed-packet boundary.

### Lite

- defaults to `packet_bound`;
- upgrades to `fresh_context` when contamination signals are present and a fresh carrier
  is available;
- performs one micro-contraction and one micro-replenishment;
- authorizes one action, one tranche, or one named checkpoint;
- may use one fresh pass when two-pass isolation costs more than the reversible allocation
  error.

### Full

- targets `blind_then_state`;
- persists packet, blind result, state reconciliation, and final decision;
- may use two fresh contexts when the host supports them;
- records a decision lifetime and explicit reranking triggers.

The analysis-cost gate still applies. Isolation cannot become a larger waste than the
allocation error it protects against.

## Evidence Boundary

The runtime can prove:

- which context items were supplied, admitted, quarantined, or excluded;
- which packet the judgment referenced;
- whether IDs and hashes match;
- whether the blind pass preceded state reconciliation;
- which evidence and assumptions were cited;
- which carrier was requested and which observable receipt was supplied.

It cannot prove:

- complete world context;
- that an outer caller classified every context item correctly;
- that a host supplied no hidden system context;
- that the true strongest alternative was included;
- that the semantic priority is correct;
- that fresh-context execution occurred without a trusted external receipt.

## Pressure Tests

Add cases for:

1. richly described active task versus terse threshold-essential alternative;
2. previous Agent conclusion recommending continuation;
3. stakeholder advocacy with no evidence;
4. user value constraint plus unsupported factual claim in the same statement;
5. historical project goal that conflicts with the current request;
6. candidate order reversal producing the same blind packet order;
7. sunk-cost narrative that changes the state-aware decision without valid switching
   evidence;
8. missing candidate/evidence references;
9. logical packet mode incorrectly claiming fresh-context isolation;
10. Full judgment that skips the blind pass;
11. clean fresh-context carrier artifacts using read-only, ephemeral, rule-disabled
    execution;
12. candidate-context asymmetry warning without automatic semantic verdict.

## Implementation Scope

Phase 1.5 creates:

- `skills/sra/resources/context-isolation.md`;
- `skills/sra/templates/context-input.json`;
- `skills/sra/templates/blind-judgment.json`;
- `skills/sra/templates/state-aware-judgment.json`;
- `skills/sra/scripts/sra_runtime.py`;
- `skills/sra/scripts/prepare_sra_run.py`;
- `skills/sra/scripts/record_sra_judgment.py`;
- `skills/sra/scripts/check_sra_run.py`;
- `skills/sra/scripts/render_sra_decision.py`;
- `tests/test_sra_context_isolation.py`;
- SRA Skill, methodology, design, packaging, and Test Lifecycle updates.

This phase does not:

- call a model automatically;
- require a specific host;
- create a global memory or retrieval system;
- scrape the entire conversation automatically;
- decide context relevance semantically in code;
- change TPlan hooks, schema, Pulse, continuation, or mutation authority;
- claim absolute isolation or correct priority.

## Acceptance Criteria

- [x] SRA explicitly defines relative independence as admitted packet context, not
      context-free judgment.
- [x] Every applicable run creates a context-admission ledger and sealed packet.
- [x] Previous conclusions, advocacy, and ambient inferences are quarantined by default.
- [x] Current user constraints remain decision constraints without becoming factual
      evidence.
- [x] Blind candidate ordering is deterministic and independent of input order.
- [x] Blind packets omit active-path identity, historical spend, switching cost,
      reusable assets, remaining cost, commitments, authority state, and state-only
      evidence or assumptions.
- [x] A valid blind result is recorded and hashed before state-aware reconciliation.
- [x] State reconciliation may change the blind result only with cited admitted
      `state_id` references of the matching adjustment kind, and each state item is
      evidence- or assumption-bound.
- [x] Packet and judgment references fail closed on unknown IDs or hash mismatch.
- [x] Lite remains bounded and low-cost; Full persists the two-stage trace.
- [x] Generated fresh-context carriers use fresh/no-fork semantics where available,
      read-only authority, and no project mutation.
- [x] Fresh carrier claims without persisted receipts remain explicitly unverified and
      produce a warning.
- [x] Same-context packet mode is labelled logical isolation and cannot claim fresh
      context; Full or contamination-pressure overrides require a recorded reason and
      remain visibly degraded.
- [x] Scripts validate workflow and evidence shape only; semantic allocation remains
      Agentic.
- [x] TPlan runtime ownership remains unchanged.
- [x] All new executable tests are registered in Test Lifecycle.
- [x] Full repository suite remains green.

## Implementation Evidence

Deterministic qualification on 2026-09-03:

```text
git diff --check                         PASS
python3 -m compileall -q skills scripts PASS
Test Lifecycle executable coverage      72 / 72
full unittest suite                      920 PASS, 5 skipped
release-pack all-platform build          PASS
SRA entry size                           9,983 / 10,240 bytes
TPlan hooks/schema/runtime diff          EMPTY
```

A real generated Codex fresh-context carrier was invoked from its empty read-only
workspace with packet-specific output schema. The CLI reached the model transport but
returned HTTP 401 because the OCI node has no usable API credential. No model judgment
was produced, and this is recorded as an environment limitation rather than a semantic
or isolation pass.

## Release Claim Ceiling

Supported claim after implementation and deterministic tests:

> SRA can run through a packet-bound hybrid workflow that classifies context, normalizes
> candidates, separates blind and state-aware judgment, validates references and hashes,
> and supports fresh-context carriers without giving scripts semantic priority authority.

Unsupported claims:

- SRA is free from all context influence;
- the packet contains all relevant facts or candidates;
- a fresh-context carrier guarantees absence of hidden host context;
- context isolation proves the resulting priority is correct;
- the workflow maximizes ROI or replaces human decision authority.
