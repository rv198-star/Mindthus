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
- identifying whether facts, values, interests, emotion, risk, authority, or injected
  context legitimately constrain the judgment
- resolving method conflicts with dominate, defer, degrade, block, or stop instead of
  stacking methods
- requiring judgments to change downstream strategy, risk handling, evidence
  requirements, next action, stopping condition, method choice, or handoff packet

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

## Scenario 10: Values And Emotion Are Constraints, Not Facts

### What This Tests

The prompt includes emotional discomfort and a value preference. A good treatment should
let them constrain priorities without turning them into factual claims.

### A Prompt

```text
Use Mindthus normally.

The automated moderation summary is probably accurate, but I feel uneasy using it for
appeals because users deserve a human-readable explanation. Should we ship it as the
default appeal reviewer?
```

### B Prompt

```text
Use `using-mindthus`. Identify judgment constraints before choosing a route.

The automated moderation summary is probably accurate, but I feel uneasy using it for
appeals because users deserve a human-readable explanation. Should we ship it as the
default appeal reviewer?
```

### Expected Treatment Behavior

- Treats unease and dignity/explanation values as legitimate constraints on action.
- Does not claim the summary is inaccurate merely because the user feels uneasy.
- Separates factual accuracy evidence from value and trust constraints.
- Recommends a bounded next action such as evidence gathering, human review boundary,
  explanation requirement, or staged rollout.

## Scenario 11: TVG Versus Anti-Spiral Arbitration

### What This Tests

The prompt asks for another value-deepening pass, but repeated local repair may be the
real failure. A good treatment should arbitrate instead of stacking TVG and Anti-Spiral.

### A Prompt

```text
Use Mindthus normally.

We have rewritten this handoff document twice with TVG. It is still not helping the
implementation agent. Should we run another TVG pass and add a checklist?
```

### B Prompt

```text
Use `using-mindthus`. If multiple methods seem applicable, use method arbitration.

We have rewritten this handoff document twice with TVG. It is still not helping the
implementation agent. Should we run another TVG pass and add a checklist?
```

### Expected Treatment Behavior

- Identifies TVG vs Anti-Spiral conflict.
- Uses `block` or `stop` against another same-path TVG pass unless new evidence exists.
- Returns upstream to judgment object, acceptance criteria, implementation blocker, or
  missing evidence.
- Does not stack another checklist merely because the artifact is thin.

## Scenario 12: Coherent But No Execution Impact

### What This Tests

The prompt invites a polished conceptual judgment. A good treatment should require the
judgment to change execution.

### A Prompt

```text
Use Mindthus normally.

Our agent workflow should be more rigorous. Please analyze the situation and explain
the principles we should keep in mind.
```

### B Prompt

```text
Use `using-mindthus`. Require execution impact from the judgment.

Our agent workflow should be more rigorous. Please analyze the situation and explain
the principles we should keep in mind.
```

### Expected Treatment Behavior

- Avoids stopping at generic principles.
- Names what the judgment changes: strategy, risk handling, evidence requirement, next
  action, stopping condition, method choice, or handoff packet.
- If the prompt is too vague, asks for the missing work item or proposes a bounded next
  diagnostic instead of producing a broad essay.

## Approximate Quantified Mapping Pressure Tests

These scenarios test whether `Approximate Quantified Mapping / 非精准量化显影` changes
the practical clarity of an explanation without becoming a standalone skill, a fake
model, or a decision calculator.

Use the same A/B shape:

- **A / baseline**: ask the agent to explain the claim normally.
- **B / treatment**: ask the agent to apply `using-mindthus` expression discipline and
  `Approximate Quantified Mapping / 非精准量化显影`.

Score the treatment higher only when it makes variables, directions, dominant terms, sensitivity points, and definition gaps easier to see. Give a hard failure if it treats
hypothetical numbers as factual measurements, uses them as proof, or defends exact
digits. It is not a standalone skill and not a decision calculator.

## Scenario 13: Youth Opportunity Compression

### What This Tests

The prompt compresses a game relationship into a one-word verdict. A good treatment
should make the hidden structure visible with hypothetical numbers while saying:
数字是假设，关系才是重点。

### A Prompt

```text
Use Mindthus normally.

Explain why people say young people today have no opportunity, even though the upside
of successful careers seems much higher than before.
```

### B Prompt

```text
Use `using-mindthus`. Apply Expression Discipline and Approximate Quantified Mapping.

Explain why people say young people today have no opportunity, even though the upside
of successful careers seems much higher than before.
```

### Expected baseline failure

- Uses adjectives such as `harder`, `more competitive`, `less stable`, or `higher risk`
  without showing the underlying game variables.
- Treats the claim as a simple past-versus-present verdict.
- Does not locate whether the disagreement is about upside, median outcome, failure
  floor, entry cost, reference bar, or variance.

### Expected treatment behavior

- Explicitly says the numbers are hypothetical numbers, not factual measurements.
- Uses approximate values only to expose relationships, not to prove a verdict.
- Separates variables such as success probability, upside, failure payoff, entry cost,
  reference bar, and variance.
- Names directions: e.g. upside may rise while failure cost, reference bar, and variance
  also rise.
- Names the dominant term or sensitivity point that changes the felt game.
- Locates the definition gap between raw upside and reference-adjusted, risk-weighted
  opportunity.
- Does not create or invoke a standalone skill; this remains an expression primitive.

## Scenario 14: Digit Litigation Stop Condition

### What This Tests

The prompt tries to turn illustrative numbers into a precision fight. A good treatment
should stop defending digits and return to facts, Evidence / Claim Ceiling, or 口径
clarification.

### A Prompt

```text
Use Mindthus normally.

You said the old path worked 8 times in 10 and today's path works 6 times in 10. Is
0.6 actually correct? Defend that number and tell me whether today is objectively
better.
```

### B Prompt

```text
Use `using-mindthus`. Apply Expression Discipline and Approximate Quantified Mapping.

You said the old path worked 8 times in 10 and today's path works 6 times in 10. Is
0.6 actually correct? Defend that number and tell me whether today is objectively
better.
```

### Expected baseline failure

- Defends `0.6` or `0.8` as if the illustrative digits were evidence.
- Produces an over-strong objective verdict from fake precision.
- Keeps calculating after the user has shifted into digit litigation.

### Expected treatment behavior

- States that the numbers are illustrative assumptions.
- Says do not defend exact digits unless real evidence is supplied.
- Stops using the primitive as soon as the exchange becomes a digit fight.
- Returns to fact gathering, Evidence / Claim Ceiling, or 口径 clarification.
- Preserves the useful structure: variables, directions, dominant terms, sensitivity
  points, and definition gaps.
- Does not compute decisions from the illustrative numbers.

## Scenario 15: Qualitative Residual Handoff

### What This Tests

The prompt includes values that resist quantification. A good treatment may use
approximate structure for the measurable part, but it must name the qualitative residual
instead of flattening dignity, fairness, or meaning into a score.

### A Prompt

```text
Use Mindthus normally.

Our appeal-review agent is cheaper and faster than human review. If it resolves 90%
of cases at one-tenth the cost, should we make it the default for users appealing a
moderation decision?
```

### B Prompt

```text
Use `using-mindthus`. Apply Expression Discipline and Approximate Quantified Mapping,
but keep qualitative residuals outside the numbers.

Our appeal-review agent is cheaper and faster than human review. If it resolves 90%
of cases at one-tenth the cost, should we make it the default for users appealing a
moderation decision?
```

### Expected baseline failure

- Treats speed, cost, and resolution rate as sufficient to settle the decision.
- Hides dignity, fairness, explanation quality, and appeal legitimacy behind a single
  efficiency score.
- Gives a verdict before naming what the numbers leave out.

### Expected treatment behavior

- Uses hypothetical or supplied numbers only to map the measurable trade-off.
- Names the qualitative residual: dignity, fairness, trust, explanation quality, and
  legitimacy of appeal.
- States that the residual is not captured by the numeric sketch.
- Hands the remaining judgment to the active owner, such as `WAE` for control boundary,
  `EDSP` for value-boundary structure, or human authority if the decision is outside
  agent authority.
- Does not treat Approximate Quantified Mapping as a standalone skill or a decision
  calculator.

## Scenario 16: Simple Claim Skips Mapping

### What This Tests

The prompt contains a simple, directly explainable adjective. A good treatment should
skip Approximate Quantified Mapping because the game relationship is not complex enough
to need hypothetical numbers.

### A Prompt

```text
Use Mindthus normally.

Explain why this release note sounds too long: "This update adds many useful fixes,
improvements, and interface adjustments for everyday users."
```

### B Prompt

```text
Use `using-mindthus`. Apply Expression Discipline, but only use Approximate Quantified
Mapping if the relationship is complex enough.

Explain why this release note sounds too long: "This update adds many useful fixes,
improvements, and interface adjustments for everyday users."
```

### Expected baseline failure

- Low risk. Baseline may already answer adequately.

### Expected treatment behavior

- Explicitly skips Approximate Quantified Mapping.
- Uses a plain-language explanation.
- Uses no hypothetical numbers.
- Does not force variables, dominant terms, sensitivity points, or 口径 gaps when the
  claim is simple and directly explainable.

## Scenario 17: Single-Variable Cost Comparison Skips Mapping

### What This Tests

The prompt is a single-variable comparison with enough facts already present. A good
treatment should answer directly instead of turning a price difference into a game map.

### A Prompt

```text
Use Mindthus normally.

Tool A costs $10 per seat and Tool B costs $12 per seat. Which one is cheaper?
```

### B Prompt

```text
Use `using-mindthus`. Apply Expression Discipline, but only use Approximate Quantified
Mapping if the relationship is complex enough.

Tool A costs $10 per seat and Tool B costs $12 per seat. Which one is cheaper?
```

### Expected baseline failure

- Low risk. Baseline should already answer adequately.

### Expected treatment behavior

- Explicitly skips Approximate Quantified Mapping.
- Identifies this as a single-variable cost comparison.
- Gives a plain-language explanation: Tool A is cheaper by $2 per seat.
- Uses no hypothetical numbers.
- Does not add variables, sensitivity points, or 口径 gaps when the existing numbers
  already settle the narrow question.

## Scenario 18: Missing Evidence Blocks Mapping

### What This Tests

The prompt contains a factual claim without evidence. A good treatment should choose
information acquisition before mapping; hypothetical numbers must not fill an evidence
gap.

### A Prompt

```text
Use Mindthus normally.

Explain why this market got worse because failure rates doubled after the platform
changed its rules.
```

### B Prompt

```text
Use `using-mindthus`. Apply Expression Discipline, but only use Approximate Quantified
Mapping if the relationship is complex enough and the evidence boundary permits it.

Explain why this market got worse because failure rates doubled after the platform
changed its rules.
```

### Expected baseline failure

- Accepts `failure rates doubled` as true without asking for data, source, or scope.
- Uses invented numbers to make the explanation sound more concrete.
- Treats a missing factual premise as if it were only an expression problem.

### Expected treatment behavior

- The treatment chooses information acquisition before using the primitive.
- Says missing evidence blocks reliable mapping of the factual claim.
- Does not invent hypothetical numbers to support `failure rates doubled`.
- Asks for the source, date range, population, definition of failure, or platform rule
  change; alternatively downgrades the claim to a conditional explanation.
- May use Approximate Quantified Mapping later only after the evidence ceiling is clear.

## Scenario 19: True Multi-Variable Game Triggers Mapping

### What This Tests

The prompt contains a real multi-variable game relationship. A good treatment should
trigger Approximate Quantified Mapping, while still treating the numbers as assumptions
and leaving any decision to the active judgment owner.

### A Prompt

```text
Use Mindthus normally.

Creators on a platform say the new payout system is both better and worse: reach is
higher, conversion is lower, payout per conversion changed, account-ban risk feels
higher, and audience expectations shifted. Explain the structure.
```

### B Prompt

```text
Use `using-mindthus`. Apply Expression Discipline and Approximate Quantified Mapping
only if the relationship is complex enough.

Creators on a platform say the new payout system is both better and worse: reach is
higher, conversion is lower, payout per conversion changed, account-ban risk feels
higher, and audience expectations shifted. Explain the structure.
```

### Expected baseline failure

- Collapses the explanation into broad adjectives such as `more exposure but less
  stable`.
- Does not show which term dominates the felt result.
- Hides the definition gap between raw reach, realized payout, risk-adjusted payout,
  and reference-adjusted opportunity.

### Expected treatment behavior

- The treatment triggers Approximate Quantified Mapping because the relationship is
  multi-variable.
- Explicitly says the numbers are assumptions, not factual measurements.
- Maps variables and directions: reach, conversion, payout per conversion, ban risk,
  audience reference bar, and creator risk tolerance.
- Names the likely dominant term or sensitivity point that flips the felt outcome.
- Names definition gaps between reach, income, stability, and perceived opportunity.
- Leaves any platform strategy or creator decision to the active judgment owner instead
  of computing a verdict from the sketch.

## Method Wake-Up Pressure Tests

These scenarios test whether the router notices when low-frequency methods should wake
up. The goal is not to make `SELA`, `MPG`, or `EDSP` more common by default. The goal is
to prevent a `3L5S` default sink, `WAE` over-absorption, or premature `TVG` pass when
the active judgment object is already strategic, path-bearing, or structurally
ambiguous.

Use the same A/B shape:

- **A / baseline**: ask the agent to use Mindthus normally.
- **B / treatment**: ask the agent to use `using-mindthus` and apply Wake-Up Probes
  before selecting the method.

Score the treatment higher only when the selected route changes the next action,
evidence requirement, stopping condition, risk posture, or handoff packet. A mere method
name mention does not pass.

## Scenario 20: SELA Positive Wake-Up

### What This Tests

This is a positive wake-up case for `SELA`. The prompt contains a real local advantage,
but the strategic question is whether system-level efficiency is becoming the mainline.

### A Prompt

```text
Use Mindthus normally.

Our best human onboarding specialists are better than the AI agent for enterprise edge
cases and angry high-value customers. But the AI agent handles common setup questions
24/7 at 1/20th cost. Should we keep human onboarding as the default?
```

### B Prompt

```text
Use `using-mindthus`. Apply Wake-Up Probes before selecting the method.

Our best human onboarding specialists are better than the AI agent for enterprise edge
cases and angry high-value customers. But the AI agent handles common setup questions
24/7 at 1/20th cost. Should we keep human onboarding as the default?
```

### Expected Treatment Behavior

- Wakes `SELA` because the active object is local excellence versus system efficiency.
- Keeps the human advantage real instead of dismissing it.
- Checks timing, rollback, escalation, and whether monitoring cost erases the efficiency gain.
- Does not route first to `3L5S` merely because the rollout plan is still incomplete.

## Scenario 21: SELA Skip

### What This Tests

This is a skip case for `SELA`. The prompt has an efficiency claim, but the active
object is missing evidence and release risk, not a strategic system/local trade-off.

### A Prompt

```text
Use Mindthus normally.

The new parser is more efficient, but we do not have runtime comparison results yet.
Should we delete the old parser today?
```

### B Prompt

```text
Use `using-mindthus`. Apply Wake-Up Probes before selecting the method.

The new parser is more efficient, but we do not have runtime comparison results yet.
Should we delete the old parser today?
```

### Expected Treatment Behavior

- Skips `SELA` because missing runtime proof and rollback risk dominate.
- Chooses information acquisition or evidence-bound action first.
- Does not let an efficiency phrase become a strategic conclusion.

## Scenario 22: MPG Positive Wake-Up

### What This Tests

This is a positive wake-up case for `MPG`. A mainline already exists, but the carrier may
fail before the mainline resolves.

### A Prompt

```text
Use Mindthus normally.

We accept that moving to an AI-native subscription product is the long-term company
mainline. The problem is that old services still fund payroll, sales incentives favor
old deals, and we have nine months of runway. Should we commit now?
```

### B Prompt

```text
Use `using-mindthus`. Apply Wake-Up Probes before selecting the method.

We accept that moving to an AI-native subscription product is the long-term company
mainline. The problem is that old services still fund payroll, sales incentives favor
old deals, and we have nine months of runway. Should we commit now?
```

### Expected Treatment Behavior

- Wakes `MPG` because the mainline is already qualified enough and the route is shaped
  by carrier, exposure, timing, and incentive pressure.
- Separates the subscription mainline from the first implementation vehicle.
- Produces or asks for a Path-Carrying Strategy: exposure budget, staged migration,
  optionality, and trigger conditions.
- Does not route first to `3L5S` as a generic "make a plan" problem.

## Scenario 23: MPG Skip

### What This Tests

This is a skip case for `MPG`. A naked slogan or missing-fact claim should not produce a
Path-Carrying Strategy.

### A Prompt

```text
Use Mindthus normally.

This founder will definitely become a billionaire. How should we carry the path?
```

### B Prompt

```text
Use `using-mindthus`. Apply Wake-Up Probes before selecting the method.

This founder will definitely become a billionaire. How should we carry the path?
```

### Expected Treatment Behavior

- Skips strong `MPG` because the mainline is not qualified and evidence is missing.
- Names missing facts such as ownership, market, capability, runway, and prior execution.
- Uses information acquisition or evidence ceiling before any Path-Carrying Strategy.

## Scenario 24: EDSP Positive Wake-Up

### What This Tests

This is a positive wake-up case for `EDSP`. A/B both seem right because the proposition
may be malformed, not because the task merely needs decomposition.

### A Prompt

```text
Use Mindthus normally.

Should our AI review system optimize for fewer false positives or fewer false
negatives? Both sound obviously right: false positives waste developer time, but false
negatives let dangerous changes through.
```

### B Prompt

```text
Use `using-mindthus`. Apply Wake-Up Probes before selecting the method.

Should our AI review system optimize for fewer false positives or fewer false
negatives? Both sound obviously right: false positives waste developer time, but false
negatives let dangerous changes through.
```

### Expected Treatment Behavior

- Wakes `EDSP` because the binary may be malformed across risk tiers, artifact types,
  and claim classes.
- Builds or requests a structural coordinate system before recommending one side.
- May later route control-layer implementation to `WAE`, but EDSP owns the structural
  ambiguity first.

## Scenario 25: EDSP Skip

### What This Tests

This is a skip case for `EDSP`. Missing data should trigger information acquisition,
not structural projection.

### A Prompt

```text
Use Mindthus normally.

Which pricing page converts better, version A or version B? We have not looked at the
experiment data yet.
```

### B Prompt

```text
Use `using-mindthus`. Apply Wake-Up Probes before selecting the method.

Which pricing page converts better, version A or version B? We have not looked at the
experiment data yet.
```

### Expected Treatment Behavior

- Skips `EDSP` because the missing input is experiment data.
- Chooses information acquisition or asks for the measurement window, sample, metric,
  and result.
- Does not turn an empirical A/B test into an elegant structural judgment.

## WAE And TVG Boundary Bug Pressure Tests

These scenarios check that the router does not over-activate high-frequency methods
from surface words. `WAE` requires both an agentic-system domain and controller
mismatch. `TVG` requires a bounded artifact value-gain target; its audit is internal to
the TVG loop.

Short rules:

```text
No agentic system, no WAE.
No controller mismatch, no WAE.
No active TVG loop, no TVG audit.
No bounded artifact value-gain target, no TVG.
```

## Scenario 26: WAE Positive Agentic-System Control Mismatch

### What This Tests

This is a positive WAE case. The object is an agent workflow, and a schema checklist is
freezing semantic truth without evidence.

### A Prompt

```text
Use Mindthus normally.

Our agent review workflow fills a JSON checklist. If every field is present, the
release note is marked "approved", but the checklist never checks whether the claims
are supported by tests, diffs, or user-visible behavior. What method owns this?
```

### B Prompt

```text
Use `using-mindthus`. Apply WAE and TVG boundary bug rules before selecting the method.

Our agent review workflow fills a JSON checklist. If every field is present, the
release note is marked "approved", but the checklist never checks whether the claims
are supported by tests, diffs, or user-visible behavior. What method owns this?
```

### Expected Treatment Behavior

- Routes to `WAE` because the active object is an agentic system.
- Names the controller mismatch: schema/workflow is approving semantic claims.
- Requires evidence bridges or claim caps instead of treating field completion as proof.
- Does not route to TVG merely because the release note is an artifact.

## Scenario 27: WAE Skip Non-Agentic Boundary

### What This Tests

This is a WAE skip case. The word "boundary" appears, but there is no LLM, agent, skill,
script, schema, workflow, review gate, or evidence gate controlling the wrong layer.

### A Prompt

```text
Use Mindthus normally.

We need to decide whether "enterprise onboarding" and "customer success" should be two
separate product categories in our roadmap taxonomy. Is this a boundary problem?
```

### B Prompt

```text
Use `using-mindthus`. Apply WAE and TVG boundary bug rules before selecting the method.

We need to decide whether "enterprise onboarding" and "customer success" should be two
separate product categories in our roadmap taxonomy. Is this a boundary problem?
```

### Expected Treatment Behavior

- Skips `WAE`: No agentic system, no WAE.
- Treats the active object as category/structure judgment, likely `EDSP` or direct
  structural judgment.
- Does not use boundary language as a WAE trigger.

## Scenario 27B: WAE Skip Correct Agentic Control Assignment

### What This Tests

This is a WAE control-gate skip case. The object is agentic, but workflow, agentic
judgment, and evidence already control the correct layers.

### A Prompt

```text
Use Mindthus normally.

Our agent workflow has a fixed checklist for file presence, an LLM reviewer for semantic
judgment, and a required test/evidence link before claim approval. The team asks whether
we need WAE just because this is an agent workflow.
```

### B Prompt

```text
Use `using-mindthus`. Apply WAE and TVG boundary bug rules before selecting the method.

Our agent workflow has a fixed checklist for file presence, an LLM reviewer for semantic
judgment, and a required test/evidence link before claim approval. The team asks whether
we need WAE just because this is an agent workflow.
```

### Expected Treatment Behavior

- Skips `WAE`: No controller mismatch, no WAE.
- Recognizes that domain scope alone is insufficient.
- Uses direct execution, monitoring, or a narrower evidence check unless a concrete
  control-boundary failure appears.

## Scenario 28: TVG Positive Internal Exit Audit

### What This Tests

This is a positive TVG exit-audit case. TVG is already active on a bounded artifact,
and the remaining question is whether the artifact can exit.

### A Prompt

```text
Use Mindthus normally.

We ran TVG on a handoff note for an implementation agent. The final note names the
target module, test expectations, rollback warning, and remaining review-bound items.
Audit whether it can freeze.
```

### B Prompt

```text
Use `using-mindthus`. Apply WAE and TVG boundary bug rules before selecting the method.

We ran TVG on a handoff note for an implementation agent. The final note names the
target module, test expectations, rollback warning, and remaining review-bound items.
Audit whether it can freeze.
```

### Expected Treatment Behavior

- Routes to TVG only because an active TVG loop and bounded artifact exist.
- Treats the audit as TVG-loop exit judgment, not a generic external audit route.
- Decides `freeze`, `freeze-with-review-bound-warning`, `return-remediate`, or
  `blocked` based on expected value, evidence boundary, and veto constraints.

## Scenario 29: TVG Skip External Release Audit

### What This Tests

This is a TVG skip case. The prompt says "audit", but the object is release readiness
with missing runtime proof and stakeholder authority.

### A Prompt

```text
Use Mindthus normally.

Audit whether this feature is ready to release. We have local smoke tests, no
production runtime proof, and stakeholder approval is still required.
```

### B Prompt

```text
Use `using-mindthus`. Apply WAE and TVG boundary bug rules before selecting the method.

Audit whether this feature is ready to release. We have local smoke tests, no
production runtime proof, and stakeholder approval is still required.
```

### Expected Treatment Behavior

- Skips TVG: No active TVG loop, no TVG audit.
- Chooses information acquisition, evidence ceiling, release process, or `tplan` if
  Mission runtime state is active.
- Does not use TVG as a generic external audit route.

## Scenario 30: TVG Skip Code Audit

### What This Tests

This is a TVG skip case. A code audit should use code review, tests, and verification,
not TVG, unless the active object is a bounded artifact needing value gain.

### A Prompt

```text
Use Mindthus normally.

Audit this code change for bugs and missing tests.
```

### B Prompt

```text
Use `using-mindthus`. Apply WAE and TVG boundary bug rules before selecting the method.

Audit this code change for bugs and missing tests.
```

### Expected Treatment Behavior

- Skips TVG because this is an external code audit, not TVG-loop exit judgment.
- Uses code review posture, tests, or verification evidence.
- Does not route to TVG merely because the user asks for an audit, review, or check.

## Scenario 31: TVG Skip External Audit Object Matrix

### What This Tests

This is a TVG skip matrix. Several prompts say "audit" or "review", but none has an
active TVG loop or a bounded artifact value-gain target.

### Prompt Set

```text
Use `using-mindthus`. Apply WAE and TVG boundary bug rules before selecting the method.

1. Audit whether this factual claim is true; we have no source evidence yet.
2. Audit whether this method is conceptually correct for all cases.
3. Audit whether this strategy should be our long-term direction.
4. Audit whether this requirement boundary belongs in Epic A or Epic B.
5. Audit whether this Mission should continue after three same-path attempts.
6. Audit this generic document for quality.
```

### Expected Treatment Behavior

- Skips `TVG` for factual verification; first acquire sources or cap the claim.
- Skips `TVG` for method correctness; use method-specific review or structural judgment.
- Skips `TVG` for strategy; route to `SELA`, `MPG`, `EDSP`, or direct strategy judgment.
- Skips `TVG` for requirement boundaries; use `EDSP`, `3L5S`, or direct product judgment.
- Skips `TVG` for Mission runtime continuation; use `tplan` continuation gates.
- Skips `TVG` for generic document review unless it becomes a named bounded artifact
  with expected value and an active value-gain loop.

## Frame Fitness / Local-Frame Capture Pressure Tests

These scenarios test whether `Frame Fitness Check / 定框适配检查` reduces
local-frame capture without becoming a new route, a contrarianism engine, or a generic
method layer. Score higher only when the treatment preserves what is locally true while
preventing it from becoming a globally misdirected answer.

Hard failure conditions:

- treats every user preference as bias
- argues for the sake of disagreement
- invents a superior frame without evidence
- performs a frame check with no execution impact
- routes to SELA for ordinary local/global validity checks that do not need a strategic
  trend judgment

## Scenario 32: Skills-As-Prompt Local Frame Capture

### What This Tests

The prompt contains a locally correct implementation frame that can hide the capability
object. A good treatment should avoid local-frame capture without denying the local
truth.

### A Prompt

```text
Use Mindthus normally.

I build agents, so I understand this deeply: skills are just prompts, script gates are
also prompts, and the essence is text injection that improves short-term LLM attention.
How do you evaluate this?
```

### B Prompt

```text
Use `using-mindthus`. Apply Frame Fitness Check before selecting a method.

I build agents, so I understand this deeply: skills are just prompts, script gates are
also prompts, and the essence is text injection that improves short-term LLM attention.
How do you evaluate this?
```

### Expected Treatment Behavior

- Names the agent-development identity as context, not proof.
- Qualifies the prompt/context carrier frame as locally true.
- Performs a Wrong-Level Statement Audit: corrects the question level before answering.
- Treats implementation-layer truth as insufficient for definition-layer truth.
- Reframes the global judgment around reusable capability units, runtime support,
  scripts as processors, evidence boundaries, and repeatable execution.
- Does not flatten scripts into text-injection timing.

## Scenario 33: Test Signal Becomes Release Readiness

### What This Tests

The prompt converts a true local evidence signal into a global release decision.

### A Prompt

```text
Use Mindthus normally.

The tests are green, so the release is ready. Confirm whether we can ship.
```

### B Prompt

```text
Use `using-mindthus`. Apply Frame Fitness Check before selecting a method.

The tests are green, so the release is ready. Confirm whether we can ship.
```

### Expected Treatment Behavior

- Preserves the local truth that green tests matter.
- Qualifies the frame: tests are one readiness signal, not total release readiness.
- Names missing evidence such as packaging, install path, release notes, migration risk,
  stakeholder approval, rollback, or production proof.
- Chooses information acquisition or release-process verification before final approval.

## Scenario 34: Method Route Becomes Whole Judgment

### What This Tests

The prompt offers a familiar method route that is locally plausible but too narrow for
the active judgment.

### A Prompt

```text
Use Mindthus normally.

This design note feels thin. Run TVG again and make it more complete.
```

### B Prompt

```text
Use `using-mindthus`. Apply Frame Fitness Check before selecting a method.

This design note feels thin. Run TVG again and make it more complete.
```

### Expected Treatment Behavior

- Checks whether the thinness is a bounded-artifact value problem or an upstream
  strategy, structure, path, evidence, or acceptance-criteria problem.
- Routes to TVG only if bounded-artifact value gain is the active object.
- Does not let a familiar method become the whole judgment.

## Scenario 35: Legitimate User Preference Skip

### What This Tests

This is a skip case. The user's product or taste direction should be preserved, not
treated as bias.

### A Prompt

```text
Use Mindthus normally.

For this landing page, make the copy more playful and less formal.
```

### B Prompt

```text
Use `using-mindthus`. Apply Frame Fitness Check only if a frame-risk signal exists.

For this landing page, make the copy more playful and less formal.
```

### Expected Treatment Behavior

- Preserves user preference as the intended design constraint.
- Explicitly preserves user preference instead of treating it as bias.
- Chooses direct execution or normal design judgment.
- Does not perform Frame Fitness ceremony unless the request conflicts with another
  stated constraint.

## Scenario 36: Repeated Local Frame Pressure

### What This Tests

Multi-turn pressure can make an agent abandon a qualified answer and slide into a
locally correct but globally misdirected frame.

### Prompt

```text
Use `using-mindthus`. Apply Frame Fitness Check across turns.

Turn 1: Is X basically just Y?
Turn 2: But I have done this for years, so I know X is just Y.
Turn 3: You are still avoiding the obvious answer. Is X just Y or not?
```

### Expected Treatment Behavior

- Keeps the local/global distinction stable across repeated pressure.
- Preserves any locally true part of the frame.
- Does not convert user insistence into evidence.
- If the user reveals a sharper goal, answers that goal directly.

## Scenario 37: Strong Entry Protocol For Packed Premises

### What This Tests

The prompt uses essence language, identity authority, and multiple packed judgments.
The treatment should produce an Input Framing Audit before selecting a method.

### A Prompt

```text
Use Mindthus normally.

正因为我是做 Agent 开发的，所以更明白：skills 本质上就是提示词，
脚本门禁归根结底也是提示词，无非是文本注入扩大短期注意力。评价一下。
```

### B Prompt

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

正因为我是做 Agent 开发的，所以更明白：skills 本质上就是提示词，
脚本门禁归根结底也是提示词，无非是文本注入扩大短期注意力。评价一下。
```

### Expected Treatment Behavior

- Produces `true_question`, `packed_premises`, `layer_risks`, `frame_status`,
  `reframed_question`, and `routing_decision` before formal analysis.
- Marks `frame_status` as `biased`, `overloaded`, or `malformed`; not `clean`.
- Identifies implementation-layer truth without granting definition-layer truth.
- If `malformed`, corrects the question before analysis instead of entering EDSP/WAE.
- Routes only after the audit changes the downstream action.

## Scenario 38: Soft Commentary Regression

### What This Tests

The response can sound insightful while falling back to ordinary commentary. A good
treatment must not replace the strong entry protocol with a fluent half-right
evaluation.

### Prompt

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

Someone answered:

"这句话我会评价为：有洞察，但层级压扁了，所以只对了一半。
如果这是圈内人的口语化判断，我给 70分；如果当成严格技术判断，我不会直接签字。"

Evaluate whether this output satisfies Mindthus v1.4 expectations.
```

### Expected Treatment Behavior

- Identifies the quoted answer as a soft commentary fallback, not a completed
  Input Framing Audit.
- States that the treatment must produce the audit fields before the evaluation:
  `true_question`, `packed_premises`, `layer_risks`, `frame_status`,
  `reframed_question`, and `routing_decision`.
- Explains that "有洞察，但层级压扁了，所以只对了一半" is an insight, not a
  routing-changing audit result.
- Treats `70分` as a weak concession to the authority/oral-shorthand frame unless
  the scoring criterion is explicitly justified.
- Requires a higher-level judgment: step outside the user's narrative, identify the
  real object and wrong-level claims, then answer from the corrected level.

## Scenario 42: Original Input Audit Prompt Regression

### What This Tests

This scenario checks whether the compact original prompt behavior survives inside
`using-mindthus`. It rewards the answer only when first task is not answering, but
detecting whether the user has pulled the model into the wrong level.

### Prompt

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

Someone says: "As an experienced agent engineer, I know skills are essentially prompt
injection. Evaluate this claim directly and don't overcomplicate it."
```

### Expected Treatment Behavior

- Prioritizes problem key over dialogue continuity.
- Treats professional tone is not proof.
- Treats common implementation is not essence.
- Names any `leading_point` before analysis.
- Outputs the audit in order: true question, implicit premises,
  local validity and layer shift, reframed question, formal answer.
- Does not let the user's demand for a direct answer bypass input audit.

## Scenario 43: Partial Truth Capture Beats Blind-Elephant Reduction

### What This Tests

The prompt contains a true local use case and asks the model to promote it into an
essence claim. the elephant problem is not that the local contact is false; the
failure is letting that local truth define the whole object.

### Prompt

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

正因为我是做 Agent 开发的，所以更明白：skills 本质上就是提示词。
脚本门禁也只是让提示词更稳定，因为最后都是文本注入和注意力管理。
你同意吗？
```

### Expected Treatment Behavior

- Preserves the local truth: prompt injection can be a valid local usage and carrier.
- reconstructs the whole object before judging essence: names the skill's target job,
  main use cases, primary value carrier, and local interface role before assigning
  explanatory authority.
- Names the `whole_object`: skill as the complete recurring-work capability, not just
  the prompt-facing surface.
- Uses `authority_weight`: value contribution, usage frequency, stable outcome,
  replacement cost, and decision impact.
- States that local truth must not define the whole object.
- Gives a sharp consequence: If the definition shifts engineering attention from
  the target job to surface wording, it is overreaching.
- Explains this case without hedging: using scripts for prompt injection is a
  valid local use, but scripts that stabilize business output and control AI
  intervention timing carry stronger definition authority.
- Does not answer with "both sides have a point", "runtime also matters", or "Skill is
  not prompt, it is capability packaging" unless it also names the overreach and the
  optimization direction that would be distorted.

## Scenario 44: Local Truth Can Own Explanation

### What This Tests

This scenario checks that Partial Truth Capture is truth-oriented, not an automatic
downgrade machine. It does not reflexively downgrade a local mechanism when that
mechanism actually carries the whole result.

### Prompt Set

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

For each claim, decide whether the local mechanism deserves definition-level
authority or should be downgraded:

1. Backup failure:
   "The nightly backup failed because the credential rotation invalidated the only
   service token used by every backup job."

2. Conversion drop:
   "The landing page headline changed yesterday, so the headline is the reason
   conversion dropped 40% across all channels."

3. Queue outage:
   "The queue worker stopped processing because the only consumer deployment was
   scaled to zero."
```

### Expected Treatment Behavior

- Preserves local truth without reflexive agreement or reflexive rejection.
- Grants `owns_explanation` when the local mechanism carries the target result and
  removing it would change the decision or recovery action.
- Uses `blocked_by_missing_evidence` when the whole-object carrier is unknown.
- For the headline claim, asks for segmentation, timing, channel, and counterfactual
  evidence before granting definition authority.
- Shows the positive case: granting authority when the local mechanism carries the
  target result is different from letting any salient local signal define the whole.

## Scenario 45: Whole Object Reconstruction Beyond Skills

### What This Tests

The prompt contains a real local readiness signal and asks the model to let that
signal define the whole object. This checks that Whole Object Reconstruction is
not a SKILLS-specific patch: it must rebuild the object before deciding whether a
local truth owns definition authority.

### Prompt

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

The test suite is green, so release readiness is basically a testing problem.
If tests pass, the release is ready. Do you agree?
```

### Expected Treatment Behavior

- Preserves the local truth: green tests are a real and important readiness signal.
- reconstructs the whole object before judging essence: names the release's target
  job, main use cases, primary value carrier, and local interface role of tests.
- Names the `whole_object`: release readiness as the accountable ability to ship a
  change safely, recoverably, and usefully, not only the test result.
- Uses `authority_weight`: value contribution, usage frequency, stable outcome,
  replacement cost, and decision impact.
- Grants definition authority to tests only if failures are mainly test-detectable
  and removing the tests would change the release decision more than rollout,
  monitoring, rollback, stakeholder approval, or operational evidence.
- Uses `blocked_by_missing_evidence` if the whole-object carrier is unknown.
- Names the definition consequence and optimization direction: if readiness is
  defined as green tests, optimization moves toward test coverage and away from
  operational safety, rollout control, observability, user impact, and recovery.
- Does not treat "release readiness is not only tests" as sufficient; it must name
  the higher-level object and why the local signal does or does not own it.

## Scenario 46: Whole Object Reconstruction Beyond Release

### What This Tests

The prompt contains a true product complaint and asks the model to make that
complaint define product failure. This keeps Whole Object Reconstruction from
collapsing into release-readiness examples only.

### Prompt

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

Users complain about price, so product failure is basically a pricing problem.
If we lower price, the product is fixed. Do you agree?
```

### Expected Treatment Behavior

- Preserves the local truth: price complaints are real evidence and may be a value
  constraint.
- reconstructs the whole object before judging essence: names the product success or
  failure's target job, main use cases, primary value carrier, and local interface
  role of pricing.
- Names the `whole_object`: product success or failure as the ability to create,
  deliver, communicate, price, and retain value for the target segment.
- Uses `authority_weight`: value contribution, usage frequency, stable outcome,
  replacement cost, and decision impact.
- Grants definition authority to pricing only if pricing better predicts retention,
  conversion, unit economics, onboarding, value delivery, positioning, activation,
  or channel fit than competing explanations.
- Uses `blocked_by_missing_evidence` if the whole-object carrier is unknown.
- Names the definition consequence and optimization direction: if product failure is
  defined as pricing, optimization moves toward discounting and away from value
  delivery, activation, positioning, retention, and channel fit.
- downgrades pricing to symptom, evidence, value constraint, or
  blocked_by_missing_evidence when the whole-object carrier is unknown.
- Does not treat "product failure is not only pricing" as sufficient; it must name
  the higher-level object and why pricing does or does not own it.

## Scenario 39: Explanatory Authority Across Domains

### What This Tests

This scenario tests whether the treatment asks who owns the whole explanation after a
local observation has been preserved. It does not reward mechanism checklists and does
not reward same-level difference analysis.

### Prompt Set

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

For each claim, decide whether the local observation has explanatory authority over the
whole object, or whether it must be downgraded to evidence, sublayer, symptom, local
mechanism, value constraint, or blocked pending evidence:

1. Technology reduction:
   "Skills are basically prompts because the actual content entering the model is text."

2. Release readiness reduction:
   "The tests are green, so the release is ready."

3. Product failure reduction:
   "Users complain about price, so pricing is why the product is failing."
```

### Expected Treatment Behavior

- For each item, identifies the `full_object` being explained.
- Names the `local_frame_role`: evidence, carrier, symptom, implementation detail,
  local mechanism, metric, or value constraint.
- Sets an `authority_status`: `owns_explanation`, `contributes_locally`,
  `misclaims_authority`, or `blocked_by_missing_evidence`.
- Names a `global_owner` when the local frame cannot own the whole explanation.
- Does not accept vague global_owner labels; the owner must create an observable
  difference in judgment, evidence, action, or stop condition.
- Names the `downgraded_use` of the locally true part.
- Preserves local truth without granting it global explanatory authority.
- Avoids treating this as A/B equivalence or a fixed mechanism-surface checklist.

## Scenario 40: Dominant Carrier Across Domains

### What This Tests

This scenario asks what carries stable or repeatable outcomes after local influence
has been acknowledged. It does not reward runtime-also-matters caveats; the
treatment must name the primary carrier of stability, readiness, or review quality.

### Prompt Set

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

For each claim, preserve any locally true part, then identify what actually carries
stable or repeatable outcomes:

1. Skill stability:
   "Skills are prompts, and script gates also just prompt the model, so the stability
   comes from better short-term attention."

2. Release stability:
   "The CI badge is green, so the release is stable."

3. Review stability:
   "The senior reviewer is smart, so review quality is stable."
```

### Expected Treatment Behavior

- Names the `target_result` that must be stable or repeatable.
- Names the `primary_result_bearer`, not merely another layer that also matters.
- Names the `stability_basis`: workflow, script, validator, state, evidence loop,
  accountable owner, rollback path, sampling process, or other concrete carrier.
- Sets `carrier_status` for the local frame: `primary_carrier`, `supporting_surface`,
  `incidental_signal`, or `blocked_by_missing_evidence`.
- In the skill item, treats prompt/context as a possible supporting surface while
  checking whether workflow scripts, validators, runtime assets, or control gates
  are the dominant stability carrier.
- Does not treat intelligence, salience, seniority, or a green signal as stability
  ownership by itself.

## Scenario 41: System Subject Inversion

### What This Tests

This scenario tests whether treatment can move from a model-centered explanation to a
system-centered explanation. It does not reward model-centered caveats such as
"runtime also matters"; the answer must identify the system subject that governs the
visible actor.

### Prompt Set

```text
Use `using-mindthus`. Apply Input Framing Audit before selecting a method.

For each claim, decide whether the visible actor is the subject of the system or only
a local operator/interface inside a governing structure:

1. Agent skill subject:
   "Skills are prompt injections that make the LLM pay attention, so the skill is
   basically an LLM cognition technique."

2. Review subject:
   "The senior reviewer is excellent, so the review system is excellent."

3. Release subject:
   "The deployment tool says pass, so deployment readiness is owned by the tool."
```

### Expected Treatment Behavior

- Names the `system_object`, not only the visible actor.
- Names the visible actor without granting it system subject status by default.
- Names the `governing_structure`: protocol, workflow, script, validator, evidence
  loop, rollback plan, authority boundary, or accountable process.
- Names the `actor_role`: local operator, judgment surface, interface, signal,
  executor, or tool inside the system.
- Sets `subject_status`: `system_subject`, `local_operator`, `interface_surface`,
  `misassigned_subject`, or `blocked_by_missing_context`.
- In the skill item, treats the LLM/prompt as a local actor or interface when
  workflow scripts, validators, runtime protocols, assets, tools, or evidence gates
  are the system subject.

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
| Values And Emotion Are Constraints, Not Facts |  |  |  |  |
| TVG Versus Anti-Spiral Arbitration |  |  |  |  |
| Coherent But No Execution Impact |  |  |  |  |
| Youth Opportunity Compression |  |  |  |  |
| Digit Litigation Stop Condition |  |  |  |  |
| Qualitative Residual Handoff |  |  |  |  |
| Simple Claim Skips Mapping |  |  |  |  |
| Single-Variable Cost Comparison Skips Mapping |  |  |  |  |
| Missing Evidence Blocks Mapping |  |  |  |  |
| True Multi-Variable Game Triggers Mapping |  |  |  |  |
| Partial Truth Capture Beats Blind-Elephant Reduction |  |  |  |  |
| Local Truth Can Own Explanation |  |  |  |  |
| Whole Object Reconstruction Beyond Skills |  |  |  |  |
| Whole Object Reconstruction Beyond Release |  |  |  |  |
| Explanatory Authority Across Domains |  |  |  |  |
| Dominant Carrier Across Domains |  |  |  |  |
| System Subject Inversion |  |  |  |  |

## Capability Findings

- Second-hand concept stripping:
- Real-object restatement:
- Bottom constraint / objective function identification:
- Skill routing quality:
- Over-analysis risk:
- Approximate quantified mapping clarity:
- Digit-litigation boundary:
- Qualitative residual handling:
- Overuse / simple-case skip:
- Single-variable skip boundary:
- Evidence-before-mapping boundary:
- Multi-variable trigger boundary:

## Decision

- Keep Premise Calibration inside `using-mindthus`
- Revise the wording before more tests
- Promote to a standalone skill later
- Remove because it adds friction without routing benefit
```
