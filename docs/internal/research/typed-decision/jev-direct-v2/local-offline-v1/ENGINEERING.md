# #211 本地离线接线适配

父版本：`8e47cdacc63d3ad53c7fd0f64aa77d9a25e4ebd2`。本轮仅离线工作，真实业务仍暂停。

## 最小改动

- `pilot.prepare` 可显式指定本地 CLI；原 `/usr/bin/codex` 默认保留。新建本地 freeze，旧 OCI freeze 不改。
- 新本地 freeze 声明一条批次级串行策略：同时一个调用，前次明确完成后至少 60 秒。
- `SerialRequests` 复用原文件锁和不可变记录；锁覆盖等待与调用，跨场景、跨两臂和重启共用账本。
- 每次记录开始、明确完成和实际间隔。中断、异常、CLI 缺少成功终态或 Jev 缺少返回回执时保留未知意向，阻止后续调用；没有自动重发或解锁覆盖入口。
- Jev 冷却发生在 Session 推理预算开始前；宿主请求耗时与包含等待的调度墙钟分开。原推理预算不扩大。
- 本地 `offline_prepare` 只用原离线 provider 与模拟 CLI，禁止 socket connect；输出六个首轮 Jev HTTP body、六个⓪首轮提示/schema，以及明确标记的夹具轨迹。
- 新增测试纳入原 lifecycle registry；不改变题文、方法卡片、阈值、原始资料、评分或默认 Skill。

## 针对性验证

`targeted.log`：84 项中，80 项 direct/local/full-context 测试及三项 registry 测试通过；一项 registry 子进程调用系统 python3，受未接受的 Xcode license 阻止。
仅修正测试进程 PATH，使子进程使用 Homebrew Python 3.13，再跑四项 registry 检查，全部通过，见 `lifecycle-local.log`。未修改系统许可、未重跑全仓审计。

测试包括两层上限、跨臂原文一致、实际方法读取、同臂 resume、未知调用阻断、完成后不重发、并发锁、重启后 60 秒间隔，以及冷却不消耗 Jev 推理预算。模拟时间不是真实服务耗时。

本地 CLI：`0.158.0-alpha.2`，路径由 `command -v codex` 核实。`exec` 和 `exec resume` 的帮助输出确认 schema/json/model/resume 参数存在；只执行 version/help，没有启动模型。

本地配置标识：provider=`openai`，未设置自定义 provider endpoint；无 CODEX_HOME 覆盖；认证文件存在，仅检查存在性，不读取认证内容。全局 AGENTS 和五个 MCP 配置存在，真实运行时的工具隔离/模型服务身份尚未通过实测证明。适配继续保留原 shell-tool 禁用与只读 sandbox 参数，未更改用户配置或降低设置。

## 执行范围

本实现的串行约束覆盖这个本地试验 root 内由驱动发起的调用，不宣称控制其他应用或其他试验根目录。CLI 内部服务行为、服务端终止和结算费用需要真实回执确认。无法确认完成时暂停，不靠本地进程退出推断服务端已结束。

这份工程记录不提供重新发送历史被拒业务的授权。独立质量评审仍由 ChatGPT 完成。
