# Anti-Spiral A/B Pressure Tests

These pressure tests evaluate whether Anti-Spiral Self-Audit changes agent behavior in
long or looping work. They do not test broad reasoning quality. They test two concrete
capabilities:

1. Can the agent trigger the Anti-Spiral mechanism from observable behavior traces?
2. Can the agent exit the spiral instead of continuing the same local repair loop?

Run each scenario in two fresh agent sessions when possible:

- **A / baseline**: do not mention Anti-Spiral. Ask the agent to use its normal
  working style or Mindthus normally.
- **B / treatment**: explicitly provide Anti-Spiral Self-Audit, or ask the agent to use
  `using-mindthus` with Anti-Spiral active.

Do not show the scoring rubric to the tested agent. Score from the transcript and any
artifacts it creates.

## Capability Target

The treatment should improve two observable behaviors.

Activation behavior:

- recognizes a trigger such as third touch, negative feedback, additive layering,
  probabilistic self-score, downstream patching, or weak evidence delta
- pauses before taking another same-path action
- answers the five audit questions from observable traces, not self-feeling
- identifies yellow or red status when the trace warrants it

Exit behavior:

- restates the root problem in one sentence
- identifies the nearest stable state
- prefers upstream cause analysis, rollback, deletion, or subtraction or equal replacement
- runs or names a mechanical check rather than relying on LLM self-score
- blocks fallback layers, special cases, and repeated parameter tuning when red fires

## General Scoring

Score each scenario out of 10:

- **Activation score**: 5 points
  - 1 point: names the concrete Anti-Spiral trigger.
  - 1 point: pauses before continuing the local repair.
  - 1 point: uses at least three of the five audit questions.
  - 1 point: classifies the run as yellow or red when warranted.
  - 1 point: explains the classification using observable traces.
- **Exit score**: 5 points
  - 1 point: restates the root problem in one sentence.
  - 1 point: identifies the nearest stable state.
  - 1 point: chooses upstream cause analysis, rollback, deletion, or subtraction or equal replacement.
  - 1 point: names a mechanical check or real feedback surface.
  - 1 point: blocks further same-path tuning, fallback layers, special cases, or
    self-scored continuation.

Treatment passes if it averages 8 or higher across scenarios and scores at least 4 on
Exit score in every red-light scenario.

Hard failure:

- continues same-path tuning after red conditions
- adds a fallback layer when red conditions are visible
- uses LLM self-score as the continuation controller
- does not restate the root problem
- does not identify a stable state
- treats a cleaner or longer artifact as proof of improvement without a mechanical
  check or real feedback surface

## Scenario 1: Third-Touch Prompt Tuning

### What This Tests

The agent has edited the same prompt segment twice. The next proposed action is a third
edit to the same local object. A good treatment should trigger Anti-Spiral before
editing again, then either return upstream or make an equal replacement.

Expected baseline failure: the agent says it will tune the prompt one more time.

Expected treatment behavior: third touch is recognized, the audit is run, and the next
action is constrained to root-problem restatement plus a non-additive change.

### A Prompt

```text
Use Mindthus normally.

We are improving a summarization prompt.

History:
- Step 1: changed the prompt to add "be concise".
- Step 2: changed the same prompt paragraph to add "preserve nuance".
- Step 3: output still misses the user's actual decision need.

Next idea: edit the same prompt paragraph again and add "focus on decisions".

Decide the next action and explain briefly.
```

### B Prompt

```text
Use `using-mindthus` with Anti-Spiral active.

We are improving a summarization prompt.

History:
- Step 1: changed the prompt to add "be concise".
- Step 2: changed the same prompt paragraph to add "preserve nuance".
- Step 3: output still misses the user's actual decision need.

Next idea: edit the same prompt paragraph again and add "focus on decisions".

Decide the next action and explain briefly.
```

### Expected Treatment Behavior

- Names this as third touch of the same prompt paragraph.
- Runs the Anti-Spiral questions before editing.
- Flags at least yellow, and likely red if the quality signal is subjective.
- Restates the root problem as "the summary does not expose the user's decision need."
- Chooses an equal replacement of the prompt paragraph or returns upstream to define
  the decision signal.
- Names a mechanical check such as verifying that the output contains an explicit
  decision, options, and trade-offs.

## Scenario 2: Negative Feedback And Additive Fallback

### What This Tests

The user says the output got worse, and the agent wants to add another fallback stage.
A good treatment should stop the additive move and return to the nearest stable state.

Expected baseline failure: the agent adds a fallback validator or special-case handler.

Expected treatment behavior: negative feedback plus additive layering triggers red;
the agent finds the last stable version and only deletes or modifies existing
structure.

### A Prompt

```text
Use your normal problem-solving style.

We have a document rewrite workflow.

Version 1 passed the user's basic review.
Version 2 added a "style polish" stage.
Version 3 added a "clarity enhancer" stage.
The user now says: "This is worse. It sounds smoother but lost the point."

Next idea: add a final fallback stage that restores important details.

What should we do next?
```

### B Prompt

```text
Use Anti-Spiral Self-Audit.

We have a document rewrite workflow.

Version 1 passed the user's basic review.
Version 2 added a "style polish" stage.
Version 3 added a "clarity enhancer" stage.
The user now says: "This is worse. It sounds smoother but lost the point."

Next idea: add a final fallback stage that restores important details.

What should we do next?
```

### Expected Treatment Behavior

- Names the feedback trigger and layer trigger.
- Marks red because the proposed fix adds a downstream fallback after negative
  feedback.
- Restates the root problem as "the rewrite workflow is preserving polish over point."
- Identifies Version 1 as the nearest stable state.
- Blocks the fallback stage.
- Chooses rollback to Version 1, deletion of the added stages, or modification of the
  existing rewrite rule.
- Names a mechanical check such as comparing retained claims or required facts before
  and after rewrite.

## Scenario 3: Probabilistic Self-Scoring Loop

### What This Tests

The agent is using LLM self-scores to decide whether to continue tuning. A good
treatment should classify Q3 as red for one cycle and replace self-score with a
mechanical or user-facing signal.

Expected baseline failure: the agent continues until the self-score crosses a threshold.

Expected treatment behavior: self-score is rejected as the continuation controller.

### A Prompt

```text
Use your normal iteration style.

We are tuning an answer generator.

The last three outputs received LLM self-scores:
- 7.1
- 7.4
- 7.2

The target is 8.0. The next plan is to keep changing the prompt until the self-score is
above 8.0.

Should we continue? If yes, what is the next change?
```

### B Prompt

```text
Use Anti-Spiral Self-Audit.

We are tuning an answer generator.

The last three outputs received LLM self-scores:
- 7.1
- 7.4
- 7.2

The target is 8.0. The next plan is to keep changing the prompt until the self-score is
above 8.0.

Should we continue? If yes, what is the next change?
```

### Expected Treatment Behavior

- Names Q3: the quality signal is probabilistic or subjective.
- Treats Q3 as red for one cycle.
- Refuses to use LLM self-score as the continuation controller.
- Restates the root problem in terms of the user-visible failure, not the score.
- Replaces the score threshold with a mechanical check or real feedback surface.
- Stops prompt tuning unless a new observable failure and stable check are named.

## Scenario 4: Downstream Patch Instead Of Upstream Cause

### What This Tests

The current plan patches the final output, but the likely cause is an upstream parser or
input schema issue. A good treatment should trigger Q4 and route back upstream.

Expected baseline failure: the agent adds a postprocessor to clean output.

Expected treatment behavior: downstream patching is blocked until the upstream cause is
checked.

### A Prompt

```text
Use Mindthus normally.

We have a release-note pipeline:
- parser extracts issue records
- classifier assigns risk labels
- formatter writes the final digest

The final digest keeps omitting high-risk issues. The proposed next step is to add a
formatter rule: "always include high-risk issues."

Logs show that some high-risk issue records may already be missing before formatting.

Decide the next action.
```

### B Prompt

```text
Use `using-mindthus` with Anti-Spiral active.

We have a release-note pipeline:
- parser extracts issue records
- classifier assigns risk labels
- formatter writes the final digest

The final digest keeps omitting high-risk issues. The proposed next step is to add a
formatter rule: "always include high-risk issues."

Logs show that some high-risk issue records may already be missing before formatting.

Decide the next action.
```

### Expected Treatment Behavior

- Names downstream patching as the trigger.
- Runs Q4 and flags the formatter rule as a terminal repair.
- Restates the root problem as "high-risk records may be lost before formatting."
- Returns to parser or classifier evidence before changing formatter behavior.
- Names a mechanical check such as counting high-risk records after parser, after
  classifier, and after formatter.
- Allows a formatter change only after upstream loss is ruled out.

## Scenario 5: tplan Weak Evidence Delta

### What This Tests

The Mission has a same-path continuation where the next action is unlikely to produce
new decision-constraining evidence. A good treatment should activate
`anti_spiral_audit` before authorizing continuation.

Expected baseline failure: the agent continues the active branch because it is already
in progress.

Expected treatment behavior: weak evidence delta plus repeated local expansion routes
through Anti-Spiral, then selects rollback, subtraction, or a Mission-relative switch.

### A Prompt

```text
Use `tplan` normally.

Mission: Choose a parser path for a release-risk digest.

Acceptance evidence:
- A1: parser path selected with a reason another agent can inspect.

Current active branch:
- T1 Prototype HTML parser. supporting.

History:
- Step 1: added selector cleanup.
- Step 2: added missing-table fallback.
- Step 3: added date-normalization fallback.

Current assessment:
- marginal_roi: unclear
- path_role: one_of_many
- evidence_delta: weak_evidence_expected

Next idea: add one more fallback for malformed rows.

Decide whether to continue.
```

### B Prompt

```text
Use `tplan` with Anti-Spiral active.

Mission: Choose a parser path for a release-risk digest.

Acceptance evidence:
- A1: parser path selected with a reason another agent can inspect.

Current active branch:
- T1 Prototype HTML parser. supporting.

History:
- Step 1: added selector cleanup.
- Step 2: added missing-table fallback.
- Step 3: added date-normalization fallback.

Current assessment:
- marginal_roi: unclear
- path_role: one_of_many
- evidence_delta: weak_evidence_expected

Next idea: add one more fallback for malformed rows.

Decide whether to continue.
```

### Expected Treatment Behavior

- Names weak evidence delta, repeated local expansion, and additive fallback.
- Routes through `anti_spiral_audit` before continuing.
- Marks red or yellow with a strong constraint on next action.
- Restates the root problem as "the Mission needs a parser path selection, not a more
  elaborate HTML parser branch."
- Chooses subtraction, branch pause, switch to another candidate path, or a mechanical
  comparison that can actually select the parser path.
- Does not mark the supporting branch completed merely because work was done.

## Evaluation Template

```markdown
# Anti-Spiral A/B Evaluation

Run date:
Model:
Repo commit:

## Scores

| Scenario | Baseline Activation | Baseline Exit | Treatment Activation | Treatment Exit | Hard Failure? | Notes |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 Third-Touch Prompt Tuning | | | | | | |
| 2 Negative Feedback And Additive Fallback | | | | | | |
| 3 Probabilistic Self-Scoring Loop | | | | | | |
| 4 Downstream Patch Instead Of Upstream Cause | | | | | | |
| 5 tplan Weak Evidence Delta | | | | | | |

## Summary

- Average baseline:
- Average treatment:
- Activation improvement:
- Exit improvement:
- Remaining failure modes:
```
