# Typed Decision — recovery entry

Branch: `experiment/typed-decision-runtime`.
Workspace: `/srv/agentdock/projects/Mindthus` (separate clone; original checkout unchanged).
Base: `1527f32b99c375db9ff73f80812c644686a6576a`.
Primary implementation task: `tsk_b044702dfd8812df`.
Engine/serving abstraction task: `tsk_d08d9be8f54ccc4b`.

## Goal
Implement #209/#210 design and #211 C01 first. Start #212 C02 only after the shared interface, recovery and cost slice has been verified. Keep non-Jev main and #112 HOLD/#207 separate. This is experimental code, not a default skill route.

## Current boundary
- Source issue contracts and the normative `docs/methodologies/typed-decision-principles.md` are binding for this experiment.
- TypeSafe official and OpenRouter backup credentials exist only in encrypted NexusDock private notes; no credential is stored in the repository or evidence files.
- One OpenRouter Jev API compatibility smoke was observed earlier; it is not semantic qualification or a live C01 campaign.
- Engineering fixtures are not semantic holdout data or evidence of benefit.
- Dynamic design is optional; do not build an automatic designer as a pilot prerequisite.

## Current step
Functional source commit: `e9e78ccb009f1bddbad5991e35df90e7805ac343`. See `verification.json` for the runtime digest and test evidence.

The typed-decision runtime now has four explicit identity layers: Decision Contract → Decision Engine → Serving Provider/Transport → Resolved Runtime. TypeSafe native and OpenRouter Decisions expose the same canonical Jev engine identity while retaining distinct serving identities. Session recovery binds engine+serving configuration, records the actual resolved model/provider separately, and fails closed if the resolved runtime drifts inside one trial. C01 itself remains vendor-neutral.

Verification for this source: 50 typed-decision tests PASS; 157 related regression tests PASS (4 skipped); full suite 1134 tests PASS (5 skipped); lifecycle coverage 80/80. Provider-neutral C01 scan and tracked-secret scan PASS. Separate Codex read-only review remains unavailable from the earlier HTTP 401 attempt; executable tests and author review are the current evidence.

**#211 remains OPEN**: C01-v2 Decision Contract correction, Chinese development/holdout data, official TypeSafe semantic runs, live session carrier/native host consumption, independent review and A/B/C value evidence remain. Current CLI intentionally supports offline fixtures only. #212 remains conditionally unstarted.

Next: implement the C01-v2 Decision Contract correction already recorded in #211, then freeze a small Chinese development set and use the official TypeSafe path as primary with OpenRouter as backup/transport evidence. Do not reopen provider abstraction unless new evidence shows a real contract gap.

## Resume
Read this file, `standard.md` section 5, then the active issue. Inspect git status and test evidence before continuing. Preserve passed evidence on unchanged source; do not rerun live inference to recover context. Goal/criteria/permission changes require an explicit contract delta, not additional guardrails.
