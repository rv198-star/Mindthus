# TPlan Authority Contract Repair Audit

Date: 2026-09-05
Status: **PASS TO IMPLEMENT, WITH CONTRACT CORRECTIONS**
Base: `2501e8ac3f55b24478abefa68b864f8472744af0`
Scope: #196 / #197 / #198 / #199 only. #200 remains design-only.
Evidence case: `RU-20260905-SLIDETHUS-VQ-OVERRUN-01`.

## 1. Audit question

The four reproduced defects look different, but all occur at the same architectural seam:

> TPlan validates the shape of state, evidence and decisions, then commits them atomically; it does not yet have a complete deterministic layer proving that the references, declared authorization and resulting state are mutually consistent for this mutation.

The repair must close that seam without turning `validate_mission()` into an evidence database or semantic judge, and without adding a second authority system.

## 2. Current authority layers

The current runtime already has three useful layers. The fix should preserve them.

1. **Pure shape contracts**
   - `validate_mission()` validates Mission/task shape and declared acceptance coverage.
   - `validate_evidence_event()` validates evidence shape, acceptance IDs and task scope.
   - `validate_execution_trace_record()` validates trace shape and safe reference syntax.

2. **Intent/state transformation**
   - `set_task_status()` owns ordinary task status and active cursor consequences.
   - `apply_mutation()` converts a reviewed decision into an in-memory candidate state.
   - `validate_hook_output()` validates decision fields, path/risk assessment and continuation authorization enums.

3. **Atomic persistence**
   - `_commit_mission_state_unlocked()` owns the locked `before -> after` transaction, prepared evidence, lifecycle trace, journal and recovery boundary.

The gap is between (1)/(2) and (3): legal fields can still describe an impossible or unauthorized consequence.

## 3. Frozen repair invariants

### I1 — Referential Integrity / #196

For **new lifecycle records**, every value in `refs.evidence_ids` must resolve uniquely inside the same Mission evidence authority boundary.

Allowed sources:

- one existing evidence event in the locked Mission evidence stream; or
- one `prepared_evidence_event` created atomically in the same transaction.

Not equivalent:

- an existing filesystem path;
- an `artifact_ref`;
- an ID from another Mission;
- a missing ID;
- an ambiguous duplicate historical ID.

**Owner:** `_commit_mission_state_unlocked()` after prepared evidence validation/ID-collision checks and after the new trace records are built, but before the transaction journal is written.

This is contextual validation and must not be moved into `validate_execution_trace_record()`, which should remain usable as a pure shape validator.

Historical trace records are not rewritten. New writes that do not reference a historical bad ID remain possible. An already-prepared legacy pending transaction is recovered according to its frozen transaction contents rather than being reinterpreted using later evidence.

### I2 — Active Path Atomicity / #197

A caller that explicitly requests **create-and-activate** must get one atomic consequence:

- the new node exists;
- its status is `active`;
- `active_task_id` selects that node;
- the same commit produces the node-addition and active-cursor lifecycle consequences.

Default node creation remains `pending` and does not steal the cursor.

**Owner:** the existing canonical activation primitive, `set_task_status(..., "active")`, reused by `add_task_node()` on the same in-memory candidate before one commit.

Do **not** add a global rule saying only one node may have `status=active`: active ancestors may coexist with the current execution leaf. Do not infer the cursor from timestamps. `requires_human` keeps its documented blocked recovery cursor behavior.

`validate_mission()` therefore should not become a universal active-node cardinality checker for this fix.

### I3 — Mission Completion Integrity / #198

A **new transition into `mission.status=completed`** is permitted only if both mechanical prerequisites hold in the same locked snapshot:

1. every node whose `role == "success-critical"` is `completed`; and
2. every Mission acceptance ID has a current mechanically qualified positive acceptance observation.

For the first repair, no new acceptance database/schema is required.

Use the existing evidence model:

- `acceptance_passed` is a positive qualified observation;
- a structurally complete legacy `acceptance` remains a compatibility-positive observation;
- `acceptance_failed` is negative;
- for each acceptance ID, **event-stream order** determines the latest qualified observation;
- a later failure blocks closure until a later qualified positive observation exists.

The evidence event has already been checked against declared acceptance IDs and task/success-critical-ancestor scope by `validate_evidence_event()`.

**Owner:** a completion-precondition check under `_commit_mission_state_unlocked()` when the candidate state newly enters `completed`. It must inspect the locked existing evidence plus same-transaction prepared evidence before the journal is written.

This is a mechanical closure gate only. It does not judge whether a PPT is visually good, whether a reviewer was wise, or whether a synthetic test is semantically equivalent to a PowerPoint holdout. Those claims remain Agent/reviewer responsibility when writing the acceptance event.

Supporting/exploratory work is not promoted into a full Mission approval ceremony. Ordinary Task `completed` remains distinct from Mission acceptance; #196 already prevents fake evidence references from giving a task transition false referential authority.

**Correction to the earlier repair plan:** do not build a new artifact-version/acceptance-mapping schema in the first #198 fix. Existing IDs and qualified pass/fail events are sufficient to close the reproduced deterministic contradiction. Add richer freshness/version binding only if later real evidence proves that gap remains material.

### I4 — Decision Consequence Integrity / #199

`continuation_authorization.authorized_action` is an execution ceiling, not descriptive metadata.

At minimum:

- `stop`, `mission_review`, and `anti_spiral_audit` must not be paired with an execution-widening mutation such as activating/resuming work;
- `continue_same_path`, `targeted_fix`, and `batch_details` may permit execution subject to the ordinary mutation/state contracts;
- qualitative fields such as weak ROI, failed lint or unclear evidence are not themselves a deterministic stop oracle.

**Owner:** one pure decision-consequence validator called by `validate_hook_output()`, therefore shared automatically by ordinary `apply_decision()` and interaction-guard authorized application before any receipt-bound mutation is applied.

Do not create a second consequence check only inside `apply_decision()`: the guard path also calls `validate_hook_output()` and must receive the same rule.

The first implementation should encode only deterministic contradictions. It should not attempt to compute whether continuation is strategically worthwhile.

## 4. Where each check belongs

| Concern | Pure shape validator | Intent transformer | Locked commit boundary |
|---|---|---|---|
| Evidence ID syntax | yes | no | — |
| Evidence ID existence/uniqueness for new refs | no | no | **yes** |
| Create-and-activate cursor consequence | no global count rule | **yes** | atomic persistence |
| Continuation action vs mutation contradiction | **decision consequence validator** | apply only after pass | final persistence |
| Mission completion prerequisites | not in pure `validate_mission()` | candidate state may be built | **yes, before journal** |
| Semantic quality/ROI judgment | **Agent/reviewer** | — | — |

This separation is the main audit result. It prevents four local patches from becoming four competing sources of truth.

## 5. Implementation order

### Step 1 — #196

Fix the common locked reference boundary first because #198 also relies on trustworthy evidence identity.

Required regression set:

- missing ID rejected;
- file path in `evidence_ids` rejected;
- cross-Mission ID rejected;
- duplicate/ambiguous historical ID cannot support a new reference;
- existing unique ID accepted;
- same-transaction prepared event ID accepted;
- `artifact_refs` unchanged;
- failure/concurrency leaves no state/trace/evidence/journal ghost.

### Step 2 — #197

Reuse canonical activation during dynamic creation. Preserve pending creation and existing init/recovery behavior.

Required regression set:

- create active -> node + cursor + matching lifecycle commit;
- create pending -> cursor unchanged;
- ordinary activation still works;
- active ancestor / selected leaf compatibility retained;
- failure injection produces no orphan node/cursor half-state.

### Step 3 — #199

Add the single deterministic continuation consequence validator and route both ordinary and guard-authorized decisions through it.

Required regression set:

- `stop + set_active_task` rejected before writes;
- review/audit-required + execution-widening mutation rejected;
- valid bounded continue remains valid;
- valid stop/review outcome remains recordable without silently executing;
- guard receipt does not override a contradictory decision contract.

### Step 4 — #198

After reference identity is trustworthy, add the completion gate at the atomic commit boundary.

Required regression set:

- any success-critical node pending/active/blocked blocks Mission completion;
- missing acceptance observation blocks;
- pass permits when all other requirements hold;
- pass then later fail blocks;
- fail then later pass permits;
- valid complete legacy `acceptance` remains compatible;
- supporting/exploratory unfinished work does not automatically block if it is not success-critical;
- advisory mode continues to record recommendation rather than mutate;
- failure/concurrency produces no partial closure.

## 6. Explicit non-goals for this repair wave

- No SRA method change.
- No #200 cross-root budget implementation.
- No new scheduler, daemon or host hook.
- No universal time/operation threshold such as 16 hours or 35 calls.
- No automatic semantic grading of deliverables.
- No retroactive rewrite of historical Missions/evidence/trace.
- No new general-purpose authority ledger.
- No new completion schema unless the existing acceptance model proves insufficient after these deterministic repairs.

## 7. Verification performed for this audit

On `2501e8ac3f55b24478abefa68b864f8472744af0`:

- the admitted Slidethus reproducer still reproduces all four current-runtime contradictions;
- the packet remains 10/10 hash matched and review-bounded;
- focused existing TPlan tests covering evidence/transition, node addition, decisions, interaction guard, persistence and outcome attribution: **60 passed**;
- `git diff --check`: PASS before the audit document change.

These tests prove current deterministic behavior and compatibility surfaces; they do not prove the future fix until the failing reproductions are converted into permanent expected-rejection regressions.

## 8. Verdict

**PASS TO IMPLEMENT.** No further architecture round is required before starting #196.

The repair wave is authorized to use the frozen invariants above. The sequence is:

> **#196 -> #197 -> #199 -> #198**, then one unified regression/compatibility audit.

#200 remains separate design work. If implementation discovers that one of these invariants cannot be enforced at the named canonical boundary without a new state model or duplicated authority, stop that issue and return to this audit rather than adding a local workaround.
