---
name: "3l5s"
description: Use when a problem is unclear, noisy, repeatedly reworked, or too large to execute directly; also use when a task list looks structured but may not be executable, verifiable, or tied to a falsifiable problem.
---

# 3L5S

## Core Claim

不清楚问题时，把信号变成可复述、可定位、可证伪的问题；问题已经清楚但过大时，
把它变成可启动、可验证的行动。已明确的小问题直接修复与受影响验证即可。

## Mainline

- `Discovery -> Definition -> Resolution`：只在观察、问题与解法尚未分开时使用。
  先取得真实信号，再定义可证伪问题，最后落地；不用摘要替代根因证据。
- `Single-layer BTGSB`：问题已足够清楚，直接检查 Baseline / Target / Gap /
  Strategy / Breakdown（基/标/差/策/拆）。信息已在任务中给出时复用，
  不重新填表；输出最小可执行动作与验收证据。
- 子项只有因具体依赖无法开始时才进一步拆分，不机械递归。

## Guardrails

保护问题定义和落地，不替代领域证据或 stakeholder 判断。
重复返工无证据增量时回查问题、目标和策略；两次补规则后拟新增第三层时，
先反螺旋，优先删除或根因替换。新反例支持的普通调试可以继续。
完整模板或 script pass 不是根因正确、策略正确或语义通过。

## Boundaries

结构判断可直接 EDSP；系统/局部趋势直接 SELA；承载路径直接 MPG；
Agentic 控制错位用 WAE；多个已可判断事项争资源用 SRA。
3L5S 不成为其他方法的必经母流程，也不重开已接受的定义。

## Runtime Support

已有清楚动作时不加载全套模板。仅在对应缺口时读取：

- `resources/landing-method.md`、`templates/single-layer-btgsb.md`：复杂问题落地。
- `resources/three-layer-recursive-loop.md`、`templates/three-layer-3l5s.md`：信号/问题/行动仍混合。
- `templates/loopback-record.md`：记录具体反馈、证据增量和返回上游原因。
- `resources/script-boundary.md`：脚本边界。
- 明确 fidelity contract audit/replay：`resources/fidelity-contract.md`、`templates/fidelity-output.json`、
  `scripts/init_3l5s_run.py`、`scripts/check_3l5s_run.py`、`scripts/validate_3l5s_output.py`。
  脚本只验证结构和引用，不决定重要性、根因、策略或 acceptance。
