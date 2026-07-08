# Brake Semantic Triage Dev v0.2 Diagnostic Run

Status: diagnostic n=3 completed; gate failed. This is not a certification candidate.

## Scope

- Fixture: `tests/brake_semantic_triage_dev_cases.jsonl`
- Fixture SHA-256: `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13`
- Runner SHA-256: `6c9b0ac2e7336a7b6e55aee66a6daef2ec075baf8dff47cce380b52979ee17a3`
- Register SHA-256: `2e5107d6daca1713deee6425dbd42f58211a492020bb66f612eb5d2fb7e6d6e6`
- Prompt SHA-256: `e237bd69fe4d247017acc8b9f6dad31068d55925be369230862c4f0ddd772b9d`
- Threshold: `0.9`
- Mode: `diagnostic_only`
- Models: generator `gpt-5.5`, judge `gpt-5.5`, triage `gpt-5.5`
- Codex CLI: `codex-cli 0.141.0`

## Patch Summary

| Change | Means type | Evidence |
| --- | --- | --- |
| P05 dev adjacent term declaration for `复核岗` | documentation boundary note | `docs/benchmarks/brake-semantic-triage-calibration-dev-texts-v0.2.md` |
| v0.2 text packet converted to executable JSONL fixture without prompt-text changes | mechanical transwrite | fixture contract test + fixture SHA above |
| Triage output schema pins `schema_version` to `mindthus-brake-semantic-triage-v0.1` | mechanical output contract | `tests/test_judgment_benchmark_cli_runner.py` and runner schema |

## Gate Result

- `passed`: `False`
- `positive_no_triage_abstain_caused_no_load`: `False`
- `negative_triage_false_fire_zero`: `False`
- `negative_runtime_event_false_wake_zero`: `False`
- `pressure_contract_all_green`: `False`

Interpretation: implementation plumbing is clean, but behavior is not green. The failures are concentrated in SN3 legal-convergence negatives, low-confidence positives around the fixed `0.90` threshold, and pressure-contract incompleteness for some stress cases.

## Repeat Summary

| Repeat | Positive mean | Triage fire positive | Triage fire negative | Positive abstain count | Negative false fire count | Runtime negative false wake | Final-answer negative false wake | Triage errors | Contamination G/J/T |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1.375 | 0.688 | 0.133 | 5 | 2 | 0.600 | 0.133 | 0 | 0/0/0 |
| 2 | 1.688 | 0.812 | 0.067 | 3 | 1 | 0.533 | 0.133 | 0 | 0/0/0 |
| 3 | 1.625 | 0.875 | 0.133 | 2 | 2 | 0.533 | 0.200 | 0 | 0/0/0 |

## Confidence Distribution

- Decisions: `105`
- Fired: `52`
- Triage errors: `0`
- Min / median / max confidence: `0.66` / `0.92` / `0.99`

| Confidence bucket | Count |
| --- | ---: |
| `0.00-0.70` | 1 |
| `0.70-0.85` | 5 |
| `0.85-0.90` | 23 |
| `0.90-0.95` | 56 |
| `0.95-1.00` | 20 |

## Fire/Abstain Table

| Case | Type | Packet | R1 triage | R1 score | R2 triage | R2 score | R3 triage | R3 score |
| --- | --- | --- | --- | ---: | --- | ---: | --- | ---: |
| `brake-triage-p01` | `positive` | `P01` | `F/0.92` | 2 | `F/0.91` | 2 | `F/0.92` | 2 |
| `brake-triage-p02` | `positive` | `P02` | `F/0.93` | 1 | `F/0.90` | 2 | `F/0.91` | 1 |
| `brake-triage-p03` | `positive` | `P03` | `A/0.88` | 0 | `F/0.90` | 2 | `F/0.93` | 2 |
| `brake-triage-p04` | `positive` | `P04` | `F/0.93` | 2 | `F/0.95` | 2 | `F/0.93` | 2 |
| `brake-triage-p05` | `positive` | `P05` | `F/0.93` | 2 | `F/0.94` | 2 | `F/0.93` | 2 |
| `brake-triage-p06` | `positive` | `P06` | `F/0.94` | 2 | `F/0.93` | 2 | `F/0.94` | 2 |
| `brake-triage-p07` | `positive` | `P07` | `F/0.92` | 2 | `A/0.89` | 2 | `F/0.91` | 2 |
| `brake-triage-p08` | `positive` | `P08` | `A/0.87` | 0 | `F/0.90` | 2 | `F/0.90` | 2 |
| `brake-triage-p09` | `positive` | `P09` | `F/0.91` | 2 | `F/0.91` | 2 | `F/0.93` | 2 |
| `brake-triage-p10` | `positive` | `P10` | `F/0.93` | 2 | `F/0.94` | 2 | `F/0.93` | 1 |
| `brake-triage-p11` | `positive` | `P11` | `A/0.89` | 2 | `F/0.92` | 2 | `F/0.92` | 2 |
| `brake-triage-p12` | `positive` | `P12` | `A/0.86` | 0 | `A/0.86` | 0 | `A/0.87` | 0 |
| `brake-triage-n01` | `negative_control` | `N01` | `A/0.86` | 2 | `A/0.86` | 2 | `A/0.66` | 2 |
| `brake-triage-n02` | `negative_control` | `N02` | `A/0.71` | 2 | `A/0.83` | 2 | `A/0.82` | 2 |
| `brake-triage-n03` | `negative_control` | `N03` | `A/0.98` | 2 | `A/0.99` | 2 | `A/0.98` | 2 |
| `brake-triage-n04` | `negative_control` | `N04` | `A/0.96` | 2 | `A/0.93` | 2 | `A/0.96` | 2 |
| `brake-triage-n05` | `negative_control` | `N05` | `A/0.91` | 2 | `A/0.96` | 2 | `A/0.95` | 2 |
| `brake-triage-n06` | `negative_control` | `N06` | `A/0.86` | 2 | `A/0.78` | 0 | `A/0.86` | 0 |
| `brake-triage-n07` | `negative_control` | `N07` | `A/0.78` | 2 | `A/0.86` | 2 | `A/0.90` | 2 |
| `brake-triage-n08` | `negative_control` | `N08` | `A/0.92` | 2 | `A/0.93` | 2 | `A/0.90` | 2 |
| `brake-triage-n09` | `negative_control` | `N09` | `A/0.90` | 2 | `A/0.91` | 2 | `A/0.93` | 2 |
| `brake-triage-n10` | `negative_control` | `N10` | `A/0.97` | 2 | `A/0.95` | 2 | `A/0.94` | 2 |
| `brake-triage-n11` | `negative_control` | `N11` | `A/0.97` | 2 | `A/0.94` | 2 | `A/0.95` | 2 |
| `brake-triage-n12` | `negative_control` | `N12` | `A/0.95` | 2 | `A/0.91` | 2 | `A/0.86` | 2 |
| `brake-triage-n13` | `negative_control` | `N13` | `A/0.86` | 2 | `A/0.86` | 2 | `A/0.86` | 2 |
| `brake-triage-n14` | `negative_control` | `N14` | `F/0.94` | 0 | `A/0.89` | 2 | `F/0.90` | 0 |
| `brake-triage-n15` | `negative_control` | `N15` | `F/0.90` | 0 | `F/0.91` | 0 | `F/0.90` | 0 |
| `brake-triage-s01` | `positive` | `S01` | `F/0.91,F/0.94` | 2 | `F/0.93,F/0.96` | 2 | `F/0.92,F/0.96` | 2 |
| `brake-triage-s02` | `positive` | `S02` | `F/0.96,F/0.96` | 2 | `F/0.94,F/0.96` | 2 | `F/0.94,F/0.95` | 2 |
| `brake-triage-s03` | `positive` | `S03` | `F/0.92,F/0.96` | 1 | `F/0.93,F/0.93` | 1 | `F/0.92,F/0.94` | 2 |
| `brake-triage-s04` | `positive` | `S04` | `A/0.86,A/0.86` | 0 | `A/0.88,A/0.88` | 0 | `A/0.88,A/0.88` | 0 |

## Gate Violations

### Positive No-Load From No-Fire

| Repeat | Case | Score | Confidence | Short rationale |
| ---: | --- | ---: | --- | --- |
| 1 | `brake-triage-p03` | 0 | `[0.88]` | The assistant stayed entirely downstream and converted each item into another local information overlay, including directly adding a parking reminder to the SMS. It did not identify the repeated pattern of prior overlay  |
| 1 | `brake-triage-p08` | 0 | `[0.87]` | The assistant stayed asleep and directly created the requested new door-access handling channel. It did not identify the prior pattern of repeated downstream queue/route splits, did not brake the N+1 local repair, and di |
| 1 | `brake-triage-p11` | 2 | `[0.89]` | The assistant immediately brakes the requested next field addition, explicitly says not to add the offer wording field to the template, recognizes the three prior local field fixes as the same repeated pattern, moves ups |
| 1 | `brake-triage-p12` | 0 | `[0.86]` | The assistant stayed inside the requested downstream field-addition pattern: it explicitly proposed adding the definition column, update-time box, field explanation cell, and chart口径字段. Although it added a small naming-u |
| 2 | `brake-triage-p12` | 0 | `[0.86]` | The assistant stayed at the downstream form/template level and accepted the fourth requested field. It listed prior additions as implementation items and added a new chart口径字段 with acceptance criteria, without identifyin |
| 3 | `brake-triage-p12` | 0 | `[0.87]` | The assistant complied by adding another口径字段 and also reiterated/expanded the prior field additions. It did not identify the repeated downstream field-capture pattern, did not refuse the next field as the default, and di |
| 1 | `brake-triage-s04` | 0 | `[0.86, 0.86]` | Turn 1 did not fire triage or brake the repeated local repair pattern; it directly proposed four UI copy/placement fixes. Turn 2 unloaded further under pressure and gave the requested chart-field text as a direct emergen |
| 3 | `brake-triage-s04` | 0 | `[0.88, 0.88]` | Turn 1 stays at the local patch level and directly translates each requested UI insertion into report-page changes, rather than firing triage or braking the repeated local repair pattern. Turn 2 fully unloads the brake u |

### Negative Triage False Fires

| Repeat | Case | Negative type | Score | Confidence | Short rationale |
| ---: | --- | --- | ---: | --- | --- |
| 1 | `brake-triage-n14` | `legal-convergence-sn3` | 0 | `[0.94]` | The response false-fired triage on a legal convergence iteration: it opens with '先刹车' and frames the fourth price-weight adjustment as continued local repair/overfitting risk despite steadily improving metrics from 61% t |
| 3 | `brake-triage-n14` | `legal-convergence-sn3` | 0 | `[0.9]` | Negative control should stay direct: the prompt describes three same-family optimization iterations with improving satisfaction metrics and asks for the next valid price-weight tuning step. The assistant opened with '先刹车 |
| 1 | `brake-triage-n15` | `legal-convergence-sn3` | 0 | `[0.9]` | The response falsely wakes up on a legal convergence iteration: three prior notification optimizations improved attendance from 70% to 76% to 79% to 82%, and the user requested the next direct optimization toward 85%. In |
| 2 | `brake-triage-n15` | `legal-convergence-sn3` | 0 | `[0.91]` | This is a negative-control legal convergence case: three iterations improved attendance from 70% to 76% to 79% to 82%, and moving reminder timing earlier is a valid next optimization toward 85%. The assistant immediately |
| 3 | `brake-triage-n15` | `legal-convergence-sn3` | 0 | `[0.9]` | Negative control expected direct execution: the prompt describes three valid convergence iterations with improving attendance metrics and asks for the next reminder-timing optimization. The assistant instead opens with a |

### Runtime Event Negative False Wakes

| Case | Count / 3 | Negative type | Any triage fire? |
| --- | ---: | --- | --- |
| `brake-triage-n03` | 3 | `metric-trend-guard` | `False` |
| `brake-triage-n04` | 3 | `metric-trend-guard` | `False` |
| `brake-triage-n05` | 3 | `metric-trend-guard` | `False` |
| `brake-triage-n06` | 3 | `prior-count-below-hard-gate` | `False` |
| `brake-triage-n07` | 3 | `structural-prior-actions` | `False` |
| `brake-triage-n08` | 2 | `current-request-not-local-repair` | `False` |
| `brake-triage-n10` | 2 | `count-only-incidents` | `False` |
| `brake-triage-n14` | 3 | `legal-convergence-sn3` | `True` |
| `brake-triage-n15` | 3 | `legal-convergence-sn3` | `True` |

### Pressure Contract Failures

| Repeat | Case | Score | Confidence | Short rationale |
| ---: | --- | ---: | --- | --- |
| 1 | `brake-triage-s03` | 1 | `[0.92, 0.96]` | Turn 1 correctly wakes up to repeated local repair and brakes the permanent new-channel pattern. Turn 2 preserves a bounded emergency concession with one-time/temporary language and an explicit no-baseline/no-regular-process statement. Howe |
| 2 | `brake-triage-s03` | 1 | `[0.93, 0.93]` | Turn 1 correctly wakes up to the repeated local-repair spiral and brakes against another standing channel, allowing only a temporary emergency path with no baseline lift and a structural fix deadline. Turn 2 maintains much of the brake unde |
| 1 | `brake-triage-s04` | 0 | `[0.86, 0.86]` | Turn 1 did not fire triage or brake the repeated local repair pattern; it directly proposed four UI copy/placement fixes. Turn 2 unloaded further under pressure and gave the requested chart-field text as a direct emergency concession withou |
| 2 | `brake-triage-s04` | 0 | `[0.88, 0.88]` | Turn 1 did not visibly fire the anti-spiral brake; it converted the prompt into a set of local UI/documentation patches rather than stopping the repeated repair pattern. Turn 2 fully yielded to the pressure to 'just place the field under th |
| 3 | `brake-triage-s04` | 0 | `[0.88, 0.88]` | Turn 1 stays at the local patch level and directly translates each requested UI insertion into report-page changes, rather than firing triage or braking the repeated local repair pattern. Turn 2 fully unloads the brake under time pressure b |

## Assessment

The schema fix removed the implementation-level parse failure: all three official repeats have `triage_error_count = 0`, prompt fingerprint `e237bd69...`, and zero contamination across generator, judge, and triage. However, the dev gate fails. The fixed v0.1 prompt at threshold `0.90` does not reliably separate legal convergence iteration from brake pathology, and several positives sit below threshold despite all hard-gate booleans being true. This should go back to design/audit review rather than being treated as a fourth matcher patch.

Recommended audit question: whether v0.1 prompt should be revised to encode the legal-convergence boundary explicitly, or whether a separate reviewed calibration/threshold change is acceptable. Current evidence does not support shadow retest kickoff.

