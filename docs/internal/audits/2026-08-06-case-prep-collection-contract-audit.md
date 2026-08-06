# Case Prep Collection Contract Audit — 2026-08-06

## Scope

Independent review of the new all-current collection path for:

```text
/mindthus:case-prep 导出当前所有mindthus相关案例
```

The review focused on case selection authority, contract separation, privacy, nested
package integrity, deduplication, and failure behavior.

## Findings And Resolutions

### Collection must not become a mega-trace

Resolution: collection mode accepts only already prepared, independently valid Judgment
or TPlan case directories. Each nested package retains its own manifest, validator,
privacy scan, trace/summary, and review boundary. The collection contains an inventory
and copies of those packages; it does not synthesize one combined Judgment Trace.

### “All current” must not mean raw conversation export

Resolution: the skill contract limits candidates to bounded reusable events and tells
the agent to omit ordinary acknowledgements, feature discussion without an observed
judgment event, and repeated turns describing the same root case. No script reads or
copies a conversation transcript.

### Duplicate and ambiguous cases

Resolution: the agent deduplicates by root event before packaging. The runtime also
fails closed on duplicate package paths and duplicate case IDs. Ambiguous weak
candidates are omitted rather than converted into invented cases.

### Nested package tampering

Resolution: the collection validator re-runs the correct nested validator for every
case package. A nested automatic-upload flag, malformed trace, raw TPlan runtime dump,
privacy mismatch, or unsupported file invalidates the collection.

### Collection manifest and file index

Resolution: `mindthus.case-collection.v1` has a published JSON Schema and an independent
built-in validator. The validator cross-checks item IDs, mode/schema pairing, package
names, paths, files index, nested directories, privacy scan status, and warning codes.

### Malformed manifest detection

Resolution: the validator recognizes a collection by both schema and the reserved
`mindthus-case-collection-` directory prefix. A malformed manifest therefore returns a
collection validation report instead of falling through to the TPlan validator.

### Collection size and output safety

Resolution: a collection is limited to 20 cases. Source packages must be regular,
symlink-free, independently valid directories, and the output collection must remain
outside every source package.

## Privacy Boundary

Every collection requires:

```text
export_requested_by_user: true
review_required_before_share: true
automatic_upload: false
contains_raw_conversation: false
contains_full_tplan_runtime: false
redaction_status: review_required
```

Nested privacy warnings are aggregated, but a clean aggregate does not prove anonymity.

## Verdict

Accepted after remediation. The collection is a bounded delivery envelope over
independent case contracts and does not weaken Judgment Trace, Case Export, or TPlan
privacy boundaries.
