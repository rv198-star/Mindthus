# Thinking Value-Gain Methodology — Value-Oriented Deep Thinking（v0.3）

## Purpose

This document defines a standalone, project-portable methodology for value-oriented deep thinking on bounded modules.

It increases a module's practical thinking value without letting the work drift into shallow completion, random brainstorming, overfitting, or endless refinement.

Depth is the means only when the module is under-thick. Practical value gain is the target. Positive-value exit is the stopping rule.

TVG is not a generic improvement pass and not a thickness-expansion method. Its leverage comes from dynamically deciding whether the current bounded module needs depth formation, grounded insight generation, value refinement, compact strengthening, warning calibration, or honest exit.

Its primary positioning is universal: it should help different projects solve the recurring AI-work problem where an AI can construct a module, section, artifact unit, plan, design, review, or reasoning block that looks structurally complete but lacks sufficient thinking value for real use.

It is designed for AI work, knowledge work, product thinking, engineering design, methodology writing, review work, and any situation where a module may look structurally complete while still being shallow, over-thick, low-density, or weak in judgment.

Core problem:

> A module can exist, be well-structured, and look complete, but still fail because it has not created enough practical value for decision, action, review, reuse, or handoff.

Core relationship:

> Sufficient thinking thickness is the substrate of value. Grounded insight yield is the core output. Value density is the delivery quality.

Core goal:

> Move a module from `structure exists` to `value is increased`: judgment becomes more usable, insights become less obvious and better grounded, trade-offs become clearer, and the final artifact carries more value per unit of reading burden.

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

Sufficient thinking thickness is required because high-value insight rarely appears from thin substrate. But once the module has enough constraints, scenarios, alternatives, trade-offs, evidence boundaries, and failure paths, another expansion round may lower value density rather than improve value.

TVG rounds are state-driven, not action-fixed. Each round first asks what the module currently lacks, then chooses a value-gain action.

Primary loop dimensions:

- `Thinking Thickness`: whether the module has enough thought substrate to support value.
- `Grounded Insight Yield`: whether the module produces non-obvious but anchored insight.
- `Value Density`: whether the artifact carries enough value relative to reading burden.

Short rule:

> `Complete is not enough. Thick is not enough. TVG exits when the module has enough thought substrate, grounded insight, and value density for its actual use.`

Grounded novelty rule:

> `TVG should make the reader think, "I had not seen it that way, but it makes sense." It may stretch beyond current reality, but the stretch must remain anchored enough to be productive speculation rather than unsupported fantasy.`

## Value-Gain Governance Layer

Because this method is intended to be portable, value gain must be governed before concrete patterns are applied.

The governance layer has three jobs:

1. classify what kind of value the module needs
2. name any module-specific veto constraints that value gain must not violate
3. require an agentic exit audit rather than format-only approval
4. separate generator and auditor roles when self-audit would be too weak
5. control how concrete patterns are admitted so they do not reduce generality

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

### Primary Loop Dimensions

Use these dimensions for internal calibration. They guide agentic judgment; they are not numeric scores and must not be computed by scripts.

| Dimension | Core Question | Low Signal | High Signal |
|---|---|---|---|
| `Thinking Thickness` | Has the module gone deep enough to support value? | missing constraints, scenarios, alternatives, trade-offs, failure paths | enough thought substrate exists for insight or refinement |
| `Grounded Insight Yield` | Did the run produce non-obvious but anchored insight? | generic, template-like, merely complete | changes understanding, judgment, framing, or action |
| `Value Density` | Is value concentrated relative to reading burden? | repetition, taxonomy, ornament, low-signal structure | high-signal expression without premature compression |

Do not optimize these dimensions independently. Thickness without insight becomes bloat; insight without grounding becomes fantasy; density without thickness becomes polished thinness.

### Grounded Novelty

A high-value TVG result should often contain grounded novelty: a non-obvious but useful viewpoint that ordinary generation would likely miss.

Grounded novelty requires all three:

- `non-obvious`: not a template answer, common summary, or compliance-shaped restatement
- `grounded`: anchored in real constraints, trends, contradictions, needs, counterexamples, or structural reasoning
- `useful`: changes understanding, judgment, expression, action, trade-off, or next inquiry

This is not novelty for novelty's sake. A surprising sentence with no anchor is not valid value gain.

### Grounded Stretch Levels

TVG may go beyond current reality when doing so reveals a useful possibility. Current reality is often past evidence and may not contain the full truth. The stretch must keep enough anchors to remain productive.

| Level | Meaning | Treatment |
|---|---|---|
| `reality-bound` | stays within current facts and constraints | safe but may be ordinary |
| `plausible-extension` | extends one step from known tensions or trends | useful default stretch zone |
| `productive-speculation` | goes beyond available proof while naming the anchor and assumption | allowed when labeled honestly |
| `free-fantasy` | lacks anchor, reasoning support, or recovery path | reject or return-remediate |

The target is grounded stretch: fresh enough to change perspective, anchored enough to remain believable.

### Late-Stage Warning Checks

`Claim Calibration` and `Handoff Readiness` are late-stage warning checks by default. They should not dominate early internal iteration and are not inside the primary value-gain loop unless the module purpose or risk profile requires it.

`Claim Calibration` warns when a fresh idea is being presented with stronger claim status than it deserves. It usually causes labeling, downgrade, or review-bound notes, not a different main action. It escalates only when factual accuracy, safety, compliance, money, release, or irreversible execution is central.

`Handoff Readiness` is checked near exit or when the module is explicitly for handoff, review, implementation, or reuse. It should not flatten early exploration.

### Veto Constraints

`veto_constraints` are explicit unacceptable states for the current module and intended use.

They are not ordinary value-gain axes, writing preferences, or style guidance. They are constraints that can block exit even when the module has improved on selected value-gain axes.

Use veto constraints to capture:

- claims that must not exceed evidence
- boundaries that must not be blurred
- downstream assumptions that must not be forced on the next user
- risks that must not be hidden by cleaner structure
- unacceptable trade-offs for the current use

Veto constraints must be named before exit audit and, when possible, before deepening begins. If a veto constraint is triggered, the module must not exit as `freeze`. Use `return-remediate` when a targeted fix can remove the violation; use `blocked` when the violation cannot be resolved without missing evidence, domain input, runtime proof, or stakeholder judgment.

Do not turn broad good practice into a veto constraint. A valid veto constraint is specific enough that a reviewer can say what would violate it.

### Agentic Exit Audit Contract

A value-gain run should leave an agentic exit audit when the module is high-impact, high-uncertainty, or handoff-critical.

For low-risk modules, the generator may perform a lightweight audit if it remains honest about review-bound items and veto constraints.

For high-impact, high-uncertainty, or handoff-critical modules, use independent auditor separation:

- `generator` performs the value-gain loop and prepares the final module.
- `auditor` reads only the final module, intended use, evidence boundary, review-bound items, and veto constraints needed for exit judgment.
- `auditor` does not rely on the generator's working notes or rationale to justify exit.
- `auditor` may accept, return, or block. It must not rewrite the module as part of the same audit.

This is still agentic judgment, not script judgment. The separation reduces self-justifying exits without turning TVG into a heavy default process.

Minimum audit structure:

- `target_module`
- `claimed_value_gain`
- `value_gain_type`
- `veto_constraints`
- `veto_constraint_result`
- `evidence_support`
- `remaining_review_bound`
- `audit_role`
- `auditor_independence`
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
7. What specific unacceptable states would veto exit even if the module improves?

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
- named veto constraints are not triggered, or exit is returned/blocked honestly
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
- veto constraints for this module and use
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

## Step 4: Run A Bounded State-Driven Value-Gain Loop

Default loop:

1. `structured draft`
   - create or identify the module in its current structured form
2. `state check`
   - classify the current module state using `Thinking Thickness`, `Grounded Insight Yield`, and `Value Density`
3. `routed value-gain action`
   - deepen, continue targeted depth formation, refine, compact-strengthen, return, block, or freeze based on state
4. `Exit-side warning checks`
   - apply claim calibration and handoff readiness near exit or when the module purpose requires them
5. `exit decision`
   - freeze, freeze-with-review-bound-warning, return-remediate, or blocked

Default limit:

> one structured draft + up to three state-driven value-gain rounds

A system may allow more rounds only with explicit justification and a named positive-value hypothesis.

### State-Driven Round Routing

| State | Meaning | Next Action |
|---|---|---|
| `under-thick` | thought substrate is insufficient | `deepen` |
| `value-thickening` | more depth is still producing useful insight | continue targeted depth formation |
| `adequate-but-loose` | thickness exists but expression is loose | `refine` |
| `over-thick` | extra material adds burden more than value | `compact-strengthen` |
| `insight-ready` | grounded insight exists but needs delivery shaping | refine and prepare freeze candidate |
| `blocked` | missing evidence, domain input, runtime proof, or owner decision prevents honest progress | `return-remediate` or `blocked` |
| `freeze-ready` | another round is unlikely to create meaningful positive value | `freeze` or `freeze-with-review-bound-warning` |

Exit-side warning checks run after the primary routing state is understood. They may add claim labels, review-bound notes, handoff repair, or a risk-based return/block decision, but they should not become a routine early-loop state.

### Routing Conflict Rule

When dimensions conflict, preserve the order of value formation:

1. If `Thinking Thickness` is too low, do not compress prematurely.
2. If `Grounded Insight Yield` is low but thickness exists, pressure for hidden contradiction, alternative frame, useful counterexample, or grounded stretch.
3. If thickness and insight exist but `Value Density` is low, refine or compact-strengthen.
4. If missing evidence or owner judgment blocks honest progress, return or block instead of writing around the gap.

Do not add an axis, profile, or warning check when it would only increase taxonomy, length, or process weight.

### Valid Round Triggers

A new round is justified only when a named module unit still has one of these problems:

- generic reasoning
- insufficient thinking thickness
- missing alternatives comparison
- weak trade-off explanation
- hidden uncertainty
- missing scenario or failure path
- weak downstream handoff value
- weak grounded insight yield
- low value density
- unresolved contradiction worth testing
- evidence / assumption boundary is unclear for the module's risk level
- generalization risk has not been checked
- template completeness may be hiding demo-level judgment
- over-thick low-density structure needs compact strengthening

Do not continue based on a vague feeling that more thinking would be nice.

### Round Discipline

Each round must record:

- target module unit
- current state
- selected value-gain action
- selected value-gain axis or axes
- trigger for the round
- what changed
- what insight, density, or useful thickness improved
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

High-impact, high-uncertainty, or handoff-critical modules should use an auditor separated from the generator. The auditor judges the final module against intended use, evidence, review-bound items, and veto constraints. The auditor should not depend on the generator's private reasoning process to make the exit decision.

The agentic exit audit should ask:

1. Does this module improve decision, action, evidence honesty, review, reuse, or handoff value?
2. Would it still be useful if the template formatting were removed?
3. Does it contain grounded insight, or only safer and longer structure?
4. Is the value density higher, or did the run add reading burden without enough value?
5. If the output goes beyond current reality, is the stretch anchored enough to be productive speculation rather than free fantasy?
6. Are the important trade-offs, uncertainties, and failure paths visible?
7. Are review-bound items honest rather than hidden behind clean structure?
8. Are any named veto constraints triggered?
9. Is another round likely to create meaningful positive value, or only more compliant output?

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
- `veto_constraints`
- `selected_value_gain_axes`
- `rounds_run`
- `round_trigger`
- `material_change`
- `alternatives_or_tradeoffs_considered`
- `evidence_or_assumption_boundary`
- `review_bound_items`
- `anti_overfitting_result`
- `exit_state`
- `audit_role`
- `auditor_independence`
- `veto_constraint_result`
- `agentic_exit_audit_result`
- `why_another_round_is_or_is_not_justified`

### Lightweight Trace Mode

For small or low-risk modules, a lighter trace is acceptable if it still preserves the value-gain decision:

- `target_unit`
- `selected_value_gain_axes`
- `value_gain`
- `review_bound_items`
- `exit_state`
- `agentic_exit_audit_result`

Use the full trace for high-impact, high-uncertainty, or handoff-critical modules.

Script boundary for issue #10:

Scripts must not score `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`; choose TVG state routes; choose `output_profile`; or decide `compact-strengthen`, `refine`, `deepen`, or `freeze`. They may only preserve records that support later agentic audit.

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

## Output Profile Bias

`output_profile` is an optional delivery preference. It is delivery bias, not an internal workflow fork.

| Profile | Delivery Bias | Guardrail |
|---|---|---|
| `insight_dense` | sharper judgments, less setup, earlier compact strengthening | must not compress before thinking thickness exists |
| `balanced` | default expression balance | must still make a clear judgment |
| `coverage_rich` | more examples, context, reasoning path, and boundaries | must not permit low-value expansion |

Profiles affect final delivery weighting only. They must not lower the standard for `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`.

Scripts must not choose `output_profile`. The generator or surrounding workflow may name it as a preference, but agentic judgment still decides whether the module has enough substrate, insight, and density to exit.

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
