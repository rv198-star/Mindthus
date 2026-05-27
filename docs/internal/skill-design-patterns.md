# Mindthus Skill Design Patterns / 内部设计模式

## Status

Internal maintainer note. This document is not part of the shallow user-facing guide.

Use it when designing, reviewing, or refactoring Mindthus skills. Do not expose these
patterns as concepts a casual user must learn before using Mindthus.

## Core Claim

External skill taxonomies are useful because they show how repeated skill shapes can be
named. Mindthus should learn that induction method, not force itself into another
taxonomy.

General skill taxonomies often describe tool use, generation, review, requirement
inversion, or fixed pipelines. Mindthus needs additional patterns because its primary
job is meta-cognitive: deciding what kind of judgment is active, what should constrain
that judgment, and how the result changes downstream action.

## Pattern 1: Judgment Kernel Skill / 判断内核型 Skill

### What It Is

A Judgment Kernel Skill helps the agent decide what problem it is facing before it
solves or generates anything.

It asks:

- Should Mindthus intervene at all?
- Is the missing input facts, context, runtime proof, or user authority?
- What is the active judgment object?
- Which method owns the main judgment?
- Does the judgment change strategy, evidence requirements, next action, stopping
  condition, method choice, or handoff?

### Mindthus Examples

- `using-mindthus`: entry judgment, routing, constraints, arbitration, and execution
  impact.
- `3L5S`: problem discovery, problem definition, and executable decomposition.
- `EDSP`: structural judgment when a proposition, boundary, or binary is unstable.
- `SELA`: strategic direction when local advantage and system-level efficiency conflict.

### Boundary

This is not the same as a reviewer. A reviewer usually checks an existing artifact.
A Judgment Kernel Skill acts before the artifact or action is chosen.

## Pattern 2: Cognitive Control Skill / 认知控制型 Skill

### What It Is

A Cognitive Control Skill protects judgment quality at small but decisive control
points.

These control points are not complete enough to become a full methodology or
philosophical framework, but they can decide whether the agent's reasoning remains
usable.

It controls questions such as:

- Is one method enough?
- Is the claim stronger than the evidence?
- Is one perspective too self-consistent and in need of pressure?
- Is local repair replacing upstream progress?
- Is abstract language hiding what the decision means?
- Is clean structure freezing uncertain truth?

### Mindthus Examples

- Cognitive primitives in `docs/methodologies/shared-primitives.md`.
- `WAE` when it protects workflow, agentic judgment, and evidence boundaries.
- `Anti-Spiral` when it brakes repeated local repair.
- `TVG` veto constraints and exit audit when they stop a thin artifact from freezing.
- `SELA` / `EDSP` role pressure when a single view is too smooth.

### Boundary

This is not a fixed pipeline. A pipeline controls step order. Cognitive Control controls
judgment strength, evidence limits, perspective pressure, stopping conditions, and
expression clarity.

## Pattern 3: Runtime Governance Skill / 运行治理型 Skill

### What It Is

A Runtime Governance Skill manages long-task state, authority, evidence, and
continuation decisions while execution is happening.

It asks:

- What is the stable Mission?
- Which task is active?
- What evidence constrains completion or continuation?
- Which decision needs human authority?
- Should the task tree split, continue, pause, subtract, stop, or close?
- Which routed judgment skill should own the semantic decision?

### Mindthus Examples

- `tplan`: Mission state, task tree, evidence, decision packets, stop reports, and
  runtime hooks.
- `tplan` Anti-Spiral gate: runtime signal that local repair may have replaced Mission
  progress.
- `tplan` decision hooks that route semantic judgment to `3L5S`, `SELA`, `EDSP`,
  `WAE`, or `TVG`.

### Boundary

This is not a normal pipeline. A pipeline normally assumes the work can move through
known stages. Runtime Governance keeps the Mission stable while allowing the task tree
to evolve under evidence, blockers, authority, and routed judgment.

## Relationship To General Skill Patterns

Mindthus skills may still use common implementation shapes:

| General pattern | Mindthus usage |
|---|---|
| Tool wrapper | Scripts and resources support `tplan`, `TVG`, and `3L5S`, but scripts do not own semantic judgment. |
| Generator | Templates, decision packets, stop reports, worksheets, and traces may be generated as support artifacts. |
| Reviewer | `WAE`, `TVG`, `SELA`, and `EDSP` can review control, value, timing, or structure. |
| Inversion | `using-mindthus` and `3L5S` often ask what the real problem is before acting. |
| Pipeline | `tplan` uses runtime order and gates, but it is not a fixed business workflow. |

These general patterns describe implementation shape. The Mindthus patterns above
describe cognitive role.

## Design Rules

- Name the cognitive role before naming the implementation shape.
- Do not turn every skill into a reviewer or pipeline for consistency.
- Keep user-facing docs focused on what the skill helps the agent decide.
- Keep pattern taxonomy internal unless it directly improves user understanding.
- If a new rule is smaller than a method but repeatedly controls judgment quality,
  consider whether it belongs in cognitive primitives.
- If a new skill mainly manages state, authority, evidence, and continuation, consider
  whether it is Runtime Governance rather than a normal pipeline.

## Quick Classification

| Skill or surface | Mindthus pattern | General implementation shapes |
|---|---|---|
| `using-mindthus` | Judgment Kernel | Inversion, reviewer-like routing |
| `3L5S` | Judgment Kernel | Inversion, generator, light pipeline |
| `EDSP` | Judgment Kernel | Reviewer, generator |
| `SELA` | Judgment Kernel | Reviewer |
| `WAE` | Cognitive Control | Reviewer |
| `TVG` | Cognitive Control | Reviewer, generator |
| `tplan` | Runtime Governance | Pipeline, tool wrapper, generator |
| Cognitive primitives | Cognitive Control | Not a standalone skill pattern |

