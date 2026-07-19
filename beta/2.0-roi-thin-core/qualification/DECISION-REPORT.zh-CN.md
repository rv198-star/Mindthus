# Mindthus 2.x ROI Thin Core 决策报告

终局：`CONTINUE_2X_ROI_THIN_CORE_AS_EXPERIMENTAL_CANDIDATE`

这条路线已经证明值得继续作为 2.x 候选：它在本轮高能力 Codex 样本中大幅降低了
加载、未缓存输入 token 和耗时，同时保留了明确 owner 直达，并在唯一一次
decision-changing 回归后用一处因果对应的 owner guardrail 替换完成修正。

这不是发布批准，也不是“所有任务都无损”的证明。

## 最终候选

- Candidate: `2.0.0-roi.2`
- Implementation commit: `493f9520b75f582aa22f6c8647ec08eab3e122d3`
- Stable baseline: 1.4.6 / `00da11657bce553cb32e8e90c06ffe959dc08362`
- Surface: Codex only
- Model / effort: `gpt-5.6-sol / xhigh`

运行形态：

- `using-mindthus` 从 7,193 bytes 降到 2,298 bytes，缩小 68.05%；
- using-mindthus 不再包含方法目录、owner 摘要、路由表、条件资源预加载或模型分流；
- 六个 owner 与 1.4.6 byte-identical；
- 3L5S 只有一处 package-time guardrail 句子替换，正文其余部分和 description 不变；
- 没有 Hook、owner index、第二入口、隐藏 atlas、AGENTS 注入或 defaultPrompt 改动。

## 为什么 ROI.1 失败、ROI.2 可以继续

ROI.1 的 10 次双臂调用中，direct、evidence、frame/whole 和 SELA owner 四类行动结果
合格，但 Anti-Spiral 失败：候选直接加载 3L5S，读到了“第三次前刹车”，随后仍明确
让用户“别讨论上游”的局部要求覆盖护栏，并建议新增 fallback。

这证明“只缩薄 using-mindthus、owner 完全不动”还不够。失败发生时 Thin Core 未加载，
所以加厚入口、增加路由或加 Hook 都不是因果修复。

ROI.2 只替换 3L5S 既有 guardrail 的一句话：第三次无新证据的局部加法是硬刹车，
即使用户要求留在局部，首句也必须拒绝；之后只能给删除或等量替换。修正测试结果：

- 第三次修补正例：候选首句拒绝新增 fallback，并只给等量替换；PASS。
- 第二轮且已有新 trace/失败测试的 near-negative：候选继续执行 schema 修正，未过度刹车；PASS。

ROI.2 没有第三次修正预算。

## 行为结论

| Case | ROI.2 结论 |
| --- | --- |
| 普通直做 | 与 Stable 完全一致，不加载 Mindthus。 |
| 证据不足 | 与 Stable 一致，拒绝在无基线时声称改善。 |
| Frame / Whole | 未加载 Mindthus，但答案仍正确保留局部真相并拒绝错误定义权；这是允许的无害唤起损失。 |
| Anti-Spiral | 直接加载修正后的 3L5S，拒绝第三次加法；near-negative 仍正常推进。 |
| 明确 SELA | 同轮直接加载 SELA，不额外加载 using-mindthus，方向与保留边界和 Stable 等价。 |

这里必须区分两件事：Frame/Whole 场景不能证明 Mindthus 造成了正确答案，因为候选没有
加载任何 Mindthus Skill；但它证明在 Sol xHigh 上，失去这次被动唤起没有造成行动退化，
且带来巨大节省。这正是本轮允许的有损优化，而不是伪装成完整 recall。

## ROI 结果

ROI.1 五个核心场景的中位数，在用 ROI.2 的修正 Anti-Spiral 结果替换唯一受影响样本后，
其 median-determining case 不变：

| Metric | Stable | ROI.2 | 下降 |
| --- | ---: | ---: | ---: |
| 显式加载 Mindthus bytes | 13,363 | 0 | 100% |
| host-reported uncached input tokens | 18,523 | 5,472 | 70.46% |
| wall duration | 72.523s | 28.496s | 60.71% |

只看三个 hard-judgment 场景（Frame/Whole、Anti-Spiral、SELA），并采用 ROI.2 修正结果：

| Metric | Stable median | ROI.2 median | 下降 |
| --- | ---: | ---: | ---: |
| 显式加载 Mindthus bytes | 27,409 | 7,937 | 71.04% |
| uncached input tokens | 21,808 | 7,214 | 66.92% |
| wall duration | 88.874s | 49.777s | 43.99% |

ROI.2 两个 Anti-Spiral 边界题自身的中位结果是：加载 bytes 下降 42.17%，uncached
input tokens 下降 53.63%，耗时下降 10.07%。它说明当 formal owner 确实需要加载时，
收益会低于“完全不唤起”的场景，但仍有明显 token 收益。

本轮共 14 次 Generator、0 Judge，counted tokens 为 1,214,384。所有 token 数来自
Codex `turn.completed.usage`；cached input 是 input 子集，没有重复相加。耗时受宿主和
网络噪声影响，只作支持证据。

## 已证明与未证明

已证明：

1. 1.4.6 的完整 using-mindthus 在部分 Sol xHigh 任务上会触发显著资源级联；
2. 删除入口中的方法 atlas 可以在不改变若干关键行动的情况下带来数量级可见的 ROI；
3. 明确 owner 可以绕过 using-mindthus 同轮直达；
4. 不能要求 Thin Core 独自承载所有 AOP：直接 owner 上的 decision-changing primitive
   必须由该 owner 的合同兜住；
5. 这种兜底不需要新路由，可以是有证据才增加的一句局部 guardrail。

未证明：

1. 所有七个 owner、所有认知原语和所有真实任务都维持相同质量；
2. 任何一次 Skill 未唤起都无害；
3. ROI.2 已达到发布、合并或默认替换 1.4.6 的成熟度；
4. 单样本行为是确定性的。ROI.2 复核中 Stable 自身在 Anti-Spiral 正例随机失守，说明
   两边都不能从一次输出推断绝对可靠率。

## 产品方向

2.x 不应再追求“零损复制 1.4.6 的全部被动唤起”。更可行的合同是：

> Thin Core 删除方法细节；Codex 原生发现 concrete owner；允许不改变行动的唤起损失；
> 只有经失败证据证明会改变行动的关键原语，才在相应直达 owner 内做最小硬化。

这意味着 1.4.6 继续作为 Recall-first / 功能完整基线，ROI.2 作为高能力 Codex 的
Efficiency-first 2.x 候选。后续不得预防性重写七个 owner，也不得把 using-mindthus 再
堆回方法 atlas。只有新的 decision-changing 失败证据才能授权新的 owner 局部修正。

## 边界

本分支不发布、不合并、不打 tag、不创建 release/PR/Issue，也不修改用户当前 Stable
安装。下一阶段若继续，应先扩大冻结任务覆盖，而不是继续改架构；本轮候选实现和路线
判断已经完成。
