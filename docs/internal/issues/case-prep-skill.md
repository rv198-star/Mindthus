# Case Prep Skill / 案例准备 Skill

Status: Implemented v1
Priority: P1
Execution: Initial production slice complete

## Problem

Judgment Trace v1.1 and Case Export v1 provide a safe structural foundation, but the
current user workflow exposes maintainer-level details: trace schemas, summary JSON,
case types, redacted excerpt flags, output directories, validators, and archive steps.
TPlan case preparation is even harder because users must understand Mission runtime
state and manually decide which evidence, decision, blocker, or recovery event is
relevant.

The result is a technically valid export path with an unnecessarily high use threshold.

## Core Decision

Add one explicit internal skill named `case-prep`.

The skill unifies the interaction surface but does not merge the underlying contracts:

```text
case-prep
├── judgment/current-context mode -> Judgment Trace v1.1 + Case Export v1
├── benchmark mode                -> archived benchmark artifacts + Judgment Trace
└── tplan mode                    -> bounded TPlan Case Packet v1
```

Judgment Trace and TPlan runtime data remain separate. A TPlan case packet may reference
one optional Judgment Trace, but it must not translate the full Mission runtime into a
Judgment Trace.

## User Contract

A user should be able to ask:

```text
/mindthus:case-prep 把刚才这次判断失败整理成案例
/mindthus:case-prep 导出这个 benchmark run 里的 mtj-002
/mindthus:case-prep 把当前 TPlan Mission 的阻塞整理成案例
```

The skill should infer the mode from concrete context and use defaults. It may ask at
most one question when multiple failure events are genuinely ambiguous.

## Mainline

### Judgment / Current Context

The agent creates a bounded Judgment Trace v1.1 and case summary from observable facts,
uses `unknown` for unassessed deltas, optionally writes explicitly redacted excerpts,
and invokes the existing Case Export validator.

### Benchmark

Given a run directory and case ID, the runtime locates or reconstructs the case trace,
reads bounded score/activation metadata, produces a reviewable summary, and packages the
case without copying the full prompt or answer by default.

### TPlan

Given a Mission directory, the runtime uses TPlan's read-only Mission Pulse and snapshot
surfaces. It exports only:

- a bounded Mission/active-path summary;
- one selected focus and selection rationale;
- at most five brief evidence events;
- a bounded Pulse view;
- runtime-provenance status and diagnostic codes;
- an optional linked Judgment Trace;
- optional explicitly selected and confirmed-redacted text excerpts.

It must not export the full `mission.json`, task tree, evidence stream, step logs,
execution trace, telemetry stream, or Mission directory.

## Output Contract

Each successful preparation produces:

- a reviewable local directory;
- a `.tar.gz` archive containing that directory;
- a concise preview with mode, focus/case type, included files, warnings, and the manual
  review boundary.

No network operation or automatic issue/benchmark submission is permitted.

## Privacy And Authority Boundaries

- Explicit invocation only; do not add passive router wake-up.
- No automatic upload.
- No full conversation or Mission dump.
- Text excerpts require explicit selection and redaction confirmation.
- Pattern scanning is not an anonymity guarantee.
- Scripts validate shape, paths, and content indicators only; the agent owns relevance,
  redaction judgment, and case interpretation.
- Generated packages remain `review_required` before sharing.

## Implementation Result

Implemented on 2026-08-06:

- explicit-only `skills/case-prep/SKILL.md` with judgment, benchmark, and TPlan modes;
- one `prepare_case.py` entry that creates local review-required directories and
  `.tar.gz` archives;
- benchmark reconstruction from bounded archived response/score records;
- separate bounded `tplan.case-packet.v1` manifest and validator;
- TPlan active-path/Pulse/provenance/event selection without raw Mission/runtime dumps;
- optional linked Judgment Trace and confirmed-redacted text excerpts;
- runtime fingerprint and all supported release-layout coverage;
- contract/privacy and integration/release audit records.

## Acceptance Criteria

- [x] `skills/case-prep/SKILL.md` defines an explicit-only, low-interaction workflow.
- [x] Judgment mode wraps Case Export v1 and creates an archive.
- [x] Benchmark mode accepts a run directory and case ID without requiring manual trace
      or summary construction.
- [x] TPlan mode produces a bounded `tplan.case-packet.v1` package from documented
      read-only runtime views.
- [x] TPlan mode never includes full Mission/runtime files by default.
- [x] Optional Judgment Trace linkage preserves contract separation.
- [x] Optional excerpts require explicit redaction confirmation.
- [x] Validators reject unsafe paths, symlinks, missing consent flags, raw Mission dumps,
      unexpected files, and known high-risk secret patterns.
- [x] A `.tar.gz` archive is generated locally with no upload.
- [x] Repository, plugin, Codex portable, Claude portable, and OpenCode layouts work.
- [x] Tests and audit records cover privacy, package boundaries, and release layouts.

## Non-goals

- Automatic data contribution.
- Central telemetry.
- Automatic benchmark admission.
- Replacing Judgment Trace or TPlan runtime contracts.
- Perfect automatic redaction.
- Exporting arbitrary attachments.
