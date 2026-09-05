# 方案审计 B：工程迁移与归档

日期：2026-09-05
对象：docs/internal/maintenance-20260905-plan.md v1.1
源码基线：1de31845cce25126651231d51047564eb055e1da
载体：本会话 ChatGPT 自身第二轮；与 A 分开检查工程风险，不声明不同模型或认知隔离。

## 审计问题

重构能否维持事务、来源和公共调用边界？归档是否保留真实恢复路径？工作包的交付状态能否被核对？

## 检查与发现

1. runtime-manifest.json 当前只列出原大文件和适配器。抽取的实际实现模块必须同步进入 required_scripts/fingerprint_files；删除模块应阻断，修改应改变指纹。禁止用“行为没变”绕过旧 Mission 的来源不匹配。
2. tplan_runtime.read_mission 在锁内恢复 pending transaction，不能直接当作无副作用 query 提取。一个锁和一个错误类型保持，事务簇最后处理；纯函数、schema、展示优先。
3. SRA 原 facade 的星号导出形成真实消费者耦合。先确认实际 imports，保持公共入口，再逐片显式内部导入；禁止模块回导 facade 或复制函数制造两份 owner。迁移后的故障注入应打到实际 owner。
4. #145 要求先清单和恢复复核再删除。v1.9.1 release commit 是已有不变恢复源；必须固定完整 SHA、树及 blob。只删 HEAD 不减历史 clone 体积，收益限于检索和维护。报告、污染证据、汇总和材料性 redline 默认保留。
5. 默认 CI 不应为验证归档自动获取全量历史日志。清单的生成/复核与普通离线测试分开；引用包括代码块和程序路径，不能只扫 Markdown link。
6. 测试大量退役与对应高风险实现搬迁不能同一 PR；阶段分别提交。若本轮只完成一个拆分片，issue 保留其余复选项，不声明整项已完成。
7. 发版、重写历史、修改旧审计结论不在授权范围。需要新记录说明当前结果，而不是把旧 PASS 改写成新验证。

## 结论

v1.1 的分阶段约束覆盖上述工程风险，允许创建 issue 并依次实施。#145 的删除 gate 仍需对具体 inventory、恢复结果和引用解析复核，不由方案 PASS 自动替代。

Verdict: PASS for staged implementation; archive deletion requires its own evidence gate.
