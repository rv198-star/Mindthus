# 修复后入口和验证用法

这是同一entry/Episode/CurrentAgentHost上的新实现。旧版本及历史freeze只作只读证据；不要把旧目录改hash后恢复到这里。

## 当前宿主交接

`comparison_v03.prepare_condition`默认`material_policy=entry_selected`：首轮读取真实`skills/using-mindthus/SKILL.md`和八方法目录，不读取八正文。
宿主需要正文时返回`artifact_action=read_methods`与`requested_methods`，正文由程序真实读取，记录入同一Episode。它不等于真正运行了方法。
完成答复再返回`replace`；复核保留原文用`retain`。只有已读取的方法才能写入`performed_methods`。
预算允许时，复核阶段也可以请求新方法；额外步骤计入原执行额度，不能侵占最终接收预留。默认至多两批方法读取。
`all_methods_diagnostic`显式保留全集预载诊断，不能把该结果标成正常入口。

## 有限回答与路线承诺分开

只有低风险、无共同义务、无依赖、无强制读取、局部覆盖成立，且唯一主方法候选处于既有不确定区间时，允许`limited_response`。
宿主必须提供来源绑定的`method_boundary`、显式`scope_status=bounded_answer|unresolved`；`performed_methods=[]`。
这不是把概率阈值降低，也不重新选择方法：原方法路由保持未决，实际有界正文可以进入S1和最终宿主接收。
S1、纠偏和接收都看得到该边界；文本语义仍需判断，空方法列表不是“没有假执行”的自动证明。

## 三类结果分别读

- `routing_complete`：已安排事项的方法路线是否明确。
- `delivery.accepted_outputs`：真实被接受的正文与hash；`delivery.pending/unassigned_scope`保留未决。
- `consumption_complete`：内部全部消费是否结束。它不是用户任务正确率，也不能取代逐维内容评阅。

组织器返回`coverage_disposition`，将不能承接的独立交付或共同前置绑定原文。
独立遗漏不抹掉其他已就绪结果；明确共享前置/未知影响范围会保留受影响事项。预算不足在新增Jev调用前拒绝，不偷偷增加配额。

## 可移植小批入口

```sh
python3 docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py prepare \
  --root /absolute/new/state/root \
  --source /absolute/path/to/original-source.json \
  --scenario E --cutoff 0 --phase initial \
  --codex /absolute/path/to/codex --model gpt-6-sol --effort xhigh \
  --host-endpoint configured-current-host
```

root必须尚不存在且在仓库外，source使用归档中的原始v2 packet（也接受有payload的记录包装）。prepare本身无模型调用；记录来源窗口、入口/运行代码/driver hash与预算。

```sh
python3 docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py step \
  --root /absolute/new/state/root --condition pure_codex
```

`step`返回原宿主handoff；当前Agent依据请求执行，使用同一入口`--reply submission.json`提交。`drive-codex`是显式的当前Codex CLI传输：新分支独立会话、分支内resume，仍通过原submit_response验证，不创建CPA客户端。

真实Jev分支读取进程中已有`TYPESAFE_API_KEY`，不在本文件、源代码、命令参数、输出或Git里存密钥。旧安全拦截不是允许绕过工具边界的理由；失败/未知调用保留，不重新提交。

## 对照解释

E��一条问题可用于新的首答组件与新实现的两轮轨迹；缺失的原始中间助手答复不能补写。
F最初需要图片而图片未取得，不能冒充原始首轮复现；纠正后F快照可作回归，但不是自主首答能力。
`evaluation_integrity`分别绑定可见前缀、分支实际执行与最终接受、评阅实际方法加载；金标准不进入生成请求。
旧可用性评分不迁移成新维度通过。用户任务可用、特定失效是否出现、完整调用成本、未决事实分别报告。
