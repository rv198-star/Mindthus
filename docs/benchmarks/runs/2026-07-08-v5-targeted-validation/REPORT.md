# Mindthus V5 Targeted Validation Diagnostic

Status: diagnostic run completed; V5 certification candidate deferred.

This run followed the V5 protocol order for targeted evidence: hot-update the current
package, run target/disputed repeats, check negative controls, apply bounded fixes, and
rerun. It did not run the full public 50-case baseline+treatment certification because
target/disputed evidence failed the gate and no independent V5 shadow fixture exists in
the repository.

## Scope

- Date: 2026-07-08
- Base git commit before this patch set: `b36830626df5d61b9ffe4ec8d2a04f695e61e58c`
- Patch source: the commit containing this report
- Fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Model: `gpt-5.5`
- Judge model: `gpt-5.5`
- Codex CLI: `codex-cli 0.141.0`
- Protocol: `docs/benchmarks/v5-certification-protocol.md`

Runtime fingerprints:

- `runtime-fingerprint-strict.json`: initial V5 targeted pack, strict status `ok`
- `runtime-fingerprint-strict-rerun.json`: broad-trigger postpatch pack, strict status `ok`
- `runtime-fingerprint-strict-safe.json`: final safe pack, strict status `ok`

## Targeted Evidence

Selected target/disputed set:

```text
2,3,4,8,10,13,15,17,19,32,33,34,37,43,47,48,49,50
```

Initial treatment repeats:

| Run | Positive Mean | Overall Mean | Runtime Negative False Wake | Positive Owner Loaded | Required Visible Action | H Brake |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `treatment-targeted-repeat-1` | 0.600 | 0.833 | 0.333 | 0.333 | 0.067 | 0.000 |
| `treatment-targeted-repeat-2` | 0.467 | 0.722 | 0.000 | 0.267 | 0.000 | 0.000 |
| `treatment-targeted-repeat-3` | 0.667 | 0.889 | 0.333 | 0.333 | 0.200 | 0.000 |

Postpatch targeted diagnostic:

| Run | Positive Mean | Overall Mean | Runtime Negative False Wake | Positive Owner Loaded | Required Visible Action | H Brake |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `treatment-targeted-postpatch-repeat-1` | 0.667 | 0.889 | 0.333 | 0.200 | 0.067 | 0.000 |

Interpretation:

- Target/disputed repeats did not approach the V5 positive threshold.
- #4, #8, #13, #17, #33, and #34 remained `0` in the postpatch run.
- #37 improved from stable `0` to `1`, but still opened with a balanced "both sides are right" shape.
- #33/#34 remained the clearest hard failure: no Anti-Spiral brake before third rule/fallback.
- Loaded-required-visible-action stayed `0.000` in the postpatch targeted run.

## Negative Controls

Public negative set:

```text
7,25,28,29,31,32,35,43,44,45,46,47
```

| Run | Overall Mean | Final-Answer False Wake | Runtime False Wake | Stay-Asleep Rate | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `treatment-negative-controls` | 1.917 | 0.000 | 0.083 | 0.917 | #25 loaded MPG/SELA at runtime |
| `treatment-negative-controls-postpatch` | 2.000 | 0.000 | 0.250 | 0.750 | broad trigger prompt regressed #25/#28/#32 |
| `treatment-negative-controls-safe` | 2.000 | 0.000 | 0.000 | 1.000 | final safe package: all 12 direct stay-asleep |

Interpretation:

- The broad Codex default prompt extension was rejected because it improved neither the
  targeted gate nor runtime negative safety.
- The final safe patch keeps the old narrow activation surface and adds only
  `method-ref review direct` plus an MPG method-reference boundary.
- The safe negative run passes both V5 false-wakeup budgets.

## Patch Summary

Kept changes:

- Added V5 runtime action effects and concrete owner anchors to `scripts/primitives/manifest.json`.
- Added required visible action examples to `skills/using-mindthus/resources/fidelity-contract.md`.
- Added five calibration pairs for trend migration, next-token capability ceiling, coffee-bean single-factor copy, malformed AI yes/no replacement, and no-data AQM without computed verdict.
- Added 3L5S Anti-Spiral brake wording for third prompt rule/fallback/local patch.
- Added EDSP decision-context anti-mush wording.
- Added SELA handoff boundary for bare build-versus-rent cost choices.
- Added MPG method-reference evidence-review boundary.
- Kept Codex activation prompt narrow: `hard frame/whole/binary/spiral/no-data`, plus `method-ref review direct`.

Rejected change:

- Broad Codex activation prompt containing `root-cause/release/trend/...` because it pushed runtime false wake-up to `3/12`.

## External Audit Follow-Up

External review accepted the gate decision and the report's failed-patch conclusion. It
also tightened how this run should be interpreted:

- The three target/disputed repeats measured the current noise band: positive mean
  `0.467 / 0.600 / 0.667`. Public-run movements smaller than this band, including the
  earlier V3-to-V4 `+0.052` movement, should be treated as unproven until repeated.
- Target/disputed positive mean must not be quoted beside full 50-case positive mean as
  the same scale. This 18-case set is intentionally harder and was selected for
  problematic or disputed cases.
- H-group brake `0.000` here is not a regression from the full-run `0.500` value. The
  target set selected #33/#34, which were the failing H cases; the full-run passing H
  cases are not present in this subset.

Patch-type classification for future reports:

| Patch Type | Examples From This Run | Certification Treatment |
| --- | --- | --- |
| Fixture / calibration anchor | five new calibration pairs | count only after repeat evidence and negative controls hold |
| Mechanical / telemetry support | manifest action effects and owner anchors | count when runtime or judge telemetry shows movement |
| Contract example | fidelity-contract visible-action examples | count only when visible-action metrics move |
| Wording clause | 3L5S brake wording, EDSP anti-mush wording, SELA/MPG boundary wording | do not count as V5 progress by default |

The wording-clause changes are retained as documentation cleanup, but this run gives no
evidence that they moved behavior: H brake stayed `0.000`, loaded-required-visible-action
stayed `0.000` in the postpatch targeted run, and the single postpatch positive mean
`0.667` stayed inside the prepatch noise band. Future wording-only patches should be
rejected as certification progress unless they are coupled to a mechanical hook,
calibration anchor, runner change, host routing change, or repeatable telemetry movement.

## Disputed Case Notes

- #32: machine final answers stayed clean, but initial targeted repeats showed runtime over-wake in 2/3. The final safe negative run had no runtime load.
- #37: postpatch score moved to `1`, but the first sentence still used the failed balanced-mush opener.
- #43: stayed direct and full-score in all targeted/negative runs.
- #47: stayed direct and full-score in the final safe negative run.
- #50: machine scores remained relatively high, but this does not compensate for #48/#37 first-sentence discipline failures.

## Shadow Status

No independent V5 shadow fixture was found in the repository. `tests/router_wakeup_weak_cue_holdout_cases.md`
is not a valid certification shadow set because it is documented as a failed calibration pool.

The certification shadow set must be held by an external or otherwise independent owner.
A team-authored shadow set can be useful as a diagnostic fixture, but it cannot serve as
the anti-overfitting veto for V5 certification.

Certification language must therefore say:

```text
shadow controls not run; no independent V5 shadow fixture found in repo; public gains remain provisional and certification is blocked pending private or rotating shadow set.
```

## Gate Decision

Full 50-case V5 certification candidate was not run.

Reasons:

- Target/disputed repeat evidence failed.
- Required visible action rate remained too low.
- H-group Anti-Spiral brake rate remained `0.000` on targeted positives.
- A broad trigger patch regressed runtime negative controls.
- Independent shadow controls are unavailable.

Next useful work is not another full 50 run. It is a smaller runtime activation design:
make public target anchors wake the correct owner without increasing public negative or
shadow false wake-up, then rerun target/disputed `n >= 3` and only then start the full
50-case split-phase certification candidate.
