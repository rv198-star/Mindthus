# Q1 源码与隔离验证交付

#234；消费方AIWork#162。规格先行提交f12d4f7，基线c034b01，未改旧runtime/manifest/CLI。

## 已实现
新增query_runtime.py：显式tplan.query.v1、snapshot.get，真实内核短锁一致读取，无隐式恢复/repin；command.get缺能力明确unsupported，不创建结果库。限制输入/输出，Root与状态符号链接拒绝，Host可指定expected build。只返回业务摘要与来源，不返回原证据/用户消息。

## 实际结果
新接口15项通过；相关既有provenance13项、只读交付12项通过，共40项上游测试。配套Node真实消费者8项通过（日志在AIWork PR）；共48项，无skip。完整日志和文件哈希见evidence。
最初fixture声明了A1但未给success-critical任务，原内核正确拒绝；修正合成fixture后成功，没有为绿色测试放宽生产校验。

18个旧fingerprint_files逐字与c034b01相同，核心SHA256仍863c05463dfa16b036a4cb1754dae7c7494689888d53cce630a2e2bc5c1428ca。只在临时合成Mission初始化/写测试证据；未访问或迁移真实Mission，未安装新版Skill、未跑模型、未部署。

## 恢复与下一步
当前分支feat/tplan-query-q1-20261021；本片提交PR，未合并、未发行。验收仅CLI/Node合同，不是H1人工业务闭环。下一片#235先选定单原子动作与新结果合同，旧Task/runtime不能回填。

复现：`python3 -B -m unittest discover -s tests/tplan -p test_query_runtime.py -v`。原读写权限/弱宿主边界不变；新增查询的成功绝不授予派工/批准。
