---
name: wae
description: Use when workflow, script, agent judgment, schema, review, or evidence may be controlling the wrong part of the work, especially when the control boundary is unclear or clean structure hides thin judgment.
---

# WAE / Workflow-Agentic-Evidence

## Core Claim / 核心判断

Workflow should control order. Agentic reasoning should resolve uncertainty and deepen judgment. Evidence should connect claims to observable proof.

Automation solves deterministic problems. Intelligence solves uncertain problems.

WAE is a control-boundary lens. It answers:

> Who or what should control this part of the work?

It is not a generic workflow designer, and it is not a four-quadrant form to fill mechanically. Its value is in catching control mismatch:

- workflow freezes truth that is still uncertain
- agentic loops drift without evidence or exit criteria
- evidence exists but does not constrain claims
- schemas make judgment look complete while the real uncertainty remains unresolved

## When To Use / 使用场景

Use this skill when:

- deciding whether to use scripts, schemas, prompts, agents, or human review
- a workflow may be freezing uncertain truth too early
- an LLM-filled structure looks clean but may be judgment-thin
- a claim needs proof, confidence caps, or review-bound items
- repeated mechanical verification should be separated from semantic judgment

Do not use it to slow down low-risk formatting or obviously deterministic work.

## Operating Flow / 判断顺序

1. Estimate `workflow certainty`: how fixed are path, order, and execution method?
2. Estimate `context certainty`: how complete and trustworthy are facts, semantics, constraints, and runtime truth?
3. Choose the controlling layer:
   - high workflow certainty + high context certainty -> workflow-heavy execution
   - high workflow certainty + low context certainty -> fixed workflow with agentic semantic completion
   - low workflow certainty + high context certainty -> agentic planning with workflow as outer contract
   - low workflow certainty + low context certainty -> bounded agentic loop with evidence acquisition
4. Add evidence bridges where claims need proof or confidence caps.

## Hard Boundary / 硬边界

Scripts may enforce order, deterministic transforms, mechanical checks, and state recording.

Scripts must not decide high-uncertainty truth, erase meaningful ambiguity, or replace judgment with field completion.

If a WAE output becomes cleaner but thinner, treat that as a regression.

## Worksheet

Use `templates/control-boundary-worksheet.md` when a concrete work item needs a lightweight control-boundary analysis.

The worksheet is an aid for judgment, not evidence that the judgment is correct.

## Full Method

Read `resources/methodology.md` when you need quadrants, boundary questions, hard rules, anti-patterns, or the practical decision table.
