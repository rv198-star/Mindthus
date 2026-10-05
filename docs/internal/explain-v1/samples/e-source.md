# E：TPlan 工作进展视图

本样例全部是合成演示数据，不是 Mindthus 或任何真实项目的进度、工作量和验收结果。

## 来源与产物

- [任务输入](e-tasks.json)：六个根工作块，含 pending、blocked、paused；公共转换入口随后将 T1 改为 active。
- [规划输入](e-work-plan.json)：同单位剩余区间、明确前置、并行条件，以及可选风险和阻塞各一条。
- [实际文字输出](e-report.txt)与[实际离线 HTML](e-report.html)：通过公共 CLI 生成，未手工改写输出。

六块剩余估计分别为 2–4、3–5、1–2、2–3、4–6、1–2 小时，因此同口径总量为 13–22 小时。40 percent 是源计划中明确标注的人工显示样本，与该总量独立；它不由任务数量或历史成本推算，也不是验收结论。

本样例没有创建任何合格验收事件。初始化声明验收要求、更新规划元数据、切换源状态，并不等于完成这些要求。

## 复现

从仓库根目录执行。新建临时目录以免影响已有 Mission；源输入保持原样。

```bash
EXPLAIN_DEMO_DIR="$(mktemp -d)"

python3 skills/tplan/scripts/init_mission.py \
  --dir "$EXPLAIN_DEMO_DIR/mission" \
  --mission-id mission-work-plan-six-blocks \
  --title "演示数据：六个工作块的进展视图（非真实项目）" \
  --objective "演示数据：展示六个根工作块的当前状态、剩余区间和前置关系；所有数字与文案均为人工样本，不对应真实项目或真实验收。" \
  --acceptance-evidence "A-DEMO-1:演示数据：仅声明演示结构用途；不是任何真实项目的合格验收证据。" \
  --task-json docs/internal/explain-v1/samples/e-tasks.json \
  --human-in-loop 0 --risk-tolerance 50 --resource-sufficiency 50

python3 skills/tplan/scripts/record_work_plan.py "$EXPLAIN_DEMO_DIR/mission" \
  --input docs/internal/explain-v1/samples/e-work-plan.json \
  --summary "演示数据：录入六块规划样本，仅更新元数据，不是业务推进或验收证据。"

python3 skills/tplan/scripts/transition_task.py "$EXPLAIN_DEMO_DIR/mission" \
  --task-id T1 --status active \
  --outcome-summary "演示数据：将 T1 激活为界面样本，非真实项目执行或验收。"

python3 skills/tplan/scripts/render_progress_view.py "$EXPLAIN_DEMO_DIR/mission" \
  --format html --out "$EXPLAIN_DEMO_DIR/progress.html"
```

生成时间和运行时来源应反映复现环境，不要求输出逐字节一致。

## 浏览器验证

2026-10-05，在 Chromium 离线环境以 1440×1024 和 390×844 两种视口实际打开保存的 HTML。默认展开层只显示整体进度、剩余总量，以及六个剩余工作块的状态、剩余量和占比条；风险、阻塞、依赖、证据、搜索和详细表格保持在默认折叠区。桌面视口中整个核心看板结束于约 927px，折叠详情入口约 955px，核心信息可在一屏内读完；390px 窄屏保持同一信息层级并纵向排列。两个视口均无页面横向溢出、外部 HTTP 请求或 JavaScript 异常；点击任一工作块会展开详情并定位对应依据。

这验证的是实现与源信息之间的对应关系及页面可用性，不证明真实项目的估计准确性，也不构成跨模型效果统计。
