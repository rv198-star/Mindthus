---
name: tvg
description: Use as a value-driven thinking-depth enhancer when an AI-generated bounded module or artifact looks rigorous and standard but is hollow, shallow, random, or weak in judgment, evidence, trade-offs, downstream handoff, reuse, or practical decision/action value.
---

# TVG / Thinking Value-Gain

## Core Claim

Thinking Value-Gain is the thin-value deepening axis for AI-generated bounded modules.

It addresses a common AI-output failure mode: the artifact looks complete, rigorous, standardized, and fluent, but the substance is hollow, shallow, random, or too weak for real judgment, decision, action, review, reuse, or handoff.

When used on a bounded artifact with a clear value target, TVG usually has high upside and low downside: it improves depth without needing to reopen the whole problem.

Short rule:

> Do not deepen for length. Deepen only where practical value can increase.

Two core inputs keep TVG from becoming generic improvement:

- `veto_constraints`: explicit unacceptable states for this module and use. They are not value-gain axes. If one is triggered, the module must not exit as `freeze`.
- `independent_auditor`: for high-impact, high-uncertainty, or handoff-critical modules, the exit audit should be performed by a reviewer that reads the final module, intended use, evidence, and veto constraints, not the generator's working process.

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
If the artifact is thin because the judgment point was wrong, route back to `3l5s`, `edsp`, or `wae` before deepening.

### Operating Flow

1. Name the smallest module that can be independently frozen, returned, or blocked.
2. Read `resources/methodology.md` only as needed.
3. Name any module-specific veto constraints before deepening.
4. Create a trace with `scripts/trace/init.py`.
5. Perform agentic value-gain work and fill the trace.
6. For high-impact, high-uncertainty, or handoff-critical modules, separate generator work from the exit auditor.
7. Validate trace shape with `scripts/trace/validate.py`.
8. Persist the trace with `scripts/trace/persist.py` when useful.
9. Make the exit decision by agentic audit, not by script output.

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

Every script result means only:

> `No schema violations were detected; agentic audit is still required.`

### Common Mistakes

- Treating schema validation as audit completion.
- Letting scripts decide `exit_state`.
- Running TVG on an unbounded document instead of a named module.
- Adding another round without a named positive-value hypothesis.
- Exposing TVG internal vocabulary in final customer/business/architecture deliverables.

## Boundaries / 边界

- Do not use TVG to reopen whole-project strategy.
- Do not deepen for length, polish, or template completeness.
- Do not add process weight to low-risk work.
- Block rather than deepen when the missing input is evidence, domain input, runtime proof, or stakeholder judgment.
- route back to `3l5s`, `edsp`, or `wae` when the artifact is thin because the problem
  definition, structural judgment, or control boundary is wrong.

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
