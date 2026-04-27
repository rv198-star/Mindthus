# WAE / Workflow-Agentic-Evidence Control Boundary

## Purpose

This method defines how to decide whether work should be controlled by deterministic workflow, agentic judgment, or evidence bridging.

Short names:

- `Workflow / Agentic` when the evidence layer is implied
- `Workflow / Agentic / Evidence` when precision matters

It answers one question:

> Who or what should control this part of the work?

Use it when there is a control-rights dispute inside the work:

- a script may be deciding something that still requires semantic judgment
- an agent may be improvising something that should be deterministic
- a review step may be approving claims without evidence
- a schema may be making uncertain truth look complete

Do not turn WAE into a ceremony. Its job is to preserve the right kind of control, not to make every task more complicated.

## Core Claim

`Workflow` should control order.

`Agentic` should resolve uncertainty and deepen judgment.

`Evidence` should connect claims to observable proof.

The three layers are complementary, not interchangeable.

## Core Variables

Evaluate work on two independent variables:

1. `Workflow certainty`: how fixed the task path, order, and execution method already are
2. `Context certainty`: how complete and trustworthy the facts, semantics, constraints, and runtime truth already are

Short rule:

> Automation solves deterministic problems.
>
> Intelligence solves uncertain problems.

## Four Control Quadrants

### High workflow certainty + high context certainty

Use workflow-heavy execution. Prefer deterministic transforms, gates, packaging, state recording, and repeatable verification.

Typical cases:

- known input/output conversion
- formatting, packaging, indexing, counting, sorting
- repeatable tests or smoke checks
- artifact assembly where the semantics are already settled

### High workflow certainty + low context certainty

Keep workflow order fixed, but let agentic judgment complete semantics, retrieve missing facts, correct understanding, and expose uncertainty. Do not pretend templates can replace missing truth.

Typical cases:

- a fixed review checklist applied to a domain-specific artifact
- a skill or spec template whose fields require real interpretation
- a workflow where evidence must be gathered before claims are accepted

### Low workflow certainty + high context certainty

Let agentic planning choose the path. Use workflow only as an outer contract and convergence frame.

Typical cases:

- facts are known but the best route is not obvious
- several implementation or product paths can work
- trade-offs and sequencing matter more than mechanical completion

### Low workflow certainty + low context certainty

Use bounded agentic loops with evidence acquisition. Allow search, inspection, dynamic planning, tool use, and revision. Do not allow fake certainty, blind looping, or open-ended drift.

Typical cases:

- unclear incident, unclear root cause, unclear fix
- exploratory research with changing hypotheses
- ambiguous strategy or product judgment under incomplete evidence

The loop must have purpose, evidence surfaces, confidence caps, and exit criteria.

## Control Layers

### Workflow Shell

The workflow shell owns entry/exit contracts, deterministic transforms, hard gate checks, state recording, evidence aggregation, assembly, repeatable verification, and process order.

It should not generate high-uncertainty content truth.

### Agentic Core

The agentic core owns semantic understanding, scenario selection, trade-off comparison, path planning under ambiguity, uncertainty reduction, anti-demo review, targeted rewrite, adversarial self-check, and judgment under incomplete context.

It should not be replaced by field completion when truth is uncertain.

### Evidence Bridge

The evidence bridge owns proof surfaces, traceability, runtime or observational evidence, review-bound items, confidence caps, unresolved assumptions, and contradiction surfacing.

It should not be used as theater. Evidence that does not constrain claims is decoration.

## Boundary Questions

1. Is this reducing mechanical cost, or freezing a thinking process?
2. Is this enforcing a floor, or replacing judgment?
3. Is the uncertainty mainly about path, or mainly about truth?
4. Would a script make the output more reliable, or merely more uniform?
5. If the output becomes cleaner but thinner, would we catch that regression?
6. What evidence would prove that this control choice improved the result?
7. If this method is followed exactly, will the applied output become more valuable, or just more compliant?

If the answer is "more compliant but not more valuable," the control layer is probably wrong.

## Script-Control Rule

Use scripts when the task is deterministic, repeatable, mechanically checkable, stateful in a way humans/LLMs forget, expensive to repeat manually, or dangerous to leave inconsistent.

Do not use scripts to decide product truth, choose strategy under uncertainty, erase domain language, collapse meaningful ambiguity into fields, make high-uncertainty reasoning look objective, or substitute for review judgment.

For WAE itself, script assistance should be treated with extra suspicion. WAE exists partly to prevent workflow from overreaching. A script may help scan obvious risk language, but it should not decide the control boundary.

Prefer a lightweight worksheet before any script.

## Pseudo-Agentic Drift

A schema, prompt, checklist, or contract can still behave like workflow control.

If high-uncertainty reasoning is reduced to field completion, the system is no longer using agentic judgment even if an LLM filled the fields.

Watch for cleaner but thinner outputs, more explicit but less sharp outputs, structured truth surfaces that substitute for actual truth, generic language replacing domain language, and review confidence rising while evidence depth does not.

Common signs:

- the answer fits the template but could apply to almost any domain
- uncertainty disappears because every field got filled
- evidence is listed after the conclusion but does not constrain it
- the agent says "validated" when only format or checklist completion occurred
- reviewers become more confident because the artifact looks orderly, not because the evidence is stronger

Corrective move:

> Keep the worksheet, but reopen the agentic core. Ask what judgment was actually made, what evidence constrained it, and what remains unresolved.

## Practical Decision Table

| Situation | Preferred Control |
|---|---|
| fixed transform, known input/output | Workflow |
| missing semantics, unclear truth | Agentic |
| claim needs proof or confidence cap | Evidence bridge |
| repeated mechanical verification | Workflow |
| trade-off under ambiguity | Agentic |
| runtime behavior claim | Evidence bridge + workflow verification |
| high uncertainty and high impact | bounded Agentic loop + Evidence bridge |
| low-risk formatting or packaging | Workflow |

## Evidence Bridge Quality

An evidence bridge is useful only when it can constrain a claim.

Weak evidence bridge:

- evidence is named but not connected to the claim
- proof exists only as a final appendix
- confidence is unchanged when evidence is missing
- review items do not affect approval or next action

Strong evidence bridge:

- each important claim has an observable proof surface
- missing evidence lowers confidence or blocks promotion
- assumptions and unresolved questions remain visible
- runtime or observational claims point to actual checks, logs, files, tests, or review records

## Hard Rules

1. Scripts must not dominate content truth generation in high-uncertainty work.
2. Scripts must not wash away domain language that should remain explicit.
3. If outputs become cleaner but thinner, treat that as regression.
4. Structured truth surfaces may expose missing truth, but must not substitute for judgment.
5. If outputs become more explicit but less sharp, treat that as regression.
6. Evidence must cap claims; it must not merely decorate them.
7. Agentic loops must be bounded by purpose, evidence, and exit criteria.

## Relationship To Other Methods

Use 3L5S or another problem-structuring method to identify the active signal, problem, or action.

Use this control-boundary method to decide who or what should control each part of the work.

Use a value-gain method when a bounded module looks structurally complete but still lacks practical value.

Use a system-efficiency lens when choosing between competing mainline directions.

Use WAE inside other methods when the question becomes:

> Should this part be a deterministic procedure, an agentic judgment, an evidence gate, or a human review?

WAE does not replace those methods. It assigns control for parts of them.

## Anti-Patterns

- `Workflow overreach`: deterministic process freezes uncertain truth too early.
- `Agentic drift`: agentic reasoning loops without evidence or exit criteria.
- `Evidence theater`: evidence artifacts exist but do not constrain claims.
- `Pseudo-agentic schema`: an LLM fills fields but no judgment happens.
- `Scripted confidence`: automation pass is treated as truth pass.
- `Unbounded optional lane`: uncertain work escapes all control surfaces.

## Worksheet Use

Use `../templates/control-boundary-worksheet.md` for a concrete work item.

Keep it light:

- fill only what helps the control decision
- preserve domain language
- leave uncertainty visible
- mark review-bound items explicitly

Do not treat a completed worksheet as proof that the boundary is correct.

## One-Line Rule

> Use Workflow to keep the run ordered, Agentic reasoning to resolve uncertainty, and Evidence bridge to keep claims honest.
