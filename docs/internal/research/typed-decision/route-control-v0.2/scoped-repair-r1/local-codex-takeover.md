# 本地 Codex 接管记录（#211）

状态：执行前核对。2026-09-24；分支 `experiment/typed-decision-runtime`，接管时 HEAD `c4630e8447253ebc59691e83ba2557c84e97298d`。本地 `main` 为 `7c0eab827547afe2b2a5a1aa972c7a8fb5606db8`，未修改。接管前已有未跟踪文件，未删除或覆盖。

## 父版本与旧证据

- R1 原冻结文件 SHA-256：`5b4d990dc77524ad25df115123e9648d762c2b5a3911037219f0b7fea9b15e9f`，原冻结记录摘要 `6a760530844d6d79c6525de9cc35ce7c75563e351c90f7b504015a9269d20448`。它的三个 admission 根目录仍指向 OCI；本地不改写该文件、原 runner 或旧账本。
- 旧九输入归档索引的 162 个文件逐一 SHA-256 校验通过。其中 8 份供应商 intent/outcome 对齐，7 份宿主回复已暂存、0 份被原入口消费。本机没有旧 OCI 工作树和运行根目录。旧版 runner 在当前源码下不能通过实现身份校验；不得靠更改旧路径/hash 或重发初检来继续。
- 接管时交接文档尚未附上；随后用户提供 `/Users/william/Downloads/Mindthus_Local_Codex_Handoff_Pack_c4630e8.zip`。ZIP SHA-256 为 `9928f8f3423ad0b7ba592b711428c372f6937bed475015a24217ecd273b37973`；`HANDOFF.md` 及四份历史报告的内容 SHA-256 均与包内 manifest 相符。交接包是历史说明、报告和迁移建议，不是运行目录备份，也不改变本轮用户指令或批准新的请求预算。
- 对 162 份归档 JSON 逐项复核：九份输入 manifest、八次初检 intent/outcome、七份已暂存回执、D1 用途接受记录、九份比较输入、五份历史①输出及九份快照均在。旧报告的 179 是“全部已有文件”口径；差额 17 与代码通常产生的 9 个 `.entry-lock` 加 8 个初检步骤 `.lock` 数量相符，但包内没有 OCI 目录清单，不能据此证明旧目录已完整迁移。原绝对路径和旧实现身份仍阻止本地直接消费旧回执；原记录保持未改，E/F 复查待办不靠重跑填补。

## 本地 R1 身份

- 入口：[local-codex-run.py](local-codex-run.py) 只更换本地输出根目录、当前宿主上下文和授权说明；调用原 R1 的 `prepare/verify/execute`，不修改语义题、门槛、provider、候选、案例、原冻结或预算。
- 本地根目录：`/Users/william/Documents/Codex/2026-09-24/mindthus-six-scenes-r1-local`；episode 在其 `episodes/` 下。新冻结记录摘要：`c9c62aec0173529db717e01c063c34da26e4f11ffcd41e1ec51c3b83d689e7ec`。
- 新冻结与 R1 原冻结的三个输入摘要、初始问题/上下文摘要、实现摘要、TypeSafe `jev-1.13.0` provider 配置和逐案上限相同；仅根目录、宿主说明及冻结时 HEAD 是本地新身份。全批最多 4 次新 Jev、预留最多 0.08 美元；CPA/OpenRouter 均不调用。
- 凭证从已有 mode `0600` 的本地 `.env` 在进程内读取，命令行、源码、记录和日志不含密钥。使用 `--credential-file` 指向它；不向外部宿主转交。

新的 R1 结果只属于本地 Codex 运行，不覆盖旧八次初检或历史 ChatGPT 产物。①建议式与②约束式保留数字名称；跨宿主历史文本只作带来源的对照材料。

## 本地实测结果

原始路径、记录摘要、逐题状态和用量见 [local-codex-observation.json](local-codex-observation.json)。43 份运行 JSON 已逐字归档，见 [证据索引](local-codex-evidence-20260924/evidence-index.json)；6 个空锁文件只用于本地互斥，不作为实验记录归档。三次新 TypeSafe 请求均有 intent/outcome，均请求冻结的 `jev-1.13.0`；B1 的服务返回确认该型号，C/D 的传输失败没有返回可核验的运行型号。没有未知在途请求，没有重发。

| 输入 | 真实 Jev 初检 | 当前 Codex 宿主消费 | ①／②状态 |
| --- | --- | --- | --- |
| B1-R1 | 1 次；M02/M03/S01 合法，S02 Score 合同错误局部隔离；4837 输入/143 输出 token，用量金额未知 | 路由仍 `no_established_primary`，无 handoff | ②未运行；不可判配对 |
| C1-R1 | 1 次；传输失败，所有题无合法结果；token/金额未知 | 无 handoff | ②未运行；不可判配对 |
| D1-R1 | 1 次；传输失败，前置 EDSP 未就绪，I2 依赖未决；token/金额未知 | 无前置产物可接受、无后继重评及 handoff | ②未运行；不可判配对 |

三次供应商调用记录时长分别为约 1.973、5.031、5.038 秒，仅是调用时长，不是端到端时长。全批 4 次上限中用了 3 次；D1 的第二次仅允许已接受实际前置产物后重评，当前条件不成立，剩余名额不作为重试额度。实际收费未知，不把 0.08 美元预留上限写成实收。CPA/OpenRouter 为 0 次；密钥扫描本地 49 个运行文件，命中 0。

工程修复的离线回归仍按父 [disposition.md](disposition.md) 记录为通过。本地实测只证实 B1 的逐题隔离和用量保留；没有证明 B1 语义成功、C/D 场景通过或宿主端到端成功。旧 E1/F1/F2 复查与七份旧回执消费，因原运行根目录/版本身份在本机不可用而仍未决。历史 ChatGPT 的①文本不可与本地 Codex 的②算同宿主配对成绩；当前没有可判的本地①／②配对。

收到交接包后，在本机用规范化 `PATH` 和 `TMPDIR=/private/tmp` 重跑 52 项 R1／当前宿主集中测试，全部通过；生命周期登记 88/88 通过。第一次未规范化的测试尝试有两项环境路径错误：子进程命中了未接受 Xcode 许可的 `/usr/bin/python3`，临时目录 `/var` 与 `/private/var` 的别名令 live admission 路径比对失败。未改生产源码或测试来消除这两项环境差异。
