# TVG Grounded Insight Loop Design

Status: reviewed design for implementation planning

Issue: https://github.com/rv198-star/Mindthus/issues/10

## Goal

Upgrade TVG from a depth-expansion-biased method into a state-driven value-gain loop.
The new TVG should preserve sufficient thinking thickness as the substrate of value,
produce grounded non-obvious insight as the core yield, and use value density as the
delivery-quality target.

This design does not create a new skill. It evolves the existing `tvg` skill and its
methodology docs so agents stop treating every TVG round as another deepening pass.

## Context

TVG v0.3 already rejects length-for-length and uses veto constraints plus auditor
separation to avoid false exits. The current method text still describes the loop as a
sequence of deepening rounds:

- gap-targeted deepening
- comparison / stress-test deepening
- integration deepening

That language solves thin AI output, but it also biases agents toward adding more
coverage and structure when the better move is refinement, compact strengthening, or
exit. Issue #10 changes the control question from "how do we deepen this module?" to
"what kind of value-gain action does the current module state require?"

## Design Principles

### Value, Not Thickness

TVG should keep the existing claim that thickness is not the goal, but make the relation
more precise:

- Sufficient thinking thickness is the substrate of value.
- Grounded insight yield is the core output.
- Value density is the delivery quality.

This prevents two opposite failures: polished thinness and over-thick low-density output.

### State-Driven Rounds

Each round should begin with a state check, not a fixed action. The method should route
to `deepen`, `continue targeted depth formation`, `refine`, `compact-strengthen`,
`return-remediate`, `blocked`, or `freeze` based on the artifact state.

### Grounded Stretch

TVG should produce viewpoints that feel fresh without becoming unsupported fantasy.
The standard should be: "I had not seen it that way, but it makes sense." This allows
productive speculation beyond current reality when the idea is anchored in constraints,
trends, contradictions, needs, counterexamples, or structural reasoning.

### Late-Stage Warnings

`Claim Calibration` and `Handoff Readiness` should be warning checks by default. They
should not dominate early internal iteration unless the module's purpose or risk profile
requires them. Their normal position is near exit, not inside the primary value-gain
loop.

### Output Profile Bias, Not Workflow Fork

An optional output profile may bias final delivery shape, but it must not change TVG's
internal mainline.

Suggested profiles:

- `insight_dense`: sharper, more compressed final expression.
- `balanced`: default delivery without strong compression or expansion bias.
- `coverage_rich`: more room for context, examples, reasoning path, and boundaries.

Profiles affect final delivery weighting only. They must not lower the standard for
`Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`.

### Test-First Implementation

Implementation must start with failing tests. The first implementation task should add
contract tests and pressure-test titles that fail against current TVG v0.3 docs before
any TVG production documentation is changed. Tests written only after the docs are
updated are not acceptable evidence for this issue.

## Proposed Method Shape

### Primary Loop Dimensions

Add three internal calibration dimensions to TVG's mainline:

| Dimension | Core Question | Low Signal | High Signal |
|---|---|---|---|
| `Thinking Thickness` | Has the module gone deep enough to support value? | missing constraints, scenarios, alternatives, trade-offs, failure paths | enough thought substrate exists for insight or refinement |
| `Grounded Insight Yield` | Did the run produce non-obvious but anchored insight? | generic, template-like, merely complete | changes understanding, judgment, framing, or action |
| `Value Density` | Is value concentrated relative to reading burden? | repetition, taxonomy, ornament, low-signal structure | high-signal expression without premature compression |

These dimensions guide agentic judgment. They are not numeric scores and must not be
computed by scripts.

### Round State Routing

Replace the fixed round sequence with a bounded state-routing loop:

| State | Meaning | Next Action |
|---|---|---|
| `under-thick` | thought substrate is insufficient | `deepen` |
| `value-thickening` | more depth is still producing useful insight | continue targeted depth formation |
| `adequate-but-loose` | thickness exists but expression is loose | `refine` |
| `over-thick` | extra material adds burden more than value | `compact-strengthen` |
| `insight-ready` | grounded insight exists but needs delivery shaping | refine and prepare freeze candidate |
| `blocked` | missing evidence, domain input, runtime proof, or owner decision prevents honest progress | `return-remediate` or `blocked` |
| `freeze-ready` | another round is unlikely to create meaningful positive value | `freeze` or `freeze-with-review-bound-warning` |

The method should keep the existing round limit discipline. The change is the routing
logic inside each round, not permission for unlimited iteration.

Exit-side warning checks run after the primary routing state is understood. They may add
claim labels, review-bound notes, handoff repair, or a risk-based return/block decision,
but they should not become a routine early-loop state.

### Grounded Novelty And Stretch

Define grounded novelty as all three of:

- non-obvious: not a template answer or common summary
- grounded: anchored in real constraints, trends, contradictions, needs, counterexamples,
  or structural reasoning
- useful: changes understanding, judgment, expression, action, trade-off, or next inquiry

Define stretch levels:

- `reality-bound`: stays within current facts and constraints
- `plausible-extension`: extends one step from known tensions or trends
- `productive-speculation`: goes beyond available proof while naming the anchor and
  assumption
- `free-fantasy`: lacks anchor, reasoning support, or recovery path and should be rejected

### Warning Checks

`Claim Calibration` should warn when a fresh idea is being presented with stronger claim
status than it deserves. It should usually cause labeling, downgrade, or review-bound
notes, not a different main action. It escalates only when factual accuracy, safety,
compliance, money, release, or irreversible execution is central.

`Handoff Readiness` should be checked near exit or when the module is explicitly for
handoff, review, implementation, or reuse. It should not flatten early exploration.

### Output Profiles

Add output-profile guidance as an optional delivery preference:

| Profile | Delivery Bias | Guardrail |
|---|---|---|
| `insight_dense` | sharper judgments, less setup, earlier compact strengthening | must not compress before thinking thickness exists |
| `balanced` | default expression balance | must still make a clear judgment |
| `coverage_rich` | more examples, context, reasoning path, and boundaries | must not permit low-value expansion |

This belongs in method docs and pressure tests only. It should not become trace-schema
automation in this issue.
It may appear in audit prompts as a delivery-bias check, but not in scripts or schema
fields that imply automated routing.

## File-Level Design

### `skills/tvg/SKILL.md`

Update the core claim and operating flow so the entrypoint names state-driven value gain.
The skill should mention the three primary dimensions and the optional output profile,
but keep details in `resources/methodology.md`.

Required behavioral phrases for tests:

- `state-driven value-gain loop`
- `Thinking Thickness`
- `Grounded Insight Yield`
- `Value Density`
- `output_profile`
- `delivery bias, not an internal workflow fork`

### `skills/tvg/resources/methodology.md`

This is the primary design surface. Update these areas:

- Purpose and Core Claim: add substrate / yield / delivery-quality framing.
- Value-Gain Governance Layer: add the three primary loop dimensions and late-stage
  warnings.
- Step 4: replace the fixed deepening sequence with state-driven routing.
- Exit Gate Audit Rule: ask whether another round creates insight, density, or needed
  thickness rather than only more compliant output.
- Delivery Translation Rule: add output-profile delivery shaping and guardrails.
- Anti-Patterns: add over-thick low-density output, premature compression, and free
  fantasy.

Keep existing veto constraints and independent-auditor behavior intact.

### `skills/tvg/resources/exit-audit-template.md`

Add lightweight prompts that help auditors check the new behavior:

- `thinking_thickness_state`
- `grounded_insight_yield`
- `value_density_result`
- `grounded_stretch_level`
- `output_profile`
- `profile_guardrail_result`

Do not make these fields script-scored. They are audit prompts.

### `docs/methodologies/tvg.md`

Update the public Chinese method page so it reflects the evolved TVG without exposing
too much internal vocabulary. It should explain:

- TVG is not extension by default.
- Enough thinking depth is necessary.
- The desired result is grounded insight with high value density.
- Some work needs dense conclusions, and some work needs richer coverage.

### `tests/test_tvg_contract.py`

Add static contract tests that assert the docs contain the new concepts and preserve
script boundaries.

Suggested test groups:

- `test_skill_exposes_state_driven_grounded_insight_loop`
- `test_methodology_defines_primary_loop_dimensions_and_state_routing`
- `test_methodology_defines_grounded_novelty_and_stretch_boundaries`
- `test_methodology_keeps_claim_and_handoff_as_late_stage_warnings`
- `test_output_profile_is_delivery_bias_not_workflow_fork`
- `test_scripts_still_cannot_score_or_route_value_gain`

### `tests/tvg_ab_pressure_tests.md`

Append issue #10 pressure scenarios. These are transcript-scored scenarios, not unit
tests, but the contract test should assert they exist.

Scenarios:

- thin but polished artifact -> `deepen`
- adequately thick but loose artifact -> `refine`
- over-thick low-density artifact -> `compact-strengthen`
- fresh but ungrounded viewpoint -> warning, downgrade, or rejection
- grounded stretch beyond current reality -> accept as productive speculation
- `coverage_rich` profile -> allow useful expansion without low-value bloat
- `insight_dense` profile -> compress delivery without skipping thinking thickness

### A/B Human Review Artifacts

Add an A/B experiment packet for manual review. The experiment should compare baseline
TVG behavior against issue #10 treatment behavior on the same input artifact.

Required review packet fields:

- source artifact
- baseline output
- treatment output
- selected state route
- output profile, when used
- reviewer preference
- review rationale
- whether the treatment produced more grounded insight, better value density, or useful
  thickness without bloat

The A/B packet is for human judgment, not automated scoring.

## Testing Strategy

Use strict test-first implementation.

1. Add failing TVG contract tests for the new wording and boundaries.
2. Run the focused test command and confirm the new tests fail for the expected missing
   phrases or scenario titles.
3. Add pressure-test scenarios and make the contract test require their titles.
4. Run the focused test command again and confirm the pressure-test coverage fails before
   production docs are updated.
5. Update `SKILL.md`, methodology, exit audit template, and public docs.
6. Run focused tests:

```bash
python3 -m unittest tests.test_tvg_contract -v
git diff --check
```

7. Prepare an A/B human-review packet comparing representative baseline and treatment
   outputs. The implementation is not done until this packet exists.
8. Run broader tests when dependencies are available:

```bash
python3 -m unittest discover -s tests -v
```

Current baseline note: full discovery fails in the present environment because PyYAML is
not installed for `tests/test_packaging_docs.py`. Focused TVG tests pass before this
design work.

## Acceptance Criteria

- TVG docs state the substrate / yield / delivery-quality relationship.
- TVG docs define the three primary loop dimensions.
- TVG docs replace fixed deepening language with state-driven routing.
- TVG docs define grounded novelty and grounded stretch, including free-fantasy rejection.
- Claim calibration and handoff readiness are late-stage warning checks by default.
- Optional output profiles are delivery-bias controls and do not fork TVG's internal loop.
- Output profiles do not lower the standards for thinking thickness, grounded insight,
  or value density.
- Existing veto-constraint and independent-auditor behavior remains intact.
- Scripts still cannot score value, choose routing actions, or decide exit state.
- Implementation starts with failing tests, and the failure is observed before production
  docs are changed.
- Focused TVG contract tests pass.
- Pressure tests document the new expected behavior across thin, loose, over-thick,
  ungrounded, grounded-stretch, and output-profile cases.
- A/B human-review artifacts compare baseline and treatment outputs for grounded insight,
  value density, and useful thickness without bloat.

## Non-Goals

- No new skill.
- No automated scoring engine.
- No trace schema version bump unless implementation discovers a hard compatibility need.
- No script-based routing for TVG state.
- No general writing-style optimizer.
- No public exposure of TVG internals beyond what the public method page needs.

## Implementation Risks

- Too many labels could make TVG heavier and less useful. Keep labels as routing aids.
- Grounded insight could be misread as novelty for novelty's sake. Keep anchor and utility
  requirements explicit.
- Claim calibration could become too conservative. Keep it as a warning unless risk or
  module purpose escalates it.
- Coverage-rich output could reintroduce bloat. Keep the value-density guardrail explicit.
