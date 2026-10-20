# H1 局部 Owner 决定、候选采用与执行授权 · 实施合同 v0.3

**状态：CONTRACT_CANDIDATE / 已按两份独立定向复审补充规则，待复评与运行时代码实现；不等于能力已通过。**

本版在保持 [v0.2 冻结稿](CONTRACT-v0.2.md) 原样的基础上收口定向复审中的授权信任根、nonce原子核销、旧写入口矩阵、canonical授权轮次、最终claim和局部revision。v0.2原始复审结论为安全 CONDITIONAL GO、执行时序 REVISE，原文在同批 reviews/ 目录留档；本版不把旧结论改写为GO。

上游：Mindthus [#236](https://github.com/rv198-star/Mindthus/issues/236)；AIWork #158/#156；[RFC-161 v0.2.1](https://github.com/rv198-star/aiwork/blob/8d9c7981d99092a951f31cb51f55c151ee2d6c5d/docs/design/RFC-161-TPLAN-DSH-RUNTIME-v0.2.1.md)。Q2 源码基线：Mindthus `a31847265a248a9a50d6536f7a12524e78783f1a`；前置草案 `b310c4dfc1bdbcf9af768faa3520766fbd53ec48`。本稿细化并拟替代前述草案中的候选字段；原草案和历史结果保留，不覆盖。

## 1. 最小可用闭环与权限边界

核心路径：保存阶段 A 的不可覆盖成果 v1 → Coordinator 开立**仅针对后续 B 的**人工决定 → B 等待、无关 C 可以继续 → 可信 Owner 确认特定候选 → **TPlan** 在短事务中记录决定和影响范围 → **AIWork Host** 以单次合法授权轮次 claim B、创建原生 DSH 执行并收回执 → 成果晚到时按当前决定判断采用。

必须维持三种不同事实：
1. `owner_decision_committed`：TPlan 已合法记录业务决定，不等于执行已停止、开始或结束。
2. `execution_claimed`：某个业务 Task / 授权轮次的执行权已发出，不等于 DSH 已受理。
3. `dispatch_receipt`：Host 真实投递返回，`unknown` 不是“未执行”，不允许换 ID 重派。

普通评论不会形成决定；普通 Q2 `principal` 只是调用者标识，不构成用户权限。工具提权仍走 DSH/AIWork 原主会话授权 #137；此处的人工作业批准绝不自动提权。#124 **在途暂停/取消继续 HOLD**。

## 2. 唯一 canonical 状态及持久化

仅**显式启用 H1 的新 Mission** 添加 `human_control` 扩展，单写权威归同一 TPlan Mission/事务，不新建一份 Host 审批库、状态机或事件总线。旧 Mission、Q2-only Mission 保持原 fixed writer/schema，不迁移/回填，不热改指纹。

建议的精确对象草案（字段名可在正式编码前微调，但语义与约束不得偷换）：

```json
{
  "human_control": {
    "schema_version": "tplan.h1.v0.1",
    "requests": {
      "HR1": {
        "business_task_id": "A",
        "blocked_task_ids": ["B"],
        "status": "pending",
        "revision": 1,
        "required_actor": "owner",
        "allowed_choices": ["approve_current", "request_changes", "withdraw_change"],
        "current_candidate_id": "CA1",
        "current_decision_id": null
      }
    },
    "candidates": {
      "CA1": {
        "task_id": "A",
        "attempt_ref": "attempt-A-1",
        "content_sha256": "sha256:<64hex>",
        "bytes_ref": "artifacts/h1/<content-id>",
        "validity": "eligible"
      }
    },
    "decisions": {},
    "execution_slots": {}
  }
}
```

- `requests` 绑定单个业务任务、特定候选和明确的阻断依赖；不同任务可各自等待。不得用 Mission 全局 `interaction_guard` 挂住数小时。
- `candidates` 保存内容身份与**可取回实际字节**。候选先写入可信 Host 控制、普通 Member 不可覆盖的 Mission 专用内容寻址存储，经 SHA 和原子创建/核验后登记引用；同名旧稿不得被覆盖。若宿主目前无法完全禁止 Member 改写存储，至少要求采用/续接时重新验 SHA，并明确标记该能力尚未满足正式上线准入；缓存失效或字节不匹配时拒绝采用，不将 hash 当可恢复文件。
- `decisions` 保存已生效决定、精确 request/revision/choice、被采纳候选、可信来源事件引用、时间及请求摘要（**不保存签名密钥、token 或用户消息正文**）；它是业务权威记录，不是每条聊天副本。
- `execution_slots` 的唯一键为 `(MissionId, BusinessTaskId, AuthorizationRound)`；保存稳定 dispatch intent/attempt binding 和回执引用。**两个不同 command_id 不允许 claim 同一 slot**，重启/结果未知不释放。
- `status` 只能经受信命令与原事务转换；同一个请求旧 revision 的卡片不得覆盖新决定。
- 所有 H1 状态变更均借现有短锁、持久准备日志和前滚恢复；不能另开临时 JSON 旁路写入，不能在一条耗时执行期间持有事务锁。
- 初片只需 1 个 A、1 个局部 request、1 个 B、独立 C 的合成 Mission；不做通用流程设计器、多用户 ACL、大规模历史迁移。候选数量/文件大小为有限上界，具体配额在第一片性能/磁盘证据后确定，不以自动删除用户成果应对容量不足。

## 3. 真正可信的 Owner 证明（最重要的安全合同）

Host 从已认证 Web 事件或原主会话（包括 IM）验证：`owner_subject_ref`、`origin_session_ref`、`origin_event_ref`、`mission_id`、`request_id`、`expected_revision`、`choice` 和对应候选摘要。Host **只依据不可由 Agent 选择或伪造的已认证事件**机械确定上述事项并签发具有效期与唯一 `nonce` 的 scope-bound receipt，不能变成模型可任意选择 request/choice 的签名 oracle。TPlan **只依据固定受信 Host 信任配置**校验签发方及密钥，不相信调用者给的 secret/key_path、输入 JSON 的 `actor=owner`、模型评论或普通 Q2 调用源。

候选 `tplan.owner_receipt.v0.1` 最小签名作用域：
`{issuer_id,key_id,owner_subject_ref,origin_binding_ref,mission_id,request_id,expected_revision,choice,candidate_sha256,origin_session_ref,origin_event_ref,issued_at,expires_at,nonce}`；签名对规范化字节做 HMAC-SHA256，验证用 `hmac.compare_digest`。Host 必须在**已认证原会话/网页事件**中核对真实 Owner 主体、请求对象、决定选项和候选摘要后签名；工具授权事件/“同意”自由文本不能作为 H1 确认。签发器不暴露给模型或普通 CLI。验签时 `issuer_id/key_id` 仅用于从**Host 预先固定、Agent 不可改写的信任表**中选择允许的密钥，绝不能让本次调用带入“指定 secret”或密钥路径。密钥必须位于 Member/普通工具不可读取的独立权限域，通过受保护 fd/IPC 或固定的受信进程处理；不能因为文件叫 private 就当作已经隔离。密钥不放 argv、Git、日志、Mission、工作区或 DSH Member 可读环境。轮换通过 `key_id` 明确选择，旧决定只保留可审计摘要，不在普通查询暴露签名或密钥。

**重要限制**：签名只证明受信 Host 签过该指令；是否来自真实 Owner 仍依赖 Host 的认证与事件绑定。H1 首版不能因为模型能调用本地 Python 就让它访问 receipt signer/secret。若部署安全边界无法隔离密钥和普通 Agent 工具，停止启用 H1 Owner 决定功能，先解决宿主边界，不能改用 `principal=owner` 补洞。

复用现有 `issue_authority_receipt` 的 HMAC 原理，**不复用其 Mission 全局 guard 及 proposal 流程**。一份 receipt 只能作用于指定的 request/revision/choice/candidate 与 Owner 主体/原事件。**在同一 canonical 短事务里**校验允许的 issuer/key、签名、时间窗（Host可信时钟及受限 skew，拒绝过期和异常未来时间）、expected revision、nonce 是否未核销，并将 nonce→decision_id、决定结果、下一 revision 一起提交。首次成功的任何决定——包括“撤回成功但旧稿采用被阻断”——都必须推进 revision。已提交的重复 command_id 只返回历史结果；相同 receipt 换 command_id 不能再次提交；nonce/issuer/choice 复用冲突或旧 Web/IM 卡一律拒绝。事务准备后恢复只前滚这一次决定，不重复核销或另签新授权。撤回和新采纳都必须有同级可信证据。

## 4. 最小命令与唯一写入边界

| 命令候选 | 调用权限 | 必须检查/结果 |
|---|---|---|
| `candidate.submit` | 合法受管 Agent 的 Host 回执 | 保存不可变实际字节并核验 attempt，**不是采用** |
| `decision.open` | 可信 Coordinator/Host | 明确 A 的候选和被阻断的 B，生成 revision；不会冻结 C |
| `decision.apply` | **可信 Owner scope receipt** | 短事务验证身份、revision、choice、候选有效性；撤回与采用分别返回真实结果 |
| `execution.claim` | 受信 Coordinator/Host 调用 | 针对特定 Task+授权轮次短事务检查当前决定、依赖、唯一 slot；返回稳定 dispatch intent |
| `receipt.record` | 绑定原 Host dispatch 的受信回执 | 记录 sent/unknown/accepted/delivered，重复幂等；无权造新 slot |
| `adoption.apply` | 受信 Coordinator/Host | 依据当前决定和候选身份采用，拒绝旧 attempt 最后返回即覆盖 |
| `snapshot.get` | 原受控查询入口 | 只读展示待人事项摘要、当前采用与阻塞原因，不暴露 Owner 原始消息 |

默认旧 `record_evidence.py`、`set_task_status`、`set_mission_status` 等仍可做**无关的合法操作**；但对 H1 控制的 B 或 Mission 完成，不能通过普通 `acceptance_passed`、自行 `completed`、直接替换成果引用、旧 Host admission 或模型提到“用户已经批准”来绕开。需要在**原 `_commit_mission_state_unlocked`、受影响 evidence writer、Mission-close 路径和 Host dispatch admission** 的共同权威边界上交叉检查。无关 C 的进度与观察记录必须可继续；不能为了拒绝 B 而禁掉所有写操作。

**写入口矩阵必须在编码前列出**：TPlan `append_event`、`record_evidence.py`、`commit_mission_state`、普通任务状态、Mission-close、所有已允许的 Host direct mutation；AIWork `coordinator-tplan-ops/gate/admission/dispatch/round`。对于首次能力切片，无法验证防绕过的入口必须 fail-closed 而非假装已被 gate 保护。H1 内核通过之前，AIWork 不开启任何生产 H1 Mission。

## 5. 取消修改、成果采用与极端时序

用户可以**立即撤回修订意图**，不等待 v2 Agent 完工；这不等于 v2 的工具已取消。如果 v1 仍在、字节可读、未被新事实判为失效、相关独立依赖和权限仍有效，则可在当前决定已提交后按 v1 继续。若 v1 不再有效，`withdraw_change` 可被接受，但采用旧稿/放行 B 必须单独保持拒绝，并准确说明原因，不得把撤回意图强行回滚。

- `decision.apply` 同时提交“撤回成功 + 采用受阻原因”是允许的业务结果；不因不能立即采用旧稿而把撤回本身锁住。
- Web/IM 同一 request 的相反选择以 expected revision 条件提交，不能靠最后到达的文字覆盖；重复同一决定返回原结果。
- **慢准备在最终 claim 前**：Host 先完成无执行副作用的模板选择、只读状态/候选检查与输入计算；然后由 TPlan 在最后一次短事务中进行**唯一授权 claim**，同时固定当前 task+canonical round、候选/依赖摘要、dispatch intent ID、稳定原生 session/request 绑定和 CommandResult。此后 Host 才允许开始具有副作用的 Session 创建/真实派发。发起真实派发前如可证实 claim 已被撤回且没有外部副作用，应标注原 slot 未发送并由合法新决定产生新轮次；若实际派发/回执未知，则沿原 slot 查询，不能换号重派。已经跨合法 claim 点的旧执行可能仍然运行，但迟到 v2 **不得自动采用**、重启或再次派 B。
- 稳定 slot/dispatch ID 不因 API timeout、Host 重启、unknown 或更换模型重置；丢失发送结果先查询原生会话/旧回执，不盲重派。
- 终态 Mission 可在受信、幂等条件下补录先前真实 attempt 的结果事实，但不能借补录重新打开任务、覆盖已采用成果或恢复派工。
- 不可逆外部动作不因撤回而伪称已撤销；工具中止能力仍由原独立 #124 决议管理。

## 6. H1 合成验收与停止条件

第一片建议的必要验证：**V06** A 待 Owner 时 B 阻断、独立 C 继续；**V07** 不可信模型/旧CLI/伪造 receipt 不可批准；**V08** 同 request 重复/相反或过期决定及跨 Web/IM 身份绑定；**V09** 十小时 v2 在途时撤回、旧稿合法采用且不等旧执行结束；**V10** 失效 v1 只能撤回不能安全采用；**V11** 同 slot 不同 ID 的唯一 claim；**V12** 恢复/未知回执不能重派；**V13** 终态晚到结果只留档不覆盖；**V15** 旧 Mission/普通CLI/新build 兼容与发行合同。

先提交定向 fixture 和失败反例，再实施最薄内核切片，按影响范围回归；不要求每次改动执行全部历史模型实验，不在本阶段开发 Web 任务卡、真实微信或媒体 Core 对接。阶段通过须清楚区分内核合成 PASS 与真实 Host/用户交互 PASS，后者归 AIWork #158/#159。

**停止条件**：需要给 Worker 密钥才能签 Owner、必须全局 guard 才能阻断 B、Model 能通过任何旧写入口绕过人工决定、同一 Mission 出现两套可写批准事实、无法固定成果实际字节、或者准备把 Q2 普通 principal 当真用户。遇到这些必须停下并修订接口，而不是增加无证据的防御层。

## 7. 实施前的有界审查准入

定向复核仅看：1) Owner receipt 威胁模型/Host 边界；2) TPlan 原写入口是否真能统一限制 B/关闭；3) 崩溃和迟到候选是否只单一 canonical；4) 新旧 runtime 构建和其他 Mindthus 使用者是否被污染。结论 GO/CONDITIONAL GO/REVISE 和修改建议保留原文。通过后再做 H1 代码；审核不意味着生产验收。


## 8. 定向复审收口的具体实现约束（v0.3 新增）

### 8.1 权限信任根、防重放与时间窗

- `issuer_id/key_id` 从 Host 在此 Mission 被创建/托管时的可信签发器配置固定；receipt 声明 key ID **不是**允许客户端上传新信任根。签发端与验签端都不得从 CLI 参数选取新 secret 或受信目录。未经证明可隔离 Host 私钥于 Agent/Member OS 身份之前，只能离线做合成验证，不允许启用真实 Owner H1 决定。
- `owner_subject_ref` 必须由 Host 实际认证映射得到，并与原 Mission owner/origin 绑定；`origin_event_ref` 必须来自已认证动作且能证明明确的 request/revision/choice/candidate 选择。网页时间、普通消息文本、模型自行组织的 `actor`、工具审批事件均不能提供同等来源。
- 签名正文规范化（键排序、UTF-8、确定性 JSON）和时间窗由一个受版本约束的 Host/Kernel 合同决定；验签不接受未定义字段。首次提交核销 nonce + command + request revision + 当前决定；仅回放同一已提交结果，不创建第二笔批准。
- 如果新决定成功记录了撤回但旧稿无效，事务仍把“撤回生效/采用受阻/阻断 B 的原因”一起写入并提升 revision；旧卡、旧 receipt、同 nonce 换 command 均不能在此后偷偷批准旧稿。

### 8.2 原生写入口矩阵与当前 before-state gate

**只允许 H1 专用受信 handler 更改 `human_control`、候选采用、阻断关系或授权轮次。** 通用 `commit_mission_state` 和原 `_commit_mission_state_unlocked` 必须从**提交前状态**及固定 H1 runtime capability 识别受控 Mission，禁止通过将 `human_control` 从 after 删除、改 blocked 任务ID、降级任务角色/依赖、伪造 `completed` 或改变成果引用来绕过。首片中不支持可信重规划这些 protected 对象时，明确拒绝重规划，并保留 C 正常执行。

| 真实已存在的入口 | 受控 H1 必须保护的最小条件 | 与 H1 无关时 |
|---|---|---|
| `tplan_runtime._commit_mission_state_unlocked / commit_mission_state / transition_task_status` | before 中的待决、blocked B、候选和轮次不能被一般状态修改删除或绕开；受控 B 不得越过 gate 变 active/completed | C 可正常改变状态及普通计划 |
| `tplan_runtime.append_event` → `record_evidence.py / checkpoint.py` | `acceptance_passed`（或会让受控 B/最终交付被视为批准的记录）不能替代 Owner 决定；保护在锁内、针对具体 Task/AC，不全局拒绝 observation | C 与无关 A 的合法普通证据继续 |
| `Mission-close / _mission_completion_findings` | 存在未合法解除的 H1 待决、缺少当前采用/有效执行授权时，不能仅凭其它 acceptance 关闭 Mission | 不含 H1 的原规则不变 |
| `append_step_log / start_execution_span / append_execution_trace_record` | 允许受信补记属于已合法 attempt 的事实，但不藉任何日志事件打开 B、claim 新轮次或采用成果 | C 正常记录，终态记录按原规则 |
| `coordinator-tplan-ops/gate/admission/dispatch/round` | 凡准备启动受控 B 的原入口必须强制核对 H1 scoped claim，而非只拿旧 Mission 全局 hash 或模型文本成功；已有 ledger 做技术回执，不再写第二套批准 | 非受控新旧 Mission 按其旧合同运行 |

本矩阵是实现约束和复核清单，不宣称上述入口现已加 H1 保护；新增代码前先写这五组对应的绕过失败用例。无法证明某个合法写入口不会跨越 B 的，H1 enabled Mission 必须在该入口 fail closed。

### 8.3 授权轮次和唯一 final claim

- `AuthorizationRound` **只能由 TPlan** 基于明确的业务决定/候选/依赖变化创建或推进，不能取自 Host requestId、模型 attempt、DSH roundId。对同一 B 的同一合法执行目的反复查询/重启/换 command_id，必须复用原 round。
- 合法新 Owner 决定可能将旧候选标过期，但新一轮 B 执行必须由内核在短事务中明确生成新轮次、保留旧 slot 记录；不得因旧 slot 回执未知就重新开相同目的轮次。纯 C 记录不会增加 B 的轮次。
- **最终短事务 claim 才是准入生效点**。commit 同时固定 `(Mission,B,Round)`、真实输入 digest、合法候选及依赖投影、稳定 dispatch intent/session 请求身份和命令结果。Session 创建与 prompt 发送在它之后，需使用同一稳定身份；从原 Host ledger、TeamSessionStore 和 canonical slot 对账，不能以 API 超时推断未派。
- 如果在“慢准备后、final claim 前”发生撤回，则 claim 读取**当前**决定，不得按准备时的旧意见派发。claim 后若决定变化，系统承认已授权旧执行可能存在；能明确证明未发送才允许标示 `not_sent/superseded`，未知则仍占 slot 等待核实，不能靠重新申请一个新 ID 绕过。

### 8.4 全 Mission revision 只能作为快照一致性提示

AIWork 已有 `coordinator-tplan-gate` 对 mission/evidence 的整体验证摘要及 `coordinator-dispatch` 的旧 revision 对比，**不得直接把它当作 H1 业务授权长期有效性的唯一 key**。H1 采用局部 `request.revision + adopted candidate digest + B 的直接依赖/关联验收 projection + authorization_round` 作为条件提交；C 的无关写入最多触发重读，不可让已合法 B slot 失效、触发重复审批或重派。真正的相关变化必须在下一次 final claim 或 adoption 时拒绝过期令牌。

旧全局 revision 逻辑对**非 H1** 按原样保持；AIWork #158 需在真实调度路径将 H1 scoped token 纳入 Host 适配，不通过直接改旧 gate 全局计算规则来掩盖差异。

## 9. 实施期接受测试与必须停止的范围

在 v0.2 的 V06–V15 合成集合之上补充四组“首片前可见失败”夹具：
1. 无权调用者自选 secret/key-path、伪造 Owner/IM/工具审批、换 command_id 重放已核销 nonce、旧 revision 重新确认 → 全部拒绝且无业务状态变化。
2. 普通 writer 试图移除 human_control、移除受控 B、改角色/依赖、直接记录通过验收或关闭 Mission → 全部拒绝；独立 C 的普通证据与任务进度成功。
3. 同一决策状态下多个 Host roundId/requestId 并行 claim B → 一份 canonical slot；准备期间发生撤回则 final claim 采用新决定，不依据已读旧快照放行。
4. C 在 B 合法决策后写入普通 observation → 全局 hash 可以变化，但 B scoped claim/已存在 slot 不被错误撤销；未知 dispatch 回执恢复后只能查询既有 slot，不重复派发。

保留既有兼容性/发行边界与安全禁区：**不创建 Host 第二批准表、不把 Q2 普通 principal 升格成 Owner、不把业务撤回当取消原生工具、不迁移旧 Mission、不解除 #124 HOLD**。本稿只收口合同；具体签发器隔离、跨语言 HMAC 与旧写入口的真实代码验证还未完成，不以这些设计文字宣称线上 PASS。
