# GJ-03 relation消费残留：单点返修

受审父提交：`f7d75a8f21af8bbd2571c6ba187d75a24f158fd9`。
独立结论：GJ-01/02/04 CLOSED；GJ-03仅剩target finding消费原始R的问题。
本次不重开其他项或设计，旧记录均保留。

唯一生产代码diff（core.py的finding）：

```diff
-relation=v('R')
+relation=adopted_value(atoms.get('R',{}))
```

[针对性日志](tests.log)：3个新增反例测试加6个受影响回归，9通过、0失败、0跳过。
新增测试通过实际round3返回建立有效reanchor，再检查：

- R=overreach且所选概率0.6：目标发现保留，发现relation=null；原始R与low_confidence limitation保留，顶层仍unresolved。
- R缺失或invalid：目标发现保留，不输出确定关系；已有invalid limitation保留。
- 已采纳sufficient/overreach/contradicts：关系仍可消费，retain/limit/recheck及独立reanchor不受影响。

本轮未重复整套实现审查或生成旧开发轨迹，未运行真实模型，预算未增加。
13题、三轮、检查/修订上限、设计基线、旧③/六案/R2均未改。
这是作者单点修复与受影响验证，交回仅该处复核，不自称独立PASS。
