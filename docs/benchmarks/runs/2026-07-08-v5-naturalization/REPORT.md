# V5 Naturalization And #17 Layer Probe Report

Status: diagnostic evidence only, not certification. This run validates two bounded tasks after `v1.4.4-diag`: #17 loaded-action layer probe and #104 semantic triage naturalization. It does not touch brake follow-up or #8/#37 register coverage.

## Code Under Test

- Implementation commit: `9d31aea` (`Naturalize V5 target triage`)
- Runner: `scripts/run-judgment-benchmark-cli.py`
- Register: `docs/benchmarks/v5-target-trigger-register.json`
- Calibration anchors: `skills/using-mindthus/resources/calibration-pairs.yaml`
- Isolated Codex home: `/private/tmp/codex-mindthus-eval-home-v5-naturalization`
- Plugin cache root: `/private/tmp/codex-mindthus-eval-home-v5-naturalization/plugins/cache/mindthus/mindthus/1.4.3`
- Mode: diagnostic host hints only; not a certification candidate and not a shadow-set substitute.

## Patch Summary

| Change | Patch Type | Certification Meaning |
| --- | --- | --- |
| Added `ai-replaces-designers-malformed-binary` and `ai-replaces-customer-support-malformed-binary` | exemplar anchor | Allowed #17 anchor expansion; not a broad wording clause |
| Added `semantic_features` and `hint_action` to the 9-case V5 target register | mechanical runtime | Enables disease-level triage independent of case id |
| Added `--v5-semantic-triage-hints` and semantic feature matching in the runner | mechanical runtime | Separates #104 from public case-number register hints |
| Added #25 method-reference stay-asleep triage | mechanical runtime guardrail | Fixes residual MPG over-wake for evidence-review prompts |
| Parameterized the Superpowers isolation path label | mechanical hygiene | Removes hardcoded local username path from runner source |
| Added contract tests for #17, semantic shadow matching, #25 stay-asleep, and register fields | test contract | Locks behavior shape without exact answer phrases |

No method-body wording clauses were added in this patch.

## Task 1: #17 Layer Probe

Command shape: `--select 17 --v5-register-hints`, repeated `n=5`.

| Repeat | Score | Loaded Owner | Required Visible Action | Verdict |
| --- | ---: | --- | --- | --- |
| 1 | 2 | `edsp` | true | `expected_owner_loaded` |
| 2 | 2 | `edsp` | true | `expected_owner_loaded` |
| 3 | 2 | `edsp` | true | `expected_owner_loaded` |
| 4 | 2 | `edsp` | true | `expected_owner_loaded` |
| 5 | 2 | `edsp` | true | `expected_owner_loaded` |

Interpretation: #17 is not a model-layer ceiling under full-config/register-hint mode. The old all-zero behavior was a loaded-action/probe gap: once malformed-binary exemplar anchors and first-sentence reconstruction action are present, #17 passes 5/5.

Artifacts:

- `17-register-hint-repeat-1/`
- `17-register-hint-repeat-2/`
- `17-register-hint-repeat-3/`
- `17-register-hint-repeat-4/`
- `17-register-hint-repeat-5/`

## Task 2: #104 Semantic Triage Naturalization

Command shape: `--select 2,3,4,13,17,33,34,48,49 --v5-semantic-triage-hints`, repeated `n=3`.

| Repeat | Positive Mean | Expected Owner Loaded | No Load | Wrong Owner | Required Visible Action |
| --- | ---: | ---: | --- | --- | ---: |
| 1 | 1.889 | 9/9 | none | none | 8/9 |
| 2 | 1.889 | 9/9 | none | none | 8/9 |
| 3 | 1.889 | 9/9 | none | none | 8/9 |

Interpretation: no-case-id semantic triage successfully naturalizes loading for all 9 registered targets across `n=3`. This validates #104's activation path: the hint is emitted from disease-level features, not from case number or case id.

Residual quality findings:

- Repeat 1: #13 scored 1; owner loaded, but whole-object reconstruction stayed bean-heavy and did not fully cover position, per-square-meter efficiency, brand, and operating model.
- Repeat 2: #13 scored 1 for the same loaded-action quality reason.
- Repeat 3: #49 scored 1; owner loaded, but the answer still used hypothetical numbers to produce a conclusion-like comparison.

These are loaded-action quality residuals, not naturalization failures. They should be handled under #105-style loaded-action probes, not by broad wording clauses.

Artifacts:

- `104-positive-semantic-repeat-1/`
- `104-positive-semantic-repeat-2/`
- `104-positive-semantic-repeat-3/`

## Negative Controls

Command shape: `--select 7,25,28,29,31,32,35,43,44,45,46,47 --v5-semantic-triage-hints`, `n=1`.

| Metric | Result |
| --- | ---: |
| Final-answer false wake-up | 0/12 |
| Runtime-event false wake-up | 0/12 |
| Owner fidelity | `direct_stay_asleep`: 12/12 |
| #25 loaded owner | `[]` |
| #25 runtime false wake | false |

Interpretation: #25 residual MPG over-wake is cleared in this diagnostic path. The negative-control event budget is reset to 0/12 for this run.

Residual non-wake quality note:

- #35 scored 1 because the answer stayed direct but stopped for workspace/material access instead of continuing the next failing test. It did not load Mindthus, so this is not a false wake-up.

Artifacts:

- `104-negative-semantic-runtime/`

## Conclusion

This patch moves the route from public case-id register hints toward disease-level semantic triage. The strongest evidence is:

- #17 full-config layer probe: 5/5 pass, so not a model ceiling.
- #104 target activation: 9/9 loaded across 3 repeats with no no-load or wrong-owner cases.
- Negative controls: runtime false wake-up 0/12, with #25 cleared.

Remaining work is not another text-rule pass. The next useful work is loaded-action mechanicalization for residual cases like #13 and #49, plus the already planned #8/#37 register coverage and independent shadow-set ownership.
