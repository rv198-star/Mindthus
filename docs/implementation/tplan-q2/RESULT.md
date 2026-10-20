# Q2 实施与验证结果

本轮基于Owner“批准动工了”，继承RFC-161 v0.2.1和#235/#238；规格先提交ae48157，再开始代码。Q1两条真实审查缺陷已复现修复，Mindthus#237合并468a007、AIWork#164合并0148f26，均未发包/部署。

## 已实现

仅一个普通observation动作：显式新Mission启用command_results；命令结果与证据复用原Mission持久事务，不新建Host批准表。同ID同载荷/主体重放，异内容冲突；结果绑定证据字节摘要。查询无隐式恢复；显式恢复核对原writer并前滚，不发送外部操作。旧CLI输出保持，guard不被普通新命令解除，不增加Owner/验收/派工权限。

候选runtime为1.6.0-q2.1；旧版运行时不变、未迁移安装包或Mission。Q2代码是新能力候选，**不是正式版本发布**。Q1 provider和AIWork独立消费者成对接入历史结果DTO，明确历史提交不等于当前决定。

## 实际证据

- Python定向检查100项全部通过：新命令21、Q1查询17、来源兼容13、持久事务6、权限完整性30、interaction guard12、真实打包布局1项（含5子场景）。
- AIWork真实Node/CLI消费者11项通过。
- 既有packaging/docs 41项：40通过，1项按其原条件跳过；未把跳过计入通过。
- 五种发行布局：Claude/Codex插件、Claude/Codex/OpenCode portable；真实构建、tar归档、干净解包后init→record→query→replay通过，五布局runtime build相同，包内无测试生成的pyc。
- 新命令测试使用多进程和os._exit，覆盖准备后中断、前滚中断、回应丢失、同ID竞争；恢复不重复证据，错build/旧Mission/无opt-in拒写。
- 64命令临时小样例：提交中位26.195ms、最大31.949ms，lookup4.0ms、replay4.34ms；仅OCI ARM64 Python3.10.12一个小样例，不宣称普遍性能/工期。结果表26601字节、Mission34120字节。容量预算/低空间拒写另有隔离测试，不向生产填盘。
- 来源回归首次3项失败均因旧固定版本预期1.5.4与明确新候选1.6.0-q2.1不一致；修改的是测试版本断言，不放宽来源规则，并另用真实Q1包验证旧Mission可用与双向错build拒写。初始矩阵与失败日志保留。

证据见evidence/tests.json、pack-report.json、capacity-sample.json及各原始日志。实际导入的13份源码依赖含bootstrap/_runtime均记录SHA；未宣称已经完成通用组件化指纹重构。

## 范围与剩余门槛

本轮仅独立源码候选及测试，不升级产品metadata/已安装Skills、不运行真实Mission、模型、浏览器、IM或Core，不混入#232/#233。H1/#236与AIWork#158仍等待本片代码审查/验收。#124 HOLD不变。

待收尾：关联PR审查和最终候选CI；按#238决定正式发行内容、版本类别及授权。候选布局打包通过不等于正式资产已发布，不能直接关闭发布单。
