# #211 设计重审与独立 Review

2026-09-25。代码父版本：`4f804a0e925e5f2a72a27d123240fae67eb22922`。

## 结论

**最小原文直读实现和 A–F 暴露开发验证已经完成；结果支持接口方向，但不支持默认扩散。**严格结果为 11/12，A 场景普通 Codex 同题动作与 Jev 一致，实际宿主纠偏尚未运行。详见 [实测结果](RESULT.md)。继续在同一批明显坏答上调通过率，仍不能回答 Jev 是否真正改善产品判断。

本次找回了“判案 / X 光机 / 抛针”的用户原话，也保留了用户后来对“LLM 随意忽略路由”的担心。拟调整为：原文直接绑定；有区分力的问题刻画不同关系；辅助未知不拖住独立工作；关键发现必须处置且可有据异议；代码落实方法读取和作用范围。没有改成重复采样投票，也没有取消②约束式。

## 已完成与未完成

| 层面 | 本轮结果 | 边界 |
| --- | --- | --- |
| 原意与原则核对 | 完成；十条原则逐条对应提案 | 历史助手意见保持来源身份 |
| 已有模型结果审计 | 独立审计核对原始记录、检测天花板和归因混淆 | 旧六题/v1.2 不成为新保留集；未展示难题增益 |
| 新方案与测试计划 Review | 两个独立 Codex 上下文分别审证据与架构，作者逐项修订后复核 | 独立上下文，不是独立事实来源或跨模型证明；运行条件仍须在实现时冻结 |
| 具体工程漏口 | 已修复：复查仍要求纠偏、或纠偏未复查时，相关事项保持未决；前置接受不会清除此义务 | 独立事项继续；预算/轮次不增加；不改旧回执 |
| 工程验证 | 新增 4 个反例修复前均失败，修复后通过；196 项关系/路由/当前宿主回归＋24 项 scoped repair 回归通过；审计员另独立跑 4 项通过 | 本轮共 220 项相关测试通过；未把父版 1524 项全仓通过说成本轮新跑 |
| 新模型与宿主效果 | 原文直读 D 最小切片已运行：干净 Jev A–F 12 次，普通 Codex A 同题 2 次；实际宿主纠偏未运行 | 严格 11/12；只证明暴露开发接口可工作，不证明产品收益 |
| #211 资格 | **未通过 / NOT QUALIFIED** | 整体非劣与 Skills/4K 实质增益仍待验证 |

## 新比较怎样分清贡献

保留自然首答后，比较“纯 Codex 复核”“只给问题清单”“同图 Codex 观察②”“Jev 观察①”“Jev 观察②”。事前固定②为主候选；①与②仍表示建议式和约束式，场景 A–F 的历史名称不变。

问题清单已能解释同等改善时，不把收益全算给 Jev。②只因多一次仲裁变好时，单列额外推理的影响。新计划区分 S0 路由与 S1 候选检查，纳入自然正确答、反向控制、无谓改写和误报；完整分母保留未决、回退与环境失败。12 个新来源即使跑完也只给开发方向，不能自动升级成统计非劣。

## 阅读入口

- [原始讨论与证据边界](SOURCES.md)
- [调整方案及十条原则映射](PROPOSAL.md)
- [对照、消融、评分与有限预算](TEST-PLAN.md)
- [独立测试证据审计及修订复核](reviews/evidence-review.md)
- [独立架构审计、漏洞反例及修复复核](reviews/architecture-review.md)
- [干净实跑与 v3.1 消费修正独立复核](reviews/clean-result-review.md)

## 工程修复记录

文件：`experiments/typed_decision/route_control.py`、`tests/test_route_control.py`。

根因：集成入口原来只对 `return_original_owner` 暂停事项，忽略复查再次返回 `request_correction`；另一个已接受的前置产物也可能经后继路由复评清除关系未决。现在先绑定 `relationship_issue` 的未决原因，再安排依赖与派发。原宿主接受前置产物仅释放该依赖；它没有权限替另一项纠偏签发完成。

四个新增测试验证：再次命中、未复查、前置接受后再次命中、前置接受后关系退回。同时检查独立事项可执行、无额外纠偏/判断、已完成重入不增调用与不改记录。这里是现有合同的正确性修复，不是新的多维观察机制效果。

执行命令（在仓库根目录）：

```sh
PATH=/Users/william/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin:$PATH TMPDIR=/private/tmp python3 -m unittest tests.test_route_control tests.test_relationship_assessment tests.test_relationship_runtime tests.test_current_host
PATH=/Users/william/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin:$PATH TMPDIR=/private/tmp python3 -m unittest tests.test_scoped_route_repair
```

结果分别为 `Ran 196 tests / OK`、`Ran 24 tests / OK`。这两次均是确定性工程验证，不调用 Jev。修复改变实现摘要，旧冻结运行仍须使用父版本；不会把新行为回写旧分数。

## 下一步边界

原文 S1 检查合同、语义依赖失效、干净 A 门和 A–F Jev 暴露验证已经完成。独立复核发现并修正了标签泄漏、风险顺序、错误前提标签进入宿主指令以及 K1 金标准误计。完整五条件、真实宿主纠偏和 N 新来源仍未准备或未运行，不把它们列为已完成。

Gate Probes：本产物服务于选择实现方向；最小接口已完成可证伪验证，证据仍不能证明 Jev 相对普通 Codex 或最终任务的收益。下一动作应等待独立新来源、严格金标准和真实宿主消费准备完成，不增加通用平台或继续追旧题通过率。
