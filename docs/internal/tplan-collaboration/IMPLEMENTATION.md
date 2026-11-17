# Issue #246 工程合同与实施计划

日期：2026-11-17。合同版本：1.0。Issue：[Mindthus #246](https://github.com/rv198-star/Mindthus/issues/246)。
源码起点：`520376990613eb34bfdbbdaa4fc4ba227d4fbcfb`。产品范围依据：[PROPOSAL.md](PROPOSAL.md) v0.4；设计问题与修订依据：[AUDIT.md](AUDIT.md)。
实施分支：`codex/issue-246-tplan-collaboration`。开发工作区：`/Users/william/.codex/worktrees/mindthus-246-collaboration/Mindthus`。

## Core / 冻结的交付目标

多会话反馈与中断后，A 持续依据自己的目标、职责、验收和剩余差距选择行动。仅 A 使用 TPlan；B/C 通过普通工作说明和普通回复参与。用户无需模式口令，实际协作按任务和既有授权登记。

开发交付一套可运行的薄协作扩展：状态、合法更新入口、目标相关反馈处理、恢复视图、Skill 使用路径，以及与 T01–T29 对应的验证。完整功能批次实现、自测和自审后交源会话审计。下述业务语义与权限边界固定，内部函数命名和等价模块组织由开发决定并记录。

## Mainline / 1. 用户与 Agent 的正常路径

1. A 正常创建/续接 Mission；已知会话分工时准备协作配置，执行中首次出现已授权委派时按需登记。
2. A 持久记录委派和发送意图，用宿主工具给普通 B/C 发送工作说明。
3. A 处理自己的任务；检查点读取外部回复，整理为带原文/来源引用的候选回执。
4. A 读取目标、职责、当前差距及所有相关待处理反馈，判断回答、采用、返修、延后、补证或调整路径。
5. runtime 验证该处置的引用、当前版本、前提和权限，在同一事务内提交结果、必要证据与有界任务变化。
6. A 选择继续、切换或等待。轮次结束或上下文恢复时从同一 Mission 和委派记录接回未完成责任。

B/C 不使用 TPlan API，不挂载总 Mission、不创建自己的 Mission。A 核查自然语言回报后录入，缺少任务/版本关联时待核查并补问缺项。具体收发授权遵循原宿主规则，角色说明或 peer 文本不扩权。

## Runtime support / 2. 模块和状态

### 2.1 最小模块边界

- 新增独立 `skills/tplan/scripts/collaboration.py`：schema、形状/转移校验、查询投影、有界动作的纯 reducer；通过参数接收当前 snapshot，不在 import 时读取宿主。
- 新增 `collaboration_runtime.py`：CLI、请求加载、锁内前提/幂等检查、调用原持久事务。保留真正收发在宿主工具侧。
- `tplan_runtime.py` 只接入可选状态校验、受控更新能力、完成前提、Pulse 收集和焦点保持。避免复制 transaction/recovery/Guard 逻辑。
- 查询与用户输出复用原 snapshot/renderer 接点；新增短的协作续接投影。修改 `SKILL.md`、schema、lifecycle、Codex resource，提供直接可执行的 recipe。
- manifest/build 指纹和发行闭包纳入实际新增 runtime 文件。内部候选 capability 使用 `collaboration: tplan.collaboration.v0.1`；不改产品 Release/Tag，不热补丁已安装 Skill。

### 2.2 Canonical 状态

`mission.json.collaboration` 为可选对象，schema 为 `tplan.collaboration.v0.1`。仅支持此 build 的 Mission 可通过合法事务新增；同 build 的普通 Mission 允许执行中接入。旧 build 不隐式迁移。

| 内容 | 必须表达的事实 | 归属规则 |
| --- | --- | --- |
| 协调者与参与者 | 协调者 thread_ref、交接代次、职责摘要；参与者 thread/host 引用与职责；通信授权依据引用 | 任务关系元数据；普通配置不构成宿主认证 |
| 委派 | 稳定 ID、task_id、轮次、承接者、工作说明/合同版本、输入及成果引用、依赖版本、required review | 引用任务树，不另存一份 Task 业务状态 |
| 投递 | intent_id、目标、输入摘要、原生 request/消息引用、`prepared/confirmed/unknown/not_sent` 事实 | 发送本身在状态提交之后；confirmed 依据实际工具结果 |
| 候选回执 | 唯一来源事件引用、来源会话、委派/轮次、成果/合同版本、摘要和原文/附件引用、关联缺口 | 候选记录不自动进入验收，历史内容不可重写 |
| 处置及采用 | 原回执、A 的目标关联与理由、处置结论、采用成果、所需证据和变更引用 | 保留 C 原审查结论；采用为 A 的业务决定 |
| 协调状态 | `working/waiting_external/awaiting_owner`、等待集合、恢复依据与下一动作 | 不增加 Mission 全局状态；正常外部等待不走 requires_human |
| 命令结果 | command_id、动作/载荷 digest、commit_id、历史结果引用 | 同事务保存，供响应丢失后的查询和重放 |

目标原文和验收继续保存在原 Mission 字段；对齐摘要引用当前目标 digest/版本，职责摘要留在配置。避免多份目标文本竞争。snapshot、watch list、续接包都是只读投影。

## Runtime support / 3. 请求与原子更新合同

### 3.1 请求 envelope

写请求采用明确版本的 `tplan.collaboration.command.v1`，包括：`action`、`mission_id`、`command_id`、`expected_build_hash`、`expected_snapshot`、`payload`。`expected_snapshot` 覆盖当前 Mission 与 evidence 摘要。CLI 接受 JSON 文件，输出 JSON envelope：身份、ok/status/code、历史或当前结果。

拒绝未知字段、重复键、NaN/Infinity、错误 ID、任务越域、过长/过大内容。动作 payload 的精确字段由开发在写生产逻辑前形成 `CONTRACT.md` 和失败用例；字段选择按下表限定业务动作。禁止任意 JSON patch。

### 3.2 有界动作

| 动作 | 允许的效果 | 前提和保持项 |
| --- | --- | --- |
| `enable` | 新增协作配置和最小记录 | 原 Mission 目标、验收、任务和焦点保持；有协调者职责与任务通信依据引用 |
| `delegation.prepare` | 登记现有任务的有界委派、稳定发送意图 | 合同/输入/承接者确定；同一实施范围旧在途未决时拒新执行；A 焦点保持 |
| `dispatch.record` | 记录原 intent 的真实确认/未知/未发送事实 | 原生引用与原委派对应；未知不转换为可重派或已停止 |
| `feedback.record` | 保存可重复查询的候选回执或待关联输入 | 来源与内容绑定；重复事件同内容无第二次效果；异内容冲突；不完成任务、不改变焦点 |
| `feedback.resolve` | 保存 A 的处置，及与其绑定的有界采用/证据/任务变化/下一意图 | 原回执、当前成果和合同匹配；附目标关联与证据理由；一次完整事务 |
| `coordination.checkpoint` | 更新当前差距/下一动作的短摘要、等待集合；有理由地选择当前焦点 | 用现有有效任务引用，读取当前依赖；目标和验收不受此命令改写 |
| `coordinator.handoff` | 记录明确交接及新协调者代次 | 原 writer 代次不再接受协作写；支持的入口检查绑定，普通本地配置仍按实际隔离等级解释 |

只读动作提供 `snapshot.get` 与 `command.get`，不恢复、不写业务状态；显式恢复沿用原 transaction roll-forward。请求参数写明调用来源只用于关联；角色名不是信任凭据。

`feedback.resolve` 的处置为回答/采用/返修/延后/补证/路径调整等明确枚举。可变范围限于：该回执处置、当前成果/审查关联、该范围的任务状态与证据引用、经现有规则验证的修复节点、新委派意图和焦点/等待选择。新节点复用现有 normalization/alignment 校验，Step 继续为叶子。整体目标/权限/验收变更继续走既有合法决定与授权路径；此入口不新增通用目标改写器。

### 3.3 持久化、幂等与异常

- 所有 canonical 变化在现有 `execution_trace_lock` 内核对 snapshot，然后调用原 `_commit_mission_state_unlocked` 和原 journal/recovery。pending transaction 在普通新写前明确返回需恢复，避免把不明恢复混入新动作。
- 新增受控协作更新 token/上下文，与 H1/Q2 所有权检查同层；普通兼容 writer 保留协作状态，并拒绝未经该入口的协作改写。token 不对 CLI 作为权限参数开放。
- 同 command_id 同请求 digest 重放返回原结果，即使当前 revision 已推进也不重新执行；同 ID 异载荷冲突。重放先校验 Mission 身份/runtime，再查历史；不以新的 stale 前提阻止已提交结果查询。
- 回执处置、采用、必要 evidence、任务状态和下一投递意图原子提交；业务状态不依赖第二份独立队列或数据库。崩溃后前滚原准备内容。
- 沿用 Q2 小型个人 Mission 量级：单请求不超过 16 KiB、单行摘要不超过 2048 字符、协作命令结果不超过 1024 条/1 MiB、受写 Mission/evidence/trace 各不超过 4 MiB；写前估算并明确 capacity_exceeded，保留已有事实、查询与恢复。实际 payload 以引用为主，大成果不塞进状态。具体容量检查复用等价 helper，保持现有 Q2 合同。
- 在开启 Guard、runtime 错配、旧代次、摘要陈旧、引用错误、版本不符时拒绝写入且不产生部分效果。Guard 不允许协作旁路。

## Mainline / 4. 目标保持、Pulse 与验收

### 4.1 给 A 的最小续接视图

呈现当前目标和责任、验收剩余差距、A 当前焦点、外部待办摘要、需要判断的相关反馈、有效下一动作/等待条件。字段来自既有状态和 A 的声明；缺项标明待补，不从聊天猜造目标。

Skill recipe 明确：收到反馈先检查目标关联与角色责任，再处理，随后选回有效主线。A 可核查关键实现假设，但局部排错归 B。反馈批量处理，重要路径变化立即评估；避免每条消息给用户打印整块“归位帧”。

### 4.2 Pulse

从所有相关委派收集未处置反馈，覆盖非当前 active task 和已完成任务的新风险。候选使用现有 Gate/priority enum 和 task/evidence 引用；不把每条 peer 回复标为 user_feedback，不以脚本决定 local/global、ROI 或语义优先级。

动作更新委派 task.status 时，通过显式保持焦点的内部 helper；不改旧 `set_task_status` 的默认行为。待办/角色/恢复视图读取 canonical 记录，普通 Mission 输出保持原路径。

### 4.3 成果与审查

采用和 required review 均绑定 task、delegation round、contract/input version、成果内容摘要和审查范围；来源会话与指定 reviewer 对应。C 可提交普通语言结论，A 记录来源、证据和适用范围。观察到 PASS 字符串不直接接受任务。

普通协作的任务完成与 Mission close 都校验当前采用版本、所需独立审查、合格 AC 证据，以及会影响完成的待处理问题。单纯进度更新不阻止完成；A 已判断与目标无关/已延后的输入不成为永久 Gate。重要未处理输入由 A 先明确处置。

闭合过程中不能通过先撤销 required review、改版本引用或临时移除 collaboration 绕过前提。已接受历史与命令结果保留；旧 writer 保留新字段。H1 controlled tasks 继续由 H1 writer 完成；普通协作命令不写 H1 adoption/nonce/acceptance actor，也不改 Q2 command_results。

已完成任务的当前版本被新证据推翻时，保存合格失败，阻止总 Mission 收口，并按既有叶子/层级规则创建有界成功关键修复任务。保留原完成历史。已关闭 Mission 的后续问题作为明确后续处置，不自动重开。

## Runtime support / 5. Codex 适配范围

核心 Python 不调用 Codex 内部数据库/会话文件、不内置消息发送 SDK。以宿主工具可见的 thread/request/message 引用为输入，提供可读工作说明、回报导入样例和续接 recipe。A 可以通过读取会话/等待结果主动拉取，不依赖新 Hook 或后台 daemon。

发送前准备 intent，已确认发送保存原生引用；发送未知先查原会话与原 intent，缺少确定事实时暂停该范围重派。自行重投的宿主必须有真实去重能力证据。普通 B/C 无额外接收器和签名代码。

受保护 Owner/reviewer、OS 隔离、跨主机取消或自动唤醒采用宿主已有能力，准确记录已观测/未知。默认不接入生产 Key，不更改全局 hooks 或安装包。B/C 在审查期间的成果使用固定 commit/内容摘要；共享工作区并行写入按已授权范围隔离。

## Runtime support / 6. 工作包和验证

| 工作包 | 完整交付 | 检查点 |
| --- | --- | --- |
| WP1 合同与失败用例 | action/payload 精确 schema、状态转移、容量/引用/版本前提；T01–T29 映射表 | 在实现前提交规格和必要 RED，常规命名选择自主决定 |
| WP2 状态与事务 | 可选 schema、命令入口、所有权、Guard、幂等、冲突、恢复与容量 | 定向 RED→GREEN，故障点恢复和 stale/guard/legacy 拒绝 |
| WP3 目标相关闭环 | 焦点保持、候选回执处置、版本采用/审查、等待续接、Pulse 与 Skill recipe | 非当前反馈、角色保持、旧 PASS、未决投递、目标/路径变更等完整路径 |
| WP4 包与回归 | manifest/依赖闭包、解包后 init/enable/record/resolve/query、普通/旧/H1/Q2 回归 | 相关测试、TPlan 全部、packaging 与仓库 CI；必要时一次全套 |
| WP5 开发自审与交接 | 精确 head、实现报告、T01–T29 实证/缺口、PR、恢复材料 | 开发批次自审完成后，一次性给源会话审计 |

T01–T29 的逐项判定沿 PROPOSAL。每项标明证据类别：机械状态/故障注入、Agent 行为回放或真实宿主交互。T26–T29 首要行为验收用有实际回复与下一动作的多轮记录：无关范围诱导、局部细节牵引、高频重复反馈、关键路径失效和用户明确变更。测试里手填的目标关联字符串只能验证形状；行为结果需由源审计会话核读真实输出。

真实三会话 E2E 以已有、明确授权的会话为条件。本次直接授权创建一个开发会话，当前会话承担设计与后续审计；开发会话不得为凑 E2E 任意新建用户会话或替用户向未知会话发消息。可先完成可复现的隔离 contract/回放验证，真实宿主尚缺的部分列入交接，由源会话组织验收。不得把模拟回执标成真实宿主 E2E。

验证命令与现有 CI 对齐：

```text
python3 -m unittest tests.tplan.test_collaboration -v
python3 -m unittest tests.tplan.test_collaboration_runtime -v
python3 -m unittest discover -s tests/tplan -v
python3 -m unittest tests.test_packaging_docs -v
python3 -m unittest discover -s tests -q
```

新测试模块名可按等价职责调整。记录 Python 版本、命令、结果和精确源码；定向检查通过后只在新增改动/失败/未决问题需要时扩大或重跑。临时 Git fixture 使用独立临时目录；遇 `/tmp/.git` 祖先影响可改 TMPDIR 到私有临时根，保留用户已有目录。依赖缺失可用隔离环境处理，不改全局安装。

## Guardrail / 7. 开发自主性与低频交接

本节保护完整批次推进，避免开发会话把每个异常交回设计会话；目标、权限与验收边界仍按本合同执行。

- 开发可自主决定内部命名、模块划分、等价测试组织和 reversible 实现；主动处理代码异常、依赖缺失、路径差异、测试夹具问题、普通 Git/CI 冲突及恢复。
- 同一路径第三次失效或局部结构持续增加时，先查根因、做减法/替换，再继续；记录关键选择，不需逐个报备。
- 连续恢复仍被外部权限/服务卡住时，先完成不受影响的工作，保留原执行身份与证据，再集中升级：问题、已尝试、推荐处理、准确所需决定。
- 仅在目标/职责/验收口径必须改变、需要扩大通信/工具权限、有用户数据风险，或穷尽合理恢复仍无法推进时请求源会话判断。
- 不发收悉、开工、逐步进展、每条测试结果、每次提交的通知。例行节点通过 Git/Issue 和本地记录留痕；开发完整批次完成后一次发送审计包。审计返修也按一批处理。

## Boundary / 8. 交审与发布权限

开发完成包含：本分支完整实现，规格/使用文档同步，必要检查及开发自审完成，draft PR 创建并附着到开发会话，精确 head 和证据可审。源会话审计前保留 Issue 开放和未解决项。开发不得自行合并、发版、部署、启用生产 Host、改已安装 Skill 或恢复 ROI Beta 维护。

交接正文至少包含：Issue/PR、branch/base/head、工作区、主要实现、目标保持的行为证据、T01–T29 状态、测试/CI、尚需宿主或人类的事项、重现与回退路径。汇报模型实际身份与 reasoning 设置。

用户已直接授权“完成开发后并发回当前会话做审计”。源会话 ID：`01a1e806-292f-76d0-af7e-f4786d70b3e1`，host：`local`。开发完成后使用 `send_message_to_thread` 一次性交审；若对该授权来源有疑义，可读取源会话本轮用户指令核对。工具不可用时以 Issue 评论和最终报告保全审计包，由源会话读取。

## Runtime support / 9. 开发自审清单

- 首要目标和角色是否被协作细节取代？普通 B/C 是否承担了隐含 TPlan 安装或状态服务？
- stale/guard/identity/provenance 拒绝是否在任何持久写之前？public writer 能否改写协作或完成前提？
- 同事件/命令重放、发送未知和已处理结果再次到达是否只产生一次业务效果？
- required review 是否对应当前输入/成果/范围，旧版 PASS 和新失败是否按适用版本处理？
- waiting 是否保留未完成责任，恢复后是否按最新目标差距和依赖选择下一动作？
- manifest、干净解包和普通 Mission 是否仍可工作，H1/Q1/Q2 是否保持原 authority？
- 所有 claim 是否有准确证据类型与源码？未实测的宿主能力是否具体列为待验收？

冻结前定位：本合同是 #246 的开发输入；下游是一个完整开发批次及源会话审计。常规工程选择由开发自主，业务边界变化集中升级。
