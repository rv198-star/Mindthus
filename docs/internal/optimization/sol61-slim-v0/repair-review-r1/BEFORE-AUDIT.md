# PR #223 定点代码审计

受审：0171ce3ca2d8a05c623f5fa87bda03a8240d3ce9
比较基线：1527f32b99c375db9ff73f80812c644686a6576a
结论：REVISE。两项派发/预算问题应在下一真实调用前修复；另有交付分类和Profile合同两项问题。
审查者是当前执行Agent的另一次审计，不声称独立盲审。没有真实模型调用、授权预算变更或工作树代码修改。

## 1. P1：格式失败绕过内部恢复停发条件

位置：docs/internal/optimization/sol61-slim-v0/run_batch.py:278–293。

observe()发现无法归类的内部重发后会置stop_subsequent_dispatch并写transport-stop-v2.json。
但driver在非returned或invalid_read_contract分支先break，停发逻辑位于其后；入口也只检查STOP.json。
模拟首个CLI有明确turn.completed、坏JSON、retrying sampling request日志时，记录了failed并继续第二个调用。
另一组合法JSON但重复读取已加载路径的模拟返回同样继续。
两组均出现transport_stop=true、driver_stop=false、fake_invocations=2。

最小修复：把恢复停发处理移到所有返回/格式分支之前；保存本次真实终态和产物后停止下一派发，重启也遵守该停止记录。
不将所有格式失败变unknown，也不自动重发。

## 2. P1：同一父账本可产生多个各自满额的后继

位置：run_batch.py:126–134、179–195。

后继额度只按原父账本34次计算。prepare可以对同一父摘要建立多个新根，各得64次额度；
锁与serial位于各自batch，不汇总兄弟后继，也没有在父记录侧绑定唯一后继。
即使以后只批准一次累计98次，两个新根仍分别满足34+64<=98；先后或并行运行会突破累计额度，并可能违反单发送者/跨根60秒间隔。

离线创建两个未授权提案得到[64,64]；两者保持execution_authorized=false，审计未假造授权或执行真实调用。
这是代码允许重复后继注册的证明；实际越额/并发没有发生。

最小修复：为这次指定父账本绑定唯一后继根并复用它的锁、serial与消耗；第二根拒绝，不新增通用强制解锁。

## 3. P2：空答案被登记为已交付

位置：run_batch.py:294–296。

复用的host schema允许空字符串；本driver没有非空检查。
真实终态+合法JSON {kind:answer,text:"",read_paths:[],objection:"simulation"} 的离线返回被记录为delivered，生成空answer.txt。
这是“供应商已返回”与“完整答案已交付”混同，会污染交付率和后续逐路径统计。

最小修复：保留供应商明确终态，空白text归入明确无有效产物/格式失败，不标delivered，不额外重试。

## 4. P2：TVG Profile逐句标注规则仍自相矛盾

位置：skills/tvg/resources/value-profiles/plain-sharp-skill-intro.md:79、100；冲突原文35、127、160。

新内容把句子功能标注降为诊断，并允许无需标注直接删除；但priority_order仍写
sentence-function assignment before deletion or compression，density_guidance仍要求先functionalize，
自检第7题仍要求删句前改写为某一功能。实际按需加载该Profile时会重新获得同一强制工作，抵消本轮减负且产生不一致消费。

最小修复：同步priority_order、density_guidance及自检问句，将剩余这项规则限定为具体问题的可选诊断，保留领域价值与veto。
不需要重写Profile或新增方法。

## 实际验证与范围

- targeted-tests.txt：15通过，包括派发隔离/预算/unknown及语义误拦检查。
- validator-packaging-tests.txt：122通过，涵盖原语、using-mindthus显式合同、发布包布局/资源。
- reproduce.py：只用Fake与模拟时钟；三组返回反例及重复后继提案，结果见counterexamples.json / counterexamples.log。
- 共137个既有针对性测试通过；没有把反例算作新增业务样本，也未声称全仓审计或模型质量通过。
- 阅读了入口、共享原语、3L5S、SELA/MPG/EDSP、WAE、TVG/Profile、TPlan、校验器、打包与新派发改动。
- 本范围未发现权限/证据硬边界被普遍删除；这不代替真实语义对照，也不构成产品采用PASS。
- 旧34次的AGENTS污染已经作为历史偏差封存，本审计不将其重复列为新缺陷；上述发现针对当前代码。
- 新98次预算仍未批准。修复前不建议继续真实对照或合并PR。
