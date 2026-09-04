# SRA v0.3 Context-Calibrated Runtime

## Purpose

SRA should be independent from inherited conclusions without becoming blind to the
current objective, values, authority, evidence, assumptions, and real execution state.
The v0.3 runtime separates those concerns into explicit data surfaces and makes every
allocation commitment mechanically recoverable.

The runtime does not decide priority. It provides a trustworthy carrier for Agentic SRA
judgment.

## Controller Ownership

### Agentic SRA Owns

- normalizing the current question into situated wording and a de-anchored challenge
  projection;
- separating source text into decision-relevant context fragments;
- judging relevance and factual sufficiency;
- candidate feasibility and role;
- minimum sufficient bundle claims;
- contraction and replenishment;
- semantic risk, value, and necessity;
- conflict reconciliation.

### Workflow Owns

- schema versions and version-bound runs;
- declared context admission lanes;
- resource and candidate references;
- quantity-contract compatibility;
- candidate demand and actual allocation compatibility;
- one posture per candidate;
- Full bundle members, IDs, feasibility/dominance code consistency, and selected-bundle
  references;
- capacity and investment-ceiling consequences that follow mechanically from declared
  quantities;
- independent packet construction;
- typed comparison;
- legal state transitions and finalization;
- Prompt, schema, Dispatch, command, packet, judgment, comparison, final-copy, and trace
  reconstruction;
- repair of derived artifacts without rewriting Agentic judgments.

### Evidence Owns

- observable facts and source identity;
- observation time;
- claim ceiling;
- explicit assumptions and overturn conditions.

Workflow validates the declared structure. It does not infer whether a bundle is truly
sufficient, whether a risk is acceptable, or which candidate deserves priority.

## Version Boundary

All active runtime artifacts use v0.3 identifiers. A prepared v0.2 run cannot be resumed
or repaired under v0.3 because its resource carrier, context boundary, bundle model,
comparison core, and finalization semantics differ.

Start a new v0.3 run from the source decision context. Historical v0.2 release artifacts
remain historical evidence; they are not silently rewritten.

## Input Contract

### Decision Question

The caller supplies one object:

```json
{
  "situated_question": "full current-state wording",
  "challenge_projection": "same allocation question without active identity, prior conclusions, or sunk-cost narrative",
  "source": "where the question came from",
  "projection_basis": "what was removed and what meaning was preserved"
}
```

Workflow never performs semantic text splitting. The caller or an Agentic intake step
owns the projection. Workflow rejects a challenge projection that directly contains a
stable original candidate ID.

This check is intentionally bounded. It prevents direct structured identity leakage; it
does not prove that prose is perfectly de-anchored.

### Context Fragments

Each context item has one declared kind:

- `user_constraint`;
- `authority_decision`;
- `observed_fact`;
- `runtime_evidence`;
- `assumption`;
- `historical_context`;
- `candidate_advocacy`;
- `previous_conclusion`;
- `ambient_inference`.

Every admitted item carries:

```text
statement
challenge_projection
projection_basis
source
decision_relevance
candidate_ids
evidence_refs
assumption_refs
```

The situated packet receives `statement`. The challenge packet receives only
`challenge_projection`, with candidate references mapped to challenge aliases.

Deterministic lanes:

| Kind | Default lane |
|---|---|
| user constraint | admitted as decision constraint |
| authority decision | admitted as scoped authority |
| observed fact / runtime evidence | admitted as evidence claim |
| assumption | admitted as explicit assumption |
| historical context | quarantined unless explicitly admitted with evidence or assumption |
| advocacy / previous conclusion / ambient inference | quarantined |

An admitted authority decision also carries `authority_holder`, `authority_scope`, and
`authority_expiry`.

### Resource Pools

Each resource pool declares:

```text
resource_id
label
quantity_contract
capacity
window
```

Quantity contracts are explicit:

```text
measured    -> exact or bounded quantity in one unit
ordinal     -> one level from a declared ordered scale
indivisible -> one or more named blocks
```

Examples:

```json
{
  "resource_id": "engineer-time",
  "quantity_contract": {"family": "measured", "aggregation": "sum", "unit": "engineer-day"},
  "capacity": {"quantity_kind": "exact", "amount": 2, "unit": "engineer-day"}
}
```

```json
{
  "resource_id": "management-attention",
  "quantity_contract": {"family": "ordinal", "aggregation": "exclusive", "scale": ["low", "medium", "high"]},
  "capacity": {"quantity_kind": "ordinal", "level": "medium"}
}
```

```json
{
  "resource_id": "review-slot",
  "quantity_contract": {"family": "indivisible", "aggregation": "set", "blocks": ["slot-a", "slot-b"]},
  "capacity": {"quantity_kind": "indivisible", "blocks": ["slot-a", "slot-b"]}
}
```

Workflow compares quantities only inside the declared resource contract. Measured
resources use additive `sum`, ordinal resources use `exclusive` single-allocation
semantics, and indivisible resources use block-set allocation. It does not convert unlike
resources into one score.

### Candidate Demand

Each candidate declares typed `resource_demand` against resource pool IDs. At least one
pool must be demanded by two or more candidates; otherwise SRA has no demonstrated shared
resource contention.

Actual current allocation, next tranche, and bundle requirements must reference resources
contained in the relevant candidate demand. Measured and bounded quantities cannot exceed
that demand; ordinal levels and indivisible blocks must remain within the declared
candidate boundary.

### Evidence

Every evidence item records:

```text
evidence_id
kind
source
statement
observed_at
claim_ceiling
```

A source without observation time is not current evidence. Timeless evidence should say
so explicitly in `observed_at` rather than silently omitting the field.

### State Context

Situated judgment may receive:

- switching costs;
- reusable assets;
- remaining costs;
- historical spend;
- current commitments;
- active-candidate identity.

Historical spend is marked `sunk_cost` and cannot justify continuation. Current
commitments bind to a declared authority decision.

## Governed Downgrades

A caller may intentionally downgrade:

- Full to Lite;
- dual view to situated-only;
- required coverage to skipped coverage.

Each downgrade needs:

```text
override_reason
approved_by
authority_ref
risk_acceptance_scope
expiry
```

`authority_ref` must resolve to an admitted authority decision. Its holder must match
both `approved_by` and the Allocation Frame's `decision_owner`.

The override is retained in packets, run state, final decision, trace, and human-readable
output. It is never a silent mode switch.

## Packet Topology

### Base Packet

The base packet contains the situated question, Allocation Frame, candidates, shared
evidence and assumptions, admitted situated context, omissions, contamination/coverage
signals, governance overrides, and warnings.

### Coverage Packet

Coverage review is orthogonal to allocation. It checks whether the question projection,
candidate surface, bundle opportunity, resources, evidence, and authority are ready.

Allowed outcomes:

- `packet_ready`;
- `packet_ready_with_warning`;
- `packet_incomplete`.

`packet_incomplete` finalizes the run as blocked with zero allocation.

### Challenge Packet

The challenge packet:

- replaces original candidate IDs with input-order-independent aliases;
- uses only the challenge question projection;
- uses only challenge projections of admitted context;
- omits active-candidate identity, switching cost, reusable assets, remaining cost,
  historical spend, current commitments, prior conclusions, and advocacy;
- retains real candidate actions, relations, typed resource demand, evidence, and
  assumptions.

The challenge view is calibration, not final authority.

### Situated Packet

The situated packet retains:

- full current-state question wording;
- original candidate IDs;
- admitted situated context;
- active identity;
- future switching cost;
- reusable assets;
- remaining cost;
- scoped commitments;
- sunk-cost records under an explicit rejection policy.

It never receives the challenge judgment or comparison report.

## Judgment Carrier

### Candidate Assessments

Each view assesses every packet candidate exactly once:

```text
candidate ID or challenge alias
feasibility
candidate_role
contraction_result
first_break_point
evidence_refs
assumption_refs
```

An infeasible candidate cannot receive current resource, the next tranche, or membership
in a selected actionable bundle.

### Allocation Ledger

Every candidate receives exactly one row:

```text
candidate_id or challenge_id
posture: floor | maintenance | candidate | defer | stop
current_allocations[]
reason
```

Mechanical rules:

- `floor` and `maintenance` carry nonzero current allocation;
- `candidate`, `defer`, and `stop` carry zero current allocation;
- deferred or stopped work cannot receive the next tranche;
- the next-tranche resource must be part of that candidate's demand;
- current plus next commitment cannot exceed the typed investment ceiling;
- current, next, and reserve allocations cannot exceed declared resource capacity.

### Full Bundle Decision

Lite records:

```text
status: not_applicable
bundle_assessments: []
selected_bundle_id: none
```

Full requires bundle assessments. Each bundle records:

```text
bundle_id
bundle members
feasibility
dominance_status
dominated_by
resource_requirements
contraction_result
target_support
evidence_refs
assumption_refs
```

Full actionable outcomes select one feasible or conditional, non-dominated bundle.
Dominance references are acyclic and point only to feasible or conditional bundles.
`infeasible` means no bundle remains coded feasible or conditional, even when such a
bundle was marked dominated. The selected resource vector bounds its members' current
plus next commitment. The next-tranche candidate and every `floor` posture belong to the
selected member set; maintenance outside it remains allowed. Two bundle rows with the
same member set are duplicates even when their local IDs differ.

Workflow validates these coded consequences. Agentic SRA remains responsible for whether
the claimed target support, feasibility, dominance, and minimum sufficiency are true.

### Next Tranche, Ceiling, And Reserve

The next tranche records:

```text
target_id
resource_allocations
window
completion_signal
start_condition
reason
```

`allocate` carries a nonempty tranche and no unresolved start condition. `conditional`
carries a named start condition or explicitly records that no target is authorized yet.
`blocked`, `request_missing_context`, and `infeasible` carry no current allocation, next
tranche, new reserve, or investment ceiling.

Reserve is one separate posture:

```text
status
resource_allocations
reason
release_trigger
review_time
```

It is not duplicated as an ordinary candidate.

## Typed Dual-View Comparison

Challenge aliases are mapped back to original candidate IDs. Workflow compares:

- allocation outcome;
- candidate feasibility, role, and contraction result;
- Full bundle member sets, resource requirements, feasibility, dominance, and selected
  bundle;
- allocation-ledger posture and current resource allocation;
- next target, quantity, window, completion signal, and start condition;
- investment ceiling;
- authorization horizon;
- reserve resources and release boundary;
- missing information.

Explanation prose is not compared. Local bundle IDs are not compared; canonical bundle
identity comes from sorted bundle members.

One engineer-hour and six engineer-months to the same candidate are a conflict. A
mechanically different bundle or candidate-role assignment is also a conflict.

Agreement is corroboration of the same typed commitment. It is not proof of semantic
truth. Conflict selects no winner and opens one targeted reconciliation.

## Outcome And Finalization

| Outcome | Immediate authorization | Runtime finalization |
|---|---|---|
| `allocate` | yes | `finalized` |
| `conditional` | only after named condition | `conditional` |
| `infeasible` | none | `finalized` |
| `blocked` | none | `blocked` |
| `request_missing_context` | none | `blocked` |

The human-readable renderer follows this table. A blocked or infeasible result never says
that work may start immediately.

## Deterministic Integrity

`run.json` is a cache, not independent authority. `check_sra_run.py` reconstructs from:

- `raw-input.json`;
- deterministic packet construction;
- recorded Agentic judgments;
- legal typed transitions.

The checker verifies:

- the exact v0.3 run-state field set and canonical Workflow claim ceiling;
- selected mode, view plan, and coverage plan;
- context admission and all packets;
- Prompt text;
- output schema;
- Dispatch JSON;
- generated CLI command;
- candidate aliases;
- judgment validation and hashes;
- comparison and reconciliation packet;
- final source and final copy;
- trace event type, order, identity, payload, and parseable UTC timestamp;
- stage-bound, non-symlink carrier receipts with canonical metadata and observable
  context boundary;
- governance override visibility;
- the in-run `judgments/` output directory required by generated carriers.

Any malformed or extended state fails closed as a structured blocked report rather than
a traceback.

The runtime claims deterministic reconstruction and detectable contract drift. It does
not claim tamper-proof storage against an adversary who can rewrite every local artifact.

## Repair

`repair_sra_run.py` rebuilds derived artifacts from valid raw input plus valid recorded
Agentic judgments:

- admission and packets;
- Prompt, schema, Dispatch, and command surfaces;
- comparison and reconciliation;
- final copy;
- run cache;
- trace.

It never edits Agentic judgment files. Prepared packet hashes anchor the raw input;
recorded judgment-event hashes anchor Agentic judgments; trace carrier facts take
precedence over the mutable run cache. Repair refuses changed raw input, changed Agentic
judgments, invalid or illegally ordered judgments, another runtime version, invalid
stage receipt paths, or missing unrecoverable carrier facts.

## Carrier Boundary

Supported carriers:

- `packet_bound`;
- `fresh_subagent`;
- `ephemeral_cli`.

Fresh carriers without an observable receipt remain declared, not proven. A receipt
proves that a carrier artifact was persisted; it does not prove absence of hidden host
context or correctness of the judgment.

## Commands

```bash
python3 skills/sra/scripts/prepare_sra_run.py \
  --input skills/sra/templates/context-input.json \
  --dir /tmp/sra-run

python3 skills/sra/scripts/record_sra_judgment.py \
  --dir /tmp/sra-run \
  --stage challenge \
  --input skills/sra/templates/challenge-judgment.json

python3 skills/sra/scripts/check_sra_run.py --dir /tmp/sra-run
python3 skills/sra/scripts/repair_sra_run.py --dir /tmp/sra-run
python3 skills/sra/scripts/render_sra_decision.py --dir /tmp/sra-run
```

Packet hashes in judgment templates are placeholders and must be copied from the prepared
packet for that run.

## Claim Ceiling

An integrity-clean run supports this statement:

> The recorded SRA v0.3 artifacts conform to the declared context, resource, bundle,
> comparison, finalization, and observable carrier contract.

It does not prove:

- complete candidate or evidence coverage;
- correct challenge projection quality;
- absent hidden host context;
- true necessity or bundle sufficiency;
- correct priority;
- optimal ROI;
- real-world business value.
