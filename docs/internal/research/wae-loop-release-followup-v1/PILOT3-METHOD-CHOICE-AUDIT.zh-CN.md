# WAE Loop pilot.3 — Method Choice Audit

日期：2026-09-08  
对象：是否应将 `Refinement Unit -> Refine Result -> Absorb` 作为 pilot.3，而不是继续 pilot.2 或走更重方案  
审计路径：B / Method-value and architecture choice only  
性质：本会话同一 ChatGPT 实例的独立审计路径；不复用 Runtime Audit 的 PASS 作为方法价值前提。不是异模型或真人外部认证。

## 结论

**PASS WITH PILOT-SCOPE CAVEAT。**

对当前目标——在 WFF / EKRI / Slidethus 真实项目中验证 WAE Loop 是否能够控制正确的 handoff depth、减少错误放手与无效深挖——pilot.3 是比 pilot.2 更优的实验运行合同。

它不是因为“结构更多”而更优，而是因为它首次让以下因果链可辨认：

> 哪一个具体交接障碍触发 refine → 这个障碍得到什么独立结果 → 该结果如何进入 Parent → 下游最终是否接住。

这直接降低真实 Pilot 的归因歧义。

## 比较的四个方案

| 方案 | 结构 | 主要优点 | 主要问题 | 裁定 |
| --- | --- | --- | --- | --- |
| A. pilot.2 | `refine + changed_scope + artifact before/after` | 最薄、成本最低 | 可以声称局部问题却整份 Parent 重写；Result 与 Parent 变化没有因果身份 | 不足以继续真实价值实验 |
| B. 只加 Unit ID | Parent + `RU-xxxx` + work | 能聚合日志，增加可读性 | Agent 仍可在 Unit 内直接重写 Parent；没有“Unit truth”和“Parent absorption”分离 | 比 A 好，但关键归因缺口仍在 |
| **C. pilot.3** | Parent → Unit → Result → Absorb → Parent' | 因果链清楚；可阻断提前重写；语义局部而非文本局部；只在 refine 路径增加成本 | 增加两个明确 lifecycle 事件；对直接编辑习惯有摩擦 | **当前 Pilot 最优** |
| D. 完整任务树 / nested Unit / 并行 invalidation | 子任务、依赖图、并行合并、版本失效 | 控制力最强 | 重新发明 TPlan/工作流系统；高成本；偏离 WAE 的 control-boundary lens | 明确拒绝 |

## 为什么 pilot.2 不够

pilot.2 已能回答：

- 发生了 refine 吗？
- Agent 自称 changed_scope 是什么？
- artifact before/after 是什么？

但不能回答：

- changed_scope 是否真的是这次 refine 的唯一判断单元？
- Agent 是先得出局部结论，再写回 Parent，还是直接重写 Parent 后反向解释？
- Parent 的变化中，哪些属于这个 refine 的直接后果？
- 一个小 blocker 导致大范围重写，是必要 dependency closure 还是过度设计？

真实 Pilot 若缺这层信息，一次高成本重写即使最终 PASS，也无法归因是 WAE 本身贵、模型工作方式漂移，还是任务确实需要全局重构。

## 为什么只加 Unit ID 仍不够

单独增加：

```text
unit_id
unit_scope
```

能改善日志分组，但无法建立**先解决 Unit、后改变 Parent**的顺序约束。它仍允许：

```text
open RU-0001
-> rewrite whole P1
-> log changed_scope="review validity"
-> handoff
```

因此它主要提升 observability，没有充分提升 experimental control。

## 为什么 pilot.3 更匹配原始 WAE Loop 目标

### 1. 它约束的是 semantic work unit，不是文档行数

Refinement Unit 只拥有一个结果性 question 与必要 semantic dependency closure。

这避免两个相反误区：

- 以“小 diff”冒充局部；
- 因为一个正确决定需要同时调整几个依赖规则，就错误禁止跨段修改。

### 2. Result 与 Parent 分离，能证明“这一轮到底产出了什么”

`Refine Result` 是 Unit 的独立结果，不等于整个 Parent 新版本。大内容可以通过 result artifact 引用，trace 只保留 bounded summary。

这对三个真实场景都成立：

- WFF：一个产品/设计规则；
- EKRI：一个有证据边界的工程事实或未知；
- Slidethus：一个策划主张/论证/表达关系。

### 3. Absorb 把局部真相与 Parent 变化建立因果绑定

只有 Result 形成后才允许 Parent update/confirm，且下一次 handoff/refine 必须从 Absorb 后 Parent identity 继续。

因此日志可以回答：

```text
RU-0001 caused Parent P1@A -> P1@B
```

而不是只看到两份毫无解释的全量文件。

### 4. 默认成本没有扩散到一般使用

- WAE Loop 默认 OFF；
- 一次已经充分的 handoff 不产生 Unit；
- `work` 事件可选；
- 只有实际 `refine` 才增加 Result + Absorb；
- 没有 Reviewer、嵌套 agent、任务树或固定多轮。

所以 pilot.3 的额外成本被限定在我们真正要研究的“为什么继续下钻”路径。

## 最强反方质疑：它是否过度限制自然编辑？

**成立一部分，因此本审计只给 Pilot-scope PASS。**

project-file Parent 在 Refine Result 前要求保持不变，意味着 Agent 不能一边推理一边直接改主文件。这会增加某些宿主中的操作摩擦。

但在当前 Pilot 目标下，这个摩擦有明确价值：

> 把“形成局部判断”和“将判断吸收到 Parent”分开，换取可验证的因果归因。

对于 P1/P2 设计稿、EKRI knowledge package、Slidethus planning artifact，这种约束是可承受的；它不是普通代码修 bug 的通用开发流程。

真实 Pilot 应记录：

- Unit 数；
- Result/Absorb 额外调用和耗时；
- Parent 改动规模；
- 是否出现 Agent 为满足流程而制造无价值中间文本。

如果真实数据表明该分离本身产生明显负担而没有提高 handoff 质量，Stable 产品化时应收缩交互，而不是因为 pilot.3 已实现就永久保留。

## 第二个反方质疑：它仍然不能阻止 Absorb 时整篇重写

**正确，而且不应继续用 deterministic runtime 去“猜”语义范围。**

pilot.3 能做到：

- 让整篇变化只能发生在 Result 之后；
- 将变化绑定到某个 Unit；
- 记录 before/after ref/hash/bytes 和 absorbed scope；
- 后续审计可以识别“一小 Unit 导致大 Parent change”的异常模式。

它不能可靠判断：

> 这次大改是不是业务上真的属于该 Unit 的必要 dependency closure。

若用 diff size、行数或固定百分比阻断，会把 textual locality 错当 semantic locality，违背 WAE 自己的控制边界。因此这里保持 Agentic/audit judgment 是正确选择。

## 第三个反方质疑：为什么不支持多个并行 Unit？

当前明确只允许一个 open Unit，是有意的 Pilot 收缩：

- 避免并行 Unit 同时修改 Parent 的 invalidation/merge 问题；
- 避免把研究转成 task graph/runtime；
- 使真实 trace 可以清楚归因每一次 Parent change。

如果以后真实项目证明并行 Unit 是主要性能瓶颈，可以另立产品假设；当前没有证据支持提前引入。

## 与 TPlan 的边界

pilot.3 新增的是一段 WAE-local causal trace：

```text
Unit state: open / resolved / blocked / absorbed
```

它没有：

- 任务优先级；
- Mission tree；
- retry scheduling；
- continuation authority；
- recovery planning；
- 并行 task orchestration。

因此当前变化仍属于 WAE delegation-depth runtime support，没有夺取 TPlan 的 lifecycle authority。

## 三场景迁移判断

### WFF

最适合直接受益。P1/P2 的一个上游语义缺口可以成为 Unit，Result 是 canonical design truth，Absorb 后再交 P2/P3。能够直接观察是否仍出现 whole-P1 regeneration。

### EKRI

`unit_kind=evidence_gap` 能把“查什么事实”与最终 knowledge package 分开；`confirm` Absorb 可以表示进一步取证后确认旧包已经足够，无需为证明 refine 存在而强制改文档。

### Slidethus

策划阶段可以把一个论证/主张/信息层级问题作为 Unit；Result 是策划语义，不直接等于重新生成整份 PPT/Storyboard。Absorb 才更新策划 Parent，从而减少上游接管视觉实现的诱因。

三者使用同一个结构，不要求场景专用 runtime 语义，符合通用机制候选要求。

## 最终裁定

在“真实 Pilot 前减少 refine 归因污染”这一目标函数下：

> **pilot.3 是比 pilot.2、只加 Unit ID、以及完整任务树更优的选择。**

该结论只支持内部 Pilot 发布，不等于 Stable 产品形态已经冻结。真实项目仍需验证额外结构带来的净收益是否超过流程成本。
