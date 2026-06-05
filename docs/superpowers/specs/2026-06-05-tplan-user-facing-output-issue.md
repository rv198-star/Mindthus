# Issue Draft: Add Human-Readable tplan User Output

## Title

Hide internal tplan IDs from ordinary user-facing output

## Context

`tplan` needs stable internal identifiers such as `T1`, `S2`, and `E3` for task-tree
state, evidence links, validation, recovery, and audit. These IDs are useful inside the
runtime, but they create a poor user experience when shown as the primary way of
communicating progress.

Users do not naturally understand `T1`, `T2`, `E1`, or `E2`. When these IDs appear in
ordinary status updates, the output feels like an internal debug report instead of a
clear human-facing explanation.

This issue should add a presentation layer that translates runtime state into natural,
mission-relative language while preserving the internal ID system underneath.

## Core Principle

Internal IDs are for runtime stability. User-facing output should lead with meaning.

The user should see:

```text
当前在推进什么
已经确认了什么
卡在哪里
下一步为什么合理
需要用户决定什么
```

The runtime may still store:

```text
active_node: T2.S1
evidence_links: E4, E7
```

But ordinary output should render that as:

```text
当前在处理：梳理 tplan 的轻量化运行策略。
已经确认：轻量化只能减少记录密度，不能降低关键风险触发。
下一步：把这个原则写进技能说明，避免后续实现时误删控制能力。
```

## Target

Create guidance for a `tplan` user-facing output adapter.

The adapter should:

- translate node IDs into task titles or natural action descriptions
- translate evidence IDs into human-readable evidence summaries
- translate decision packets into concise rationale and next-action language
- keep internal IDs available only when needed for debug, audit, strict review, or
  explicit user request
- preserve evidence honesty without exposing raw runtime references as the main content

## Proposed Direction

### 1. Default User Output Shape

Ordinary `tplan` updates should prefer a compact natural-language structure:

```text
当前目标：
...

当前进展：
...

已确认：
...

下一步：
...
```

Use only the fields that matter for the moment. Do not force every update into a fixed
template when a shorter answer is clearer.

### 2. Evidence Translation

Evidence IDs should be rendered as meaningful claims:

- `acceptance_passed`: what passed and where it was observed
- `blocker`: what prevents safe continuation
- `user_feedback`: what the user corrected, rejected, or confirmed
- `decision`: what choice was made and why it matters
- `key_finding`: what was learned that changes the next action

The output can omit raw `E1` labels unless the user is inspecting internals.

### 3. Node Translation

Task IDs should be rendered as task names, active work descriptions, or parent-chain
summaries.

For example:

```text
Internal: active_node = T2.S1
User-facing: 当前在处理“整理 tplan 自适应运行策略”的第一段落。
```

### 4. Debug And Audit Mode

Raw IDs may appear when:

- the user asks for internal state
- strict audit requires stable references
- a stop report needs exact recovery anchors
- a script failure references a specific invalid node or evidence item

Even then, IDs should be secondary to human-readable descriptions.

### 5. Stop Reports

Stop reports should remain compact Chinese handoff packets, but should not lead with raw
task/evidence IDs. IDs may appear in a final "internal recovery references" section when
needed.

## Non-Goals

- Do not remove internal IDs from `mission.json`, `evidence.jsonl`, decision packets, or
  script validation.
- Do not make user-facing summaries less evidence-constrained.
- Do not replace evidence links with vague reassuring language.
- Do not require a long template for every ordinary status update.
- Do not hide IDs when the user explicitly asks for runtime internals.

## Acceptance Criteria

- `tplan` docs distinguish internal runtime references from user-facing language.
- Ordinary user-facing status updates do not lead with `T1`, `S2`, `E3`, or similar IDs.
- Evidence references are translated into observable, human-readable summaries.
- Task references are translated into task titles, active work descriptions, or parent-chain
  summaries.
- Debug/audit/strict contexts may still expose raw IDs, but only as secondary references.
- Stop report guidance avoids raw IDs as the main communication layer.
- Tests or examples show the same runtime packet rendered once as internal state and once
  as user-facing output.
