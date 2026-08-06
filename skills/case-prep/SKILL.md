---
name: case-prep
description: "Use only when the user explicitly asks to prepare, export, package, or contribute one or all current Mindthus judgment, benchmark, or bounded TPlan cases for analysis."
---

# case-prep

## Core Claim

`case-prep` turns explicitly requested judgment, benchmark, or TPlan events into local
review-required case archives. The default batch request is:

```text
/mindthus:case-prep 导出当前所有mindthus相关案例
```

It unifies the user interaction, not the underlying data models.

Judgment cases use Judgment Trace v1.1 and Case Export v1. TPlan cases use a separate
bounded `tplan.case-packet.v1` contract and may only reference an optional Judgment
Trace. No automatic upload or benchmark admission is allowed.

## Mainline

### 1. Select Mode From Concrete Context

- `collection`: the user asks for all current Mindthus-related cases.
- `benchmark`: the user names a benchmark run directory and case ID.
- `tplan`: the user names or clearly refers to a Mission directory/current TPlan Mission.
- `judgment`: the user asks to package one current or previous judgment interaction.

Do not ask the user to choose a schema or case type. For `collection`, identify all
bounded, reusable cases in the current conversation and referenced current Mission,
deduplicate repeated discussion of the same root event, and omit ambiguous candidates
rather than starting a questionnaire. Ask at most one question only when the user named
a narrower target but multiple concrete events remain indistinguishable.

### 2. Collection Mode — Default For “All Current Cases”

When the request is “导出当前所有mindthus相关案例” or equivalent:

1. Scan the current conversation for material Mindthus events: judgment failure,
   judgment repair, value delta, routing ambiguity, regression candidate, named
   benchmark case, or current TPlan blocker/acceptance/continuation/authority/recovery/
   provenance/telemetry event.
2. Exclude ordinary acknowledgements, feature requests without an observed judgment
   event, and repeated turns that describe the same root case.
3. Prepare every retained item through its existing `judgment`, `benchmark`, or `tplan`
   contract. Never build one synthetic mega-trace.
4. Package the prepared directories with:

```bash
python3 skills/case-prep/scripts/prepare_case.py collection \
  --case-dir <prepared-case-1> \
  --case-dir <prepared-case-2>
```

5. Return one collection `.tar.gz`, the included case count and short inventory, and
   keep every nested case independently reviewable.

### 3. Judgment Mode

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

### 4. Benchmark Mode

Run:

```bash
python3 skills/case-prep/scripts/prepare_case.py benchmark \
  --run-dir <benchmark-run-dir> \
  --benchmark-case-id <case-id>
```

The runtime locates or reconstructs the trace and summary from bounded archived
response/score telemetry. It does not copy the full prompt or answer by default.

### 5. TPlan Mode

Run:

```bash
python3 skills/case-prep/scripts/prepare_case.py tplan \
  --mission-dir <mission-dir> \
  --focus auto
```

Use an explicit `--focus` only when the user named blocker, acceptance, continuation,
authority, recovery, provenance, telemetry, or general investigation.

TPlan mode exports a bounded active-path summary, one focus, at most five brief evidence
events, a compact Pulse-compatible view derived from the same atomic read-only snapshot, runtime-provenance status, and an optional linked Judgment
Trace. It must not export the complete Mission, task tree, evidence stream, step logs,
execution trace, telemetry stream, or Mission directory.

### 6. Review And Deliver

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

- `resources/collection-mode.md`
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
