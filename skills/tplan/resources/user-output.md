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
