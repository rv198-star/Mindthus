# Primitive Activation / 原语唤起机制

## 这是什么

Primitive Activation 是认知原语和运行时检查的轻量工程承载方式。

它解决的不是“再造一个方法”，而是让横切原语在少数关键动作前被明确注入：
选方法前、交付 / 冻结前、同路径继续前。

一句话：

> 原语唤起只提醒 agent 该想什么，不替 agent 判断想得对不对。

这比纯文档提醒更硬一点，因为它给原语稳定 `id`、触发事件、行动影响和可复制的
agent context 注入块；
但它不是完整 AOP，不做全生命周期注入，不做通用 hook engine，也不替代
`SELA`、`MPG`、`3L5S`、`EDSP`、`WAE`、`TVG` 或 `tplan` 的主判断。

## 为什么不是纯文档

`shared-primitives.md` 和 `docs/methodologies/primitives/` 已经能说明 5 个认知原语是什么，
但它们仍然依赖 agent 记得读、记得用。
当任务复杂、上下文长、产物看似已经完成时，agent 容易忘记那些横切刹车。

Primitive Activation 的目标是把“记得用”变成一个可执行的上下文注入动作：

```bash
python3 scripts/primitives/check.py --event before-freeze --method tvg --agent-context
```

脚本输出一个 `BEGIN MINDTHUS PRIMITIVE CONTEXT` 块。上游 agent / wrapper 可以把这个块
插入到关键动作前的上下文里，让 agent 在作答前看到应唤起哪些原语、需要自查哪些点，并明确：
`script_verdict: shape_only`，`agentic_judgment_required: true`。

这就是当前的“轻量注入”：注入提醒层，不注入结论；注入位置很少，不做全生命周期拦截。

## 为什么不是完整 AOP

完整 AOP 会要求定义大量 join point、生命周期阶段和注入规则。Mindthus 当前没有这个诉求。

当前只保留三个轻量事件。事件只定义“什么时候可能要注入”，不直接决定所有 skill
该注入什么：

| Event | 什么时候用 | 唤起目标 |
|---|---|---|
| `before-route` | 选择 Mindthus 方法前 | 避免简单任务被方法化；先确认当前信息面是否足够，避免缺事实时用方法补洞。 |
| `before-freeze` | 交付、冻结、转交或停止前 | 避免“看起来完成”但目标漂移、证据不足、误用信号未处理。 |
| `before-continue` | 同路径继续或长任务继续前 | 避免惯性续跑、局部修补螺旋和无证据增量的继续。 |

这三个事件是轻量注入点，不是强制流程。低风险、明确、机械可验证的小任务可以不跑脚本。

## Skill-Specific Intervention / 逐 Skill 介入策略

原语注入不能只靠通用事件。真正的策略写在 `scripts/primitives/manifest.json` 的
`method_events` 里：每个 skill 按自己的工作流声明 `intervention_points`、
`active_primitives` 和 `required_agent_checks`。

通用事件只做 fallback；只要 `method_events[method][event]` 存在，脚本就使用该 skill
专属策略。

| Skill | 典型介入点 | 主要注入原语 / 检查 |
|---|---|---|
| `using-mindthus` | 前置校准、介入边界、信息面充分性检查、方法仲裁、路由答案冻结 | `evidence_claim_ceiling`, `no_abstract_jargon_wall` + 最小充分介入 / context sufficiency 检查 |
| `3l5s` | 问题定义冻结、BTGSB 拆解冻结、执行反馈 loopback | `evidence_claim_ceiling`, `anti_spiral` + freeze / smell 检查 |
| `edsp` | EDSP 输出冻结、场景投影入口、坐标系重建 | `evidence_claim_ceiling`, `perspective_pressure`, `no_abstract_jargon_wall` |
| `sela` | 战略方向冻结、Timing Check、方向复核 | `evidence_claim_ceiling`, `perspective_pressure`, `no_abstract_jargon_wall` |
| `mpg` | 主线承载方案冻结、触发条件冻结、路径复核 | `evidence_claim_ceiling`, `approximate_quantified_mapping`, `anti_spiral` |
| `wae` | 控制边界冻结、脚本 / schema 边界、agentic loop 继续 | `evidence_claim_ceiling`, `anti_spiral`, `no_abstract_jargon_wall` |
| `tvg` | TVG exit gate、产物冻结、下一轮 value-gain loop | `evidence_claim_ceiling`, `anti_spiral`, `no_abstract_jargon_wall` |
| `tplan` | Mission 交接冻结、decision packet 冻结、同路径继续 | `evidence_claim_ceiling`, `anti_spiral` + continuation authorization 检查 |

这张表只是人读索引；运行时以 `manifest.json` 为准。
详细人工审查见 [Primitive Activation Design Review](primitive-activation-review.md)。

## Primitive Shape

每个认知原语至少要有稳定形状：

```yaml
id: evidence_claim_ceiling
name: Evidence / Claim Ceiling / 证据上限
short_rule: "结论强度不能超过证据；缺关键事实时降级或阻断。"
trigger:
  - before-route
  - before-freeze
  - before-continue
action_effect:
  - downgrade-claim
  - gather-evidence
  - block
  - stop
not_a:
  - fact-generator
  - evidence-substitute
owner: primitives/evidence-claim-ceiling
```

这些字段让 AGENTS、skill、脚本、trace 和后续文档能引用同一个原语，而不是复制一段自然语言。

## 脚本边界

`scripts/primitives/check.py` 只做六件事：

1. 根据 `method + event` 读取 skill 专属介入策略。
2. 没有专属策略时，根据通用 `event` 找到 fallback primitives。
3. 返回 intervention points 和 required agent checks。
4. 可输出 `--agent-context` 注入块，供 agent / wrapper 放入关键动作前上下文。
5. 校验 manifest 形状，防止原语记录坏掉。
6. 明确脚本输出仍然只是 shape-only reminder，不是判断结果。

它不能：

- 判断是否可以 freeze。
- 判断 evidence 是否真实充分。
- 判断方法输出是否正确。
- 判断审美、业务、策略或用户价值是否成功。
- 替代用户授权、TVG exit gate 或 tplan continuation authorization。

脚本成功只表示：

> 该事件的原语注入形状可用；agentic judgment 仍然必需。

## 与 shared-primitives.md 的关系

`shared-primitives.md` 是 5 个认知原语的索引：稳定名字、primary owner、短规则和导航。
每个原语的语义定义放在 `docs/methodologies/primitives/<id>.md`。
Primitive Activation 负责运行时 shape：事件、逐 skill 介入点、active primitives 和
required agent checks。`Gate Probes`、`Failure Smells`、`Continuation Authorization`
这类运行时检查只放在 checks / intervention points，不进入认知原语索引。

三者不要互相覆盖：

- `shared-primitives.md` 不写长定义，避免变成公共抽屉。
- `docs/methodologies/primitives/` 不替各 skill 决定何时使用，只说明原语自身边界。
- `scripts/primitives/manifest.json` 只记录和校验可注入形状，不判断原语是否用得正确。

## 与现有方法的关系

- `using-mindthus` 可以在路由前使用 `before-route`。
- `TVG` 可以在 freeze 或继续下一轮前使用 `before-freeze` / `before-continue`。
- `tplan` 可以在同路径继续前使用 `before-continue`，但 continuation authorization 仍由
  tplan 自己判断和记录。
- `WAE` 的边界仍然成立：脚本只控制 shape 和注入提醒层，不控制 truth。

## 导航

- 返回 [shared primitives](shared-primitives.md)
- 查看 [Primitive Activation Design Review](primitive-activation-review.md)
- 查看 [Using Mindthus skill](../../skills/using-mindthus/SKILL.md)
- 查看 [tplan](tplan.md)
- 查看 [TVG](tvg.md)
