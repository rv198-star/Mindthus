# TPlan 执行过载案例：合同修复与接入方案

Date: 2026-09-05
Status: #196/#197/#199/#198 implemented and self-tested in candidate `45c0ac0b1cdc80465deeb2accba5ad80bf919535`; implementation review passed; merge/release pending. #200 remains design-only.
Original reproduction base: `407112ded87377b5b7dd351c49dd0d20b1d598d4` (TPlan source identical to v1.10.0).
Repair audit: `docs/internal/audits/2026-09-05-tplan-authority-contract-repair-audit.md` on `2501e8ac3f55b24478abefa68b864f8472744af0`.
Implementation review: [four-contract repairs and final verification](../audits/2026-09-05-tplan-authority-contract-implementation-review.md).

案例：[RU-20260905-SLIDETHUS-VQ-OVERRUN-01](../../../data/cases/slidethus-vq-execution-overrun-20260905/README.md)。
复现：[reproduce.py](../../../data/cases/slidethus-vq-execution-overrun-20260905/reproduce.py)；
结果：[current-runtime-observations.json](../../../data/cases/slidethus-vq-execution-overrun-20260905/current-runtime-observations.json)。

## 0. 先把问题分对

目标不是让日志更漂亮，而是让已声明的引用、状态、验收和执行约束具有一致的机械后果。

本轮通过公共API和临时合成Mission确认四类当前缺口。原附件没有完整运行日志或源码
快照，因此只把前两类与事故摘要对应；Mission提前完成和stop授权仍激活任务是当前
代码新复现，不能倒写成原事故事实。原任务失败也不是方法净收益为负的因果证明。

严重级别定为 **P1正确性问题**：会污染后续决策依赖的状态/引用或忽略明确停止决定；
不使用未获证实的全局P0灾难标签。可以优先修，不需要用第二个真实任务重复同一bug
来取得资格。预算/执行入口是独立设计候选，不把它冒称为已声明全局预算的绕过漏洞。

## 1. R1：证据引用在同一事务内解析

### 根因

`transition_task_status` 接受 `evidence_refs`；`validate_execution_trace_record` 只检查
引用为安全字符串。`_commit_mission_state_unlocked` 验证新增evidence的结构/ID，
却不解析本次引用。不存在的ID与误放进去的文件路径因而都能伴随completed写入。

### 最小修复

在既有锁与事务所有者中建立一个共同引用解析步骤，对本次新增的typed evidence IDs
使用同一Mission已有证据和本事务prepared证据的并集。ID必须唯一可解析；不靠E前缀、
占位词黑名单或文件是否存在决定是否合法。`artifact_refs`维持独立语义。

检查发生在本次写入journal/状态/trace之前；decision、普通transition、guard的授权
mutation与恢复路径共享相同规则。prepared evidence在同一次原子提交中可被引用。
路径误填要报错，由调用者选择正确引用类型，脚本不自动把错误ID洗成artifact。

历史坏引用只读时保留并显式诊断，不回填伪造证据；无关历史警告不能让一切合法写入
都永远失败。任何正在被使用且无法唯一解析的引用，保持拒绝。

### 验收

- 不存在ID、真实文件路径误填ID、另一Mission的ID、重复歧义ID均拒绝。
- 已存在的合法证据，以及同一事务新建的合法证据可以引用。
- artifact通路仍可用；引用可解析不等于证明验收真实或充分。
- 拒绝本次变更时没有ghost event、部分journal或伪状态；加入失败注入与并发追加测试。
- pending transaction恢复复用原证据边界，不以新内容重解释旧事务。

## 2. R2：创建并激活共享一个状态转换

### 根因

`add_task_node(status=active)`直接追加节点，未调用统一activation逻辑；普通
`set_task_status(active)`则会同步游标。当前可生成活动根节点T6但cursor=null。

### 最小修复

新增默认pending；显式请求新增并激活时，在同一个内存候选状态中复用统一activation
转换，再由一次既有事务提交。优先保持现有显式CLI意图兼容，而不是直接移除
`--status active`。生成node_added与active_node_changed的同一commit_id/时间边界。

“活动任务”和“当前执行叶游标”不是一对一计数：祖先任务可以保持active，合法并行
表示不能误伤。尚未选择工作的Mission允许cursor=null；requires_human可以保留
blocked恢复游标。检查应围绕所声明的激活动作，而不是粗暴规定“只能有一个active”。

### 验收

- 原T6反例：新增active与游标/trace一起成功，或在写入前给出明确拒绝；不再不一致成功。
- 默认pending新增不抢占游标；已有活动祖先、显式切换、blocked恢复游标保持。
- 新增加激活中途失败时，节点、cursor、trace不产生半状态。
- 直接初始化、普通transition、decision mutation、恢复路径检查同一后果。
- 旧运行只做诊断/显式恢复，不自动选择“看起来最新”的任务。

## 3. R3：完成状态受验收范围约束

### 已证实的最小缺口

`apply_decision(close)`只需合法字段，就能在两个success-critical Task仍pending、
没有acceptance_passed时写入Mission completed。有acceptance_failed也一样。
这与lifecycle.md的完成规则冲突。不能用事后warning代替这项确定性前置条件。

### 分两片落地，先止住明确矛盾

A. 所有写入Mission completed的规范路径，在同一锁定快照中检查success-critical
工作的关闭条件和当前声明的Mission验收项。缺失、失败未解决或引用不明不能被
rationale中的“已完成”取代。非完成退出继续使用blocked/budget_exhausted/abandoned/
superseded等现有结果，不改写目标来凑成功。

B. 关键Task/验收的实质充分性仍由Agent或具名review负责。修复前审计进一步做了减法：
第一阶段不新增验收映射数据库或schema，直接复用现有 acceptance ID 与 qualified
`acceptance_passed` / `acceptance_failed`（以及完整 legacy `acceptance` 兼容读）。
对每个Mission acceptance ID，以证据流顺序读取最新合格观察；最新为失败或不存在则
不能关闭，后续新的合格通过可以重新满足。脚本只判断引用、范围和机械正反状态，
不判断PPT好不好，也不把字段齐全视为质量合格。只有后续真实证据证明还缺产物版本/
更细 freshness 绑定时，才另行扩展。

普通支持性动作的“执行完成”可以仅有相应artifact/done-condition依据，不强迫每次
读文件都做全Mission验收。任何key_finding、path_delta、decision_applied或计数增加，
不能自动满足某个acceptance。局部synthetic测试只支持其声明范围，不能升级成真实
Office/holdout验收。先冻结明确的关闭规则，再改老测试中无证据关闭的便利fixture。

后续反证推翻一个完成声明时，保留原事件，显式记录失效/替代及重新审议关系；
由规范路径决定重开或替代。外部TASKS/issue同步是投影，不是第二份完成权威。
旧completed记录维持可读并标未验证，拒绝通过Repair补造验收或改写历史。

### 验收

- 关键任务pending/active/blocked时Mission不能completed。
- 仅测试摘要、空ID、错Task/错验收项、陈旧产物、未处理失败均不能形成完成授权。
- 合法且当前的验收覆盖可以关闭；supporting任务不会被强制重复全Mission仪式。
- 后续失败不会仍呈现无保留accepted；reopen/replace必须具备明确依据。
- 事后已知的失败不能被用来伪称过去一定知情；历史读取与新关闭授权分开。

## 4. R4：续行授权的枚举必须约束实际动作

### 根因与新反例

`_validate_continuation_authorization`只检查枚举。当前合法字段组合：

```text
recommendation = continue
continuation_authorization.authorized_action = stop
proposed_mutations = set_active_task(T1)
```

仍返回applied_decision并激活T1。探针同时给出fail lint/no-new-evidence，但这些语义
信号不是机械判罪依据；**stop与继续执行动作的直接矛盾**才是这项bug的判定依据。

### 最小修复

让canonical decision validator检验recommendation、authorized_action及mutation的
确定性一致性，并在apply前拒绝矛盾。stop不能隐式授权激活；mission_review和
anti_spiral_audit只能进入相应待审路径，而非直接获得同路径执行许可。所有能应用
相同decision的规范入口，包括guard授权路径，都经过这一检查。

保留“证据弱但仍可能值得继续”的Agentic判断：本修复不把weak/unclear评分硬编码成
停止，也不实现基于时间/次数的语义优先级算法。允许真正一致、有依据的继续；
不新增另一份续行权威或把文字授权当作宿主不可伪造凭据。

### 验收

- stop + activation、review/audit-required +立即推进的矛盾拒绝且无写入。
- 一致的继续、针对性修复和批量细节处理保留；合法停止/待审可明确记录。
- 外层recommendation、内层授权和mutations任一单独篡改都不能扩大允许动作。
- 旧evidence原样可读，新写入严格；新规则有跨入口、重放、并发/失败原子性测试。

## 5. D1：跨工作区的续投边界与执行覆盖（设计候选）

### 已有证据与上限

多个root下累计消耗高、未见持久化价值重估是需求线索。没有原始全局授权、计时span
和全流水，本轮不能宣布“突破了35次Mission总预算”、精算TPlan造成的耗时或证明
Anti-Spiral从未被思考。没有SRA分配记录，也不据此修改SRA方法。

### 最小验证方向

先把现有TPlan continuation结果接到一个明确受管的外部Host执行入口。区分两件事：
是否采到执行/重试信号；下一次受管动作是否真的经过继续决定。只有采集不等于执法，
没有object_id日志不等于没有重复工作。无接入时明确reported-only/coverage-unknown，
不把空Pulse称为健康证据。

存在明确资源上限时，作用域应是受批准的Mission/decision-path/window与tranche，
不是目录名。attempt/root/worker只是同一批投入的执行实例。独立任务可有各自范围，
不能把全仓库的一切操作揉成一个预算。上限与单位从授权输入来，不硬编码35次/16小时。

同一批投入耗尽后，新root不自动生成额度。下一份投入需重新声明要得到的新增证据、
剩余阻碍、替代路径及新的授权上限。计数使用稳定operation ID与原子预占/结算；
失败、重复回执、重启、并发和结果未知都不能重置为零。只有真实接入的范围才可宣称
enforced；任意绕过进程/文件写入的强防护仍归#140，观测复用#143/#146。

**先做TPlan受管入口，不以SRA–TPlan大集成为前提。** SRA未来可提供资源决定引用，
TPlan持执行权威；避免两套余额/授权表。一次新批次只汇总必要风险和证据，不让每个
低风险动作填写厚重案卷。

### 设计阶段验收

先比较“仅原root上限”与“同一已授权决策路径跨root上限”的有界fixture：耗尽后换root、
重启、并行尝试、重复回执、显式新增tranche、无监控宿主。未重新授权的下一次受管
provider调用应根本不发生，而不是调用完才打warning。随后才能申请小预算真实Host
验证；fixture通过不是价值证明。

停止条件：若需要新调度器/全平台矩阵才能起步、无法取得调用前控制、或记录成本
抵消节约，则缩小到覆盖提示和已有continuation接入。该设计issue不自动解除#144冻结，
不批准真实跑批、新Hook部署或SRA强制调用。

## 6. 执行顺序和共同出口

1. 入库原件、审批、一次回溯usage记录和当前反例；保持原日志不可变。
2. 修复前 Authority Contract Audit 已通过；无需再开架构轮。按 `#196 -> #197 -> #199 -> #198` 推进，每项先失败回归、再根因修复、再正反例与当前全套验证。
3. R3 的最小关闭规则已在审计中冻结：success-critical 节点全部 completed，且每个 Mission acceptance ID 的最新合格观察为正；第一阶段不新建验收schema。
4. 四项合并后做统一v1.10.x兼容/包验证，按实际合同变更再决定版本，当前不发版。
5. D1只做单入口设计和有界实验计划，真实接入与功能实现另行批准。

共同出口：已解决的反例转为永久回归；合法对照、角色/权限、原子提交、旧Mission
只读及显式恢复、runtime fingerprint、所有发行布局保持；报告准确的执行/通过/跳过
数量。不同问题分别提交，拒绝用更改测试期望来保留明显矛盾。

发布标签不移动，原事故证据不补写。#141/#142/#147/#148既有关闭范围分别是渲染、
provenance、稀疏呈现和re-entry，不把本次新问题混成这些旧issue全部失败。

## Issue 映射

| 项目 | Issue | 状态 |
|---|---|---|
| R1 事务内证据引用解析 | #196 | 已实现、自测及评审通过，待合并 |
| R2 创建/激活与活动游标原子一致 | #197 | 已实现、自测及评审通过，待合并 |
| R3 Mission完成前置与验收范围 | #198 | 冻结的最小关闭合同已实现及验证，待合并 |
| R4 续行授权与实际mutation一致 | #199 | 已实现、自测及评审通过，待合并 |
| D1 外部受管执行与跨root续投边界 | #200 | 设计/验证候选，未批准实施 |

父证据入口复用#144，不新增一个大总纲。#144已补入库记录和分母排除说明。

本会话进行了两方面复核：证据/隐私复核确认原包逐字节保留，历史报告和合成复现
分开；修复范围复核保留活动祖先/blocked游标、轻量动作、旧记录读取及宿主能力边界，
撤回将单root上限称为既有Mission总预算的推断。均为ChatGPT自身复核，不称异模型认证。
