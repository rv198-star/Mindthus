# Issue Draft: Make tplan Runtime Adaptive By Risk

## Title

Make tplan lighter by adapting runtime ceremony to risk

## Context

Current `tplan` preserves important Mission control capabilities, but its runtime loop can
feel too heavy in ordinary use. Step logs, decision packets, reviews, audits, and script
calls may appear to be always-on ceremony, even when the work is low-risk, reversible,
short, or already well understood.

This creates a cost problem: the user and agent pay the overhead of strict governance
before the situation has shown that strict governance is needed.

The optimization direction is not to reduce `tplan`'s capability boundary. The goal is to
make `tplan` behave like a thin Mission state machine during ordinary work, then expand
into a full control plane when risk, complexity, irreversibility, recovery needs, or
judgment pressure requires it.

## Core Principle

Runtime level may reduce recording density, but it must not weaken key risk triggers.

In other words:

```text
tplan 的能力边界不缩水；
tplan 的执行仪式按风险、复杂度、可逆性、恢复需求分层。
```

Lite mode may write less, create fewer nodes, and skip routine packets. It must not drop
Mission anchoring, evidence/log separation, decision hooks for high-impact changes, or
graceful stop behavior.

## Target

Introduce an Adaptive tplan policy with three runtime levels:

- `lite`: low-risk, short-path, reversible work.
- `normal`: default Mission work with real subtasks and selective evidence.
- `strict`: high-risk, long-running, multi-branch, audit-heavy, or human-authority-sensitive work.

The levels should affect:

- log density
- evidence density
- Step materialization frequency
- decision packet frequency
- review/audit frequency
- script-call bundling

The levels must not affect:

- Mission objective and acceptance criteria preservation
- active node recoverability
- task-tree legality when nodes are materialized
- evidence/log separation
- alignment gates for important changes
- decision hooks for high-impact decisions
- graceful stop when safe continuation is not authorized

## Proposed Direction

### 1. Runtime Levels

`lite` keeps only the minimum state required for recovery:

```text
mission objective
acceptance criteria
active node
latest state
blocker / evidence / decision summary
```

`normal` maintains a task tree and records evidence selectively.

`strict` runs the full control-plane path: formal review, decision packet, stronger
evidence links, audit, and human authority gates where appropriate.

### 2. Delayed Step Materialization

Ordinary execution actions should begin as task-local notes or lightweight logs.

Promote an action into a Step only when it needs:

- recovery
- acceptance
- rollback
- evidence reference
- decomposition into multiple actions

### 3. Sparse Evidence

Keep `evidence.jsonl` reserved for events that constrain claims:

- acceptance passed or failed
- blocker
- user feedback
- decision
- state transition
- key finding

Do not promote ordinary process logs into evidence.

### 4. Impact-Based Decision Hooking

Use three levels of decision handling:

- `inline alignment`: ordinary Step/SubTask choices with a short parent-alignment note.
- `light packet`: subpath switch, blocker, repeated failed attempt, or meaningful uncertainty.
- `full mission review`: success-critical task changes, Mission closure, abandonment,
  user feedback challenging the target, or same-path third repair.

### 5. Checkpoint Command

Consider a future `checkpoint` command that records state, optional log, optional
evidence, validation, and survey update in one call.

This is a runtime ergonomics improvement, not a semantic decision engine.

### 6. Triggered Anti-Spiral

Anti-Spiral should remain a serious brake, not a permanent interruption.

Trigger it only when signals appear:

- same object touched for the third time
- user says the result got worse or remains unsatisfactory
- new layers are being added without acceptance progress
- next same-path action cannot produce new decision-constraining evidence

## Non-Goals

- Do not turn `tplan` into a simple TODO list.
- Do not remove Mission anchoring.
- Do not weaken evidence/log separation.
- Do not let lite mode bypass high-impact decision hooks.
- Do not make scripts decide semantic truth or runtime level correctness.
- Do not make shorter records the goal when recovery, acceptance, or audit needs more detail.

## Acceptance Criteria

- `tplan` docs clearly state that runtime levels reduce ceremony, not core control capability.
- Lite mode has a hard minimum state contract: Mission objective, acceptance criteria,
  active node, latest state, and blocker/evidence/decision summary.
- Docs define when actions should be promoted from lightweight log to Step.
- Docs define sparse evidence categories and explicitly reject process-log promotion.
- Decision hook guidance distinguishes inline alignment, light packet, and full Mission review.
- Anti-Spiral is documented as trigger-based rather than always-on.
- High-impact changes still require alignment/review regardless of runtime level.
- Tests or pressure scenarios cover lite work that remains recoverable and strict work
  that still triggers review.
