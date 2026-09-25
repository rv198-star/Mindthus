# #211 v0.3 审计修复与离线验证

父版本：`5985bd2c7b5d87ecebeabdbafe41add4d354e818`。分支：`experiment/typed-decision-runtime`。
对应 [实现审计](IMPLEMENTATION-AUDIT-20260926.md) 与 [修正设计](REPAIR-DESIGN.md)。
用户在审计后要求直接补全；本轮完成实现修复、测试代码和离线回归。

**工程接线已通过下列离线验证；真实 Jev／当前 Codex 的新版五条件比较仍未运行。**
没有将合成观察或回执当成模型效果。#211 仍为 **NOT QUALIFIED**。

## 1. 已修复什么

| 审计项 | 本次实现 | 对应新用例（名称缩写） |
| --- | --- | --- |
| F01 S1 无法计账 | 新模式登记 `candidate` 判断步骤；S1 和复查计入原 Episode | `clean_public_entry`、`correction_recheck`、`pending_reentry` |
| F02 ①未消费建议 | ①收到完整 S1 观察，可保留或修订一次；S0 观察/覆盖也进入执行请求 | `advice_can_retain`、`advice_can_revise_once` |
| F03 仲裁缺正文 | 仲裁同时收到原候选、新候选、观察和引用，裁决绑定当前版本 | `arbitration_has_candidate`、`mixed_revision_and_objection`、`arbitration_rejects_stale` |
| F04 仲裁恢复丢裁决 | 同请求先重放已完成结果；只有新请求才检查剩余仲裁额度 | `arbitration_has_candidate_and_survives_acceptance_resume` |
| F05 前置接受清掉覆盖义务 | 定点重判使用 v0.3 合同；遗漏事项/必要候选保持未决 | `accepted_predecessor_cannot_clear_missing_coverage`、`actual_artifact_rechecks_only_waiting_consumer` |
| F06 修订前置后仍接受旧后继 | 记录实际输入版本；前置变更撤销旧用途接受，依赖后继保持未决，独立事项继续 | `predecessor_revision_invalidates_consumer`、`predecessor_revision_leaves_independent_work_accepted`、`simultaneous_revision_does_not_accept_stale_dependency` |
| F07 辅助未知拖住主路线 | S0 同批新增作用范围题；仅明确可选的辅助/伴随未知不阻断主路线；原观察保留 | `optional_method_unknown`、`required_method_unknown`、`optional_companion_unknown` |
| F08 两种方式材料失配 | ①／②执行时加载同一套 canonical 方法正文，差别在消费规则 | `same_method_material_for_both_policies` |
| F09 接收与终态不完整 | 接收请求含正文、初检/复查/仲裁和剩余义务；拒绝加入 pending；消费完成与语义正确分开 | `host_declines_acceptance`、`acceptance_contains_observations`、`acceptance_budget_exhaustion` |

F06 的处理是保守地保留未决：即使同一回复同时改写前置和后继，也没有新版本用途接受证据，
不能自动通过。未新增重执行额度。历史已接受版本保存在 `invalidated_accepted_uses`，不改写旧记录。

另外补齐：

- `conversation` 要求 `author_ref/source_ref`；介入摘要覆盖真实消息正文与角色顺序，绑定到 Episode。
- finding 保存实际输入文档引用及候选范围/hash；引用粒度是全文，没有冒称 Jev 精确定位了词句。
- 每个 `corrected` finding 关联新产物实际替换范围；语法映射不证明修正语义正确。
- 原宿主执行回执可以提交具名 `dependency_acceptance`，因此 D 接力可通过已有 CLI handoff 消费。
- 同 Episode 原宿主上下文保持一致；仲裁要求独立上下文；Codex 观察对照的声明宿主必须与实际首份宿主回执一致。
- 合同升为 `0.3.1`；旧模式的可选参数默认保持原行为，旧两项根因回归继续通过。

## 2. 五条件最小实验入口

新增 `experiments/typed_decision/comparison_v03.py`，复用原 Episode、Session 与 CurrentAgentHost：

| 条件标识 | 已实现入口 | 尚未证明 |
| --- | --- | --- |
| `pure_codex` | 同原始材料自然首答→一次复核→可选争议仲裁→接收；保留首答 | 当前真实 Codex 的行为/效果 |
| `questions_only` | 同上，增加未填答案的 S0 模板与 S1 四题，不给 gold 或共同人工 frame | 提醒本身的真实增益 |
| `codex_observation_committed` | 显式实验 admission；调用者提供独立当前 Codex 观察回调，按同题组输出并沿用② | 回调与真实 Codex 进程的实接、服务端身份及效果 |
| `jev_advisory` | 官方 Jev 路径＋①建议消费 | 新版真实①结果 |
| `jev_committed` | 官方 Jev 路径＋②完整处置/接收 | 新版真实②结果 |

`run_condition(...)` 接收条件、原始 packet、现有宿主 hooks 和相应 provider；它不启动新的模型进程。
独立 Codex 观察回调必须返回绑定的 request ID、独立 context ID、配置、逐题答案及用量；
普通 LLM 的自报数字保持 `ordinary_llm_uncalibrated`，不会伪造 Jev 分布。
安全原始返回/有效用量沿用已有捕获逻辑。产品默认入口仍仅接官方 TypeSafe `jev-1.13.0`。

`common_candidate(...)` 接收已有实际候选和作者/上下文/来源身份；通过 `candidate_snapshot`
进入共同候选 S1 诊断，跳过 S0 和重新生成。完整路径不传这个参数。live admission 绑定快照摘要；
新运行普通路径判断上限为 3，有真实依赖为 4，共同候选为 2，原宿主工作额度另计。

`prepare_campaign(...)` 只准备材料：校验 12 家族、先 EEFF 后 ABCDEEFF、来源身份去重、
事前平衡五条件顺序、同宿主配置和材料摘要，将验收要求留在 `reviewer_only`。
它不发请求、不实施阶段晋级、不执行评分，也不是批次额度调度器。92 是含技术预留的整个计划上限，
不是允许每条分支重复使用的额度；实际实验仍需按设计冻结分阶段剩余额度与停止点。
来源声明为 synthetic/historical_exposed 时始终保持 development_only。

## 3. 测试与复现

新增 `tests/test_route_control_v03.py`、`tests/test_comparison_v03.py`，以及
`experiments/typed_decision/fixtures/route-v03/` 下八份合成夹具：A/B/C/D 各一，E/F 各二。
其中包含多轮 Skills 范围纠正、简单解释反向控制、已有 4K 的补救与购前显示取舍。
题目观察和宿主回复都是注入的工程材料，**不测模型准确率，不是新的外部来源**。

最终相关回归：**310 项通过**，其中本轮新增 **50 项**（A–F 夹具循环另含 8 个子用例）。
验证包含公共 Python 入口、CLI 创建 handoff、恢复幂等、拒绝错误回执、同版本材料、
辅助/必要未知、仲裁前后恢复、局部依赖失效、单题异常隔离及旧 scoped repair。

本地命令：

```sh
TMPDIR=/private/tmp PATH=/opt/homebrew/opt/python@3.13/libexec/bin:$PATH /opt/homebrew/bin/python3.13 -m unittest tests.test_route_control_v03 tests.test_comparison_v03 tests.test_route_control tests.test_current_host tests.test_scoped_route_repair tests.test_relationship_runtime tests.test_relationship_assessment tests.test_relationship_live tests.test_observation_assessment -q
```

使用 `/private/tmp` 是为了 macOS `/var` 符号链接不干扰既有严格路径校验；Homebrew Python
避开本机系统 Python 的 Xcode license 错误。未放宽运行时身份规则。
开发中出现并修复的失败包括 native 仲裁缺方法 hash、测试夹具的题号/空 reason、CLI 重跑复用
旧 episode ID。只将最终上述运行记为通过，未写成一次测试即全绿。

工程 CLI 示例（新建仓库外 state root；该命令只用注入观察并等待宿主）：

```sh
python3 -m experiments.typed_decision.entry --mode route-control.v0.3 \
  --fixture experiments/typed_decision/fixtures/route-v03/B-control.json \
  --state-root /absolute/new/state-root
```

后续用 `--host-response` 提交相同 handoff 的回复。夹具自带固定 episode ID；重复跑新实验时
在副本中登记新 episode ID，不能把已登记 ID 指到新目录。共同候选和五条件使用 Python 实验 API，
没有声称这条 CLI 已自动运行整批五条件。

## 4. 四类结论与剩余工作

| 层面 | 状态 | 可以说什么 |
| --- | --- | --- |
| 工程实现 | 上述 9 项已修复；310 项离线回归通过 | 新版合同和恢复/消费路径可按工程夹具走完 |
| 真实模型 | 本轮未运行，新增 Jev/CPA/OpenRouter 调用均为 0 | 不新增模型准确率、耗时或费用结论 |
| 宿主消费 | handoff 工程验证通过；真实当前宿主实接未运行 | 注入回复不等于真实任务采用 |
| 比较结论 | 接口已补；新版真实五条件未运行 | 不能宣称 Jev 优于、非劣于或等于纯 Codex |

真实历史缺失轮次、当前自然首答、12 个新来源和真实匿名评分产物仍按
[来源准备记录](SOURCE-PREP-20260926.md) 与设计第 0/3/4/5 步处理。未编造来源填空，未更改旧账本、
旧 OCI 路径/hash、历史分数或 main。下一步实测应基于本次新实现冻结；不能拿旧 admission 继续写入。
本轮没有新的独立审计；回归通过不代替独立审题和真实任务评阅。
