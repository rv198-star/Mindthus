# Brake V0.4 Threshold 0.82 Dev Diagnostic

Status: **incomplete diagnostic; not an n=3 gate decision.**

> Superseded by the completed n=3 record below. The earlier status is retained
> to preserve the chronology of the two invalid runtime attempts.

The requested V0.4 threshold calibration is implemented and two valid full
repeats completed. The third repeat was invalidated by an external Codex usage
limit before it could finish. This report records the evidence without treating
the two repeats as a certification result or a Batch 5 request.

## Frozen Configuration

- Prompt version and SHA-256: `v0.4` /
  `cf50cd28995eadf1065da28b8bb4555c0b421524cf8eedae971b7939718a15c1`
- Threshold: `0.82`, explicitly bound to the V0.4 prompt lineage.
- Threshold-config SHA-256:
  `eb7872bc6cb548e5b53dab7836df8141493855d64a65bfff1a262cbf515c6afd`
- Runner SHA-256:
  `4a82cce5f3b9af5b2e76a898a6c8576318fa6efb18ed5ed9044de7e38374fb9d`
- Original fixture SHA-256:
  `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13`
- V0.4 expansion fixture SHA-256:
  `591d785ea0a824f244162236d261790aa4ff4c68fbe593c7ddf98f37ffa890e3`
- A1/A2 anchor fixture SHA-256:
  `bbfe78f370f3e42fb5c7389c4484dc062c262d35a37d3f58acba97167dc16c99`
- Generator, judge, and triage model: `gpt-5.5`.

The pre-registered negative control remains: all `54` negative case-turns in a
completed n=3 must have no four-hard-gate-true result; any four-true result at
confidence `>= 0.82` requires rolling back to `0.85` and review. The n=3
denominator was not reached here, so this clause has not been certified.

## Valid Repeats

| Packet | Repeat 1 positive mean | Repeat 2 positive mean | Positive triage fire R1/R2 | Negative triage false fire R1/R2 | Negative runtime false wake R1/R2 |
| --- | ---: | ---: | --- | --- | --- |
| Original dev | `1.75` | `1.50` | `1.000 / 0.812` | `0.000 / 0.000` | `0.000 / 0.000` |
| V0.4 expansion | `2.00` | `2.00` | `1.000 / 1.000` | `0.000 / 0.000` | `0.000 / 0.000` |
| A1/A2 anchors | `1.00` | `1.50` | `1.000 / 1.000` | n/a | n/a |

Both valid repeats have `triage_error_count = 0`, all four contamination counts
(generator, triage, action, judge) equal to `0`, and zero deterministic
loaded-action payload validation failures. The original fixture's active/valid
loaded-action contract turns were `16/16` in repeat 1 and `13/13` in repeat 2.

These are separated evidence layers, not a merged score:

1. **Activation:** original positive fire rate varied from `1.000` to `0.812`.
2. **Mechanical action:** every active contract payload in both valid repeats
   passed deterministic validation.
3. **Semantic action:** the original means meet the `1.5` floor in each valid
   repeat, while A1/A2 remain variable (`1.00`, then `1.50`).

## Invalid Attempts

- [`repeat-1/INVALID-ATTEMPT.md`](repeat-1/INVALID-ATTEMPT.md) preserves the
  pre-run API enum failure caused by the local `ultra` reasoning-effort setting.
  It is excluded from all results above.
- [`valid-repeat-3/INVALID-ATTEMPT.md`](valid-repeat-3/INVALID-ATTEMPT.md)
  preserves the external usage-limit interruption. Its partial artifacts are
  excluded from all results above.
- [`valid-repeat-3-capacity-retry/INVALID-ATTEMPT.md`](valid-repeat-3-capacity-retry/INVALID-ATTEMPT.md)
  preserves the capacity-recovery attempt. It was stopped after the original
  packet recorded generator contamination on `brake-triage-s04`; its partial
  artifacts are likewise excluded.

## Decision Boundary

The following remain unproven and must not be inferred from this report:

- the completed n=3 primary-fixture gate;
- the `54`-row negative falsification appendix;
- A1/A2 three-repeat stability and their per-record judge rationales;
- any external shadow or Batch 5 eligibility.

When external capacity is available, run one fresh repeat under this exact
frozen configuration. Only then may a report add the complete six-gate verdict,
the 54-row negative appendix, and the A1/A2 rationale records.

## Completed N=3 Verdict

The clean third repeat is `valid-repeat-3-contamination-retry`. It follows two
excluded repeats: the first capacity-recovery retry contaminated generator
output on S04, and is preserved as an invalid attempt; no frozen configuration
was changed before the clean retry.

| Gate | Result | Evidence |
| --- | --- | --- |
| Original dev positive mean >= 1.5 in every repeat | PASS | `1.75 / 1.50 / 1.50` |
| Expansion mechanism packet positive mean | PASS | `2.00 / 2.00 / 2.00` |
| Negative triage false fire | PASS | `0/54` |
| Negative runtime-event false wake | PASS | `0/54` |
| Four-hard-gate falsification clause | PASS | `0/54` four-true rows at confidence `>=0.82` |
| Stable activation and loaded-action semantic behavior | FAIL | Original positive fire rate is `1.000 / 0.812 / 0.875`; pressure and A1/A2 semantic scores remain variable. |

The overall n=3 gate is **FAIL** because the last gate is not green. This is a
measurement result, not a request for Batch 5 or a prompt/fixture/runner/gate
change.

The required case-level material is mechanically extracted from the raw records
in [`N3-MECHANICAL-EXTRACTS.md`](N3-MECHANICAL-EXTRACTS.md): the 54-row negative
falsification appendix, all R2 activation-loss rows, all six A1/A2 judge
rationales, and the handoff-manifest fingerprints.
