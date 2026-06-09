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

Three core inputs keep TVG from becoming generic improvement:

- `value_profile`: optional value definition package for this module and use. If absent, TVG uses the default practical-value profile. A supplied profile defines what good, bad, priority, profile-specific axes, and profile-specific veto constraints mean for the artifact.
- `veto_constraints`: explicit unacceptable states for this module and use. They are not value-gain axes. If one is triggered, the module must not exit as `freeze`.
- `independent_auditor`: for high-impact, high-uncertainty, or handoff-critical modules, the exit audit should be performed by a reviewer that reads the final module, intended use, evidence, and veto constraints, not the generator's working process.

Optional delivery control:

- `output_profile`: `insight_dense | balanced | coverage_rich`. This is delivery bias, not an internal workflow fork. It may affect final expression shape, but it must not lower the standard for `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`.

Profile guardrails live in `resources/methodology.md`: `insight_dense` should preserve calibrated claim tension, `balanced` should avoid unnecessary synthetic machinery, and `coverage_rich` should preserve useful review or handoff structure.

Value profile guardrails live in `resources/methodology.md`: the default practical-value profile is the fallback, supplied profiles may specialize value-gain axes and audit prompts, inferred profiles must be marked `inferred-with-warning`, and profiles cannot override evidence honesty, claim ceilings, user constraints, safety boundaries, or veto constraints.

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
3. Resolve the active `value_profile`: `default | supplied | inferred-with-warning`.
4. Name any module-specific veto constraints before deepening.
5. Check the current module state using `Thinking Thickness`, `Grounded Insight Yield`,
   and `Value Density`.
6. Pass the thickness gate before applying density optimization or `output_profile`.
7. Select value-gain axes from the default profile or the supplied profile's derived axes.
8. Perform the routed value-gain action: `deepen`, targeted depth formation, `refine`,
   `compact-strengthen`, warning calibration, `return-remediate`, `blocked`, or `freeze`.
9. Apply `output_profile` only as exit-side graded refinement.
10. For high-impact, high-uncertainty, or handoff-critical modules, separate generator work from the exit auditor.
11. Validate trace shape with `scripts/trace/validate.py`.
12. Persist the trace with `scripts/trace/persist.py` when useful.
13. Make the exit decision by agentic audit, not by script output.

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
- choose, infer, complete, rank, or satisfy `value_profile`
- decide whether a value profile is true, complete, aesthetically successful, or sufficient for exit
- decide `compact-strengthen`, `refine`, `deepen`, or `freeze`

Every script result means only:

> `No schema violations were detected; agentic audit is still required.`

### Common Mistakes

- Treating schema validation as audit completion.
- Letting scripts decide `exit_state`.
- Running TVG on an unbounded document instead of a named module.
- Adding another round without a named positive-value hypothesis.
- Inferring a specialized value profile from the artifact being improved when that artifact may be the flawed sample.
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
