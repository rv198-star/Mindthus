---
name: sra
description: "Use when multiple valid problems, tasks, branches, projects, or continuation choices compete for the same scarce resource, or current work competes with switching, maintaining, deferring, stopping, or reserving it. Default to Lite for one bounded tranche; expand to Full for bundles, major commitments, multiple constrained resources, direction-changing uncertainty, fixed thresholds, or irreversible exposure."
---

# SRA / Scarce Resource Allocation / 稀缺资源优先分配

## Core Claim / 核心判断

SRA decides which valid work receives a shared scarce resource now.

> 先排除不可行，再保护达标必要项；方向、依赖、瓶颈和窗口决定先后；
> 组合价值决定本轮投哪套；边际价值决定下一份资源投哪里。

Every applicable SRA judgment uses the same contraction–replenishment core. Lite
compresses it into one `micro-contraction` and one `micro-replenishment`; Full expands
the same logic across bundles, resource channels, pressure scenarios, and decision
lifetimes.

SRA owns allocation among sufficiently judgeable candidates. It does not own problem
definition, structural truth, long-term trend, carrier strategy, agentic control,
artifact quality, or durable runtime state.

The method is itself resource-constrained: use the smallest reasoning depth whose cost
is lower than the plausible loss from a wrong allocation.

## Mainline / 主路径

### Entry Outcome And Analysis-Cost Gate

Choose one outcome before analysis:

- `direct`: one obvious low-risk action dominates, resources are not actually
  contested, or trying costs less than analyzing.
- `lite`: authorize one bounded action, meaningful tranche, or named checkpoint.
- `full`: bundles, major or irreversible commitment, multiple constrained resource
  pools, direction-changing uncertainty, fixed thresholds, or material path dependency
  control the decision.
- `blocked`: target, evidence, authority, candidate readiness, or resource boundaries
  are too incomplete to allocate responsibly.

`auto` starts from Lite and expands only when a named Full condition is load-bearing.
`direct` is an intervention outcome, not a third reasoning mode.

### Allocation Frame

Name only what the allocation needs:

- `parent_objective`
- `target_threshold`
- `time_window`
- `risk_floor`
- `decision_owner`
- `contested_resource`
- `evidence_ceiling`

Resource pressure keeps the target threshold visible. Changing the target is a separate
authorized decision.

### Candidate Horizon Probe

Before choosing, scan beyond the active task:

1. current path;
2. hard gate, blocker, or threshold-essential predecessor;
3. direction-changing unknown, irreversible risk, or closing opportunity window;
4. strongest feasible alternative contribution to the same objective;
5. maintain, reserve, defer, and stop postures.

Lite normally keeps two to four actionable candidates. Ask only for missing fields that
can change the allocation. An incomparable credible candidate causes Full escalation or
`blocked`, not an invented priority.

### Priority Order

Apply this order before ROI-style comparison:

1. `hard_gate`
2. `feasible_bundle`
3. `threshold_essential`
4. `direction_or_bottleneck`
5. `risk_adjusted_bundle_value`
6. `marginal_tranche_value`
7. `reserve`

A necessary item receives enough resource to satisfy the current target and evidence
threshold. Further improvement competes as `value_expanding` work.

### Lite / 快速优先级决策

Lite asks where the next meaningful resource tranche should go.

1. Lock the minimal Allocation Frame.
2. Run the Candidate Horizon Probe.
3. Identify hard gates, threshold-essential work, and the strongest alternative.
4. Run one `micro-contraction`: cap, remove, or downgrade the current allocation until
   the next reduction would threaten the unchanged target threshold or risk floor.
5. Run one `micro-replenishment`: from that current floor, compare the next meaningful
   tranche across the surviving current path, strongest alternative, and reserve.
6. Separate switching cost from sunk cost.
7. Choose `continue`, `switch`, `maintain`, `defer`, `stop`, or `reserve`.
8. Set an investment ceiling, authorization horizon, displaced-work decision, and
   reranking trigger.

A Lite answer without both a contraction result and a replenishment result is ordinary
priority discussion, not a complete SRA judgment.

Lite authorizes only `one_action`, `one_tranche`, or `until_named_checkpoint`:

```text
当前决定：continue | switch | maintain | defer | stop | reserve
为什么现在：与目标门槛直接相关的理由
当前底座：微型收缩后仍能守住目标与风险底线的最低投入
下一投入批次：从当前底座出发，微型回补选择的最小资源块
当前投入上限：本次最多投入多少
授权边界：one_action | one_tranche | until_named_checkpoint
延后或停止：被挤出的工作
重排触发：什么变化会重新打开判断
```

Escalate to Full when direction can change, multiple feasible bundles exist, commitment
is major or hard to reverse, fixed threshold or bundle effects control value, resource
channels disagree, switching cost is material, a credible alternative is incomparable,
or the decision authorizes more than one tranche or checkpoint.

### Full / 完整资源分配

1. Lock objective, threshold, window, risk floor, authority, and evidence ceiling.
2. Identify contested resource pools and the dominant constraint.
3. Build minimum comparable candidate cards.
4. Route direction-changing unknowns only to the point needed for current action.
5. Construct an evidence-bounded `current minimum sufficient bundle` or alternatives.
6. Eliminate `infeasible` and dominated bundles.
7. Run resource contraction while preserving target and risk floor.
8. Run replenishment from the lowest feasible bundle by meaningful tranches.
9. Select a risk-adjusted allocation and reserve.
10. State main allocation, support, maintenance, defer, stop, next tranche,
    authorization boundary, decision lifetime, and reranking triggers.

Minimum candidate card:

```text
candidate_id
objective_contribution
resource_demand_vector
dependency_or_bundle_role
evidence_state
delay_cost_or_opportunity_window
irreversibility_or_downside
```

Splitting one candidate into more rows does not increase its allocation claim.

### Resource Contraction And Replenishment

Contraction finds what remains indispensable, substitutable, parallelizable, degradable,
or merely value-expanding while target and risk floor stay fixed.

Replenishment asks which next meaningful tranche removes the bottleneck, unlocks
options, produces decision-relevant evidence, protects a closing window, or creates the
largest objective-relevant gain.

When removal and addition orders differ, preserve dependency, complementarity, fixed
threshold, switching-cost, or uncertainty explanations. Return a partial or conditional
order rather than a false total ranking.

### Human-Readable First

Lead with what receives the resource now, what is displaced, and what reopens the
decision. Keep internal fields for audit, validation, or handoff.

## Guardrails / 从属补漏

### Shared Core Across Lite And Full

Lite reduces analysis width, not method identity. It must still expose the current
floor found by one bounded contraction and the next tranche chosen by one replenishment
comparison. Full repeats and expands those moves across credible bundle hypotheses.

Before contraction, a bundle or current posture is only a target-reaching hypothesis.
Call it a current floor only after the contraction test identifies the first realistic
break point.

### Evidence-Bounded Necessity

A `current minimum sufficient bundle` is sufficient only under current evidence,
explicit assumptions, the declared window, and the risk floor. Record why each
load-bearing part is necessary now and what makes that claim false or obsolete.

Backup, rollback, review, and redundancy may be threshold-essential. Keep substitutes
as separate bundles. When no bundle reaches the unchanged target and risk floor, return
`infeasible` rather than lowering the target silently.

### Resource Vector And Meaningful Tranche

Keep time, money, specialist capacity, general labor, management attention, risk or
exposure budget, and opportunity window as distinct channels. Identify real contention,
parallel work, and any fixed threshold.

The next unit is a decision-relevant tranche: a complete experiment, engineer-day,
review cycle, deliverable package, or the smallest block producing an observable result.

### Switching Cost, Sunk Cost, And Reserve

Compare future consequences from the current state:

- `sunk_cost` does not justify continuation;
- `switching_cost` is the future cost of changing paths;
- `reusable_asset` retains future value;
- `remaining_cost` is the new resource needed to finish;
- `reserve` has a reason, release trigger, and review time.

### Stop And Evidence Discipline

Lite stops after one bounded allocation and reranking trigger. Full stops when the
selected bundle is stable across adjacent realistic pressure scenarios, the first
tranche is clear, remaining uncertainty cannot change the current action, and another
round has no named positive-value hypothesis.

Scripts validate fields, enums, references, and empty evidence surfaces. They do not
compute semantic priority, ROI, necessity, or allocation correctness. A passing report
is not semantic approval.

## Boundaries / 边界

- Use `3l5s` when the problem or candidate needs definition or decomposition. SRA asks
  only for the minimum comparable candidate card.
- Use `edsp` for an unstable proposition, false binary, or structural coordinate system.
- Use `sela` for long-term system-efficiency versus local-advantage direction pressure.
- Use `mpg` when one selected mainline needs carrier, exposure, timing, optionality, and
  path posture under volatility.
- Use `wae` only for an agentic-system controller mismatch.
- Use `tvg` for value gain inside one bounded artifact; use SRA only when that artifact
  competes with external work for the same resource.
- Anti-Spiral supplies a brake and allowed action set; SRA decides where released
  resources go. Do not create recursive handoff.
- `tplan` owns Mission state, Pulse arbitration, Mission identity, continuation,
  authority, recovery, and task mutation. SRA supplies allocation judgment only when
  real candidates contest a common resource.
- Stay direct for one known blocker, independent parallel resources, or a reversible
  choice cheaper to try than analyze.

## Runtime Support / 支撑材料

- `resources/methodology.md` — complete Lite/Full method and ownership details.
- `resources/fidelity-contract.md` — first-release fidelity and claim ceiling.
- `templates/fidelity-output.json` — passing Lite audit example.
- `scripts/validate_sra_output.py` — shape-only validator.
- `../../docs/methodologies/sra.md` — public explanation.
- `../../tests/sra_pressure_tests.md` — positive, boundary, and adversarial cases.
