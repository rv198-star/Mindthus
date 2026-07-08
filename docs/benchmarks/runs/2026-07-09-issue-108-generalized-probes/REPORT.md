# Issue 108 Generalized Probe Diagnostic

Status: diagnostic mostly green; not certification.

This run verifies the #108 fix for public-case narrow fitting. It uses host
register/semantic triage hints, so it is diagnostic evidence only and not a
shadow-set substitute.

## Patch Summary

| Area | means_type | Change |
| --- | --- | --- |
| #8 probe | mechanical_runtime | Reframed as statistical mechanism used as capability-ceiling evidence; removed public prompt phrase keys and added paraphrase feature families. |
| #13 probe | mechanical_runtime | Reframed as one local attribute used as the sole cause of a multi-factor business result; removed coffee-shop controller list from the probe. |
| #37 probe | mechanical_runtime | Reframed as active decision context owning definition authority; removed B/PPI direction from the probe. |
| #49 probe | mechanical_runtime | Reframed as no-data concrete-number conclusion-like comparison; removed `risk exposure` as a required trigger. |
| Contract tests | test_contract | Added two surface-changed variants per disease family and guards against public-case keys. |
| Legacy artifact caveat | documentation | Marked the `4cbba4f` focus-case green result as narrow-fitting suspect pending this #108 supersession. |

No method-body wording clause was added.

## Run Shape

| Field | Value |
| --- | --- |
| Implementation commit | `9825730864db38a2ff34e2d932dc19d0fc4d45e6` |
| Run commit | `6d42d4daf1d1f5bee5084c8a5947028102e786ce` |
| Original public cases | `#8,#13,#37,#49` with `--v5-register-hints`, n=3 |
| Surface-changed variants | 8 custom diagnostic cases with `--v5-semantic-triage-hints`, n=3 |
| Model / judge | `gpt-5.5` / `gpt-5.5` |
| Contamination gate | `--fail-on-contamination` |

## Aggregate

| Group | Score-2 | Score-1 | Expected owner loaded | Required visible action | Contamination |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original register cases | 11/12 | 1/12 | 12/12 | 11/12 | 0 |
| Surface-changed variants | 24/24 | 0/24 | 24/24 | 24/24 | 0 |

## Residual

Original #13 repeat 3 scored `1` even though `using-mindthus` loaded. The judge rationale
shows the remaining mismatch: the answer satisfied the generalized #108 shape by treating
the local attribute as a bounded carrier and naming non-local result controllers, but the
legacy public case rubric still expected old coffee-shop-specific dimensions such as
location/floor-efficiency/brand. This should not be "fixed" by reintroducing those
public-case terms into the probe.

## Interpretation

#108's narrow-fitting concern is addressed at the register/probe/test level: the new
contract tests and semantic-triage variant run prove the four disease families can fire
when the surface wording, domain, and role direction change. The original public #13
result remains partially constrained by its legacy case-specific rubric, so this report
does not claim a clean 12/12 public-case rerun.

## Artifacts

- `summary-aggregate.json`
- `issue-108-variant-cases.jsonl`
- `original-register-repeat-1/`
- `original-register-repeat-2/`
- `original-register-repeat-3/`
- `variant-semantic-repeat-1/`
- `variant-semantic-repeat-2/`
- `variant-semantic-repeat-3/`
