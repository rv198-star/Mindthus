# Root-Cause Replacement / 根因替换

## 这是什么

Root-Cause Replacement 是一个 cross-cutting execution primitive。它处理这样一种恢复动作：证据已经把问题定位到错误的上游假设、canonical rule、controller、contract 或 ownership，而继续修改下游症状只会保留错误模型。

它不是 root-cause finder，也不是新的 judgment owner。问题定义仍归 `3L5S`，结构判断仍归 `EDSP`，控制边界仍归 `WAE`，反复局部修补由 `Anti-Spiral` 触发刹车；本原语只规定根因明确后的修复形态。

Short rule:

> **Fix the cause. Replace the rule. State the intended behavior directly.**
>
> **修根因，换规则，直接写正确逻辑。**

## 何时触发

满足任一条件时进入本原语：

- `Anti-Spiral` 回看上游后，证据表明局部 patch 正在维持错误模型；
- failing test、trace、运行证据或结构分析已经定位错误 canonical owner / rule / contract；
- 新增 exception、fallback、override 或 special case 只能遮住症状，无法改变产生症状的规则；
- controller mismatch 已经明确，正确动作是重新分配 ownership，而不是继续增加 override。

根因仍是 hypothesis 时，先服从 `Evidence / Claim Ceiling`：标记假设、补证据或缩小 claim。Root-Cause Replacement 不能把“我觉得这是根因”升级成事实。

## Mainline / 主路径

### 1. Name the broken cause

用一句话指出产生错误的上游原因，并绑定证据：错误假设、错误 owner、错误 contract、错误状态模型或错误规则。

### 2. Locate the canonical owner

找到应该承载正确语义的唯一 canonical location。正确逻辑应进入拥有定义权的位置，而不是散落到调用方、fallback、测试特例或输出后处理。

### 3. Replace the canonical logic

优先执行 `delete / rewrite / equal-replace`：删除失效规则，在 canonical owner 中直接写入正确逻辑，并同步移除由旧模型产生的冗余例外。

兼容层只服务真实的外部 contract 或迁移窗口。兼容层需要明确 owner、期限或 removal condition，避免临时适配器重新成为永久模型。

### 4. Affirmative Canonicalization / 肯定式正则化

Canonical mainline 直接描述目标行为、有效状态、controller、contract 和成功路径。

Boundary / veto / safety / authority 部分承载禁止行为。这样主逻辑说明“系统应该怎样工作”，边界说明“哪些行为必须被阻断”，两类语义各自归位。

修正规则时直接改写 canonical statement，使新的正确描述独立成立；旧错误规则不再通过反向限制继续存活。

### 5. Revalidate downstream impact

替换后检查受影响的 contract、测试、调用方、数据迁移、文档和回滚面。测试应证明新 canonical logic，而不是继续保护旧模型留下的历史例外。

## Decision Shape / 动作形态

| 观察到的状态 | 动作 |
|---|---|
| 根因有直接证据，canonical owner 明确 | 直接 rewrite / equal-replace |
| 根因仍是假设 | 补证据、缩小 claim，暂不扩大改动面 |
| 局部修复反复增长 exception / fallback | Anti-Spiral 刹车后回到 canonical owner |
| 外部 contract 暂时不能同步升级 | 建立有 removal condition 的迁移适配层 |
| failing test 持续提供新的因果约束 | 沿因果链继续正常 debugging |

## Failure Smells / 误用信号

- 新规则只解释旧规则什么时候失效，却没有形成独立正确的 canonical statement；
- diff 主要增长 exception、fallback、override、special case，而主 owner 保持不变；
- 测试开始验证历史补丁组合，而不是业务 contract；
- controller mismatch 已知，但控制权仍散落在多个调用方；
- “根因修复”变成无证据的大规模重写。

出现这些信号时，动作应该回到证据、canonical owner 或 Anti-Spiral，而不是继续增加结构层。

## 边界

Root-Cause Replacement 不要求每个 bug 都重构。根因本来就在局部实现时，局部修改就是正确的根因修复。

它也不否定 staged migration。真实外部兼容约束可以需要 adapter；关键是 adapter 服务迁移，而不是接管 canonical model。

安全、权限、合规和 hard veto 仍然可以使用明确的禁止性语言。Affirmative Canonicalization 约束的是 mainline truth expression，不削弱真实边界。

## 与其他方法的关系

- `Anti-Spiral` 决定何时停止重复局部修补；本原语规定上游根因明确后的恢复动作。
- `WAE` 判断 Workflow / Agentic / Evidence 的 controller ownership；ownership 错位明确后，本原语推动直接重写 owner，而不是叠加 override。
- `TVG` 只能强化正确边界内的 bounded artifact；发现错误 canonical model 时先退出强化循环并回到本原语。
- `3L5S` / `EDSP` 可以帮助找到真正的问题或结构；本原语不接管这些判断。

## 导航

- 返回 [Cognitive Primitives](../shared-primitives.md)
- 查看 [Anti-Spiral Self-Audit](../anti-spiral-self-audit.md)
