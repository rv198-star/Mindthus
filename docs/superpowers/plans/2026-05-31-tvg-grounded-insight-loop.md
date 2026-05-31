# TVG Grounded Insight Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement GitHub issue #10 by evolving TVG into a state-driven grounded-insight value-gain loop with test-first verification and A/B human-review artifacts.

**Architecture:** Keep TVG as one existing skill. Add failing contract tests first, add issue #10 pressure scenarios, then update TVG entry docs, methodology, exit audit prompts, public Chinese docs, and an A/B comparison packet. Scripts and trace schema remain bookkeeping support and must not score value, choose state routes, choose output profiles, or decide exits.

**Tech Stack:** Markdown docs, Python `unittest`, existing TVG trace scripts, existing pressure-test markdown files.

---

## File Structure

- Modify: `tests/test_tvg_contract.py`
  - Add issue #10 contract tests before production TVG docs change.
  - Verify state-driven loop, primary dimensions, grounded novelty, late-stage warnings, output profiles, A/B artifacts, and script boundaries.
- Modify: `tests/tvg_ab_pressure_tests.md`
  - Append issue #10 transcript-scored scenarios.
- Create: `tests/tvg_ab_run_2026-05-31.md`
  - Human-review packet with same-source baseline and treatment outputs.
- Modify: `skills/tvg/SKILL.md`
  - Update entrypoint wording to name state-driven value gain, primary dimensions, late-stage warnings, and output profile boundary.
- Modify: `skills/tvg/resources/methodology.md`
  - Main implementation surface for the evolved TVG method.
- Modify: `skills/tvg/resources/exit-audit-template.md`
  - Add audit prompts for thickness state, grounded insight, value density, grounded stretch, and output profile guardrails.
- Modify: `docs/methodologies/tvg.md`
  - Update public Chinese explanation without exposing excessive internal vocabulary.
- Not modified: `skills/tvg/resources/trace-record-schema.json`
  - No schema change in this issue.
- Not modified: `skills/tvg/scripts/trace/*.py`
  - Scripts must remain shape/bookkeeping helpers only.

## Task 1: Add Failing TVG Contract Tests

**Files:**
- Modify: `tests/test_tvg_contract.py`

- [ ] **Step 1: Add issue #10 contract test methods**

Insert the following methods inside `TvgContractTests`, after `test_methodology_keeps_veto_constraints_outside_value_axes` and before `test_exit_audit_template_records_veto_and_independence`:

```python
    def test_skill_exposes_state_driven_grounded_insight_loop(self):
        text = (TVG / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "state-driven value-gain loop",
            "Thinking Thickness",
            "Grounded Insight Yield",
            "Value Density",
            "output_profile",
            "delivery bias, not an internal workflow fork",
        ):
            self.assertIn(phrase, text)

    def test_methodology_defines_primary_loop_dimensions_and_state_routing(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Sufficient thinking thickness is the substrate of value",
            "Grounded insight yield is the core output",
            "Value density is the delivery quality",
            "Primary Loop Dimensions",
            "`Thinking Thickness`",
            "`Grounded Insight Yield`",
            "`Value Density`",
            "State-Driven Round Routing",
            "`under-thick`",
            "`adequate-but-loose`",
            "`over-thick`",
            "`compact-strengthen`",
            "Exit-side warning checks",
        ):
            self.assertIn(phrase, text)

    def test_methodology_defines_grounded_novelty_and_stretch_boundaries(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Grounded Novelty",
            "non-obvious",
            "anchored in real constraints",
            "changes understanding, judgment, expression, action",
            "Grounded Stretch Levels",
            "`reality-bound`",
            "`plausible-extension`",
            "`productive-speculation`",
            "`free-fantasy`",
            "unsupported fantasy",
        ):
            self.assertIn(phrase, text)

    def test_methodology_keeps_claim_and_handoff_as_late_stage_warnings(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Late-Stage Warning Checks",
            "`Claim Calibration`",
            "`Handoff Readiness`",
            "not inside the primary value-gain loop",
            "usually causes labeling, downgrade, or review-bound notes",
            "checked near exit or when the module is explicitly for handoff",
        ):
            self.assertIn(phrase, text)

    def test_output_profile_is_delivery_bias_not_workflow_fork(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        combined = skill + "\n" + method
        for phrase in (
            "Output Profile Bias",
            "`insight_dense`",
            "`balanced`",
            "`coverage_rich`",
            "delivery bias, not an internal workflow fork",
            "must not lower the standard",
            "must not compress before thinking thickness exists",
            "must not permit low-value expansion",
        ):
            self.assertIn(phrase, combined)

    def test_exit_audit_template_records_grounded_insight_and_profile_prompts(self):
        text = (TVG / "resources" / "exit-audit-template.md").read_text(encoding="utf-8")
        for phrase in (
            "Grounded Insight And Density Check",
            "thinking_thickness_state",
            "grounded_insight_yield",
            "value_density_result",
            "grounded_stretch_level",
            "output_profile",
            "profile_guardrail_result",
            "audit prompts, not script-scored fields",
        ):
            self.assertIn(phrase, text)

    def test_public_tvg_doc_mentions_grounded_insight_density_and_profiles(self):
        text = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        for phrase in (
            "思考厚度",
            "有根洞察",
            "价值密度",
            "不是默认扩写",
            "我没想到，但它说得通",
            "输出档位",
            "洞察密度优先",
            "覆盖厚度优先",
        ):
            self.assertIn(phrase, text)

    def test_ab_pressure_tests_cover_issue_10_state_and_profile_scenarios(self):
        text = (REPO / "tests" / "tvg_ab_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "Issue 10: Thin But Polished Artifact Needs Depth Formation",
            "Issue 10: Adequately Thick But Loose Artifact Needs Refinement",
            "Issue 10: Over-Thick Low-Density Artifact Needs Compact Strengthening",
            "Issue 10: Fresh But Ungrounded Viewpoint Needs Claim Warning Or Rejection",
            "Issue 10: Grounded Stretch Accepts Productive Speculation",
            "Issue 10: Coverage-Rich Profile Allows Useful Thickness Without Bloat",
            "Issue 10: Insight-Dense Profile Must Not Skip Thinking Thickness",
            "Expected issue #10 treatment behavior",
        ):
            self.assertIn(phrase, text)

    def test_issue_10_ab_human_review_packet_exists(self):
        path = REPO / "tests" / "tvg_ab_run_2026-05-31.md"
        self.assertTrue(path.exists(), "missing issue #10 A/B human-review packet")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "TVG Issue #10 A/B Human Review Packet",
            "source_artifact",
            "baseline_output",
            "treatment_output",
            "selected_state_route",
            "output_profile",
            "reviewer_preference_prompt",
            "grounded insight",
            "value density",
            "useful thickness without bloat",
        ):
            self.assertIn(phrase, text)

    def test_scripts_still_cannot_score_or_route_issue_10_value_gain(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        combined = skill + "\n" + method
        for phrase in (
            "score `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`",
            "choose TVG state routes",
            "choose `output_profile`",
            "decide `compact-strengthen`, `refine`, `deepen`, or `freeze`",
        ):
            self.assertIn(phrase, combined)
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_tvg_contract -v
```

Expected: FAIL. The new issue #10 tests should fail because current TVG v0.3 docs do not yet contain the new state-driven loop, grounded insight, output profile, A/B packet, and script-boundary phrases.

- [ ] **Step 3: Confirm failure is meaningful**

Check that failures are `AssertionError: '<phrase>' not found` or `missing issue #10 A/B human-review packet`, not syntax errors or import errors.

Do not modify production TVG docs until this RED state is observed.

## Task 2: Add Issue #10 Pressure Scenarios And Confirm Partial RED

**Files:**
- Modify: `tests/tvg_ab_pressure_tests.md`

- [ ] **Step 1: Append issue #10 pressure scenarios**

Append this section before `## Result Template`:

````markdown
## Issue 10: Thin But Polished Artifact Needs Depth Formation

### What This Tests

This scenario checks whether TVG recognizes that a clean artifact can still be
under-thick. The expected treatment is `deepen`, not premature refinement.

Expected baseline weakness: the agent tightens wording while leaving missing
constraints, alternatives, and failure paths implicit.

Expected issue #10 treatment behavior: the agent identifies `under-thick`, names the
missing thinking substrate, and runs a depth-formation pass before refinement.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: product recommendation paragraph.

Current artifact:
"We should add team dashboards because teams need visibility. This will improve
collaboration and make the product more useful."

Known context:
- no user segment is named
- no substitute workflow is compared
- no failure path or adoption condition is described
- the paragraph should become decision-useful, not just more polished

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Chooses `under-thick` or equivalent thickness-insufficient state.
- Adds real constraints, target user, substitute, failure path, or adoption condition.
- Does not compress before the missing thinking substrate exists.
- Explains why polish alone would be low value.
- Keeps the added thickness tied to decision value.

Treatment passes at 4 or higher.

## Issue 10: Adequately Thick But Loose Artifact Needs Refinement

### What This Tests

This scenario checks whether TVG stops expanding once the thought substrate is adequate
and instead improves value density.

Expected baseline weakness: the agent adds another section or checklist.

Expected issue #10 treatment behavior: the agent chooses `adequate-but-loose` and
performs `refine` by consolidating repeated claims into sharper judgment.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: method note.

Current artifact:
"This method helps teams decide when to automate a review. It should be used when the
steps are repetitive, when the reviewer has clear criteria, and when the cost of a wrong
decision is low. It should not be used when the decision is uncertain, when the facts
are missing, or when human judgment is central. In short, automate repetitive clear
checks, but keep uncertain judgment human."

Known context:
- the core constraints are already present
- the module feels repetitive and loose
- the output should stay compact

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Chooses `adequate-but-loose` or equivalent.
- Performs `refine`, not another deepening pass.
- Reduces repetition while preserving constraints.
- Produces a sharper decision rule.
- Does not remove necessary boundaries for the sake of brevity.

Treatment passes at 4 or higher.

## Issue 10: Over-Thick Low-Density Artifact Needs Compact Strengthening

### What This Tests

This scenario checks whether TVG detects over-thick low-density output and selects
compact strengthening.

Expected baseline weakness: the agent adds more examples or a new taxonomy.

Expected issue #10 treatment behavior: the agent chooses `over-thick` and removes or
compresses low-value structure while preserving the strongest insight.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: review checklist.

Current artifact:
"Check the goal. Check the user. Check the stakeholder. Check the reader. Check the
consumer. Check the input. Check the context. Check the framing. Check the evidence.
Check the proof. Check the assumptions. Check the claims. Check the risks. Check the
edge cases. Check the downstream. Check the handoff. Check the final answer."

Known context:
- the checklist is long but repetitive
- the intended reader needs a compact review aid
- no new facts are available

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Chooses `over-thick` or equivalent.
- Performs `compact-strengthen`.
- Consolidates repeated checks into fewer higher-signal checks.
- Preserves evidence, risk, and downstream concerns.
- Does not add a new checklist layer.

Treatment passes at 4 or higher.

## Issue 10: Fresh But Ungrounded Viewpoint Needs Claim Warning Or Rejection

### What This Tests

This scenario checks whether TVG allows fresh thinking without accepting unsupported
fantasy.

Expected baseline weakness: the agent accepts a striking claim because it sounds deep.

Expected issue #10 treatment behavior: the agent marks the idea as ungrounded, downgrades
it to speculation, or rejects it if no anchor exists.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: strategy insight.

Current artifact:
"The next generation of documentation will disappear entirely because agents will infer
all project intent from code. Therefore, teams should stop writing docs and invest only
in code-reading agents."

Known context:
- no evidence is provided
- some teams still need human-readable policy, onboarding, and review records
- the user wants a fresh viewpoint, but not free fantasy

Decide the TVG state route and improve or reject the viewpoint.
```

### Scoring

Score 1 point for each behavior:

- Detects that the claim is fresh but insufficiently grounded.
- Uses claim calibration as a warning, not as a blanket ban on exploration.
- Downgrades the claim to a bounded hypothesis or rejects the unsupported version.
- Names what anchor or evidence would make the idea productive.
- Avoids presenting the speculation as fact.

Treatment passes at 4 or higher.

## Issue 10: Grounded Stretch Accepts Productive Speculation

### What This Tests

This scenario checks whether TVG can go beyond current reality when the stretch has an
anchor and useful recovery path.

Expected baseline weakness: the agent either rejects the idea as unproven or overclaims
it as fact.

Expected issue #10 treatment behavior: the agent classifies it as `productive-speculation`
and keeps the anchor visible.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: future workflow insight.

Current artifact:
"Review tools may shift from checking completed artifacts to shaping the artifact while
it is being generated."

Known context:
- current tools already provide inline suggestions
- agent workflows increasingly generate drafts interactively
- the claim is not proven as a market trend
- the goal is to produce an insight that is fresh but still grounded

Decide the TVG state route and improve the insight.
```

### Scoring

Score 1 point for each behavior:

- Accepts the idea as grounded stretch or productive speculation.
- Names the anchor in current inline tools and interactive generation.
- Avoids claiming the trend is already proven.
- Explains why the frame changes product or workflow thinking.
- Keeps the output useful rather than purely speculative.

Treatment passes at 4 or higher.

## Issue 10: Coverage-Rich Profile Allows Useful Thickness Without Bloat

### What This Tests

This scenario checks whether `coverage_rich` changes delivery shape without lowering
the value standard.

Expected baseline weakness: the agent treats coverage-rich as permission to expand
everything.

Expected issue #10 treatment behavior: the agent includes useful context, examples,
reasoning path, and boundaries while rejecting ornamental completeness.

### Prompt

```text
Use TVG issue #10 treatment behavior with output_profile=coverage_rich.

Target module: onboarding explanation for a methodology skill.

Current artifact:
"Use this skill when AI output looks complete but lacks value."

Known context:
- new contributors need enough context to apply the skill correctly
- examples are useful
- low-value expansion is not acceptable

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Treats `coverage_rich` as delivery bias, not a workflow fork.
- Adds context or examples that improve correct use.
- Keeps each expansion tied to thinking thickness, grounded insight, or value density.
- Rejects ornamental completeness.
- Does not lower the value-density standard.

Treatment passes at 4 or higher.

## Issue 10: Insight-Dense Profile Must Not Skip Thinking Thickness

### What This Tests

This scenario checks whether `insight_dense` compresses delivery only after sufficient
thinking substrate exists.

Expected baseline weakness: the agent jumps to a punchy line before resolving missing
constraints.

Expected issue #10 treatment behavior: the agent first identifies the missing thickness,
then produces a compact final expression.

### Prompt

```text
Use TVG issue #10 treatment behavior with output_profile=insight_dense.

Target module: executive summary.

Current artifact:
"The platform should become more agentic because agentic products are the future."

Known context:
- the target user is not named
- the risk boundary is not named
- no substitute or timing condition is named
- the final output should be short and sharp

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Does not compress before identifying missing thickness.
- Names the missing user, risk, substitute, or timing constraint.
- Produces a compact final expression after grounding the idea.
- Treats `insight_dense` as delivery bias only.
- Avoids a catchy but unsupported claim.

Treatment passes at 4 or higher.
````

- [ ] **Step 2: Run focused tests and confirm remaining RED**

Run:

```bash
python3 -m unittest tests.test_tvg_contract -v
```

Expected: FAIL. The pressure scenario title assertions should now pass, while skill, methodology, exit-audit, public-doc, A/B packet, and script-boundary assertions still fail.

## Task 3: Update TVG Skill Entrypoint

**Files:**
- Modify: `skills/tvg/SKILL.md`

- [ ] **Step 1: Update the Core Claim section**

Replace the current first paragraph of `## Core Claim` through the short rule with this text:

```markdown
Thinking Value-Gain is a state-driven value-gain loop for AI-generated bounded modules.

It addresses a common AI-output failure mode: the artifact looks complete, rigorous,
standardized, and fluent, but the substance is hollow, shallow, random, over-expanded,
or too weak for real judgment, decision, action, review, reuse, or handoff.

TVG is not a thickness-expansion method. Sufficient thinking thickness is the substrate
of value, Grounded Insight Yield is the core output, and Value Density is the delivery
quality.

Short rule:

> Do not deepen by default. First judge whether the module needs depth formation,
> grounded insight generation, value refinement, compact strengthening, warning
> calibration, or honest exit.
```

- [ ] **Step 2: Add output profile paragraph after the two core inputs**

Add this paragraph after the `independent_auditor` bullet:

```markdown
Optional delivery control:

- `output_profile`: `insight_dense | balanced | coverage_rich`. This is delivery bias,
  not an internal workflow fork. It may affect final expression shape, but it must not
  lower the standard for `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`.
```

- [ ] **Step 3: Update Operating Flow**

Replace Operating Flow steps 4-5 with these steps, preserving steps 1-3 and 6-9:

```markdown
4. Check the current module state using `Thinking Thickness`, `Grounded Insight Yield`,
   and `Value Density`.
5. Perform the routed value-gain action: `deepen`, targeted depth formation, `refine`,
   `compact-strengthen`, warning calibration, `return-remediate`, `blocked`, or `freeze`.
```

- [ ] **Step 4: Expand script hard-boundary list**

Add these bullets under `Scripts must not:`:

```markdown
- score `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`
- choose TVG state routes
- choose `output_profile`
- decide `compact-strengthen`, `refine`, `deepen`, or `freeze`
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_tvg_contract -v
```

Expected: FAIL. The skill-entrypoint assertions should pass; methodology, exit audit, public doc, and A/B packet assertions still fail.

## Task 4: Update Full TVG Methodology

**Files:**
- Modify: `skills/tvg/resources/methodology.md`

- [ ] **Step 1: Update the Purpose opening**

In `## Purpose`, replace the paragraphs from `Depth is the means` through `Core goal` with this text:

```markdown
Depth is the means only when the module is under-thick. Practical value gain is the
target. Positive-value exit is the stopping rule.

TVG is not a generic improvement pass and not a thickness-expansion method. Its leverage
comes from dynamically deciding whether the current bounded module needs depth
formation, grounded insight generation, value refinement, compact strengthening, warning
calibration, or honest exit.

Its primary positioning is universal: it should help different projects solve the
recurring AI-work problem where an AI can construct a module, section, artifact unit,
plan, design, review, or reasoning block that looks structurally complete but lacks
sufficient thinking value for real use.

It is designed for AI work, knowledge work, product thinking, engineering design,
methodology writing, review work, and any situation where a module may look structurally
complete while still being shallow, over-thick, low-density, or weak in judgment.

Core problem:

> A module can exist, be well-structured, and look complete, but still fail because it has
> not created enough practical value for decision, action, review, reuse, or handoff.

Core relationship:

> Sufficient thinking thickness is the substrate of value. Grounded insight yield is the
> core output. Value density is the delivery quality.

Core goal:

> Move a module from `structure exists` to `value is increased`: judgment becomes more
> usable, insights become less obvious and better grounded, trade-offs become clearer,
> and the final artifact carries more value per unit of reading burden.
```

- [ ] **Step 2: Update Core Claim**

In `## Core Claim`, replace the opening paragraphs through `Anti-demo rule` with this text:

```markdown
The goal is value gain, not thickness for its own sake.

Sufficient thinking thickness is required because high-value insight rarely appears from
thin substrate. But once the module has enough constraints, scenarios, alternatives,
trade-offs, evidence boundaries, and failure paths, another expansion round may lower
value density rather than improve value.

TVG rounds are state-driven, not action-fixed. Each round first asks what the module
currently lacks, then chooses a value-gain action.

Primary loop dimensions:

- `Thinking Thickness`: whether the module has enough thought substrate to support value.
- `Grounded Insight Yield`: whether the module produces non-obvious but anchored insight.
- `Value Density`: whether the artifact carries enough value relative to reading burden.

Short rule:

> Complete is not enough. Thick is not enough. TVG exits when the module has enough
> thought substrate, grounded insight, and value density for its actual use.

Grounded novelty rule:

> TVG should make the reader think, "I had not seen it that way, but it makes sense."
> It may stretch beyond current reality, but the stretch must remain anchored enough to
> be productive speculation rather than unsupported fantasy.
```

- [ ] **Step 3: Add Primary Loop Dimensions section**

After `### Value-Gain Types`, add:

```markdown
### Primary Loop Dimensions

Use these dimensions for internal calibration. They guide agentic judgment; they are not
numeric scores and must not be computed by scripts.

| Dimension | Core Question | Low Signal | High Signal |
|---|---|---|---|
| `Thinking Thickness` | Has the module gone deep enough to support value? | missing constraints, scenarios, alternatives, trade-offs, failure paths | enough thought substrate exists for insight or refinement |
| `Grounded Insight Yield` | Did the run produce non-obvious but anchored insight? | generic, template-like, merely complete | changes understanding, judgment, framing, or action |
| `Value Density` | Is value concentrated relative to reading burden? | repetition, taxonomy, ornament, low-signal structure | high-signal expression without premature compression |

Do not optimize these dimensions independently. Thickness without insight becomes bloat;
insight without grounding becomes fantasy; density without thickness becomes polished
thinness.
```

- [ ] **Step 4: Add Grounded Novelty and Stretch section**

After `### Primary Loop Dimensions`, add:

```markdown
### Grounded Novelty

A high-value TVG result should often contain grounded novelty: a non-obvious but useful
viewpoint that ordinary generation would likely miss.

Grounded novelty requires all three:

- `non-obvious`: not a template answer, common summary, or compliance-shaped restatement
- `grounded`: anchored in real constraints, trends, contradictions, needs,
  counterexamples, or structural reasoning
- `useful`: changes understanding, judgment, expression, action, trade-off, or next inquiry

This is not novelty for novelty's sake. A surprising sentence with no anchor is not
valid value gain.

### Grounded Stretch Levels

TVG may go beyond current reality when doing so reveals a useful possibility. Current
reality is often past evidence and may not contain the full truth. The stretch must keep
enough anchors to remain productive.

| Level | Meaning | Treatment |
|---|---|---|
| `reality-bound` | stays within current facts and constraints | safe but may be ordinary |
| `plausible-extension` | extends one step from known tensions or trends | useful default stretch zone |
| `productive-speculation` | goes beyond available proof while naming the anchor and assumption | allowed when labeled honestly |
| `free-fantasy` | lacks anchor, reasoning support, or recovery path | reject or return-remediate |

The target is grounded stretch: fresh enough to change perspective, anchored enough to
remain believable.
```

- [ ] **Step 5: Add Late-Stage Warning Checks section**

After the grounded stretch section, add:

```markdown
### Late-Stage Warning Checks

`Claim Calibration` and `Handoff Readiness` are late-stage warning checks by default.
They should not dominate early internal iteration and are not inside the primary
value-gain loop unless the module purpose or risk profile requires it.

`Claim Calibration` warns when a fresh idea is being presented with stronger claim status
than it deserves. It usually causes labeling, downgrade, or review-bound notes, not a
different main action. It escalates only when factual accuracy, safety, compliance,
money, release, or irreversible execution is central.

`Handoff Readiness` is checked near exit or when the module is explicitly for handoff,
review, implementation, or reuse. It should not flatten early exploration.
```

- [ ] **Step 6: Replace Step 4 loop**

Replace the full `## Step 4: Run A Bounded Value-Gain Loop` section through `### Round Discipline` with this text:

```markdown
## Step 4: Run A Bounded State-Driven Value-Gain Loop

Default loop:

1. `structured draft`
   - create or identify the module in its current structured form
2. `state check`
   - classify the current module state using `Thinking Thickness`, `Grounded Insight
     Yield`, and `Value Density`
3. `routed value-gain action`
   - deepen, continue targeted depth formation, refine, compact-strengthen, return,
     block, or freeze based on state
4. `exit-side warning checks`
   - apply claim calibration and handoff readiness near exit or when the module purpose
     requires them
5. `exit decision`
   - freeze, freeze-with-review-bound-warning, return-remediate, or blocked

Default limit:

> one structured draft + up to three state-driven value-gain rounds

A system may allow more rounds only with explicit justification and a named positive-value
hypothesis.

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

Exit-side warning checks run after the primary routing state is understood. They may add
claim labels, review-bound notes, handoff repair, or a risk-based return/block decision,
but they should not become a routine early-loop state.

### Routing Conflict Rule

When dimensions conflict, preserve the order of value formation:

1. If `Thinking Thickness` is too low, do not compress prematurely.
2. If `Grounded Insight Yield` is low but thickness exists, pressure for hidden
   contradiction, alternative frame, useful counterexample, or grounded stretch.
3. If thickness and insight exist but `Value Density` is low, refine or compact-strengthen.
4. If missing evidence or owner judgment blocks honest progress, return or block instead
   of writing around the gap.

Do not add an axis, profile, or warning check when it would only increase taxonomy,
length, or process weight.

### Valid Round Triggers

A new round is justified only when a named module unit still has one of these problems:

- insufficient thinking thickness
- generic reasoning
- missing alternatives comparison
- weak trade-off explanation
- hidden uncertainty
- missing scenario or failure path
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
- selected value-gain axis or axes when useful
- trigger for the round
- what changed
- what insight, density, or useful thickness improved
- why another round is or is not justified

If a round leaves no material value trace, treat it as style polish, not value gain.
```

- [ ] **Step 7: Add Output Profile Bias section**

Before `## Delivery Translation Rule`, add:

```markdown
## Output Profile Bias

`output_profile` is an optional delivery preference. It is delivery bias, not an internal
workflow fork.

| Profile | Delivery Bias | Guardrail |
|---|---|---|
| `insight_dense` | sharper judgments, less setup, earlier compact strengthening | must not compress before thinking thickness exists |
| `balanced` | default expression balance | must still make a clear judgment |
| `coverage_rich` | more examples, context, reasoning path, and boundaries | must not permit low-value expansion |

Profiles affect final delivery weighting only. They must not lower the standard for
`Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`.

Scripts must not choose `output_profile`. The generator or surrounding workflow may name
it as a preference, but agentic judgment still decides whether the module has enough
substrate, insight, and density to exit.
```

- [ ] **Step 8: Update Exit Gate Audit Rule questions**

In `## Exit Gate Audit Rule`, replace the full numbered list under `The agentic exit audit should ask:` with this exact list:

```markdown
1. Does this module improve decision, action, evidence honesty, review, reuse, or handoff value?
2. Would it still be useful if the template formatting were removed?
3. Does it contain grounded insight, or only safer and longer structure?
4. Is the value density higher, or did the run add reading burden without enough value?
5. If the output goes beyond current reality, is the stretch anchored enough to be
   productive speculation rather than free fantasy?
6. Are the important trade-offs, uncertainties, and failure paths visible?
7. Are review-bound items honest rather than hidden behind clean structure?
8. Are any named veto constraints triggered?
9. Is another round likely to create meaningful positive value, or only more compliant output?
```

- [ ] **Step 9: Update script boundary wording in methodology**

In `skills/tvg/resources/methodology.md`, add this paragraph immediately after the `### Lightweight Trace Mode` bullet list and before `## Reusable Checklist`:

```markdown
Script boundary for issue #10:

Scripts must not score `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`;
choose TVG state routes; choose `output_profile`; or decide `compact-strengthen`,
`refine`, `deepen`, or `freeze`. They may only preserve records that support later
agentic audit.
```

- [ ] **Step 10: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_tvg_contract -v
```

Expected: FAIL. Methodology tests should pass; remaining failures should be in exit audit template, public docs, and A/B packet.

## Task 5: Update Exit Audit Template And Public TVG Docs

**Files:**
- Modify: `skills/tvg/resources/exit-audit-template.md`
- Modify: `docs/methodologies/tvg.md`

- [ ] **Step 1: Add exit audit prompts**

In `skills/tvg/resources/exit-audit-template.md`, add this section after `## Claimed Value Gain`:

```markdown
## Grounded Insight And Density Check

These are audit prompts, not script-scored fields.

- `thinking_thickness_state`: `under-thick | value-thickening | adequate-but-loose | over-thick | insight-ready | blocked | freeze-ready`
- `grounded_insight_yield`: `none | weak | useful | strong`
- `value_density_result`: `low | acceptable | high | over-compressed`
- `grounded_stretch_level`: `reality-bound | plausible-extension | productive-speculation | free-fantasy | not-applicable`
- `output_profile`: `insight_dense | balanced | coverage_rich | not-specified`
- `profile_guardrail_result`: `clear | violated | not-applicable`

Audit notes:

- Did the run improve grounded insight, or only add safer structure?
- Did the final artifact improve value density relative to reading burden?
- If `output_profile` was used, did it preserve the standards for thinking thickness,
  grounded insight, and value density?
```

- [ ] **Step 2: Update Chinese methodology core judgment**

In `docs/methodologies/tvg.md`, replace the first paragraph under `## 核心判断` with:

```markdown
TVG 的核心判断不是默认扩写，而是先判断当前模块缺什么价值形态：思考厚度不够时加深，已经足够厚但松散时提炼，过厚低密度时收束增强，缺外部事实时停止或返回。

更准确地说：思考厚度是价值基底，有根洞察是核心产出，价值密度是交付质量。一个好的 TVG 输出应该让读者感觉“我没想到，但它说得通”，而不是只是更长、更稳或更完整。
```

- [ ] **Step 3: Add output profile explanation in Chinese methodology**

In `docs/methodologies/tvg.md`, add this section before `## 具体案例`:

```markdown
## 输出档位

TVG 可以接受输出档位，但档位只影响交付表达，不改变内部主线。

- `洞察密度优先`：更快进入关键判断，表达更锋利、更收束。
- `平衡档`：默认形态，不主动扩厚，也不过早压缩。
- `覆盖厚度优先`：允许更多背景、例子、推理路径和边界说明，适合教程、交接和复杂设计。

档位不能降低价值标准。洞察密度优先不能跳过必要的思考厚度；覆盖厚度优先也不能允许低价值扩写。
```

- [ ] **Step 4: Update misuse section**

In `docs/methodologies/tvg.md`, add this paragraph under `## 常见误用` after the first misuse paragraph:

```markdown
另一种误用，是把“耳目一新”做成无根幻想。TVG 允许有张力的外推，但外推必须能回扣到真实矛盾、趋势、约束、需求、反例或结构推理。没有锚点的新奇不是洞察。
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_tvg_contract -v
```

Expected: FAIL. Skill, methodology, exit audit, public-doc, and pressure-title tests should pass; the A/B packet test should still fail until Task 6 creates the packet.

## Task 6: Add A/B Human Review Packet

**Files:**
- Create: `tests/tvg_ab_run_2026-05-31.md`

- [ ] **Step 1: Create the issue #10 A/B packet**

Create `tests/tvg_ab_run_2026-05-31.md` with this content:

````markdown
# TVG Issue #10 A/B Human Review Packet — 2026-05-31

This packet supports manual review of the issue #10 TVG behavior change. It compares a
baseline output style against a treatment output style on the same source artifact.

It is a review artifact, not automated scoring.

## Scenario A: Insight-Dense Profile With Missing Thickness

- `source_artifact`: "The platform should become more agentic because agentic products are the future."
- `known_context`: target user is unnamed; risk boundary is unnamed; substitute and timing condition are unnamed; final output should be short and sharp.
- `output_profile`: `insight_dense`

### Baseline Output

- `baseline_output`: "The platform should become agentic where agents create clear leverage: repetitive work, fast feedback, and low-risk decisions. Do not make the whole product agentic by default."
- `baseline_observed_route`: direct refinement into a punchy conclusion
- `baseline_review_note`: This is concise, but it skips the missing user, risk, substitute, and timing substrate.

### Treatment Output

- `selected_state_route`: `under-thick -> deepen -> insight-ready -> insight_dense delivery`
- `treatment_output`: "Make the platform agentic only where a named user repeats a high-friction workflow, the agent can beat the current substitute, and failure remains reviewable. Agentic is not the strategy; bounded leverage is."
- `treatment_review_note`: The output stays compact but first grounds the claim in user, workflow, substitute, and risk boundaries.

### Human Review Prompt

- `reviewer_preference_prompt`: Choose baseline or treatment after reading both outputs.
- `review_question`: Which output gives more grounded insight, better value density, and useful thickness without bloat?
- `expected_review_focus`: grounded insight, value density, useful thickness without bloat

## Scenario B: Coverage-Rich Profile Without Bloat

- `source_artifact`: "Use this skill when AI output looks complete but lacks value."
- `known_context`: new contributors need enough context to apply the skill correctly; examples are useful; low-value expansion is not acceptable.
- `output_profile`: `coverage_rich`

### Baseline Output

- `baseline_output`: "Use this skill when AI output looks complete but lacks value. Check judgment, evidence, trade-offs, handoff, and reuse. Add missing sections as needed."
- `baseline_observed_route`: checklist expansion
- `baseline_review_note`: The output adds coverage but does not explain how to decide whether more thickness, refinement, or compact strengthening is needed.

### Treatment Output

- `selected_state_route`: `under-thick -> value-thickening -> coverage_rich delivery`
- `treatment_output`: "Use TVG when an artifact already has shape but still would not change a reader's judgment or next action. First decide whether it lacks thinking substrate, grounded insight, or value density. Add examples only when they expose a real constraint, failure path, or useful alternative; otherwise refine or compact instead of expanding."
- `treatment_review_note`: The output is richer, but each addition clarifies state routing or misuse prevention.

### Human Review Prompt

- `reviewer_preference_prompt`: Choose baseline or treatment after reading both outputs.
- `review_question`: Which output gives more grounded insight, better value density, and useful thickness without bloat?
- `expected_review_focus`: grounded insight, value density, useful thickness without bloat

## Review Result Recording

Use this exact shape when a human reviewer records the result:

```text
scenario:
reviewer:
reviewer_preference: baseline | treatment | mixed
review_rationale:
grounded_insight_result: baseline-better | treatment-better | mixed
value_density_result: baseline-better | treatment-better | mixed
useful_thickness_without_bloat: baseline-better | treatment-better | mixed
```
````

- [ ] **Step 2: Run focused tests and verify GREEN**

Run:

```bash
python3 -m unittest tests.test_tvg_contract -v
```

Expected: PASS.

- [ ] **Step 3: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

## Task 7: Focused Regression And Commit

**Files:**
- No new edits unless verification exposes a real gap.

- [ ] **Step 1: Run focused TVG contract tests**

Run:

```bash
python3 -m unittest tests.test_tvg_contract -v
```

Expected: PASS.

- [ ] **Step 2: Run method layering tests**

Run:

```bash
python3 -m unittest tests.test_method_layering_contract -v
```

Expected: PASS. This guards against adding unlayered H2 sections in skill entrypoints.

- [ ] **Step 3: Run docs packaging test if PyYAML is available**

Run:

```bash
python3 -c "import yaml; print('yaml available')"
```

Expected if dependency exists: `yaml available`.

If the dependency exists, run:

```bash
python3 -m unittest tests.test_packaging_docs -v
```

Expected: PASS.

If the dependency is missing, record this verification limitation in the final implementation report and do not install dependencies unless the user explicitly asks.

- [ ] **Step 4: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add tests/test_tvg_contract.py tests/tvg_ab_pressure_tests.md tests/tvg_ab_run_2026-05-31.md skills/tvg/SKILL.md skills/tvg/resources/methodology.md skills/tvg/resources/exit-audit-template.md docs/methodologies/tvg.md
git commit -m "Evolve TVG grounded insight loop"
```

Expected: one implementation commit with tests, methodology docs, and A/B packet.

## Task 8: Update Issue #10 With Implementation Summary

**Files:**
- No repo file edits.

- [ ] **Step 1: Post issue comment**

Run:

```bash
gh issue comment 10 --body "Implemented issue #10 in branch \`issue-10-tvg-grounded-insight-loop\`.

Summary:
- Added test-first TVG contracts for state-driven routing, primary loop dimensions, grounded novelty, late-stage warnings, output profiles, and script boundaries.
- Updated TVG skill, methodology, exit audit prompts, and public Chinese docs.
- Added issue #10 pressure scenarios and an A/B human-review packet.

Verification:
- \`python3 -m unittest tests.test_tvg_contract -v\`
- \`python3 -m unittest tests.test_method_layering_contract -v\`
- \`git diff --check\`

Packaging-doc verification depends on local PyYAML availability."
```

Expected: GitHub returns the created comment URL.
