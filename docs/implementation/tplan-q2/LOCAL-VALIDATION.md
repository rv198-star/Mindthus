# Q2 本地 CI 与代码审查收尾

**验证范围**：Mindthus #235 / PR #239，AIWork PR #166。GitHub CI 不作为本轮唯一交付路径；依 Owner 授权，采用 OCI 本地等价范围验证，保留解释器差异，不将静态/夹具测试当作真实 DSH 交付。

## 代码审查问题（先失败、后修复）

1. 新 Q2 build 必须把修改过的 `query_runtime.py` 同时加入 `required_scripts` 与 `fingerprint_files`，旧 1.5.4 的指纹不受影响。
2. 普通写入、历史读取、显式恢复都要在锁内验证 `Mission` 目录与 canonical Mission ID 的匹配关系。
3. AIWork 对 `snapshot.get` 不得接受 `command_not_found`；只有 `command.get` 才允许此结果。修复前的定向反例确实失败，修复后分别通过 Q2 23项、Node 12项。
4. 原 `v1.13.0` 发布边界测试固定了当时 TPlan generation `1.5.4`，但 Q2 候选可显式声明 `1.6.0-q2.1`。新版测试仍逐字核对历史发行日志和新候选身份，不修改已发布资产/证据。

## 本地执行的检查

- Python 3.12.14 OCI 主机：`/srv/agentdock/.local/bin/python3.12 -m unittest discover -s tests -q` **1,249 项发现，1,242 通过、7 按原规则跳过、0 失败**。日志 `evidence/local-ci/full-unittest-py312.log`。
- Python 3.11.17 OCI 缓存离线容器：挂只读候选源，禁网、tmpfs，`test_command*.py` 24 项与 `test_query_runtime.py` 17 项均 PASS。日志 `evidence/local-ci/python311-core-final.log`。
- 宿主 Python 3.10：原 CI 的 packaging/docs 检查、4 个方法/运行时 smoke 命令完成 PASS；其 TPlan-all 和完整 suite 在修订前分别出现版本断言/未支持的 `unittest.enterContext`，保留原始失败日志，不认定通过。
- 既有 Q2 五种布局构建与打包解包的专属测试再次包含在 Python3.11 24 项和 Python3.12 全量 suite 内；既有上下游 Q2 Host 12 项定向 PASS（独立 CI 记录另见 AIWork）。
- 检查结果/文件指纹见 `evidence/local-ci/local-validation.json`，脚本执行环境与 source HEAD 都在其中；最终提交 SHA 由本轮归档后的 PR 元数据确定。

**准确性边界**：原 GitHub CI 设 Python3.11。整套 Full unittest 当前为 OCI Python3.12，不宣称同解释器字节级复现；核心 Q2 在 Python3.11 真实运行通过。所有测试使用合成任务，不涉及生产已安装 Skill、真实 Mission、DSH 模型/微信、外发或 #124 的在途终止。

## 发布和后续

这是一项新增 `tplan.command.v1` 功能候选，不能仅因修复审查 P2 就宣称纯 Bugfix release。#238 继续独立评估版本类别、正式归档、实际使用者是否需升级；合并源代码不自动发布。Q2 通过后 H1 #236 先冻结新增 canonical 语义与可信 Host 交互合同，不把 Q2 的普通 caller identity 冒充 Owner。
