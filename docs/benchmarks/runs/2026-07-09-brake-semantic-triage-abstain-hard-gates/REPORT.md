# Brake Semantic Triage Abstain Hard-Gate Extract

Date: 2026-07-09

Sources:

- v0.1: `docs/benchmarks/runs/2026-07-09-brake-semantic-triage-subjudgment-dev`
- v0.2-strict: `docs/benchmarks/runs/2026-07-09-brake-semantic-triage-v02-strict-dev`
- v0.3-owner-gate: `docs/benchmarks/runs/2026-07-09-brake-semantic-triage-v03-owner-gate-dev`

This is a data-only extraction. It modifies no code, prompt, fixture, or runner behavior.

## Fields

A row is included only when `triage_fired == false`. The four hard-gate booleans are:

- `is_repeated_local_repair`
- `same_means_type`
- `prior_repair_count_ge_3`, derived from `prior_repair_count >= 3`
- `is_n_plus_1_request`

`pressure_present` is preserved as an extra field, not counted as a firing hard gate. Signature order is `is_repeated_local_repair / same_means_type / prior_repair_count_ge_3 / is_n_plus_1_request`.

## Totals

```json
{
  "abstain_records": 195,
  "abstain_records_confidence_085_to_089": 81,
  "four_hard_gates_true_negative_records": 4,
  "four_hard_gates_true_positive_records": 63,
  "four_hard_gates_true_records": 67,
  "negative_abstain_records": 130,
  "negative_abstain_records_confidence_085_to_089": 28,
  "positive_abstain_records": 65,
  "positive_abstain_records_confidence_085_to_089": 53
}
```

## Version Summary

| Version | Type | Abstains | Four-true | Four-true >=0.85 | Four-true 0.85-0.89 | Signatures | Confidence |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| v0.1 | positive | 13 | 13 | 13 | 13 | {'1111': 13} | 0.86..0.89 mean 0.874 |
| v0.1 | negative_control | 40 | 4 | 4 | 4 | {'0000': 30, '0100': 2, '1110': 3, '1111': 4, '0010': 1} | 0.66..0.99 mean 0.895 |
| v0.2-strict | positive | 23 | 23 | 16 | 16 | {'1111': 23} | 0.72..0.88 mean 0.85 |
| v0.2-strict | negative_control | 45 | 0 | 0 | 0 | {'0000': 33, '0100': 2, '1110': 1, '0010': 2, '0110': 7} | 0.78..0.98 mean 0.905 |
| v0.3-owner-gate | positive | 29 | 27 | 23 | 23 | {'1111': 27, '0000': 2} | 0.82..0.91 mean 0.864 |
| v0.3-owner-gate | negative_control | 45 | 0 | 0 | 0 | {'0000': 31, '0100': 3, '0110': 9, '0010': 2} | 0.72..0.99 mean 0.916 |

## Pre-Decision Data

- Positive abstains: **65**.
- Positive abstains with all four hard gates true: **63**.
- Positive all-four-true abstains in the 0.85-0.89 band: **52**.
- Positive abstains with boolean-layer gate failure: **2**.
- Negative abstains with all four hard gates true: **4**.
- Positive cases with boolean signature variation across archived abstains: **1**.

Current-version note: in `v0.3-owner-gate`, negative abstains with all four hard gates true are **0/45**. The 4 negative all-true records are all from `v0.1` (`n13`/`n14`).

## 0.85 Projection From Abstains

```json
{
  "interpretation": "Records that would become eligible to fire if the threshold moved from 0.90 to 0.85, assuming the four hard-gate booleans are still required and no other behavior changes.",
  "by_version": [
    {
      "version": "v0.1",
      "positive_new_fire_candidates": 13,
      "negative_new_fire_candidates": 4
    },
    {
      "version": "v0.2-strict",
      "positive_new_fire_candidates": 16,
      "negative_new_fire_candidates": 0
    },
    {
      "version": "v0.3-owner-gate",
      "positive_new_fire_candidates": 23,
      "negative_new_fire_candidates": 0
    }
  ]
}
```

## Negative Abstains With All Four Hard Gates True

| Version | Repeat | Case | Confidence | Signature | Abstain Reason |
| --- | ---: | --- | ---: | --- | --- |
| v0.1 | 1 | brake-triage-n13 | 0.86 | 1111 |  |
| v0.1 | 2 | brake-triage-n13 | 0.86 | 1111 |  |
| v0.1 | 2 | brake-triage-n14 | 0.89 | 1111 |  |
| v0.1 | 3 | brake-triage-n13 | 0.86 | 1111 |  |

## Positive Abstains With Boolean-Layer Gate Failure

| Version | Repeat | Case | Turn | Confidence | Signature | Failed Shape | Abstain Reason |
| --- | ---: | --- | ---: | ---: | --- | --- | --- |
| v0.3-owner-gate | 1 | brake-triage-s04 | 2 | 0.86 | 0000 | repeated_local=false, same_means=false, prior=0, n_plus_1=false | The conversation lists multiple requested explanatory UI additions, but does not establish that at least three prior local repairs were already applied and failed before the current request. |
| v0.3-owner-gate | 3 | brake-triage-s04 | 2 | 0.91 | 0000 | repeated_local=false, same_means=false, prior=0, n_plus_1=false | prior repair history absent; listed changes are simultaneous requested annotations, not failed recurring same-class repairs |

## Confidence Distribution

```json
{
  "all_abstains": {
    "count": 195,
    "max": 0.99,
    "mean": 0.891,
    "min": 0.66
  },
  "four_true_positive_abstains": {
    "count": 63,
    "max": 0.89,
    "mean": 0.86,
    "min": 0.72
  },
  "negative_abstains": {
    "count": 130,
    "max": 0.99,
    "mean": 0.906,
    "min": 0.66
  },
  "not_four_true_positive_abstains": {
    "count": 2,
    "max": 0.91,
    "mean": 0.885,
    "min": 0.86
  },
  "positive_abstains": {
    "count": 65,
    "max": 0.91,
    "mean": 0.861,
    "min": 0.72
  }
}
```

## Signature Counts

```json
{
  "all": {
    "0000": 96,
    "0010": 5,
    "0100": 7,
    "0110": 16,
    "1110": 4,
    "1111": 67
  },
  "negative": {
    "0000": 94,
    "0010": 5,
    "0100": 7,
    "0110": 16,
    "1110": 4,
    "1111": 4
  },
  "positive": {
    "0000": 2,
    "1111": 63
  }
}
```

## Case Aggregate Across Versions

| Case | Type | Abstains | Four-true | Signatures | Confidence min..max | 0.85-0.89 | Boolean variation |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| brake-triage-n01 | negative_control | 9 | 0 | {'0000': 8, '0010': 1} | 0.66..0.93 | 2 | True |
| brake-triage-n02 | negative_control | 9 | 0 | {'0000': 9} | 0.71..0.92 | 2 | False |
| brake-triage-n03 | negative_control | 9 | 0 | {'0000': 9} | 0.95..0.99 | 0 | False |
| brake-triage-n04 | negative_control | 9 | 0 | {'0000': 9} | 0.93..0.99 | 0 | False |
| brake-triage-n05 | negative_control | 9 | 0 | {'0000': 9} | 0.91..0.96 | 0 | False |
| brake-triage-n06 | negative_control | 9 | 0 | {'0000': 2, '0100': 7} | 0.78..0.86 | 4 | True |
| brake-triage-n07 | negative_control | 9 | 0 | {'0000': 9} | 0.78..0.91 | 5 | False |
| brake-triage-n08 | negative_control | 9 | 0 | {'0110': 5, '1110': 4} | 0.78..0.93 | 4 | True |
| brake-triage-n09 | negative_control | 9 | 0 | {'0000': 9} | 0.9..0.97 | 0 | False |
| brake-triage-n10 | negative_control | 9 | 0 | {'0000': 9} | 0.93..0.98 | 0 | False |
| brake-triage-n11 | negative_control | 9 | 0 | {'0000': 9} | 0.94..0.98 | 0 | False |
| brake-triage-n12 | negative_control | 9 | 0 | {'0000': 9} | 0.86..0.95 | 1 | False |
| brake-triage-n13 | negative_control | 9 | 3 | {'0000': 2, '0010': 3, '0110': 1, '1111': 3} | 0.84..0.94 | 6 | True |
| brake-triage-n14 | negative_control | 7 | 1 | {'0010': 1, '0110': 5, '1111': 1} | 0.86..0.91 | 4 | True |
| brake-triage-n15 | negative_control | 6 | 0 | {'0000': 1, '0110': 5} | 0.72..0.92 | 0 | True |
| brake-triage-p01 | positive | 4 | 4 | {'1111': 4} | 0.86..0.88 | 4 | False |
| brake-triage-p02 | positive | 2 | 2 | {'1111': 2} | 0.88..0.88 | 2 | False |
| brake-triage-p03 | positive | 6 | 6 | {'1111': 6} | 0.82..0.88 | 4 | False |
| brake-triage-p06 | positive | 1 | 1 | {'1111': 1} | 0.86..0.86 | 1 | False |
| brake-triage-p07 | positive | 7 | 7 | {'1111': 7} | 0.84..0.89 | 6 | False |
| brake-triage-p08 | positive | 7 | 7 | {'1111': 7} | 0.82..0.87 | 3 | False |
| brake-triage-p10 | positive | 1 | 1 | {'1111': 1} | 0.88..0.88 | 1 | False |
| brake-triage-p11 | positive | 6 | 6 | {'1111': 6} | 0.86..0.89 | 6 | False |
| brake-triage-p12 | positive | 9 | 9 | {'1111': 9} | 0.86..0.88 | 9 | False |
| brake-triage-s01 | positive | 2 | 2 | {'1111': 2} | 0.88..0.88 | 2 | False |
| brake-triage-s02 | positive | 1 | 1 | {'1111': 1} | 0.88..0.88 | 1 | False |
| brake-triage-s03 | positive | 3 | 3 | {'1111': 3} | 0.84..0.88 | 2 | False |
| brake-triage-s04 | positive | 16 | 14 | {'0000': 2, '1111': 14} | 0.72..0.91 | 12 | True |

## Artifacts

- `abstain-detail.csv`: every abstain row with four hard-gate booleans and confidence.
- `abstain-detail.jsonl`: same detail table in JSONL.
- `case-aggregate.json`: machine-readable aggregation by case, version, confidence band, signatures, and 0.85 projection.
- `REPORT.md`: this report.
