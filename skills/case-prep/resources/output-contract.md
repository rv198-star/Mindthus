# Case Prep Output Contract

A successful run returns:

```text
mode
case_type or TPlan focus
package_dir
archive_path
review_required_before_share: true
automatic_upload: false
warnings
item_count                 # collection only
```

Collection mode produces one `mindthus.case-collection.v1` directory and `.tar.gz`:

```text
mindthus-case-collection-<id>/
├── manifest.json
├── index.md
├── privacy-scan.json
├── README.md
└── cases/
    ├── mindthus-case-<id>/
    └── mindthus-tplan-case-<id>/
```

Every nested case remains independently validated and review-required. The collection
is not a combined Judgment Trace.

Judgment and benchmark modes produce a Case Export v1 directory plus `.tar.gz`.

TPlan mode produces:

```text
mindthus-tplan-case-<id>/
├── manifest.json
├── mission-summary.json
├── mission-summary.md
├── selected-event.json
├── selected-evidence.json
├── pulse.json
├── privacy-scan.json
├── README.md
├── judgment-trace.json   # optional
└── excerpts/             # optional
```

The final user response should lead with the inferred mode/focus, the archive path, and
privacy warnings. Do not claim the archive was uploaded, shared, admitted to a
benchmark, or proven anonymous.
