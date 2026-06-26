# Issue Draft: Add An Agentic-System Domain Gate For WAE

> Status note: this is a repair issue spec, not current routing guidance. Broad WAE
> trigger language quoted below is preserved as counterexample context; current routing
> guidance lives in `skills/using-mindthus/SKILL.md`, `skills/wae/SKILL.md`, and
> `docs/methodologies/wae.md`.

## Title

Restrict WAE routing to agentic-system control-boundary problems

## Context

Recent usage shows a serious routing bug: `WAE` is being treated as a broad method for
any boundary, responsibility, process, governance, or evidence-related question.

That is too wide. `WAE` was intended for LLM / agent / skill / workflow / script /
schema / evidence-gate systems, where the active risk is that the wrong controller is
owning part of the work:

- workflow freezes semantic truth too early
- an agent reasons without evidence or exit criteria
- a schema or checklist makes judgment look complete
- an evidence gate records fields but does not constrain claims
- a skill, prompt, script, review step, or human gate controls the wrong layer

The current wording makes this bug easy to trigger. `WAE` is described as a
`control-boundary lens`, and `using-mindthus` routes `Control-boundary mismatch ->
wae`. Without a domain gate, agents can wrongly generalize WAE to ordinary
organizational workflows, conceptual boundaries, issue granularity, product taxonomy,
or structural A/B judgments.

## Core Principle

WAE is not a general boundary method.

It should activate only when both gates pass:

```text
Domain Gate: the object is an LLM / agent / skill / workflow / script / schema /
evidence-gate system.

Control Gate: workflow, agentic reasoning, evidence, schema, script, review, or human
authority may be controlling the wrong part of the work.
```

If the Domain Gate fails, do not use WAE even if the question contains words like
boundary, workflow, responsibility, process, evidence, control, review, or governance.

If the Domain Gate passes but there is no controller mismatch, direct execution,
information acquisition, or another Mindthus method should own the work.

## Target

Tighten WAE routing so that:

- WAE wakes for agentic production systems with controller mismatch.
- WAE does not absorb ordinary structural, conceptual, product, organization, or issue
  granularity judgments.
- EDSP remains the default owner for malformed propositions, false binaries, category
  boundaries, and structural ambiguity.
- 3L5S remains the default owner for problem-definition and task-landing failures.
- Evidence / Claim Ceiling remains a cross-cutting constraint, not a reason to route
  every evidence-adjacent question to WAE.

## Proposed Direction

### 1. Add A Domain Gate To WAE

Update `skills/wae/SKILL.md` and `docs/methodologies/wae.md` so the first trigger is
not merely "control boundary" but "agentic-system control boundary."

Candidate core wording:

```text
WAE is an agentic-system control-boundary lens. Use it only when LLMs, agents, skills,
prompts, scripts, schemas, workflows, review gates, or evidence gates may be
controlling the wrong part of the work.
```

### 2. Tighten Router Language

Update `skills/using-mindthus/SKILL.md`:

- Change `Control-boundary mismatch -> wae` to an agentic-system scoped route.
- Add a skip rule: "Do not let WAE absorb ordinary conceptual, organizational,
  product, or structural boundaries."
- Keep the existing rule that WAE must not absorb strategic or structural judgment
  merely because workflow, agents, scripts, or review appear in the prompt.

### 3. Mirror The Boundary In AGENTS

Update `AGENTS.md` so project-level guidance says:

- WAE handles Agentic / Workflow / Evidence control boundaries inside agentic systems.
- It is not the default method for all boundary, responsibility, process, or evidence
  questions.
- Category boundaries and malformed propositions should usually route to EDSP.

### 4. Add Contract Tests

Extend `tests/test_mindthus_router_contract.py` to require:

- WAE's Domain Gate wording exists in `skills/wae/SKILL.md`.
- `using-mindthus` scopes WAE to agentic-system control-boundary mismatch.
- `AGENTS.md` mirrors the narrower WAE boundary.
- The router contains a skip rule for non-agentic boundary questions.

### 5. Add Pressure Scenarios

Extend `tests/mindthus_router_pressure_tests.md` with both positive and skip cases:

- Positive: an agent workflow uses a schema checklist to approve semantic claims that
  have no evidence bridge.
- Positive: a skill/script/review gate decides truth that should remain with agentic
  judgment and evidence.
- Skip: a product taxonomy or issue granularity question asks where category boundaries
  belong; route to EDSP or direct judgment, not WAE.
- Skip: an organizational responsibility/process question has no LLM, agent, skill,
  script, schema, or evidence-gate system; do not route to WAE by default.
- Skip: a missing-data claim needs information acquisition, not WAE.

## Non-Goals

- Do not remove WAE.
- Do not make WAE LLM-only; scripts, schemas, workflows, review gates, and evidence
  gates still belong when they are part of an agentic production system.
- Do not turn WAE into a general governance, process-design, or responsibility-mapping
  method.
- Do not weaken Evidence / Claim Ceiling.
- Do not move structural ambiguity, category boundaries, or malformed propositions out
  of EDSP.
- Do not add a new method or cognitive primitive.

## Acceptance Criteria

- WAE documentation states that WAE is an agentic-system control-boundary lens.
- `using-mindthus` routes to WAE only for agentic-system control-boundary mismatch.
- `AGENTS.md` clearly says WAE is not the default method for all boundary or process
  questions.
- Router pressure tests include WAE positive cases and non-agentic boundary skip cases.
- Contract tests fail before the wording change and pass after it.
- Focused tests pass:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
python3 -m unittest tests.test_packaging_docs -v
```

## Implementation Notes

The fix should be small but strict. The important behavior change is not "use WAE
less" in the abstract. It is:

```text
No agentic system, no WAE.
No controller mismatch, no WAE.
```

This issue should be implemented as a router and method-boundary repair, not as a
rewrite of WAE's full methodology.
