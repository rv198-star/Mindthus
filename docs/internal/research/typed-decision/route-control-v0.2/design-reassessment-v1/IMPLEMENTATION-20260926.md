# #211 v0.3 实现接管说明

状态：**已编写代码与运行配置入口；未做测试、独立审计或新模型实验。**
用户本轮要求暂缓这三项活动；不能据此声称修正设计的工程门、E/F 小批或 A–F 比较已经通过。
主设计和执行顺序见 [REPAIR-DESIGN.md](REPAIR-DESIGN.md)。

## 本次写入的能力

`entry.run(..., mode='route-control.v0.3')` 进入 `route_control_v03.run`，沿用原
`relationship_runtime.Episode`、`Session`、方法文件绑定和当前宿主 handoff。
旧 `route-control.v0.2.1` 入口及旧账本的合同保持历史身份。

新输入 `mindthus.route-control-input.v2` 包含旧路由的有界字段，加上：

| 字段 | 要求 |
| --- | --- |
| `conversation` | 按轮次有序的 `{document_id,role,order}`，指向同包原始 user/assistant 文档；保留原作者，不把旧助手文本写成当前回答 |
| `host_inferences` | `{provenance:'host_inference',owner_ref,issue_views}`；每个事项的 actor/goal/scope 可为 null，有推断时须有原文引用 |
| `intervention` | `{turn_id,history_sha256}`；hash 为 `digest(conversation)`，一个 Episode 只在预登记的本轮介入 |
| `consumption_policy` | `advisory` 为①建议式；`committed` 为②约束式，身份在调用前固定 |

其余 `issues/dependencies/authority/task_budget` 沿用旧路由的容量、原文引用和权限校验。
`issues=[]` 时可通过当前宿主唯一 organize 槽提出最小事项；已有事项直接使用，不额外调用
组织者。方法候选、actor、goal 与 scope 始终是宿主推断，正确路线不进入运行输入。

S0 旧方法关系题与新覆盖题同批判断。新覆盖题检查**已列事项内**是否缺必要方法/直接路径，
及**原请求整体**是否遗漏一个事项；后者以 `unassigned_scope` 留下未分配范围。
②的缺失/未知限制受影响动作；①保留建议身份，原宿主可以合理改路。已由原负责人明确确认
的必要取证与前置依赖在两种方式下均保留。

实际宿主产物生成后，S1 同批检查范围/处境、局部解释的支持范围、主张来源及证据与当下
决定是否匹配。每条可处置发现拥有稳定 ID、来源引用、候选 hash 和受影响事项。
②的一次宿主回复必须覆盖全部发现：修订、原文/方法来源支持的异议或未决；修订才有一次
相关复查，异议最多使用原 Episode 的一次独立仲裁。①记录观察和实际产物，不强加逐项
处置义务。

终态 `accept_only` 只确认已绑定的产物 hash，回复不能改答案；若它调用当前 Agent，使用
已有 execution 额度。预算沿用每 Episode 四次判断、一次组织、一次修订、一次仲裁及
输入指定的执行次数。无额度、复查仍未解决或无真实宿主接收回执时保留待决状态。

## 本地配置与旧记录边界

新运行的 repo、state root、输入包和授权引用均由参数提供。`entry.py` 新增 `--repo` 与
`--prepare-admission`；准备命令只产生身份绑定的 admission JSON，不发模型请求。
它使用固定官方 TypeSafe `jev-1.13.0`，实际服务端身份仍须由将来回执确认。
准备 live admission 需要明确 `--authorization-ref`；用户暂停测试期间不执行该命令。
新 state root 在仓库外，仍绑定真实绝对路径与 Episode registry；换机器新建新运行，
不会把 OCI 账本移来修改路径或 hash。旧 runner、旧 freeze、原始失败与分数未改；
旧活动 Episode 若仍需续行，应使用它冻结的原代码环境，不能拿这次新代码摘要强行续写。

当前宿主交接回复形状由请求 schema 区分：

| 请求 | 回复核心字段 |
| --- | --- |
| `route-v03-organize-request` | `issues`, `host_inferences`, `usage` |
| `route-v03-execution-request` | 旧执行字段，①的实际方法可从已加载 canonical 方法中选择 |
| `route-v03-correction-request` | 覆盖全部 finding 的 `dispositions`、有实际改写时的 `revisions` |
| `route-v03-arbitration-request` | 每个异议的独立 `decisions` 和来源依据 |
| `route-v03-accept-request` | 各事项的接受布尔值与原产物 hash，不能带改写文本 |

所有回复仍走 `current_host.submit_response` 的同一 request ID/hash、owner、context 和
elapsed 校验，并在同一 Episode 原请求下恢复；没有新宿主模型依赖。

## A–F 准备与停止点

| 场景 | 要保留的原问题 | 本轮状态 |
| --- | --- | --- |
| A 日常处理 | 直接做与真正缺事实分开 | 新模式可表达；新来源未冻结、未运行 |
| B 单方法诊断 | 方法是否实际改变建议 | 新模式可表达；新来源未冻结、未运行 |
| C 主辅协作 | 方向判断和承载路径各司其职 | 新模式可表达；新来源未冻结、未运行 |
| D 阶段接力 | 原宿主接受前置产物后，相关后继才复查 | 沿用既有依赖接力；新来源未冻结、未运行 |
| E Skills | 两轮范围纠正与“只是提示词”推论分开 | 历史来源已定位；当前自然轨迹与新来源未运行 |
| F 4K/显示 | 物理限制与当前处境的选择分开 | 历史来源已定位；当前自然轨迹与新来源未运行 |

现存来源与缺失轮次见 [来源准备记录](SOURCE-PREP-20260926.md)。`bsc-001/bsc-002`
是暴露的开发材料；其中 `bsc-002` 的购前问法也不是 4K 原任务的逐字首问。
4K 原任务的文字轮次可按历史任务 ID 回读，原始图片当前缺失；Skills 的原始助手轮次
尚未定位。它们不能作为新来源的独立得分。E/F 首四个新家族与后续 A–F 八个家族尚未选取；
若现在为它们编造“真实新来源”，会破坏随后比较的证据边界。

五个计划条件仍是纯 Codex 复核、问题清单、Codex 观察②、Jev①、Jev②。
条件材料、当前宿主自然首答、同输入观察和真实接收尚未产生。设计中的步骤 3–6
涉及实测和验收，依用户本轮限定保持未运行；现阶段只能说**实现代码已写**，不能说
端到端方案或对照实验完成。
