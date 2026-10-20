# TPlan Q2 首片合同：一次 observation 与同事务命令结果

关联 Mindthus #235/#238；AIWork #156；RFC-161 v0.2.1。Owner已批准动工，Q1审查修复基线4b4f83a；Q1合并/检查前只准备规格，不提前宣称Q2准入。此文在运行代码修改前提交。

## 1. 最小业务动作

唯一新增业务动作 `evidence.record`：追加一个 `event_type=observation` 的普通证据，携带summary、可选task_id、JSON payload。不接受event_type输入，不提供验收/Owner批准/状态变更/派工。旧record_evidence.py的默认参数、输出和语义不改。

新入口 `command_runtime.py --mission-dir <Host控制的目录> --principal <普通调用来源标识> --request-json <JSON>`。显式协议 `tplan.command.v1`；动作有evidence.record、command.get、runtime.recover。principal只用于同一命令载荷身份，不是Owner认证，不授予任何高权限；Host控制传输参数，弱CLI只能做原范围内的普通操作。

evidence.record精确请求字段：protocol、action、mission_id、command_id、expected_build_hash、payload。payload字段为summary（1–2048字符、单行）、task_id（null或已有任务ID）、data（JSON对象）。不接受额外字段、重复JSON键、非有限数值；整个请求上限16KiB。command.get使用上述身份字段但无payload；runtime.recover同样无payload，command_id为待确认的原请求身份（不存在时如实报未找到，不能代表外部从未执行）。

## 2. Canonical存储及原子性

新Mission通过 `init_mission.py --command-results` 显式启用，canonical mission.json新增可选 `command_results={schema_version:"tplan.command_results.v0.1",records:{...}}`。无flag保持原Mission形状，无记录时不自动认领旧任务。

每条结果包含command_id、action、principal、request_digest、commit_id、evidence_id、committed_at。digest覆盖动作、Mission身份、调用来源、expected_build_hash及规范化载荷。同ID同digest返回replayed，异digest返回command_conflict。成功结果与observation在**同一个既有Mission持久事务**中提交并前滚恢复；不在Host另建去重账本。CommandResult是历史提交事实，不是当前业务决定，也不包含完整证据内容。

所有持久检查与登记在既有短时锁内完成，先检查pending、目录身份、准确runtime与能力。新动作遇pending返回recovery_required，不自动恢复；显式runtime.recover核对当前及准备态的runtime来源后调用原恢复代码，不派工/不发送外部动作。回应丢失后原ID查询/重试，不生成新ID。提交过程出现I/O失败保守返回outcome_unknown，不能据退出码断言未写入。

普通写入口必须保持command_results原样，不可擅自替换/删改；新增结果只由该命令入口经原事务加入。旧writer通过原build指纹拒绝新Mission；新writer不修改旧Mission。查询仍不写、不恢复，仅持锁元数据可能变化。

## 3. 版本、能力和支持范围

这是新增可选能力，不是伪装的纯bug修复。候选runtime generation拟为 `1.6.0-q2.1`（内部候选身份，不是产品Release/Tag）；产品包版本不在本片直接改。manifest声明command_results能力及新脚本；完整依赖闭包包含原内核、identity/contracts、新commands模块、CLI、init、bootstrap及实际使用的共享_runtime。既有格式指纹规则不改，外部依赖以发行清单一并校验；未经实际闭包验证不作正式发行结论。

本片不做新组件化指纹schema，旧规则下新build与旧build不兼容是预期结果。旧任务使用原固定包，不回填schema/provenance。新命令只服务显式启用的新任务；不在已安装collection上热补丁。新build里默认旧CLI用法保持，运行时选择由Host明确控制。

Q1 `snapshot.get`可在匹配新build上展示command_result_store；`command.get`仅已启用新能力时返回结构化历史结果，旧包/无能力返回unsupported_capability。新增查询DTO为 `schema=tplan.command_result.v1, authority=historical_result_only, command_id, result`；result包含上述持久字段，不能被UI解释为当前采用或当前执行。

## 4. 返回和拒绝

命令envelope固定protocol、mission_id、command_id、action、ok、status、code、message、data。
status区分committed/replayed/read/recovered、rejected/conflict/recovery_required/outcome_unknown。错误包括invalid_request、unsupported_capability、runtime_mismatch、invalid_state、mission_unavailable、guard_open、command_conflict、command_not_found、capacity_exceeded、outcome_unknown。错误消息不含真实证据正文或路径；Host transport timeout不解释为业务失败。命令结果查询和恢复都不扩大权限。

## 5. 容量与可观察边界

首片只覆盖小型个人Mission：最多1024条持久命令结果，结果表序列化≤1MiB；受影响Mission/evidence/trace各≤4MiB；写前预估新增字节，不超限后才发现。空闲空间至少16MiB并足够两倍本次事务估计量；容量不足拒新写，不清理既有事实。历史查询/重放不因到达写预算而失效。保留至Mission显式归档，不自动删除用户成果、事务或引用旧包。

实际隔离测试测量查询/提交/恢复耗时和字节量，CLI/Host使用既有20秒超时，不承诺固定速度。超出支持范围应明确capacity_exceeded；扩容属于以后明确的小改动，不先换数据库。低空间测试使用隔离/模拟free-space探针，不向生产填盘。

## 6. 实施前后验证

1. 新启用Mission提交一次：证据与结果同时存在；同ID重放字节不变；同ID异payload/principal冲突。
2. 多进程相同请求只一个committed、其余replayed；不同命令各自证据ID唯一。
3. 准备事务写入前失败、准备完成后进程中断、恢复中断、提交后回应丢失分别检查；query不恢复，显式恢复和原ID重放不重写。
4. 错expected_build、无能力、新旧build错配、非法证据、guard、目录/符号链接/超限不产生业务副作用；普通CLI原文本输出不变。
5. 新包从干净的真实发行布局解压后可init/record/query，依赖完整；旧包继续处理自己的Mission；错包拒写。Q1 CLI/Node读取同一历史结果合同。
6. 只重测相关事务/来源/普通证据/guard和新命令路径；不运行真实用户任务、模型调用、外发或H1审批。

通过只代表Q2代码与这些范围的工程验证。#238据真实候选判断是否独立发行/版本类别；不自动发版，AIWork#124 HOLD不变，#236/H1另按规格推进。
