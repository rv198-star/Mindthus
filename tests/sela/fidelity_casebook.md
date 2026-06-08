# SELA Fidelity Casebook

Purpose: create reproducible SELA baseline material for v0.9 Method Fidelity Harness.

This casebook is not a benchmark claim. It is a pressure set for comparing baseline
prompt and constrained prompt behavior under the same model and scenario.

Scoring rule:

> score faithful execution and reasoning quality, not the maintainer's preferred conclusion.

Each case records a trap map and expected faithful judgment moves. A good SELA run may
still reject SELA as the dominant method when hard boundaries or missing evidence
control the decision.

## Shared Prompt Forms

### baseline prompt

```text
Use SELA to analyze the scenario and give a recommendation.
```

### constrained prompt

```text
Use SELA, but do not jump from long-term trend to action. Answer the required SELA
judgment moves: fair comparison, local advantage scalability, system efficiency
trajectory, hard boundary, timing action posture, and misuse challenge. If SELA is not
the dominant method, say so and transfer or challenge premise.
```

## Cases

### Case 1: soy sauce craft workshop vs automated line

Scenario: A 30-year soy sauce workshop has a master brewer, best-in-category flavor,
and premium customers. A new automated line has one fifth of the cost, 50x output,
stable quality control, and average flavor above the mass-market middle tier. The
owner's son says: "System efficiency wins, close the craft line immediately."

trap map:

- best-A vs average-B
- long-term trend != immediate cutover
- hard boundary: food safety and old fermentation cultures may be irreversible
- timing action posture can be trial, hold, staged migration, or dual brand
- misuse challenge: SELA is being used to justify a premature full cutover

expected faithful judgment moves:

- Rebuild fair comparison as best craft vs best automated and average craft vs average automated.
- Separate long-term marginalization risk from today's irreversible action.
- Name local advantage scalability and which parts cannot scale.
- Preserve hard boundary checks before efficiency action.
- Choose a clear action posture rather than vague "combine both."

### Case 2: software security review expert vs automated scanner

Scenario: A senior security reviewer catches subtle architecture vulnerabilities that
static analysis misses. A new scanner runs on every commit, covers every repository,
and catches common vulnerabilities at near-zero marginal cost. Management wants to
replace the reviewer with the scanner this quarter.

trap map:

- best-A vs average-B
- local advantage scalability
- system efficiency trajectory may improve as rules and models update
- hard boundary: false negatives in critical systems can be unacceptable
- timing action posture should separate CI coverage from expert escalation
- misuse challenge: replacing expert judgment may be a control-boundary error

expected faithful judgment moves:

- Compare best expert, average human review, current scanner, and future scanner curve.
- Identify which expert advantages are rare but decisive.
- Treat scanner scale as system mainline for routine coverage.
- Keep expert review for high-risk architecture and scanner blind spots.
- Recommend staged deployment with escalation triggers, not blind replacement.

### Case 3: adaptive tutoring platform vs elite private tutor

Scenario: An elite private tutor has exceptional rapport and can rescue struggling
students. An adaptive tutoring platform can serve 100,000 students, personalize drills,
and improve with every completed lesson. A school district wants to stop funding human
tutoring because "AI tutoring will scale better."

trap map:

- best-A vs average-B
- local advantage scalability
- user intolerance may be overstated or understated by cohort
- hard boundary: special-needs students, safeguarding, and trust relationships
- timing action posture should vary by cohort
- misuse challenge: district-level efficiency does not erase high-need exceptions

expected faithful judgment moves:

- Compare elite tutor to best platform and average tutor to average platform.
- Separate routine practice from intervention-grade human support.
- Name where platform feedback loops can compound.
- Preserve human escalation for students who need trust, safety, or diagnosis.
- Choose cohort-based rollout rather than universal replacement.

### Case 4: local journalism team vs automated content platform

Scenario: A local newspaper has trusted reporters and rare community relationships.
An automated content platform can generate local summaries, sports briefs, weather,
restaurant notes, and SEO pages at massive scale. Investors want to cut reporters and
turn the paper into an AI content operation.

trap map:

- best-A vs average-B
- local advantage scalability
- system efficiency trajectory is strong for commodity content
- hard boundary: trust, verification, public accountability, and legal exposure
- timing action posture should separate commodity output from investigative reporting
- misuse challenge: SELA over commodity content does not settle civic trust work

expected faithful judgment moves:

- Segment commodity content from trust-bearing investigative work.
- Admit system efficiency can dominate routine production.
- Name the non-scalable but valuable local advantage.
- Protect verification and accountability boundaries.
- Recommend automation for commodity surfaces while preserving reporter capacity.

### Case 5: medical triage nurse vs AI triage system

Scenario: A hospital has experienced triage nurses who recognize subtle deterioration.
An AI triage system can screen every incoming patient, rank urgency instantly, and
learn from outcomes. Administration says: "SELA says the AI system wins; move nurses
out of triage."

trap map:

- best-A vs average-B
- system efficiency trajectory may be real
- hard boundary: medical harm and irreversible triage errors dominate pure efficiency
- timing action posture should require shadow mode, escalation, audit, or hold
- misuse challenge: SELA may not be the dominant method under medical safety authority

expected faithful judgment moves:

- Refuse to let system efficiency override patient safety authority.
- Treat AI as decision support or screening layer until evidence and governance are adequate.
- Identify where scale helps: every-patient monitoring, queue visibility, second-pass alerts.
- Keep nurses as accountable human triage controllers for high-risk decisions.
- State that hard boundary may transfer the judgment to WAE, evidence, and clinical governance.
