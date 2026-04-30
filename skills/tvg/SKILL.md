---
name: tvg
description: Manual-only. Never activate from ordinary document feedback, shallow-output comments, thin judgment, requests to deepen, audit, improve, add value, or make a document more useful. Use only when a human, agent, script, or external workflow explicitly says TVG, or an external workflow routes to TVG.
---

# TVG / Thinking Value-Gain

## Core Claim

Thinking Value-Gain is a value-driven thinking-depth enhancer for AI-generated bounded modules.

It addresses a common AI-output failure mode: the artifact looks complete, rigorous, standardized, and fluent, but the substance is hollow, shallow, random, or too weak for real judgment, decision, action, review, reuse, or handoff.

When used on a bounded artifact with a clear value target, TVG usually has high upside and low downside: it improves depth without needing to reopen the whole problem.

Short rule:

> Do not deepen for length. Deepen only where practical value can increase.

## Activation Boundary

TVG is manual or explicitly routed. Use it only when a human, agent, script, or
workflow explicitly says `TVG`.

Workflow routing must be explicit: an external process, script, upstream hook, or user
instruction names TVG. Do not infer workflow routing from an artifact that merely
looks suitable for TVG.

Agent invocation must also be explicit: another agent may call TVG only when its task
packet, hook output, or instruction names TVG. Agent-local inference from a shallow
document or thin judgment does not count.

普通的“这份文档有点空”“AI 输出看起来浅”“判断很薄”“需要深化”“审查是否空洞”反馈，可以作为判断信号，但不被普通文档反馈被动唤起 TVG。先按当前任务直接回应；只有用户显式要求使用 TVG，或 workflow 明确路由，才进入 TVG trace 和 value-gain loop。

## Hard Boundary

Scripts support bookkeeping and calibration only. They must never replace agentic judgment.

Scripts may:

- initialize trace records
- validate trace shape and required fields
- persist trace records
- report factual completeness issues

Scripts must not:

- choose value-gain types or axes
- decide whether another round is worth doing
- score value gain, demo risk, or overfitting risk
- write or change `exit_state`
- promote patterns
- output `PASS` as an audit verdict

Every script result means only:

> `No schema violations were detected; agentic audit is still required.`

## Trace Boundary

Trace is an audit/calibration log, not working context.

It records the summary of what was changed, what value was claimed, what remains
review-bound, and why another round is or is not justified. It must not control flow
decisions, choose value-gain axes, or decide whether another round runs.

Do not replay the full trace into later rounds by default. Use the current module,
the current exit gate, and the latest audit summary as working context. Summarize
current-round outcome in the trace and archive old detail when a run has many rounds.

## When To Use

Use this skill when:

- a module exists but may still be thin
- a document looks complete but downstream use would require invention
- an AI output looks rigorous but feels hollow, surface-level, or randomly assembled
- a review needs to distinguish value gain from added length
- a bounded deepening loop needs trace discipline
- a bounded module needs a value-driven depth pass before review, reuse, handoff, or exit

Do not use this skill to reopen whole-project strategy or to add process weight to low-risk work.

## Operating Flow

1. Name the smallest module that can be independently frozen, returned, or blocked.
2. Read `resources/methodology.md` only as needed.
3. Create a trace with `scripts/trace/init.py`.
4. Perform agentic value-gain work and fill the trace.
5. Validate trace shape with `scripts/trace/validate.py`.
6. Persist the trace with `scripts/trace/persist.py` when useful.
7. Make the exit decision by agentic audit, not by script output.

## Trace Commands

Initialize:

```bash
python3 skills/tvg/scripts/trace/init.py \
  --module-id example-module \
  --module-title "Example module" \
  --module-type methodology \
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

## Resource Files

- `resources/methodology.md` — full Thinking Value-Gain methodology
- `resources/exit-audit-template.md` — human/LLM audit template
- `resources/trace-record-schema.json` — script validation schema

## Common Mistakes

- Treating schema validation as audit completion.
- Letting scripts decide `exit_state`.
- Running TVG on an unbounded document instead of a named module.
- Adding another round without a named positive-value hypothesis.
- Exposing TVG internal vocabulary in final customer/business/architecture deliverables.
