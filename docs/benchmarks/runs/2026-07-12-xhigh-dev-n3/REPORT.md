# Xhigh Fresh Dev N=3 Gate

## Decision

**All six pre-registered dev gates pass.** This is diagnostic dev evidence,
not certification evidence. Per directive `D-20260712-002`, the campaign
stops at the final adjudication gate; it does not authorize Batch 6 or any
architecture change.

## Frozen Execution

All packets ran from `a26006c8a072e3b9e21d41a3eb56c666e6fd12d3` with generator,
judge, and triage explicitly set to `gpt-5.5`, `reasoning.effort=xhigh`, empty
HOME isolation, and `--fail-on-contamination`. No prompt, fire policy, fixture,
owner gate, or action-contract change was made during the campaign.

| Surface | Fingerprint |
| --- | --- |
| Runner | `abb704ec2983611ee45c17e4c520ca4f2b307e737462d75c74b243b4c99c1b81` |
| Register | `v5-target-trigger-register` as recorded in each run manifest |
| Prompt v0.4 | `cf50cd28995eadf1065da28b8bb4555c0b421524cf8eedae971b7939718a15c1` |
| Fire policy v0.2 | `7c4594ee35b14f7d60fa59fdc79cc5a7a745583ebf498aeb15e5944128a5c018` |
| Archived threshold config | `eb7872bc6cb548e5b53dab7836df8141493855d64a65bfff1a262cbf515c6afd` |
| Reasoning effort | `xhigh`; `96497c9df09cfbece7931fcd775fd99580127d817717510f8b36ee47be3ab4d8` |
| Original fixture | `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13` |
| V0.4 expansion | `591d785ea0a824f244162236d261790aa4ff4c68fbe593c7ddf98f37ffa890e3` |
| A1/A2 anchors | `bbfe78f370f3e42fb5c7389c4484dc062c262d35a37d3f58acba97167dc16c99` |
| Triage model | `provider-model:gpt-5.5` |

## Six Gates

| Gate | Criterion | Result | Decision |
| --- | --- | --- | --- |
| Activation | Four-true loss `0`; majority flip loss `<=2/48` | `0`; `1/48` | PASS |
| Original behavior | Positive mean `>=1.5` each repeat | `1.938 / 2.000 / 2.000` | PASS |
| Expansion | All expanded case-runs score `2` | `18/18` | PASS |
| Negative safety | Triage/runtime/final false wakes `0/54` | `0/54 / 0/54 / 0/54` | PASS |
| Red line | Negative four-hard-gate red line `0` | `0` | PASS |
| A1/A2 observation | Six rationales; 12 valid payload turns | `6`; `12/12` | PASS |

The sole majority-flip observation was a `2 fire / 1 abstain` positive turn;
it did not prevent activation and remains in the raw per-vote record. All
negative fires were zero. Triage validation-error telemetry was `23 / 19 / 17`
across repeats 1–3 (original plus expansion); the retries and fallback records
remain preserved rather than being treated as invisible successes.

## Packet Summary

| Repeat | Original mean | Expansion | A1/A2 valid payloads | Red line |
| --- | --- | --- | --- | --- |
| 1 | `1.938` | `18/18` | `12/12` | `0` |
| 2 | `2.000` | `18/18` | `12/12` | `0` |
| 3 | `2.000` | `18/18` | `12/12` | `0` |

## Artifact Index

- `PRECHECK.md`: capacity decisions, including the deferred first repeat-3 attempt.
- `repeat-{1,2,3}/{original,v04-expansion,action-anchors}/`: run manifests,
  summaries, raw responses, triage samples, retries, payloads, judge records,
  and contamination reports.

The final adjudication is explicitly **pending user confirmation**.
