# Independent R1 review received through the original ChatGPT task

Reviewed commit: 8acbdc403a475df1d7639c78c34e381e50261b43.
Source task: 调研 Mindthus 结合方案 (6ab0b15c-f328-83e8-9488-17c0111221b8).
This is reviewer feedback, not new execution authority. Sandbox attachment links belong to the reviewer's environment; attachments were not fetched here.

**固定提交 `8acbdc403a475df1d7639c78c34e381e50261b43` 的只读复审完成。独立结论：`REVISE`，只剩一项同类恢复缺口；第 2、3、4 项关闭。**

:chatgpt-content-reference{index="5"}[完整复审报告](sandbox:/mnt/data/Mindthus_211_R1_Readonly_Review_8acbdc4.md) · :chatgpt-content-reference{index="6"}[复现脚本、实际输出与测试日志](sandbox:/mnt/data/Mindthus_211_R1_Readonly_Review_8acbdc4.zip)

## 一、四项修复的逐项结论

| 原发现 | 本轮结论 | 核验结果 |
|---|---|---|
| **1. 串行账本缺失／损坏仍放行** | **原反例已修复，但尚未完全关闭** | 丢失串行目录、丢失两套账本但保留业务意向、损坏完成记录等情况均能阻断；仍遗漏“只剩返回、缺少意向”的恢复现场。 |
| **2. 冷却中断误写未知发送** | **关闭** | `host intent` 已移入获得串行锁、结束冷却后的 `invoke()`。等待中断时没有发送意向，恢复后只调用一次。 |
| **3. 评阅直调绕过串行** | **关闭** | `host_call()` 自身强制执行冻结的串行策略；调用方不传 scheduler，也不能绕过共享锁和已有未知请求。 |
| **4. 墙钟跳变绕过 60 秒** | **关闭** | 单调时钟控制等待；无法确认连续性时重新完整等待 60 秒。墙钟跳变与重启反例均通过。 |

对应实现位于 `pilot.py:81–89、113–134` 和 `serial.py:29–99`。第 3 项的保障仍以第 1 项账本完整性为前提。 

## 二、唯一剩余发现：孤立返回被忽略，另一个场景仍可发送

**位置：`experiments/jev_direct/serial.py:50–63`。**

当前代码只通过 `intent.json` 发现已有业务调用，再读取其对应 `outcome.json`。因此，**意向文件缺失时，仍然存在的 outcome 或 reply 根本不会进入完整性检查**。当两套串行账本也在恢复时遗漏，空集合检查通过，后续调用被当成首次请求。

我用新建的 X／Y 合成批次复现了两个变体：

| 部分恢复现场 | 当前代码的实际行为 |
|---|---|
| X 已模拟完成；恢复时遗漏 `serial/`、`serial-bindings/`、X 的 `host/0/intent.json`，但保留原 outcome、reply、结果与 seal | Y 的模拟 CLI 被调用 **1 次**；没有等待；新记录 `actual_gap_seconds=null` |
| X 写出模拟 reply 后中断，尚无正式 outcome；恢复时遗漏同样三处记录，保留 reply 与请求材料 | Y 同样被调用 **1 次**；没有等待；仍记为首次请求 |

**没有重写剩余文件或重新计算其哈希，也没有修改原始实验记录。**这是不完整恢复的反例，不是“攻击者同时伪造全部证据”。两个变体均为离线模拟，不能说真实环境已经发生了多发。

第一种情况下，重新检查 X 自身的 seal 确实会发现缺失；但启动新场景 Y 时，该检查没有覆盖 X，所以仍然放行。复现输出保存在证据包的 `independent-probes.json`。

### 最小返工要求

**在现有 `_validate()` 内补齐意向与返回的双向完整性检查。**发现孤立 `outcome.json`，以及宿主的孤立 `reply.json`，而缺对应意向／串行绑定时，应报告记录不完整，停止自动续发，不能初始化为 `first_call`。

同时保留第 2 项已经修好的行为：**只有 request／prompt／schema 等发送前材料、没有发送或返回证据的现场，仍应允许正常恢复。**不要仅因目录或 `run-start` 存在，就再次把未发送工作永久卡成未知。

补两个孤立返回反例和一个“仅准备材料仍可恢复”的负对照即可，**不需要增加新平台或重写调度器。**

## 三、独立验证结果与范围

**73 项局部测试已在隔离环境实际复跑：73 通过，0 失败、0 跳过。**三份政策正文从固定提交补齐，测试断言未改。另做 **8 个补充边界探针**：6 个控制符合预期，2 个变体复现上述同一缺口。

受审改动文件、测试文件、审计入口及三份政策正文的本地字节，均与 GitHub 固定提交返回的 blob SHA 核对一致；测试树运行前后未变。详细校验在 `verification-independent.json`。

**证据覆盖限制：**本轮未对新的 `offline-evidence.tar.gz` 做 383 文件逐项解包校验，因此不宣称该归档已独立通过完整性验收；这不是本次 `REVISE` 的依据。剩余发现依据的是固定源码和独立可重复的反例。

**下一轮只需关闭这一处孤立返回恢复边界，其余三项无须重做。真实十二条业务路径仍为 `UNRUN`，质量／净收益未评估；本次没有访问 OCI 或启动真实模型。** :chatgpt-content-reference{index="4"}

