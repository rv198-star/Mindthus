# Mindthus Judgment Kernel Issues Design

Status: approved issue-first design for implementation planning
Date: 2026-05-26

## Goal

Mindthus should become a sharper analysis and judgment skill layer, not a memory
product, retrieval system, or universal workflow gateway.

The immediate goal is to design a set of issue-first work slices for the 6+1 judgment
capability target:

1. Intervention judgment
2. Judgment object recognition
3. Judgment constraint recognition
4. Pressure testing
5. Method arbitration
6. Execution impact
7. Context injection point

This document is not a release roadmap. Version labels may be used later only after a
coherent group of issues has been completed and verified.

## Baseline

Mindthus already has useful method skills:

- `3L5S` for problem discovery, definition, and decomposition.
- `SELA` for long-term system efficiency versus local advantage.
- `EDSP` for structural ambiguity, malformed binaries, and scenario projection.
- `WAE` for workflow, agentic judgment, and evidence control boundaries.
- `TVG` for bounded artifact value deepening.
- `tplan` for Mission-level runtime state, evidence, and stopping discipline.
- `Anti-Spiral` for repeated local repair loops.

The current `Cognitive Primitives` extraction is also valid. It centralizes repeated
cross-cutting guardrails such as Minimal Sufficient Lens, Evidence / Claim Ceiling,
Perspective Pressure, Anti-Spiral, and No Abstract Jargon Wall.

However, that extraction is architecture hygiene. It does not by itself upgrade
Mindthus' original analysis and judgment capability.

## Target

Mindthus should help an agent answer:

- Does this task need Mindthus, or should the base model directly answer or execute?
- Is the missing input facts, context, data, runtime proof, or user clarification?
- If Mindthus should intervene, what is the active judgment object?
- What constrains this judgment: facts, values, interests, emotion, risk, authority, or
  injected context?
- Does the judgment need pressure testing?
- If multiple methods seem applicable, which one dominates, defers, degrades, blocks,
  or stops?
- Did the judgment change downstream strategy, risk handling, evidence requirements,
  next action, or stopping conditions?

The target is a sharper judgment layer for downstream agent work. It is not a complete
cognitive memory system and does not implement storage, retrieval, ranking, or profile
management.

## Non-Goals

- Do not create a full meta-framework above all skills.
- Do not make `3L5S` a universal entry point.
- Do not make `TVG` or `tplan` proactively activate for ordinary work.
- Do not implement memory, retrieval, context ranking, or a user profile store.
- Do not turn evidence into the only legitimate constraint on judgment.
- Do not add a full game-theory skill.
- Do not force all work into a version-scoped roadmap before the issues are clear.

## Design Principles

### Issue First, Release Later

Work should be captured as focused issues. A version boundary should be chosen only
after completed issues form a coherent release theme.

### Use Mindthus Less, But Better

The entry layer should route more tasks away from Mindthus when direct execution,
information gathering, or user clarification is the correct next move.

### Diagnose Before Routing

`using-mindthus` should not jump from user text to skill name. It should first identify
whether the task needs Mindthus, then identify the judgment object, then route.

### Constraints Are Not Only Evidence

Evidence constrains factual claims. It should not erase values, interests, emotional
signals, risk posture, authority boundaries, or explicit user preferences.

### Context Is An Interface

Mindthus may receive relevant contextual constraints from an upstream platform, but it
does not own memory. Injected context must remain a judgment input, not an override of
the user's current instruction.

### Output Must Affect Execution

A judgment that sounds coherent but does not change downstream strategy, risk handling,
evidence requirements, next action, or stopping conditions is not enough.

## Capability Model

### 1. Intervention Judgment

Purpose: decide whether Mindthus should intervene at all.

Routes:

- Direct execution: the task is clear, low-risk, bounded, and facts are sufficient.
- Information acquisition: facts, files, data, runtime proof, or user clarification are
  missing.
- Mindthus intervention: the task contains a hard judgment point.

Acceptance signal: simple tasks should not trigger method ceremony, and insufficient
facts should not produce confident method conclusions.

### 2. Judgment Object Recognition

Purpose: identify what kind of judgment is active before selecting a skill.

Initial judgment objects:

- Problem-definition failure -> `3L5S`
- False binary or structural ambiguity -> `EDSP`
- Long-term system efficiency versus local advantage -> `SELA`
- Workflow / agentic / evidence control mismatch -> `WAE`
- Bounded artifact with thin practical value -> `TVG`
- Mission runtime state, evidence, continuation, or stopping problem -> `tplan`
- Repeated local repair or add-layer spiral -> `Anti-Spiral`

Acceptance signal: routing tests should verify both positive triggers and do-not-trigger
boundaries.

### 3. Judgment Constraint Recognition

Purpose: identify what has legitimate force over the current judgment.

Constraint types:

- Facts and evidence
- User values and preferences
- Interests, incentives, and stakeholder positions
- Emotional signals
- Risk posture and reversibility
- Authority and permission boundaries
- Injected context from an upstream platform

Acceptance signal: tests should prevent two opposite failures: treating value judgments
as factual claims, and letting emotion or preference masquerade as fact.

### 4. Pressure Testing

Purpose: challenge non-trivial judgments before accepting a clean conclusion.

Existing surfaces:

- `SELA`: `System Advocate`, `Local Defender`, `Timing Auditor`
- `EDSP`: `Builder`, `Challenger`, `Synthesizer`
- `TVG`: failure, alternative, evidence, and downstream pressure
- `Anti-Spiral`: repeated-touch and weak-evidence brake

Needed refinement: keep game-theoretic and incentive concerns as pressure surfaces, not
as a standalone game-theory method.

Acceptance signal: non-trivial cases gain useful challenge pressure; low-risk or
deterministic cases do not pay role or process overhead.

### 5. Method Arbitration

Purpose: decide what happens when multiple Mindthus methods appear applicable.

Initial arbitration actions:

- `dominate`: one method owns the main judgment.
- `defer`: a method waits for another method to resolve a prerequisite.
- `degrade`: a method produces a weaker claim because constraints are insufficient.
- `block`: a method prevents another method from making an over-strong conclusion.
- `stop`: Mindthus should not continue; direct execution, evidence acquisition, user
  clarification, or handoff is required.

Known conflict cases:

- `TVG` wants another value pass while `Anti-Spiral` detects local repair.
- `SELA` sees long-term efficiency while `WAE` restricts immediate action because of
  risk or irreversibility.
- `EDSP` creates a structural direction while factual evidence is still too weak for a
  confident claim.
- `3L5S` requests more problem definition while the user already supplied a sufficient
  target and wants execution.

Acceptance signal: conflict cases should produce a clear owner, downgrade, block, or
stop decision, not a stack of methods.

### 6. Execution Impact

Purpose: require judgments to affect downstream work.

A useful Mindthus judgment should change at least one of:

- strategy
- risk handling
- evidence requirement
- next action
- stopping condition
- method choice
- handoff packet

Acceptance signal: pressure tests should score whether the judgment changes execution,
not only whether it sounds coherent.

### 7. Context Injection Point

Purpose: reserve an interface for upstream platforms to provide relevant background
constraints without making Mindthus a memory system.

Suggested context packet fields:

- `current_goal`
- `user_preference`
- `long_term_objective`
- `role_or_stake`
- `prior_experience`
- `risk_posture`
- `emotional_signal`
- `authority_boundary`
- `fresh_context`

Rules:

- Current user input takes priority over older context.
- Injected context may constrain judgment but must not silently override the user's
  current instruction.
- Context must be labeled by function: fact, preference, value, interest, emotional
  signal, risk, authority, or project background.
- If injected context conflicts with current input, the conflict must be surfaced.
- If no context packet exists, Mindthus should still work from current visible context.

Acceptance signal: docs explain what upstream platforms may inject, but no Mindthus
runtime memory or retrieval implementation is added.

## Work Items

### Issue 1: Mindthus Intervention Boundary

Implement a clear entry boundary in `using-mindthus` and project instructions.

Scope:

- Add direct execution, information acquisition, and Mindthus intervention paths.
- Make "do not use Mindthus" a first-class valid decision.
- Preserve Minimal Sufficient Lens.

Acceptance:

- Router contract tests cover simple direct tasks.
- Router contract tests cover missing-facts tasks.
- Router contract tests cover genuine hard judgment points.

### Issue 2: Judgment Object Routing

Add a lightweight judgment-object diagnostic before skill routing.

Scope:

- Add the initial object list.
- Link each object to its default skill or action.
- Include do-not-trigger boundaries for `TVG` and `tplan`.

Acceptance:

- Tests verify positive and negative routing for each object.
- `TVG` requires a bounded artifact.
- `tplan` requires Mission-level runtime state or long-task control needs.

### Issue 3: Context Injection Point

Document a context constraint input shape for upstream platforms.

Scope:

- Add suggested context packet fields.
- State that Mindthus does not implement memory or retrieval.
- Define conflict and precedence rules.

Acceptance:

- Docs distinguish injected context from current user instruction.
- Tests or documentation contracts prevent claims that Mindthus stores or retrieves
  memory.

### Issue 4: Judgment Constraint Recognition

Expand constraint handling beyond evidence ceilings.

Scope:

- Describe facts, values, interests, emotion, risk, authority, and context constraints.
- Clarify which constraints can support factual claims and which support preferences,
  priorities, or action choices.

Acceptance:

- Pressure cases show values and emotions can legitimately influence decisions.
- Tests prevent unsupported factual claims from hiding behind values or emotion.

### Issue 5: Method Arbitration Rules

Define lightweight cross-method conflict actions.

Scope:

- Add `dominate`, `defer`, `degrade`, `block`, and `stop`.
- Add example conflicts and expected resolutions.

Acceptance:

- Tests cover SELA vs WAE, TVG vs Anti-Spiral, EDSP vs evidence limits, and 3L5S vs
  direct execution.

### Issue 6: Execution Impact Requirement

Require Mindthus judgments to change downstream execution.

Scope:

- Define execution-impact surfaces.
- Update pressure tests to score downstream effect, not just textual coherence.

Acceptance:

- At least one pressure case fails if output is coherent but does not change strategy,
  evidence, risk, next action, or stop condition.

### Issue 7: Pressure Surface Consolidation

Audit and consolidate pressure surfaces after the first six issues.

Scope:

- Keep existing SELA / EDSP multi-role pressure.
- Keep game-theoretic and incentive checks as pressure surfaces.
- Avoid adding a standalone game-theory skill unless repeated real cases prove it is
  necessary.

Acceptance:

- Existing multi-role tests still pass.
- Low-risk deterministic cases still skip pressure overhead.
- Shared primitive docs remain concise and do not become a new method layer.

## Recommended Execution Order

First batch:

1. Issue 1: Mindthus Intervention Boundary
2. Issue 2: Judgment Object Routing
3. Issue 3: Context Injection Point

Second batch:

4. Issue 4: Judgment Constraint Recognition
5. Issue 5: Method Arbitration Rules
6. Issue 6: Execution Impact Requirement

Final cleanup:

7. Issue 7: Pressure Surface Consolidation

This order improves the entry boundary first. It also avoids using pressure,
arbitration, or execution-impact rules before Mindthus knows whether it should
intervene and what object it is judging.

## Verification Strategy

Use contract tests and pressure tests rather than subjective release claims.

Expected test surfaces:

- `tests/test_mindthus_router_contract.py`
- `tests/mindthus_router_pressure_tests.md`
- targeted tests for new context-injection and arbitration wording
- existing SELA / EDSP / TVG / WAE / tplan contract tests

The main negative assertions should be as important as the positive assertions:

- do not trigger Mindthus for simple tasks
- do not conclude when facts are missing
- do not trigger `TVG` without a bounded artifact
- do not trigger `tplan` for ordinary complexity
- do not let injected context silently override current user input
- do not let values or emotion assert factual claims without support

## Open Questions

- Should the first batch be implemented entirely in `using-mindthus`, or should
  `AGENTS.md` carry the same route table in shortened form?
- Should context injection be documented only in `using-mindthus`, or also in
  `docs/methodologies/shared-primitives.md` as a cross-cutting interface?
- Should method arbitration live in `using-mindthus`, or should it become a separate
  methodology resource once it grows beyond a lightweight rule set?
