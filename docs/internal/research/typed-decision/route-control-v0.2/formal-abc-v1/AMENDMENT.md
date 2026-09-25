# 续行指针格式修复（保留冻结）

冻结版 `run.py` 的 `run_graph` 把 `B/C-latest.json` 写成普通 JSON，`run_host` / `fallback` 却用 `session.read_record` 读校验包。HB/B、HC/B、HD/B、HD/C 已完成首轮裁决并留下原始 Episode；首次宿主续行在读取指针时失败，未调用模型、未消费回执。

`normalize_latest.py` 仅对可重建的 latest 指针做格式转换。它逐字节保存原指针到 `snapshots/*-latest-raw-<sha>.json`，按原 payload 包装成 `mindthus.decision-record.v1`，验证后原子替换指针。Episode 原账本、冻结、题目、预算、供应商请求和回执均不修改。每当冻结版运行器重新写出 latest 后，需要再次运行该转换。此修复不增加任何模型调用、问题或预算；结果报告须列出原失败和修复。

HD 的冻结图要求原宿主在消费 I1 回执时同时决定是否接受其候选方案。`stage_hd_host.py` 仅为尚未消费的 HD/C 把冻结版宿主调用与随后的图续行拆开；原宿主检查实际输出、记录对应哈希的接受回执后，再用冻结版 `run.py HD C` 续行。已经消费且持久化为未接受的 HD/B 不改写旧记录，其 I2 如实保持未决。

当前 Codex 已阅读 HD/C I1 的真实回执：其列出纸图、现有网页、组合及完整 App，并统一提出第三站、断网、采用率与稀缺资源比较维度；这足以作为 I2 的候选输入，不代表外部事实已证实。`accept_hd_c_artifact.py` 将这一次人工语义接受连同回执路径和哈希写为 P1 的外部源校验记录。
