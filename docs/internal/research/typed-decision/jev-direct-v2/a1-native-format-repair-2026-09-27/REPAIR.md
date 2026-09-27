# A1/native 宿主格式定点修复

基线：`ae8787084e39e2b4cfbd4a6570ab792fb3764815`。本补丁只处理公共宿主 schema 发送边界、同请求格式失败终态和 A1/native 的一次技术验证；R2 四项发现保持 CLOSED。

## 实现和验证

- `pilot.host_call` 同时保存本地完整 `schema.json`、API 副本 `schema.api.json` 和摘要绑定。深复制后只在 schema 节点移除已确认不兼容的 `uniqueItems`；当前真实 schema 恰好移除 read_paths、used_methods 两处。required、additionalProperties、枚举、类型等不变。native/direct 共用这个边界，本地原校验器继续严格拒绝重复、非法枚举，交付检查继续拒绝未加载的方法声明。
- 归档 `event_msg/task_complete` 通过 session 元数据、turn_context、精确原始 UserMessage、task_started 绑定请求摘要、工作目录、模型/推理配置、线程和轮次。只接受本案三元错误码 `invalid_request_error / invalid_json_schema / text.format.schema` 作为可追加对账的格式失败；安全错误、普通错误文本、非零退出、超时、缺终态、来源不符继续不能解锁未知请求。
- 旧意向、schema、冻结和历史返回不动。对账追加宿主 reconciliation 和独立绑定的串行 failure 记录，不制造成功 completion。新请求保存 CLI stdout/stderr 和单独宿主会话时间；纯 HTTP 时间没有测量。
- `technical_retry.register/run_once` 使用原运行目录和同一串行账本，读取原 A1/native 请求，登记独立代码后继身份，不改写旧 freeze。继承 1/4 次已消耗，剩 3 次，本轮最多新增 1 次，读请求也停止；再次进入只返回原终态或保持未知。旧会话 28.518 秒保持原口径；以已记录 shell 墙钟 30.22 秒作为保守时间预算扣减。
- 保留全批单请求在途、完成后 60 秒单调时钟冷却与恢复约束。追加记录主动等待时间，不改变等待行为。

命令：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_jev_direct_host_boundary tests.test_jev_direct_router.PilotTests tests.test_jev_direct_local -v
```

56 项通过，原始日志见 `related-tests.log`。固定回归材料是原已入库 A1 schema 与 `tests/fixtures/jev_direct_schema_failure/` 中本次真实归档事件；测试仅重定位临时路径，合成响应不进入真实结果。源档案的 session/turn 元数据按需投影，原始事件摘要和行号保留；终态错误和 UserMessage 原文保留，不导出无关系统指令。

本地完整合同 canonical SHA-256：`8b819c765eaee80278ec236f3fd4369cd366b5967002ab692f025abd6175ddd3`。
API 副本 canonical SHA-256：`6f6afd070a41f9c02bcba12b489dc576ea59ffe1e0b59c29cef1c0e016fc2861`。
新旧差异见 `schema.diff`。

这些结果只证明相关工程回归通过。尚未证明 API 接受格式、模型返回、答案交付或内容正确；真实技术重试单独记录于 RESULT.md。

约束依据：本次 API 原始错误为直接证据；[OpenAI Structured Outputs 文档](https://developers.openai.com/api/docs/guides/structured-outputs)说明其只支持 JSON Schema 子集。未据此批量删除其他约束。
