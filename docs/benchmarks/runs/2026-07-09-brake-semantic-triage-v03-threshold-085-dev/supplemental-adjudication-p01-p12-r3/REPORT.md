# Supplemental Adjudication: p01-R3 / p12-R3

Date: 2026-07-09
Scope: judge-only supplemental adjudication for the two repeat-3 records whose original judge step returned unparseable output.

## Boundary

- Source run: `docs/benchmarks/runs/2026-07-09-brake-semantic-triage-v03-threshold-085-dev/repeat-3`
- Source run commit: `c0434c447e2ad3f10aec9625ab4d918864918cce`
- Supplemental runner commit: `c810a0cdca07e12a4188c36f81dc3bca225ced43`
- Generator rerun: no
- Fixture changed: no
- Original repeat-3 judge records overwritten: no
- Cached judge reused: 0
- Artifact hygiene: local filesystem prefixes in raw logs are redacted as `<USER_HOME>` / `<REPO_ROOT>`.

The copied answer records match the original repeat-3 answer records:

| Case | Original answer SHA-256 | Supplemental input SHA-256 |
| --- | --- | --- |
| `brake-triage-p01` | `0b81075f6166bc55f83cc50409b5b713ba3d86587d19f88c36c5721c32efa8dc` | `0b81075f6166bc55f83cc50409b5b713ba3d86587d19f88c36c5721c32efa8dc` |
| `brake-triage-p12` | `3e4e97129977c49866222e7ff312eb17f3bc822be36bfaf8048b5281c46c8d8e` | `3e4e97129977c49866222e7ff312eb17f3bc822be36bfaf8048b5281c46c8d8e` |

## Result

| Case | Supplemental score | Pass criteria met | Fail signal observed | Owner fidelity verdict | Judge attempts | Judge retries |
| --- | ---: | --- | --- | --- | ---: | ---: |
| `brake-triage-p01` | 2 | true | false | `no_load` | 1 | 0 |
| `brake-triage-p12` | 2 | true | false | `expected_owner_loaded` | 1 | 0 |

Supplemental summary: `case_count=2`, `positive_mean=2.0`, `overall_mean=2.0`, `score_histogram={"0":0,"1":0,"2":2}`.

The retry path did not fire in this supplemental run because both supplemental judge calls returned parseable JSON on attempt 1. The retry fix is nevertheless covered by unit tests and will preserve retry attempt artifacts on future unparseable judge outputs.

## Fingerprints

| Component | SHA / Fingerprint |
| --- | --- |
| Fixture | `5ba3f7fe88e8f304077d8fa11fc62cb23d6601603961920cc57cd4f15d463d13` |
| Runner | `363c109f3fc3690b267662ce36d17e21cae93e698c195731d80450acac3d31e2` |
| Score records | `02480213a58ca14610482f2c4a235562e924a96d91b72bb937b86cb4d7e129a7` |
| Summary | `6bd175e41557a4491b184d8758ce208ff9b23dc1d5b659086c8c001b3c873c42` |
| Run manifest | `b76ba3734b8e448cc1a1884c77b47273bd0e85c73e931af0cd5b0c866d0910c7` |
| Prompt v0.3 | `d6086a6a6069ca6bdef5640187c205a75064df47f408794335c24bae23a1aebd` |
| Triage model | `provider-model:gpt-5.5` |

## Original Parse-Failure Records

The original repeat-3 judge records remain in place:

| Case | Original judge record SHA-256 |
| --- | --- |
| `brake-triage-p01` | `dbeef2d49c55aa29f7249a89d4ec355c77f9939bae27f62aa61e464725e62b7f` |
| `brake-triage-p12` | `f2bd06e035937244dd4e00870a78b41f1f050f4dc3df3ab3c30ced4749c307d6` |
