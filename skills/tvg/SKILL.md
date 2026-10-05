---
name: tvg
description: Use as a value-directed strengthening loop for bounded AI artifacts that need clearer judgment, evidence, trade-offs, handoff, reuse, or action value.
---

# TVG / Thinking Value-Gain

## Core Claim

把已成形、有边界的产物向具体使用价值推进。已经充分就保留；有明确缺口才改。
好不等于更长、更多结构或更高自评分；compact-strengthen 也是改进。

## Mainline

明确产物服务谁、用于什么、最重要缺口、证据与用户约束。
这就是 expected_value：Agent 从任务解析输出期望值，不给用户增加配置负担。
exit gate 是从该期望编译的内部停机条件；output_profile 只改变交付倾向，不分叉工作流。
沿 default / supplied / inferred-with-warning 选择 value_profile；推断来源需说明，
不能从薄弱产物本身反推应有标准。改善最影响判断、行动、交接或复用的缺口，
随后看产物是否已充分：充分 freeze；需原始事实/根因修复则 return-remediate；
真实 veto 或无权限则 blocked。

一次充分改进可以退出。只有可定位的剩余问题和 next-round positive-value
hypothesis 才继续 deepen/refine；承接已完成判断，不重新跑全套分析。
Thinking Thickness、Grounded Insight Yield、Value Density 是结果视角，
不要求每次分别写评分或三份审查。

## Guardrails

保护定向改进：证据上限、用户风格/价值、权限和 veto_constraints 保持。
veto 是明确不可接受状态，不是加分轴；触发时不能 freeze，脚本不能创建或免除 veto。
高影响、高不确定或交接关键产物仍需 independent_auditor，与生成者分离；不能用生成者自评分
替代必要独立审计。普通可逆编辑不默认加评审调用。
脚本仅做记录、字段与引用校验，不决定 quality、exit_state、Gate success 或继续收益。
pressure 是资源投入约束，不是最低轮数或质量分。

## Boundaries

没有 bounded artifact 和明确 value-gain target 就不用。
TVG audit 只用于 active TVG loop 内退出，不是通用代码、release、事实或战略审计。
canonical model 错误先根因替换，不继续加厚。没有收益假设就停止。
面向用户的结果默认由当前 Agent 使用 Explain 交付，clarity 无需额外指令；
brief / ELI5 / audience / HTML 是按需模式。需要补判断、证据或使用价值才由 TVG
强化；源信息缺口交回原 owner，不用更顺的表达补齐事实。

### Presentation

For human-facing results, use [Explain](../explain/SKILL.md) by default (clarity) in this response; retain method authority.

## Runtime Support / 按需支撑

主路径足够时不用全读 `resources/methodology.md`。只有具体 gate、profile、
pressure 或状态歧义才定位相关章节；0–5 value_gain_scoring_reference 是可选
比较辅助，分数不计算决策。

- 专门价值锚点：按实际用途读 `resources/value-profiles/` 中对应 profile。
  Profile 的领域标准仍有效；句序、逐句标签与增厚配方只是诊断/示例。
- 明确要 trace/replay：`scripts/trace/init.py`、`validate.py`、`persist.py`。
  显式 trace 初始化仍保留兼容的 scoring reference 与 pressure=2 默认值；
  typical_rounds 是参考，不要求跑满。debug_log 默认关闭。
- 显式 fidelity contract 审阅：`resources/fidelity-contract.md`、`templates/fidelity-output.json`、
  `scripts/validate_tvg_output.py`；No schema violations 不等于内容通过。
- 需要图像 atlas exploration 才读 `resources/atlas-search-contract.json` 和 `scripts/atlas/`。
  原有 9→3→9、lineage、交付材料与用户审美归属保留，不当普通文本的默认路径。

业务交付讲清结果与限制，不泄漏内部术语或写作配方。
