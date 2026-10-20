# TPlan Q1 query protocol v1 — 编码前规格

关联 #234；AIWork #162；总目标 AIWork #156；设计 RFC-161 v0.2.1。基线 Mindthus c034b01（package 1.13.0，runtime generation 1.5.4）。本片只读程序入口与一个Node消费者，不提供人工批准、派工或写动作。

## 1. 接口与固定运行时

新入口 `skills/tplan/scripts/query_runtime.py`，调用 `python3 -B -I /固定包/.../query_runtime.py --mission-dir /Host已验证根目录/ID --request-json '<JSON>'`。兼容脚本自身显式导入同目录内核。固定sourceRoot由Host构造器配置，不由模型选择；Python解释器使用绝对路径。继承的PYTHONPATH不参与选择（-I）。旧脚本、manifest、指纹文件和已安装包不修改。

新增查询脚本是旧runtime之上的只读客户端，并非新writer，Q1不将它塞进旧fingerprint_files导致旧任务换build。协议和查询实现自身有单独版本/文件SHA；实际writer身份来自原runtime_fingerprint。未来新写入能力另行建新build/schema，不回填旧任务。

## 2. 请求

JSON对象精确字段：`protocol="tplan.query.v1"`、`action="snapshot.get"|"command.get"`、`request_id`、`mission_id`；可选`expected_build_hash="sha256:<64hex>"`；command.get另需`command_id`。身份字符串为1–128字符字母/数字/点/下划线/短横线且首字符字母数字。拒绝额外字段、未知protocol/action、重复JSON键、非法JSON常量和超过16KiB请求。

mission-dir是传输边界参数，不放在模型payload。Host仅允许managed missionRoot下一层目录，拒绝越界与目录别名；单独CLI由调用者选择受信目录。目录必须已存在，根/mission.json/关键状态文件不得用符号链接转向外部。Q1不创建Mission。

## 3. 成功DTO

统一envelope：`protocol, request_id, action, mission_id, ok, status, code, message, data`。
成功：ok=true/status=read/code=null。data包含：
- `schema="tplan.snapshot.v1"`、`authority="observation_only"`。
- mission：id/title/status；focus_task_id：原active_task_id（关注焦点，不是并发数量上限）。
- tasks：id/title/status/role/acceptance_evidence；work_plan：原元数据或null（不是执行授权）。
- evidence_count、trace_count；不返回原证据正文、消息、签名秘密或完整内部trace。
- interaction_guard：内核提供的可见控制摘要（present、guard_id、revision、phase、baseline_active_task_id），不包含原用户消息。
- revision：mission/evidence/guard digests，仅供观察一致性比较，不是claim或授权token。
- runtime：package_version/source_id/build_hash/capability_versions/capabilities、compatibility/origin/compatible；不泄露安装绝对路径。
- query_capabilities：当前仅snapshot.get；command_result_store=false。

复用 `read_user_update_snapshot`：同一内核短锁读取mission/evidence/trace/guard，拒绝pending transaction，不调用隐式恢复入口。validate_mission仅作结构合法性核对，不做语义验收。所选runtime与recorded fingerprint不匹配时不给可用snapshot；legacy_unpinned允许诊断性只读，compatible=null，不认领/回写。expected_build_hash提供时另核验所选runtime，Host消费者必须固定该值。

## 4. 错误与退出码

| code | exit | status | 含义 |
|---|---|---|---|
| invalid_request / unsupported_protocol / unsupported_action | 2 | rejected | 修正调用，不执行 |
| unsupported_capability | 3 | rejected | 当前writer没有持久CommandResult；不表示原命令未执行 |
| recovery_required | 4 | recovery_required | 发现未完事务，需要正确writer另行恢复；本查询没有前滚 |
| runtime_mismatch | 5 | rejected | 选错build或Mission指纹不匹配；不修改指纹 |
| mission_unavailable | 6 | rejected | 目录/文件不可用或路径违反约束 |
| invalid_state | 7 | rejected | 合法输入下的状态结构/JSON/guard损坏 |
| runtime_unavailable | 8 | rejected | 固定runtime或其依赖不完整 |
| query_failed | 9 | rejected | 其他内部读取故障，仅给安全原因 |
| snapshot_too_large | 10 | rejected | 单源文件超过8MiB/输出超过128KiB，不能返回截断成功 |

stdout恰好一份JSON加换行；错误不把原用户数据/堆栈写入日志，旧CLI行为不改变。`--help`保留普通CLI帮助。Host自身启动超时/不可执行/坏envelope返回`transport_error`或`protocol_error`，不宣称任务失败、恢复或重新执行。

Q1 command.get先做请求形状校验，直接报告unsupported_capability，不为了补能力创建任何结果库。后续Q2扩展时另版本/能力协商。

## 5. 只读承诺与限制

所有业务文件的路径集合、字节和mtime不因查询改变；不写provenance、不恢复事务、不更新日志/通知/CommandResult、不运行模型。原runtime短锁`.execution_trace.lock`可存在或创建为空（Windows可能一个锁字节），仅为本地协调元数据，不属于业务状态；空目录或不存在的任务不因query而创建。使用-B禁写pycache。

本片只支持与原runtime相同的受信本地文件写入者协作；不声明防住同OS用户任意篡改文件。Host目录校验和结构化输出不是新认证或执行许可。达到读取上限时只报明确错误，容量预算不是性能测试结果。

## 6. 验收 V01/V02

用临时合成Mission，不使用真实数据：正常/guard只读、pending transaction不恢复、legacy不认领、错身份/错build/未知protocol/额外字段/重复键/坏状态/缺能力/大小上限/目录越界；多进程查询与官方写入的完整快照；普通CLI与Node消费者结果一致；查询前后业务字节/mtime不变。只重跑与读取/指纹有关的既有测试，旧CLI文本仍可用。接口测试通过不是H1/Web/IM验收。

本合同先提交，随后才写接口/测试。代码完成以PR和真实测试证据留档，暂不合并/发行/部署。#232/#233独立关闭修复与本片无关。

## 审查补正
源文件类型与大小在实际读取的同一内核短锁内复核；读取后的证据和trace逐项用原内核验证器检查，不把可解析JSON等同于合法记录。Q1的command.get只有unsupported_capability结果；未来成功DTO需通过新能力合同成对接入。
