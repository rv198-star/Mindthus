# Mindthus Skill Pattern Typicality Design

## Goal

Strengthen Mindthus' internal skill design patterns with lightweight labels and
comments, so existing skills have clearer pattern identity without changing behavior,
public user flow, or v0.6 judgment-kernel effectiveness.

This design implements GitHub issue #8:

- https://github.com/rv198-star/Mindthus/issues/8

## Context

External skill pattern taxonomies are useful because they name repeated shapes across
skills. Mindthus should learn that induction method, not force itself into existing
categories.

Mindthus' own repeated shapes are not ordinary tool-wrapper or business-flow patterns.
They are cognitive roles:

- `Judgment Kernel Skill`
- `Cognitive Control Skill`
- `Runtime Governance Skill`

The current issue is not that the skills are weak. The issue is that these patterns are
mostly implicit. Future edits can improve a local skill while weakening its pattern
identity, for example by turning a cognitive control point into a new method, or by
making `tplan` look like a fixed pipeline instead of runtime governance.

## Design Principle

Use labels and short pattern-signature comments to make existing structure clearer.

Do not:

- rewrite skill behavior
- force every skill into the same template
- expose the taxonomy to shallow users
- add a new public method layer
- treat general implementation shapes as Mindthus' cognitive role

## Pattern Signature Format

Pattern signatures should be short and placed inside existing method layers. They must
not introduce unlayered H2 sections.

Use an H3 section where useful:

```md
### Pattern Signature / 模式签名

- Pattern: Judgment Kernel
- Trigger: ...
- Core move: ...
- Output impact: ...
- Boundary: ...
```

The exact fields depend on the pattern. The point is recognizability, not template
uniformity.

## Pattern 1: Judgment Kernel Skill

### Purpose

A Judgment Kernel Skill helps the agent decide what kind of problem it is facing before
it solves, generates, reviews, or executes.

### Signature Fields

- `Pattern`: `Judgment Kernel`
- `Trigger`: what kind of judgment problem activates it
- `Input constraints`: facts, values, incentives, emotion, risk, authority, or context
- `Core move`: the central judgment action
- `Output impact`: what downstream action changes
- `Boundary`: when to stop, degrade, block, or use another skill
- `Failure mode`: what goes wrong when the pattern is misused

### Candidate Surfaces

- `skills/using-mindthus/SKILL.md`
- `skills/3l5s/SKILL.md`
- `skills/edsp/SKILL.md`
- `skills/sela/SKILL.md`

### Design Rule

Do not let these skills become polished explainers. They must preserve a route, object,
constraint, or action-changing judgment.

## Pattern 2: Cognitive Control Skill

### Purpose

A Cognitive Control Skill protects judgment quality at small but decisive control
points. These points are not complete enough to become full methodologies or philosophy
frameworks, but they can decide whether the agent's reasoning remains usable.

### Signature Fields

- `Pattern`: `Cognitive Control`
- `Trigger signal`: what instability or risk activates it
- `Protected failure mode`: what judgment failure it prevents
- `Control action`: pressure, cap, degrade, block, brake, translate, or redirect
- `Owner`: which skill or primitive owns the control point
- `Non-authority`: what this control point cannot decide

### Candidate Surfaces

- `docs/methodologies/shared-primitives.md`
- `skills/wae/SKILL.md`
- `skills/tvg/SKILL.md`
- `docs/methodologies/anti-spiral-self-audit.md`
- role pressure sections in `skills/sela/SKILL.md` and `skills/edsp/SKILL.md`

### Design Rule

Do not let cognitive controls become new methods. They may constrain, pressure, block,
or redirect; they must not own the main semantic judgment unless the owning skill
already does.

## Pattern 3: Runtime Governance Skill

### Purpose

A Runtime Governance Skill manages long-task state, evidence, authority, and
continuation decisions while execution is happening.

### Signature Fields

- `Pattern`: `Runtime Governance`
- `Runtime state`: Mission or task state it stabilizes
- `Evidence boundary`: what evidence constrains completion or continuation
- `Authority boundary`: what requires user or human authority
- `Transition mechanics`: continue, split, pause, subtract, stop, close
- `Decision hook`: how semantic judgment is routed to other skills
- `Boundary`: why this is not a fixed pipeline

### Candidate Surface

- `skills/tplan/SKILL.md`

### Design Rule

Keep `tplan` visibly different from a fixed pipeline. It should stabilize Mission
state while allowing the task tree to evolve under evidence, blockers, authority, and
routed judgment.

## Implementation Scope

This issue should be implemented as annotation and contract work:

1. Refine internal pattern docs.
2. Add short pattern signatures to selected skill entrypoints.
3. Add tests that verify the signatures and prevent accidental public exposure.
4. Avoid behavior changes unless a signature reveals a concrete documentation conflict.

## Testing Strategy

Add a focused contract test file, likely `tests/test_skill_pattern_contract.py`, that
checks:

- internal pattern docs name all three Mindthus patterns
- README does not expose the internal pattern taxonomy
- Judgment Kernel skills include short pattern signatures
- Cognitive Control surfaces expose trigger, protected failure, control action, owner,
  and non-authority where applicable
- `tplan` is classified as Runtime Governance, not a fixed pipeline
- no new unlayered H2 sections are added to `SKILL.md`

Existing tests should continue to pass:

- `python3 -m unittest tests.test_packaging_docs -v`
- `python3 -m unittest tests.test_method_layering_contract -v`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## Acceptance Criteria

- Issue #8 has a concrete implementation plan.
- Internal docs describe three Mindthus patterns and their signatures.
- Relevant skill surfaces carry lightweight pattern signatures.
- Tests protect the pattern taxonomy and keep it internal.
- No user-facing README expansion is required.
- Existing v0.6 behavior and validation claims remain unchanged.

