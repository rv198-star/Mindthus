# tplan User-Facing Output Adapter

## Core

Internal IDs are for runtime stability. User-facing output should lead with meaning.

Runtime state may store `T1`, `S2`, `E3`, and decision packet references. Ordinary user
updates should translate those references into task titles, evidence summaries, current
blockers, and next-action language.

## Default Shape

Use only the fields that matter, but ordinary updates should usually prefer this shape:

```text
当前目标：
...

当前进展：
...

可计推进：
- ...

关键约束：
- ...

已确认事实：
- ...

下一步：
...
```

The goal is not to hide uncertainty. The goal is to explain evidence and state in the
language the user can act on.

## Node Translation

Render task references by title or active work description.

```text
Internal: active_task_id = T1
User-facing: 当前在处理“整理 tplan 用户输出适配器”。
```

Parent chains should become short path summaries:

```text
Internal: T2 -> S1
User-facing: 当前在“优化运行时性能”下面处理“轻启动摘要输出”。
```

## Evidence Translation

Render evidence references as observable summaries, without mixing progress and
constraints:

- `acceptance_passed` or complete legacy `acceptance`: countable progress describing
  what passed and where it was observed
- `acceptance_failed`: a key constraint, never positive progress
- `blocker`: what prevents safe continuation
- `user_feedback`: what the user corrected, rejected, or confirmed
- `decision` / `decision_recommendation`: what choice was made and why it matters
- `key_finding`: what was learned that changes the next action
- `stop_report`: why work stopped and what is needed to resume

Only qualified acceptance deltas and runtime-applied path decisions belong under
`可计推进`. Blockers, failures, feedback, stop reports, risk changes, failed acceptance,
and unapplied recommendations belong under `关键约束`. Key findings and state facts may
appear under `已确认事实`, but they do not become progress by wording alone.

Do not lead with `E1`, `E2`, or similar labels in ordinary updates.

## Debug And Audit Mode

Raw IDs may appear when:

- the user asks for internal state
- strict audit requires stable references
- a stop report needs exact recovery anchors
- a script failure references a specific invalid node or evidence item

Even then, place IDs after the human-readable explanation.

```text
内部恢复引用：
- mission_id: ...
- active_task_id: T1
- evidence_ids: E1, E2
```

## Stop Reports

Stop reports should not lead with raw task or evidence IDs. They should first explain:

- current goal
- what was attempted
- blocker
- why continuing is unsafe
- what the human needs to provide
- resume condition

Internal recovery references may appear as a final section when needed.

## Runtime Support

Use `scripts/render_user_update.py` to render a compact Chinese update from Mission
runtime state.

Default mode hides raw IDs:

```bash
python3 skills/tplan/scripts/render_user_update.py "$MISSION_DIR"
```

Debug mode appends secondary internal recovery references:

```bash
python3 skills/tplan/scripts/render_user_update.py "$MISSION_DIR" --include-internal
```

### Automatic Update Delivery

An automatic status delivery may carry the opaque cursor returned by its previous
render:

```bash
python3 skills/tplan/scripts/render_user_update.py "$MISSION_DIR" \
  --delivery automatic --cursor OPAQUE_CURSOR --json
```

The renderer compares the complete Mission digest, evidence boundary, and a
message-free Interaction Guard control-state digest without writing state. With no
new user-visible runtime state, the first two automatic calls
return `update_kind=quiet` and no text; the third returns an honest `heartbeat`, then
resets its cursor streak. This is delivery pacing, not progress evidence.

Use `--delivery explicit` for a user-initiated status question. It always returns a
brief answer even when the cursor is unchanged. New Mission/evidence state, a blocker,
stop, Guard boundary change, or a cursor error must never be hidden as quiet. A
pending Mission transaction is an explicit error: the renderer and a survey-only
checkpoint never recover it by writing state. Each delivery channel owns its own
cursor; do not put it in `mission.json`, evidence, or a renderer sidecar.

When a Guard change causes a full render, the text must say whether write protection is
active (with its phase and revision) or has just been released. Never expose message
references or message text in that status line.

`checkpoint.py` with neither a log nor evidence is a survey-only no-op. It reports
`checkpoint_noop` and does not claim that work was recorded.

## Progress And Remaining Work View

When the user asks to understand overall progress, remaining work, workload shares or
parallel execution conditions, render the optional work view from one read-only
Mission/evidence snapshot:

```bash
python3 skills/tplan/scripts/render_user_update.py "$MISSION_DIR" --progress

python3 skills/tplan/scripts/render_user_update.py "$MISSION_DIR" \
  --html "$MISSION_DIR/reports/progress.html"
```

The HTML option implies the progress view. It produces one self-contained offline
document. Its **first-screen contract** is deliberately narrow: show the declared
overall progress, remaining work, and the remaining-work share for each comparable
block. A compact Mission status line may orient the user. Risk/blocker narratives,
qualified evidence, dependency graphs, detailed estimate basis, search/filter controls,
source notes and existing execution artifacts belong in a default-collapsed detail
area. New semantic fields do not move onto the first screen merely because they exist.

The document embeds styling and a small script for selecting a work block and, inside
the detail area, search/status filtering. It has no CDN, remote font, external script,
implicit network request or action button. The view does not write Mission state or
evidence and cannot replace the Standard execution report. Interval shares remain
intervals in the visual representation; the renderer does not select a midpoint.

HTML delivery follows Explain's dual-surface contract: after generating the one
self-contained file, a host with native HTML/artifact preview should display that same
artifact inline in the conversation and also expose the file for independent download.
A host without inline HTML support falls back to the downloadable artifact and states
the host limitation. The TPlan renderer itself only produces the artifact; host UI
presentation does not become Mission state or runtime authority.

For the view alone, use the dedicated renderer:

```bash
python3 skills/tplan/scripts/render_progress_view.py "$MISSION_DIR" --format text

python3 skills/tplan/scripts/render_progress_view.py "$MISSION_DIR" \
  --format html --out "$MISSION_DIR/reports/progress.html"

python3 skills/tplan/scripts/render_progress_view.py "$MISSION_DIR" --format json
```

Formats are `text`, `html` and `json`; output defaults to stdout. `--out` (or
`--output`) writes an artifact atomically. Outputs inside the Mission must be under
`reports/`; the renderer refuses runtime-state targets and the Standard execution
report filenames. `--include-internal` adds secondary recovery references.

When `reports/execution-cost-tree.md` or `.svg` already exists, the view links that
actual file. HTML written to a file uses relative links; text uses absolute links.
The links are labelled as existing records that may predate the current snapshot.
Rendering the overview does not generate, refresh or overwrite either Standard
artifact, and missing files do not produce invented links.

### Keep Planning Metadata Current

When a plan is formed, its scope changes, a major blocker changes the remaining work,
or estimates are revised, maintain the optional `work_plan` using already available
context. Use the canonical writer, whose full input contract is in `schema.md`:

```bash
python3 skills/tplan/scripts/record_work_plan.py "$MISSION_DIR" \
  --input /path/to/work-plan.json --summary "Updated the existing planning facts."
```

Do not edit Mission control JSON directly. Leave unknown estimates, prerequisites and
parallel conditions unknown; do not question the user block by block or invent values
to fill the view. Planning metadata is not an acceptance result or continuation grant.

### Read The Numbers And Conditions Faithfully

The optional `mission.json.work_plan` contract is defined in `schema.md`. Its
`build_work_view` projection supplies the numbers and relationships; text and HTML
use that same projection.

- Show a declared overall progress value only with its source label, unit and basis.
  When none exists, show known state and qualified progress evidence without
  inventing an overall percentage.
- Show real, non-overlapping work blocks. Parent/child hierarchy is not a dependency
  graph and does not imply that a parent's estimate is additional to its children.
- Keep explicit zero estimates distinct from unknown estimates. Add comparable
  remaining ranges only within one unit and expose incomplete coverage. Mixed units
  produce separate declared subtotals, never one total.
- A completed node with positive source remaining work, or without qualified progress
  evidence in the supplied attribution, remains visible as needing reconciliation.
  Preserve its original status and estimate; expose the reason, mark coverage partial
  and do not assert a complete remaining total. Real unresolved ancestor/descendant
  state rows may appear separately, without adding a new estimate or copying a
  parent's amount. `remaining_uncertain` and `accounting_role=state_context` identify
  those presentation cases; they do not change task state or authorize execution.
- A block's remaining share describes the already estimated work in the same unit.
  Partial coverage stays visible; interval shares need not add to 100%. This is not a
  Mission completion percentage, schedule or cost estimate.
- Missing prerequisite data means unknown. An explicit empty dependency list means
  the source declared no prerequisite. Only recorded dependencies produce graph
  edges; visual position and task hierarchy create no edges.
- A completed recorded prerequisite satisfies that recorded dependency only.
  Present supplied parallel conditions; do not infer that execution units, workspaces,
  budget, timing or authority are available.
- Current risks and major blockers are optional source information. Show their
  supplied summaries, impacts and release conditions when present; omit absent
  sections instead of inventing entries or empty tables. This includes active existing
  Shared Risk Context signals with their original severity, scope, affected surfaces,
  confidence, recovery condition and source. A reporting task is not the entire affected
  scope. Do not hide a known major restriction behind disclosure.
- Keep Mission stop/human-authority states, write protection and material data
  limitations visible before the work table. A useful explanation cannot upgrade an
  implementation to accepted, or a plan to authorization.

The overview retains the ordinary adapter's five semantic inputs: qualified progress,
recorded constraints, confirmed facts, next-step text and Interaction Guard state
including a just-released transition. It reuses their existing source rules and helpers.
Constraints and acceptance counterexamples retain evidence type, time and task source;
historical blockers are not silently relabelled as current risks. Estimate confidence
is preserved in text and HTML when supplied.

Runtime provenance is checked against the same in-memory Mission snapshot, without a
second Mission read. Legacy and compatible-relocated records carry visible warnings.
An incompatible runtime returns diagnostics only: `diagnostic_only=true`,
`work_view=null`, no business progress summary and no new recovery/adoption path.
The complete existing provenance report remains in `runtime`; see
`runtime-provenance.md` for its unchanged authority boundary.

The JSON payload is `tplan.progress_view.v1`; `work_view` retains the
`tplan.work_view.v0.1` source projection, alongside Mission meaning, snapshot digests,
qualified progress, constraints, facts, next step, guard transition and display limitations. JSON keeps stable task references;
ordinary human text leads with titles. This is a read-only representation, not a new
Mission schema, judgment owner or acceptance result.

`render_user_update.py --progress --json` preserves its cursor and change metadata
and adds `progress`. An explicit request gets `update_kind=progress` even if the
source cursor is unchanged; automatic unchanged calls retain `quiet`/`heartbeat`
delivery. A runtime incompatibility returns `update_kind=diagnostic` even for an
unchanged cursor. `--html PATH --json` also returns `html_path`. An explicitly requested HTML
artifact is generated even when the same snapshot was previously rendered. Without
either option, the original compact update and heartbeat contract is unchanged.

Explain may use this view as input for a requested clearer or shorter delivery.
Preserve the source constraints, risks, uncertainty and optional workload information;
do not add a compulsory Explain step to every Mission update.

## Terminal Mission Delivery Contract

For every terminal Mission handoff (`completed`, `blocked`, `budget_exhausted`,
`abandoned`, `superseded`, or `requires_human`) and every explicit cost review, render
the Standard execution artifacts before writing the final user response. This is an
artifact/evidence obligation, not a requirement to paste the complete tree into ordinary
business text. Lead with results, limitations and next action, and link the details:

```bash
python3 skills/tplan/scripts/render_execution_cost_tree.py "$MISSION_DIR" \
  --completion-handoff
```

This writes these reproducible artifacts:

- `$MISSION_DIR/reports/execution-cost-tree.md`
- `$MISSION_DIR/reports/execution-cost-tree.svg`

The command prints two absolute Markdown links. Copy both into the terminal user
response under a short label such as `TPlan 执行记录` so the user can open the report or
view the process graph directly. Do not replace the links with a claim that the graph
exists. If rendering fails, state that the execution graph is unavailable, include the
recoverable command above, and do not hide the failure behind a completed claim. Do not
substitute a hand-authored, alternate, or approximate SVG/diagram for the failed
Standard renderer.

The report includes the Mission runtime-provenance result. A known incompatible
fingerprint makes `--completion-handoff` fail before either existing report artifact is
replaced. Diagnose duplicate roots, selected-versus-installed paths, missing render
capabilities, and Mission mismatch with `scripts/runtime_doctor.py`; recovery steps are
defined in `runtime-provenance.md`. A legacy unpinned Mission may render with an
explicit warning, but that warning must not be presented as a verified creator runtime.

After completion or cost review, use `scripts/render_execution_cost_tree.py`. Default
to `standard`: show every real Mission / Task / SubTask / Step and declared edge, with
status, result, attribution, and only those elapsed/cost/Token fields that were observed
or explicitly reported unavailable. Missing cost channels are consolidated into one
Mission-level coverage statement; an omitted Standard field never means zero.
The primary Standard/Audit layout is a portrait SVG execution view: rows follow
first-observed chronology when lifecycle trace exists, every observed card has a
shared-scale range bar, and the declared hierarchy is overlaid as tree edges. Exact
lifecycle coverage is labelled an actual execution timeline; partial coverage is an
observed execution window; no trace is a Mission structure snapshot. Vertical row
spacing is ordinal and must never be interpreted as duration.
Keep `host_measured`, `platform_reported`, and `inferred` visibly distinct. A
host-measured model span is caller-visible request time, not a claim about pure provider
inference time. Label the uncovered elapsed remainder as not exactly recorded; do not
assign it to LLM or script by guesswork. Do not merge nodes or invent display groups.
Use `compact` only as a labelled Unicode text-tree projection for a quick handoff; it
does not render SVG. Compact always keeps real root Tasks, then selects real active or
abnormal, retry, error, open-span, dynamic, and top direct-cost nodes while preserving
the real ancestor paths required to reach them. The default is the top three direct-cost
nodes; `--top-cost N` may override it. Every visible line keeps actual elapsed, LLM,
and script time. Tool/wait time appears only when collected. Node Token appears only
for an execution-signal or selected top-cost node. Routine successful outcomes are
omitted; abnormal, retry, error, open-span, and dynamic outcomes remain visible.
Measurement sources and the Mission-level not-exactly-recorded remainder move to one
footer rather than repeating in every node. Compact reports only shown/total and omitted
counts in the tree; the machine report retains the full selection policy. Compact
prefixes every real node with `[T]`, `[ST]`, or `[P]` for Task, SubTask, or Step and
prints that legend above the tree. Use `audit` for complete topology plus recovery and
measurement detail. Unknown measurements must remain unknown.

Execution-cost report JSON uses `tplan.execution_cost_tree.v0.9`. It retains the
complete lifecycle, cost, Token, Codex channel, diagnostic, and per-node contracts and
adds `presentation_density`, derived from actual trace/cost coverage rather than a
platform name. `outcome_attribution` remains separate on the Mission and every node.
Costs remain visible even when attribution is `telemetry_only`. Compact uses short
labels such as `推进`, `约束`, `仅写回`, `仅遥测`, and `未分类`; Standard/Audit explain
the attribution. Audit also shows evidence ids, commit ids, unclassified reasons, and
compatibility warnings.
Never turn these categories into a completion percentage, score, Token-per-result
ratio, or causal claim that a particular span produced an evidence event.
The top-level `runtime` field separately reports exact, relocated, legacy, or
incompatible runtime provenance and its diagnostics.
The top-level `telemetry_capture` field separately reports the optional Codex adapter's
binding, activation, and channel coverage. Coverage `v0.2` keeps App and CLI records
separate and retains concrete build/version plus user/project source path, source hash,
enumeration, handler hash, trust, enabled, binding, and callback-health diagnostics.
Standard reduces absent channels to one Mission-level statement and conditionally
renders observed or explicitly unavailable node metrics.
Audit renders every channel status and diagnostic reason. It also renders every
activation state, including explicit `not_reported` reasons for hosted tools,
model/turn data, Tokens, waits, or SubAgents. JSON retains both the complete channel
report and raw cost/lifecycle fields. Missing telemetry is never rendered as zero and
never changes the one-to-one Mission hierarchy.
