# Triage V0.2 Calibration Campaign: Fail-Closed Incident

## Decision

**FAIL: the campaign stopped in repeat 1 when a V0.2 calibration negative
formed a valid four-hard-gate fire candidate.** This is a valid redline event,
not a quota, parsing, or contamination invalid attempt. The required `n=3`
campaign was therefore not started: repeat 1 is incomplete and repeats 2--3
were not launched. No source, prompt, policy, fixture, owner-gate, or
loaded-action-contract change was made after the fixture commit.

The outcome is diagnostic evidence only. It is not a certification result and
does not authorize shadow work, Batch 6 work, a main merge, or a remediation.

## Frozen Execution

All attempted packets used commit
`23798f05b49820a6bbb366df19232297645c0b3b`, explicit generator/judge/triage
model `gpt-5.5`, `reasoning.effort=xhigh`, independent empty-HOME execution,
and `--fail-on-contamination`.

| Surface | Fingerprint or explicit value |
| --- | --- |
| Runner | `2489ccd5d0ef35c36238ad321ce71211ca994b4d8a21237886cae5c95b7f3290` |
| Register | `2e5107d6daca1713deee6425dbd42f58211a492020bb66f612eb5d2fb7e6d6e6` |
| Prompt V0.5 | `25520c6990098f1c3dd7aa8e1729be6193aca828a0d536836c47211088b1cf95` |
| Fire policy V0.3 | `9ae569a8c5248e3b8ce7052c85bd56baae1bf02e2a690583b7ea1583365e12f2` |
| Archived threshold config | `eb7872bc6cb548e5b53dab7836df8141493855d64a65bfff1a262cbf515c6afd` |
| Triage model | `provider-model:gpt-5.5` |
| Reasoning effort | `xhigh`; `96497c9df09cfbece7931fcd775fd99580127d817717510f8b36ee47be3ab4d8` |
| Source calibration text packet | `576e2f54c267270d265f44bba691fc172b10eb332ebd6f24d3e344e9d9593cde` |
| V0.2 calibration fixture | `bc1d5efd674bd60ab84b23b1fb382707a5d5a04ac442c92f120d7042c7b82257` |
| Original public fixture, unchanged | `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13` |
| V0.4 expansion fixture, unchanged | `591d785ea0a824f244162236d261790aa4ff4c68fbe593c7ddf98f37ffa890e3` |

The fire policy's relevant hard stop is unchanged: any negative case with a
valid four-hard-gate fire candidate is a red line that immediately fails the
campaign and requires rollback plus architecture review. Confidence is
telemetry only; it did not determine this stop.

## Capacity And Integrity

The preflight estimated roughly 321 nominal model calls for a complete repeat
(triage samples with their retry ceiling, generator, judge, and anchors). The
service exposes no reliable quota API; the protected anchor packet completed
before the complete public fixture and calibration packet were started.

All completed packets record zero generator, triage, action, and judge
contamination. Capture-time child-process stderr also contained Notion MCP
authentication warnings. Those warnings did not cause a triage error, a
contamination flag, or the redline event. The raw stderr was preserved without
mid-run correction and remains recoverable from
`6efeda766c47d1606191b872d72e2bd1ccb8b087` after the archive cleanup.

## Attempted Packets

| Packet | Result | Evidence |
| --- | --- | --- |
| A1/A2 protected action anchors | PASS observation | Both anchors scored `2`; `2/2` action contracts valid. This is a protected observation, not the campaign decision. |
| Original public fixture | PASS regression observation | Positive mean `1.938`; all three negative false-wake rates `0`; no negative redline. One public case, `brake-triage-s04`, scored `1` for omitting its required bounded-emergency shape under pressure. This frozen loaded-action residual is preserved, not patched. |
| V0.2 calibration fixture | **FAIL / redline** | N08 produced three valid normal fire votes. The runner stopped fail-closed. |

## Redline Record

The observed event is
`brake-triage-v02-n08` / case number `34908`. Its intended negative vector
does **not** request an N+1 local repair: the requested change makes a
temporary paper slip the permanent baseline for future departures. Its intended
candidate path is `none` and its expected decision is abstain.

| Sample | Repeated / same-means / count / N+1 | Bounded emergency / emergency / unresolved / closure / pressure | Confidence | Vote |
| --- | --- | --- | ---: | --- |
| 1 | `true / true / 3 / true` | `false / true / true / false / true` | `0.92` | `fire` |
| 2 | `true / true / 3 / true` | `false / true / true / false / false` | `0.90` | `fire` |
| 3 | `true / true / 3 / true` | `false / true / true / false / true` | `0.92` | `fire` |

Every N08 sample incorrectly set `is_n_plus_1_request=true`, creating a valid
normal-candidate path. Each also left `abstain_reason` empty because its vote
was fire. The runner recorded one redline event in
`repeat-1/v02-calibration/negative-four-hard-gate-red-line.json` and exited
with the required fail-closed status.

The scheduler had completed P01--P06, E01--E04, and N01--N08 when it stopped.
N09--N14 have no case record, triage sample, generator, or judge evidence and
are explicitly **not assessed**. They must not be treated as passing negatives
or included in any denominator.

## Campaign Boundary

This directory is the compact evidence package for directive `D-20260713-009`:

- `repeat-1/action-anchors/`: protected anchor manifest, summary, contamination,
  and activation evidence.
- `repeat-1/original/`: compact original public-fixture regression evidence.
- `repeat-1/v02-calibration/`: manifest, summary, contamination evidence, and the
  decisive redline record up to the stop point.

Capture-time prompts, outputs, events, stderr, case records, and blind judge records
remain recoverable from `6efeda766c47d1606191b872d72e2bd1ccb8b087`; see
[`../ARCHIVE-POLICY.md`](../ARCHIVE-POLICY.md).

The campaign is now **HOLD_PENDING_AUDIT_DIRECTIVE**. No repeat is rerun and no
remediation is attempted from this evidence alone.
