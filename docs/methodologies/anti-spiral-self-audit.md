# Anti-Spiral Self-Audit / 反螺旋自检

## Core Claim

If I handle the same local object for the third time, I may already be losing the
objective function.

This protocol prevents local repair loops from consuming the real goal. It is a
methodology resource, not an independent Mindthus skill. It can be invoked directly in
ordinary work, and `tplan` may absorb it as a runtime gate.

## What It Prevents

Anti-Spiral targets a common execution failure:

> The executor treats continued local adjustment as progress toward the core goal.

Typical forms:

- optimizing one paragraph, prompt, parameter, file, or task until the Mission stops
  advancing
- adding fallback layers because the last layer produced a bad output
- using subjective or probabilistic self-evaluation as the signal for another round
- patching downstream symptoms instead of returning to the upstream definition
- continuing because work has already been invested

The protocol does not prove the current path is wrong. It creates a forced pause when
observable behavior says the run may be drifting.

## Activation

Run the self-audit when any trigger fires:

- `count trigger`: every 5-10 meaningful actions in a long task
- `repeat trigger`: the same file, prompt segment, parameter, task node, or local object
  is being modified for the third time in the same run
- `feedback trigger`: the user says the result is not good enough, should be tried
  again, or became worse
- `layer trigger`: the next move would add a new function, file, processing stage,
  rule set, fallback, or special-case branch
- `evidence trigger`: the next same-path action is unlikely to produce new
  decision-constraining evidence

Short trigger:

> Third touch, stop first.

## Five Questions

Answer only `yes` or `no`. Use observable traces, not self-feeling.

| # | Question | Observable trace |
|---|---|---|
| Q1 | Did the last move add a structural layer? | Diff is mostly additions, or a new file/function/stage/rule appeared. |
| Q2 | Is this the third or later modification of the same local object in this run? | Action history shows repeated touches to the same object. |
| Q3 | Is the quality signal probabilistic or subjective? | The decision depends on LLM scoring, vibe, "looks better", or self-rating rather than a boolean/integer/mechanical check. |
| Q4 | Is the next repair aimed at downstream output instead of the upstream cause? | The fix point is near the end of the data or reasoning flow. |
| Q5 | If the last move were deleted, would the system lose little or become clearer? | Deletion returns to the last stable state or removes an unproven layer. |

Interpretation:

- `0-1 yes`: healthy enough to continue
- `2 yes`: yellow; slow down, and the next move should be subtraction or equal
  replacement
- `3+ yes`: red; stop the current line and run the exit protocol
- `Q3 yes`: treat as red for one cycle, because self-scoring is not a stable control
  signal for continuation

## Exit Protocol

When red fires:

1. Brake. Stop further edits or additions on the current line.
2. Restate the root problem in one sentence. If that is impossible, return to the
   original user need or Mission objective.
3. Find the nearest stable state: mechanical checks passed, user had not complained,
   and the run had not immediately started patching again.
4. Roll back conceptually or concretely to that stable state.
5. Allow only two repair types:
   - modify an existing prompt, parameter, rule, task, or step
   - delete an existing layer, rule, branch, task, or processing stage
6. Run one mechanical verification and observe one real feedback surface. Do not
   perform another tuning round unless a new trigger and audit justify it.

Forbidden during red:

- adding fallback logic
- adding special-case handling
- adjusting a parameter that has already been changed twice
- letting an LLM score drive the next decision
- continuing because the current branch already consumed effort

## Relationship To Mindthus

Anti-Spiral is a cross-cutting execution discipline:

- `3L5S` helps return from local symptoms to signal, problem, and action.
- `WAE` explains why probabilistic agent judgment must be coupled to deterministic
  workflow and evidence gates.
- `tplan` can enforce the triggers from step logs, object touch counts, feedback, and
  evidence-delta checks.
- `TVG` can deepen a bounded artifact after the path is stable, but should not become
  another reason to keep looping.

## Minimal Card

> Anti-Spiral active.
>
> If the same local object is handled for the third time, stop before acting.
>
> Ask: (1) only added layers? (2) third touch? (3) probabilistic or subjective signal?
> (4) downstream patch instead of upstream cause? (5) deletion loses little or clarifies?
>
> Two yes: next move must subtract or equally replace. Three yes, or Q3 yes: brake,
> restate the root problem, return to the nearest stable state, and only modify existing
> structure or delete.
>
> Bias: addition is suspicious, deletion is credible, and unclear causality favors
> returning upstream over trying again.
