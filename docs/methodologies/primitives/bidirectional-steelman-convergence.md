# Bidirectional Steelman Convergence / 双向钢人收敛

Bidirectional Steelman Convergence is a cross-cutting cognitive primitive for real
competing-frame judgments. It is not a standalone method, not a new route, and not a
judgment owner.

Its purpose is narrow: after the active object and decision context are fit enough to
compare, strengthen the active position and the strongest relevant counter-position,
then converge through the disagreement that can actually change the verdict.

## Core Rule

> 先把双方都加强到最难被轻易击败，再找真正会翻转结论的那个变量。

Do not use this primitive merely because two opinions are mentioned. Use it when a
material judgment risks either:

- accepting the user's or agent's current frame too easily; or
- ending in symmetrical `both sides are right` framing even though the decision needs a
  sharper owner, condition, evidence move, or action.

The active judgment owner remains `EDSP`, `SELA`, `Whole Elephant`, `Decision Context
Calibration`, or another routed owner. This primitive only supplies competing-frame
pressure and convergence.

## Prerequisite: Lock Before Steelman

Do not steelman a malformed question as if its offered sides were exhaustive.

Before this primitive runs, lock the comparison surface:

- same judgment object;
- same decision actor/timing/target when the judgment is situated;
- same evidence / claim ceiling;
- no unresolved frame error that would make the A/B comparison synthetic.

If Frame Fitness or EDSP finds a malformed binary, reframe first. A third-frame escape
is valid and preferred over strengthening a false binary.

## Mainline

### 1. Steelman A

Construct the strongest defensible version of the active/current position.

Preserve what is genuinely true. Do not weaken it to make the later verdict easy.
Name the strongest support, the result it predicts, and the boundary it must survive.

### 2. Steelman B

Construct the strongest relevant counter-position under the same object, context, and
evidence ceiling.

This is not `find objections to A`. The counter-position should be able to win if its
view of the result controller, evidence, or decision target is actually better.

### 3. Decisive Discriminator

Do not summarize ten differences. Name the disagreement with the highest verdict value:

- a fact that would change the conclusion;
- a result controller or definition-authority difference;
- an actor/timing/target/tradeoff variable that flips situated advice;
- a failure prediction that distinguishes the frames;
- or another observable condition that changes strategy, evidence, next action, stop,
  or handoff.

If no identified difference can change the verdict or action, the steelman pass has not
created decision value and should stop rather than add prose.

### 4. One Information-Gain Move

Resolve the decisive discriminator with the smallest useful next move:

- externally verifiable fact or runtime result -> acquire evidence;
- user-owned goal, value, acceptable loss, or authority -> ask at most one decisive
  question;
- facts/context already sufficient -> ask nothing and decide now;
- evidence cannot currently resolve the difference -> lower the claim ceiling or return
  an explicit conditional / blocked disposition.

`One question` is an upper bound, not a requirement.

### 5. Commit

Return control to the active judgment owner and commit to the strongest supported
visible result:

- verdict or active conditional branch;
- why that frame wins for the current object/decision;
- the main overturn condition;
- next action.

Do not end with a generic 50/50 synthesis merely because both steelmanned positions
contain local truths.

## Minimal Internal Shape

When useful for validation or debugging, keep the internal shape small:

```yaml
active_position:
strongest_counter_position:
comparison_lock:
  judgment_object:
  decision_context:
  evidence_ceiling:
third_frame_escape:
true_disagreement:
decisive_discriminator:
resolution_move: acquire_evidence | ask_one_user_question | decide_now | conditional_or_blocked
one_question:
overturn_condition:
```

This is not a reasoning transcript. Keep fields as bounded claims or references.

## Boundaries

- No real competing-frame judgment, no steelman pass.
- No frame lock, no steelman pass.
- Missing facts are not an invitation to invent stronger arguments; acquire evidence.
- User preferences, values, aesthetics, and risk posture are legitimate constraints,
  not opposing positions that require steelmanning by default.
- Low-risk deterministic execution should remain direct.
- Do not force symmetry after the evidence becomes asymmetric.
- Do not require consensus. A strong counter-position may still lose clearly.
- Do not create a new method route, judgment owner, or runtime role model.

## Relationship To Existing Primitives

- `Frame Fitness Check` runs earlier when the question itself may be captured or
  malformed.
- `Whole Elephant Protocol` still owns definition-authority judgments; steelman helps it
  compare a local-definition claim with the strongest competing whole-object account.
- `Decision Context Calibration` still owns situated decisions; steelman helps expose
  which context variable actually flips the answer.
- `Perspective Pressure` remains useful inside SELA/EDSP. This primitive is narrower and
  explicitly requires symmetric strengthening plus decisive convergence.
- `Evidence / Claim Ceiling` decides how far either position may claim facts.
- `Aspect Ownership Matrix` still chooses the visible judgment owner; steelman cannot
  average or override owners.

## Validation Boundary

The presence of this document or its markers proves only that the protocol is available.
It does not prove behavioral improvement.

Behavioral acceptance requires preregistered comparison against current Mindthus and the
source bidirectional-steelman protocol on known regressions, surface-changed variants,
and negative controls. If the source protocol performs as well as or better than the
Mindthus adaptation, keep the simpler treatment instead of preserving extra machinery.
