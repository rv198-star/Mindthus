# WAE / Workflow-Agentic-Evidence

## 这是什么

WAE 是 `Workflow / Agentic / Evidence`，一套 agentic-system control-boundary lens。
Use it only when LLMs, agents, skills, prompts, scripts, schemas, workflows, review
gates, or evidence gates may be controlling the wrong part of the work. 它回答的
不是“问题是什么”，而是“这部分 agentic 系统工作应该由什么控制”。

Domain scope: LLMs, agents, skills, prompts, scripts, schemas, workflows, review gates, or evidence gates.

Domain Gate：对象必须是 LLM / agent / skill / workflow / script / schema /
evidence-gate system。No agentic system, no WAE。

Control Gate：workflow、agentic reasoning、evidence、schema、script、review 或
human authority 可能控制错了工作层。No controller mismatch, no WAE。

在 agent 项目里，失败经常不是来自单点能力不足，而是控制权放错了位置：脚本开始决定本该由人或 agent 判断的事，agent 反复处理本该固定下来的机械步骤，review gate 在没有证据时宣布通过，schema 把不确定的真相包装成已完成状态。

WAE 把这些混在一起的东西拆开：workflow 控制顺序和机械动作，agentic judgment 处理语义和不确定性，evidence 把说法连接到可观察事实。

## 解决什么问题

WAE 解决的是控制权错位。

典型场景包括：

- 自动化脚本越权做语义判断。
- Agent 在重复执行确定性格式化、搬运、校验，浪费上下文和判断力。
- 评审流程只检查字段存在，不检查 claim 是否被证据约束。
- 日志很多，但没有可用于决策的 evidence。
- 工作流看起来很规范，但出错后没人知道该回退、停下还是继续。
- 新增规则越来越多，却没有说明它们控制的是 workflow、agent 还是 evidence。
- 名义上已经由 Agentic owner 负责的工作继续委托后，下游 helper / adapter 仍然需要决定会改变结果的语义。

这些场景都默认发生在 agentic 系统里。普通概念分类、组织责任、产品边界、
结构 A/B 判断或流程治理问题，不会因为出现“边界 / 责任 / 流程 / 证据”这些词
就自动进入 WAE。

WAE 的价值，是让系统在复杂时仍然知道“谁管什么”。它不要求所有事情都自动化，也不要求所有事情都交给 agent。它追求的是控制面匹配。

## 核心判断

WAE 的核心判断是三分法：

- `Workflow` 负责确定性的顺序、状态、格式、脚本调用和机械校验。
- `Agentic` 负责上下文理解、语义判断、取舍、归因和不确定性处理。
- `Evidence` 负责把判断与可观察事实连接起来，避免 review 只靠信心。

判断时先看两个变量：

1. `workflow certainty`：路径是否确定，步骤能否机械执行。
2. `context certainty`：语义是否确定，事实是否足够，claim 是否可验证。

路径确定、语义确定的工作交给 workflow。路径不确定或语义不确定的工作保留 agentic judgment。凡是会影响结论、验收、继续/停止或用户信任的 claim，都需要 evidence 约束。

## 第二层：Ownership Closure / 所有权闭合

多数 WAE 判断做到上面的控制分配就够了。但复杂 agentic system 里还有一种失败：
**第一层 Owner 分对了，语义却在委托链里继续往下泄漏。**

例如：

```text
Agentic service owns persistence
    -> Repository.save(record)
    -> StorageAdapter.persist(record)
```

如果 `StorageAdapter` 仍然必须自己决定 `insert / update / append`、冲突是拒绝还是覆盖、哪些字段写入、失败或返回语义是什么，那么“Agentic owns persistence”只是名义上的第一层答案。真正改变结果的语义选择仍没有被显式 owner 掌握。

WAE 把这种情况称为 `Semantic Ownership Leakage / 语义所有权泄漏`。这时才进入条件性的 `Ownership Closure / 所有权闭合`：沿着**可能携带语义选择的 delegation boundary**继续检查，而不是沿代码层级无限递归。

核心原则：

> Ownership must extend to the last non-mechanical decision point.
>
> Ownership follows semantic choice; Workflow follows deterministic consequence.

检查时问：下游是否仍需要理解业务/领域语义、从多个合理结果中选择、解释 prose/隐含上下文，或者决定会改变状态、副作用、权限、失败语义和最终结果的行为？如果是，边界没有闭合，应把该选择交给明确 semantic owner，或把它显式化为结构化 contract。

### Mechanical Boundary / 机械边界

递归不是越深越好。一旦剩余工作同时满足这些条件，就必须停止：

- 输入完整且结构化；
- 对允许的输入，行为唯一确定；
- 不再需要业务或领域判断；
- 剩余验证与执行可以机械完成；
- 未知或不完整输入会 fail closed，而不是靠 heuristic 猜语义。

例如 Agentic 已明确给出：

```yaml
kind: append
conflict: reject
return_fields:
  - id
  - created_at
```

后续 schema validation、parameterized SQL、transaction、row mapping 可以很复杂，但如果行为已经由该 contract 唯一决定，它们仍然属于 Workflow / mechanical execution。

所以 Ownership 追随的是**语义选择**，不是 implementation depth。

### Evidence 可以重开边界，但普通失败不行

Ownership Closure 不是 `fix -> test -> fix` 的泛化 Loop。

如果真实 runtime evidence 表明某个下游组件仍不知道该选哪种业务行为，它可以推翻此前“边界已经闭合”的判断，让 WAE 重新细化 ownership。

但如果语义已经完整，只是 SQL placeholder 写错、格式转换有 bug、timeout 或其他机械实现失败，这只是 execution repair。Owner 和 semantic contract 没变，就不属于 Ownership Refinement。

## 怎么用

轻量 WAE 不需要复杂表格，先问三句：

1. 这是 `path uncertainty` 还是 `truth uncertainty`？
2. 这个 claim 需要什么 evidence 才能成立？
3. 如果错了，能否安全回退，代价多大？

如果答案已经清楚，就直接定边界。例如：

- 格式化、文件存在、schema shape、命令退出码：交给 workflow。
- 文档是否有价值、方法是否浅薄、问题定义是否正确：交给 agentic judgment。
- 测试输出、diff、日志、用户反馈、真实运行结果：作为 evidence。

如果边界仍然不清，再使用 worksheet 或更完整的控制边界分析。WAE 的目标是减少控制混乱，不是给每个任务增加一层流程。

只有在已经分配 semantic owner 后仍出现 delegation smell、下游多种合理行为、heuristic 语义推断，或 runtime evidence 暴露隐藏 semantic choice 时，才继续做 Ownership Closure。普通 WAE case 不需要多跑这一层。

## 具体案例

### 案例 A：CI 能不能判断文档质量

CI 可以检查 README 是否存在、链接是否有效、方法页是否包含必要标题、测试是否通过。这些属于 `Workflow`，路径确定，适合自动化。

但 CI 不该判断“这篇 README 是否真的让新用户有动力使用”。这是 `Agentic` 判断，需要上下文、读者感受和取舍。相关 evidence 可以是用户反馈、review 结论、具体阅读障碍和 diff，而不是脚本输出 `PASS`。

### 案例 B：logs 很多但没有 evidence

一个 agent 可能记录了十几条 step logs：读了文件、改了文档、跑了命令。但这些 logs 只说明发生过什么，不说明结论成立。

WAE 会要求把关键 claim 单独接到 evidence 上。例如“安装说明有效”需要脚本语法检查或实际安装结果；“文档更易懂”至少需要具体改动、示例覆盖和 reviewer 反馈，而不是“我已经优化过”。

### 案例 C：Repository 已经 Agentic owns，为什么还没闭合

一个 Agentic service 正确拥有 persistence intent，但把一个只有 domain object 的 `save(record)` 交给 generic adapter。adapter 仍要决定追加还是更新、冲突策略和返回行为。

这不是“再跑一次 WAE”或“多做一次测试”能解决的问题，而是当前 ownership contract 没有延伸到最后一个 semantic choice。正确修复是先把这些选择显式化，例如形成完整 `PersistenceCommand`，再把确定性的 SQL/execution 留给 Workflow。

## 常见误用

第零种误用，是把 WAE 当成所有边界问题的默认方法。没有 agentic system，
不要用 WAE；没有 controller mismatch，也不要用 WAE。

第一种误用，是把 WAE 当通用流程设计器。WAE 只处理 agentic 系统里的控制权，
不负责把所有工作流程化。

第二种误用，是把 evidence 做成字段。字段存在不代表证据有效；证据必须能约束具体 claim。

第三种误用，是让脚本代替判断。脚本可以验证 shape、状态和确定性规则，但不能判断“这个文档是否真正有价值”“这个策略是否方向正确”。

第四种误用，是把 agentic judgment 无限扩大。凡是确定、可重复、低风险的工作，都应该尽量交给 workflow，避免 agent 在机械环节消耗注意力。

第五种误用，是把 Ownership Closure 当通用 Agent Loop。只有 Evidence 暴露新的 semantic remainder 时才移动 ownership boundary；普通 implementation retry、测试修复或执行重试不会自动触发 refinement。

## 边界

低风险、低不确定性、确定性的格式化工作不需要套 WAE。直接脚本化即可。

WAE 也不负责定义问题本身。如果还不知道问题是什么，用 `3L5S`。如果争论的是长期趋势和局部优势，用 `SELA`。如果命题结构摇摆，用 `EDSP`。如果控制边界已经明确，真正的问题是多个有效行动争夺同一稀缺资源，用 `SRA` 做分配。

当 evidence 不足时，WAE 不会替你补事实。它只会指出“这个 claim 还没有被约束”，然后要求补证据、降级结论或停止。

Ownership Closure 也不是长任务 runtime：它不建立 Mission、任务树、checkpoint、recovery state 或持久化 refinement history。它只判断语义 ownership 是否已经闭合。

## 与其他方法的关系

- `3L5S` 处理问题发现与落地，WAE 处理其中的控制边界。
- `SELA` 给长期方向，WAE 判断方向落地时哪些步骤能自动化、哪些必须保留判断。
- `SRA` 在控制边界已经闭合后决定跨候选资源投向；WAE 只约束 SRA 的 Workflow / Agentic / Evidence 分工，不替它选优先级。
- `tplan` 是 WAE 的典型落地和承载场景：TPlan 管 Mission/task state、顺序、blocker、checkpoint、recovery 和 resumption；WAE 管 semantic control boundary，以及在必要时判断 ownership 是否闭合。长 Mission 可以反复调用 WAE，但这种 recurrence 由 TPlan 承载，不会把 WAE 变成第二套 runtime。
- `Anti-Spiral` 可以被理解为 WAE 的失败保护：当 agentic 判断开始用局部修补替代证据进展时，必须刹车。

一句话区分：

```text
TPlan：下一步发生什么、什么状态要继续？
WAE：这个语义决定由谁拥有、这个 ownership 是否已经闭合？
```

## 导航

- 返回 [README](../../README.md)
- 查看 [WAE skill](../../skills/wae/SKILL.md)
- 深入 [Ownership Closure resource](../../skills/wae/resources/ownership-closure.md)
