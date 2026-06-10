---
name: tvg
description: Use as a value-directed text/artifact strengthening loop when an AI-generated bounded module looks complete but must be moved closer to an explicit standard of "good" for judgment, evidence, trade-offs, downstream handoff, reuse, or action value.
---

# TVG / Thinking Value-Gain

## Core Claim

Thinking Value-Gain is a value-directed text/artifact transformation loop for AI-generated bounded modules.

Short version:

> TVG moves a bounded text or artifact closer to a defined standard of "good".

That standard comes from `expected_value`, the active `value_profile`, fixed evidence boundaries, veto constraints, and the exit gate. TVG is for artifacts that look complete, rigorous, standardized, and fluent, but are hollow, shallow, random, over-expanded, or too weak for real judgment, action, review, reuse, or handoff.

TVG is not a generic prompt trick or length expansion method. Thinking Thickness is the substrate of value, Grounded Insight Yield is the core output, and Value Density is the delivery quality.

Core inputs:

- `expected_value`: Agent input contract for what the target artifact must become useful for. It names target artifact, artifact job, useful outcome, hard constraints, evidence boundary, and output bias. Gate is an internal stop condition compiled from expected_value, not a user-facing configuration burden.
- `value_profile`: optional value definition package. If absent, use the default practical-value profile. Resolve as `default | supplied | inferred-with-warning`. A profile may define `value_semantics`, optional `realization_surface`, and optional `gain_policy`.
- `veto_constraints`: explicit unacceptable states. They are not value-gain axes; if triggered, the module must not exit as `freeze`.
- `independent_auditor`: for high-impact, high-uncertainty, or handoff-critical modules, separate generator work from the exit auditor.
- `output_profile`: `insight_dense | balanced | coverage_rich`. This is delivery bias, not an internal workflow fork; it must not lower standards for `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`.

Value profiles can specialize value axes, observable surfaces, gain policies, veto constraints, and audit prompts. They cannot override evidence honesty, claim ceilings, user constraints, safety boundaries, or hard veto constraints.

## Mainline / 主路径

### When To Use

Use when a bounded module already exists but downstream use would still require invention, judgment repair, evidence recovery, trade-off clarification, review structure, or handoff strengthening. Do not use TVG to reopen whole-project strategy or add process weight to low-risk work.

### Operating Flow

1. Name the smallest module that can be frozen, returned, or blocked.
2. Resolve `expected_value` and the active `value_profile`.
3. Compile the internal `exit_gate` from expected value, TVG bottom lines, downstream use, active profile, veto constraints, and next-round positive value.
4. Check `Thinking Thickness`, `Grounded Insight Yield`, and `Value Density`.
5. Pass the thickness gate before density optimization or `output_profile`.
6. Select value-gain axes from the default or supplied profile.
7. Run the value-gain move: `deepen`, targeted depth formation, `refine`, `compact-strengthen`, warning calibration, `return-remediate`, `blocked`, or `freeze`.
8. Apply `output_profile` only as exit-side graded refinement.
9. For high-impact, high-uncertainty, or handoff-critical modules, use an independent exit audit.
10. Validate and persist trace shape when useful; make the exit decision by agentic audit, not script output.

## Guardrails / 从属补漏

### Hard Boundary

Scripts support bookkeeping only. They may initialize traces, validate required fields, persist records, and report factual completeness issues. They must not replace agentic judgment.

Scripts must not create, waive, or satisfy veto constraints; decide whether another round is worth doing; write or change `exit_state`; decide whether independent auditor separation is required; output `PASS` as an audit verdict; score `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`; choose TVG state routes; choose `output_profile`; decide whether `expected_value` is correct or complete; choose, infer, complete, rank, or satisfy `value_profile`; decide default gate correctness or exit gate success; decide whether `realization_surface` fit or `gain_policy` success was achieved; decide whether a prompt, document, design, or handoff artifact reached the user's quality target; decide whether a value profile is true, complete, aesthetically successful, thick enough, or sufficient for exit; decide `compact-strengthen`, `refine`, `deepen`, or `freeze`.

Every script result means only:

> `No schema violations were detected; agentic audit is still required.`

### Value Profile Boundary

Default practical-value profile is the fallback. Supplied profiles may specialize what "good" means and how improvement should show up, but optional layers must not turn TVG into a domain-specific workflow. Inferred profiles must be marked `inferred-with-warning`, and profile source conflicts with the artifact being improved should be treated as contamination risk.

Scripts validate profile shape only and must not decide whether a value profile is true, complete, aesthetically successful, thick enough, or sufficient for exit.

### Common Mistakes

- Treating schema validation as audit completion.
- Running TVG on an unbounded document instead of a named module.
- Adding another round without a named positive-value hypothesis.
- Running a default TVG pass without making the expected output value visible.
- Inferring a specialized value profile from the flawed artifact sample.
- Treating loop-assisted artifact success as proof that the profile itself is strong.
- Exposing TVG internal vocabulary in final customer/business/architecture deliverables.

### Runtime Support

Full method: `resources/methodology.md`. Audit template: `resources/exit-audit-template.md`. Trace schema: `resources/trace-record-schema.json`. Value profile construction: `resources/value-profiles/profile-construction.md`.

Trace scripts: `python3 skills/tvg/scripts/trace/init.py`, `python3 skills/tvg/scripts/trace/validate.py`, and `python3 skills/tvg/scripts/trace/persist.py`.

Fidelity support: use `resources/fidelity-contract.md`, `templates/fidelity-output.json`, and `scripts/validate_tvg_output.py`; this is a fidelity contract shape check, not semantic approval.

## Boundaries / 边界

- Do not deepen for length, polish, or template completeness.
- Do not require a supplied `value_profile` for ordinary tasks.
- Block rather than deepen when missing input is evidence, domain input, runtime proof, or stakeholder judgment.
