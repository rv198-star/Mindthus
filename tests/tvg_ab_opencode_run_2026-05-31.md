# TVG Issue #10 OpenCode Version A/B Packet - 2026-05-31

- `runner: opencode`
- `model: opencode/deepseek-v4-flash-free`
- `old_tvg_commit`: `adc07e8`
- `new_tvg_commit`: `c684470`
- `isolated_project_skills`: each run used a separate temporary project with its own `.opencode/skills/tvg`
- `same_input_prompts`: yes
- `review_mode`: external AI review by the same OpenCode model route

Note: `72live/deepseek-v4-flash` was attempted but hung on a minimal prompt, so the completed run used the available DeepSeek V4 Flash route `opencode/deepseek-v4-flash-free`.

## Setup

Old TVG skill files were installed into:

```text
/tmp/tvg-opencode-ab/old/.opencode/skills/tvg/
```

New TVG skill files were installed into:

```text
/tmp/tvg-opencode-ab/new/.opencode/skills/tvg/
```

OpenCode logs confirmed that each generation used the project-level `tvg` skill and read `.opencode/skills/tvg/resources/methodology.md`.

## Scenario O1: Coverage-Rich Product Review

- `input`: "We should add team dashboards because teams need visibility."
- `known_context`: no user segment, substitute workflow, adoption risk, or failure path is named.
- `target_style`: coverage-rich product review note

### Old TVG Output

- `old_tvg_output`:

```text
Team Dashboards - Product Design Rationale

Target users (unvalidated hypothesis): team leads needing cross-member progress without sync overhead; individual contributors needing context on how their work affects team goals; stakeholders wanting periodic summary without dedicated meetings.

Specific visibility gap: current status gathering is synchronous and scattered across tools.

Why dashboards vs alternatives:
- Periodic reports: lower build cost, but stale immediately and no drill-down.
- Alerts/notifications: good for exceptions, bad for ambient awareness.
- Dashboards: real-time, configurable, single pane, but requires integration investment and data hygiene.

Adoption risk and failure paths:
- Data freshness lags.
- Per-team config too heavy.
- Everything surfaced creates noise.
- Unclear whether value is retention or workflow efficiency.

Decision needed from review:
1. Is this visibility gap painful enough?
2. Build vs integrate?
3. What validation is needed before committing?

Review-bound items: user segment priority is unvalidated; data hygiene state is unknown; retention vs efficiency framing is unresolved.
```

### New TVG Output

- `new_tvg_output`:

```text
团队仪表盘 - 价值主张

目标用户与粒度差异：
- 技术负责人 / 工程经理：关注团队级趋势与异常。
- 产品经理：关注跨团队汇总视图。
- 资深 IC：关注任务级可见性。
- 高层：关注跨团队趋势，而非单团队细节。

单一视图无法同时服务这些群体。

为什么不是其他方式：
- Slack 日报 / 周邮件：成本低，但无趋势追踪、无下钻、无历史积累。
- 分析师按需取数：灵活但延迟高、非自助。
- 仪表盘：以较高建设成本换取持续低摩擦的自助访问。

失败路径：
- 指标过载。
- 数据管线延迟。
- 易度量替代重要。
- 维护衰减。
- 组织错配。

已知与假设的边界：
- 已知：6 人以上团队在状态同步中定期损失时间，但需补充来源。
- 假设：仪表盘可减少此开销。
- 假设：数据管线可靠。
- 待评审：MVP 上线后两周测量实际使用率。

产品评审需要决策：优先用户群体、自建还是现有工具、MVP 最低指标集、成功标准。
```

### External AI Review

- `external_ai_review`: old TVG wins
- `review_preference`: old
- `review_rationale`: For a coverage-rich product review note, the old output is more structured and easier to review point by point. The new output is also rich, but the old output exposes review-bound items more explicitly.

## Scenario O2: Insight-Dense Executive Claim

- `input`: "AI review will replace human review because it is faster."
- `known_context`: speed matters, but release risk, accountability, and evidence quality still matter.
- `target_style`: insight-dense executive summary

### Old TVG Output

- `old_tvg_output`:

```text
AI review replaces human review only where speed's marginal value exceeds the combined cost of release risk, accountability diffusion, and evidence degradation -- a threshold most domains have not yet crossed.
```

### New TVG Output

- `new_tvg_output`:

```text
AI review replaces human review -- but only where speed matters more than the cost of error.
```

### External AI Review

- `external_ai_review`: new TVG wins
- `review_preference`: new
- `review_rationale`: For insight-dense delivery, the new output compresses the trade-off into a cleaner executive sentence. The old output is richer and more explicit, but less dense as an executive summary.

## Scenario O3: Balanced Operational Rule

- `input`: "Automate review when checks are repetitive and clear. Keep humans for uncertain judgment."
- `known_context`: the core constraint exists but is loose; output should become an executable decision rule.
- `target_style`: balanced

### Old TVG Output

- `old_tvg_output`:

```text
Automate review when checks are repetitive, outcomes deterministic, and pass/fail criteria explicit. Keep humans for uncertain judgment.
```

### New TVG Output

- `new_tvg_output`:

```text
Automate any review check whose pass/fail condition is specifiable as a deterministic rule.
Route to human judgment when evaluation requires context, interpretation, or trade-offs.
```

### External AI Review

- `external_ai_review`: new TVG wins
- `review_preference`: new
- `review_rationale`: The new output converts both branches into operational criteria. The old output improves "clear" but leaves "uncertain judgment" mostly unchanged.

## Overall External Review

The external reviewer preferred:

- Old TVG: 1 scenario
- New TVG: 2 scenarios
- Mixed: 0 scenarios

This does not support the claim that the new TVG is always better than the old TVG. It supports a narrower claim:

- Old TVG can still be stronger for coverage-rich review artifacts that benefit from explicit structure and review-bound items.
- New TVG is stronger for insight-dense compression and balanced operational rule refinement.
- The strongest future TVG direction is not to discard old depth expansion, but to keep useful old thickness while adding state routing, value density, and output-profile discipline.
