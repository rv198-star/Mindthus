# Router Wake-Up Weak-Cue Calibration Run

Run date: 2026-06-17

Purpose: test whether the first weak-cue holdout pool has enough discriminability to
continue into a full A/B certification run.

## Sample

Source pool: `tests/router_wakeup_weak_cue_holdout_cases.md`

Pilot size:

- 2 baseline runs.
- 2 treatment runs.
- 10 scenarios per run.
- 6 positive wake-up cases per run.
- 4 adjacent skip traps per run.

Isolation:

- Baseline agents were told to use only `git show HEAD:skills/using-mindthus/SKILL.md`.
- Treatment agents were told to use only working-tree `skills/using-mindthus/SKILL.md`.
- Agents were not shown the weak-cue casebook because it contains expected owners.
- Expected owners were applied after collection by the controller.

## Result

Runner command:

```bash
python3 scripts/router-wakeup-ab.py \
  --scores /tmp/router-wakeup-weak-cue-v1-calibration.jsonl \
  --experiment holdout \
  --json
```

Runner result:

```text
certified=false
failed_checks=baseline-ceiling, positive-lift, mcnemar, method-lift-edsp,
method-mcnemar-edsp, method-lift-mpg, method-mcnemar-mpg, method-lift-sela,
method-mcnemar-sela
```

Observed metrics:

- Baseline positive wake-up recall: 100%.
- Treatment positive wake-up recall: 100%.
- Lift: 0 percentage points.
- McNemar p: 1.0.
- Baseline skip precision: 100%.
- Treatment skip precision: 100%.
- Adjacent absorption: 0%.
- Over-methodization: 0%.

## Interpretation

Do not expand this sample.

The weak-cue v1 pool still exposes the owner too strongly for the current baseline.
It is better than Scenario 20-25 as a prompt style, but it does not create measurable
headroom for wake-up lift. Continuing to the full holdout sample would spend runs on a
set that has already failed the discriminability gate.

This result does not show that the router change is useless. It shows that both the
known set and weak-cue v1 are too easy for the current baseline. The next certification
attempt should move to real-use replay or substantially more indirect, context-rich
cases where the expected owner is latent in the transcript rather than concentrated in
one short prompt.

## Next Sampling Direction

Use real-use replay first:

- collect at least 50 historical or redacted routing moments;
- label the active judgment object before seeing either answer;
- replay each transcript against baseline and treatment;
- score with the same JSONL schema;
- stop early if baseline triggers `baseline-ceiling`.

If synthetic cases are still needed, build them from multi-turn transcripts where the
low-frequency owner emerges from accumulated context, not from a single sentence.
