---
name: tvg
description: Use as a value-driven thinking-depth enhancer when an AI-generated bounded module or artifact looks rigorous and standard but is hollow, shallow, random, or weak in judgment, evidence, trade-offs, downstream handoff, reuse, or practical decision/action value.
---

# TVG / Thinking Value-Gain

## Core Claim

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

Four core inputs keep TVG from becoming generic improvement:

- `expected_value`: Agent input contract for what the target artifact must become useful for. It can be explicit, inferred with warning, or provisional by default. It names the target artifact, artifact job, useful outcome, hard constraints, evidence boundary, and output bias. Gate is an internal stop condition compiled from expected_value, not a user-facing configuration burden.
- `value_profile`: optional value definition package for this module and use. If absent, TVG uses the default practical-value profile. A supplied profile always has `value_semantics`; advanced profiles may also define optional `realization_surface` and `gain_policy` layers so TVG knows where value should become observable and which deepening moves are preferred.
- `veto_constraints`: explicit unacceptable states for this module and use. They are not value-gain axes. If one is triggered, the module must not exit as `freeze`.
- `independent_auditor`: for high-impact, high-uncertainty, or handoff-critical modules, the exit audit should be performed by a reviewer that reads the final module, intended use, evidence, and veto constraints, not the generator's working process.

Optional delivery control:

- `output_profile`: `insight_dense | balanced | coverage_rich`. This is delivery bias, not an internal workflow fork. It may affect final expression shape, but it must not lower the standard for `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`.

Profile guardrails live in `resources/methodology.md`: `insight_dense` should preserve calibrated claim tension, `balanced` should avoid unnecessary synthetic machinery, and `coverage_rich` should preserve useful review or handoff structure.

Value profile guardrails live in `resources/methodology.md`: the default practical-value profile is the fallback, supplied profiles may specialize value semantics, observable value surfaces, gain policies, and audit prompts, inferred profiles must be marked `inferred-with-warning`, optional profile layers must not turn TVG into a domain-specific workflow, and profiles cannot override evidence honesty, claim ceilings, user constraints, safety boundaries, or veto constraints.

## Mainline / 主路径

### When To Use

Use this skill when:

- a module exists but may still be thin
- a document looks complete but downstream use would require invention
- an AI output looks rigorous but feels hollow, surface-level, or randomly assembled
- a review needs to distinguish value gain from added length
- a bounded deepening loop needs trace discipline
- a bounded module needs a value-driven depth pass before review, reuse, handoff, or exit

Do not use this skill to reopen whole-project strategy or to add process weight to low-risk work.

### Operating Flow

1. Name the smallest module that can be independently frozen, returned, or blocked.
2. Read `resources/methodology.md` only as needed.
3. Resolve `expected_value`: what the artifact must be useful for, what it must not violate,
   what evidence boundary it must preserve, and what delivery bias is expected.
4. Resolve the active `value_profile`: `default | supplied | inferred-with-warning`.
5. Compile the internal `exit_gate` / stop condition from `expected_value`, TVG bottom lines,
   module responsibility, downstream use, active profile, and next-round positive value.
6. Name any module-specific veto constraints before deepening.
7. Check the current module state using `Thinking Thickness`, `Grounded Insight Yield`,
   and `Value Density`.
8. Pass the thickness gate before applying density optimization or `output_profile`.
9. Select value-gain axes from the default profile or the supplied profile's derived axes.
10. Perform the routed value-gain action: `deepen`, targeted depth formation, `refine`,
   `compact-strengthen`, warning calibration, `return-remediate`, `blocked`, or `freeze`.
11. Apply `output_profile` only as exit-side graded refinement.
12. For high-impact, high-uncertainty, or handoff-critical modules, separate generator work from the exit auditor.
13. Validate trace shape with `scripts/trace/validate.py`.
14. Persist the trace with `scripts/trace/persist.py` when useful.
15. Make the exit decision by agentic audit, not by script output.

## Guardrails / 从属补漏

### Hard Boundary

Scripts support bookkeeping and calibration only. They must never replace agentic judgment.

Scripts may:

- initialize trace records
- validate trace shape and required fields
- persist trace records
- report factual completeness issues

Scripts must not:

- choose value-gain types or axes
- create, waive, or satisfy veto constraints
- decide whether another round is worth doing
- score value gain, demo risk, or overfitting risk
- write or change `exit_state`
- decide whether independent auditor separation is required
- promote patterns
- output `PASS` as an audit verdict
- score `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`
- choose TVG state routes
- choose `output_profile`
- decide whether `expected_value` is correct or complete
- choose, infer, complete, rank, or satisfy `value_profile`
- decide default gate correctness or exit gate success
- decide whether `realization_surface` fit or `gain_policy` success was achieved
- decide whether a thick prompt, document, design, or handoff artifact reached the user's quality target
- decide whether a value profile is true, complete, aesthetically successful, or sufficient for exit
- decide `compact-strengthen`, `refine`, `deepen`, or `freeze`

Every script result means only:

> `No schema violations were detected; agentic audit is still required.`

### Common Mistakes

- Treating schema validation as audit completion.
- Letting scripts decide `exit_state`.
- Running TVG on an unbounded document instead of a named module.
- Adding another round without a named positive-value hypothesis.
- Running a default TVG pass without making the expected output value visible.
- Inferring a specialized value profile from the artifact being improved when that artifact may be the flawed sample.
- Treating loop-assisted artifact success as proof that the profile itself is strong.
- Exposing TVG internal vocabulary in final customer/business/architecture deliverables.

## Boundaries / 边界

- Do not use TVG to reopen whole-project strategy.
- Do not deepen for length, polish, or template completeness.
- Do not add process weight to low-risk work.
- Do not require a supplied `value_profile` for ordinary tasks; use the default practical-value profile.
- Do not let a supplied profile override evidence honesty, claim ceilings, user constraints, safety boundaries, or veto constraints.
- Block rather than deepen when the missing input is evidence, domain input, runtime proof, or stakeholder judgment.

## Runtime Support / 支撑材料

### Trace Commands

Initialize:

```bash
python3 skills/tvg/scripts/trace/init.py \
  --module-id example-module \
  --module-title "Example module" \
  --module-type methodology \
  --veto-constraint "do not freeze if evidence boundaries are hidden" \
  --output /tmp/tvg-trace.json
```

Validate:

```bash
python3 skills/tvg/scripts/trace/validate.py /tmp/tvg-trace.json
```

Persist:

```bash
python3 skills/tvg/scripts/trace/persist.py \
  /tmp/tvg-trace.json \
  --store .tvg/traces
```

### Resource Files

- `resources/methodology.md` — full Thinking Value-Gain methodology
- `resources/exit-audit-template.md` — human/LLM audit template
- `resources/trace-record-schema.json` — script validation schema
- `resources/fidelity-contract.md` — TVG fidelity contract for v0.9.
- `templates/fidelity-output.json` — example v0.9 fidelity output shape.
- `scripts/validate_tvg_output.py` — validate fidelity contract output shape with the shared core.
- `resources/value-profiles/profile-construction.md` — guidance for building and evaluating value profiles without confusing profile power with runtime rescue
