# Typed Decision — recovery entry

Branch: `experiment/typed-decision-runtime`.
Workspace: `/srv/agentdock/projects/Mindthus` (separate clone; original checkout unchanged).
Base: `1527f32b99c375db9ff73f80812c644686a6576a`.
Task: `tsk_b044702dfd8812df`.

## Goal
Implement #209/#210 design and #211 C01 first. Start #212 C02 only after the shared interface, recovery and cost slice has been verified. Keep non-Jev main and #112 HOLD/#207 separate. This is experimental code, not a default skill route.

## Current boundary
- Source issue contracts read in full, including #209 bounded dynamic design update.
- No model API credentials present in the service environment; live inference not run.
- Engineering fixtures are not semantic holdout data or evidence of benefit.
- Dynamic design is optional; do not build an automatic designer as a pilot prerequisite.

## Current step
#209/#210 source documents are landed. #211 first offline engineering slice is implemented: typed contracts, native Jev/structured-chat adapters, immutable batched-call journal, C01 DAG, local method-file consumption and existing Trace v1.1 bridge.

Final verification: 45 targeted tests; full suite 1129 tests with 5 skipped; lifecycle coverage 80/80. Sources for skills/scripts/TPlan/release remain unchanged. Separate Codex read-only review failed authentication (HTTP 401); only author self-review and executable probes were completed.

**#211 remains OPEN**: real A/B/C datasets/protocol/budget, live session carrier/native host consumption, independent review and semantic/value evidence remain. Current CLI intentionally supports offline fixtures only. #212 was not started; its original conditional entry is unchanged. Do not automatically expand the first slice into C02 or a dynamic designer to claim completion.

Next: resume #211 from these remaining gates, preserving the final offline evidence when runtime source is unchanged. Inspect verification.json and REVIEW.md. No live Jev call or benefit result exists.

## Resume
Read this file, `standard.md` section 5, then the active issue. Inspect git status and test evidence before continuing. Preserve passed evidence on unchanged source; do not rerun live inference to recover context. Goal/criteria/permission changes require an explicit contract delta, not additional guardrails.
