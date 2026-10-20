# H1 scoped Owner 与执行准入 · 独立审查证据

**状态：设计合同复核完成；尚无 H1 运行时代码或真实 Host 安全验收。**

**受评对象与固定指纹：**
- v0.2 `CONTRACT-v0.2.md`，commit `5761821dd2384522c3e07bcf0e46f56ab7ffb11e`，SHA-256 `67325df84a06702d7c8f533ac545d5c250e2aba4c140d98476ae7af5581cf8ff`
- v0.3 `CONTRACT-v0.3.md`，commit `f4ce1caf8a77a3cae815da3e8c47c4ac700acd29`，SHA-256 `d16e00fedcf81d7a3fd0ab698bba1c5e400196851b9597df18f631c791b9f3b7`
- v0.3.1 `CONTRACT-v0.3.1.md`，commit `62927a18ea72124083866adcc40d1853ec4c1c95`，SHA-256 `d7e304508a67d64b603ba1f9d79800eb9501ea56c6fca8d4a59775287ccdffd9`

**方式**：OCI 两个隔离的 Codex ACP 会话，事先分别指定权限/安全和 Mission/执行时序角度；各自完整阅读同一冻结合同并计算 SHA，对照必要 TPlan、AIWork 源码。原始评审互不交换意见，差异复核由原审阅者分别进行。这不是两名真人或不同模型，也不是已完成真实 DSH 安全测试。

## 结论与最小处置

| 受评版本 | 权限与身份 | Mission执行时序 | 准入裁决 |
|---|---|---|---|
| v0.2 | CONDITIONAL GO，3条 P1 | REVISE，4条 P1 | 方向保留，不能直接编码 |
| v0.3 | GO，原 3 条均关闭 | CONDITIONAL GO，原4条中3关闭1部分解决 | 仅补旧 claim 发送者竞态 |
| v0.3.1 | v0.3安全条款未改变 | **GO，唯一剩余 P1 已关闭** | 设计合同可作为首个**合成实现切片**依据 |

**最后一项采用做减法**：首片**不支持**在 claimed slot 的发送结局未知时，以“尚未观察到发送”为由将其标为 `not_sent/superseded` 并开启替代派工。Owner 仍可立即撤回业务决定，旧候选不得自动采用；但同一执行目的的新物理派发须在旧 slot 可核查之前保守等待或明确安全阻断。此举避免为了首版增加复杂的 Host sender fencing 服务，并不等于释放/暂停已在途工具。#124 HOLD 保持。

**实施期必须真实验证**：Host 签发者的 OS/权限隔离、origin 认证、HMAC/nonce/revision 并发核销、legacy evidence/状态/Mission-close 入口防绕过、A/B/C 局部准入、唯一 slot、外部派发丢回执及迟到候选。当前所有这些属于设计要求，**未测试、未部署**。

## 原始独立审查全文与差异确认

### 1. 安全/Owner身份 · v0.2 原文审阅

**ACP Session**：`acps_98b7aa22fd50dee919246bdb`

**（1）校验与结论：CONDITIONAL GO**

已完整阅读固定合同、对照前版草案，并只读检视指定源码。两次 `sha256sum` 均为：

`67325df84a06702d7c8f533ac545d5c250e2aba4c140d98476ae7af5581cf8ff`

Mindthus HEAD 与指定 commit `5761821dd2384522c3e07bcf0e46f56ab7ffb11e` 一致。AIWork 源码取自本地 `aiwork-dev`，HEAD 为 `de83344ac8a546becd605aa18f465902ed578fa9`。

整体设计可以继续；下列三项须在首个运行时代码切片前补成明确规则。它们是接口合同缺口，不是已证实的现网漏洞。本次未修改文件、Git、issue 或配置，未运行产品任务、调用网络模型，也未读取其他审阅者结论。

**（2）必须修订的三项**

1. **P1：核验器的信任根不能来自本次调用参数。**  
   位置：[§3，签名与密钥传递规则](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/docs/implementation/tplan-h1/CONTRACT-v0.2.md:65)。合同规定“受信签发凭据”，但没有明确 `issuer_id/key_id` 如何映射到受信密钥。旧 [tplan_runtime.py:1203](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/skills/tplan/scripts/tplan_runtime.py:1203) 的签发与核验均接受调用方提供的 secret，这只能作为密码学机制参考。  
   **反例：**普通 CLI 自选 secret、自签 receipt，再把同一个 secret 或其文件路径交给核验器；HMAC 正确仍不能证明 Owner 身份。  
   **一句最小解法：**规定 H1 核验密钥仅从 Agent 不可修改的 Host 信任配置按允许的 issuer/key 查得，普通调用不能指定 secret、密钥路径或信任配置，持有 HMAC 密钥的核验进程也必须处于普通 Member 工具域之外。

2. **P1：真实来源到具体动作的绑定还需明确，防止签发器成为 signing oracle。**  
   位置：[§3，Host 来源验证流程](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/docs/implementation/tplan-h1/CONTRACT-v0.2.md:65)。待验证字段包含 `owner_subject_ref`，签名作用域却没有它或等价的受信绑定标识。现有 [owner helper](/srv/agentdock/projects/aiwork-dev/plugins/workbench/coordinator-owner-identity.js:3) 检查原会话、事件和来源字段；[approval broker](/srv/agentdock/projects/aiwork-dev/plugins/workbench/coordinator-approval-broker.js:120) 允许单个待办时省略引用。这些不能直接承担 H1 的候选级确认。  
   **反例：**Owner 原本对另一个工具审批说“同意”，Agent 随后选择 H1 request、revision 和候选，请 Host 对这些参数签名；或者伪造 Web `rpcId/clientTimeZone`、IM channel 外形，被误当成认证来源。  
   **一句最小解法：**规定 Host 从不可由模型伪造的认证入口和既有 Mission 来源绑定中取得主体与精确事件，机械绑定该事件明确确认的 request/revision/choice/candidate，并签入主体或受信绑定标识，来源映射或意图不明确时拒签。

3. **P1：nonce、revision、过期与幂等的联合规则尚未闭合。**  
   位置：[§3，重复事件规则](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/docs/implementation/tplan-h1/CONTRACT-v0.2.md:72)及 §5。已有唯一 nonce、有效期和旧 revision 拒绝，但未明确核销点、所有成功决定是否推进 revision，以及更换 command_id 后如何处理。  
   **反例：**同一 receipt 被包装成两个 command_id 并发提交；或“撤回成功但采用受阻”没有推进 revision，旧批准卡随后仍能成功。仅返回原 command_id 的结果不足以排除这些情况。  
   **一句最小解法：**规定首次提交在同一事务内检查时间窗和 expected revision、核销 nonce、绑定来源动作到唯一命令并推进 revision，已提交重放仅返回历史结果，恢复已准备事务不重新产生授权，未知 issuer/key、过期、异常未来时间及冲突重用均拒绝。

**（3）留给实施期验证，不必扩写成完整文档**

上述修订只需短规则和接口约束；以下应以 fixture、入口矩阵和运行证据证明：

- Member 实际无法读取密钥、继承受保护 fd、访问签发 IPC 或修改信任配置；“私有路径”本身不构成隔离证据。
- Web/IM 的认证身份、原会话和内部回传排除真实贯通；现有精确原生 Agent 检查、可信来源解析应保留。
- 按 §4 完成写入口矩阵，验证普通 Q2 principal、旧 CLI、evidence、Mission-close 和 Host admission 都不能绕过 B，同时 C 可继续。
- HMAC 跨语言规范化、字段篡改、密钥轮换、并发核销、崩溃恢复和过期边界测试。

合成 PASS 不证明真实 Host 身份链 PASS；后者仍由 #158/#159 提供证据。

**（4）一条最小合成验收时序**

未来用**假时钟、隔离测试密钥、认证入口 stub、派工计数 stub**执行，不接真实用户或 DSH：

1. 保存 v1 实际字节，开立 A→待决→B；断言 B 拒绝 claim，C 可写进度。
2. 普通 Q2/CLI 分别尝试 `principal=owner`、自选密钥、伪造 Web/IM 来源、借用工具审批事件、直接请求签名；全部拒绝且状态不变。
3. 可信 Owner 请求修订，提交后启动模拟十小时 v2；随后生成“撤回修改并采用 v1”的精确事件。篡改候选、跨 Mission、过期和未知 key 的 receipt 均拒绝。
4. 合法撤回在事务准备后模拟崩溃，再恢复；断言只提交一次、revision 推进、采用 v1，v2 仍在途且 C 可继续。
5. 原命令重放只返回历史结果；换 command_id 重用 nonce、旧 Web/IM 相反决定均不能改变当前决定。
6. B claim 后模拟投递 unknown、重启；断言换 ID 不能再次派工。迟到 v2 只留档，不覆盖 v1、不重派；终态补录同样如此。

**（5）值得保留，以及刻意不做的事项**

保留 TPlan 单一业务权威、局部待人和短事务；保留决定、claim、真实投递三种事实；保留候选实际字节及不可覆盖身份、稳定 execution slot，以及“撤回成功”和“旧稿可否采用”分开表达。这些直接回应用户随时撤回十小时修订、继续采用有效 v1 的需求。

继续保持 Worker 不直聊 Owner、业务确认不授予工具权限，不替换 DSH TaskBoard，不另建 Host 可写审批权威，不引入全 Mission 长锁。#124 在途暂停/终止继续 HOLD；本轮不要求完整 UI、多用户 ACL、真实 IM 集成、产品 E2E，也不构成开发或部署授权。


### 2. 安全/Owner身份 · v0.3 差异复核

**ACP Session**：`acps_98b7aa22fd50dee919246bdb`

**结论：GO（仅限权限与安全边界的设计合同复核）。**

已完整阅读 [CONTRACT-v0.3.md](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/docs/implementation/tplan-h1/CONTRACT-v0.3.md)，并比对 v0.2 差异。两版 SHA256 均与指定值一致，HEAD 为指定的 `f4ce1caf8a77a3cae815da3e8c47c4ac700acd29`。全程只读，未读取其他审阅者结论文件。

我此前提出的三条 P1 **均已在文本层实质解决，可以关闭**：

| 原问题 | v0.3 收口情况 |
|---|---|
| 核验信任根可随调用参数带入 | **关闭**。§3、§8.1 固定 Host 信任表，禁止调用方提供 secret/key-path，并要求密钥处于 Member/普通工具不可访问的独立权限域。 |
| 来源与具体动作绑定不足，签发器可能成为 signing oracle | **关闭**。§3、§8.1 签入主体及来源绑定，要求认证事件明确对应 request/revision/choice/candidate；排除工具审批和泛化“同意”，签发器不向模型或普通 CLI 暴露。 |
| nonce、revision、过期和幂等未形成联合规则 | **关闭**。§3、§8.1 明确同事务校验与核销、成功决定推进 revision、换 command_id 不可重复提交，以及准备事务恢复只前滚一次。 |

**未发现本安全视角下新增的阻断冲突；剩余必须修订条款为零。** §8.2 的提交前状态保护和 §8.3–8.4 的局部授权规则，也没有削弱上述 Owner 边界。

真实 Host 的进程/OS 隔离、认证来源映射、跨语言签名一致性及故障恢复仍须实施验证。这些已有明确准入约束，不因代码尚未实现而判定合同失败。

一条可执行的实施期验收时序：

1. 用隔离测试密钥、假时钟和认证入口 stub 建立局部待决：B 阻断，C 可继续。
2. 普通 Q2/CLI 尝试自选密钥、伪造 Web/IM 来源、借用工具审批事件和直接调用签发器；断言全部拒绝且业务状态不变。
3. 合法提交“撤回成功但 v1 无效、采用受阻”，在事务准备后注入崩溃并恢复；断言仅一笔决定、revision 只推进一次、B 仍阻断。
4. 原 command 重放仅返回历史结果；换 command 重用 receipt、旧 revision 相反选择、过期或篡改候选的 receipt 均不能产生新授权。

以上是待执行的验收要求；本次没有运行测试，也不代表代码、真实 Host 安全或产品 E2E 已通过。


### 3. Mission/执行生命周期 · v0.2 原文审阅

**ACP Session**：`acps_78cf10711ad735db519822e2`

**（1）SHA 校验通过；结论：REVISE。**

已完整阅读 [CONTRACT-v0.2.md](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/docs/implementation/tplan-h1/CONTRACT-v0.2.md)，并阅读前版草案理解差异。`sha256sum` 两次结果均为：

`67325df84a06702d7c8f533ac545d5c250e2aba4c140d98476ae7af5581cf8ff`

Mindthus HEAD 与指定 commit `5761821dd2384522c3e07bcf0e46f56ab7ffb11e` 一致。AIWork 源码对照采用本地 Q2 工作树 `fd4ef21fdfbd0fd5baba8662d1c0daa4e2a101fc`。

设计方向可保留，但以下四处需要在首个运行时代码切片前补清。本轮严格只读，未运行产品、业务任务或验收，未调用网络模型，未查看其他审阅者结论；结论不构成开发或部署授权。

**（2）首片前必须修订的四项**

1. **P1｜§4：写入口矩阵仍是要求，尚未成为可执行约束。**  
   源码中 [`append_event`](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/skills/tplan/scripts/tplan_runtime.py:3408) 独立追加证据；Mission 关闭读取验收事件；普通 [`commit_mission_state`](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/skills/tplan/scripts/tplan_runtime.py:4212) 接收完整前后状态。  
   **反例：**只拦 B 的状态转换，却允许普通提交删除 `human_control`、移除 B 或修改其角色/依赖，再借旧验收与关闭路径完成 Mission。  
   **一句最小解法：**补齐 §4 已要求的矩阵，以事务的 **before 状态和固定 H1 能力**识别受控 Mission，明确保护 H1 对象、阻断关系、成果引用及关闭条件，同时允许 C 的无关观察和进度。

2. **P1｜§2、§4：`AuthorizationRound` 的权威来源与增轮条件未定义。**  
   [`coordinator-round`](/srv/agentdock/projects/aiwork-tplan-q2-20261021/plugins/workbench/coordinator-round.js:32) 当前把调用参数中的 attempt/round 纳入回执键；这不能直接充当 canonical 授权轮次。  
   **反例：**同一有效决定下，用不同 `roundId` 分别 claim；每个 slot 都“唯一”，B 却执行两次。  
   **一句最小解法：**规定轮次由 TPlan 合法业务转换产生，同一执行目的始终复用当前轮次，Host attempt/round/request ID 只能绑定该轮次，超时、重启、重放和换模型均不能增轮。

3. **P1｜§1、§5：最终准入点与派工持久化边界仍有歧义。**  
   §5 同时要求“派工前再次验证”和承认“先前 claim 已跨准入点”；当前 [`dispatch`](/srv/agentdock/projects/aiwork-tplan-q2-20261021/plugins/workbench/coordinator-dispatch.js:113) 在慢准备前检查，之后创建 Session、投递 prompt。  
   **反例：**claim v2 → 创建 Session 期间撤回并采用 v1 → Host 尚未投递；实现者可能分别选择继续发送、拒绝发送或另开一次执行，合同没有唯一答案。  
   **一句最小解法：**把不产生执行的慢准备放在最终 claim 前，以最终 claim 短事务作为唯一准入点，同事务固定 slot、输入、dispatch/Session/request 绑定及命令结果；其后不明结果保留原身份查询，不能释放或换号重派。

4. **P1｜§2、§5：局部授权不能沿用全 Mission hash 作为持续有效条件。**  
   [`coordinator-tplan-gate`](/srv/agentdock/projects/aiwork-tplan-q2-20261021/plugins/workbench/coordinator-tplan-gate.js:13) 对整个 `mission.json + evidence.jsonl` 求 revision；dispatch 对已 reserved 身份又要求 revision 不变。  
   **反例：**B 已获准但仍在准备，独立 C 追加一条观察；Host 恢复时因全局 revision 改变拒绝原绑定，而唯一 slot 又不能重置，形成与人工决定无关的阻塞。  
   **一句最小解法：**全局 hash 只用于读取一致性，B 的授权有效性绑定本请求 revision、采用内容和相关依赖；C 的无关写入最多触发重读，不能废弃 slot 或要求重新批准。

**（3）留给实施期验证，无需扩成完整文档**

- 故障注入验证准备日志前滚、决定与命令结果同事务、重复回执不产生新执行。
- 候选存储验证真实字节、假 SHA、缺失文件、同名替换、采用时校验，以及迟到 v2 不覆盖 v1；§2 已明确要求，无须重新设计资产系统。
- 按写入口矩阵逐入口验证：绕过 B 失败，C 的合法操作成功；终态补录只记录事实。
- 验证旧 Mission/Q2-only 继续使用原 writer，新 H1 build 不自动收养无指纹旧任务，旧 writer 拒写 H1；现有指纹机制可复用，不能靠改写历史指纹通过。
- 配额、磁盘余量和候选大小用首片证据确定；真实 Web/IM 身份、Host 存储隔离及用户交互继续归 #158/#159 验证。

**（4）一条最小合成验收时序**

使用临时 Mission、假 Host、内存原生队列和可控时钟，未来按以下顺序执行：

1. 保存 A 的真实 v1；建立局部待决 HR，令 v2 attempt 保持在途；断言 B 被拒绝，独立 C 可追加观察和推进。
2. 将 B 调度器停在“慢准备完成、最终 claim 之前”；推进假时钟十小时，提交可信撤回并选择仍有效 v1。断言撤回立即成功，重复命令返回原结果，旧 revision 的相反决定失败。
3. 让 C 再写一条观察，释放屏障；两个不同 command/Host round 竞争 B，断言只得到一个 canonical slot，输入为 v1。
4. 假队列接受原 request 后制造超时，并在回执落盘前崩溃；恢复后使用原 ID 查询补录，断言原生 prompt 总数仍为 **1**，换 command/attempt/round 均不能重派。
5. 合法完成 B、C 并关闭 Mission，再提交迟到 v2 结果；断言仅留档，当前成果仍为 v1，Mission 不重开，派工数仍为 **1**。

**（5）值得保留与刻意不做**

保留单一 TPlan canonical、短事务、任务范围等待，以及“决定提交／执行 claim／真实投递回执”三种事实的区分；保留撤回意图与旧稿采用分别成功或失败、实际字节留存、迟到结果按当前决定处理的设计。

继续不做全 Mission 长时 guard、Host 第二套审批权威、Worker 直接向用户索取决定、替换 DSH TaskBoard、历史任务迁移、通用流程设计器，以及把撤回描述为真实工具取消；#124 保持 HOLD。


### 4. Mission/执行生命周期 · v0.3 差异复核

**ACP Session**：`acps_78cf10711ad735db519822e2`

**结论：CONDITIONAL GO。** 已完整阅读 [v0.3](/srv/agentdock/worktrees/Mindthus-tplan-h1-20261021/docs/implementation/tplan-h1/CONTRACT-v0.3.md) 并比对 v0.2；两版 SHA256、HEAD 均与给定值一致。未读取 `reviews/`，判断仅依据合同差异与我上轮问题。

| 原问题 | 复核结果 |
|---|---|
| 旧写入口与关闭绕过 | **关闭**：§8.2 补齐矩阵，以 before-state 和固定 capability 识别 H1，覆盖删除对象、修改角色/依赖及验收绕过，同时保留 C。 |
| 授权轮次来源不明 | **关闭**：§8.3 明确由 TPlan 产生，同一执行目的复用轮次，Host ID、重启和 unknown 均不能自行增轮。 |
| claim 与派工生效点不明 | **部分解决**：§5、§8.3 已明确最终 claim、同事务绑定和副作用顺序；新增“证明未发送后 superseded”分支仍需补一条约束，见下。 |
| 全局 revision 误伤 C | **关闭**：§8.4 明确局部条件与全局快照的区别，C 不使 slot 失效、不触发重批或重派。 |

**剩余必须修订：1 条 P1。**

**§5、§8.3：`not_sent/superseded` 必须排除旧派发者恢复后继续发送。**  
反例：旧 Host 在 claim 后、发送前停住；另一处理者确认“目前未发送”，标记 superseded 并启动替代轮次；旧 Host 恢复后仍持原 claim 发出请求。当前“没有外部副作用”只描述过去，尚未排除这个未来动作。

**最小补句：**仅在原 intent 的所有发送者已被可靠阻止继续发送后，才允许 canonical 地提交 `not_sent/superseded` 并据此替代派发；无法证明时保留原 slot 为待核实，不据此重派。

**可执行验收：**在旧派发者取得 final claim 后、首次副作用前设置屏障 → 提交撤回并尝试标记未发送、创建替代轮次 → 恢复旧派发者；应满足“旧请求不发送、替代请求仅一次”，或在无法阻止旧发送者时拒绝未发送结算及据此替代派发。屏障处加入崩溃恢复后重复验证。

其余属于实施期验证：真实 Host 隔离、原生回执对账、事务故障恢复、候选真实字节/假哈希、旧 writer 与指纹兼容。无需因尚无实现继续扩写合同；本次结论也不代表代码或真实 Host 安全已通过。


### 5. Mission/执行生命周期 · v0.3.1 唯一 P1 差异确认

**ACP Session**：`acps_78cf10711ad735db519822e2`

**GO：上一轮唯一 P1 已在合同层关闭，无剩余必须修订项。**

两版 SHA256 均与指定值一致；已阅读 v0.3.1 并核对差异。

§5、§8.3 明确取消首片中提前回收 claimed slot、据此开启替代派工的能力，保留原 ID 对账。“未观察到发送”不再构成释放依据，因此原反例中“他人释放旧 slot 并发新请求”这一步被禁止；旧 Host 恢复仍可能发送，与即时撤回业务决定的语义相容。

§9 第5项直接覆盖该阻塞时序，并要求不出现第二笔自动派工或旧结果采用，可作为实施期验收。

本结论仅确认该 P1 的文本闭合，不代表代码、DSH 或真实 Host 已验收。
