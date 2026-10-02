# 候选实现及执行边界

T0 提交：`d73aec69394dd70df0bbd321451b940622a06156`。冻结四份材料保持原摘要。
产品父版本：`1527f32b99c375db9ff73f80812c644686a6576a`。
此提交是候选代码，不包含真实内容验收结论。未修改 main、已安装 Skill、旧 #211 或默认安全设置。

## 最小变化

- #214：schema、枚举、必填与内部 stdout 泄漏继续阻断；20处词面/句序/标签相似性判断降为 `semantic_hints`。结构通过永远不是语义正确。
- #215：入口及 Frame/Whole 核心缩短，按剩余判断缺口读资源。完整审计只在显式调试/重放使用；旧合同与开发校准保留。manifest 明确其提醒作用域。
- #216：SELA/MPG 仅补未解决的方向或路径判断；EDSP 不要求先经过3L5S。支持已明确时不重跑伴随镜头。
- #217：3L5S 已知小任务直达、已知大任务按需 BTGSB；WAE 嵌套深度和填满字段不自动制造风险或不确定性。SRA 已有 Lite 复用，未再造分支。
- #218：TVG 一次充分改进可退出；profile 的固定句序/逐句标签成为诊断。证据、veto、必要独立退出审计和 trace 兼容仍保留。
- #219：TPlan 文档使用已有 init_lite/checkpoint；只在 consequential 变更时展开 packet。权限、unknown、provenance 和终态脚本没有放宽；成本树文件仍交付，不强制正文整树粘贴。
- #221：发布包跨布局修正共享文档相对链接。安装诊断保留所有已跟踪文件、摘要与稳定合同标记；不再要求旧措辞原样存在。一个共享核心，无模型发行分叉，无版本发布。

## 有关测试

`engineering-evidence/regression-361.txt`：361通过、0失败、0跳过，均为受影响模块。
其中派发5项采用模拟传输/模拟时钟，实际模型调用0。
入口38处旧措辞/固定流程断言由9项条件式合同接线检查替代；旧版本仍在Git。
这些源文件检查不评价模型语义；真实行为另由冻结T0评判。

附加 skill-creator quick_validate 缺少 PyYAML，未执行成功；未安装依赖。
既有发布包测试已实际检查全部入口 frontmatter、资源及运行包布局。

## #220 执行入口

```sh
python3 docs/internal/optimization/sol61-slim-v0/run_batch.py prepare BATCH_DIR \
  --adapter-root PINNED_EXPERIMENT_CHECKOUT --candidate CANDIDATE_SHA \
  --parent-batch PRESERVED_PARENT_BATCH --admission AUTHORIZED_ADMISSION_JSON
python3 docs/internal/optimization/sol61-slim-v0/run_batch.py run BATCH_DIR
```

适配器固定 `ed5171bf7b34746027acd730864d9c98ef1dd8d2`；复用官方HTTP、真实CLI终态分类及单发送者账本。
所有读取、失败计入64次总上限与每路径3次；前一明确终态后至少60秒。未知无自动重发。
当前版和精简版同模型/medium/传输/只读交换能力。保留完整正常按需资源，执行端不按规范挑方法。
两臂及裸对照均使用调用级 `skip_host_skill_discovery=true`、`plugins=false`，避免已安装Skill污染对照；
解析记录确认 guardian_approval/hooks 保持启用。没有改全局配置。
裸对照不加载Mindthus；它仍是同一Codex系统环境，不能称供应商无系统提示的纯裸API。

业务只渲染 prompt/condition，规范和历史答案不进入请求。模拟与真实绑定显式分离。
CLI会话时间不是纯HTTP时间；未暴露的底层尝试与金额保持unknown。

## 首批运行偏差与修复

上述31a145候选首次运行将CLI工作目录放在仓库内，继承了项目AGENTS。
34个绑定线程均确认该污染；22份实际答案保存，不能作为T0隔离对照验收。
派发已停止；34次均有明确返回，无unknown，原64次预算剩30次。
详见 `CONTEXT-FAILURE-AND-REPAIR.md` 与 `contaminated-batch/`。

修复仅调整本实验传输输出目录到仓库外，沿用原官方适配器。
请求摘要、工作目录、线程归档与账本绑定；实际发现项目指令或目录不符即停止后续派发。
父记录和已消耗预算不可重置。10项相关离线接线测试通过，未重复361项回归。
当前 `successor-admission-proposal.json` 明确未授权，不能派发。
修复后的产品材料仍可固定使用31a145候选，不改变T0输入或判据。
