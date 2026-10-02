# #220 首批隔离偏差、实际产物与定点修复

本轮产品减负候选已实现并提交；T0规定的真实隔离对照尚未完成。
执行端错误地将CLI工作目录放在仓库下，导致34次真实调用全部继承项目AGENTS。
这不是模型能力失败，也不能将所得答案和开销当作T0约定的隔离对照通过。
未修改冻结输入、独立判据、main、已安装Skill或旧#211记录。

## 已执行及保留的事实

- T0固定提交：`d73aec69394dd70df0bbd321451b940622a06156`。
- 当前版材料：`1527f32b99c375db9ff73f80812c644686a6576a`。
- 精简候选材料：`31a145cf6608908fc4cdd6303b8c59baa0745a19`。
- 官方适配器固定：`ed5171bf7b34746027acd730864d9c98ef1dd8d2`。
- CLI：0.159.2；已实际发送均为`gpt-6.1-sol / medium`、已登记官方HTTP配置。
- 44条计划路径中22条已有真实答案，另22条未发送。34次逻辑调用/CLI启动，包括12次必要资料读取；所有34次均明确返回。
- 0个unknown、0个新安全拒绝、0条可观察内部恢复日志。精确底层HTTP数和金额仍为unknown。
- 在明确终态后的冷却窗口停止driver，没有取消在途模型请求，没有停止后补发。

已交付D01、I01、F01、F02、M01、M02、E01、W01、W02、P01、P02的Sol当前/精简两臂。
R01、V01、V02、L01、L02两臂及8条Astra、4条无Mindthus对照均未发送。
预备的R01请求文件没有intent，属于未发送，不能写成unknown。
每份原始答案位于 `contaminated-batch/runs/<序号-场景-模型-臂>/answer.txt`；
同目录保留请求、待发送格式、原始CLI返回、真实终态、accept和计量。

| 已付开销 | 实际观测 |
|---|---:|
| 宿主CLI会话 | 650.209秒，约10分50秒 |
| 主动冷却等待 | 1979.413秒，约32分59秒 |
| 活动墙钟：首个意向到末次终态 | 2630.765秒，约43分51秒 |
| 原始输入token | 813710，其中cached_input 304640 |
| 原始输出token | 10339，其中reasoning_output 2920 |

CLI会话不是纯HTTP耗时；墙钟不含此前工程与材料准备。
这些是无效对照的实际成本，不能删除，也不能据此宣称减负收益或模型退步。
`executor-assessment.json`中的内容笔记仅供定位原文，不构成隔离验收结论。

## 可绑定的偏差证据

`contaminated-batch/bound-context-index.json`将34个真实thread.started ID绑定到各自已有rollout归档。
34/34存在项目AGENTS用户指令；首个原始指令事件另存于
`first-thread-project-instructions.json`。只读取此次调用的绑定归档，没有查找账号凭据或其他聊天。
原始serial、意向、终态、停发记录全部保留。归档不复制重复的source缓存及锁文件；
材料由固定Git提交重建，材料摘要和实际加载原文在batch/wire中保留。
`evidence-index.json`只索引本次新归档，不声称重审旧实验全部哈希。

## 最小修复与离线验证

1. 原适配器生成cwd的位置保持不变，仅把本实验传输输出目录迁到
   `/private/tmp/mindthus-slim-cli/<配置摘要>/<批次摘要>/<请求摘要>/`。
   派发前检查不在仓库内且祖先无AGENTS/.git；证据仍复制回绑定账本。
2. 记录真实绑定线程的cwd及项目AGENTS观测。目录不符或再次继承项目指令时，
   保存真实结果并停止后续派发。归档不可得明确记未核验，不伪造通过。
3. 旧根禁止继续派发；后继必须绑定旧账本并扣除已用34次。
   未授权的预算提案不能执行，无通用ignore-unknown或重置余额开关。

`engineering-evidence/isolation-and-lineage-10.txt`：10通过、0失败、0跳过。
包括5项原派发回归及5项隔离/后继反例；均为模拟传输/时钟，模型调用0。
覆盖仓库祖先指令不进入外部工作目录、旧模式停发、提案不可发送、34次扣账、模拟父记录不能作为真实父记录。
原361项日志保持，不重复全套测试；这些测试不能代替真实隔离效果验证。

## 可执行后继及尚待预算确认

原64次硬上限剩30次，即使每路径只调用一次，也不足覆盖44条隔离路径。
具体建议：累计总上限98次；旧34次继续计费记账，修复后最多64次，
相当于复用原剩余30次并额外增加最多34次。
仍为44条既定路径、每条最多3次、不追分重试、不调用Jev或评审模型。
不因预算未用完追加案例或生成；既定未知/安全拒绝规则和60秒间隔保持。

`successor-parent-receipt.json`绑定原34次意向与明确终态；
`successor-admission-proposal.json`的`execution_authorized=false`，仅供具体审批，当前不允许运行。
只有收到Owner针对新增预算的批准，才追加实际授权记录并使用以下入口：

```sh
python3 docs/internal/optimization/sol61-slim-v0/run_batch.py prepare NEW_BATCH_DIR \
  --adapter-root /Users/william/.codex/worktrees/jev-direct-continuation/Mindthus \
  --candidate 31a145cf6608908fc4cdd6303b8c59baa0745a19 \
  --parent-batch /Users/william/Projects/Github/Mindthus/.tplan/slim-eval-v0-20261002 \
  --admission ACTUAL_OWNER_AUTHORIZATION_JSON
python3 docs/internal/optimization/sol61-slim-v0/run_batch.py run NEW_BATCH_DIR
```

调用级禁用Skill自动发现及插件、官方服务/认证、模型和medium保持一致；
项目工作目录隔离改变了执行接线，没有关闭安全检查。
仍是Codex共同系统环境，无Mindthus臂不冒称完全无系统提示的API。
T0场景/规范不修改；旧22份答案封存为偏差产物，不挑选后替换成最优答案。
#220、Epic #213和draft PR #223保持未完成/未默认采用。

后续接线审计更新：四项返修及自复审见 `repair-review-r1/REVIEW.md`。
上面的31a145命令保留为本报告写成时的历史示例。下一真实后继应固定包含
Profile返修的新候选SHA，并使用已批准的授权记录；pending提案现在连prepare也会拒绝。
同一父账本只能绑定一个后继根；修复没有增加真实调用预算。
