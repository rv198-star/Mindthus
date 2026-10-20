# H1 局部 Owner 决定、候选采用与执行授权 · 实施合同 v0.2

**状态：CONTRACT_CANDIDATE / 待定向权限复核；不等于运行时代码完成。**

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

Host 从已认证 Web 事件或原主会话（包括 IM）验证：`owner_subject_ref`、`origin_session_ref`、`origin_event_ref`、`mission_id`、`request_id`、`expected_revision`、`choice` 和对应候选摘要。Host 对这一明确动作签发具有效期与唯一 `nonce` 的 scope-bound receipt；TPlan **仅验证受信签发凭据**，不相信输入 JSON 的 `actor=owner`、模型评论或普通 Q2 调用源。

候选 `tplan.owner_receipt.v0.1` 最小签名作用域：
`{issuer_id,key_id,mission_id,request_id,expected_revision,choice,candidate_sha256,origin_session_ref,origin_event_ref,issued_at,expires_at,nonce}`；签名对规范化字节做 HMAC-SHA256，验证用 `hmac.compare_digest`。Host 必须先验证来源再签，不提供模型可调用的签发工具。密钥由 Host 私有路径或受保护 fd/IPC 传递给受信内核写入口，不放 argv、Git、日志、Mission、工作区或 DSH Member 可读环境。轮换通过 `key_id` 明确选择，旧决定只保留可审计摘要，不在普通查询暴露签名或密钥。

**重要限制**：签名只证明受信 Host 签过该指令；是否来自真实 Owner 仍依赖 Host 的认证与事件绑定。H1 首版不能因为模型能调用本地 Python 就让它访问 receipt signer/secret。若部署安全边界无法隔离密钥和普通 Agent 工具，停止启用 H1 Owner 决定功能，先解决宿主边界，不能改用 `principal=owner` 补洞。

复用现有 `issue_authority_receipt` 的 HMAC 原理，**不复用其 Mission 全局 guard 及 proposal 流程**。一份 receipt 只能作用于指定的 request/revision/choice/candidate；重复事件在原 `command_id` 下返回既有结果，相反决定必须新 revision 且拒绝旧卡。撤回和新采纳也必须有同级可信证据。

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
- claim B 前必须核销当前授权轮次和候选引用；Host 耗时准备模板或创建 Session 后真正派工前需再验证有效性。若首次合法 claim 在撤回前已跨准入点，承认在途可能继续；但迟到 v2 **不得自动采用**、重启或再次派 B。
- 稳定 slot/dispatch ID 不因 API timeout、Host 重启、unknown 或更换模型重置；丢失发送结果先查询原生会话/旧回执，不盲重派。
- 终态 Mission 可在受信、幂等条件下补录先前真实 attempt 的结果事实，但不能借补录重新打开任务、覆盖已采用成果或恢复派工。
- 不可逆外部动作不因撤回而伪称已撤销；工具中止能力仍由原独立 #124 决议管理。

## 6. H1 合成验收与停止条件

第一片建议的必要验证：**V06** A 待 Owner 时 B 阻断、独立 C 继续；**V07** 不可信模型/旧CLI/伪造 receipt 不可批准；**V08** 同 request 重复/相反或过期决定及跨 Web/IM 身份绑定；**V09** 十小时 v2 在途时撤回、旧稿合法采用且不等旧执行结束；**V10** 失效 v1 只能撤回不能安全采用；**V11** 同 slot 不同 ID 的唯一 claim；**V12** 恢复/未知回执不能重派；**V13** 终态晚到结果只留档不覆盖；**V15** 旧 Mission/普通CLI/新build 兼容与发行合同。

先提交定向 fixture 和失败反例，再实施最薄内核切片，按影响范围回归；不要求每次改动执行全部历史模型实验，不在本阶段开发 Web 任务卡、真实微信或媒体 Core 对接。阶段通过须清楚区分内核合成 PASS 与真实 Host/用户交互 PASS，后者归 AIWork #158/#159。

**停止条件**：需要给 Worker 密钥才能签 Owner、必须全局 guard 才能阻断 B、Model 能通过任何旧写入口绕过人工决定、同一 Mission 出现两套可写批准事实、无法固定成果实际字节、或者准备把 Q2 普通 principal 当真用户。遇到这些必须停下并修订接口，而不是增加无证据的防御层。

## 7. 实施前的有界审查准入

定向复核仅看：1) Owner receipt 威胁模型/Host 边界；2) TPlan 原写入口是否真能统一限制 B/关闭；3) 崩溃和迟到候选是否只单一 canonical；4) 新旧 runtime 构建和其他 Mindthus 使用者是否被污染。结论 GO/CONDITIONAL GO/REVISE 和修改建议保留原文。通过后再做 H1 代码；审核不意味着生产验收。
