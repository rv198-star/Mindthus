# Mindthus Codex Routing Convergence 终局决策报告

终局：`STOP_2X_EXPLORATION`

这轮探索没有证明 2.x 路由路线值得继续。它也不是“所有工作都白做了”：我们已经把
哪些优化有效、哪些目标没有被证明，以及失败发生在哪一层分开了。按预先冻结的停止
规则，H1 与 H2 都不能进入 Stable 对照，因此停止继续设计 H3，保留 1.4.6 作为功能
完整基线。

## 已证明什么

### H1：owner metadata 有局部价值

只收紧 owner description，确实能减少已观察到的误命中：WAE、MPG、3L5S 的边界更
准确，明确的 WAE 与 3L5S 正例仍能命中，普通和 evidence-first 任务只加载薄入口。
这说明 metadata precision 是有效的局部优化手段。

但 H1 无法保证 Decision Context 先于方向建议。修正后模型虽然不再误读 owner，仍先
给出“hold migration”再索要上下文。问题已经不在 owner metadata，因此 H1 被拒绝。

### H2：单入口资源拓扑在静态结构上可成立

H2 成功构建出：一个 Codex 可发现的薄入口、七个不可发现但可按需读取的 owner
资源、无 Hook、无 AGENTS 注入、无 defaultPrompt、无第二入口、无完整 reference
atlas。owner 正文及支持树可反向归一化到 1.4.6 冻结哈希；专项、兼容与全仓测试均
通过，三份独立只读审查最终均为 PASS。

Q1 还证明了第一轮薄入口可以被真实读取，并正确做到：不加载 index/owner、不先给
continue/hold/stop 方向，只问一个会改变答案的阻断问题。

## 没有证明什么

H2 没有通过完整资格。Q2 用精确 thread UUID 恢复会话后，宿主工作目录回到了仓库
worktree，模型同时读取了项目 AGENTS、Stable 源 Skill、方法文档、H2 源文件和最后的
候选 MPG 资源。这使 owner 命中证据被污染，不能证明候选在隔离条件下完成了同轮
entry -> index -> owner 路由。

同一调用还消耗 204,951 input + 5,062 output = 210,013 counted tokens，超过单次
200,000 的明确授权上限。冻结协议要求出现这一情况立即 `H2_REJECTED`，不得补跑。

因此本轮不能声称：

- H2 的同会话 owner 直达可靠；
- 四个被动认知原语全部保留；
- 相比 Stable，实际加载字节中位数下降至少 50%；
- uncached input tokens 中位数下降至少 10%；
- 显式 `$mindthus:<owner>` 坐标损失可以接受。

这里必须区分“未证明”和“理论上绝对不可能”。证据没有证明所有未来 Codex 宿主都
无法实现这种拓扑；它证明的是：在本 Mission 的候选、宿主生命周期、预算、修正次数
和禁止边界内，H2 无法取得可信资格，不能据此继续 2.x。

## 成本

| 路线 | Generator | Judge | Counted tokens | 结果 |
| --- | ---: | ---: | ---: | --- |
| H1 | 9 | 0 | 823,020 | metadata 局部有效，架构资格失败 |
| H2 | 2 | 0 | 238,508 | Q1 通过，Q2 隔离与预算硬失败 |
| **Mission 总计** | **11** | **0** | **1,061,528** | **STOP_2X_EXPLORATION** |

没有运行 Stable 对照，因为用户协议只允许合格候选进入对照；没有运行 Judge，因为
两臂输出从未完整。剩余预算不构成继续理由，停止条件优先于“预算还没用完”。

## 为什么现在停止

H1 已用完唯一 metadata 修正仍失败；H2 在 live 冻结后出现硬失败，协议明确禁止补跑
或再改候选；H3、Hook、第二路由层、owner 正文重写和放宽标准都在禁止范围内。继续只
能靠扩大边界或事后改门槛，无法产生当前授权内新的 decision-changing evidence。

所以最终动作是：停止 2.x 路由探索，保留 1.4.6 为功能完整基线；保留 H1/H2 分支、
构建物合同、原始 JSONL 和失败证据供未来重新立项参考；不发布、不合并、不打 tag、
不创建 Beta.3、不准备 release。
