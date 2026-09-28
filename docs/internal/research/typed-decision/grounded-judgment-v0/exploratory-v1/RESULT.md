# Exploratory value batch — partial delivery, stopped on new unknown

Authorized start: `444cc7233758df1c046eac676215c4445ad7dda3`.
Frozen exploratory admission/code/input commit: `b48839852097c92b373ee1befcafe1586a325572`.
Four cases, 12 intended paths; **2 delivered, 1 stopped with unknown send, 9 not sent**.
The batch is not complete and establishes no Jev increment. No additional model review or retry.

## Actual products and concise comparison

| Case | A original entry | B fine questions | C Jev |
|---|---|---|---|
| Skills text-only | delivered; 3 host calls | delivered; 3 host calls | not sent |
| Skills + independent validator | not sent | atoms returned; draft call unknown; 2 host calls, no answer | not sent |
| 4K usability goal | not sent | not sent | not sent |
| 4K physical-density goal | not sent | not sent | not sent |

Raw readable outputs: [Skills text A first draft/check/final](answers/skills-text-A.md),
[Skills text B first draft/check/final](answers/skills-text-B.md).
Both checks kept the first draft; neither path used a revision. A requested three method documents
in one read continuation; B used one atomic call, one draft call and one check call.

Both answers accept the text/context explanation for the given text-only implementation and
limit the extrapolation to Skills as a whole. A additionally states a broader definition of Skills;
B sticks more closely to what the case establishes. These observations do not establish an
important correctness improvement. There is no completed reversal pair and no C answer, so this
batch cannot answer reversal sensitivity, Jev-vs-B increment or whether the extra complexity pays.
The remaining content assessment belongs to ChatGPT; no separate reviewer model was called.

Twelve [answer/state JSON files](answers/) preserve final text where present and explicit nulls
where absent. The Skills-validator B file contains the actual atomic results and composition,
not a substitute answer. No fixture or manually authored answer fills any missing path.

## Stop evidence

Local call `000007`, `skills-validator-B:1` (draft after one returned atomic call):

- Request SHA256: `0c3df7db8af82010010ba1686aa92ce604a7d561b3d314e1442bd0b68a386eb8`.
- CLI thread: `01a0e755-b819-7fc3-810f-7988e9d750e5`; no turn ID exposed in stdout.
- Raw error: **`Connection failed: error sending request`**.
- Stdout: thread.started → turn.started → error → turn.failed with that message.
- Exit code 1; `reply_text=null`; host session 8.860 seconds.
- No bound connection-stage/pre-send proof; no HTTP acceptance/remote completion evidence.
  `turn.failed` here proves the CLI turn failed, not that a provider never accepted generation.
- Classified `unknown / unclassified_cli_failure`. Serial slot 000007 retains its intent and
  has **no completion**. Batch STOP prevents subsequent dispatch. No automatic retry occurred.

Direct original evidence:
[raw CLI events/error](blocked-call-000007-raw.json),
[terminal classification](blocked-call-000007-terminal.json),
[request](blocked-call-000007-request.json),
[import/state binding](blocked-call-000007-import.json).
This is a real transport/CLI failure with unresolved remote send state, **not a newly observed
safety refusal**. The unrelated plugin-icon warnings in stderr were retained and not treated as
model failure or a reason for engineering expansion.

Separately, `TYPESAFE_API_KEY` was absent from the current environment before any call. The
executor asked for the existing official credential entry and did not substitute a channel or
start a credential probe. All C paths therefore remain **not sent**, Jev calls=0; this is not a
Jev provider failure. Even restoring that credential alone cannot clear the new serial unknown.

## Actual cost observations

| Path | Logical calls / CLI starts | Session processing | Active wait | Answer |
|---|---:|---:|---:|---|
| Skills text A | 3 / 3 | 111.5 s | 119.3 s | delivered |
| Skills text B | 3 / 3 | 121.5 s | 178.9 s | delivered |
| Skills validator B | 2 / 2 | 67.2 s | 119.3 s | none |
| Total | **8 / 8** | **300.2 s** | **417.5 s** | 2 |

Active batch wall from first send intent through the unknown terminal: **720.4 seconds**.
Wait is actual active sleep; time spent between dispatches also contributes to the at-least-60s
interval, so active sleep need not equal exactly 60×7. No interval rule was relaxed.
Session time includes CLI/auth/transport overhead; it is not pure HTTP or model inference time.
Last failed call is included, not excluded to present a clean successful subset.

Observed internal recovery notices: zero. Underlying HTTP count, exact generation attempts,
auth/connection breakdown and monetary amount: **unknown**. Available original token usage
remains in each response/measurement; missing usage for the failed call remains unknown.
No cross-provider token-to-dollar conversion. Jev requests: **0**. Driver retries: **0**.
Ceilings remaining numerically: logical 80, host 64, Jev 16; these do **not** authorize resending
the unknown or spending the remainder automatically. Skills-validator B retains 2/7 consumed.

## Evidence and limited engineering change

- [PLAN.md](PLAN.md), cases.business.json, independent norms and two single-condition diffs were
  committed before dispatch. Public historical excerpts plus explicitly artificial conditions;
  original image absent. No holdout or formal sealing claim.
- Formal eight-case admission retained; exploratory requires exactly four public executor-prepared
  cases and explicit batch scope/authorization. Aggregate hard ceilings 88/16/72 enforced in addition
  to per-path 6/7/9. [Admission checks](admission-test.log) cover this change only; the prior 31 tests
  were not rerun and closed judgment code was not reviewed again.
- [calls.jsonl](calls.jsonl): all eight raw transport returns, terminal classifications and import
  bindings, readily inspectable without unpacking a full archive.
- [summary.json](summary.json): twelve states, actual atoms/findings/checks/answers and measurements.
- `raw-evidence.jsonl.gz`: lossless packed original batch JSON records (including inputs, config,
  requests, wires, serial records and runtime events). It is optional supporting evidence;
  no user file transport is needed to inspect the report, answers or stop.
- Original live directory remains `/Users/william/.codex/tmp/gj-exploratory-v1-run`.

## Current conclusion / unfinished scope

The intended 12-path exploration remains unfinished because a new send is unknown. Do not
start another root, reclassify it from generic connection text, apply the old B1 exception, or
retry without evidence/explicit disposition under the governing rules. No new platform recovery
file is prescribed. An official Jev credential entry is separately still needed for any future C.

There is insufficient completed comparison to recommend Jev or reject its value. Preserve these
results and the fixed remaining cases; do not expand the batch to chase a positive result.
Design/GJ-01–04/old R2 and six-case conclusions remain unchanged; no quality/default-adoption claim.
