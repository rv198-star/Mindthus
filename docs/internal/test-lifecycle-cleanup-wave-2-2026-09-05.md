# Test Lifecycle Cleanup Wave 2 — 2026-09-05

Parent #167, work item #170. This is the first low-risk slice, not a blanket retirement.
Baseline before this slice: 749b9a33 (SRA dependency fix). No production files change.

## Reviewed retirements

| Retired executable owner | Protected invariant | Current replacement | Residual risk |
|---|---|---|---|
| V10ReadinessTests.test_release_pack_carries_license_judge_script_and_rubric | LICENSE, COMMERCIAL-LICENSE.md, fidelity judge and SELA rubric in three layouts | PackagingDocsTests.test_release_pack_builder_creates_claude_marketplace_root_layout calls _assert_packaged_fidelity_assets | None knowingly removed; all 12 original path assertions retained |
| PackagingDocsTests.test_release_pack_includes_split_primitive_docs | Whole Elephant primitive document in five package roots | Same existing all-layout build validates all five exact paths | None knowingly removed; all five paths retained |

The current package is now built once instead of three times for this assertion cluster.
This does not share mutable packages across independent tests. Existing tests that modify
packages or check separate package modes keep their own temporary output.

## Replacement evidence

`test_fidelity_asset_coverage_detects_each_missing_packaged_file` creates a temporary
17-file tree. It removes each file separately, observes an AssertionError from the exact
helper used by the real package test, then restores that file. This proves the replacement
checks detect every retired assertion's missing-file failure. It does not certify file
content or semantic judgment; other existing tests continue to cover those surfaces.

Net test functions: minus one (two removed, one fault-injection table added).
All original asset cases remain; test count reduction is not the acceptance criterion.

## Preserved

Historical v0.9/v1.0 acceptance reports, licensing text, judge exit legitimacy, privacy,
authority, transaction, runtime recovery, prior SRA failure regressions and platform
isolation tests remain executable. No historical test is retired solely due to age.

## Evidence and remaining work

Focused packaging/readiness/release tests: 64 run, 63 pass, one optional dependency skip.
Whole-suite and remote CI results belong to this slice's PR and exact commit.
The first slice removes two redundant builds; no percentage speed-up is claimed from a
single noisy measurement. Remaining #170 work: review other assertion ownership overlaps
and update test ownership after #171/#172 structural moves. Do not close the full issue
based on this slice alone.
