# Medium rerun — actual products and bounded interpretation

Runtime source: `c58720446fefa21c2bb872bcfbcf134f8dfcc3ac`.
Previous max products remain at `4925b5c3ea5266e792f4e83e7b322139bdf410e1`.
This is the one Owner-authorized rerun of the same eight public inputs; not holdout,
blind review, stable performance measurement or a default-adoption qualification.
No evaluator model was called. Content notes are the executor's group-aware reading.

## Actual completion

All 24 requested paths have a terminal disposition: A 8 delivered, B 7 delivered
and 1 failed, C 8 delivered by retaining exact new A. No handling, semantic retry,
new unknown, safety/permission refusal, host CLI launch or Sol call.

| Input window | A clean direct | B fixed primitives | C Jev checks actual A |
|---|---|---|---|
| case-01 / quality 97% | Automatic main flow | Automatic main flow | A retained |
| case-02 / quality 99.2% | Manual main flow | Manual main flow | A retained |
| case-03 / specified-version delivery | 80% → 100%; benefit on this metric | Same core result | A retained |
| case-04 / accuracy given correct version | No gain on this metric | Pre-send SSL failure; no reply | A retained |
| case-05 / UI size | Scaling can help; comfort needs testing | Same core result | A retained |
| case-06 / physical PPI | Software cannot increase PPI | Same core result, extra goal discussion | A retained |
| case-07 / 30-day output | New flow: 5400 vs 3000 | Same core result | A retained |
| case-08 / 3-day output | Old flow: 300 vs 0 | Same core result | A retained |

All available first host replies meet their core fixed norm. A and retained C
follow all four condition reversals. B follows three complete reversal pairs;
its Skills reversal is incomplete because case-04/B has no answer. The failure
remains in the eight-case denominator. No blanket whole-response PASS is assigned.

Full first replies and actual C records: [ANSWERS.md](ANSWERS.md).
Preselected full 4K comparison: [CASE-06.md](CASE-06.md).
Individual path products: `answers/case-01-A.json` through `case-08-C.json`.
The raw archive additionally contains requests, actual wire bodies, provider
returns, local validation/import, immutable state-after and scheduler evidence.

## The real failure

Local call `000009`, key `case-04-medium-prompt-A:0`, error `transport_failure`.
Raw diagnostic: `URLError`, reason `SSLError`, errno / SSL code 8; no HTTP response.
Observed stage: `connection_establishment_failed`; evidence:
`HTTPSConnection.connect raised before generation HTTP write`.
Diagnostic body digest:
`b81e034e4a08760dd5a725a8aeabe219ae7295dd3b7acdd01271d35ff7dd9e5c`.
Measured host session 6.463959709s. Generation send status is evidence-bound pre-send;
provider acceptance and remote-terminal fields remain unknown in the original
diagnostic. This is not a content failure or security rejection. It was not retried.

See `calls/000009/{intent,request,wire,raw,terminal,import,state.after}.json` in
[raw-evidence.tar.gz](raw-evidence.tar.gz). Failed usage/fees are unavailable and
not converted into a measured zero. Seven fully delivered cases, excluding case-04,
are used below for matched performance; whole-batch reliability retains the failure.

## Judgment versus extra prose

Ordinary-effort A already corrects the important insufficient user inferences in
cases 01/03/05/07, while accepting the sufficient conditions in 02/04/06/08.
This batch does not support the premise that this host needs the primitive packet
to identify those relationships. It says nothing decisive about older model versions
or harder, less explicitly framed source disputes.

The fixed packet adds no observed important final-decision correction. Some B replies
use “带节奏点” or method-layer terminology and longer explanations. That is recorded
as presentation/extra intervention, not automatically a wrong core decision.

In case-06, B accepts the physical-PPI goal, then asks whether the user's “real”
goal is experience and warns against upgrading the claim to “软件对这个屏幕的任何体验
目标都没有帮助”. The user had explicitly limited the goal to physical PPI.
This is unnecessary reframing and a warning against a broader unasserted claim;
it does not demonstrate a better decision. A also adds a conditional alternative
experience goal and recommends trying scaling in that branch. These branches
are therefore not wholly caused by the packet.

Case-04/A similarly accepts the already limited metric and then adds four points
about alternative potential value. No case-04/B content judgment is possible.
Case-05/A says enlarged text/control dimensions are “也更清晰”; the provided facts
do not establish a clarity improvement. Both A/B add OS/application details without
case-specific verification. These are evidence/action limits, preserved with the
correct core answer, not silently counted as fully validated claims.

The current two-question detector expressly excludes conditional multi-goal discussion.
Its negative outcomes do not certify that every supplement is needed, every factual
detail is right, or that claim fidelity is perfect. No definition or threshold was
changed to make it flag these actual replies.

## Actual Jev results

All 16 answers are valid under the current Noul contract and consumed as deny;
no unresolved, provider/contract error or handling was observed.

| Case | Q_TARGET | Q_SCOPE | Consumption |
|---|---:|---:|---|
| 01 | 0.05 | 0.10 | retain A |
| 02 | 0.04 | 0.08 | retain A |
| 03 | 0.07 | 0.09 | retain A |
| 04 | 0.07 | 0.09 | retain A |
| 05 | 0.08 | 0.11 | retain A |
| 06 | 0.10 | 0.13 | retain A |
| 07 | 0.05 | 0.09 | retain A |
| 08 | 0.05 | 0.06 | retain A |

Jev saw only each new clean A, never B, old answers or evaluation norms.
Thus it did not detect/repair B's extra reframing. C is not an independent host
generation when there is no handling: all eight finals are exact A text.

## Host tokens and processing — seven complete paired cases

Cases 01/02/03/05/06/07/08 only. Processing is measured adapter session time,
including transport/worker overhead, not pure HTTP generation time.

| Path | Host prompt tokens | Host completion tokens | Host total tokens | Processing |
|---|---:|---:|---:|---:|
| A | 1,743 | 12,883 | 14,626 | 98.585s |
| B | 13,048 | 14,826 | 27,874 | 113.152s |
| C complete pipeline, including shared A | 1,743 | 12,883 | 14,626 | 118.643s |

C adds seven Jev calls / 20.059s, with raw Jev usage 90,887 input and 266 output
tokens. Its complete pipeline has 14 logical calls (seven shared A plus seven
checks), versus B's seven. Physical experiment totals do not debit shared A twice.

Under the Owner's near-zero financial-cost assumption for Jev, C avoids the
constant host packet overhead: 11,305 fewer host input tokens than B; total host
tokens 47.5% lower in this sample. That is a host-token observation, not a measured
fee reduction: cache, prompt/output prices, units and actual charges are unresolved.
It is not zero total tokens, and a triggered handling would add host tokens/calls.

There is no processing-speed advantage over B in this batch: C is about 5.49s slower
across seven complete cases. It also adds a mandatory cooldown between A and Jev.
A alone already has the same core decisions and fewer calls/time. No positive actual
bias-and-correction case demonstrates why the additional detector is necessary here.

## Medium versus sealed max — same seven available matched windows

| Host group | Max total tokens | Medium total tokens | Max session | Medium session |
|---|---:|---:|---:|---:|
| A | 21,248 | 14,626 | 135.754s | 98.585s |
| B | 39,053 | 27,874 | 158.564s | 113.152s |

Known reasoning-token sums decline from 40,558 to 22,801 across these host groups;
core decisions remain correct. This is a single repeated sample observation.
`medium` was explicitly transmitted and responses returned; the effective backend
effort level is not attested. Official DeepSeek defines medium as a default-high
alias; CPA mapping remains unverified. Network/cache/time variation prevents a
stable latency or fee-ROI claim. Old max scores and products were not rewritten.

## Complete accounting and limits

New logical calls: 24 = 16 host attempts (15 answers, one pre-send failure) + 8 Jev.
Inherited: 35 = 27 host + 8 Jev. Cumulative: 59 = 43 host + 16 Jev.
No budget reset; new phase residual 8 host calls is unused and does not authorize
another rerun, semantic retry or completing case-04/B automatically.

New measured adapter sessions 251.899s; active waiting 1438.091s; loading 0.017s
separately. Wall from first intent to last terminal 1632.313s, including the first
conservative cooldown 1692.318s (about 28m12s). Minimum bound serial gap 60.002s.
The same parent lock/ledger was used, and old failures/unknowns remain unchanged.
Observed internal recovery 0; exact underlying HTTP attempts and dollar fees unknown.
Raw whole-batch Jev usage: 108,794 input / 304 output tokens. Raw host known totals
exclude missing failed-call usage explicitly; see [metrics.json](metrics.json).

The practical signal is to avoid loading a long generic packet when it adds no
needed judgment. Jev can be a low-host-token conditional gate, but this batch
does not establish extra correction value or a speed advantage for this exact
post-draft gate. It also does not show that all cognitive primitives are useless.
Defaults/main/ROI-Beta, older studies and GJ/R2 closed findings stay unchanged.

Remaining missing product: case-04/B only. No new unresolved send state. No further
model batch or evaluator is started. Evidence locations: [evidence-index.json](evidence-index.json),
[raw-evidence.tar.gz](raw-evidence.tar.gz), [summary.json](summary.json),
[targeted offline tests](TESTS.log), [pre-dispatch scope](EXECUTION.md).
