# host-normalizer-v1 — D2 / I2 / Round 2

本批是完整合同返修；R1 legacy canary 保持原样。
合同：[CONTRACT.md](../../input/CONTRACT.md)。

`normalize_record.py` 将存在性、类型、内容与范围分别校验：

| 发现 | 修复 |
| --- | --- |
| F1 / F2 | 接受 enabled=False 与 weight=0/100，使用精确类型校验 |
| F3 | 精确四键集合，拒绝缺键、额外键、同数量的错误键 |
| F4 | id/label 是 strip 后非空的字符串；保留原字符串及其空白 |
| F5 | enabled 仅接受 exact bool |
| F6 | weight 仅接受 exact int 0..100，排除 bool/int 子类及其他类型 |

输入允许普通 dict 子类；输出为按 id,label,enabled,weight 排列的新 dict。
成功与异常路径保留输入；所有非法值均 ValueError。实现无 import 和 I/O。

## 回归与自审

380 项行为用例重建 C 的全部 337 项输入/期望，并增加 43 项边界；另有 1 项静态纯度检查。
行为测试逐项检查新字典、字段顺序、值身份、输入保留、正确异常、无文件/网络/进程 I/O、无 stdout/stderr。
完整测试实跑 381 项，0 失败、0 跳过，结果 OK，见 `test-results.txt`。
`verify_contract.py` 核对旧 C 用例矩阵、合同 SHA、实际测试摘要及三个 Python 文件的内存编译；结果见 `self-review.json`。

在本目录使用指定解释器运行：

```sh
/private/var/tmp/mindthus-246-py311/bin/python -B -m unittest test_normalize_record -q > test-results.txt 2>&1
/private/var/tmp/mindthus-246-py311/bin/python -B verify_contract.py > self-review.json
```

复核固定成果时可运行相同命令并省略重定向，以读取结果而保持文件内容。
逐文件 SHA256 和整体摘要随 HOST_ARTIFACT_R2 交接；整体为文件名→SHA256 映射按
`json.dumps(files, sort_keys=True, separators=(',', ':')).encode('utf-8')` 序列化后取 SHA256。

B 自测、自审完成，无已知残余问题。下一步由 A 固定 R2 成果，交 C 独立复审。
