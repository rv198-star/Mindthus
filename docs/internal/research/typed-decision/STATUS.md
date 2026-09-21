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
#209/#210 source documents imported; next implement a thin bounded provider/session and the C01 graph with offline adversarial recovery tests.

## Resume
Read this file, `standard.md` section 5, then the active issue. Inspect git status and test evidence before continuing. Preserve passed evidence on unchanged source; do not rerun live inference to recover context. Goal/criteria/permission changes require an explicit contract delta, not additional guardrails.
