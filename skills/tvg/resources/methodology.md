# Thinking Value-Gain Methodology — Value-Oriented Deep Thinking（v0.2）

## Purpose

This document defines a standalone, project-portable methodology for value-oriented deep thinking on bounded modules.

It increases a module's practical thinking value without letting the work drift into shallow completion, random brainstorming, overfitting, or endless refinement.

Depth is the means. Practical value gain is the target. Positive-value exit is the stopping rule.

Its primary positioning is universal: it should help different projects solve the recurring AI-work problem where an AI can construct a module, section, artifact unit, plan, design, review, or reasoning block that looks structurally complete but lacks sufficient thinking value for real use.

It is designed for AI work, knowledge work, product thinking, engineering design, methodology writing, review work, and any situation where a module may look structurally complete while still being shallow in judgment.

This is not a method for making modules thicker.

It is a method for forcing deeper thinking while keeping that thinking aimed at practical value.

Core problem:

> A module can exist, be well-structured, and look complete, but still fail because it has not created enough practical value for decision, action, review, reuse, or handoff.

The most dangerous false positive is an automation- or template-controlled demo artifact: it fully satisfies the template, has excellent structure, and looks review-ready, but still lacks real value-bearing judgment.

Core goal:

> Move a module from `structure exists` to `value is increased`: judgment becomes more usable, trade-offs become clearer, evidence becomes more honest, and downstream use no longer requires inventing critical truth.

## Standalone Positioning

This method is standalone and transferable across projects.

It is an execution-layer method for bounded thinking units, not a top-level strategy lens.

It should not decide whole-project direction, replace domain judgment, or override a larger workflow's source-of-truth rules.

Its core concepts must stay generic enough to apply across business reasoning, product design, engineering design, knowledge work, review work, and methodology writing.

It does not require any project-local framework as a dependency.

Internally, it uses a generic three-layer value-gain control mechanism:

> `Control Layer + Thinking Layer + Evidence / Exit Layer`

- `Control Layer` keeps the loop bounded and prevents random drift.
- `Thinking Layer` performs value-oriented reasoning, comparison, pressure testing, and rewrite.
- `Evidence / Exit Layer` audits whether the module gained enough practical value to freeze, return, or block.

A project may map these layers to its own workflow, agent, review, or governance model, but that mapping belongs outside this standalone method.

## Design Origin

This method generalizes a repeated pattern from practical AI-assisted work:

- define exit quality before deepening begins
- use a fixed outer control shell so loops do not drift
- let reasoning deepen truth, alternatives, trade-offs, and anti-demo pressure
- preserve evidence, uncertainty, and review-bound items
- freeze only when another round is unlikely to create meaningful positive value

The generalized version is not tied to any lifecycle phase, project, domain, or named case.

Any future extension, example, or reusable pattern must preserve this portability. If a useful detail only works inside one project, domain, or remembered case, keep it as an example rather than a core rule.

## When To Use / When Not To Use

### Use When

Use this method when a module is:

- structurally present but intellectually thin
- complete-looking but generic
- correct in format but weak in judgment
- missing alternatives, trade-offs, or why-this-not-that rationale
- missing realistic scenarios, edge cases, constraints, or failure paths
- forcing downstream users to invent critical truth
- likely to be reused, handed off, reviewed, or turned into a decision basis

Typical module types:

- methodology modules
- product/business modules
- architecture or design modules
- engineering implementation modules
- test or evidence modules
- review and release-judgment modules
- prompt, skill, or workflow modules

### Do Not Use It To

Do not use this method to:

- make text longer without improving decision value
- add ornamental structure
- reopen the whole problem space after a good-enough answer exists
- hide missing evidence behind confident prose
- tune a module only for one remembered case while weakening generality
- continue deepening after positive return has clearly flattened

### Trigger Question

> `Is this module merely complete, or is it deep enough to be used, challenged, and handed off?`

## Core Claim

The goal is value gain, not thickness for its own sake.

Depth is only useful when it increases the module's ability to support decisions, action, review, reuse, or downstream handoff.

A module gains thinking value when it has enough of the following:

- real constraints
- concrete scenarios
- meaningful alternatives
- explicit trade-offs
- boundary conditions
- failure paths
- evidence and uncertainty separation
- downstream usability
- exit reasoning

Short rule:

> `Complete is not enough. Value-added enough is the handoff threshold.`

Anti-demo rule:

> `A perfect template can still be a low-value demo if it does not improve judgment, action, evidence honesty, or downstream use.`

## Value-Gain Governance Layer

Because this method is intended to be portable, value gain must be governed before concrete patterns are applied.

The governance layer has three jobs:

1. classify what kind of value the module needs
2. require an agentic exit audit rather than format-only approval
3. control how concrete patterns are admitted so they do not reduce generality

### Value-Gain Types

Use these types to clarify what `value` means for the current module. Select only the types that matter.

| Type | Core Question | Typical Improvement |
|---|---|---|
| `decision-value` | Does the module help someone choose better? | decision states, trade-offs, why-this-not-that |
| `evidence-value` | Does it make claims more honest? | evidence boundary, assumptions, review-bound items |
| `handoff-value` | Does it reduce downstream invention? | clearer contract, constraints, accepted unknowns |
| `risk-reduction-value` | Does it reduce false green, demo risk, or misuse? | failure paths, anti-demo findings, misuse warnings |
| `reuse-value` | Does it improve a reusable class without overfitting? | generalized axes, pattern boundaries |
| `execution-value` | Does it make action more executable? | next action, owner, validation path, exit state |

If the module's value type cannot be named, do not start by adding detail. First clarify what value the module is supposed to create.

### Agentic Exit Audit Contract

A value-gain run should leave an agentic exit audit when the module is high-impact, high-uncertainty, or handoff-critical.

Minimum audit structure:

- `target_module`
- `claimed_value_gain`
- `value_gain_type`
- `evidence_support`
- `remaining_review_bound`
- `disagreements`
- `demo_false_positive_risk`
- `overfitting_risk`
- `downstream_usability`
- `exit_state`
- `why_not_another_round`

This audit can be lightweight, but it must be judgment-bearing. It cannot be replaced by a script pass or template check.

### Pattern Admission Levels

Concrete patterns must earn their place.

| Level | Meaning | Placement |
|---|---|---|
| `example-only` | useful in one case, not yet generalized | example file only |
| `candidate-pattern` | plausible across a class, lightly tested | pattern library with strong boundaries |
| `reusable-pattern` | useful across multiple module types or scenarios | pattern library |
| `core-rule` | required by almost every module for value safety | core checklist only after strong evidence |

Default stance:

> new concrete patterns start as `example-only` or `candidate-pattern`, not as core rules.

Current pattern status:

> Concrete patterns in this method should be treated as `example-only` or `candidate-pattern` unless they have explicit cross-context evidence. Do not treat a candidate pattern as a stable reusable rule merely because it appears in the pattern library.

## Step 1: Define Exit Quality First

Before working on a module, define what value increase would be good enough to exit.

Ask:

1. What is this module responsible for?
2. Who or what consumes it downstream?
3. What decision, action, implementation, or review should it enable?
4. What must not be left for downstream users to invent?
5. What remaining uncertainty can be explicitly carried as review-bound?
6. What would make this module look complete but still fail?

The exit gate should be defined before the loop starts. Otherwise the work becomes subjective and can continue forever.

### Exit Gate Template

A module may exit only when:

- its role and downstream consumer are explicit
- critical truths needed by downstream users are not missing
- key alternatives or trade-offs have been considered when material
- core scenarios or use paths are no longer title-level
- important constraints and failure modes are visible
- evidence-backed claims are separated from assumptions
- unresolved uncertainty is explicitly review-bound
- another round is unlikely to create meaningful positive value
- exit readiness has been checked by agentic judgment, not only by script or template audit

## Step 2: Choose Value-Gain Axes

Do not improve everything equally.

Select the few axes that matter for this module.

### Common Value-Gain Axes

| Axis | Value-Gain Question | Low-Value Signal |
|---|---|---|
| `role-depth` | What job does this module perform in the larger system? | module is descriptive but not useful |
| `scenario-depth` | Which concrete scenarios, paths, states, and exceptions matter? | only happy-path or title-level examples exist |
| `judgment-depth` | What alternatives were compared, and why this one? | conclusion appears without reasoning |
| `constraint-depth` | What real-world, technical, business, operational, or social constraints bind the answer? | answer feels context-free |
| `evidence-depth` | What is proven, inferred, assumed, or review-bound? | confidence is not calibrated |
| `boundary-depth` | What is in scope, out of scope, optional, or deferred? | module expands or shrinks arbitrarily |
| `failure-depth` | How could this fail, mislead, or be misused? | no anti-demo or adversarial pressure exists |
| `downstream-depth` | Can the next user act without inventing missing truth? | handoff still requires interpretation |
| `generalization-depth` | Does this improve a reusable class of cases? | one case becomes stronger while generality weakens |
| `anti-demo-depth` | Would this still be valuable if the template and formatting were ignored? | structure looks excellent but decision value is thin |

Use only the axes that create material value gain.

## Step 3: Use Layered Depth Control

A deepening loop needs freedom to think, but also control surfaces to prevent drift.

Use three layers.

### Control Layer

The Control Layer fixes the loop boundaries.

It owns:

- module boundary
- target artifact unit
- value-gain axes selected for this round
- round limit
- state transitions
- required trace record
- exit gate

It prevents:

- random brainstorming
- unbounded exploration
- solving a different problem
- adding structure without value
- automation- or template-controlled demo output that passes format checks but fails value checks

### Thinking Layer

The Thinking Layer performs the actual value-increasing reasoning.

It owns:

- semantic completion
- alternative comparison
- trade-off articulation
- scenario expansion
- exception and failure-path discovery
- anti-demo review
- targeted rewrite
- synthesis into a stronger module

It prevents:

- shallow template filling
- generic summaries
- unsupported conclusions
- structure without judgment

### Evidence / Exit Layer

The Evidence / Exit Layer keeps the module honest.

It owns:

- evidence / assumption separation
- review-bound items
- unresolved uncertainty
- positive-value assessment for another round
- freeze / return / blocked decision
- downstream handoff notes

It prevents:

- confident hallucination
- false completeness
- endless refinement
- over-claiming

### Trace / Working Context Boundary

Trace is an audit/calibration log, not working context.

The working context for a TVG round is the current module, the exit gate, selected
value-gain axes, and any current evidence or assumptions needed for this round. The
trace records only the audit summary of what changed, what value was claimed, what
remains review-bound, and why another round is or is not justified.

Trace must not control flow decisions. It does not decide whether to run another
round, which axis to choose, or whether the module can exit. Those remain agentic
audit decisions.

Do not replay the full trace into later rounds by default. If many rounds exist,
summarize current-round outcome into `value_gain` and `agentic_exit_audit`, then
archive old detail outside the active working context.

## Step 4: Run A Bounded Value-Gain Loop

Default loop:

1. `structured draft`
   - create or identify the module in its current structured form
2. `R1: gap-targeted deepening`
   - address the most important thinness signals
3. `R2: comparison / stress-test deepening`
   - compare alternatives, pressure-test assumptions, expose anti-demo risks
4. `R3: integration deepening`
   - integrate the strongest gains and tighten the module
5. `exit decision`
   - freeze, freeze-with-review-bound-warning, return-remediate, or block

Default limit:

> one structured draft + up to three deepening rounds

A system may allow more rounds only with explicit justification.

### Axis Selection And Conflict Rule

When multiple value-gain axes are possible, do not deepen all of them for completeness.

Prioritize the axis most likely to change:

- decision
- action
- evidence honesty
- handoff usability
- review confidence

If two axes conflict, prefer the one that most changes the module's actual downstream use.

Do not add another axis when it would only increase taxonomy, length, or process weight.

### Valid Round Triggers

A new round is justified only when a named module unit still has one of these problems:

- generic reasoning
- missing alternatives comparison
- weak trade-off explanation
- hidden uncertainty
- missing scenario or failure path
- weak downstream handoff value
- unresolved contradiction worth testing
- evidence / assumption boundary is unclear
- generalization risk has not been checked
- template completeness may be hiding demo-level judgment

Do not continue based on a vague feeling that more thinking would be nice.

### Round Discipline

Each round must record:

- target module unit
- selected value-gain axis or axes
- trigger for the round
- deepening action performed
- what changed
- what downstream usability improved
- why another round is or is not justified

If a round leaves no material value trace, treat it as style polish, not value gain.

## Reusable Value-Gain Patterns

This section is a pattern library, not the core method.

Patterns are optional accelerators discovered from test cases. They must not become mandatory checklist items unless the active module's value mechanism actually matches the pattern.

Pattern admission rule:

- keep a pattern only if it improves a reusable class of modules
- name the value mechanism it serves
- state when not to use it
- keep it subordinate to the exit gate, selected value-gain axes, anti-overfitting review, and agentic exit audit

If a pattern makes one case stronger but narrows the method's portability, keep it as an example outside the core method rather than as a reusable pattern.

### Decision-State Conversion Pattern

Value mechanism:

- converts passive evaluation outputs into action-guiding decision states

Use when:

- a module outputs only a score, ranking, status, or label
- the output looks tidy but does not help users decide what to do next

Decision states should clarify:

- what action follows
- what evidence is required
- what uncertainty remains
- when human judgment may override the mechanical result
- what should remain optional, deferred, or review-bound

Do not use when:

- the module only needs a measurement, not an action decision
- the existing label already maps unambiguously to action
- adding decision states would create governance weight without value gain

### Continuation-Proof Chain Pattern

Value mechanism:

- tests whether claimed usefulness can support adoption, renewal, payment, or continued operational commitment

Use when:

- a product, business, or adoption module claims value
- the module says something is useful but does not explain why continuation would happen

Continuation chain:

> `pain holder → continuation owner → substitute to beat → decision loop → proof artifact → continuation signal`

Do not use when:

- commercial continuation is not the relevant value mechanism
- correctness, safety, runtime proof, or compliance is the real value mechanism
- applying the chain would force business semantics onto a non-business module

## Step 5: Apply Anti-Overfitting Review

Value-gain work can fail by becoming too case-tuned.

Before exit, ask:

1. Did we make only one remembered case stronger?
2. Did the module lose generality while gaining local detail?
3. Did we add special-case branches that should be reusable axes instead?
4. Did we mistake realistic detail for reusable insight?
5. Did we increase operator burden beyond the value gained?
6. Did we preserve the narrow excellence as an optional lane when it should not become mainline?
7. If the formatting and template were removed, would the module still create decision, action, evidence, or handoff value?

A module is overfit when:

- it works impressively for the example that inspired it
- but becomes harder to apply to the broader class of cases it claims to serve

## Step 6: Exit Honestly

The loop must end in one of four states.

### `freeze`

Use when:

- the exit gate is met
- unresolved uncertainty is not material to current use
- another round is unlikely to create meaningful positive value

### `freeze-with-review-bound-warning`

Use when:

- the module is usable
- but specific uncertainties, evidence gaps, or context assumptions must be carried forward

### `return-remediate`

Use when:

- the module has a specific fixable weakness
- another targeted round is likely to create meaningful positive value

### `blocked`

Use when:

- the module cannot honestly deepen without missing evidence, domain input, runtime proof, or stakeholder judgment

### Exit State Calibration

Exit states should be monitored across real usage, not only selected per run.

If `return-remediate` and `blocked` remain unused across a meaningful usage window, audit whether:

- exit thresholds are too lenient
- reviewers are using `freeze-with-review-bound-warning` as a soft-pass default
- samples are biased toward easy freezes
- fixable weaknesses are being carried as warnings instead of being returned for remediation

This is a calibration signal, not an automatic failure.

## Exit Gate Audit Rule

A module must not exit only because an automated check, script audit, schema validation, template check, or structural review passes.

Exit requires agentic gatekeeping: a human or LLM reviewer must judge whether the module creates practical value for its actual use.

The agentic exit audit should ask:

1. Does this module improve decision, action, evidence honesty, review, reuse, or handoff value?
2. Would it still be useful if the template formatting were removed?
3. Are the important trade-offs, uncertainties, and failure paths visible?
4. Are review-bound items honest rather than hidden behind clean structure?
5. Is another round likely to create meaningful positive value, or only more compliant output?

Automated checks may support the audit, but they cannot replace it.

### Optional Exit-Audit Rule: Premature Exit Check

Before accepting `no further positive value`, check whether the exit claim may be false convergence.

Ask three questions:

1. Is this module important to decision, action, evidence, review, reuse, or handoff?
2. Has it received real failure, alternative, evidence, or downstream pressure?
3. Does it still look generic, template-like, under-evidenced, or overclaiming?

If the module is important, insufficiently pressured, and possibly false-complete, run one targeted `Minimum Pressure Pass`.

Choose one pressure:

- `failure pressure`: where would this fail?
- `alternative pressure`: what better, cheaper, or safer path might exist?
- `evidence pressure`: where does the claim exceed evidence?
- `downstream pressure`: what would downstream still need to invent?

Continue only if the pass changes decision, action, evidence, handoff, or review value.

If it only adds length, taxonomy, confidence language, or process weight, stop.

This rule belongs inside exit audit. It is not a default extra loop round.

## Positive Value Exit Rule

Do not ask only:

> `Can we still add more?`

Ask:

> `Would another round create meaningful positive value for the module's actual use?`

Positive value may include:

- clearer decision leverage
- stronger downstream usability
- better evidence honesty
- sharper trade-off reasoning
- more realistic scenario coverage
- reduced false-confidence risk
- improved generalization without overfitting

Stop when another round would mostly add:

- length
- repetition
- ornamental structure
- local case tuning
- operator burden
- complexity without decision gain

### Another-Round Decision Positioning

In standard runs, `another_round_decision` may often resolve to `only_with_new_evidence`.

Its main role is to prevent unsupported extra rounds, not to replace the value-gain audit.

Use it as a guardrail against continuing without a named source of positive value.

## Minimum Trace Record

When this method materially affects a module, record:

- `module_name`
- `module_role`
- `downstream_consumer`
- `exit_gate`
- `selected_value_gain_axes`
- `rounds_run`
- `round_trigger`
- `material_change`
- `alternatives_or_tradeoffs_considered`
- `evidence_or_assumption_boundary`
- `review_bound_items`
- `anti_overfitting_result`
- `exit_state`
- `agentic_exit_audit_result`
- `why_another_round_is_or_is_not_justified`

This record is summary-level. It should not accumulate every draft, prompt, discarded
alternative, or process note. If a run produces verbose round detail, keep the latest
summary in the active trace and archive old detail separately.

### Lightweight Trace Mode

For small or low-risk modules, a lighter trace is acceptable if it still preserves the value-gain decision:

- `target_unit`
- `selected_value_gain_axes`
- `value_gain`
- `review_bound_items`
- `exit_state`
- `agentic_exit_audit_result`

Use the full trace for high-impact, high-uncertainty, or handoff-critical modules.

## Reusable Checklist

Before declaring a module valuable enough, check:

- Is its role clear?
- Is its downstream consumer clear?
- Are the selected value-gain axes explicit?
- Are key scenarios or paths no longer title-level?
- Are alternatives and trade-offs visible where material?
- Are constraints and failure paths visible?
- Are claims separated from assumptions?
- Are review-bound items explicit?
- Has overfitting risk been checked?
- Has automation/template-controlled demo risk been checked?
- Has an agentic exit audit checked value, not only format or script pass?
- Is there a reason to believe another round would or would not create positive value?

## Delivery Translation Rule

TVG is an internal thinking and audit method.

Its method vocabulary should not leak into customer-facing, business-facing, architecture-facing, or implementation-facing deliverables by default.

Terms such as `value-gain`, `exit gate`, `pressure pass`, `anti-demo`, `review-bound`, and `positive-value exit` may be useful in trace records or internal reviews.

Final deliverables should translate those terms into natural business, product, architecture, engineering, or review language.

The final artifact should expose the improved judgment, not the scaffolding used to produce it.

## Known Boundaries And Calibration Notes

This method has real-use evidence, but it still requires calibration.

Known boundaries:

- real use has shown positive effect, especially when a module needs more reviewable intermediate reasoning and stronger downstream handoff
- synthetic examples remain useful for method coverage, but they are not a substitute for real work artifacts
- evidence may be stronger in some domains than others; avoid promoting domain-specific exit habits into universal rules without cross-context proof
- current concrete patterns should not be treated as `reusable-pattern` without explicit cross-context evidence
- review artifacts may converge with run outputs unless disagreements are explicitly recorded
- final delivery language may need translation to remove internal method vocabulary

Calibration rules:

- monitor exit state distribution over time
- treat long-term absence of `return-remediate` or `blocked` as a reason to audit thresholds
- keep candidate patterns subordinate to value mechanism fit
- keep the optional premature-exit pressure rule inside exit audit, not in the main loop

## Relationship To Other Methods

This method can coexist with other methodologies.

It should not require them.

Use it as a bounded-module value deepening and exit-audit method inside a larger project, product, engineering, research, review, or knowledge-work system.

The larger system remains responsible for deciding strategic direction, source-of-truth order, workflow ownership, and final acceptance policy.

This method is responsible only for improving or auditing whether a named module has gained enough practical thinking value to be used, challenged, handed off, or frozen.

Any mapping between this method and a project's local methodology stack should be documented in that project's integration guide, not in this standalone method.

## Anti-Patterns

Do not:

- equate longer output with higher value
- equate structural completeness with readiness
- accept automation- or template-controlled perfection as proof of value
- use script audit as the only exit gate
- open a deepening round without a named module unit
- use the final round to reopen the entire problem space
- hide uncertainty under stronger prose
- use positive-value language to avoid necessary work
- preserve every local insight as a mainline rule
- make the method so heavy that it prevents useful work

## One-Line Summary

> `Set the exit gate first, improve only named module units through bounded rounds, separate control from thinking from evidence/exit, stop when another round no longer creates meaningful positive value, and reject detail that overfits one case while weakening general use.`
