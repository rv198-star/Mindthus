---
name: case-prep
description: "Use only when the user explicitly asks to prepare, export, package, or contribute a Mindthus judgment case, benchmark case, or bounded TPlan Mission case for analysis."
---

# case-prep

## Core Claim

`case-prep` turns an explicitly requested judgment, benchmark, or TPlan event into a
local review-required case archive. It unifies the user interaction, not the underlying
data models.

Judgment cases use Judgment Trace v1.1 and Case Export v1. TPlan cases use a separate
bounded `tplan.case-packet.v1` contract and may only reference an optional Judgment
Trace. No automatic upload or benchmark admission is allowed.

## Mainline

### 1. Select Mode From Concrete Context

- `benchmark`: the user names a benchmark run directory and case ID.
- `tplan`: the user names or clearly refers to a Mission directory/current TPlan Mission.
- `judgment`: the user asks to package the current or previous judgment interaction.

Do not ask the user to choose a schema or case type. Ask at most one question only when
multiple candidate failure events are genuinely ambiguous.

### 2. Judgment Mode

Create temporary, bounded inputs on behalf of the user:

- a Judgment Trace v1.1 using observable facts;
- `unknown` for every unassessed decision delta;
- a `mindthus.case-summary.v1` summary;
- optional excerpts only when useful, explicitly selected, and redacted.

Then run:

```bash
python3 skills/case-prep/scripts/prepare_case.py judgment \
  --trace <trace.json> \
  --summary <summary.json> \
  --case-type <type> \
  --out-dir /tmp/mindthus-case-exports
```

### 3. Benchmark Mode

Run:

```bash
python3 skills/case-prep/scripts/prepare_case.py benchmark \
  --run-dir <benchmark-run-dir> \
  --benchmark-case-id <case-id>
```

The runtime locates or reconstructs the trace and summary from bounded archived
response/score telemetry. It does not copy the full prompt or answer by default.

### 4. TPlan Mode

Run:

```bash
python3 skills/case-prep/scripts/prepare_case.py tplan \
  --mission-dir <mission-dir> \
  --focus auto
```

Use an explicit `--focus` only when the user named blocker, acceptance, continuation,
authority, recovery, provenance, telemetry, or general investigation.

TPlan mode exports a bounded active-path summary, one focus, at most five brief evidence
events, a compact Pulse view, runtime-provenance status, and an optional linked Judgment
Trace. It must not export the complete Mission, task tree, evidence stream, step logs,
execution trace, telemetry stream, or Mission directory.

### 5. Review And Deliver

Inspect the generated preview and validator result. Tell the user:

- inferred mode and focus/case type;
- what was included and excluded;
- any privacy warnings;
- the local archive path;
- that sharing still requires manual review and a separate action.

## Guardrails

### Excerpts

Raw text is excluded by default. When excerpts materially improve analysis, write small
redacted UTF-8 files and pass each with:

```bash
--excerpt label=/path/to/redacted.txt --confirm-excerpts-redacted
```

Do not treat the confirmation flag as proof of adequate redaction. Read the generated
package before delivery.

### Safety And Scope

- Explicit invocation only; do not add passive wake-up routing.
- No automatic upload, issue creation, or benchmark admission.
- No full conversation or full TPlan runtime dump.
- Never invent a decision delta; use `unknown` when unassessed.
- Do not expose private chain of thought.
- Scripts validate shape, paths, and known sensitive patterns; agentic relevance and
  privacy judgment remain required.
- Keep the final state `review_required_before_share: true`.

## Runtime Support

Read only the resource that matches the active mode:

- `resources/judgment-mode.md`
- `resources/benchmark-mode.md`
- `resources/tplan-mode.md`
- `resources/privacy-boundary.md`
- `resources/output-contract.md`

Primary runtime:

- `scripts/prepare_case.py`
- `scripts/validate_case_packet.py`

## Boundaries

This skill is a bounded artifact generator and tool wrapper, not a new judgment method.
It does not change `using-mindthus` routing ownership, TPlan Mission authority, or
Judgment Trace semantics.
