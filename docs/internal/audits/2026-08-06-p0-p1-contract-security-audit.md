# P0/P1 Independent Audit 1 — Contract, Privacy, and Boundary Review

Date: 2026-08-06
Verdict: Passed after remediation

## Independent Review Scope

This pass reviewed the implementation as a data-contract and local-security surface. It did not rely on release-package success as evidence.

Reviewed surfaces:

- Judgment Trace schema and Python validator;
- benchmark-to-trace adapter semantics;
- Case Export consent, privacy, redaction, file-layout, and tamper checks;
- Test Lifecycle registry ownership and lifecycle statements;
- absence of automatic upload and network behavior;
- TPlan separation from Judgment Trace.

## Findings and Remediation

### 1. Information acquisition was mislabeled as a hard judgment point

The benchmark adapter correctly routed `information_acquisition` to `acquire_information`, but its generic hard-judgment expression still emitted `hard_judgment_point: true`.

Remediation:

- explicitly exclude `information_acquisition` from hard-judgment classification;
- add a regression test asserting the route, owner, and hard-judgment flag together.

### 2. `privacy-scan.json` was not reconciled with validator observations

The package validator checked the manifest's declared scan status, but did not verify that the separate `privacy-scan.json` status and warning-code list matched the package's actual findings. A tampered package could therefore carry an internally inconsistent scan report.

Remediation:

- validate the privacy-scan schema, fields, status, warning-code list, and note;
- compare both status and warning codes with fresh validator observations;
- add a tampering regression test.

### 3. Test registry contained a resolved compatibility statement

The packaging/release registry note still described the Python 3.10 `tomllib` failure as current after the fallback had been implemented and tested.

Remediation:

- replace the stale statement with the current Python 3.11 CI and tested Python 3.10 fallback boundary.

## Verification

Commands and checks:

```bash
python3 -m unittest tests.test_judgment_trace tests.test_case_export tests.test_test_lifecycle -v
python3 scripts/check-test-lifecycle.py
python3 -m compileall -q scripts skills/_runtime/judgment
```

Result:

- 20 focused tests passed;
- all 68 executable test files were registered exactly once;
- no new Judgment Trace or Case Export module imports network or subprocess clients;
- trace validation remains shape-only and does not claim semantic truth;
- Case Export remains local-only and review-required;
- TPlan Mission, task, checkpoint, evidence, and telemetry state remain outside Judgment Trace.

## Residual Boundaries

- Pattern scanning cannot prove anonymity or complete redaction.
- Explicit excerpts remain user-selected content and require manual review.
- Judgment Trace records observable facts and evaluator labels, not private reasoning.
- Test lifecycle status does not automatically delete or archive tests.

## Final Verdict

Passed after the three findings above were corrected and covered by regression tests.
