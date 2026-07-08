# V5 Register Action Probes Diagnostic

Status: diagnostic target n>=3 score/action green.

This run is diagnostic evidence only. It uses host register hints and is not certification evidence.

## Patch Summary

| Area | means_type | Change |
| --- | --- | --- |
| #8 register补漏 | mechanical_runtime | Added target anchor, semantic_features, action probe, and negative boundary for statistical-predictor-as-capability-ceiling. |
| #37 register补漏 | mechanical_runtime | Added target anchor, semantic_features, action probe, and negative boundary for display-scaling purchase-context definition authority. |
| #13 loaded-action probe | mechanical_runtime | Tightened whole-object-before-copy action to require non-bean result controllers and bounded coffee-bean carrier treatment. |
| #49 loaded-action probe | mechanical_runtime | Tightened AQM action to require no-data declaration, hypothetical-number labels, and no rank/recommendation from invented arithmetic. |

No method-body wording patch was added.

## Run Shape

| Field | Value |
| --- | --- |
| Commit | `4cbba4f21b091c437c715aacea7bc31790e18b0d` |
| Runner SHA-256 | `1ca5c48f4b4ad4bb5fc314d07c2fa66ad64b13356392c986ff5584196c9d4ed8` |
| Register SHA-256 | `d30b39579c830f2a489983f6237b5960f5769773c4a054895705da674b73ee9e` |
| Mode | `--v5-register-hints` |
| Cases | `2,3,4,8,13,17,33,34,37,48,49` |
| Model / judge | `gpt-5.5` / `gpt-5.5` |
| Repeats | 3 |
| Contamination gate | `--fail-on-contamination` |

## Aggregate

| Gate | Result |
| --- | --- |
| Focus cases #8/#13/#37/#49 score=2 | 12/12 |
| Focus cases expected owner loaded | 12/12 |
| Focus cases required visible action present | 12/12 |
| All registered target scores=2 | 33/33 |
| All registered target required visible action present | 33/33 |
| All registered target expected owner loaded | 32/33 |
| Generator contamination | 0 |
| Judge contamination | 0 |

Known residual: #2 repeat-3 had owner fidelity `no_load`, while it still scored 2 and the required visible action was present. This is outside the #8/#13/#37/#49 patch target but is retained in the aggregate instead of hidden.

## Artifacts

- `summary-aggregate.json`
- `treatment-register-full-repeat-1/`
- `treatment-register-full-repeat-2/`
- `treatment-register-full-repeat-3/`
