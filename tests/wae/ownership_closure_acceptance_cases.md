# WAE Ownership Closure Acceptance Cases

Issue: #149
Status: frozen acceptance design before implementation
Date: 2026-08-09

## Purpose

These cases define the behavioral boundary for adding `Ownership Closure` to WAE.
They are intentionally frozen before substantive WAE implementation changes so the
method is evaluated against predeclared failure classes rather than post-hoc examples.

The target upgrade is narrow:

> WAE should not stop at a nominal control assignment when delegated work still
> contains a result-changing semantic choice.

The target invariant is:

> Ownership must extend to the last non-mechanical decision point.

The stopping principle is:

> Ownership follows semantic choice; Workflow follows deterministic consequence.

These cases do **not** authorize a new top-level methodology, a WAE runtime state
machine, a TPlan-lite task loop, a new persistent schema, or a new governance gate.

## Evaluation dimensions

A conforming WAE implementation should demonstrate all of the following:

1. `first_order_fidelity` — ordinary WAE cases remain ordinary WAE cases.
2. `leakage_detection` — hidden semantic choice behind delegation is recognized.
3. `boundary_refinement` — ownership or the contract is refined until the semantic
   choice has an explicit owner.
4. `mechanical_stop` — refinement stops once the remainder is uniquely mechanical.
5. `evidence_reopen` — runtime evidence may invalidate a previously assumed closure.
6. `loop_discrimination` — retry/repair is not confused with ownership refinement.
7. `tplan_separation` — Mission/task runtime remains TPlan responsibility.
8. `cross_domain_generalization` — the rule is not persistence-specific.
9. `fail_closed_unknowns` — a mechanical executor does not invent missing semantics.

## Case OC-01 — First-order WAE is sufficient

**Role:** negative control / no escalation

### Situation

An agentic reviewer decides whether a generated release note contains an unsupported
claim. It reads the source diff and release evidence, decides the claim is unsupported,
and emits a structured decision:

```yaml
claim_id: release-runtime-generation
status: reject
reason_code: unsupported_by_release_evidence
```

A deterministic renderer converts that decision into the standard release-review
format. The renderer has no authority to change `status`, reinterpret `reason_code`,
or invent an alternative conclusion.

### Expected WAE behavior

- Assign semantic review to `Agentic` and rendering to `Workflow`.
- Do not enter Ownership Closure refinement merely because there is a downstream
  renderer/helper.
- Treat the structured decision as a sufficient semantic handoff because downstream
  output is uniquely derivable from it.

### Must not happen

- Do not recursively inspect every formatter/template implementation layer.
- Do not convert deterministic rendering into additional Agentic work.
- Do not create Mission/task state to prove closure.

### Pass condition

WAE can state why the boundary is already closed and stop at the mechanical handoff.

---

## Case OC-02 — Hidden semantic choice behind a generic storage helper

**Role:** primary positive case / Semantic Ownership Leakage

### Situation

An Agentic service is declared to own persistence semantics for a learning record. It
constructs a domain object and calls:

```text
Repository.save(record)
    -> S3StorageAdapter.persist(record)
```

The storage adapter has no complete persistence command. To implement `persist`, it
must still decide among reasonable alternatives:

- `insert`, `update`, or `append`;
- reject, overwrite, merge, or ignore on conflict;
- which mutable fields are written;
- which fields are returned;
- whether a duplicate is an error, no-op, or idempotent success.

### Expected WAE behavior

- Detect that the nominal Agentic owner did not close the semantic boundary.
- Diagnose the failure as `Semantic Ownership Leakage`.
- Refine ownership or the contract until the result-changing choices above are made by
  an explicit semantic owner.
- A valid refinement may produce a complete structured command such as:

```yaml
kind: append
table: learning_record
values: ...
conflict: reject
return_fields:
  - id
  - created_at
```

### Must not happen

- Do not call the adapter deterministic merely because it has an implementation-shaped
  name such as `adapter`, `repository`, or `helper`.
- Do not let the adapter infer conflict policy from field names, prose, conventions, or
  heuristics while still classifying the boundary as closed.
- Do not fix the case by adding a retry loop around `persist`.

### Pass condition

Every result-changing persistence choice has a visible semantic owner before the
mechanical persistence layer begins.

---

## Case OC-03 — Mechanical Boundary stops refinement

**Role:** anti-over-Agentic guard / stopping case

### Situation

The semantic owner produces this complete command:

```yaml
kind: append
table: learning_record
values:
  learner_id: "L-42"
  concept_id: "C-7"
  score: 0.81
conflict: reject
return_fields:
  - id
  - created_at
```

The remaining path is:

```text
schema validation
-> parameterized SQL generation
-> transaction execution
-> row mapping
-> exit-code/runtime evidence
```

For the admitted command vocabulary, each step is deterministic and unknown command
kinds fail closed.

### Expected WAE behavior

- Recognize a `Mechanical Boundary`.
- Stop Ownership Boundary Refinement.
- Keep schema validation, SQL generation, execution, row mapping, and mechanical
  evidence in Workflow/mechanical control.

### Must not happen

- Do not require Agentic reasoning merely because SQL or transactions are complex.
- Do not recurse down implementation depth after semantic choice has reached zero.
- Do not ask an agent to second-guess an already complete `conflict: reject` decision.

### Pass condition

WAE explicitly stops because the semantic remainder is zero, not because the code stack
has ended.

---

## Case OC-04 — Evidence reopens a nominally closed boundary

**Role:** evidence-feedback case

### Situation

A repository implementation passes:

- TypeScript typecheck;
- build;
- unit tests;
- mocked repository tests.

A real PostgreSQL/HTTP runtime test then fails because the final adapter cannot determine
whether a duplicate learning record should be appended, updated, or rejected. The mock
had hidden this choice.

### Expected WAE behavior

- Treat the runtime result as evidence that the earlier ownership granularity was wrong.
- Reopen the closure judgment even though previous evidence was green.
- Inspect the delegation path and refine the semantic contract/owner.
- Preserve the distinction between "tests passed" and "ownership was actually closed".

### Must not happen

- Do not dismiss the runtime evidence because prior tests were green.
- Do not classify this only as an implementation bug when the failure reveals a real
  multiple-reasonable-path semantic choice.
- Do not make Evidence a persistent WAE runtime ledger merely to support reopening.

### Pass condition

Evidence can invalidate a prior closure assumption and cause a boundary correction.

---

## Case OC-05 — Execution retry is not Ownership Refinement

**Role:** negative control / loop discrimination

### Situation

A complete persistence command correctly states:

```yaml
kind: append
conflict: reject
```

The SQL builder accidentally emits a malformed parameter placeholder. Integration tests
fail with a syntax error. No semantic choice is missing: the correct behavior is fully
specified, and the defect can be repaired mechanically.

### Expected WAE behavior

- Keep the existing ownership boundary.
- Treat correction/retry as execution repair, not Ownership Boundary Refinement.
- Enter closure analysis only if new evidence reveals a missing result-changing choice.

### Must not happen

- Do not move SQL syntax repair into Agentic ownership solely because a test failed.
- Do not describe every `fix -> test -> fix` cycle as recursive ownership refinement.
- Do not use WAE Closure as a generic reflection loop.

### Pass condition

The implementation can explain: owner unchanged, semantic contract unchanged, only
mechanical execution was defective.

---

## Case OC-06 — TPlan hosts recurrence but does not own closure semantics

**Role:** WAE/TPlan boundary case

### Situation

A long-running migration Mission is managed by TPlan. It has task state, acceptance
evidence, blockers, checkpoints, and recovery. During one migration Task, runtime
evidence shows that a generated migration helper still decides whether a foreign-key
relationship should `CASCADE`, `RESTRICT`, or `SET NULL`.

### Expected WAE behavior

- WAE determines that this is unresolved semantic ownership and refines the boundary.
- TPlan continues to own Mission/task state, blocker recording, ordering, checkpoint,
  recovery, and resumption.
- TPlan may record WAE's result and schedule the resulting implementation work, but does
  not decide the semantic ownership rule itself.

### Must not happen

- Do not create a WAE Mission, task tree, checkpoint, or recovery state.
- Do not move TPlan's runtime lifecycle into WAE.
- Do not reduce the semantic decision to a TPlan bookkeeping field whose presence is
  mistaken for correctness.

### Pass condition

The two methods can be composed without duplicated runtime control planes:

```text
TPlan: when/what state continues
WAE:   who owns the semantic decision
```

---

## Case OC-07 — Cross-domain semantic leakage

**Role:** generalization case

### Situation A: API mapping

A mapper receives `UserProfile` and must produce an external provider payload. Exact
field projection is known, but the downstream mapper still has to decide whether a
missing legal name should fall back to display name, be omitted, or block the request.

### Situation B: UI generation

A template generator can mechanically render sections, but the generator still decides
which warning is prominent, which information is hidden by default, and what error
recovery action is offered.

### Situation C: integration fallback

A provider client can mechanically issue HTTP requests, but a generic integration
helper still chooses retry count, fallback provider, degradation behavior, and whether
partial data is acceptable.

### Expected WAE behavior

For each situation:

- Continue refinement while the downstream layer still chooses among multiple
  reasonable outcomes that change user-visible/system behavior.
- Stop once those choices are represented in a complete structured contract and the
  remaining mapping/rendering/call plumbing is deterministic.

### Must not happen

- Do not define Ownership Closure as a persistence-only rule.
- Do not classify layout, mapping, or provider plumbing as semantic merely because the
  domain is unfamiliar.
- Do not classify a helper as mechanical while it interprets prose or heuristics to
  choose a result-changing policy.

### Pass condition

The same criterion — remaining semantic choice, not technology type — determines
whether refinement continues.

---

## Case OC-08 — Unknown mechanical input fails closed

**Role:** Mechanical Generation Eligibility / fail-closed case

### Situation

A deterministic persistence executor supports:

```text
append | replace | delete
```

It receives:

```yaml
kind: reconcile
```

No semantics for `reconcile` exist in the structured contract.

### Expected WAE behavior

- The executor fails closed and reports unsupported/underspecified input.
- WAE treats the unknown as unresolved semantic ownership if `reconcile` is actually
  required by the product intent.
- A semantic owner must define what `reconcile` means before the executor can become
  mechanical again.

### Must not happen

- Do not guess that `reconcile` means `replace` or `merge`.
- Do not derive semantics from the command name, nearby fields, historical frequency,
  or provider conventions.
- Do not claim Mechanical Boundary eligibility when unknown inputs are handled by
  heuristic interpretation.

### Pass condition

Unknown semantic input cannot silently cross a boundary declared mechanical.

---

## Cross-case acceptance matrix

| Case | Must refine | Must stop | Evidence may reopen | Must remain TPlan-free | Primary failure protected |
|---|---:|---:|---:|---:|---|
| OC-01 | no | yes | n/a | yes | false-positive escalation |
| OC-02 | yes | after contract closure | yes | yes | Semantic Ownership Leakage |
| OC-03 | no | yes | n/a | yes | over-Agenticization |
| OC-04 | yes | after correction | yes | yes | green-test closure illusion |
| OC-05 | no | yes | only with new semantics | yes | generic-loop confusion |
| OC-06 | yes | after closure | yes | no: composed with TPlan | control-plane duplication |
| OC-07 | conditional | yes at mechanical boundary | yes | yes | persistence overfitting |
| OC-08 | yes if intent requires unknown kind | yes after definition | yes | yes | heuristic semantic invention |

## Mechanical Boundary test

Ownership refinement may stop only when the remaining work satisfies all of these:

- input is complete and structured;
- output/behavior is uniquely determined for admitted inputs;
- no domain or business judgment remains;
- validation/execution can be mechanical and domain-independent at that layer;
- unknown or underspecified inputs fail closed rather than inventing semantics.

This is a stopping test, not a requirement to introduce a new runtime validator or
schema in this issue.

## Expected public terminology

The acceptance suite assumes these conceptual roles, while final wording may be refined
without changing behavior:

- `Ownership Closure` — the WAE target state / conditional mode;
- `Ownership Boundary Refinement` — the mechanism for moving the boundary;
- `Semantic Ownership Leakage` — semantic choice escapes through nominal delegation;
- `Mechanical Boundary` — the point where deterministic consequence begins.

`Recursive Ownership Refinement` may remain the design-observation name, but a passing
implementation must not imply generic execution-loop semantics.

## Freeze rule

Substantive WAE implementation changes should be reviewed against these cases. If a
case itself needs to change because the design proves incoherent, change the case
explicitly and explain why; do not silently weaken an expectation to make an
implementation pass.
