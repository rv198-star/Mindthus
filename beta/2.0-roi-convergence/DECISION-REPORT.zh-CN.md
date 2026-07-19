# Mindthus 2.x ROI-First Routing Convergence 决策报告

终局：`STOP_2X_ROI_CONVERGENCE_NO_QUALIFIED_SUCCESSOR`

这轮没有找到一个在冻结底线之上、又能可靠优于 ROI.2 的新路线。三条新路线都完成了
真实采样；它们都守住了预注册的唤起率底线，但都在同一个关键点失守：面对缺少决策
上下文的 continue/stop 请求，模型先给了暂停、停止或 hold 姿态，而不是先锁定会改变
答案的条件。

唯一显示正 ROI 的 R2 使用了一次允许的等量修正。修正后的 895-byte Decision Context
gate 能正确拦住欠上下文请求，却在冻结的清晰 MPG 任务中因为 RPO/可接受损失未明而
继续阻断，没有同轮给出路径动作。继续只能再加例外、改题或放宽交互标准，因此按停止
规则关闭路线。

结论不是“2.x 全部无效”。ROI.2 仍是已经证明相对 1.4.6 有显著收益的实验候选；本轮
证明的是：在 ROI.2 之上继续靠 discovery/入口拓扑做减法，没有得到可接受的 successor。

## 冻结目标与底线

本 Mission 把 recall 当约束、ROI 当目标：

- 显式 owner：SELA、MPG、WAE 三个冻结代表题必须 3/3 同轮命中；
- 被动原语：Frame/Whole、Decision Context、Anti-Spiral 至少命中 2/3；
- 所有题不得出现 decision-changing 行动退化；
- 普通与 evidence-first 不得加载 formal owner 或增加交互；
- 主 ROI 是九题 host-reported uncached input tokens 中位数；相对 incumbent 至少下降
  5% 才算可识别改进；
- 同一路线最多一次等量/减法修正，不允许 Candidate D。

Incumbent 是未发布的 ROI.2，Stable 1.4.6 继续作为 recall-first / 功能完整基线。

## 三条路线结果

| 路线 | 架构差异 | 显式 owner | 被动原语 | 行动门 | uncached 中位数 | 相对 incumbent |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| ROI.2 incumbent | 2.3 KB 薄入口＋原生 owners | 3/3 | 3/3 | Decision Context FAIL | 10,407 | — |
| R1 | 1,242-byte 最小被动入口 | 3/3 | 2/3 | Decision Context FAIL | 11,449 | **差 10.01%** |
| R2 | 750-byte 显式仲裁入口＋owner-local gate | 3/3 | 3/3 | Decision Context FAIL | 8,714 | **好 16.27%** |
| R3 | 无 using 入口，仅原生 owner 集 | 3/3 | 2/3 | Decision Context FAIL | 13,146 | **差 26.32%** |

三个正式 owner 代表题全部命中。R1 牺牲 Frame/Whole 被动唤起，R3 牺牲 Decision
Context 被动唤起，仍都达到 2/3 底线；漏唤起的 Frame/Whole 回答本身没有行动退化。

但 Decision Context 不能只看“是否读了 Skill”：

- incumbent 和 R1 读了 MPG＋SELA；
- R2 读了 3L5S；
- R3 没读 Mindthus；
- 四者都在事实不足时先给了暂停/停止方向。

这说明被动 activation rate 达标不等于 primitive fidelity 达标。错误 owner 命中甚至会让
“有唤起”掩盖错误动作。

## ROI 细节

九题有效面板：

| Metric | Incumbent | R1 | R2 | R3 |
| --- | ---: | ---: | ---: | ---: |
| loaded Mindthus bytes median | 7,937 | 7,937 | 7,937 | 7,937 |
| uncached input median | 10,407 | 11,449 | 8,714 | 13,146 |
| duration median | 63.244s | 54.258s | 57.718s | 66.286s |
| panel counted tokens total | 386,118 | 387,548 | 468,814 | 450,298 |

只看六个 hard-judgment 场景，uncached 中位数为：incumbent 12,476，R1 14,971.5，
R2 12,140.5，R3 14,090.5。R2 在这一子集只好 2.69%，低于 5% 可识别门槛。

R2 的主中位数虽然最好，总 counted tokens 却最高。一个清晰 MPG 样本读取 MPG、SELA
及资源共 44,179 bytes，消耗 127,702 counted tokens、154.431 秒。这不否定冻结的
primary metric，但说明 R2 的收益伴随明显尾部和 owner cascade，不能用单个漂亮中位数
概括。

## R2.1 唯一修正

R1、R3 的主 ROI 已经差于 incumbent，因此没有把预算用于“先修质量、再期待成本奇迹”。
R2 是唯一同时具备正 ROI 信号和局部失败的路线，获准一次等量替换：

- 删除 750-byte 显式方法仲裁合同；
- 替换为 895-byte Decision Context gate；
- 不改 EDSP、3L5S、MPG 或其他 owner 正文；
- 不加 Skill、Hook、index、资源、模型分支或第二 gate。

定向正负配对：

| Case | 结果 | 加载 | Uncached | 结论 |
| --- | --- | --- | ---: | --- |
| 欠上下文 continue/stop | PASS | using-mindthus 895 bytes | 5,074 | 不给姿态，只问一个阻断问题。 |
| 完整上下文 MPG | FAIL | using＋MPG＋SELA 14,968 bytes | 15,829 | 追问 RPO，未给路径动作。 |

第二题暴露的不是无意义问题：RPO/可接受损失确实可能改变迁移判断。恰恰因为它合理，
这个失败更重要——只要 gate 足够认真，它就会把许多“产品认为应直达 owner”的任务
重新定义成欠上下文；如果让它更窄，第一题又会恢复为先给姿态。当前合同无法同时守住
这两个产品要求。

协议禁止第二次修正，因此没有全量重资格，也没有用剩余预算设计例外清单。

## 一次测试载体纠错

v1.0 Frame/Whole 题直接讨论 Codex Skill。R2、incumbent、R1 三个样本均读取了内置
`openai-docs` Skill，并各执行四次网页检索，消耗 201,145–300,129 counted tokens。
其中 R1 完全没有读取 Mindthus，仍消耗 275,010；所以不能把这三次成本归因给 Mindthus。

Mission 只做了一次协议级等量替换：改用“零件测试不能定义整机安全”的同构命题。三个
污染样本继续计入总预算，但不进入 recall、质量或 ROI verdict。v1.1 四臂都在
14,457–30,222 counted tokens 内完成，无 openai-docs 或网页检索。其余八题字节不变。

这次纠错没有改路线、门槛或结论方向；它避免把竞争系统 Skill 的成本误判成 Mindthus
成本。协议明确禁止 v1.2。

## 已证明与未证明

已证明：

1. 在本冻结面板中，删除或进一步缩小 using 入口不会自动破坏显式 owner 直达；三条
   新路线的 SELA/MPG/WAE 都是 3/3。
2. 允许一个被动 primitive miss 可以守住 2/3 recall floor；R1/R3 的 miss 本身未改变
   Frame/Whole 行动。
3. 入口拓扑仍会改变 ROI，R2 的 overall uncached median 比 ROI.2 低 16.27%；但这个
   信号不能越过行动门失败。
4. Decision Context 是当前结构的关键矛盾：没有专属 gate 时 Sol 会过早给姿态；gate
   足够强时又会在清晰 owner 任务中扩大“阻断上下文”的定义。
5. formal owner 的正文与资源级联仍是主要成本来源；把入口降到 0 并不保证更低总成本。
6. 评估载体本身可能触发 Codex 系统 Skill；只看模型答案或源码字数会产生错误归因。

未证明：

1. 任何新路线在行动质量底线之上优于 ROI.2；
2. R2 的 16.27% 中位收益可以在修正后保留；R2.1 未获准全量重资格；
3. 三个 owner、三个被动 primitive 的小面板代表真实任务总体命中率；
4. 单样本 latency 或 owner cascade 是确定性行为；
5. ROI.2 已达到发布成熟度。

## 成本与可复现性

- Generator：41 次；Judge：0 次；
- input tokens：2,496,115；output tokens：53,475；
- counted tokens：2,549,590；cached input 是 input 子集，没有重复相加；
- 36 次有效初始面板，3 次污染但计费样本，2 次 R2.1 定向配对；
- 全部调用为 `gpt-5.6-sol / xhigh`、fresh isolated `CODEX_HOME`、单 arm、只读；
- 三路线静态检查 PASS；R2.1 修正静态检查 PASS；仓库测试两次均为 619/619 PASS；
- 原始 JSONL、stderr、plugin list、summary、冻结协议和算术汇总均保留在本目录。

算术汇总见 `qualification/evidence/FINAL-SUMMARY.json`；语义判定见
`qualification/SEMANTIC-VERDICTS.json`。脚本只做路径识别与统计，不替代语义评分。

## 最终产品判断

保持当前分层：

- 1.4.6：recall-first、功能完整 Stable 基线；
- ROI.2：efficiency-first、未发布实验 incumbent；
- R1/R2/R3/R2.1：全部拒绝，不替换 ROI.2。

当前不再继续做 routing micro-patch。若未来重开，必须先做新的产品选择：是否允许
Decision Context gate 在更多 owner 任务中增加一次阻断交互，或者是否降低“欠上下文时
绝不先给姿态”的质量要求。那是价值边界变化，不是本 Mission 内还能靠技术规则免费解决
的问题。

本分支不发布、不合并、不打 tag、不创建 Issue/PR、不修改 Stable 安装，也不准备 release。
