# H1-A · Task-scoped pending gate / 首个运行时候选

**状态：代码候选，待本地全仓 CI 与源码审查、PR 合并；不是 H1 产品闭环通过。**
Owner 已授权按 RFC-161 v0.2.1 和 Mindthus #236 分片推进。合同 v0.3.1 已经过两项独立权限/时序审查。本片只验证局部 pending gate 的既有写入口一致性，不把代码绿色误报为真实 Owner/DSH/IM 接入。

## 实现范围

- init_mission.py 的新 Mission 显式使用 --command-results --human-control 选项；默认旧 CLI 仍创建原 Mission 形状。
- TPlan 新增 tplan_h1.py 纯约束：pending B 的完整子树、活动焦点、旧任务/角色/依赖/控制状态的篡改、伪造正面验收以及 Mission 关闭均不能绕过；独立 C 可以执行/记录。
- 历史 B 验收仍能被只读 Q2 查询，不被当作当前批准；新 B 验收提交会被拒绝。
- 此分支候选 runtime 为 1.6.0-h1a.1，并声明 task_scoped_owner_gate capability，新模块纳入必需文件和指纹；正式 Mindthus Stable 版本尚未调整或发布。

## 证据与限制

RED：最初六项测试中五项因 --human-control 和 H1 状态不存在而按预期失败。定向代码复审补充了子任务改挂、历史验收不阻 C、活动焦点、畸形状态等反例，已加入定向测试。最终全仓通过结果在候选 HEAD 验证后追加记录。

测试使用合成 Mission 与内部测试 marker _H1_CONTROL_AUTHORITY；该 marker 不是可信 Owner 认证机制，不能暴露给普通 Agent。**本片没有公开 decision.open / decision.apply、没有签发或派工接口，也没有真实 Owner 权限能力。**

历史兼容例外：无 runtime_provenance 的非常早期 Mission 仍保留原普通写入时 legacy_adopted 行为，但绝不会由此创建 human_control。已有 provenance 的旧 Mission 必须使用匹配 writer，不能被 H1 新构建改写。这不构成新 H1 功能的旧任务迁移。

## 后续切片

候选实际字节保存、Host 可信 scoped receipt、nonce/revision 防重放、有效撤回并采用旧稿、唯一 execution.claim、原生 DSH 回执与晚到结果、Web/IM 均属于后续 H1-B/H1-C/AIWork #158/#159，不在本片。Core/运营工作树、已安装 Skill、真实 Mission 与生产运行不改，#124 HOLD 不变。

## 冻结提交本地验收（后补证据，非运行时代码变更）

- 源码冻结：dc7c9dc434dcf195a785aea95ba5da9ab1fba69f。测试期间工作树干净、HEAD不变。
- OCI Python3.12 全仓 unittest discover 1,265 项：1,258 PASS、7 原条件 SKIP、0 FAIL；用时 267.042 秒。
- OCI 已缓存 Python3.11 离线/只读源码容器：H1-A 16/16 PASS；另有此前 Q2 核心+查询组合已 PASS。
- AIWork Q2真实 Node→Python 历史查询兼容 12/12 PASS，未将历史命令结果充当当前批准。
- 独立 ACP 只读代码审查最后确认 H1-A P1/P2 均关闭，但它未做落盘/真实Host验收。
- 初始 RED、完整 Python3.12、Python3.11、Node 12 原始日志和 sha256 清单位于 evidence/H1A-VERIFICATION.json。
- 该验收限于合成 H1-A 内核和受影响历史使用方式；Q2发布和H1-B可信权限仍有独立工单。
