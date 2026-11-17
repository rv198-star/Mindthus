# Legacy canary — Round 1

这是明确注入故障的 legacy canary，供真实 B → A → 独立 C 审查往返使用。
`normalize_record.py` 原样复制自 `input/normalize_record.py`，保留原实现。
完整评审合同：`input/CONTRACT.md` 中的 `host-normalizer-v1`。

本批交付：原实现、一个正常输入 smoke test、本文档。
Smoke 覆盖一条所有字段均为真值的正常记录，并检查输出值、顺序、新字典和输入保留。
完整合同验收待 C 独立审查；收到发现后按后续返修指令处理。

在本目录运行：

```sh
/private/var/tmp/mindthus-246-py311/bin/python -B -m unittest test_normalize_record_smoke -v
```
