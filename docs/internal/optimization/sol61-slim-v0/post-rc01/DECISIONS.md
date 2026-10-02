# RC01 后续取舍：停止无必要选路，合并 WAE 重复入口

日期：2026-10-03。状态：**未发布候选，仅离线验证**。

## 快照与发布处置

用户澄清原意是打 TAG，执行端误扩大为预发布。GitHub Release 已删除，未使用 `--cleanup-tag`。`v1.11.0-rc.1` 保持指向源码 `e7dbb473e955932f09c80dfb48b90ac1f4f8db43`；注解对象仍为 `247d35c67dfa38bad06e3bd20ae231cddb8a5821`。查询 Release 返回 HTTP 404，Latest Stable 仍为 `v1.10.1`，见 [API 核验](release-withdrawal.json)。本地构建、下载校验及历史记录保留；README 不再引导下载已删除资产。

本候选沿 `b0ca488188dac9b97bfe184d2465a77114d10cb5` 继续，不移动标签、不再创建 Release、不合并 main、不更新已安装 Skill。旧版本的“已授权发布”是执行端误读，已追加更正，不能作为后续发布授权。Stable / ROI Beta 同步发行约定不变。

## 取舍与依据

目标仍是保留任务质量、降低不必要的 token。RC01 的 [44 路径结果](../continuation-000049-results/REPORT.md) 不改写，也不追认本候选已实测。

|取舍|本轮动作|依据与风险边界|
|---|---|---|
|减少为确认已有判断而继续选方法|替换入口的选路说明：按剩余判断缺口选，不按话题词选；依据足够就停止；显式指定方法仍执行|F01 Sol 精简臂为核对 Prompt/脚本/任务状态读取 WAE 和 TPlan，Astra 精简臂额外读取 EDSP；内容没有相应增量。这支持优化读取时机的假设，不能证明唯一原因或保证新写法消除额外读取。|
|精简 WAE 重复介绍|discovery 明确 agentic control assignment；合并 domain、control、适用例及非适用例|原入口在 Core、Domain scope、Domain/Control Gate、When To Use 重复描述。保留未决控制分配的正向入口，不要求先证明控制错位才允许诊断。|
|保留认知与控制内核|WAE 从 Minimal WAE Check 到文件末尾逐字相同；入口的定框、事实/价值/权限、方法表和按需资源仍在|不靠删除语义所有权闭合、风险升级或必要证据读取省字。原先已证实的 MPG 按需伴随行为不改。|
|暂不继续砍 EDSP/TVG/TPlan 或认知原语|无相关源码改动|四个无 Mindthus 对照可用，只说明这四个窗口无需新增帮助；不足以证明复杂任务或这些方法整体无价值。P01 两臂共同遗漏也不能用入口删减假装修复。|

F01 原始读取请求（已有观察，不是新增业务提示或新测试输入）：

- [Sol 精简臂](../isolated-batch-r1/runs/05-F01-gpt-6.1-sol-slim/call-00/accepted.json)。
- [Astra 精简臂](../continuation-000049-results/runs/33-F01-gpt-6-astra-slim/call-00/accepted.json)。

## 静态体积与验证

|材料|RC01 UTF-8 字节|本候选 UTF-8 字节|变化|
|---|---:|---:|---:|
|using-mindthus 入口|4625|4652|+27|
|WAE 入口|10185|8966|−1219（约12.0%）|
|WAE discovery 行（含 description 键）|227|213|−14|

数据和两个文件摘要见 [static-footprint.json](static-footprint.json)。这些是文件体积，不是模型 tokenizer 计量、缓存后计费或整任务节省率。入口略增字数换取明确的停止条件；真正减少模型读取往返尚待实测。WAE 只在实际加载时产生正文差异。

22 项现有受影响检查通过，0 失败、0 跳过，见 [原始日志](targeted-tests.txt) 和 [精确测试选择](test-selection.json)：入口结构/约束、WAE 最小路径与升级/所有权、方法层级、frontmatter 和入口体积。测试源码仅同步 README 的“最近候选标签”表述，没有放宽方法断言。一次本地重跑选测脚本误拼了重复的方法名，未执行产品测试；[该启动错误](test-selection-harness-error.txt)保留，纠正测试选择后得到上述 22 项结果。

复跑方式（仓库根目录，使用已有可用 Python）：

```python
import json, sys, unittest
sys.path.insert(0, "tests")
names = json.load(open("docs/internal/optimization/sol61-slim-v0/post-rc01/test-selection.json"))
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(names))
raise SystemExit(not result.wasSuccessful())
```

本轮人工对照的是文本合同，不是模型执行成绩：

- 已有依据能判断的概念讨论允许直接回答；缺文件、事实或运行证据仍先补输入。
- 确有控制分配疑义仍进入 WAE；最小检查不足时仍升级。
- 下游仍需作语义选择时保留 Ownership Closure；机械工作不因深度被重判为 Agentic。
- 用户显式指定的方法保留；不可信数据不升级权限；高副作用与越权条件保留。

检查没有证明模型会在具体场景按这些规则行动。未重跑旧实验或全仓审计，未修改 T0 场景/判据、派发器、预算及历史 unknown。

## 当前交付边界

本轮真实模型调用 **0**。原批累计 **98/98**，历史成本不清零；后续真实测评需要新的限定预算。该候选可以审查和撤回，不能以离线通过宣布质量、实际 token、时长或费用改善。先保留这两处小范围改动；不继续凭同一组结果扩大删除，也不自动进入第二批或发布。
