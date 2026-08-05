# Case Export v1 / 用户授权案例导出

Mindthus Case Export creates a bounded package on local disk for user review. It is a
precondition for later voluntary contribution, not a telemetry or upload system.

## Create A Package

Use a validated Judgment Trace and a structured case summary:

```bash
python3 scripts/export-mindthus-case.py \
  --trace skills/_runtime/judgment/fixtures/traces/intervention.json \
  --summary skills/_runtime/judgment/fixtures/case-summaries/judgment-failure.json \
  --case-type judgment_failure \
  --out-dir /tmp/mindthus-case-exports
```

The command creates:

```text
mindthus-case-<case-id>/
├── manifest.json
├── judgment-trace.json
├── case.md
├── privacy-scan.json
└── README.md
```

No network request is made.

## Explicit Redacted Excerpts

Raw conversation text is excluded by default. To include a selected UTF-8 excerpt, the
user must name the file explicitly and confirm that it was reviewed and redacted:

```bash
python3 scripts/export-mindthus-case.py \
  --trace path/to/trace.json \
  --summary path/to/summary.json \
  --case-type value_delta \
  --out-dir /tmp/mindthus-case-exports \
  --excerpt observation=path/to/redacted-observation.txt \
  --confirm-excerpts-redacted
```

The exporter rejects common private-key and token patterns and warns about a limited
set of identifiers such as email addresses and home paths. This scan is not an
anonymization guarantee.

Attachments are deliberately unsupported in v1. Full prompts, full answers, task logs,
environment variables, credentials, and private file contents are never included
implicitly.

## Validate Before Sharing

```bash
python3 scripts/validate-mindthus-case.py /tmp/mindthus-case-exports/mindthus-case-...
```

A passing validator means only that the package follows the current shape and no known
blocking pattern was detected. The manifest always keeps:

```text
review_required_before_share: true
automatic_upload: false
redaction_status: review_required
```

Sharing is a separate manual action.

## Review Checklist

1. Read every file in the package.
2. Confirm the manifest accurately describes included content.
3. Remove names, credentials, customer data, private paths, and unnecessary excerpts.
4. Re-run the validator.
5. Decide separately whether to contribute the package.

Delete the package directory to remove the local export. The exporter creates no
central copy.

## From Export To Benchmark Or Test

A reviewed export is only a candidate. Admission should be a separate review that:

- confirms the case is sufficiently redacted and authorized;
- identifies the protected failure class or counterfactual decision delta;
- assigns a benchmark case ID or test lifecycle owner;
- records evaluator limits and avoids claiming causal value without comparison evidence.

The `links` section in `manifest.json` may be filled at export time or during later
review. No automatic issue creation or benchmark admission occurs.

## TPlan Boundary

TPlan may provide an explicitly selected, redacted excerpt or a reference to a bounded
Judgment Trace. Case Export v1 does not export a Mission directory, task tree, evidence
log, telemetry stream, or recovery state.
