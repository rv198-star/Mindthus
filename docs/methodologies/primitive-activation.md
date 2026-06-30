# Primitive Activation / 原语唤起机制

## 这是什么

Primitive Activation 是认知原语的轻量工程承载方式。

它解决的不是“再造一个方法”，而是让横切原语在少数关键动作前被明确叫醒：
选方法前、交付 / 冻结前、同路径继续前。

一句话：

> 原语唤起只提醒 agent 该想什么，不替 agent 判断想得对不对。

这比纯文档提醒更硬一点，因为它给原语稳定 `id`、触发事件和行动影响；
但它不是完整 AOP，不做全生命周期注入，不做通用 hook engine，也不替代
`SELA`、`MPG`、`3L5S`、`EDSP`、`WAE`、`TVG` 或 `tplan` 的主判断。

## 为什么不是纯文档

`shared-primitives.md` 已经能说明认知原语是什么，但它仍然依赖 agent 记得读、记得用。
当任务复杂、上下文长、产物看似已经完成时，agent 容易忘记那些横切刹车。

Primitive Activation 的目标是把“记得用”变成一个可执行动作：

```bash
python3 scripts/primitives/check.py --event before-freeze --method tvg
```

脚本输出该事件应唤起哪些原语、agent 需要自查哪些点，并明确：
`script_verdict: shape_only`，`agentic_judgment_required: true`。

For primitives that need a visible audit artifact, activation can hand off to a
shape validator. Whole Elephant Protocol / 全象流程 uses:

```bash
python3 scripts/primitives/validate_whole_elephant.py audit.json
```

That validator only checks whether the required audit fields exist. It does not
decide whether the final judgment is true.

## 为什么不是完整 AOP

完整 AOP 会要求定义大量 join point、生命周期阶段和注入规则。Mindthus 当前没有这个诉求。

当前只保留三个轻量事件：

| Event | 什么时候用 | 唤起目标 |
|---|---|---|
| `before-route` | 选择 Mindthus 方法前 | 避免简单任务被方法化，避免缺事实时用方法补洞。 |
| `before-freeze` | 交付、冻结、转交或停止前 | 避免“看起来完成”但目标漂移、证据不足、误用信号未处理。 |
| `before-continue` | 同路径继续或长任务继续前 | 避免惯性续跑、局部修补螺旋和无证据增量的继续。 |

这三个事件是提醒点，不是强制流程。低风险、明确、机械可验证的小任务可以不跑脚本。

## Primitive Shape

每个 primitive 至少要有稳定形状：

```yaml
id: gate_probes
name: Gate Probes / 冻结前定位自省
short_rule: "交付、冻结、继续、转交或停止前，确认当前位置和目标。"
trigger:
  - before-freeze
  - before-continue
action_effect:
  - freeze
  - return-remediate
  - block
  - stop
  - ask-user-authority
not_a:
  - standalone-method
  - semantic-judge
  - evidence-substitute
  - gate-replacement
owner: shared-primitives
```

这些字段让 AGENTS、skill、脚本、trace 和后续文档能引用同一个原语，而不是复制一段自然语言。

## 脚本边界

`scripts/primitives/check.py` 只做四件事：

1. 根据 `event` 找到应唤起的 primitives。
2. 根据 `method` 应用少量条件性唤起，例如 `tplan` 的 continuation authorization。
3. 返回 required agent checks。
4. 校验 manifest 形状，防止原语记录坏掉。

它不能：

- 判断是否可以 freeze。
- 判断 evidence 是否真实充分。
- 判断方法输出是否正确。
- 判断审美、业务、策略或用户价值是否成功。
- 替代用户授权、TVG exit gate 或 tplan continuation authorization。

`scripts/primitives/validate_whole_elephant.py` is stricter but still shape-only:
it can block a formal answer when the Whole Elephant audit JSON is missing
`object_hierarchy`, `whole_object`, `local_success_points`, `strategy_choice`,
`definition_owner`, `result_controller`, or `decision_consequence`; it still
cannot decide whether those fields are substantively correct.

脚本成功只表示：

> 该事件的原语唤起形状可用；agentic judgment 仍然必需。

## 与 shared-primitives.md 的关系

`shared-primitives.md` 仍然是认知原语的索引和短正本。
Primitive Activation 负责运行时唤起形态。

当前不急着把每个 primitive 拆成独立文件。更合理的边界是：

- `shared-primitives.md` 保留索引、短定义和关键边界。
- `primitive-activation.md` 记录结构化形态和脚本边界。
- 如果某个 primitive 的正文超过约 60 行，或需要独立模板 / schema / casebook，再拆到
  `docs/methodologies/primitives/<id>.md`。

这样避免 `shared-primitives.md` 变成公共抽屉，也避免为了工程化而过早拆散文档。

## 与现有方法的关系

- `using-mindthus` 可以在路由前使用 `before-route`。
- `TVG` 可以在 freeze 或继续下一轮前使用 `before-freeze` / `before-continue`。
- `tplan` 可以在同路径继续前使用 `before-continue`，但 continuation authorization 仍由
  tplan 自己判断和记录。
- `WAE` 的边界仍然成立：脚本只控制 shape 和提醒，不控制 truth。

## 导航

- 返回 [shared primitives](shared-primitives.md)
- 查看 [Using Mindthus skill](../../skills/using-mindthus/SKILL.md)
- 查看 [tplan](tplan.md)
- 查看 [TVG](tvg.md)
