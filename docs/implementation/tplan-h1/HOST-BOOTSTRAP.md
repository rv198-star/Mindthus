# H1 受保护 Host 的启动绑定入口

## 变更目的

H1 默认 execute() 必须保持 host_disabled，但被明确授权且具备 OS 隔离的可信 Host 需要在启动时绑定一个固定 Mission 和固定 key/Owner/reviewer scope。本变更新增 bind_host_writer(directory, config)，返回只接收 request 的调用对象；每个请求不能更换 trust 配置。

固定配置严格检查字段并复制为不可变映射，嵌套 acceptance_actors 同样冻结。Mission 路径要求规范绝对路径、无 symlink/..、固定 ID 与目录 dev/inode，替换同内容目录也拒绝。普通 execute() 继续使用禁用的默认 trust 路径，未增加环境开关、CLI 配置或通用 signer。

Python 对象或闭包本身不构成隔离。调用方必须保护代码、目录祖先、key、IPC 和写权限，并观察实际认证 Owner/独立 reviewer 事件。此 API 不会把普通 model principal 变成 Owner。

## 验证与实际消费

- 8 新增 binding tests，覆盖固定配置、嵌套配置变更、替换目录、错误 scope、实际 C2、精确重放与普通入口仍禁用。
- 与原 H1 core/completion/kernel gate/candidate path 84 tests 合计 **92 PASS**，Python 3.12.14。证据：[host-bootstrap-python312.txt](evidence/host-bootstrap-python312.txt)。
- AIWork #158 的独立 OCI 合成试验已使用该 API：私有固定 writer + 实际 DSH A/C/reviewer，canonical A/C completed、HR1 pending、Owner decision0、B slot0。该应用证据不替代尚未执行的真人 Owner/B/C2。
- 独立源码复核未发现新的具体缺陷。原 runtime.read_mission 恢复仍由可信 Host 启动过程负责，bind 不自行引入第二套事务恢复。

只是源码入口和测试，未修改已安装 Skill、发行包或真实 Mission；普通调用仍 fail closed。
