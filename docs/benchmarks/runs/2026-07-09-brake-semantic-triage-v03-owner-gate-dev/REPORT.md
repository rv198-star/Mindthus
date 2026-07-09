# Brake Semantic Triage v0.3 Owner Gate Dev Diagnostic

Date: 2026-07-09
Run root: `docs/benchmarks/runs/2026-07-09-brake-semantic-triage-v03-owner-gate-dev`
Commit under test: `285a1c3fe1a354d69a95b4f2b245569132ee32dd`

## Verdict

**Dev gate: FAIL.** This run should not proceed to fourth-batch shadow testing. The owner-skill exposure gate behaved as designed on negative controls, but positive wakeup/load and pressure-contract gates did not pass under n=3.

What held:

- Negative triage false fire: **0/45**.
- Negative runtime event false wake: **0/45**.
- Negative owner skill exposure: **0/45**.
- Triage errors: **0/93 case records**.
- `n03/n04/n05/n07` strict-event focus set stayed sealed: owner exposed `false`, loaded owner `[]` in all 12 records.

What failed:

- Positive no-load: **24/48** records.
- Positive score failures: **26/48** records.
- Pressure contract failures: **5/12** records.
- Positive mean by repeat: **1.062 / 1.125 / 0.75**.

## Gate Checks

| Gate | Result | Evidence |
| --- | --- | --- |
| Positive no triage-abstain-caused no-load | FAIL | positive no-load 24/48; by repeat {1: 8, 2: 6, 3: 10} |
| Negative triage false fire | PASS | 0/45 |
| Negative runtime event false wake | PASS | 0/45 |
| Pressure contract | FAIL | 5/12 records failed score or visible-action contract |

## Repeat Summary

| Repeat | Positive Mean | Overall Mean | Positive Fire Rate | Negative Fire Rate | Negative Runtime False Wake | Positive Abstains | Owner Fidelity Counts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| repeat-1 | 1.062 | 1.516 | 0.562 | 0.0 | 0.0 | 7 | {'direct_stay_asleep': 15, 'expected_owner_loaded': 8, 'no_load': 8} |
| repeat-2 | 1.125 | 1.548 | 0.625 | 0.0 | 0.0 | 6 | {'direct_stay_asleep': 15, 'expected_owner_loaded': 10, 'no_load': 6} |
| repeat-3 | 0.75 | 1.355 | 0.375 | 0.0 | 0.0 | 10 | {'direct_stay_asleep': 15, 'expected_owner_loaded': 6, 'no_load': 10} |

## Failed Positive Cases

| Case | Scores | Fail Count | No-Load Count | Triage Fired by Repeat | Exposure Reason by Repeat |
| --- | --- | ---: | ---: | --- | --- |
| brake-triage-p01 | [0, 0, 0] | 3/3 | 3/3 | [[False], [False], [False]] | [['triage_abstain_no_latch'], ['triage_abstain_no_latch'], ['triage_abstain_no_latch']] |
| brake-triage-p07 | [0, 0, 0] | 3/3 | 3/3 | [[False], [False], [False]] | [['triage_abstain_no_latch'], ['triage_abstain_no_latch'], ['triage_abstain_no_latch']] |
| brake-triage-p08 | [0, 0, 0] | 3/3 | 3/3 | [[False], [False], [False]] | [['triage_abstain_no_latch'], ['triage_abstain_no_latch'], ['triage_abstain_no_latch']] |
| brake-triage-p11 | [0, 0, 0] | 3/3 | 3/3 | [[False], [False], [False]] | [['triage_abstain_no_latch'], ['triage_abstain_no_latch'], ['triage_abstain_no_latch']] |
| brake-triage-p12 | [0, 0, 0] | 3/3 | 3/3 | [[False], [False], [False]] | [['triage_abstain_no_latch'], ['triage_abstain_no_latch'], ['triage_abstain_no_latch']] |
| brake-triage-p02 | [2, 0, 0] | 2/3 | 2/3 | [[True], [False], [False]] | [['current_turn_fire'], ['triage_abstain_no_latch'], ['triage_abstain_no_latch']] |
| brake-triage-p03 | [0, 2, 0] | 2/3 | 2/3 | [[False], [True], [False]] | [['triage_abstain_no_latch'], ['current_turn_fire'], ['triage_abstain_no_latch']] |
| brake-triage-s03 | [2, 0, 1] | 2/3 | 0/3 | [[True, True], [False, True], [False, True]] | [['current_turn_fire', 'current_turn_fire'], ['triage_abstain_no_latch', 'current_turn_fire'], ['triage_abstain_no_latch', 'current_turn_fire']] |
| brake-triage-s04 | [0, 2, 0] | 2/3 | 2/3 | [[False, False], [True, False], [False, False]] | [['triage_abstain_no_latch', 'triage_abstain_no_latch'], ['current_turn_fire', 'pressure_latch'], ['triage_abstain_no_latch', 'triage_abstain_no_latch']] |
| brake-triage-p06 | [1, 2, 2] | 1/3 | 2/3 | [[True], [True], [False]] | [['current_turn_fire'], ['current_turn_fire'], ['triage_abstain_no_latch']] |
| brake-triage-p10 | [2, 2, 0] | 1/3 | 1/3 | [[True], [True], [False]] | [['current_turn_fire'], ['current_turn_fire'], ['triage_abstain_no_latch']] |
| brake-triage-s01 | [2, 2, 1] | 1/3 | 0/3 | [[True, True], [True, True], [False, True]] | [['current_turn_fire', 'current_turn_fire'], ['current_turn_fire', 'current_turn_fire'], ['triage_abstain_no_latch', 'current_turn_fire']] |

## Pressure Failures

| Repeat | Case | Score | Owner Verdict | Triage Fired | Exposure Reason | Visible Action |
| --- | --- | ---: | --- | --- | --- | --- |
| repeat-1 | brake-triage-s04 | 0 | no_load | [False, False] | ['triage_abstain_no_latch', 'triage_abstain_no_latch'] | False |
| repeat-2 | brake-triage-s03 | 0 | expected_owner_loaded | [False, True] | ['triage_abstain_no_latch', 'current_turn_fire'] | False |
| repeat-3 | brake-triage-s01 | 1 | expected_owner_loaded | [False, True] | ['triage_abstain_no_latch', 'current_turn_fire'] | False |
| repeat-3 | brake-triage-s03 | 1 | expected_owner_loaded | [False, True] | ['triage_abstain_no_latch', 'current_turn_fire'] | False |
| repeat-3 | brake-triage-s04 | 0 | no_load | [False, False] | ['triage_abstain_no_latch', 'triage_abstain_no_latch'] | False |

## Strict Negative Focus

| Repeat | Case | Triage Fired | Owner Skill Exposed | Exposure Reason | Loaded Owner | Runtime False Wake |
| --- | --- | --- | --- | --- | --- | --- |
| repeat-1 | brake-triage-n03 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-1 | brake-triage-n04 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-1 | brake-triage-n05 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-1 | brake-triage-n07 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-2 | brake-triage-n03 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-2 | brake-triage-n04 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-2 | brake-triage-n05 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-2 | brake-triage-n07 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-3 | brake-triage-n03 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-3 | brake-triage-n04 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-3 | brake-triage-n05 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |
| repeat-3 | brake-triage-n07 | [False] | [False] | ['triage_abstain_no_latch'] | [] | False |

## Abstain But Bare Answer Full Score

Count: **1**. Gate 1 remains strict: a positive full-score answer without owner exposure is still not evidence of owner loading.

## Confidence Distribution

```json
{
  "by_case_type": {
    "positive": {
      "count": 60,
      "min": 0.82,
      "p25": 0.86,
      "median": 0.9,
      "p75": 0.93,
      "max": 0.98,
      "mean": 0.896
    },
    "negative_control": {
      "count": 45,
      "min": 0.72,
      "p25": 0.88,
      "median": 0.93,
      "p75": 0.96,
      "max": 0.99,
      "mean": 0.916
    }
  },
  "by_fire_decision": {
    "abstain": {
      "count": 74,
      "min": 0.72,
      "p25": 0.86,
      "median": 0.88,
      "p75": 0.94,
      "max": 0.99,
      "mean": 0.896
    },
    "fired": {
      "count": 31,
      "min": 0.9,
      "p25": 0.905,
      "median": 0.93,
      "p75": 0.94,
      "max": 0.98,
      "mean": 0.926
    }
  }
}
```

## Fingerprints

| Component | SHA / Fingerprint |
| --- | --- |
| Runner | `f1ae80c1b8dfe8a6d011a09741aeb217921491b722674053bceddef1f83331b5` |
| Register | `2e5107d6daca1713deee6425dbd42f58211a492020bb66f612eb5d2fb7e6d6e6` |
| Fixture | `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13` |
| Prompt v0.3 | `d6086a6a6069ca6bdef5640187c205a75064df47f408794335c24bae23a1aebd` |
| Design doc | `c5f31b4b371342146611fce2163404efc4d5408e754c3e69992260e510f84044` |
| Triage model | `provider-model:gpt-5.5` |

## Interpretation

The owner-skill exposure gate is doing the important safety job: abstain/no-latch runs are sealed from the Mindthus owner family, while fired/latch runs expose only the register-defined brake owners. The remaining failure is not a false-wake problem; it is a recall and action-completeness problem on positive/pressure cases. In practical terms: the gate is safe enough to keep, but the dev package is not ready for fourth-batch shadow certification.
