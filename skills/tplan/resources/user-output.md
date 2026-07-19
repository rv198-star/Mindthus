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

已确认：
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

Render evidence references as observable summaries:

- `acceptance`: what passed and where it was observed
- `blocker`: what prevents safe continuation
- `user_feedback`: what the user corrected, rejected, or confirmed
- `decision` / `decision_recommendation`: what choice was made and why it matters
- `key_finding`: what was learned that changes the next action
- `stop_report`: why work stopped and what is needed to resume

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

## Terminal Mission Delivery Contract

For every terminal Mission handoff (`completed`, `blocked`, `budget_exhausted`,
`abandoned`, `superseded`, or `requires_human`) and every explicit cost review, render
the full Standard execution report before writing the final user response:

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
recoverable command above, and do not hide the failure behind a completed claim.

After completion or cost review, use `scripts/render_execution_cost_tree.py`. Default
to `standard`: show every real Mission / Task / SubTask / Step and declared edge, with
status, actual elapsed, cumulative LLM-call, script, tool, wait, Token, and result slots.
The primary Standard/Audit layout is a portrait SVG execution timeline: rows follow first-observed
chronology, the left rail prints observed relative time, every card has a shared-scale
range bar, and the declared hierarchy is overlaid as tree edges. Exact lifecycle
coverage makes those offsets Mission-relative; partial coverage visibly uses the
observed trace window. Vertical row spacing is ordinal and must never be interpreted as
duration.
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
