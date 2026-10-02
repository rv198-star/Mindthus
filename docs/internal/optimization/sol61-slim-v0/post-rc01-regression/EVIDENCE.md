# 本轮证据导航

- [结果及限制](REPORT.md)；[40条答案](PATHS.md)；[20组配对](PAIRS.md)。
- 调用前：[PLAN](PLAN.md)、[授权](admission.json)、[配置](batch.json)、[配置/输入绑定](batch-binding.json)、[题文与规范](inputs.json)。规范不进入业务提示。
- 原始证据：`runs/` 内40份 `answer.txt`、40份 `result.json`、59套 `call-XX/` 请求/返回/终态及计时；`scheduling/serial/` 内59对意向/completion。目录名以PATHS链接为准。
- 机械请求/返回对账：[delivery-binding-check.json](delivery-binding-check.json)。内容核对及答案摘要：[assessment.json](assessment.json)。两者范围不同。
- 原始用量与计时保留在每次 `terminal.json` / `measurement.json`；[逐路径汇总](path-status-40.json)、[按模型/臂汇总](groups.json)、[总量](totals.json)、[配对数据](pairs.json)。
- [运行日志](driver.log)、[启动冷却](parent-cooldown.json)；[开始](start-checkpoint.json)、[中点](midpoint-checkpoint.json)、[Sol完成](sol-complete-checkpoint.json)、[最终检查点](final-checkpoint.json)。
- [新增准入相关20项模拟测试](scoped-wiring-tests.txt)，不把它当作内容效果或独立审计。
- [TPlan执行报告](execution-cost-tree.md)、[过程图](execution-cost-tree.svg)是整个减负Mission的累计运行视图，不是本轮59次供应商计量；本轮计量以totals及逐调用原始记录为准。Mission未自动标成已发布。
- [文件摘要清单](evidence-index.json)：仅本目录逐文件SHA256及字节数，排除清单自身；用于定位/防误改，不声明独立全量工程审计。包含先前提交的准入文件及本次新增真实产物，不含旧批原始证据。

可从归档重算三份机械汇总（写入新目录，不覆盖原证据）：

```sh
python3 docs/internal/optimization/sol61-slim-v0/post-rc01-regression/collect_metrics.py \
  docs/internal/optimization/sol61-slim-v0/post-rc01-regression \
  /tmp/mindthus-post-rc01-derived
```

未暴露的HTTP请求数和金额继续unknown；旧000049仍远端未知。本目录没有新模型探针或补试。
