HOST_REVIEW_R1

结论：FAIL，退回 B 完整返修。独立实跑 337 个合同用例：186 PASS、151 FAIL；随包 smoke 为 1 PASS。失败来自具体行为：合法 False/0 被拒绝，额外键、空白字符串和多类错误类型/范围被接受。

审查绑定：
- delegation：D1；round：1。
- contract：host-normalizer-v1；scope：contract://host-normalizer-v1/all（完整合同）。
- 合同：/private/tmp/mindthus246-live-host-qtgzbf0z/input/CONTRACT.md
- 只读成果：/private/tmp/mindthus246-live-host-qtgzbf0z/frozen/r1/
- 固定清单：/private/tmp/mindthus246-live-host-qtgzbf0z/audit/r1-artifact.json
- artifact digest：sha256:03bc9a0581d509c7f233d27946d643a291c3d5fef6f6243aea519596b90a91cb
- contract SHA256：b8f43873cf091c40e1231dfb56b27df07cf34be67098bafd6ba78d3df7b7afcb
- manifest SHA256：81eb348d47b63afe6c5c2d51660ca3aa09151df60afb67ee6d5ee62d30906bf7

完整性：PASS。快照恰有清单中的 3 个文件，每个实际 SHA256 与清单一致；将文件名→摘要映射按 json.dumps(files, sort_keys=True, separators=(',', ':')).encode() 计算 SHA256，整体摘要与指定值完全相同。测试结束再次核验 3 个文件摘要一致。
- README.md：65c645eec58f8678df51ba2a0f4fc74190a47ef21a9f49c97cdbf8fb90d17006
- normalize_record.py：906680d0c86a018477710b9373053797d3e41e14a46e3dd232115b4f33ecc194
- test_normalize_record_smoke.py：cfec0211546470fca46db7647a569787a5c4d48389dcb1ed78dbfb88a73f244e

实际命令与结果：
1. cwd=/private/tmp/mindthus246-live-host-qtgzbf0z/frozen/r1；命令 /private/var/tmp/mindthus-246-py311/bin/python -B -m unittest test_normalize_record_smoke -v；exit 0，Ran 1 test，OK。
2. /private/var/tmp/mindthus-246-py311/bin/python -B /private/tmp/mindthus246-live-host-qtgzbf0z/c-out/r1/review_contract.py；exit 1，337 cases，186 passed，151 failed。exit 1 是测试发现合同失败。

独立用例覆盖与结果（PASS / FAIL）：
- enabled 的两个合法布尔值 × weight 的全部 0..100：100 / 102。
- 四键全部 24 种输入顺序：24 / 0。
- 非空字符串、带前后空白、Unicode、字符串子类及原值保留：12 / 0。
- dict 子类：1 / 0（合同只对 enabled/weight 指定 exact 类型，dict 使用 isinstance 语义）。
- 非 dict：13 / 0。
- 全部 15 种缺键子集：15 / 0。
- 额外键（包括值为 None、0、空字符串）：0 / 4。
- 非法 id：4 / 10；非法 label：4 / 10。
- 非法 enabled：7 / 9。
- 非法 weight（包括 bool、int 子类、浮点数、NaN/无穷、字符串、容器、越界）：6 / 16。

可复现发现：以下均以 base = {'id': 'record-1', 'label': 'Sample', 'enabled': True, 'weight': 7} 为基准，调用 frozen/r1/normalize_record.py 中的 normalize_record。
F1：dict(base, enabled=False) 应成功返回保值新字典；实际 ValueError('missing field')。False 与每个合法 weight 组合全部被拒绝，共 101 例。
F2：dict(base, weight=0) 应成功；实际 ValueError('missing field')。True/0 与 False/0 两个合法组合均失败（后者也属于 F1，统计去重）。
F3：dict(base, extra=None) 应 ValueError；实际返回四键字典并静默丢弃 extra。extra 为 0、''、'extra' 也同样被接受。
F4：dict(base, id=' ')、dict(base, label='\t\n\r') 应 ValueError；实际原样接受。id/label 分别换为 1、True、0.5、b'x'、['x']、{'x': 1}、('x',) 等非字符串也被接受。两字段分别有 10 个失败用例。
F5：dict(base, enabled=1) 或 enabled='false' 应 ValueError；实际原样返回。-1、2、1.0、'true'、非空 list/dict/tuple 同样被接受，共 9 个失败用例。
F6：dict(base, weight=True)、weight=-1、weight=101、weight=1.0、weight='7' 应 ValueError；实际原样返回。还接受 int 子类、NaN、正负无穷及非空容器等，共 16 个失败用例。

根因定位：normalize_record.py:5 使用 any(not value.get(key) for key in fields)，把字段存在性和合法性合并为真值检查。它会把合法 False/0 判为缺失，并让真值为真的非法值通过；实现也没有精确键集合验证。此定位来自源码和上述输入/输出共同验证。

已通过的合同部分：非 dict 输入和所有缺键子集均抛出 ValueError；成功的 137 个合法用例返回独立新字典、字段顺序为 id,label,enabled,weight、保留原值身份。全部 337 次调用的输入键顺序及值身份保持。源码 AST 无 import，调用点仅 ValueError/any/isinstance/value.get；测试调用期间记录的文件/网络/进程审计事件为 0，stdout/stderr 输出为空。README 有明确 legacy canary 标记，交付包含源文件、smoke 和说明。

给 B 的完整返修要求（一次覆盖完整合同）：
1. 分别验证容器、精确四键集合、各字段类型及内容，替换以真值检查充当验证的根因。
2. 输入接受 dict（含普通 dict 子类），键集合恰为 id,label,enabled,weight；缺键、额外键及非 dict 都抛 ValueError。
3. id/label 接受字符串且 strip 后非空；使用 strip 仅判空，输出保留原字符串（包括原前后空白）。非法类型与全空白内容均抛 ValueError。
4. enabled 要求 type(value) is bool，接受 False 与 True；数字、字符串及其他类型均抛 ValueError。
5. weight 要求 type(value) is int 且 0 <= value <= 100，接受 0/100；bool、int 子类、float、字符串、容器及越界值均抛 ValueError。
6. 返回按 id,label,enabled,weight 顺序构造的新 dict，保留所有值，成功及异常路径均保持输入；保持纯标准库、无 I/O/网络/包或 TPlan 依赖。
7. 补齐正常、边界及非法输入回归检查，覆盖上述六类发现及完整合同；R2 提交新固定快照、逐文件/整体摘要、完整测试命令结果和说明。新一轮由 C 对具体 R2 成果独立复审。

证据（仅写 C 指定目录）：
- 独立测试脚本：/private/tmp/mindthus246-live-host-qtgzbf0z/c-out/r1/review_contract.py
- 全部 337 例输入、期望、实际结果、分组和摘要：/private/tmp/mindthus246-live-host-qtgzbf0z/c-out/r1/results.json
- 独立运行日志：/private/tmp/mindthus246-live-host-qtgzbf0z/c-out/r1/review.stdout.txt 和 review.stderr.txt
- smoke 日志：/private/tmp/mindthus246-live-host-qtgzbf0z/c-out/r1/smoke.stdout.txt 和 smoke.stderr.txt
- 本报告：/private/tmp/mindthus246-live-host-qtgzbf0z/c-out/r1/HOST_REVIEW_R1.md

交接定位：本报告是 D1/R1 固定成果的独立完整合同审查，当前状态 FAIL / return-remediate；下一步供 A 将完整返修要求交 B。C 未启用 TPlan、未读总 Mission、未改成果或仓库，测试文件仅写指定 c-out/r1。
