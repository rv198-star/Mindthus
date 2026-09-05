# TPlan Case Summary

## Focus

- focus: `acceptance`
- selection reason: The read-only Pulse view selected an acceptance-related signal.

## Mission

- title: Issue 3 PPTX 首次成稿质量与成本修复
- objective: 按 VQ-000 至 VQ-014 工单依赖顺序完成 Slidethus 首次成稿视觉质量与成本修复，使 PPTX 生成更快、逻辑更清晰、视觉效果更好，并通过规定的测试、独立审计与真实 PowerPoint holdout 验收。
- status: active
- human_in_loop: 0
- risk_tolerance: 25
- resource_sufficiency: 60

## Active Path

- active task: none
- active task status: none
- parent path: none

## Read-Only Pulse View

- signals: ['evidence:acceptance_failed']
- next gate: review_blocker
- gate owner: agentic_review
- rationale: Latest bounded review signal is evidence event acceptance_failed.

## Runtime Provenance

- status: exact
- severity: ok
- compatible: True
- diagnostic codes: []

## Selection Boundary

Only a bounded active-path summary and up to 5 brief evidence events
are included. The full Mission, task tree, evidence stream, step logs, execution trace,
and telemetry stream are excluded.
