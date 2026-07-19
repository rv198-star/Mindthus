# TVG-Profile 案例三：`cinematic-visual-direction`

## 这页讲什么

这是 TVG-Profile 的四层完整高级案例。它面向相对通用的影视画面优化：把一句简短画面要求，转成可生成、可审图、可定向迭代、也能把用户偏好交还给用户的运行包。

对应资源：

- `skills/tvg/resources/value-profiles/cinematic-visual-direction/profile.md`
- `skills/tvg/resources/value-profiles/cinematic-visual-direction/resources/`
- `skills/tvg/resources/value-profiles/cinematic-visual-direction/scripts/`
- `skills/tvg/scripts/atlas/`

外部 cinematic skill 仍然只是行为样本，不是 source truth。我们吸收的是它怎样组织镜头、做减法、约束脏乱和保留物理关系，不复制具体 wording。

## 为什么它不是“巨物 Profile”

此前的 `cinematic-colossal-realism` 把两层东西装在了同一个名字里：

1. 相对通用的影视导演控制，例如 primary read、director shot spine、director subtraction、controlled fracture 和 shot economy。
2. 巨物场景才需要的 witness anchor、three-layer scale、partial threat、frame overflow 和大尺度环境反馈。

这会让人误以为高级案例只适用于黑龙、古神或灾难尺度画面。现在第一层成为 canonical Profile，第二层降为 `colossal-pressure` 场景适配器。巨物能力没有删除，只是不再冒充通用电影规则。

安静江景可以只使用核心 Profile；黑龙压城则使用核心 Profile 加 `colossal-pressure`。二者共享导演控制，但不共享不相关的场景约束。

## 四层怎样工作

| 层 | 负责什么 | 不负责什么 |
| --- | --- | --- |
| `value_semantics` | 定义一张影视画面怎样形成 primary read、镜头主轴、场景关系和可信物理反馈 | 不把某类题材偏好升级成普遍规则 |
| `realization_surface` | 把问题落到 eye path、reveal、subtraction、camera、light、material、motion、negative space 等可审查单位 | 不用“更电影感”替代具体判断 |
| `gain_policy` | 规定先保留什么、修什么、减什么，以及何时才激活场景适配器 | 不把每一轮都做成继续加效果 |
| `runtime_support` | 提供 prompt skeleton、lint、field lock、九宫格编号、血缘、hash 和 trace 形状校验 | 不替 Agent 选图、判断美学成功或决定退出 |

## 场景适配器

`colossal-pressure` 是第一个正式适配器。它只在巨物、神祇、灾难尺度、深海或宇宙压迫场景中追加：

- witness / instrument anchor
- human、environment、colossus 三层尺度
- dominant partial threat
- frame overflow 与 partial visibility
- 大尺度力量对云、水、尘、建筑和人群的反馈
- 适配器自己的强度 2–5

这个强度不是 TVG 的全局 resource pressure。前者控制巨物场景怎样显现，后者控制 TVG 愿意投入多少轮判断资源。

## 多宫格怎样接进来

九宫格是通用 runtime carrier，不属于巨物适配器。

1. `R00-E01..R00-E09` 在生成前逐格写明探索意图。
2. Agent 根据固定 Profile 选出三个父候选。
3. 下一轮仍使用 `R01-E01..R01-E09`，主 ID 保持稳定。
4. 每个子图额外显示 `from R00-Exx`，trace 保存完整 parent chain。
5. 三个父图到九个子图的每一行都必须有 Profile 增益假设。
6. 搜索结束只叫 `search-freeze`，因为后续若重新生成 `2x2`，四张新图仍需 delivery audit。
7. 交付审计通过后，用户才在 `S01..S04` 中决定最终偏好。
8. `1x1` 可以跳过、直接接受 tile，或按选中来源受控重绘。

脚本能证明编号、血缘、文件引用和 hash 没有断，不能证明图真的变好。

操作说明和 shape-valid 示例见：

- `skills/tvg/resources/value-profiles/cinematic-visual-direction/examples/atlas-search-workflow.md`
- `skills/tvg/resources/value-profiles/cinematic-visual-direction/examples/atlas-search-trace.example.json`

## 为什么它仍是高级案例

它不是因为文件多才高级，而是因为四类控制权没有混在一起：

- Profile 定义价值和增益方向。
- 场景适配器只补局部题材约束。
- workflow 固定顺序、编号、交付和 finalization 状态。
- 脚本处理确定性变换与证据记录。
- Agent 处理语义选择、审图和退出判断。
- 用户处理没有客观唯一答案的最终品味选择。

这也是把外部 SKILL 迁成 TVG-Profile，而不是复制它的真正收益。

## 证据上限

一次黑龙、江景或仙侠实跑，只有在生成前确实锁定了本 Profile，才能支持：这套 Profile 与 runtime 在该次任务中产生了可观察的约束和迭代价值。

现有“一江春水向东流”运行发生在 canonical 拆分之前，锁定的是任务级前身 `poetic-cinematic-river-v0`。它可以证明 atlas carrier、血缘和交付状态实际跑通过，不能被事后改写成 `cinematic-visual-direction` 的视觉效果实证。

它不能直接证明：

- 这套 Profile 已经覆盖所有影视画面。
- `colossal-pressure` 适合非巨物场景。
- 多轮 runtime rescue 等同于 single-pass Profile power。
- 脚本校验通过等同于美学成功。
- Agent 或用户的一次选择构成普遍审美真理。

## 兼容说明

旧路径 `cinematic-colossal-realism` 继续保留，用来回放 v1.4.6 资源、脚本和历史证据。新工作应解析 `cinematic-visual-direction`，需要巨物压力时再显式添加 `colossal-pressure`。

## 导航

- 返回 [TVG 详细介绍页](../tvg.md)
- 查看 [轻量 Profile 案例](plain-sharp-skill-intro.md)
- 查看 [风格型影视 Profile 案例](film-style-profiles.md)
