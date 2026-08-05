# Case Export Contract / 用户授权案例导出合同

Status: Implemented (initial v1)
Priority: P1
Execution: Complete for local export, validation, and review contract

## Problem

Mindthus needs real failure and value-delta cases to improve routing, methods, benchmarks, and tests. Usage is distributed across users, clients, and nodes, so a centralized collection mechanism would require substantial privacy, consent, storage, and governance work.

Waiting for centralized telemetry would block learning infrastructure. Exporting raw conversations would also collect more data than the judgment problem requires.

## Core Decision

Create a local, user-controlled Case Export Contract before implementing centralized collection.

The export must package a bounded, inspectable judgment case that the user can review before sharing. Default exports should prefer structured judgment facts and redacted excerpts over full conversation transcripts.

This issue defines the contract and a local exporter. It does not create automatic upload or background telemetry.

## Case Types

The first version should support a small set of case intents:

- `judgment_failure`: a route, frame, evidence, or decision failure occurred.
- `judgment_repair`: a later intervention corrected an earlier judgment path.
- `value_delta`: baseline and Mindthus paths produced a material decision difference.
- `routing_ambiguity`: owner or method selection remained unclear.
- `test_regression_candidate`: a real case may deserve a fixture or regression test.

The list should remain small until real exported cases demonstrate additional categories.

## Proposed Package

```text
mindthus-case-<case-id>/
├── manifest.json
├── judgment-trace.json
├── case.md
├── privacy-scan.json
├── excerpts/                 # optional, user-reviewed and redacted UTF-8 text
└── README.md                 # privacy and sharing notice
```

`judgment-trace.json` should use the Judgment Trace contract when available. Until that schema is implemented, the exporter may use a versioned draft adapter rather than inventing an incompatible permanent format.

## Proposed Manifest Fields

```json
{
  "schema_version": "mindthus.case-export.v1",
  "case_id": "...",
  "case_type": "judgment_failure",
  "created_at_utc": "...",
  "source_client": "optional",
  "source_method": "optional",
  "consent": {
    "export_requested_by_user": true,
    "review_required_before_share": true,
    "automatic_upload": false
  },
  "privacy": {
    "contains_raw_prompt": false,
    "contains_raw_answer": false,
    "contains_attachments": false,
    "contains_user_selected_excerpts": false,
    "redaction_status": "review_required",
    "pattern_scan_status": "passed"
  },
  "links": {
    "benchmark_case_id": null,
    "related_test_id": null,
    "related_issue": null
  }
}
```

## Required Human-Readable Case Summary

`case.md` should make the exported case understandable without requiring the original conversation:

- decision context;
- observed failure or value delta;
- active judgment object;
- selected route or method;
- missed or correctly detected signal;
- evidence available and missing;
- action, risk, evidence, or stop-condition delta;
- expected repair or learning hypothesis;
- uncertainty and redaction notes.

## Mainline Work

1. Define the versioned manifest and directory contract.
2. Align the structured judgment section with Judgment Trace.
3. Define redaction defaults and prohibited automatic inclusions.
4. Provide one CLI or script that exports a case to a local directory only.
5. Require a review step before any package is considered shareable.
6. Add fixtures for a failure case, a value-delta case, and a minimal redacted case.
7. Add validation for package shape, consent flags, and accidental high-risk content indicators where feasible.
8. Document how a reviewed package could later become a benchmark fixture or GitHub contribution.

## Privacy and Consent Rules

- No automatic upload.
- No silent inclusion of full prompts, answers, task logs, credentials, environment variables, or private file contents.
- Raw excerpts require explicit selection and redaction confirmation; attachments are unsupported in v1.
- Export generation and contribution are separate user actions.
- The package must disclose what it contains before sharing.
- Validation may detect suspicious content shapes, but cannot guarantee anonymization.

## Guardrails

- Do not claim that structured export is automatically anonymous.
- Do not make centralized telemetry a hidden dependency.
- Do not make the first version client-specific.
- Do not require TPlan mission export; TPlan may supply an explicitly selected reference or excerpt through an adapter.
- Do not use case export as proof that Mindthus caused a better outcome without an evaluator or comparison basis.

## Implementation Result

Implemented on 2026-08-06:

- local package implementation in `skills/_runtime/judgment/case_export.py`;
- versioned manifest schema under `skills/_runtime/judgment/resources/`;
- `scripts/export-mindthus-case.py` and `scripts/validate-mindthus-case.py`;
- Judgment Trace v1 as the structured core;
- failure, value-delta, and minimal-redacted summary fixtures;
- explicit excerpt selection plus `--confirm-excerpts-redacted`;
- blocking scans for common private-key and credential patterns and bounded warnings for
  identifiers requiring human review;
- manifest/package consistency checks and an always-on manual-review boundary;
- release-package validation and user documentation in `docs/internal/case-export.md`.

Attachments are intentionally unsupported in v1. This keeps the first contract
text-only and prevents a nominally explicit feature from becoming an unbounded binary
or private-file collection surface. Adding attachments later requires a separate
privacy and content-type design.

## Acceptance Criteria

- [x] A versioned Case Export schema and package layout exist.
- [x] A local exporter creates a reviewable package without network access.
- [x] Default export excludes raw conversation text and attachments.
- [x] Users can explicitly include selected, confirmed-redacted text excerpts.
- [x] Three canonical case intents validate successfully.
- [x] Documentation explains export, review, contribution, and deletion steps.
- [x] Judgment Trace v1 is used as the structured core.
- [x] No centralized collection, upload endpoint, or background telemetry was introduced.

## Dependencies

- Judgment Trace Infrastructure: preferred structured core and long-term compatibility anchor.

Contract design, privacy rules, package layout, and fixtures may begin before the final Judgment Trace schema is frozen.

## Non-goals

- Automatic issue creation.
- Automatic benchmark admission.
- Centralized storage.
- User identity tracking.
- Full conversation backup.
- Failure Learning Loop implementation.
