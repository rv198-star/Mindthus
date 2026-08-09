# WAE Ownership Closure

Layer: `mainline extension` with guardrails and boundaries
Issue: #149

## Core / 核心

WAE normally answers:

> Who or what should control this part of the work?

Ownership Closure adds a conditional second question:

> Does the chosen semantic owner still own every result-changing semantic choice after delegation?

The target invariant is:

> Ownership must extend to the last non-mechanical decision point.

The governing rule is:

> Ownership follows semantic choice; Workflow follows deterministic consequence.

`Ownership Closure` is the target state. `Ownership Boundary Refinement` is the
mechanism used when the current boundary is not closed. `Recursive Ownership
Refinement` may describe that mechanism, but it is not a separate Mindthus method.

## Mainline / 主路径

Do not run this mode after every WAE decision. Enter it only when the initial control
assignment may hide another semantic boundary.

### Trigger signals

Use Ownership Closure when one or more of these are true:

- a declared semantic owner delegates to a repository, adapter, helper, generator,
  template, mapper, policy shell, or other generic downstream component;
- the downstream component still has multiple reasonable result-changing behaviors;
- the downstream component must interpret prose, names, field shapes, heuristics, or
  hidden context to choose behavior;
- runtime evidence shows that an apparently complete owner cannot determine end-to-end
  behavior without a downstream semantic decision;
- a supposedly mechanical layer must invent behavior for unknown or underspecified
  input.

A useful smell is:

```text
semantic owner
    -> generic helper(...)
```

The smell is not itself proof of leakage. Inspect whether the helper still owns a
semantic choice.

### Closure flow

1. **Name the current semantic owner.** State the result-changing choices that owner is
   supposed to control.
2. **Inspect the delegation boundary.** Look only at delegations that may carry those
   choices downstream; do not recursively inspect implementation depth for its own sake.
3. **Test the semantic remainder.** Ask whether the delegate still needs domain meaning,
   trade-off judgment, contextual interpretation, or a choice among multiple reasonable
   outcomes that changes state, permission, side effects, failure semantics, or the
   final result.
4. **Refine when needed.** If such a choice remains, the boundary is not closed. Diagnose
   `Semantic Ownership Leakage`, move the choice to an explicit semantic owner or make
   it explicit in a structured contract, then re-evaluate the next delegation boundary.
5. **Stop at the Mechanical Boundary.** Once the remaining behavior is uniquely
   derivable from complete structured input and unknown input fails closed, stop
   refinement and keep the remainder mechanical/Workflow-controlled.

This is boundary convergence, not task decomposition. The analysis may revisit WAE as
new evidence appears, but it does not create a generic execution loop.

## Semantic Ownership Leakage

`Semantic Ownership Leakage` means:

> A nominal semantic owner delegates work while a downstream component still has to
> make a result-changing semantic choice that the declared ownership contract did not
> resolve.

Typical examples include a persistence adapter still choosing insert/update/append or
conflict policy; an API mapper choosing fallback semantics; a UI generator choosing
information priority or recovery behavior; or an integration helper choosing retry,
fallback, degradation, or partial-success policy.

The technology layer is not what makes these Agentic. The remaining semantic choice is.

Do not diagnose leakage merely because implementation is complex. A complicated SQL
builder, transaction engine, renderer, or protocol stack can remain mechanical when its
input already determines behavior uniquely.

## Mechanical Boundary / 停止条件

Ownership Boundary Refinement must stop when the remaining work satisfies all of these:

1. **Complete structured input** — every result-changing admitted choice needed by the
   downstream executor is represented explicitly.
2. **Unique admitted behavior** — for admitted inputs, the intended output or action is
   mechanically determined rather than selected from several reasonable meanings.
3. **No domain judgment remains** — the executor does not need business interpretation,
   contextual trade-offs, or natural-language inference.
4. **Mechanical validation is sufficient** — shape, legality, references, deterministic
   transforms, execution, and observable results can be checked without deciding domain
   truth.
5. **Unknown input fails closed** — unsupported or underspecified input is rejected or
   surfaced; it is not converted into a semantic guess.

This is a WAE-local stopping test. It does not authorize a new schema, validator,
runtime gate, or persistent state machine.

Ownership follows semantic choice, **not implementation depth**.

## Evidence Feedback

Evidence has two roles in Closure work:

- prove or constrain claims about the realized behavior;
- reveal that the previous ownership granularity was wrong.

A green unit test, typecheck, or mocked integration can support an implementation claim
without proving Ownership Closure. If real runtime evidence later reveals that a
downstream component cannot choose behavior without inventing semantics, WAE may reopen
the closure judgment and refine the boundary.

Reopening requires evidence of a **semantic remainder**, not merely an execution defect.
A syntax error, malformed placeholder, timeout, or other repairable mechanical failure
does not change ownership when the intended behavior was already fully specified.

## Guardrails / 防止误用

### Not a generic loop

Do not call every `act -> test -> fix -> retest` sequence Ownership Boundary
Refinement. Retry changes execution; Closure changes the semantic ownership boundary.

A useful discrimination question is:

> Did the evidence reveal a missing result-changing choice, or only a defective
> implementation of an already-complete choice?

Only the first can reopen Ownership Closure.

### Not unlimited Agentic expansion

Do not move deterministic work into Agentic control because it is difficult, deeply
nested, domain-specific in syntax, or implemented in many layers. Stop as soon as the
Mechanical Boundary test passes.

### Evidence is feedback, not WAE state

Ownership Closure does not require a WAE ledger, checkpoint history, task tree, or
persistent refinement state. Evidence may be supplied by the surrounding work and may
change the WAE judgment without becoming a new WAE runtime.

## Boundary with TPlan

WAE Ownership Closure and TPlan can recur together, but they own different things.

- **WAE** decides who owns a result-changing semantic choice and whether that ownership
  boundary is closed.
- **TPlan** owns long-running Mission/task state, ordering, checkpoints, blockers,
  recovery, decision hooks, resumption, and lifecycle control.

Inside a TPlan Mission, runtime evidence may cause a task to invoke WAE Closure again.
TPlan records and schedules the consequence; WAE performs the semantic boundary
judgment. WAE must not create duplicate Mission state or recovery machinery.

Short distinction:

```text
TPlan: what happens next, and what state continues?
WAE:   who owns this semantic decision, and is that boundary closed?
```

## Worked contrast

### Closure refinement

```text
Agentic service owns persistence
    -> Repository.save(record)
    -> adapter must still choose append vs update and conflict behavior
```

The adapter still owns unresolved semantic choices. Refine the contract until those
choices are explicit, for example:

```yaml
kind: append
conflict: reject
return_fields:
  - id
  - created_at
```

If the remaining executor can now validate and execute that command deterministically,
the Mechanical Boundary has been reached.

### Ordinary repair, not closure refinement

The same complete command reaches an SQL builder that emits a malformed parameter
placeholder. The implementation is wrong, but the semantic contract is complete.
Repair and retest without moving the ownership boundary.

## Boundary / 不做什么

Ownership Closure does not:

- create a new top-level Mindthus methodology;
- replace WAE's Minimal Check or make deep analysis the default;
- decompose Mission/Task/SubTask/Step structures;
- own retry scheduling, task recovery, or checkpoints;
- require persistent WAE state;
- authorize new governance gates or schemas;
- treat helper names, architecture layers, or code depth as proof of ownership.

Use the frozen acceptance casebook at
`tests/wae/ownership_closure_acceptance_cases.md` as the implementation and regression
reference for this mode.
