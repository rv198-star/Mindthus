# Mindthus Codex Routing Continuation 终局决策报告

终局：`STOP_2X_EXPLORATION`

预算翻倍解决了上一轮的两个技术疑点：这次 Q2 在可信隔离目录中恢复会话，且单次
调用只消耗 97,248 counted tokens，远低于新的 400,000 上限。但候选仍在明确应由
MPG 处理的任务中额外读取了无关的 SELA owner，因此 H2 在 owner fidelity 这一项
关键资格上失败。

这使结论比上一版更确定：停止不再是因为 carrier 污染或预算撞线，而是冻结候选本身
无法稳定做到“清晰 owner 任务只加载正确 owner”。

## 新证据证明了什么

- Q1 通过：只读取安装包内的薄入口，不读 index/owner，不先给方向，只问一个会改变
  答案的阻断问题。
- Q2 的宿主进程保持在 isolated workspace，没有读取仓库、项目 `AGENTS.md` 或 Stable
  Skills，旧的隔离污染已被排除。
- Q2 正确读取了 owner index 和 MPG owner，说明 single-entry -> index -> owner 的宿主
  生命周期可以实际发生。
- Q2 随后又读取 SELA owner。测试提示具备 MPG 的 actor、carrier、exposure、path
  volatility 和当前路径决策，却不存在 SELA 所要求的“系统长期效率/趋势与真实局部优势
  冲突”。所以 SELA 是无关 owner，而不是合法 companion lens。

最终回答虽然实用，但冻结协议把 owner fidelity 设为一票否决项，不能用回答质量或平均
得分掩盖。Q2 因而构成可信的 critical failure。

## 为什么不继续跑 Q3-Q7、Stable 和 Judge

资格协议规定：一个关键能力失败即可阻止 CONTINUE；只有通过资格的候选才能进入 Stable
对照；Judge 只在两臂输出完整后执行。Q2 已经给出会改变终局的可信失败，继续生成剩余
样本不会恢复候选资格，反而违反“下一步无法产生新 decision-changing evidence 时停止”
的规则。

要继续只能再改候选、增加路由结构、放宽“不得加载无关 owner”标准，或设计 H3。这些
都超出本次授权。因而这里不是预算用完，而是路线在既定边界内已经收敛。

## 成本

| 范围 | Generator | Judge | Input | Output | Counted tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| 原 Mission | 11 | 0 | 1,042,356 | 19,172 | 1,061,528 |
| 本次 continuation | 2 | 0 | 122,990 | 2,823 | 125,813 |
| **累计** | **13** | **0** | **1,165,346** | **21,995** | **1,187,341** |

总预算为 8,000,000 counted tokens，仍剩 6,812,659；调用上限为 32 Generator / 8
Judge，实际使用 13 / 0。大量剩余预算恰好说明终止原因是资格失败，而不是资源不足。

## 最终判断

H1 已证明 metadata 收紧具有局部价值，但无法守住 Decision Context；H2 已证明薄入口与
按需资源拓扑可以被宿主执行，却无法守住清晰 owner 的唯一命中。两条授权路线都不能在
不增加隐藏载体或明显质量风险的条件下证明 2.x 的产品价值，因此停止 2.x 路由探索，
保留 1.4.6 为功能完整基线。

这不是证明所有未来 single-entry 方案在理论上不可能，而是证明冻结候选
`9c271c1f3fb86f1e81f4860d32d9e5ac4f08b59c` 在本次明确门槛下不合格。继续需要新的产品
立项与新授权，不属于本 Mission。

不发布、不合并、不打 tag、不创建 Beta.3、不准备 release。
