---
name: sra
description: "Use when multiple valid actions or bundles compete for the same scarce resource. Default to Lite for one bounded tranche; use Full for bundles, multiple constrained resources, fixed thresholds, or major or irreversible commitments."
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

SRA owns allocation among sufficiently judgeable candidates; neighboring methods retain
problem definition, structural truth, direction, carrier strategy, control, artifact
quality, and runtime state. Use the smallest reasoning depth whose cost is lower than
the plausible loss from a wrong allocation.

## Mainline / 主路径

### Entry Outcome And Analysis-Cost Gate

Choose one outcome before analysis:

- `direct`: one obvious low-risk action dominates, resources are independent, or trying
  costs less than analyzing.
- `lite`: authorize one bounded action, tranche, or checkpoint.
- `full`: bundles, multi-resource constraints, fixed thresholds, direction changes, or
  major/irreversible commitments control the decision.
- `blocked`: a load-bearing target, evidence, authority, candidate, or resource boundary
  is incomplete.

`auto` starts from Lite and expands only when a named Full condition is load-bearing.
`direct` is an intervention outcome, not a third reasoning mode.

### Allocation Frame

Name only `parent_objective`, `target_threshold`, `time_window`, `risk_floor`,
`decision_owner`, `contested_resource`, and `evidence_ceiling`. Resource pressure keeps
the target visible; changing it is a separate authorized decision.

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

Use the minimum comparable candidate card in `resources/methodology.md`; splitting one
candidate into more rows does not increase its allocation claim.

### Resource Contraction And Replenishment

Contraction finds the current floor while target and risk stay fixed. Replenishment
selects the next meaningful tranche by bottleneck, evidence, window, optionality, and
objective gain. When removal and addition orders differ, preserve dependency,
complementarity, fixed-threshold, switching-cost, or uncertainty explanations; return a
partial or conditional order rather than a false total ranking.

### Human-Readable First

Lead with what receives the resource now, what is displaced, and what reopens the
decision. Keep internal fields for audit, validation, or handoff.

## Guardrails / 从属补漏

### Shared Core Across Lite And Full

Lite reduces analysis width, not method identity: expose the current floor from one
bounded contraction and the next tranche from one replenishment comparison. Full expands
both across credible bundles. Before contraction, a posture is only a target-reaching
hypothesis; the first realistic break point establishes the floor.

### Evidence-Bounded Necessity

A `current minimum sufficient bundle` is bounded by evidence, assumptions, window, and
risk floor. Record why each load-bearing part is necessary and what overturns it.
Backup, rollback, review, and redundancy may be essential; substitutes stay separate.
Return `infeasible` when no bundle reaches the unchanged target and risk floor.

### Resource Vector And Meaningful Tranche

Keep time, money, specialist capacity, labor, attention, exposure, and opportunity
windows as distinct channels. Identify real contention, parallel work, and any fixed
threshold. A meaningful tranche is the smallest complete experiment, engineer-day,
review cycle, deliverable, or other block producing an observable result.

### Switching Cost, Sunk Cost, And Reserve

Compare future consequences: `sunk_cost` never justifies continuation;
`switching_cost` is future change cost; `reusable_asset` retains future value;
`remaining_cost` is new completion cost; `reserve` needs a reason, release trigger, and
review time.

### Stop And Evidence Discipline

Lite stops after one bounded allocation and reranking trigger. Full stops when the
bundle is stable across adjacent realistic pressure, the first tranche is clear, and
another round has no action-changing value hypothesis. Scripts validate shape only;
they do not compute priority, ROI, necessity, or allocation correctness.

## Boundaries / 边界

- Use `3l5s` for candidate definition/decomposition; SRA asks only for minimum
  comparability.
- Use `edsp` for unstable structure, `sela` for long-term efficiency direction, and
  `mpg` for one selected mainline's carrier/path posture.
- Use `wae` for agentic controller mismatch and `tvg` for value gain inside one bounded
  artifact.
- Anti-Spiral supplies the brake and allowed actions; SRA allocates released resources
  without recursive handoff.
- `tplan` owns Mission state, Pulse arbitration, identity, continuation, authority,
  recovery, and mutation; SRA supplies cross-candidate allocation judgment.
- Stay direct for one known blocker, independent resources, or a cheaper reversible
  trial.

## Runtime Support / 支撑材料

- `resources/methodology.md` — complete Lite/Full method and ownership details.
- `resources/fidelity-contract.md` — first-release fidelity and claim ceiling.
- `templates/fidelity-output.json` — passing Lite audit example.
- `scripts/validate_sra_output.py` — shape-only validator.
- `../../docs/methodologies/sra.md` — public explanation.
- `../../tests/sra_pressure_tests.md` — positive, boundary, and adversarial cases.
