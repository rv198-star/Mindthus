# Invalid Attempt 0: Required Flags Omitted

Status: excluded from all V0.4 triage and loaded-action evidence.

The original invocation omitted both `--brake-semantic-triage-subjudgment` and
`--brake-loaded-action-contract`. Its `original/run-manifest.json` records both flags
as `false`, plus `triage_enabled=false` and `owner_skill_activation_gate=disabled`.
The resulting answers are preserved for process traceability but are not a baseline,
not a repeat, and not included in any aggregate.

A zero-case parser smoke test immediately afterward confirmed that the intended command
line sets both flags to `true`. All valid repeats begin after this record.
