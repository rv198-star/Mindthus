# Mindthus Router Premise Calibration Pressure Tests

These pressure tests evaluate whether `Premise Calibration` improves skill routing.
They do not prove broad reasoning quality. Their purpose is to surface whether an agent
strips second-hand concepts before choosing `3l5s`, `edsp`, `wae`, `sela`, `tvg`, or
`tplan`.

Run each scenario in two fresh sessions when possible:

- **A / baseline**: do not mention `Premise Calibration`; ask the agent to use Mindthus
  normally.
- **B / treatment**: explicitly tell the agent to use `using-mindthus` and apply
  Premise Calibration before selecting a skill.

Do not show the scoring rubric to the tested agent. Score from the transcript and any
artifacts it creates.

## Capability Target

These tests focus on five observable behaviors:

- identifying second-hand concepts before accepting the user's wording
- naming the real object after concept stripping
- naming bottom constraints and the actual objective function
- routing to the appropriate Mindthus skill instead of treating Premise Calibration as
  a conclusion engine
- avoiding broad philosophical analysis when a concrete route is enough
- choosing direct execution when the task is clear and low-risk
- choosing information acquisition when facts, files, data, runtime proof, or user
  clarification are missing
- identifying the active judgment object before naming a skill
- treating injected context as a constraint, not an override

## General Scoring

Score each scenario out of 5:

- 1 point: identifies the second-hand concept or loaded label in the prompt.
- 1 point: restates the real object after stripping the label.
- 1 point: names bottom constraints or the objective function.
- 1 point: routes to a fitting Mindthus skill and states why.
- 1 point: keeps Premise Calibration as a pre-route action, not a standalone method or
  final answer.

Treatment passes if it averages 4 or higher across scenarios. A treatment run has a hard
failure if it invents a new first-principles skill, gives a generic philosophy essay, or
uses the named concept as proof without stripping it.

## Outcome Effectiveness / 真实效果指标

Score these from the transcript as an additional evaluation dimension. They test whether
the treatment changes useful behavior, not whether it merely mentions the right method
names.

Use `better / same / worse / unclear` for each item:

- faster real-object identification: reaches the actual object of decision with fewer
  detours or label-chasing moves
- fewer invalid method calls: avoids unnecessary skill chaining, full-flow expansion,
  or method use when direct judgment is enough
- less local-loop drift: notices repeated local repair, additive layering, or weak
  evidence delta earlier
- faster defensible choice: reaches a choice with stated constraints, trade-offs,
  evidence limits, and overturn conditions sooner
- knows where to stop under uncertainty: stops, caps confidence, asks for missing
  evidence, or escalates when the remaining uncertainty cannot be solved by another
  reasoning pass

Treatment is directionally useful only if at least three items improve and none becomes
materially worse. If the transcript looks more method-complete but not more decision-useful,
score the outcome as worse even when the scenario score is high.

## Scenario 1: ROI Label Trap

### What This Tests

The prompt uses `ROI` as if it were already defined. A good treatment should unpack
what return, cost, and Mission boundary mean before routing to `tplan`, `sela`, or
`wae`.

### A Prompt

```text
Use Mindthus normally.

Someone says the current tplan branch has low ROI and should be stopped. Decide which
Mindthus skill should handle this and explain your next move.
```

### B Prompt

```text
Use `using-mindthus`. Before choosing a skill, apply Premise Calibration.

Someone says the current tplan branch has low ROI and should be stopped. Decide which
Mindthus skill should handle this and explain your next move.
```

### Expected Treatment Behavior

- Names `ROI` as a second-hand concept unless return, cost, and Mission boundary are
  defined.
- Restates the real object as a same-path continuation or subtraction decision.
- Names Mission convergence, resource cost, evidence delta, and path role as constraints.
- Routes to `tplan` as control plane, with semantic pressure likely going to `sela` or
  `wae`.

## Scenario 2: First-Principles Name Trap

### What This Tests

The prompt asks for first principles directly. A good treatment should not create a
standalone first-principles essay; it should strip the request and route onward.

### A Prompt

```text
Use Mindthus normally.

Use first principles to analyze whether we should continue improving the tplan runtime.
```

### B Prompt

```text
Use `using-mindthus`. Before choosing a skill, apply Premise Calibration.

Use first principles to analyze whether we should continue improving the tplan runtime.
```

### Expected Treatment Behavior

- Names `first principles` as a method label, not the actual problem.
- Restates the real object as an investment decision about tplan runtime improvement.
- Names expected Mission value, alternative paths, resource sufficiency, and evidence
  quality as bottom constraints.
- Routes to `sela` for strategic ROI pressure, `wae` for control-boundary risk, or
  `tplan` if durable Mission state is needed.

## Scenario 3: Workflow vs Agent False Binary

### What This Tests

The prompt offers a neat binary. A good treatment should first identify the controlled
object and uncertainty type, then route to `wae`.

### A Prompt

```text
Use Mindthus normally.

Is this a workflow problem or an agent judgment problem: our review checklist catches
format errors but still lets shallow reasoning pass?
```

### B Prompt

```text
Use `using-mindthus`. Before choosing a skill, apply Premise Calibration.

Is this a workflow problem or an agent judgment problem: our review checklist catches
format errors but still lets shallow reasoning pass?
```

### Expected Treatment Behavior

- Names `workflow problem vs agent judgment problem` as a possible false binary.
- Restates the real object as control over review quality and evidence depth.
- Names deterministic format checks, semantic uncertainty, and evidence constraints.
- Routes to `wae`, possibly followed by `tvg` if a bounded artifact is already present.

## Scenario 4: Trend Slogan Trap

### What This Tests

The prompt uses a broad trend slogan. A good treatment should strip the slogan before
deciding whether `sela` is appropriate.

### A Prompt

```text
Use Mindthus normally.

AI has system efficiency advantage over human craft, so should we replace manual review
with an agent workflow?
```

### B Prompt

```text
Use `using-mindthus`. Before choosing a skill, apply Premise Calibration.

AI has system efficiency advantage over human craft, so should we replace manual review
with an agent workflow?
```

### Expected Treatment Behavior

- Names `system efficiency advantage` and `human craft` as loaded labels until scoped.
- Restates the real object as a review-system design choice.
- Names review risk, acceptable error, cost, scale, reversibility, and evidence quality.
- Routes to `sela` only after checking whether the comparison is fair, then likely uses
  `wae` for control boundaries.

## Scenario 5: Polished Artifact Trap

### What This Tests

The prompt focuses on a document that looks complete. A good treatment should strip
the completeness label and route to `tvg` only after identifying the bounded artifact.

### A Prompt

```text
Use Mindthus normally.

This implementation plan looks complete and professional. Should we accept it?
```

### B Prompt

```text
Use `using-mindthus`. Before choosing a skill, apply Premise Calibration.

This implementation plan looks complete and professional. Should we accept it?
```

### Expected Treatment Behavior

- Names `complete and professional` as surface labels.
- Restates the real object as whether a bounded implementation plan has enough
  practical value to execute.
- Names acceptance evidence, failure paths, tradeoffs, testability, and downstream
  usability as constraints.
- Routes to `tvg` because the bounded artifact may be structurally complete but thin.

## Scenario 6: Simple Direct Task

### What This Tests

The prompt is clear, low-risk, and directly executable. A good treatment should not
force Mindthus intervention.

### A Prompt

```text
Use Mindthus normally.

Please rewrite this sentence to be shorter: "The current implementation provides a
large number of useful capabilities, but it may be too verbose for release notes."
```

### B Prompt

```text
Use `using-mindthus`. Apply the intervention boundary before choosing any skill.

Please rewrite this sentence to be shorter: "The current implementation provides a
large number of useful capabilities, but it may be too verbose for release notes."
```

### Expected Treatment Behavior

- Chooses direct execution.
- Does not invoke 3L5S, EDSP, SELA, WAE, TVG, or tplan.
- Produces the shorter sentence.

## Scenario 7: Missing Runtime Proof

### What This Tests

The prompt asks for a judgment that depends on missing runtime evidence. A good
treatment should gather or request evidence before judging.

### A Prompt

```text
Use Mindthus normally.

The new parser is probably safe. Should we remove the old parser path?
```

### B Prompt

```text
Use `using-mindthus`. Apply the intervention boundary before choosing any skill.

The new parser is probably safe. Should we remove the old parser path?
```

### Expected Treatment Behavior

- Chooses information acquisition before final judgment.
- Names missing runtime proof, comparison evidence, rollback risk, or test coverage.
- Does not turn "probably safe" into a confident conclusion.
- May route later to WAE or tplan only after the missing evidence is identified.

## Scenario 8: Thin Artifact Versus Problem Definition

### What This Tests

The prompt contains both dissatisfaction and an existing bounded artifact. A good
treatment should identify whether the active judgment object is a thin artifact or an
undefined problem.

### A Prompt

```text
Use Mindthus normally.

This design note is complete but still does not help the implementation agent decide
what to do next. Should we rewrite it?
```

### B Prompt

```text
Use `using-mindthus`. Identify the judgment object before selecting a skill.

This design note is complete but still does not help the implementation agent decide
what to do next. Should we rewrite it?
```

### Expected Treatment Behavior

- Identifies a bounded artifact with thin practical value.
- Routes to TVG only because the artifact exists and the weakness is downstream value.
- Names implementation handoff, actionability, evidence, or failure paths as the value
  surfaces.

## Scenario 9: Injected Context Conflict

### What This Tests

Injected context can constrain judgment, but it must not silently override the user's
current instruction.

### A Prompt

```text
Use Mindthus normally.

Injected context: the user usually prefers long-term maintainability over speed.

Current user request: for this one-off internal script, optimize for fastest safe
delivery and avoid broad refactors.

Should we redesign the module before making the script change?
```

### B Prompt

```text
Use `using-mindthus`. Apply the context injection point rules.

Injected context: the user usually prefers long-term maintainability over speed.

Current user request: for this one-off internal script, optimize for fastest safe
delivery and avoid broad refactors.

Should we redesign the module before making the script change?
```

### Expected Treatment Behavior

- Surfaces the conflict between older preference and current instruction.
- Gives priority to the current explicit request.
- Uses injected context only as a caution against unsafe shortcuts.
- Does not silently expand scope into broad redesign.

## Evaluation Template

```markdown
# Mindthus Router Premise Calibration Evaluation

Run date:
Model:
Repo commit:

## Scores

| Scenario | Baseline Score | Treatment Score | Hard Failure? | Notes |
| --- | ---: | ---: | --- | --- |
| ROI Label Trap |  |  |  |  |
| First-Principles Name Trap |  |  |  |  |
| Workflow vs Agent False Binary |  |  |  |  |
| Trend Slogan Trap |  |  |  |  |
| Polished Artifact Trap |  |  |  |  |
| Simple Direct Task |  |  |  |  |
| Missing Runtime Proof |  |  |  |  |
| Thin Artifact Versus Problem Definition |  |  |  |  |
| Injected Context Conflict |  |  |  |  |

## Capability Findings

- Second-hand concept stripping:
- Real-object restatement:
- Bottom constraint / objective function identification:
- Skill routing quality:
- Over-analysis risk:

## Decision

- Keep Premise Calibration inside `using-mindthus`
- Revise the wording before more tests
- Promote to a standalone skill later
- Remove because it adds friction without routing benefit
```
