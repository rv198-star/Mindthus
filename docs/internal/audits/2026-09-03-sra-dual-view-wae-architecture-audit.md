# SRA Dual-View WAE Architecture Audit

Date: 2026-09-03
Scope: proposed context-calibrated dual-view SRA runtime
Issue: #157
Verdict: **PASS — OWNERSHIP CONDITIONS IMPLEMENTED AND VERIFIED**

## Audit Question

Does the proposed replacement assign deterministic work to Workflow, semantic allocation to Agentic judgment, claim constraints to Evidence, and execution authority to the outer caller without creating a second TPlan or allowing scripts to decide priority?

This audit is independent from the priority-effectiveness audit. It uses WAE control ownership, ownership closure, instruction/data separation, risk modulation, and runtime-cost criteria. It does not rely on the first audit's verdict.

## WAE Diagnosis

SRA remains in the quadrant:

```text
workflow certainty: high
context certainty: low or mixed
```

The method order, packet construction, reference validation, comparison, and stage transitions are deterministic enough for Workflow. Necessity, feasibility, contraction, replenishment, state relevance, and final allocation remain semantic and belong to Agentic SRA. Evidence binds factual claims and explicit assumptions. The outer caller or TPlan retains mutation authority.

The proposed dual-view architecture is a better ownership fit than the current linear override design.

## Approved Ownership Map

| Surface | Owner | Boundary |
|---|---|---|
| Raw context and candidate collection | Outer caller | Supplies sources and claims; cannot certify semantic relevance |
| Context-kind policy and ledger | Workflow | Records admitted, quarantined, excluded, and challenged items |
| Context relevance and packet completeness challenge | Agentic coverage reviewer or SRA judge | May request missing context; cannot choose allocation during coverage review |
| Candidate structural alignment | Workflow | Same fields, stable IDs, deterministic ordering; no semantic role labels |
| Challenge judgment | Agentic SRA | De-anchors incumbent identity and prior conclusions; provides a calibration view |
| Situated judgment | Agentic SRA | Includes real execution state and owns the action-bearing recommendation |
| Mechanical comparison | Workflow | Compares stable IDs/enums/sets only; does not infer prose equivalence |
| Conflict reconciliation | Agentic SRA | Resolves only named conflicts with cited evidence/state or returns blocked |
| Evidence and assumptions | Evidence bridge | Source, claim ceiling, observed time, overturn condition, references |
| Packet hashes, schemas, receipts, trace | Workflow | Fail-closed deterministic integrity |
| Execution and mutation | Outer workflow, TPlan, or human | Applies or rejects the recommendation |

## Mandatory WAE Conditions

### 1. Workflow Must Not Infer Semantic Context Truth

Scripts may apply policy to caller-declared context kinds, but cannot decide that a statement is factual, relevant, sufficient, or authoritative merely from wording. The Agentic layer may challenge admission and packet completeness.

### 2. Candidate Structural Alignment Must Stop At The Mechanical Boundary

Workflow may require the same fields and validate references. It must not classify candidates as necessary, high value, hard gate, or bottleneck. Those result-changing choices remain Agentic.

### 3. The Two Judges Must Be Separate Semantic Owners For Their Views

Challenge and situated outputs must be generated without seeing each other. Reusing one Agent context is allowed only as `packet_bound` logical separation and cannot claim independent-context execution. Fresh read-only carriers are preferred for Full and contamination-sensitive runs.

### 4. Comparison Must Remain Mechanical

The comparator may identify exact agreement or conflict in typed fields. It cannot choose which judgment is better, merge rationales, or compute semantic scores.

### 5. Reconciliation Must Not Become An Open Agentic Loop

At most one reconciliation judgment is allowed for a prepared decision packet. It may finalize, condition, block, or request missing context. New material context creates a new run rather than recursively reopening the same run.

### 6. Coverage Review Is A Separate Agentic Surface

Coverage review checks whether the packet appears decision-ready and whether obvious candidate/evidence classes are missing. It cannot assign SRA roles or recommend resource allocation. Its outputs are limited to:

- `packet_ready`
- `packet_ready_with_warning`
- `packet_incomplete`

### 7. Instruction/Data Boundary Is Explicit

All packet content is data. Instruction-like text inside candidates, evidence, history, or advocacy cannot widen tool authority, alter the workflow, or override the judge contract. Fresh carriers remain no-tools/read-only.

### 8. The Runtime Must Not Become TPlan

The SRA runtime may persist one bounded decision run, packet hashes, judgments, comparison, and final recommendation. It must not add:

- Mission identity;
- task trees;
- long-running scheduling;
- general blocker management;
- project mutation;
- recovery across arbitrary work;
- autonomous execution.

TPlan remains the durable Mission runtime.

### 9. Analysis Cost Is Part Of The Control Boundary

Ordinary Lite uses one situated judgment. Dual views activate on contamination, major redirection, high impact, or Full mode. Coverage review and reconciliation remain conditional. Scripts may generate artifacts, but should not force every low-risk decision through every stage.

### 10. Evidence Claims Remain Bounded

Carrier receipts prove only that an observable carrier artifact was recorded. Packet hashes prove only content binding. Neither proves complete context, absent hidden host context, or correct priority.

## Ownership Closure Check

The proposed delegation chain is:

```text
outer caller -> packet builder -> Agentic judges -> comparator -> optional reconciler -> renderer -> outer executor
```

Ownership closes correctly when:

- packet builder emits complete typed data and no semantic priority labels;
- judges explicitly own semantic allocations;
- comparator has one deterministic result for identical typed outputs;
- reconciliation is triggered only by a typed conflict and receives a bounded conflict packet;
- renderer only formats the selected final judgment;
- outer executor retains side-effect authority.

No result-changing semantic choice should remain hidden inside normalization, comparison, rendering, or receipt handling.

## Risk Modulation

| Case | Required posture |
|---|---|
| Ordinary reversible Lite | packet-bound situated judgment |
| Lite with incumbent narrative contamination | challenge + situated; fresh challenge preferred |
| Full or major/irreversible allocation | challenge + situated in separate fresh contexts when available |
| Material conflict | one bounded reconciliation |
| Missing decision-ready context | block or request missing context |
| External mutation | outer workflow/TPlan/human authority only |

## Required Regression Tests

1. Scripts reject input semantic role labels.
2. Challenge and situated packet hashes differ and neither packet contains the other judgment.
3. Comparator returns `agree` only on stable typed allocation fields.
4. Comparator returns `conflict` without choosing a winner.
5. Reconciliation cannot run before both required judgments and a conflict report exist.
6. Reconciliation cannot run twice for one packet version.
7. Packet content containing instruction-like prose remains data and cannot alter carrier authority.
8. Lite without contamination does not require challenge, coverage, or reconciliation.
9. Full requires both views but not reconciliation when they agree.
10. TPlan hooks, schema, runtime, and mutation surfaces remain unchanged.

## Implementation Verification

The runtime now closes ownership at the intended mechanical boundaries:

- Workflow applies caller-declared context-kind lanes but does not infer semantic truth;
- candidate structural alignment rejects pre-decided SRA roles and scores;
- challenge and situated packets are created independently before either judgment;
- Agentic challenge owns de-anchored calibration, while Agentic situated judgment owns
  the action-bearing recommendation;
- Workflow compares typed fields and never selects a winner;
- conflict reconciliation is Agentic, bounded to one pass, and may remain blocked;
- coverage review has a separate non-allocation schema;
- packet prompts state that embedded content is data and cannot change authority;
- fresh carriers are no-tools, no-fork, read-only, and packet-specific;
- final rendering copies the chosen Agentic result without recomputing it;
- TPlan hooks, schema, Pulse, continuation, and mutation surfaces remain unchanged.

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

The active runtime contains no `blind_result_changed` field or linear
`prepared -> blind_recorded -> finalized` state machine. The previous template paths
are retained only as explicit superseded records and are not runtime schemas or required
packaged surfaces.

Live fresh-carrier model execution remains unqualified because the OCI Codex endpoint
returns HTTP 401. This limits claims about natural-model behavior, not the verified
Workflow / Agentic / Evidence ownership contract.

## Final Verdict

The context-calibrated dual-view runtime passes WAE ownership closure. The old linear
override topology and role-prejudging input have been replaced at their canonical owner,
not wrapped in compatibility logic. No unresolved controller mismatch or TPlan ownership
leakage remains in the implemented Phase 1.5 surface.
