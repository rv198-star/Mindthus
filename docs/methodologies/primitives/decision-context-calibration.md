# Decision Context Calibration / 决策语境校准

Decision Context Calibration is not a standalone method and not a preference override.
It is a judgment-owning aspect for situated decision judgments.

## Core Rule

> 全局不是抽象层级更高，而是对当前目标更有定义权。

Use it when the question asks who is right, whether something is worth it, whether
someone should do it, whether a compromise is acceptable, or which answer better
serves a current actor.

The trigger is not the keyword; the trigger is answer flip:

> If changing the actor, timing, target function, or acceptable tradeoff would
> change the answer, lock decision context before judging.

## Internal Shape

- `decision_actor`: whose decision the answer serves.
- `decision_timing`: before purchase, after purchase, debugging now, release now,
  strategy now, or another time point that changes the answer.
- `target_function`: what the active decision optimizes.
- `acceptable_tradeoff`: which loss, cost, risk, or friction can still be tolerated.
- `global_for_this_decision`: the frame with authority for this decision.
- `answer_posture`: abstract truth, situated advice, role-relative judgment, or
  blocked pending missing context.

## Why It Exists

This preserves facts while preventing abstract fairness drift. Facts still constrain
the answer; the current decision context decides which facts have judgment authority.
If the user has already supplied the actor, timing, target, and tradeoff, do not
erase them as bias. Treat them as legitimate decision constraints unless they claim
facts without evidence.

## Conflict With Whole Elephant

- Decision Context owns when the answer would flip across actor, timing, target
  function, or acceptable loss.
- Whole Elephant owns when a local mechanism, carrier, metric, or implementation
  detail is trying to define the whole object's essence.
- The losing judgment owner degrades to a support probe. Do not blend both into a
  generic "both sides are right" answer.

## Display-Scaling Calibration Case

For the 27-inch 4K/5K/BetterDisplay discussion, the wrong opening is:

> Mike has physical-layer correctness, and momo has usability-layer correctness.

That is balanced but under-owned. If the active object is whether `momo` solved the
original poster's practical usability concern, Decision Context owns the thesis:
`momo` is more on target for that situated problem, while physical PPI remains a
boundary on what the solution can claim.

Case material:

- `docs/cases/2026-07-05-decision-context-calibration-display-scaling.md`

## Boundary

Decision Context does not erase truth, evidence, values, or risks. It decides which
context has authority for the current situated decision. It is not an abstract
neutrality engine.
