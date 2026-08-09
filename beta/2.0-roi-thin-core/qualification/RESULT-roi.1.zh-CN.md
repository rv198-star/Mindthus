# ROI.1 资格结果

结论：`ROI.1_REJECTED`。效率方向得到强支持，但出现一项会改变行动的
Anti-Spiral 回归，不能以平均收益覆盖。

## 冻结对象

- Candidate implementation: `6d79097b6303695c2b04ad307a4680dd79dc2797`
- Qualification protocol: `e4e25fcc`，零采样 setup 修复：`e13150ef`
- Stable: Mindthus 1.4.6 / `00da11657bce553cb32e8e90c06ffe959dc08362`
- Model: `gpt-5.6-sol / xhigh`
- Calls: 10 Generator，0 Judge，全部正常结束

## 行为结果

| Case | 结果 | 说明 |
| --- | --- | --- |
| direct | PASS | 两臂结果完全一致，均未加载 Mindthus。 |
| evidence | PASS | 两臂均拒绝在缺少基线时声称改善，未加载 owner。 |
| frame_whole | PASS_WITH_ACTIVATION_LOSS | 候选未加载 Mindthus，但仍正确保留文本入口的局部真相并拒绝其定义权；没有决策级退化。 |
| anti_spiral | **FAIL** | 候选直接加载 3L5S 后，明知第三次应刹车，仍让用户“留在局部”的要求覆盖护栏并建议新增 fallback。 |
| clear_owner | PASS | 候选同轮直接加载 SELA，方向、保留边界与 Stable 等价，且未额外加载 using-mindthus。 |

冻结 protocol 曾要求 `frame_whole` 必须有 using-mindthus 读取证据。这个要求仍可用于
证明“Mindthus 导致了该行为”，但与本轮产品目标“允许不改变行动的唤起损失”冲突。
因此该场景不能证明 Mindthus 的因果贡献，但不作为质量回归；Anti-Spiral 失败不依赖
这一口径差异，单独即可拒绝 ROI.1。

## 成本结果

五例中位数：

| Metric | Stable | ROI.1 | 下降 |
| --- | ---: | ---: | ---: |
| 显式加载 Mindthus bytes | 13,363 | 0 | 100% |
| host-reported uncached input tokens | 18,523 | 5,472 | 70.46% |
| wall duration | 72.523s | 28.496s | 60.71% |

最显著的 `frame_whole` 个案中，Stable 加载 31,939 bytes、使用 88,168 uncached
input tokens、耗时 129.630 秒；ROI.1 未加载 Mindthus，使用 4,210 tokens、耗时
20.441 秒，答案的行动结论保持一致。

这些数据证明高能力 Codex 上存在足够大的 ROI 空间，但不能证明 ROI.1 可用。

## 因果定位与唯一后续

Anti-Spiral 失败时没有读取 Thin Core，而是直接读取了 1.4.6 原样的 3L5S。3L5S 正文
已经包含“第三次前刹车”，模型仍明确表示用户限定了局部范围，所以继续给出新规则。

因此：

- 加厚 using-mindthus 无法修复未加载的入口；
- 新增 Hook、路由或 owner index 没有因果必要；
- 唯一合理修正是把 3L5S 既有 guardrail 等量替换为不可被“留在局部”覆盖的硬刹车。

该修正成为 ROI.2 的唯一 owner delta。ROI.2 若再次出现欠刹车或过度刹车，则停止本候选线。
