# 历史基准归档试点复核

日期：2026-09-05；父项 #167；归档 #145。
载体：ChatGPT 本会话分开的分类复核与恢复/引用复核，不声明外部或新上下文审计。

## 冻结对象

清单提交：237a1af386d5a995525325d7c231ecf906b5b8ab。
清单文件：docs/benchmarks/archive-pilot-20260905.json。
清单 SHA256：e3b9f82d1f253d40f424bcb8f814bf2fa5ffe572083a146c0809cfa464c091da。
来源：d735d11c14d92325607fe6b844eb29f7c426df62（v1.9.1 peeled commit）。
范围：docs/benchmarks/runs/2026-07-09-brake-generalization-dev/repeat-1。

## A：分类与保留复核

范围内37个源文件全部逐行登记，32项拟迁出、5项保留。5项是 activation-summary、
contamination-report、judge-output-schema、run-manifest、summary。父目录 REPORT.md 和
summary-aggregate.json、其他重复实验、latest.md 均保留。

本次试点不是把全库6241项统一批准；其余候选仍需各自完整清单、材料性例外和引用审查。
本范围的32项是逐调用答案、提示、事件、stderr与逐案例评分原始数据。报告所载分数、
激活、污染和非认证边界由保留的汇总/污染/配置支撑；逐案例复查仍可按源提交和blob恢复。
未识别出必须留在日常HEAD、且不能以汇总及精确恢复路径支持的额外红线文件。

分类结论：批准该37项清单的32项迁移，保留5项；不授权扩大目录或通配全库删除。

## B：恢复与引用复核

实际运行：

```text
python3 scripts/benchmark_archive.py --manifest docs/benchmarks/archive-pilot-20260905.json
status=verified
files=37, restored_files=37
migrate_files=32, migrate_bytes=147812
checkout_mutated=false
```

该验证真实使用 git archive 在新的临时目录恢复文件；每个恢复文件以 Git blob 算法重新
计算OID并比较源记录大小。不是仅检查Git对象是否存在。远端 v1.9.1 peeled tag再次查询
匹配上述固定提交；没有创建、移动或重写标签。

引用检查使用 git grep 文件清单加保留报告阅读，不局限Markdown链接。该 repeat-1 的
仓库引用出现在父REPORT和本次同批迁移的回答/原始输出内；没有当前测试或运行脚本消费
该历史repeat。latest.md 保留的父报告入口仍有效。父报告须追加不可变archive base和
清单导航；归档恢复说明给出同一相对路径到精确源SHA的规则。未改写原始历史结果。

恢复工具的4项离线测试通过：全部内容恢复、清单缺行/重复/错blob/错大小/路径越界拒绝、
索引迁移集合准确性，以及不可变来源格式。普通CI用小型临时Git fixture，完全不fetch历史。

工程结论：上述恢复、分类与引用条件满足后，允许仅从Git索引移除清单的32项并加忽略规则，
保留工作区副本为本地历史材料。迁移后必须再次 --check-index、整仓回归和打包，通过后才合并。

## 边界

本次净HEAD减少量需减去清单、工具、测试和恢复导航新增字节，不能把147812字节毛移除量
当作净减量。整个#145仍开放。Git历史和原有证据SHA保持，因此不宣称clone体积明显减少。
