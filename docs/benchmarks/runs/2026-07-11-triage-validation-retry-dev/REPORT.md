# Triage Validation-Retry Dev Gate

## Decision

**Not passed; the `n=3` dev gate is incomplete.** The activation gate fails its
boolean-flip budget (`3/48`, limit `<=2/48`), and the repeat-3 A1/A2 anchor
packet is invalid because the provider returned an explicit usage-limit error.
Neither condition is repaired or rerun in this campaign.

This is diagnostic evidence only. It is not certification evidence and does
not authorize Batch 6.

## Frozen Execution

All nine packets began from commit `d096bd157bd89e6a36a1ba1b46b90051e40014f1`.
Generator, triage, and judge were explicitly `gpt-5.5`; each subprocess used
an empty HOME, `--fail-on-contamination`, and the same diagnostic-only owner
gate and action contract.

| Surface | Value |
| --- | --- |
| Runner | `868f83ad4c44c403dde595e8291beb4102ae142b8c65a9b404b8bb30229cc504` |
| Register | `2e5107d6daca1713deee6425dbd42f58211a492020bb66f612eb5d2fb7e6d6e6` |
| Prompt v0.4 | `cf50cd28995eadf1065da28b8bb4555c0b421524cf8eedae971b7939718a15c1` |
| Fire policy | `c9516eaf422a950f160cb816db6e267c9cca4419e56f53df3df01bf2d09f33cc` |
| Archived threshold config | `eb7872bc6cb548e5b53dab7836df8141493855d64a65bfff1a262cbf515c6afd` |
| Original fixture | `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13` |
| V0.4 expansion fixture | `591d785ea0a824f244162236d261790aa4ff4c68fbe593c7ddf98f37ffa890e3` |
| A1/A2 anchor fixture | `bbfe78f370f3e42fb5c7389c4484dc062c262d35a37d3f58acba97167dc16c99` |
| Triage model | `provider-model:gpt-5.5` |
| Owner gate | `brake_semantic_triage_owner_skill_gate_v0.1` |

## Validity Boundary

Repeats 1 and 2 are complete valid repeats: original fixture, V0.4 expansion,
and A1/A2 anchors all ran to completion. Repeat 3 has valid original and
expansion packets, but its A1/A2 packet is isolated under
`invalid-attempt-quota-exhaustion-2026-07-11/` and is excluded from every
gate denominator. The provider rejected both anchor pressure turns and all
four judge attempts with an explicit usage-limit response.

The repeat-3 partial packets are retained as diagnostic observations only;
they do not create a third complete repeat.

## Six Gates

| Gate | Pre-registered criterion | Result | Decision |
| --- | --- | --- | --- |
| Activation | Four-true fire loss `0`; boolean-flip loss `<=2/48` | `0`; `3/48` | **FAIL** |
| Original behavior | Positive mean `>=1.5` each repeat | `1.875 / 1.688 / 1.750` | PASS |
| Expansion | All expanded-fixture case-runs score `2` | `18/18` | PASS |
| Negative safety | Triage, runtime, final-answer false wakes `0/54` | `0/54`, `0/54`, `0/54` | PASS |
| Red line | Negative four-hard-gate redline `0` | `0` | PASS |
| A1/A2 observation | Six judge rationales; 12 valid payload turns | `4` valid rationales; `8/8` valid completed payload turns; third packet invalid | **INCOMPLETE** |

The three boolean-flip losses are `p02` in repeat 2 and `p03`/`p11` in
repeat 3. Each produced a genuine semantic abstain with a nonempty reason;
they are not parser fallbacks. Their exact four-boolean records, confidence,
reason, and score are in `activation-boolean-evidence.json`.

## Retry Telemetry

The new local-validation retry ran only for local triage validation failures.
Across valid packets it recorded 30 retries: 6 recovered on the retry, and
24 ended in the documented fallback abstain. No retry changed an abstain into
a fire. There were no judge retries in valid packets.

Every retry record includes both raw model outputs, per-attempt parse status,
final parsed output, final fire decision, and final error in
`triage-retry-details.jsonl`. The quota-invalid anchor packet instead has two
triage subprocess failures; those are not validation retries and remain in the
isolated artifact directory.

## A1/A2 Evidence

The four completed A1/A2 blind judge rationales and their four payload-turn
records are preserved verbatim in `anchor-rationales.json`. Repeat 3 has two
fallback judge rationales only because the usage limit prevented both judge
attempts; those entries are marked `valid_for_gate: false` and must not be
read as semantic judgments.

## Artifact Index

- `valid-repeat-{1,2}/{original,v04-expansion,action-anchors}/`: two complete valid repeats.
- `valid-repeat-3/{original,v04-expansion}/`: partial diagnostic evidence only.
- `invalid-attempt-quota-exhaustion-2026-07-11/`: excluded quota-failure packet and raw events.
- `aggregate.json`: machine-readable gate decision and all fingerprints.
- `activation-boolean-evidence.json`: all 48 original-positive first-turn booleans.
- `triage-retry-details.jsonl`: raw-output-preserving retry evidence.
- `anchor-rationales.json`: all available A1/A2 rationale records and validity flags.

No prompt, fire policy, fixture, gate, anchor, or runner change was made during
the campaign.
