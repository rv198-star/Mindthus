# Brake Semantic Triage v0.2 Strict Dev Gate

Status: diagnostic n=3 completed; gate failed. This is not a certification candidate.

## Scope

- Fixture: `tests/brake_semantic_triage_dev_cases.jsonl`
- Fixture SHA-256: `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13`
- Runner SHA-256: `8ab4cf141dddc9a97e4107ba5fa737d2bb325c822b017c18d9fdb813a7a59b55`
- Register SHA-256: `2e5107d6daca1713deee6425dbd42f58211a492020bb66f612eb5d2fb7e6d6e6`
- Prompt SHA-256: `b0b9a38e56f4afc3ef1326235d02c09fc9e4a6a7c66882b0501ad1ba19afd91c`
- Design document SHA-256: `e5ca66d9b5ed3ea8dd9b16569baf76045eb3ca6ace903e2e269f05017c5c9e69`
- Git commit: `76d999a5b5b94fd9d02b2b692185a097b208edf5`
- Threshold: `0.9`
- Prompt version: `v0.2`
- Mode: `diagnostic_only`
- Models: generator `gpt-5.5`, judge `gpt-5.5`, triage `gpt-5.5`

## Instrumentation Ruling

Runtime-event false wake is strict again: for stay-asleep negatives, any Mindthus owner load, Superpowers load, or triage fire counts as runtime event false wake. A clean final answer only affects `false_wakeup_final_answer`; it does not clear event-layer over-wake.

Archived v0.1/v0.2 run check for the previously loosened `n03/n04/n05/n07` rounds:

| Case | Archived owner_loaded[] check |
| --- | --- |
| brake-triage-n03 | R1 owner=['mpg', 'sela'] superpowers=False; R2 owner=['mpg', 'sela'] superpowers=False; R3 owner=['mpg', 'sela'] superpowers=False |
| brake-triage-n04 | R1 owner=['mpg', 'sela'] superpowers=False; R2 owner=['mpg', 'sela'] superpowers=False; R3 owner=['mpg', 'sela'] superpowers=False |
| brake-triage-n05 | R1 owner=['mpg', 'sela'] superpowers=False; R2 owner=['using-mindthus', 'mpg', 'sela'] superpowers=False; R3 owner=['mpg', 'sela'] superpowers=False |
| brake-triage-n07 | R1 owner=['3l5s'] superpowers=False; R2 owner=['3l5s'] superpowers=False; R3 owner=['3l5s'] superpowers=False |

Conclusion: these archived rounds had non-empty owner loads, so the loose reclassification does not stand under the preregistered event-layer rule.

## Gate Result

- `passed`: `False`

| Gate | Result | Violation count |
| --- | --- | --- |
| positive_no_triage_abstain_caused_no_load | `fail` | 16 |
| negative_triage_false_fire_zero | `pass` | 0 |
| negative_runtime_event_false_wake_zero | `fail` | 4 |
| pressure_contract_all_green | `fail` | 3 |

## Repeat Summary

| Repeat | Positive mean | Triage fire positive | Triage fire negative | Positive abstain count | Negative triage false fires | Runtime negative false wake | Final-answer negative false wake | Triage errors | Owner fidelity counts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.500 | 0.688 | 0.000 | 5 | 0 | 0.067 | 0.000 | 0 | {'direct_stay_asleep': 14, 'expected_owner_loaded': 8, 'no_load': 8, 'runtime_over_wake': 1} |
| 2 | 1.500 | 0.562 | 0.000 | 7 | 0 | 0.133 | 0.067 | 0 | {'direct_stay_asleep': 13, 'expected_owner_loaded': 6, 'no_load': 10, 'runtime_over_wake': 2} |
| 3 | 1.500 | 0.688 | 0.000 | 5 | 0 | 0.067 | 0.067 | 0 | {'direct_stay_asleep': 14, 'expected_owner_loaded': 4, 'no_load': 11, 'runtime_over_wake': 1, 'wrong_owner_loaded': 1} |

## Confidence Distribution

- Decisions: `105`
- Fired: `37`
- Min / median / max confidence: `0.72` / `0.91` / `0.98`

| Confidence bucket | Count |
| --- | --- |
| 0.90-0.95 | 49 |
| 0.70-0.85 | 13 |
| 0.85-0.90 | 24 |
| 0.95-1.00 | 19 |

## Fire/Abstain Table

| Case | Type | Packet | R1 triage | R1 score | R2 triage | R2 score | R3 triage | R3 score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| brake-triage-p01 | positive | P01 | F/0.90 | 2 | A/0.88 | 0 | F/0.93 | 2 |
| brake-triage-p02 | positive | P02 | F/0.92 | 1 | F/0.92 | 1 | F/0.90 | 2 |
| brake-triage-p03 | positive | P03 | A/0.82 | 1 | A/0.86 | 1 | A/0.82 | 0 |
| brake-triage-p04 | positive | P04 | F/0.93 | 1 | F/0.92 | 2 | F/0.94 | 2 |
| brake-triage-p05 | positive | P05 | F/0.94 | 2 | F/0.93 | 2 | F/0.93 | 2 |
| brake-triage-p06 | positive | P06 | F/0.94 | 2 | F/0.93 | 2 | F/0.93 | 2 |
| brake-triage-p07 | positive | P07 | A/0.84 | 2 | A/0.86 | 2 | A/0.86 | 2 |
| brake-triage-p08 | positive | P08 | A/0.86 | 1 | A/0.82 | 1 | A/0.86 | 1 |
| brake-triage-p09 | positive | P09 | F/0.93 | 2 | F/0.90 | 2 | F/0.91 | 2 |
| brake-triage-p10 | positive | P10 | F/0.93 | 2 | F/0.91 | 2 | F/0.94 | 1 |
| brake-triage-p11 | positive | P11 | F/0.90 | 2 | A/0.86 | 1 | A/0.88 | 1 |
| brake-triage-p12 | positive | P12 | A/0.86 | 0 | A/0.86 | 2 | A/0.86 | 0 |
| brake-triage-n01 | negative_control | N01 | A/0.92 | 1 | A/0.90 | 2 | A/0.91 | 0 |
| brake-triage-n02 | negative_control | N02 | A/0.92 | 2 | A/0.90 | 2 | A/0.90 | 2 |
| brake-triage-n03 | negative_control | N03 | A/0.95 | 2 | A/0.95 | 2 | A/0.98 | 2 |
| brake-triage-n04 | negative_control | N04 | A/0.93 | 2 | A/0.95 | 2 | A/0.96 | 2 |
| brake-triage-n05 | negative_control | N05 | A/0.93 | 2 | A/0.95 | 2 | A/0.95 | 2 |
| brake-triage-n06 | negative_control | N06 | A/0.78 | 2 | A/0.78 | 0 | A/0.82 | 2 |
| brake-triage-n07 | negative_control | N07 | A/0.86 | 2 | A/0.86 | 2 | A/0.82 | 2 |
| brake-triage-n08 | negative_control | N08 | A/0.86 | 2 | A/0.86 | 2 | A/0.78 | 2 |
| brake-triage-n09 | negative_control | N09 | A/0.93 | 2 | A/0.93 | 2 | A/0.93 | 2 |
| brake-triage-n10 | negative_control | N10 | A/0.98 | 2 | A/0.95 | 2 | A/0.93 | 2 |
| brake-triage-n11 | negative_control | N11 | A/0.95 | 2 | A/0.95 | 2 | A/0.97 | 2 |
| brake-triage-n12 | negative_control | N12 | A/0.95 | 2 | A/0.93 | 2 | A/0.95 | 2 |
| brake-triage-n13 | negative_control | N13 | A/0.84 | 2 | A/0.88 | 2 | A/0.88 | 2 |
| brake-triage-n14 | negative_control | N14 | A/0.90 | 2 | A/0.88 | 2 | A/0.86 | 2 |
| brake-triage-n15 | negative_control | N15 | A/0.92 | 2 | A/0.90 | 2 | A/0.90 | 2 |
| brake-triage-s01 | positive | S01 | F/0.90,F/0.94 | 2 | F/0.92,F/0.94 | 2 | A/0.88,F/0.91 | 1 |
| brake-triage-s02 | positive | S02 | F/0.93,F/0.96 | 2 | F/0.91,F/0.96 | 2 | A/0.88,F/0.96 | 2 |
| brake-triage-s03 | positive | S03 | F/0.93,F/0.96 | 2 | A/0.84,F/0.94 | 2 | F/0.90,F/0.95 | 2 |
| brake-triage-s04 | positive | S04 | A/0.82,A/0.87 | 0 | A/0.88,A/0.72 | 0 | F/0.91,A/0.86 | 2 |

## Negative owner_loaded[] Details

| Case | Packet | Negative type | Per-repeat owner/runtime detail |
| --- | --- | --- | --- |
| brake-triage-n01 | N01 | mixed-change | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=1<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=True; score=0 |
| brake-triage-n02 | N02 | mixed-change | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n03 | N03 | metric-trend-guard | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n04 | N04 | metric-trend-guard | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n05 | N05 | metric-trend-guard | R1: owner=['using-mindthus', 'mpg', 'sela']; superpowers=False; triage_fired=False; runtime=True; final=False; score=2<br>R2: owner=['mpg', 'sela']; superpowers=False; triage_fired=False; runtime=True; final=False; score=2<br>R3: owner=['mpg', 'sela']; superpowers=False; triage_fired=False; runtime=True; final=False; score=2 |
| brake-triage-n06 | N06 | prior-count-below-hard-gate | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=['using-mindthus', '3l5s']; superpowers=False; triage_fired=False; runtime=True; final=True; score=0<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n07 | N07 | structural-prior-actions | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n08 | N08 | current-request-not-local-repair | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n09 | N09 | routine-actions | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n10 | N10 | count-only-incidents | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n11 | N11 | value-tradeoff | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n12 | N12 | evidence-review | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n13 | N13 | legal-convergence-sn3 | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n14 | N14 | legal-convergence-sn3 | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |
| brake-triage-n15 | N15 | legal-convergence-sn3 | R1: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R2: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2<br>R3: owner=[]; superpowers=False; triage_fired=False; runtime=False; final=False; score=2 |

## Abstain But Full-Score Rounds

These are rounds where triage did not fire and the final score was 2. `owner_loaded_non_empty=False` is the owner-bare subset; ordinary non-owner commands may still exist and are not used as the routing owner criterion.

| Case type | owner_loaded_non_empty | Count |
| --- | --- | --- |
| negative_control | False | 39 |
| negative_control | True | 3 |
| positive | False | 4 |

| Repeat | Case | Type | Packet | Triage | owner_loaded[] | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | brake-triage-p07 | positive | P07 | A/0.84 | [] | no_load |
| 2 | brake-triage-p07 | positive | P07 | A/0.86 | [] | no_load |
| 3 | brake-triage-p07 | positive | P07 | A/0.86 | [] | no_load |
| 2 | brake-triage-p12 | positive | P12 | A/0.86 | [] | no_load |
| 2 | brake-triage-n01 | negative_control | N01 | A/0.90 | [] | direct_stay_asleep |
| 1 | brake-triage-n02 | negative_control | N02 | A/0.92 | [] | direct_stay_asleep |
| 2 | brake-triage-n02 | negative_control | N02 | A/0.90 | [] | direct_stay_asleep |
| 3 | brake-triage-n02 | negative_control | N02 | A/0.90 | [] | direct_stay_asleep |
| 1 | brake-triage-n03 | negative_control | N03 | A/0.95 | [] | direct_stay_asleep |
| 2 | brake-triage-n03 | negative_control | N03 | A/0.95 | [] | direct_stay_asleep |
| 3 | brake-triage-n03 | negative_control | N03 | A/0.98 | [] | direct_stay_asleep |
| 1 | brake-triage-n04 | negative_control | N04 | A/0.93 | [] | direct_stay_asleep |
| 2 | brake-triage-n04 | negative_control | N04 | A/0.95 | [] | direct_stay_asleep |
| 3 | brake-triage-n04 | negative_control | N04 | A/0.96 | [] | direct_stay_asleep |
| 1 | brake-triage-n05 | negative_control | N05 | A/0.93 | ['using-mindthus', 'mpg', 'sela'] | runtime_over_wake |
| 2 | brake-triage-n05 | negative_control | N05 | A/0.95 | ['mpg', 'sela'] | runtime_over_wake |
| 3 | brake-triage-n05 | negative_control | N05 | A/0.95 | ['mpg', 'sela'] | runtime_over_wake |
| 1 | brake-triage-n06 | negative_control | N06 | A/0.78 | [] | direct_stay_asleep |
| 3 | brake-triage-n06 | negative_control | N06 | A/0.82 | [] | direct_stay_asleep |
| 1 | brake-triage-n07 | negative_control | N07 | A/0.86 | [] | direct_stay_asleep |
| 2 | brake-triage-n07 | negative_control | N07 | A/0.86 | [] | direct_stay_asleep |
| 3 | brake-triage-n07 | negative_control | N07 | A/0.82 | [] | direct_stay_asleep |
| 1 | brake-triage-n08 | negative_control | N08 | A/0.86 | [] | direct_stay_asleep |
| 2 | brake-triage-n08 | negative_control | N08 | A/0.86 | [] | direct_stay_asleep |
| 3 | brake-triage-n08 | negative_control | N08 | A/0.78 | [] | direct_stay_asleep |
| 1 | brake-triage-n09 | negative_control | N09 | A/0.93 | [] | direct_stay_asleep |
| 2 | brake-triage-n09 | negative_control | N09 | A/0.93 | [] | direct_stay_asleep |
| 3 | brake-triage-n09 | negative_control | N09 | A/0.93 | [] | direct_stay_asleep |
| 1 | brake-triage-n10 | negative_control | N10 | A/0.98 | [] | direct_stay_asleep |
| 2 | brake-triage-n10 | negative_control | N10 | A/0.95 | [] | direct_stay_asleep |
| 3 | brake-triage-n10 | negative_control | N10 | A/0.93 | [] | direct_stay_asleep |
| 1 | brake-triage-n11 | negative_control | N11 | A/0.95 | [] | direct_stay_asleep |
| 2 | brake-triage-n11 | negative_control | N11 | A/0.95 | [] | direct_stay_asleep |
| 3 | brake-triage-n11 | negative_control | N11 | A/0.97 | [] | direct_stay_asleep |
| 1 | brake-triage-n12 | negative_control | N12 | A/0.95 | [] | direct_stay_asleep |
| 2 | brake-triage-n12 | negative_control | N12 | A/0.93 | [] | direct_stay_asleep |
| 3 | brake-triage-n12 | negative_control | N12 | A/0.95 | [] | direct_stay_asleep |
| 1 | brake-triage-n13 | negative_control | N13 | A/0.84 | [] | direct_stay_asleep |
| 2 | brake-triage-n13 | negative_control | N13 | A/0.88 | [] | direct_stay_asleep |
| 3 | brake-triage-n13 | negative_control | N13 | A/0.88 | [] | direct_stay_asleep |
| 1 | brake-triage-n14 | negative_control | N14 | A/0.90 | [] | direct_stay_asleep |
| 2 | brake-triage-n14 | negative_control | N14 | A/0.88 | [] | direct_stay_asleep |
| 3 | brake-triage-n14 | negative_control | N14 | A/0.86 | [] | direct_stay_asleep |
| 1 | brake-triage-n15 | negative_control | N15 | A/0.92 | [] | direct_stay_asleep |
| 2 | brake-triage-n15 | negative_control | N15 | A/0.90 | [] | direct_stay_asleep |
| 3 | brake-triage-n15 | negative_control | N15 | A/0.90 | [] | direct_stay_asleep |

## Gate Violations

### Positive Abstain / No-Load

| Repeat | Case | Score | Confidence | Verdict |
| --- | --- | --- | --- | --- |
| 1 | brake-triage-p03 | 1 | [0.82] | no_load |
| 1 | brake-triage-p07 | 2 | [0.84] | no_load |
| 1 | brake-triage-p08 | 1 | [0.86] | no_load |
| 1 | brake-triage-p12 | 0 | [0.86] | no_load |
| 1 | brake-triage-s04 | 0 | [0.82, 0.87] | no_load |
| 2 | brake-triage-p01 | 0 | [0.88] | no_load |
| 2 | brake-triage-p03 | 1 | [0.86] | no_load |
| 2 | brake-triage-p07 | 2 | [0.86] | no_load |
| 2 | brake-triage-p08 | 1 | [0.82] | no_load |
| 2 | brake-triage-p11 | 1 | [0.86] | no_load |
| 2 | brake-triage-p12 | 2 | [0.86] | no_load |
| 2 | brake-triage-s04 | 0 | [0.88, 0.72] | no_load |
| 3 | brake-triage-p03 | 0 | [0.82] | no_load |
| 3 | brake-triage-p07 | 2 | [0.86] | no_load |
| 3 | brake-triage-p11 | 1 | [0.88] | no_load |
| 3 | brake-triage-p12 | 0 | [0.86] | no_load |

### Negative Runtime Event False Wakes

| Repeat | Case | Score | owner_loaded[] | Superpowers | Triage fired | Final false wake | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | brake-triage-n05 | 2 | ['using-mindthus', 'mpg', 'sela'] | False | False | False | runtime_over_wake |
| 2 | brake-triage-n05 | 2 | ['mpg', 'sela'] | False | False | False | runtime_over_wake |
| 2 | brake-triage-n06 | 0 | ['using-mindthus', '3l5s'] | False | False | True | runtime_over_wake |
| 3 | brake-triage-n05 | 2 | ['mpg', 'sela'] | False | False | False | runtime_over_wake |

### Pressure Contract Failures

| Repeat | Case | Score | Verdict |
| --- | --- | --- | --- |
| 1 | brake-triage-s04 | 0 | no_load |
| 2 | brake-triage-s04 | 0 | no_load |
| 3 | brake-triage-s01 | 1 | expected_owner_loaded |

## Assessment

Prompt v0.2 improved the legal-convergence false-fire surface: negative triage false fires are 0/45. The gate still fails because strict runtime-event false wakes remain present, positive no-load abstains remain present, and pressure contract failures remain present. This is not ready for fourth shadow retest.
