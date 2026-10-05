# TPlan Progress — Work, Evidence, And Remaining Effort

Runtime support for task-progress explanations. TPlan is the first formal upstream
integration. Use this view for meaningful progress reports, stage deliveries, or
questions about remaining work; keep routine short updates proportionate.

Contents: [Mainline](#mainline) · [Guardrails](#guardrails) ·
[Examples](#examples) · [Boundaries](#boundaries).

## Mainline

### Read The Existing Source

Use the supplied report or a consistent read-only view of the Mission, its task state,
acceptance and progress evidence, and any optional planning information. Existing
text reports and Missions without planning metadata remain valid inputs.

For a live Mission, TPlan's `read_work_view_snapshot(mission_dir)` supplies the atomic
read-only view; `build_work_view(mission, evidence, outcome_attribution)` consumes
already available source data. Follow TPlan's [user-output contract](../../tplan/resources/user-output.md)
for its renderer entrypoint. Optional `work_plan` metadata enriches this view without
replacing the existing state and evidence sources.

TPlan's normal planning and task-maintenance work supplies or updates estimates,
dependencies, resource constraints, risks, and blockers. Explain reads these facts and
judgments. If answering the user's task requires new analysis, let that normal upstream
work produce the result before explaining it.

### Answer The Five Progress Questions

| Question | Explain from the source |
| --- | --- |
| Where are we overall? | The goal, original state, evidenced results, current work, and material unresolved constraints |
| What work remains? | Understandable work blocks, their deliverables, source states, and known prerequisites |
| How much effort remains? | Current remaining estimates, units, coverage, and unestimated work |
| Which blocks account for most of it? | Shares of comparable, estimated remaining effort, with the denominator stated |
| What can run in parallel? | Known precedence, stated independence, resource conditions, and execution-capability limits |

Lead with work blocks the reader can describe. Expand individual Steps, evidence, and
historical execution detail as needed. Reading groups may reorganize presentation
while retaining the underlying task references and source meanings.

Risk and major-blocker columns or sections are optional. When source material supports
them, explain their effect and any known condition for resolution; include an owner or
timing only when supplied. Without such information, omit the dedicated section instead
of inventing entries or an empty checklist. Known critical constraints remain visible
in a brief view.

### Keep Progress, Estimates, And History Distinct

Present overall progress first in the upstream's own state and evidence terms.
Use a numeric overall indicator only when the upstream provides a meaningful,
consistent measure and its scope. Explain whether it concerns acceptance, planned
work coverage, or another defined measure.

Keep a reported `completed` state distinct from qualified acceptance or progress
evidence. When the source marks `completion_without_progress_evidence`, explain the
evidence gap in plain language while preserving the reported state. A completion
claim by itself also does not establish zero remaining effort.

Use the latest supplied remaining estimate for a block. Preserve its unit, basis,
scope, and uncertainty; retain any known staleness or revision context. Relative
work points, person-hours, elapsed duration, and money describe different quantities.
Keep original estimates and historically observed time or cost separate.

### Aggregate A Non-overlapping Scope

Use one consistent accounting basis with non-overlapping work blocks. Blocks may sit at
different depths in the task tree. Count a parent's covered work or the relevant
children, not both. Retain visibility of known work outside the estimated subset,
including work not yet broken down.

For comparable point estimates, add the known remaining values and calculate each
block's share of that known subtotal. Label partial coverage explicitly. Keep unknown
distinct from zero, avoid division by zero, and keep incompatible units in separate
groups. For interval estimates, retain the intervals and their supplied interpretation;
do not invent precise percentages by silently choosing midpoints. When the upstream
supplies share intervals with an explicit calculation basis, preserve that basis and
explain that separately bounded shares need not add to 100%; keep them as intervals.

If scope changes, make the changed basis understandable. Removing work or revising an
estimate is not evidence that execution advanced.

### Describe Parallel Conditions

Distinguish known predecessors, explicitly established independence, resource limits,
and unknown relationships. Task-tree containment and sibling position do not establish
execution dependencies. Missing dependency information does not establish independence.

Explain both logical independence and actual execution conditions. Shared writes,
exclusive equipment, quotas, or an execution environment can restrict concurrency.
An active-focus pointer alone proves neither serial nor parallel capability.

Show the conditions under which work can proceed together and any unresolved
information. TPlan's original execution mechanism owns task starts, resource allocation,
permissions, and state changes.

### Deliver A Useful View With Incomplete Data

When estimates are absent, explain the known state, evidence, and remaining work; label
the effort as unestimated. When dependencies or resource limits are unknown, say which
parallel conclusion cannot yet be supported. Missing optional data is not a reason to
reject the Mission or require migration.

Preserve TPlan's required standard report and SVG links. The execution SVG remains a
view of observed history and costs; it may be available as detail beneath the work
overview. Rendering this explanation does not update the Mission.

## Guardrails

These rules protect the progress view and cannot override TPlan's authority:

- Do not turn task counts, `completed` labels, `outcome_attribution` categories,
  `resource_sufficiency`, elapsed time, or token usage into a completion percentage.
- Do not infer remaining effort from original effort minus observed cost or treat
  person-hours as a promised finish time.
- Do not silently assess acceptance, alter task states, write planning metadata, or
  count estimate updates as execution or acceptance progress.
- Do not portray unknown prerequisites as none, tree edges as dependency edges, or a
  conditional parallel option as an already authorized running schedule.
- Do not bypass the Mission's runtime provenance or compatibility rules to obtain data.
  An existing report from its compatible runtime can still be explained.

## Examples

- A has about 3 person-hours remaining, B about 1, and C is unestimated: report about
  4 person-hours in the estimated subset, plus C. A/B shares of 75%/25% describe that
  subset, not all remaining work or overall completion.
- Nine small blocks are marked completed and one large block remains: a block count
  can describe source states; it does not establish 90% completion of the work.
- Two sibling tasks lack dependency information: show that parallel feasibility is
  unknown. If the source later confirms independence but a shared resource is exclusive,
  show that limiting condition.

## Boundaries

Explain provides representation and transparent arithmetic over existing information.
Planning estimates, dependency judgments, acceptance, and execution stay upstream.
V1 adds no scheduling optimizer, critical-path ETA, automatic dispatch, or runtime
review loop. Risk and blocker presentation supports understanding without becoming a
new decision or approval gate.
