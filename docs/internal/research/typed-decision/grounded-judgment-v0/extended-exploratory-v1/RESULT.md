# Eight-case exploration — 24/24 real answers delivered

The final named technical attempt succeeded. All 24 A/B/C paths now have a first
complete actual answer and final workflow state; the earlier 21 delivered states
are unchanged. This includes preserved technical failures/compensations, not a
fault-free first-attempt rate or a claim that all content passed.
Independent content review of this eight-case batch remains pending.

## Limited diagnosis and final attempt

000077 failed with `Connection failed: error sending request` after 6.683 seconds,
without an answer or reliable generation send-stage evidence. It differs from the
old 000049 SSE idle timeout. Its two observable retries belong to auxiliary MCP
initialization; the docs MCP 403 is not a confirmed generation safety denial.
The precise historical cause remains unestablished.

CLI 0.159.2; one current uncredentialed DNS/TCP/TLS check succeeded with normal
certificate verification. No HTTP/authentication/model probe, credential extraction,
channel change or safety/configuration change was performed. Current connectivity
does not prove what happened to 000077. [Diagnosis](LAST-TRY.md) ·
[connection record](connection-check-000077.json).

Owner authorized one final attempt and abandonment on failure. The appended
[exact disposition](last-try-000077.json) preserves 000077 as
`risk_accepted_remote_unknown`, not a completion or pre-send failure. New 000078
uses exactly the same actual wire as 000077; it returned an answer in 96.280 seconds.
No prior Jev atom was regenerated. Existing 000047/000049 dispositions remain
specific; no general ignore-unknown policy or retry loop was introduced.

Following that success, the two already authorized, prepared A/B compensations
returned their first answers and normal one-time checks. Five new host calls,
zero new Jev calls, all returned; no new unknown/refusal/unclassified recovery.
Execution code: `7ad0bbd433eb1e4d28a379b0caffe4191527068a`.

| New call | Path / phase | Session s | Active wait s | Observed gap s |
|---|---|---:|---:|---:|
| 000078 | display-goal-2-C:6 / draft | 96.280 | 60.008 | 60.008 |
| 000079 | mechanism-object-2-A:2 / draft | 137.159 | 43.343 | 60.005 |
| 000080 | mechanism-object-2-A:3 / check | 60.000 | 43.005 | 60.005 |
| 000081 | record-source-1-B:2 / draft | 82.156 | 43.483 | 60.003 |
| 000082 | record-source-1-B:3 / check | 69.877 | 33.392 | 60.006 |

The first gap follows local risk disposition and does not establish remote
completion. Every subsequent observed gap is at least 60 seconds. Active sleep is
less than the gap when evidence/validation work occupies part of it.
New session total 445.472s; active sleep 223.230s; local execution window
759.493s (12.658min). Connection/authentication recovery
component durations, precise HTTP/generation attempts and missing fees stay unknown.
[Actual timing and bindings](last-try-actual.json).

## All paths and original products

Eight executor-prepared synthetic extensions, explicitly not independent holdout.
The same fixed case inputs/materials, Sol 6.1/xhigh official HTTP configuration and
existing official Jev 1.13.0 remain. Thirteen questions, three pre-rounds, thresholds,
two findings and one check/revision are unchanged. No old batch or model evaluator ran.

| Case | A original entrance | B precise Agent | C Jev |
|---|---|---|---|
| display-goal-1 | [delivered / 2 calls](answers/display-goal-1-A.md) | [delivered / 2 calls](answers/display-goal-1-B.md) | [delivered / 4 calls](answers/display-goal-1-C.md) |
| display-goal-2 | [delivered / 3 calls](answers/display-goal-2-A.md) | [delivered / 3 calls](answers/display-goal-2-B.md) | [delivered / 7 calls](answers/display-goal-2-C.md) |
| mechanism-object-1 | [delivered / 4 calls](answers/mechanism-object-1-A.md) | [delivered / 2 calls](answers/mechanism-object-1-B.md) | [delivered / 4 calls](answers/mechanism-object-1-C.md) |
| mechanism-object-2 | [delivered / 4 calls](answers/mechanism-object-2-A.md) | [delivered / 4 calls](answers/mechanism-object-2-B.md) | [delivered / 5 calls](answers/mechanism-object-2-C.md) |
| record-source-1 | [delivered / 3 calls](answers/record-source-1-A.md) | [delivered / 4 calls](answers/record-source-1-B.md) | [delivered / 4 calls](answers/record-source-1-C.md) |
| record-source-2 | [delivered / 2 calls](answers/record-source-2-A.md) | [delivered / 4 calls](answers/record-source-2-B.md) | [delivered / 4 calls](answers/record-source-2-C.md) |
| skills-scope-1 | [delivered / 2 calls](answers/skills-scope-1-A.md) | [delivered / 2 calls](answers/skills-scope-1-B.md) | [delivered / 4 calls](answers/skills-scope-1-C.md) |
| skills-scope-2 | [delivered / 3 calls](answers/skills-scope-2-A.md) | [delivered / 3 calls](answers/skills-scope-2-B.md) | [delivered / 4 calls](answers/skills-scope-2-C.md) |

Each product includes the original draft, check and final; no rewritten or selected
best answer. Full denominators: 24 paths and 104 planned atoms per B/C arm.

The three newly completed answers:

- [display-goal-2/C](answers/display-goal-2-C.md): try scaling on the existing display
  against the actual reading goal before comparing a replacement; preserve the
  physical pixel-density distinction. No adopted finding, no C check.
- [mechanism-object-2/A](answers/mechanism-object-2-A.md): prompt/context explains
  generation, while the whole service additionally requires signature and failure
  branch control. One normal check, no revision.
- [record-source-1/B](answers/record-source-1-B.md): limits the direct-verification
  claim despite case-internal primary-source identity; retains synthetic-case/real
  device distinction. Check has `check_conflict` unresolved basis; no revision.
  Do not relabel that check as implementation verification PASS.

## Complete costs, with historical failures retained

83 logical calls = 59 host generation CLI starts + 24 Jev. 80 returned transport records; 3 historical unknowns (000047/000049/000077). Two original local format failures (000011/000029) stay in events; transport
return and valid-answer acceptance are different. Five explicitly authorized
technical compensations are included; automatic outer-driver retries zero.
Observed generation auth/fallback/reconnect/sampling log counts zero; exact
underlying HTTP counts remain unknown. The auxiliary MCP retries are separate.

Unused original caps: 93 logical / 85 host / 8 Jev. No expanded budget was used. Unused allowance is not a target or authority to
seek nicer answers. Old unknown processing/billing/overlap risk persists.

Inclusive session/processing 5645.720s (94.10min); active wait 4640.769s (77.35min). Local execution windows 10636.134s; first send to last local terminal 24101.168s, including engineering/Owner pauses. A host session is not pure HTTP time; a local unknown-call ending is not a remote
completion. Raw usage is separated by provider; missing cost remains unknown.

| Arm | Logical | Host | Jev | Session s | Active wait s |
|---|---:|---:|---:|---:|---:|
| A | 23 | 23 | 0 | 1569.563 | 1234.648 |
| B | 24 | 24 | 0 | 3107.479 | 1338.624 |
| C | 36 | 12 | 24 | 968.677 | 2067.497 |

All arms retain common inputs, materials, judgment core and host model/configuration;
several transport/sending-contract technical successors are explicitly separated
in summary.transport_source_groups. These are not clean matched first-attempt costs. Do not
remove old failures or equate skipped/unresolved work with same-effective-judgment
speedup or dollar ROI.

## Executor observations — not an independent content verdict

| Fixed contrast | Complete observed products | Limit |
|---|---|---|
| Purchase vs current-display goal | A/B/C shift from 5K candidate comparison to current-display adjustments. | C's host shift has no adopted Jev finding behind it. |
| Generation stage vs whole service | All three preserve the adequate local explanation, adding signature/refusal control for the whole-service object. | No important A/B final error corrected by C is observed here. |
| Direct vs reported case record | Reported side rejects unsupported direct verification; all three direct-side answers also limit case-internal verification wording. | Differs from the frozen direct-side expectation. Preserve possible shared over-limitation and wording/provenance ambiguity; do not rewrite norms. |
| This Skill vs all Skills | All three preserve the adequate local explanation and limit the generalization. | No clear additional C correction of an important A/B final judgment. |

C atoms are unchanged by compensation: zero adopted findings/checks in eight cases;
raw P equals the claim window in all eight, three P low-confidence/five adopted.
Seven R unresolved; reported-source R adopted as sufficient despite the frozen
overreach expectation. B states: 95 support, 6 deny, 2 unresolved, 1 invalid; C:
38 support, 66 unresolved. These are descriptive states, not correctness scores.
Contract errors, missing dependencies and warranted uncertainty remain separate.
No path used a revision. Missing C findings here are mostly unresolved coverage,
not an established eight-case confirmation that no correction was needed.

The newly completed answers do not show a clear additional important final-judgment
correction by C in executor inspection. This is a bounded exploratory observation,
not universal Jev failure, blind/independent review, stable mean or default qualification.
The source-identity contrast especially needs the planned content review; do not
claim all 24 answers correct merely because delivery finished. Thresholds, examples,
acceptance rules and original responses are not changed to seek a win.

## Evidence and closure

[24 original products](answers/) · [83 bound calls](calls.jsonl) ·
[file-to-archive index](evidence-index.json) · [execution log](execution.log) ·
[summary/usage](summary.json) · [new additive evidence](business-evidence-after-000078.tar.gz).
The three earlier archives and all 1606 earlier index entries are preserved; 101 new
records are additive. Routine packaging verification is not a new independent hash
audit. The old [78-call stop](RESULT-000078.md), [76-call result](RESULT-000076.md),
50-call checkpoints and all failures/unknown dispositions remain.
Group-concealed [review packets](blind-review/) and separate mapping are ready;
execution/material preparation are not claimed independently blind.

Execution/answer delivery complete; independent content review pending. No remaining
unsent path or missing answer, no pending local generator. Historical remote states
and missing fees remain unknown. No new retry or batch; old GJ/R2 CLOSED, old six/four
case conclusions, main/default Skill, default NOT QUALIFIED and ROI-Beta boundaries
remain. Completion is not evidence of Jev quality increment or default adoption.
