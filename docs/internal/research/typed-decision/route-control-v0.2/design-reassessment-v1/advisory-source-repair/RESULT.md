# 4K 建议式返回合同修复

## 已修复的根因

旧①要求 objection=null，把“来源缺失但能给有限答案”与“必要条件缺失无法继续”一起拒绝。
现在合法异议可以进入运行时；由原宿主显式给出 answer / bounded_answer / unresolved，按该处置继续或保持未决。
旧回复没有新字段时，有异议默认 unresolved，不把它悄悄改成通过。原文、引用、原作者上下文全部保留。

另一个实际兼容问题：原4K回复同时引用用户/原始来源和历史助手转述。现在逐一校验所有引用，
允许历史助手作为争议上下文，并要求至少一条 user/source 依据；历史助手不能单独充当事实证据。

bounded_answer 限来源/范围和方法边界，不适用于权限、依赖、新事实异议；原有必要事实与依赖检查保留。
异议随输出进入最终接收证据，最终宿主仍可拒绝。②合同未改，旧失败记录未改。

## 工程验证

**325 项相关测试通过**。新增7项覆盖：

- 原封存5.6 Sol 4K拒绝回复不改正文和异议，修复后通过字段/引用校验，默认仍未决。
- 显式 bounded_answer 进入原宿主接受，异议和限制可见，接受绑定正文 hash。
- 必要未知不能通过，同时不阻止独立事项接收。
- 错误引用、权限异议放行、空的有限答案被拒绝。
- ②严格合同不变，完成后重入不重复调用。

测试使用合成观察及封存真实回复回放，不冒充新 Jev 效果。命令：

```sh
TMPDIR=/private/tmp PATH=/opt/homebrew/opt/python@3.13/libexec/bin:$PATH /opt/homebrew/bin/python3.13 -m unittest tests.test_advisory_source_objection tests.test_route_control_v03 tests.test_comparison_v03 tests.test_route_control tests.test_current_host tests.test_scoped_route_repair tests.test_relationship_runtime tests.test_relationship_assessment tests.test_relationship_live tests.test_observation_assessment tests.test_live_d_adapter tests.test_independent_live_adapter -q
```

## 一次新的真实4K验证

代码冻结 `0d24ec7c4`；全新根目录 `/Users/william/Documents/Codex/2026-09-26/mindthus-advisory-source-repair`。
宿主 gpt-5.6-sol/xhigh，官方 TypeSafe jev-1.13.0，使用相同历史F材料，自行组织三个事项。
原图仍缺失，没有人工代答或补写来源。真实调用为2次 Jev（S0/S1）与5次 Codex（组织、3项执行、最终接收）。

| 事项 | 宿主处置 | 最终接收 |
| --- | --- | --- |
| I1：对楼主实际可用性与“都解决”的判断 | bounded_answer，保留缺图和技术代价边界 | **accepted=true**，绑定实际正文hash |
| I2：核验原图、原话和具体设置 | unresolved | accepted=false，缺少原始材料 |
| I3：逐项验证清晰度、配置、性能、尺寸效果 | unresolved | accepted=false，缺少实测依据 |

三份执行回复全部合法进入运行时，不再出现 v03_advisory_result_required。
原宿主真实接收了 I1 主答；I2/I3 未决原因与原始异议完整保留。
**这是主答已交付、核验项未完成；consumption_complete=false，不能说整批全通过。**
本次没有独立内容盲评，不把宿主接收当成外部事实或 Jev 判断增益证明。

这次是修复验证，不计入旧独立对照成绩：执行槽明确设为4（最多三个事项＋一次最终接收），
执行总时间仍360秒，单次240秒，Jev上限3次。旧比较只给两个执行槽而允许拆出三个事项，
本次避免该预算矛盾遮蔽合同验证；不能将新旧交付差异全部归因于合同一项变化。
旧根目录、预算、hash和失败记录均不改写，不重发旧请求。无 CPA/OpenRouter，费用暂计0，实际未知。

## 证据

- [字段与边界](CONTRACT.md)、[事前计划](PLAN.md)、[真实执行入口](run.py)
- [机器结果](RESULT.json)、[只读记录](evidence.tar.gz)、[摘要](evidence.sha256)

本修复解决返回的合法消费与局部交付，不证明 Jev 提升判断质量。必要未知与整体未决必须继续分别报告。
