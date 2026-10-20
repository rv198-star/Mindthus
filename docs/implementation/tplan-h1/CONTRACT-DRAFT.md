# H1 · TPlan 局部人工决定与成果采用：实施合同候选 v0.1

**状态：PRE-IMPLEMENTATION / 尚未冻结正式 Schema；仅 H1 #236 的规格草案，不是已实现能力。** 依据 AIWork RFC-161 v0.2.1、Mindthus Q2 #235（main 合并 a31847265a248a9a50d6536f7a12524e78783f1a）及 AIWork #158。H1 在通用 Mindthus/TPlan 内核中演进；DSH/AIWork 负责可信 Owner 来源及执行事实，媒体 Core 保持自身业务采用事实。#124 在途暂停/终止仍 HOLD。

## 1. 原生能力与真正缺口

- Q2 已提供 opt-in 的新 Mission 构建、短时事务、证据和 CommandResult 同事务、原命令重放/显式恢复。这是技术底座，不是任何 Owner 审批能力。
- 旧 TPlan 的 authority receipt 依赖 **Mission 全局** interaction guard 处于 awaiting_authority，签署内容与一次 proposal/较晚收到的确认关联。**不能直接拿该 guard 长期表示局部待办**，否则误阻塞独立 Task。
- Q2 普通 principal 是普通请求来源，不是 Host 身份认证，不允许被模型写作 owner。DSH 原生 TeamTaskBoard 的成员工具完成也不是 TPlan 的人工作业批准。
- 因此 H1 要增加 **任务范围的业务待决对象** 与可信决定验证，复用现有事务，而不是复制运行状态机、为每条评论开全局 guard，或引入新数据库。

## 2. 最小 canonical 对象（字段名为候选，先证实可行）

仅显式启用 H1 的 **新 Mission** 才允许出现可选 `human_decisions` 扩展，且由一套 TPlan writer 更新；旧 schema/旧 writer 不得写入，已存在的其它 Mission 不回填。Q2 命令结果独立保留。

一个局部请求含：`request_id`、`business_task_id`、`artifact_ref`（引用可恢复的实际字节、内容 SHA 和生成 attempt）、`required_actor=owner`、`allowed_choices`、`decision_revision`、`affected_downstream_task_ids`、`pending_or_decided`。不需要独立的“人类任务板”；看板由这份记录投影。普通 Team task、模型评论不自动生成该对象。

Owner 决定记录含：`decision_id/command_id`、`request_id`、`expected_decision_revision`、`selected_choice`、`selected_artifact_ref`、可信来源 receipt 摘要、`committed_at`。**用户更改主意要使用新命令/新 revision；旧回执重放是历史成功，不是当前决定。**

执行授权按 `execution_slot=(Mission, businessTask, canonical授权轮次)` 唯一绑定 intent/requestId/固定输入。不同 commandId/attempt 不能绕过同一 slot。已授权的旧 attempt 即使晚到，只能按当前采用规则决定是否成为业务成果；原生 running/completed 仍属 DSH。

## 3. 真正的 Owner 身份：沿用信任方式，不沿用全局 guard

- **Host** 从已验证 Web 登录或原主会话（含 IM）事件取得可信原始消息、身份和 origin；确保用户动作准确指向一个 Request/选项/当前 revision。
- **TPlan** 验证针对该 Request 的 scoped authority receipt：覆盖 Mission+requestId+revision+choice+artifact digest+Origin event Ref+签发/有效性，安全凭据始终由可信 Host 保管，不进入 Mission JSON/模型提示/日志。
- 旧 `issue_authority_receipt()` 绑定全局 guard 与 proposal，不应直接挪用；可借鉴其 HMAC/签名核验的思路，但需在此局部对象上设计新的证明与验证合同。模型填写 `actor=owner`、伪造确认 Ref 或 Coordinator 自述“人已同意”，均不生效。
- 工具权限审批仍由 DSH 原既有 #137 链路负责。业务确认不能带来工具提权；普通 Codex/advisory 场景维持旧自主合同，没有可信 Host 则不伪称已能解决 Owner 待办。

## 4. 最小命令切片与状态生效

| 命令/动作（拟名） | 允许行为 | 不允许行为 |
|---|---|---|
| `decision.open` | 受管 Coordinator 建立唯一局部待决事项，冻结候选与相关依赖 | 直接以“需人确认”为由暂停整个 Mission |
| `decision.apply` | 校验 Host receipt、Request/revision/选项/旧成果有效性，短事务记录当前决定 | 把提交消息/讨论当作批准；以长锁等待在途任务 |
| `candidate.submit` | 可信 attempt 登记不可覆盖的实际成果引用 | 以最后返回结果覆盖当前采用 |
| `adoption.apply` | 按**当前**决定与成果指纹采取某候选，区分撤回意图与采用成功 | 将历史成功回执表述为当前批准 |
| `execution.claim` | 先核对合法依赖/当前决定，再短事务记唯一 execution_slot 授权 | 任意 requestId 或失败后换号重复发起 |
| `receipt.record` | Host 以原请求 Ref 记录已发送/未知/完成事实；终态后允许受信、幂等补记迟到结果 | 重开 Mission、重派工或自动放行 |

只使用 Q2 统一命令结果/短时恢复合同的可复用部分，但不要把 `evidence.record` 的普通权限扩大成 `decision.apply`。新 schema/能力只在新 H1 build 中显式 opt-in，旧 writer 拒写而不是暗中升级。

## 5. 不同顺序的真实语义

**正常**：A 的成果已保存 → 提出局部待办 → 依赖 A 的 B 不可 claim → 独立 C 继续 → Owner 在原会话/卡片确认特定成果 → B 在 current revision 下合法 claim，DSH 执行回执与业务允许执行分开。

**十小时反悔**：v2 attempt 已开始 → Owner 撤回这次修改并指定仍有效 v1 → 新决定短时提交 → B 可按 v1 继续（前提是其它依赖和权限仍满足），不用等 v2 → 迟到 v2 记录为未采用候选，不能覆盖 v1、重派或重复通知。旧稿已失效时，撤回意图可成功但“采用旧稿”仍拒绝，显示具体原因。

**并发/失败**：同一 Web/IM 决定重复送达只返回原结果；旧确认卡 revision 冲突不隐式覆盖；claim 与撤回交错按提交先后处理，但 claim 已发生的在途执行不能伪称已被取消；Host 收不到投递结果则保持 unknown，按原 slot/requestId 查询而不换 ID。

## 6. H1 第一片最小验证（V06–V13/V15 的有界选集）

先做一个合成 Mission：A→人工待决→B，独立 C。依序验证待决只挡 B、C 不受阻；模型普通 CLI 不能绕过 owner gate；两来源重复、相反与过期决定；可恢复旧稿存在真实内容；撤回无需等十小时 attempt；旧结果不可覆盖；同 slot 不同 ID；崩溃/不确定回执保守；终态受信迟到只留档；老 Mission/old CLI 原行为不退化。

**上线前必须完成的设计细节**：Host receipt 的可信签发/核验载体、作用域与防重放；canonical 的精确字段和原子提交点；成果引用的字节保留与容量预算；所有受支持旧写入口的 gate 一致性。经一次有界安全/权威接缝评审后再写 H1 核心；不预设全部采用本稿字段，也不做全量历史迁移、替换 DSH 引擎、另建队列或进入产品 UI/媒体集成。

## 7. 分工、发布与停止条件

Mindthus #236 只负责通用规则和合成正确性；AIWork #158 才负责真实 DSH/Web/IM Owner 身份与现有 dispatch/receipt 关联；#159 负责看板任务讨论和人工处理卡；Mindthus #238 评估正式发行，产品 dev/prod 部署另授权。若发现需要双写 canonical、必须常驻全局 guard 才能阻断 B、或非 Host 可信请求能自行批准，则**暂停编码并修订方案**，不靠增加认证字符串补洞。
