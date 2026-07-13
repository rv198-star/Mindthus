# Research Runtime Artifact Retention Policy

Status: archive-only research evidence

Applied on 2026-07-13 to `codex/brake-semantic-triage-design` after the brake
research line was closed. The cleanup parent is
`6efeda766c47d1606191b872d72e2bd1ccb8b087`.

## Retained Evidence Spine

The branch tip keeps the material needed to understand and audit the decisions:

- campaign reports, freeze receipts, prechecks, and invalid-attempt summaries;
- top-level aggregate tables and focused extraction packages;
- per-run manifests, summaries, contamination reports, and activation summaries;
- the decisive negative four-hard-gate redline record; and
- compact action-anchor rationales and retry/activation extracts where they carry
  a finding not reproduced in the report.

## Removed From The Branch Tip

The cleanup removes generated, high-volume runtime material:

- per-call prompts, answers, events, stderr, and last-message files;
- generator, triage, action, and judge intermediate records;
- score-record streams and full raw-response streams;
- per-sample schemas and duplicated telemetry; and
- disposable external-shadow fixture text.

In total, 23,847 generated files were removed from the branch tip. The 16 closed
campaign directories went from 24,230 files and about 219 MB of checkout footprint
to 383 files and about 4.4 MB.

## Recovery And Path Semantics

This cleanup does not rewrite Git history. A deleted artifact can be inspected at the
cleanup parent, for example:

```bash
git show 6efeda766c47d1606191b872d72e2bd1ccb8b087:<path>
```

Path fields inside retained JSON and Markdown remain provenance pointers to the
capture-time layout. Some no longer resolve at the branch tip; use the cleanup parent
when raw reconstruction is genuinely necessary.

## Future Default

Raw benchmark output should stay outside Git unless a specific artifact is required
to support a decision that cannot be reconstructed from the compact report, manifest,
aggregate, or redline record. New campaigns should publish the smallest sufficient
evidence package instead of committing an entire runtime directory.
