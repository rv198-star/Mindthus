# 一次本地未发送修复与剩余调用安排

2026-10-02，Owner提供已登记Sub2API凭据，实际只装载到执行进程。
C宿主核对的第一次外层调用保存为local000002、serial000084。
原始终态是unknown/ContractError，原raw没有诊断；全部原始记录保留。

固定配置的host_timeout=180，而复用的deadline_post_json仅允许0<timeout<=90。
invalid_deadline检查先于multiprocessing.get_context、Pipe、Process和worker.start。
用这次真实wire与实际180参数作离线反例，错误为invalid_deadline，
worker context调用为0。因此这是确定的本地未发送错误，不是供应商失败、
发送后超时或新的远端unknown风险接受。旧unknown终态及STOP不改写；
追加绑定同一请求、配置和源码的对账，串行收据只表示本地invoke已结束，
local_outcome=confirmed_local_not_sent、provider_outcome=no_request；没有供应商completion。

修复先提交，再登记有效配置和父身份。超时改为现有执行器支持的90秒，
不更换客户端、服务、模型、参数、提示或阈值。共享driver正常路径额度不变；
专用修复入口仅允许该C核对补发一次，保留已消耗尝试，不能忽略其他unknown。

本组仍最多5次尝试（继承84，累计89）：2Jev已返回、1本地拒绝已消耗，
剩余仅2次宿主调用，顺序C补发核对→B同题路由。无新Jev、CLI、探针、评审。
未知、安全/权限拒绝或再次失败停止，不循环。父锁、serial和至少60秒保持。

在看到B结果前登记：若B采用的分支产生与C逐字相同的完整HTTP body、
端点及本地返回合同，B显式共享C首份实际核对返回。
没有第二次B核对请求、intent、terminal或独立生成；共享请求不能作为两份
独立生成质量样本，处理成本只计一次。B若retain则复用原A2；
若需要不同核对请求，剩余预算不足时如实未完成，不发第6次。

针对性验证：原参数在worker前拒绝；不匹配错误不能对账；
补发只改变请求序号/超时且生成wire不变；只有完全同wire可共享；
模拟返回不能进入真实状态。相关7项已有接线回归亦通过。
这只是工程修复，不证明API接受、纠偏质量或Jev价值。
