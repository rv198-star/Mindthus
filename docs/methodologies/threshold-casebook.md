# Mindthus Threshold Casebook / 边界案例集

## 这是什么

Threshold Casebook records cases where Mindthus is easy to misuse.

它不收集“明显应该用某个方法”的例子，而是收集压线场景：看起来可以开方法，
但更好的答案可能是直接执行、降级结论、补证据、转交判断，或者停止。

短句理解：

> 边界案例集不是教 agent 多用 Mindthus，而是教它在摇摆处用对或不用。

## 解决什么问题

Mindthus 的风险不是方法不够多，而是方法看起来都能解释当前问题。这样会产生
三种退化：

- 简单任务被过度方法化；
- 缺证据的问题被包装成更漂亮的判断；
- 局部修补被误认为持续进展。

Casebook 用具体案例固定这些边界：ordinary execution is enough 时不要开方法；
right answer is a stop, downgrade, or handoff 时不要继续推理。

## 核心判断

一个好案例必须能说明“为什么不用某个看似合理的方法”。

最有价值的案例通常满足至少一个条件：

- 两个方法都看似合理；
- 方法能让答案更像答案，但不能让结论更可靠；
- 继续推进会隐藏缺失证据；
- 停止、降级或转交比继续生成更正确。

## 怎么用

在设计、修改或验收 Mindthus skill 时，用这些案例做压力检查。

步骤很轻：

1. 读当前任务的一句话目标。
2. 选一个最相似的边界案例。
3. 判断当前应该使用、降级、转交还是停止。
4. 如果 skill 的指引会把案例推向错误动作，修 skill，而不是给案例加例外。

## 具体案例

### 案例 A：普通执行已经足够

用户说：“把 README 里的错别字改掉。”

Expected route: Stop -> direct execution

3L5S should not run，因为问题清楚、低风险、可直接执行。这里 ordinary execution
is enough。最小正确动作是定位错别字、修改、运行相关文档测试。

如果 agent 开始做 Discovery / Definition，只会增加沟通成本。

### 案例 B：SELA 看见方向，但不能推出立即承诺

一个团队讨论是否把手工研究流程换成 agentic research。长期系统效率可能明显更高，
SELA sees direction but not commitment。

Expected route: Find -> `sela` -> direction judgment, not commitment

正确输出不是“立刻全量迁移”，而是把长期方向、试点边界、不可逆风险和时机检查说清楚。
如果缺预算、团队能力或真实试点证据，结论应保持为方向判断，而不是承诺判断。

### 案例 C：EDSP 因缺证据而停止

用户问：“这个产品是不是会打败现有 SaaS？”

EDSP 可以处理结构推演，但 EDSP should stop because evidence is missing。如果没有市场、
渠道、价格、留存、销售周期或竞品数据，极限推演只能给结构假设，不能给胜负结论。

Expected route: Find -> `edsp` -> claim ceiling / evidence handoff

正确动作是输出需要哪些证据，以及当前结论的 claim ceiling。

### 案例 D：WAE 划清脚本顺序和判断真相

一个 workflow 能稳定生成报告、跑检查、产出 PASS。

WAE separates script order from agentic truth：脚本可以控制顺序、输入输出和证据格式，
但不能因为字段填满就决定“方案正确”。业务语义、架构取舍和下游影响仍需要 agentic
judgment 或人工判断。

Expected route: Find -> `wae` -> separate script order from truth judgment

### 案例 E：TVG 应该阻断而不是加深

一份安全交接文档结构完整，但缺少真实日志、复现步骤和影响范围。

TVG blocks rather than deepens。继续补“风险分析”和“建议措施”会让文档更像完成品，
但核心证据仍然缺失。正确动作是 block，要求补运行时证据或明确 review-bound。

Expected route: Stop -> Evidence / Claim Ceiling -> block rather than deepen

### 案例 F：反螺旋停止局部修补

同一个 prompt 已经第三次被改，用户反馈仍然是“还是不对”。

Anti-Spiral stops local repair。下一步不是再加一条规则，而是回到目标、输入、验收标准或
方法选择。继续局部修补只会让结构更厚，判断更弱。

Expected route: Stop/Find -> Anti-Spiral -> return upstream

### 案例 G：区分合成角色压力和真实激励冲突

一个设计方案需要被挑战，但参与者没有明显利益冲突。用 Builder / Challenger /
Synthesizer 这类 Multi-Role Pressure 就够了。

如果销售、法务、实施、财务各自会因结论不同而受益或受损，就不是普通多角色模拟。
Perspective Pressure distinguishes synthetic role pressure from real incentive conflict；
此时应触发 Adversarial Incentive Check，检查谁可能隐藏成本、转移风险或包装收益。

Expected route: Find pressure -> Perspective Pressure -> choose synthetic roles or incentive check

## 常见误用

第一种误用，是把案例当新规则。案例只帮助判断边界，不替代主方法。

第二种误用，是为了覆盖所有可能性不断加案例。Casebook 应该收集高信号压线场景，
不是普通 FAQ。

第三种误用，是看到案例相似就机械套用。真实任务仍要看目标函数、证据和风险。

## 边界

Casebook 不替代 skill 本身，也不替代测试、证据或领域研究。

它尤其不应该变成总入口。当前任务如果已经清楚，直接执行即可；当前任务如果缺事实，
先补事实；当前任务如果超出权限，转交或降级。

## 与其他方法的关系

- `using-mindthus` 用它帮助判断何时停止、降级或路由。
- `shared-primitives` 解释案例里反复出现的横切机制。
- `TVG` 可以加深案例说明，但不能把案例升级成普适规则。
- `tplan` 可以把案例作为长任务决策 hook 的参考。

## 导航

- 返回 [README](../../README.md)
- 查看 [Shared Primitives](shared-primitives.md)
- 查看 [Using Mindthus skill](../../skills/using-mindthus/SKILL.md)
