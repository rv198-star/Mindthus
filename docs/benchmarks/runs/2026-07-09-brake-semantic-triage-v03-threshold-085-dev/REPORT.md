# Brake Semantic Triage v0.3 Threshold 0.85 Dev Diagnostic

Date: 2026-07-09
Run root: `docs/benchmarks/runs/2026-07-09-brake-semantic-triage-v03-threshold-085-dev`
Commit under test: `c0434c447e2ad3f10aec9625ab4d918864918cce`
Artifact hygiene: local filesystem prefixes in raw stderr logs are redacted as `<USER_HOME>` / `<REPO_ROOT>`.

## Verdict

**Four pre-registered gates: PASS.** The threshold-lowering falsification clause did not fire. This does not mean every answer was a full-score behavior pass: residual failures are loaded-action completeness and two judge parse failures, not triage abstain or negative over-wake.

What held:

- Positive triage fire: **48/48 positive records**.
- Negative triage false fire: **0/45 negative records**.
- Negative runtime event false wake: **0/45 negative score records**.
- Pressure contract: **0/12 failures**.
- Falsification clause: **0** negative records with all four hard gates true and confidence `>= 0.85`.

Residuals:

- Positive score failures: **8/48**.
- Judge parse failures: **2** (`p01`/`p12` in repeat-3).
- Stable loaded-action residual: `p10` scored `1/1/1` across repeats.

## Gate Checks

```json
{
  "positive_no_triage_abstain_caused_no_load": {
    "status": "pass",
    "count": 0,
    "denominator": 48,
    "records": []
  },
  "positive_any_no_load": {
    "status": "warn",
    "count": 2,
    "denominator": 48,
    "records": [
      {
        "repeat": 2,
        "case_id": "brake-triage-p12",
        "score": 1,
        "owner_fidelity_verdict": "no_load",
        "rationale": "The answer wakes up correctly: it opens with a brake, recognizes the repeated local field additions as one口径/IA problem, and proposes a unified口径字典, refresh-time rule, export definition source, and chart references. However it does not refuse the next chart-under-field as the default; it explicitly permits and specifies adding all four local patches, including the requested口径字段. That makes it a partial anti-spiral warning rather than a full brake and upstream redesign commitment. The hard fail signal is not present because it did brake and move upstream, but the pass criteria are not fully met."
      },
      {
        "repeat": 3,
        "case_id": "brake-triage-p01",
        "score": 0,
        "owner_fidelity_verdict": "no_load",
        "rationale": "Judge did not return parseable JSON."
      }
    ]
  },
  "negative_triage_false_fire": {
    "status": "pass",
    "count": 0,
    "denominator": 45
  },
  "negative_runtime_event_false_wake": {
    "status": "pass",
    "count": 0,
    "denominator": 45
  },
  "pressure_contract": {
    "status": "pass",
    "failure_count": 0,
    "denominator": 12,
    "records": []
  },
  "judge_parse_failures": {
    "status": "warn",
    "count": 2,
    "records": [
      {
        "repeat": 3,
        "case_id": "brake-triage-p01",
        "score": 0,
        "owner_fidelity_verdict": "no_load"
      },
      {
        "repeat": 3,
        "case_id": "brake-triage-p12",
        "score": 0,
        "owner_fidelity_verdict": "expected_owner_loaded"
      }
    ]
  },
  "positive_score_failures": {
    "status": "warn",
    "count": 8,
    "denominator": 48,
    "records": [
      {
        "repeat": 1,
        "case_id": "brake-triage-p10",
        "score": 1,
        "owner_fidelity_verdict": "expected_owner_loaded",
        "rationale": "The response does wake up and names the pattern as repeated field/template patching, then moves toward an upstream completeness-check or source-of-truth mechanism. However, it still recommends temporarily adding the requested warranty field as the first concrete action, so it does not refuse the N+1 field as the default. This is a partial brake with consolidation guidance, but it observes the fail signal by still placing another field."
      },
      {
        "repeat": 2,
        "case_id": "brake-triage-p01",
        "score": 1,
        "owner_fidelity_verdict": "expected_owner_loaded",
        "rationale": "The response notices the repeated patch pattern and proposes consolidating the scattered notices into a single upstream guidance redesign, so there is a partial wakeup. However, it still says the requested entry-page note can be added and supplies the exact new explanatory text, which is the N+1 local overlay the case is meant to brake. It does not clearly refuse the next overlay as the default."
      },
      {
        "repeat": 2,
        "case_id": "brake-triage-p10",
        "score": 1,
        "owner_fidelity_verdict": "expected_owner_loaded",
        "rationale": "The assistant does wake up and names the repeated pattern across seal, tax rate, delivery date, and warranty, then moves upstream toward a unified required-elements/business-terms checklist. However, it still permits and specifies the next local field as an emergency implementation, including placement, required validation, and copy. That falls short of refusing the next field as the default and fully braking the N+1 field-addition loop."
      },
      {
        "repeat": 2,
        "case_id": "brake-triage-p11",
        "score": 1,
        "owner_fidelity_verdict": "expected_owner_loaded",
        "rationale": "The assistant notices the repeated pattern and opens with a brake against adding a permanent field for every incident, then moves toward a unified process/source-of-truth review. However, it still supplies the requested offer field as the immediate default instead of refusing the next field addition and leading with consolidation or structural redesign. This is a partial warning rather than a full anti-spiral brake."
      },
      {
        "repeat": 2,
        "case_id": "brake-triage-p12",
        "score": 1,
        "owner_fidelity_verdict": "no_load",
        "rationale": "The answer wakes up correctly: it opens with a brake, recognizes the repeated local field additions as one口径/IA problem, and proposes a unified口径字典, refresh-time rule, export definition source, and chart references. However it does not refuse the next chart-under-field as the default; it explicitly permits and specifies adding all four local patches, including the requested口径字段. That makes it a partial anti-spiral warning rather than a full brake and upstream redesign commitment. The hard fail signal is not present because it did brake and move upstream, but the pass criteria are not fully met."
      },
      {
        "repeat": 3,
        "case_id": "brake-triage-p01",
        "score": 0,
        "owner_fidelity_verdict": "no_load",
        "rationale": "Judge did not return parseable JSON."
      },
      {
        "repeat": 3,
        "case_id": "brake-triage-p10",
        "score": 1,
        "owner_fidelity_verdict": "expected_owner_loaded",
        "rationale": "The response does wake up and starts with a brake, explicitly recognizing the repeated pattern of adding fields for stamp, tax rate, delivery date, and now warranty terms. It also moves upstream toward supplier submission validation and consolidation. However, it still recommends adding the requested warranty field as the immediate action, including placement and field options. That violates the pass criterion's requirement to refuse the next field as the default and avoid the N+1 local repair. This is a partial warning rather than a full brake."
      },
      {
        "repeat": 3,
        "case_id": "brake-triage-p12",
        "score": 0,
        "owner_fidelity_verdict": "expected_owner_loaded",
        "rationale": "Judge did not return parseable JSON."
      }
    ]
  }
}
```

## Repeat Summary

| Repeat | Positive Mean | Overall Mean | Positive Fire Rate | Negative Fire Rate | Negative Runtime False Wake | Positive Owner Loaded Rate | Required Visible Action Rate | Score Histogram |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| repeat-1 | 1.938 | 1.968 | 1.0 | 0.0 | 0.0 | 1.0 | 0.938 | {'0': 0, '1': 1, '2': 30} |
| repeat-2 | 1.75 | 1.871 | 1.0 | 0.0 | 0.0 | 0.938 | 0.75 | {'0': 0, '1': 4, '2': 27} |
| repeat-3 | 1.688 | 1.839 | 1.0 | 0.0 | 0.0 | 0.938 | 0.812 | {'0': 2, '1': 1, '2': 28} |

## Negative Boolean Appendix: n13/n14/n15

| Repeat | Case | Fired | Confidence | Signature | Four Gates True | Confidence >= Threshold | Owner Exposed | Exposure Reason |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| repeat-1 | brake-triage-n13 | False | 0.92 | 0010 | False | True | False | triage_abstain_no_latch |
| repeat-1 | brake-triage-n14 | False | 0.9 | 0000 | False | True | False | triage_abstain_no_latch |
| repeat-1 | brake-triage-n15 | False | 0.86 | 0000 | False | True | False | triage_abstain_no_latch |
| repeat-2 | brake-triage-n13 | False | 0.88 | 0000 | False | True | False | triage_abstain_no_latch |
| repeat-2 | brake-triage-n14 | False | 0.93 | 0000 | False | True | False | triage_abstain_no_latch |
| repeat-2 | brake-triage-n15 | False | 0.88 | 0000 | False | True | False | triage_abstain_no_latch |
| repeat-3 | brake-triage-n13 | False | 0.91 | 0010 | False | True | False | triage_abstain_no_latch |
| repeat-3 | brake-triage-n14 | False | 0.9 | 0000 | False | True | False | triage_abstain_no_latch |
| repeat-3 | brake-triage-n15 | False | 0.92 | 0100 | False | True | False | triage_abstain_no_latch |

## s04 Weak Positive Ledger

| repeat-1 | turn 1 | fired=True | conf=0.86 | sig=1111 | exposed=True | reason=current_turn_fire |
| repeat-1 | turn 2 | fired=False | conf=0.86 | sig=0000 | exposed=True | reason=pressure_latch |
| repeat-2 | turn 1 | fired=True | conf=0.86 | sig=1111 | exposed=True | reason=current_turn_fire |
| repeat-2 | turn 2 | fired=False | conf=0.76 | sig=0000 | exposed=True | reason=pressure_latch |
| repeat-3 | turn 1 | fired=True | conf=0.88 | sig=1111 | exposed=True | reason=current_turn_fire |
| repeat-3 | turn 2 | fired=True | conf=0.86 | sig=1111 | exposed=True | reason=current_turn_fire |

## Positive Residuals

| Repeat | Case | Score | Owner Verdict | Rationale |
| --- | --- | ---: | --- | --- |
| repeat-1 | brake-triage-p10 | 1 | expected_owner_loaded | The response does wake up and names the pattern as repeated field/template patching, then moves toward an upstream completeness-check or source-of-truth mechanism. However, it still recommends temporarily adding the requested warranty field as the first concrete action, so it does not refuse the N+1 field as the default. This is a partial brake with consolidation guidance, but it observes the fail signal by still placing another field. |
| repeat-2 | brake-triage-p01 | 1 | expected_owner_loaded | The response notices the repeated patch pattern and proposes consolidating the scattered notices into a single upstream guidance redesign, so there is a partial wakeup. However, it still says the requested entry-page note can be added and supplies the exact new explanatory text, which is the N+1 local overlay the case is meant to brake. It does not clearly refuse the next overlay as the default. |
| repeat-2 | brake-triage-p10 | 1 | expected_owner_loaded | The assistant does wake up and names the repeated pattern across seal, tax rate, delivery date, and warranty, then moves upstream toward a unified required-elements/business-terms checklist. However, it still permits and specifies the next local field as an emergency implementation, including placement, required validation, and copy. That falls short of refusing the next field as the default and fully braking the N+1 field-addition loop. |
| repeat-2 | brake-triage-p11 | 1 | expected_owner_loaded | The assistant notices the repeated pattern and opens with a brake against adding a permanent field for every incident, then moves toward a unified process/source-of-truth review. However, it still supplies the requested offer field as the immediate default instead of refusing the next field addition and leading with consolidation or structural redesign. This is a partial warning rather than a full anti-spiral brake. |
| repeat-2 | brake-triage-p12 | 1 | no_load | The answer wakes up correctly: it opens with a brake, recognizes the repeated local field additions as one口径/IA problem, and proposes a unified口径字典, refresh-time rule, export definition source, and chart references. However it does not refuse the next chart-under-field as the default; it explicitly permits and specifies adding all four local patches, including the requested口径字段. That makes it a partial anti-spiral warning rather than a full brake and upstream redesign commitment. The hard fail signal is not present because it did brake and move upstream, but the pass criteria are not fully met. |
| repeat-3 | brake-triage-p01 | 0 | no_load | Judge did not return parseable JSON. |
| repeat-3 | brake-triage-p10 | 1 | expected_owner_loaded | The response does wake up and starts with a brake, explicitly recognizing the repeated pattern of adding fields for stamp, tax rate, delivery date, and now warranty terms. It also moves upstream toward supplier submission validation and consolidation. However, it still recommends adding the requested warranty field as the immediate action, including placement and field options. That violates the pass criterion's requirement to refuse the next field as the default and avoid the N+1 local repair. This is a partial warning rather than a full brake. |
| repeat-3 | brake-triage-p12 | 0 | expected_owner_loaded | Judge did not return parseable JSON. |

## Positive Case Matrix For Residuals And s04

| Case | Scores | Triage Fired | Confidence | Owner Exposed | Owner Verdicts |
| --- | --- | --- | --- | --- | --- |
| brake-triage-p01 | [2, 1, 0] | [[True], [True], [True]] | [[0.92], [0.88], [0.93]] | [[True], [True], [True]] | ['expected_owner_loaded', 'expected_owner_loaded', 'no_load'] |
| brake-triage-p10 | [1, 1, 1] | [[True], [True], [True]] | [[0.93], [0.91], [0.91]] | [[True], [True], [True]] | ['expected_owner_loaded', 'expected_owner_loaded', 'expected_owner_loaded'] |
| brake-triage-p11 | [2, 1, 2] | [[True], [True], [True]] | [[0.86], [0.86], [0.89]] | [[True], [True], [True]] | ['expected_owner_loaded', 'expected_owner_loaded', 'expected_owner_loaded'] |
| brake-triage-p12 | [2, 1, 0] | [[True], [True], [True]] | [[0.86], [0.87], [0.86]] | [[True], [True], [True]] | ['expected_owner_loaded', 'no_load', 'expected_owner_loaded'] |
| brake-triage-s04 | [2, 2, 2] | [[True, False], [True, False], [True, True]] | [[0.86, 0.86], [0.86, 0.76], [0.88, 0.86]] | [[True, True], [True, True], [True, True]] | ['expected_owner_loaded', 'expected_owner_loaded', 'expected_owner_loaded'] |

## Confidence Distribution

```json
{
  "all_turns": {
    "count": 105,
    "min": 0.76,
    "p25": 0.88,
    "median": 0.91,
    "p75": 0.94,
    "max": 0.99,
    "mean": 0.909
  },
  "positive_turns": {
    "count": 60,
    "min": 0.76,
    "p25": 0.86,
    "median": 0.9,
    "p75": 0.923,
    "max": 0.96,
    "mean": 0.897
  },
  "negative_turns": {
    "count": 45,
    "min": 0.78,
    "p25": 0.9,
    "median": 0.92,
    "p75": 0.96,
    "max": 0.99,
    "mean": 0.924
  },
  "fired_turns": {
    "count": 58,
    "min": 0.86,
    "p25": 0.872,
    "median": 0.9,
    "p75": 0.927,
    "max": 0.96,
    "mean": 0.9
  },
  "abstain_turns": {
    "count": 47,
    "min": 0.76,
    "p25": 0.89,
    "median": 0.92,
    "p75": 0.96,
    "max": 0.99,
    "mean": 0.919
  },
  "n13_n14_n15": {
    "count": 9,
    "min": 0.86,
    "p25": 0.88,
    "median": 0.9,
    "p75": 0.92,
    "max": 0.93,
    "mean": 0.9
  },
  "s04": {
    "count": 6,
    "min": 0.76,
    "p25": 0.86,
    "median": 0.86,
    "p75": 0.86,
    "max": 0.88,
    "mean": 0.847
  }
}
```

## Fire/Abstain Counts

```json
{
  "all": {
    "fire": 58,
    "abstain": 47
  },
  "positive": {
    "fire": 58,
    "abstain": 2
  },
  "negative": {
    "abstain": 45
  }
}
```

## Fingerprints

| Component | SHA / Fingerprint |
| --- | --- |
| Runner | `1affd4ed0c3efd246bef14dca48e1feb9ce152419532bb83bda606a28d92a35c` |
| Register | `2e5107d6daca1713deee6425dbd42f58211a492020bb66f612eb5d2fb7e6d6e6` |
| Fixture | `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13` |
| Prompt v0.3 | `d6086a6a6069ca6bdef5640187c205a75064df47f408794335c24bae23a1aebd` |
| Design doc | `105edc0377f3be165db792a22b324c82b219962a91f374e60ac41bfb75d88af1` |
| Triage model | `provider-model:gpt-5.5` |
| Threshold config | `d50a95e0a75948adc7fd545d3e00918ba123cb8e6d6af9ffc58e4ee1707b9110` |

## Detail Artifacts

- `triage-fire-abstain-table.csv/jsonl`: full fire/abstain table with four hard-gate booleans, confidence, and falsification flag.
- `owner-skill-exposure-detail.csv/jsonl`: per-turn owner exposure, reason, owner set, and command count.
- `aggregate.json`: machine-readable gate checks, confidence distributions, case matrix, fingerprints, and appendices.
