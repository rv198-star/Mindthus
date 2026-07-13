# Method Fidelity Usage Log

## 定位

`v1.0` 让单次 fidelity judge 可复现、可打回。`v1.0.1` 的小改是把每一次真实使用变成可积累的数据。

这不是新方法，也不是自动判断器。它只是一个轻量习惯：

> 每次真实使用某个 Mindthus 方法并完成 judge 后，追加一条可脱敏日志。

## 为什么先做这个

如果只看单次输出，Mindthus 只能回答“这一次有没有按纪律执行”。一旦积累几十到上百条记录，项目才有可能回答更重要的问题：

- 哪个方法的约束增益最大？
- 哪个方法加了约束也没有明显收益？
- 哪些模型更容易被结构约束改善？
- 哪些场景其实应该砍掉方法，而不是继续扩写方法？

这条线服务于“收敛而非扩张”。它的目标不是证明所有方法都有效，而是让项目有能力用数据砍掉测不出效果的东西。

## 记录字段

默认日志路径：

```bash
data/fidelity-usage-log.jsonl
```

每行是一个 JSON object：

- `schema_version`: 固定为 `mindthus-fidelity-usage-log-v0.1`
- `logged_at`: 记录时间
- `record_type`: `real_use`、`evaluation` 或 `fixture`
- `scenario`: 脱敏后的场景摘要
- `method`: `3L5S`、`SELA`、`MPG`、`EDSP`、`WAE`、`TVG`、`tplan` 或 `using-mindthus`
- `model`: 产出方法结果的模型
- `judge_model`: judge 来源，可为空
- `baseline_score`: 未加约束版本分数；没有 baseline 时可为空
- `constrained_score`: 约束版或真实使用版本 judge 分数；无 rubric 的真实任务可为空
- `max_score`: 该 rubric 的最高分；无 rubric 的真实任务可为空
- `score_delta`: 有 baseline 时等于 `constrained_score - baseline_score`，否则为空
- `constraint_helped`: `yes`、`no`、`mixed` 或 `unknown`
- `invocation_mode`: `explicit_router`、`explicit_skill`、`automatic_best_effort` 或 `unknown`
- `decision_changed`: 是否实质改变判断或行动
- `rework_reduced`: 是否减少下游返工
- `overhead_level`: `none`、`low`、`moderate`、`high` 或 `unknown`
- `harm_observed`: 是否造成更差判断、延误或额外负担
- `mechanism`: 脱敏后的重复成功或失败机制，供跨任务聚类
- `source`: 可复核来源，例如 issue、测试包、artifact 路径
- `notes`: 简短备注
- `tags`: 标签列表

## 使用

追加一条真实记录：

```bash
python3 scripts/log-fidelity-usage.py \
  --scenario "SELA 判断旧流程是否继续投入" \
  --method SELA \
  --model "gpt-5-codex" \
  --judge-model "human-review" \
  --baseline-score 7 \
  --constrained-score 10 \
  --max-score 12 \
  --constraint-helped yes \
  --source "#27" \
  --tags "real-use,sela"
```

没有 baseline 时也可以记录：

```bash
python3 scripts/log-fidelity-usage.py \
  --scenario "MPG 判断主线兑现前的路径承载" \
  --method MPG \
  --model "gpt-5-codex" \
  --constrained-score 8 \
  --max-score 10 \
  --constraint-helped mixed
```

自然发生的真实任务不需要强造 rubric 分数：

```bash
python3 scripts/log-fidelity-usage.py \
  --scenario "脱敏后的真实任务摘要" \
  --method using-mindthus \
  --model "gpt-5-codex" \
  --constraint-helped mixed \
  --invocation-mode explicit_router \
  --decision-changed yes \
  --rework-reduced unknown \
  --overhead-level low \
  --harm-observed no \
  --mechanism "纠正了实现层事实接管定义层判断"
```

校验日志：

```bash
python3 scripts/log-fidelity-usage.py --validate --log data/fidelity-usage-log.jsonl
```

Fresh checkout note: if the default `data/fidelity-usage-log.jsonl` file does not
exist yet, validation reports `Records: 0` and exits 0. Missing non-default log paths
still fail, so a typo is not silently accepted.

## 边界

- 日志只保存可脱敏摘要，不保存完整隐私上下文。
- 脚本只检查字段和分数形状，不判断方法是否真的有价值。
- 单条记录不能证明方法有效；只有累积样本才有分析意义。
- `constraint_helped` 是人工或 judge 的观察，不是自动真相。
- v0.1 的新增真实使用字段是向后兼容扩展；旧记录没有这些字段仍可校验。
