# DSF指定000098风险接受与一次补试

2026-10-02，Owner在已推送的7b5694224026c0a1c95d1abe585470f01a868dbe
报告之后明确选择：“接受上述指定风险，允许DSF补试一次并继续”。
这是本请求独有的向前授权，不把之前PLAN的禁止自动重试改写成当时已有例外。

仅指定`stance-routing-coverage-v1:dsf41-current-B:0`，父serial000098、本地000011，
request `346106b19d142cc27b46475a158ed1cd7a457c96aaf28215279ac61eb59ec6b5`。
旧remote unknown、原始intent/raw/terminal/STOP及已耗尝试/时间全部保留。
新增accepted-unknown只是风险处置，绝非供应商completion或确定pre-send。
Owner接受可能重复计算/计费和旧远端重叠；60秒等待不证明旧远端已结束。

同一批次、父锁/serial、原输入/材料、官方Jev和既有CPA.rn-us DSF/medium配置。
新B:1只允许一次指定同wire补试；若取得首份有效返回，继续原计划C原题/载体控制
及按需B/C各一次独立核对。不重跑旧A1/A2、5.5、5.6或6.1；不补发被拒绝的5.4。
再次unknown、实际安全/权限拒绝停止，不切换身份、渠道或启动形式，不追加循环。

不增加预算：累计当前101=77宿主＋24Jev，硬上限仍111=83宿主＋28Jev。
此次最多5次新增（3宿主＋2Jev），按需消费，指定补试计入剩余额度。
B的历史计数1继续累加：补试序号1、必要核对序号2，总B槽3含旧unknown；
C保持两槽。只在此指定入口允许第三B槽，不推广其他路径。

最小接线复用NamedSerial风险回执、Driver及原适配器；旧000068例外不改。
新增3项离线测试只核对同wire/序号、核对合同/预算不重置、指定serial绑定。
模拟返回不导入实际产物；不重审旧核心/GJ/R2、不探针或补齐精确费用。
原报告/索引保留为补试前检查点；后续新证据另存，避免覆盖已固定原始unknown。

入口：`python -m experiments.bias_trigger.stance_routing_dsf_resume --prepare`；
随后同一已授权凭据仅载入进程，`--run`最多执行一次。
该入口只允许当前指定处置，没有通用ignore-unknown或强制解锁开关。

## 补试后独立C续接

唯一B补试serial000099明确失败：生成前TLS连接建立失败，ssl_error_code=8。
原始阶段证据支持pre_send；旧000098仍unknown，不因此追溯改判。
B补试已耗尽，不再补发；这不是安全/权限拒绝或新的unknown。
继续已经获准而未发送的C原题/载体控制及至多一次核对，不增加任何B调用。
`--complete-C-after-B-failure`只绑定此次具体B失败终态摘要和C完全未发送状态，
遇unknown/refusal或另一终态不能继续；不是通用绕过STOP或重试开关。
同一服务、账号、传输、原始业务材料及预算保持；不靠换形式修复TLS或规避拒绝。
仅更新必要技术后继源码身份，旧配置/风险处置/失败不覆盖。
