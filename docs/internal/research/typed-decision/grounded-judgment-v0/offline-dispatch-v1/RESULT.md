# Grounded judgment — dispatch wiring, offline evidence

Scope: the user-authorized dispatch/scheduling implementation, based on reviewed implementation
`d7da2e4cc4b60fcbb4e90c6176a25e3745feb88b` and closure
`2320d1065b2690d737f79aff0b7b36fb8b0aee42`. Design remains
`006731c43a48099d41bfbc5f3421bd5267a6404f`. This is author engineering verification,
ready for scoped review of **new wiring only**, not another core/design audit.

## Delivered implementation

- `dispatch.py`: request-to-wire projection, official adapter connection, batch dispatch lock,
  existing `SerialRequests` cooldown, immutable intent/raw/terminal/envelope/import linkage.
  Uses existing official Jev endpoint and `relationship_live.deadline_post_json` (including its
  subprocess diagnostics), existing `_run_cli`, `api_schema`, `parse_events`, and transport
  recovery observation. No replacement HTTP client, proxy, channel, or retry loop.
- `runtime.py`: five-line import check for dispatch-owned runs. Standalone `init/next/accept`
  still works; dispatch-owned `accept` additionally requires a matching persisted receipt.
  Binding includes batch, local call key, request, wire, simulation mode, raw return and terminal.
- `materials.py`: imports owner-supplied business packets separately from evaluation-only norms.
  No sample generation. An owner provenance/seal reference is an assertion, not independent
  proof that a sample is unseen. Real preparation verifies the imported eight-case seal and input digest.
- `__main__.py`: `dispatch-demo`, `import-materials`, `dispatch-prepare`, `dispatch-step`.
- `dispatch_demo.py` and `test_grounded_dispatch.py`: mock clock and wire-shaped transport returns.
  No core, scoring, 13 questions, three-round dependency, discovery/check limits, old experiment,
  default Skill, main, or historical evidence changes.

The new batch snapshots the existing profile overrides and the original
`mindthus.generation-scheduling.v2` protocol, with a new scope covering A/B/C and all stages.
Its source identity includes prototype, existing executors and shared dependencies; it has no
old B1 risk-acceptance disposition and cannot clear an earlier unknown. The archived protocol's
historical A1-only scope is retained as history; the new `batch.json.scope` records this stage's
forward application. Simulation caps do not authorize live execution.

## Verification actually performed

[tests.log](tests.log): **31 passed, 0 failed, 0 skipped** — 27 new wiring tests plus four
existing file-exchange regressions affected by the import hook. No full core suite, old R2,
old six-case rerun, authentication probe, or model review.

The tests cover:

- Actual official Jev body and host command/config/schema passed to mocked existing transports;
  original schemas retain duplicate constraints and the sending copy is API-compatible.
- Full C three-round dependency → read → draft → check → revision, plus B and A and cross-arm waits.
- Batch single sender, conservative restart cooldown, budgets, done/no resend and interrupted import stop.
- Exact receipt binding, different case with identical input, changed wire, simulation/real isolation.
- Success vs confirmed format/pre-send failure vs timeout/missing/wrong-thread/wrong-turn terminal
  unknown vs permission refusal. Local write completion does not clear unknown.
- Unclassified retry logs preserve the return and stop subsequent dispatch. Exact unexposed HTTP
  counts alone do not block a valid terminal. Norms remain outside business packets.

The actual adapter unit tests replace environment access with an empty or synthetic-only mapping
and replace `_run_cli` / `deadline_post_json`; no actual credentials were read and neither a real
host CLI nor API request ran. This is not evidence of API acceptance or actual serving behavior.

## Complete simulated trace and counts

[trace.jsonl](trace.jsonl) contains **282 immutable JSON records**, packed as
`{path,file_sha256,record}`. File hashes are over original canonical JSON plus newline; absolute
paths inside records identify the original temporary simulation root, not a reusable live run.
[demo.stdout.json](demo.stdout.json) is the executable CLI's summary. [MANIFEST.json](MANIFEST.json)
indexes these artifacts and source bytes.

This is the existing public `skills-validator` development case with a synthetic method read,
not holdout and not a new business result. Order C → B → A is for this wiring demonstration only.

| Arm | Simulated logical calls | Simulated CLI starts | Jev exchanges | Read / check / revision |
|---|---:|---:|---:|---|
| C | 7 | 3 | 4 | 1 / 1 / 1 |
| B | 5 | 5 | 0 | 1 / 1 / 1 |
| A | 3 | 3 | 0 | 1 / 1 / 0 |

C phases: `round1, round2, round3, draft(read), draft(answer), check, revision`.
The record chain preserves raw atomic answers → adapted atoms → combined findings → first draft
→ bound check → revision; the mock score replies also include the official rubric legend.
The C final raw answer is:

> 【模拟修订】保留原文给定前提，限定结论；仅测试一次修订的接线。

Fifteen simulated calls × 2 seconds = 30 simulated processing seconds; 14 × 60 = 840 simulated
active-wait seconds; complete mock clock = **870 seconds**. No actual 60-second sleeps occurred.
Mock usage is explicitly synthetic. Real model calls and real CLI launches: **0**.
Driver retries: 0. Host recovery logs observed in this mock: 0. Actual underlying request/generation
counts, connection/auth recovery durations and monetary cost remain unknown, not inferred from logs.
These numbers prove wiring behavior only, not real throughput or Jev judgment quality.

## Terminal and recovery boundaries

A dedicated CLI invocation must have one thread start and one ordered, compatible terminal.
A normal `turn.completed` permits answer parsing; a structured bound request-format failure is
separate from an answer. Ordinary error text, nonzero exit, timeout, ambiguous/missing terminal
or thread/turn mismatch remains unknown. A pre-send diagnostic must match this Jev wire digest
and explicitly identify a connection-establishment failure; local send/write is not sufficient.
HTTP 401/403 is recorded with its diagnostic as a permission/authentication refusal, not retried.
Other HTTP failures without proof of generation termination conservatively remain unknown.

Serial `completion.status=returned` means the invocation returned a known terminal to the serial
scheduler, **not** that it delivered an answer: the adjacent terminal/envelope records distinguish
returned, failed and safety_refusal. Unknown throws inside the scheduler and has no completion.
The unknown envelope is still imported and preserved. No automatic resubmission or forced unlock.
Unimported transaction records require evidence reconciliation, never a fresh dispatch.

Official within-invocation recovery remains governed by v2 and the existing bounded transport.
This layer adds no recovery attempt. Existing observable recovery detection stops subsequent work
when evidence cannot classify it; it does not turn an ordinary lack of HTTP count visibility into
a stop. It also does not infer there is necessarily background remote work.

## Entry points and real batch parameters still to determine

See [RUN.md](RUN.md) and the deliberately unauthorized [admission.example.json](admission.example.json).
Engineering scope has no unfinished item. Future execution prerequisites remain: scoped wiring
review, eight owner-prepared unseen variants and norms / four reversal pairs with seal, actual
execution order, approved call/time/money budgets, existing official CLI binary/version identity
and execution authorization. No new sample or real batch has been sealed or started here.

GJ-01–04 remain CLOSED. Old six-case conclusions stand. Default adoption remains NOT QUALIFIED;
Jev quality increment and monetary ROI remain unestablished.
