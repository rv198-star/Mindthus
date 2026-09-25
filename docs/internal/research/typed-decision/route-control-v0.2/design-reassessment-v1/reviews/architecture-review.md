# #211 独立架构审计

审计日期：2026-09-25。审计员：独立子任务 `independent_architecture_review`。代码基线：`4f804a0e925e`。本审计只写本文件；未修改 runtime，未提交，未调用 Jev、CPA 或 OpenRouter。使用 WAE 最小检查判断控制归属，事实依据来自仓库代码、既有结果及一次明确标注的离线注入复现。

## 最终裁决

**本轮设计重审通过，三项阻塞均已解除。**AR-1 的现有代码消费漏口已有有界修复，并由审计员独立运行四项回归确认；AR-2/AR-3 的提案表述已修订。最终被审三份文件的 SHA 见文末“复核 3”。新关系合同、原文直视图、辅助观察消费及相关复用均仍是提案，D/N 尚未执行，#211 未取得资格。本裁决允许作者继续准备最小实施与冻结材料，不将审查当作实时调用授权或产品增益证明。

## 首轮被审版本与裁决（历史保留）

| 文件 | SHA-256 |
| --- | --- |
| `SOURCES.md` | `f8edcf5ac43f99b50cc79e064fcd2a89af92d6a82f41158da80c69a1215235af` |
| `PROPOSAL.md` | `2d0176835c041128d15f380ee375a41f86bc864801da7584d9d034284743c70e` |
| `TEST-PLAN.md` | `541eefbd9edaf554d4070c169724bf6d1c8b1ea594c6c139cea99c2267466fa7` |

**提案方向成立；上述版本需要三项有界修订，才适合作为实施基线。**主要阻塞是处置义务尚未贯通到宿主消费、未决仲裁的实际入口与文字不一致，以及无条件的工程保证表述。此裁决不要求重建路由器、降低阈值或新增常驻裁判，也不授予 D/N 实时执行资格。#211 仍未取得资格。

## Core / 关键判断

“不同问题像 X 光角度”与“常规路由必须落实”可以同时成立。前者要求保留关系与不确定性，后者要求模型不能静默跳过已经生效的处理义务。合适的控制对象是**已定方法、检查义务和有界处置过程**；事实结论及真正未决的关系仍需要语义判断。

因此，同一事项里的一个可选观察未知，不应自动否决其余已足够明确的工作；已经被确认为必要的事实、权限或依赖，也不能因其他观察正确而被平均掉。新提案按动作依赖限制影响范围，比直接降低 `.8/.2` 或取消执行约束更有依据。但“每条观察是否必要”必须在合同中先有含义，不能由拿到不理想结果的执行者临时降级。

## 阻塞发现

### AR-1 / P1：复查再次要求纠偏时，集成入口仍可消费执行产物

定位：`experiments/typed_decision/route_control.py:529` 只对 `return_original_owner` 把关系检查对应事项降为未决。复查返回 `request_correction` 时，流程仍能进入 `execution` 并在 `:580` 消费无异议文本。执行回执只验证方法集合、版本和非空产物，没有验证这条尚未解决的关系发现已被处置。

这与 `relationship_runtime.py:542` 的独立入口不同：后者只有复查 `continue_original` 才记 `corrected_rechecked`，否则退回。当前集成虽然把完整关系报告交给宿主，但“报告已附上”不能等于“发现已处理”。本问题不是要求所有单元格变绿，而是已经命中的具名义务可以没有处置记录就消失。

**对提案的最小要求：**第 4/5 节与 D 测试明确区分首次纠偏完成、复查通过、复查仍命中、未复查。复查仍命中时，绑定受影响动作；允许有来源的异议经既定规则解决，或保持未决交回原宿主。没有这种处置，不得把后续普通执行回执计为“已遵守纠偏约束”。补充未复查的身份也不得误记验证通过。一次纠偏、一次复查的上限继续有效，不自动追加纠偏。

**已运行的离线复现：**使用仓库现有 `tests.test_route_control` 与 `tests.test_relationship_assessment` 夹具。在临时目录中替换 registry，令 `definition` 初检与复查都为 `account_missing`；未发任何模型请求。结果为：

```text
initial_action = request_correction
recheck_action = request_correction
route_mode = committed
consumed_outputs = ['I1']
pending = {}
```

准确复现代码如下；Python 需支持本仓库语法。本机使用 `/Users/william/miniconda3/bin/python3`。系统 `/usr/bin/python3` 被未接受的 Xcode 许可拦住，未将其算作代码失败。

```python
from pathlib import Path
from unittest.mock import patch
import tempfile
from tests.test_route_control import packet, Provider, Executor, Hook, DEFAULT
from tests.test_relationship_assessment import packet as relation_packet
from experiments.typed_decision import route_control as rc
from experiments.typed_decision import relationship_runtime as rt
from experiments.typed_decision import relationship_assessment as rel

repo = Path.cwd()
rp = relation_packet(candidate='范围只谈Skills，本质仍然只是提示词。')
d = packet()
d.update(episode_id=rp['episode_id'], turn_id=rp['turn_id'],
         revision=rp['revision'], documents=rp['documents'],
         authority=rp['authority'], relationship=rp)
d['issues'][0]['request_ref'] = rel.quote(rp['documents'][0])
for key in ('handling', 'assessability'):
    d['issues'][0][key].update(
        owner_ref=rp['authority']['owner_ref'], revision=rp['revision'],
        refs=[rel.quote(rp['documents'][0])])
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    with patch.object(rt, '_registry', return_value=root / 'registry'), \
            patch.dict(DEFAULT, {'definition': 'account_missing'}):
        result = rc.run(root / 'episode', Provider(), d, repo,
                        executor=Executor(), corrector=Hook())
    print({
        'initial_action': result['relationship']['initial']['result']['action'],
        'recheck_action': result['relationship']['recheck']['result']['action'],
        'route_mode': result['route']['mode'],
        'consumed_outputs': sorted(result['outputs']),
        'pending': result['pending'],
    })
```

这是控制流反例，不能用来声称 Jev 在任何真实任务里一定产生该结果；也不能据此重写历史六题分数。

### AR-2 / P2：当前“现有仲裁”不能接住初始未决路由

提案第 3 节说 M02/M03 分歧可按现有具名仲裁处理，但实际 `route_control.py:556` 会把初始 `delegated_unresolved` 放入 pending 并移出等待队列。已有仲裁在 `:595` 之后，只能由已经派发的执行者返回 objection 触发。HB 的支持兼约束、HC/HD 的适用性中间值，不会自动抵达这个入口。

**最小修订有两种合法选择：**本切片维持该事项未决、交回原宿主并单列其结果；或者明确承认需要新增一次未决处置接线，复用已有仲裁合同、同一 episode 与总预算。后一选择须纳入实施范围、调用上限和 D 测试，不能标成现有能力。不得让同一个执行上下文仅改一个标识就成为“独立仲裁”，也不得因没有独立上下文隐式调用 CPA。

### AR-3 / P2：删除“100% 可保证程序执行和记录”的无条件陈述

提案 Guardrail 的最后一句仍给出无条件保证。本次 AR-1 就表明，设计意图与实际路径之间可以存在漏处置；宿主回执也只证明应用边界上的声明，不能证明所有语义步骤实际发生。应改为“把按合同检查、记录处置与拒绝不合规回执作为可测试的工程要求；语义有效性另验”，并明确故障/不支持时不能报已完成。

这不削弱执行控制。相反，必须用可观察的反例测试约束实现，不能靠口头保证替代验证。

## Mainline / 支持的最小替换与必须保留的控制

1. **先换消费含义，不加全局扫描。**对原文已有信息允许直接绑定；真正由压缩提案带来的语义丢失才检查提案。保留主体、时点、目标及来源身份。q0/q1 有用途，但不应因表示不完美就把原文中已有事实变成未知事实。
2. **每题说明会限制哪个动作。**辅助 unknown 保留 unknown；必要未知限制依赖项；具名发现必须处置。无需建立新数据库，复用现有 issue/check/ref、版本与 trace。
3. **语义分歧采用一次有界处置。**保留直接方法适用题，允许关系题补充；禁止多数投票或按模型概率当事实认证。没有可提交主方法时如实未决，不能为降低未决率虚构主方法。
4. **把“处理过”落实到宿主边界。**保留实际读取 canonical 方法、有效路由版本、同一 episode、不可变请求/回执、已知义务、产物接受权和源绑定异议。必要发现的处置记录应随真实候选版本进入消费。不能把普通非空输出或 `performed_methods` 列表当语义完成证明。
5. **复查只失效真正依赖新候选的关系。**但当前题组全部看得到完整 State，不能仅因题目的显式 locator 未变就推断语义独立。可复用条件需由冻结合同声明；新事实、目标或候选变化影响哪些问题，应有一对会失效/不会失效的反例。先做小范围，不能悄悄复用旧候选判断。

已经存在的两项工程修复——单题合同错误隔离、已接受前置产物后的未决后继复查——直接复用。v1.2 已经修复的候选立场绑定与 explanation/decision 消费差异继续保留。它们无需再次被命名为本次创新，也不需要为本次文档审计重新实现。

## 十条原则核对

| 原则 | 独立判断 |
| --- | --- |
| 1 实际后果 | 提案以自然遗漏与最终决定为收益，优于放行率；要补 AR-1 的真实处置闭环。 |
| 2 相关 State | 原文直视图和候选版本正确；保持必要关系，不能把取消大提案等同取消对象绑定。 |
| 3 连贯维度 | 保留高层方法题，允许区分关系，符合原则；不要求所有问题原子化。 |
| 4 自描述合同 | 新题文未冻结的状态写明，作为设计稿可以；实施前须冻结义务、依赖和复用条件。 |
| 5 定点纠偏 | 当前统一 unknown 退回范围过宽；缩小作用范围须同时防止 AR-1 的漏处置。 |
| 6 合批与依赖 | 已有同 State 合批应保留；只复查相关关系的收益尚未验证，不能预先宣称少计费或更准。 |
| 7 类型与未知 | route-control 的 Score unknown 已正确隔离；关系消费者的统一 return 是政策限制，不能改成 false/PASS。 |
| 8 组合与权责 | 方法履行与事实结论分开正确；AR-2 必须把真实仲裁入口写清。 |
| 9 资格与边际价值 | 新计划的自然首答、问题清单、同图判断器、①/②和反向控制能区分重要混淆；12 家族只作方向性证据。 |
| 10 有界设计 | 复用合同、一次修正与一次复查正确；新增未决入口若采纳必须共用额度，不能增设隐藏循环。 |

## 非阻塞建议与证据上限

- **候选增加不应天然变成必要门。**当前 `route_control.consume:252` 遍历全部保留候选，任一个中间值即可阻断已有明确主方法。它是值得检验的消费假设；还不能断言所有弃权都错，更不能统一删除该门。开发反例应同时包括“新增候选确有必要竞争”和“新增候选只有辅助价值”。
- **①/②归因要写清包的范围。**②允许额外独立仲裁，而①通常没有；若出现差异，可先称政策包效果。要单独归因于强制处理而非多一次推理，应报告未仲裁配对及仲裁子集，或另设有相同机会的控制。无需现在扩成全组合试验。
- **轻重与争议不能由临时偏好决定。**“低影响噪声”“重大争议”目前是设计用语；形成可运行合同前要写明哪些输出只需有据说明、哪些必须仲裁、哪些必需保留未决。不能以“轻微”关闭必要事实或范围义务。
- **局部模型能力仍是开放解释。**修复输入与消费后，Jev 仍可能给出不准确/不稳定的关系评估；当前证据不允许把余下失败一概归咎架构，也不允许反向宣判 Jev 机制无价值。v1.2 的六次开发请求只支持那三个暴露对象的定点改进。

## 如何证伪提案

在 D 先验证 AR-1、AR-2 和依赖失效边界。正确候选不应仅因用户保留原错误主张继续被命中；错误候选仍须产生处置义务；必要未知应保留限制；辅助 unknown 不应阻断无依赖动作；拒绝误报必须有据且符合仲裁规则。工程夹具只能证明这条消费路径按合同走，不证明检测有效。

N 的五组复核对照值得保留：若问题清单已经解释全部改善，Jev 的额外判断收益未证实；若 Jev 观察准确但②仍漏用，是消费/宿主问题；若②强制采纳错误观察而改坏，是该政策的反例；若正确处理比例增加却最终决定不改善，新增处理没有达到目标。全分母计入未决、回退与技术失败，不按成功提交者筛选。若合理新来源长期都是平局，应收缩结论与投入，不能通过预置更坏候选制造增益。

## Gate Probes / 交付定位

这是对待实施设计的独立架构判断与一个离线控制流反例，服务于作者有界修订和用户决定是否继续。没有新实时模型证据，没有默认上线结论。三项阻塞修订后可复核文档基线；运行时改动仍需单独通过具名工程检查与预注册实测。

## 复核 1 / AR-1 的有界代码修复

作者随后修改了 `route_control.py` 并添加四项回归；审计员独立阅读 diff，未修改这些文件。复核时的文件身份：

| 文件 | SHA-256 |
| --- | --- |
| `experiments/typed_decision/route_control.py` | `ad1c6a725a99b62c4bdd663cc8480d0b0b9a7fdd5044c2643d5b330a2777b18f` |
| `tests/test_route_control.py` | `da24f9d36d9b67efe516609110630f339538114f732d4a1859988a1d24f0d394` |

修复把最新关系评估中非 `continue_original` 的状态绑定到受影响事项，分别保留 `relationship_correction_unverified`、`relationship_correction_unresolved` 或 `relationship_scope_unresolved`。派发前检查该限制，位于前置产物复评入口之前；因此另一产物被接受不能清除本候选的纠偏义务。独立事项仍能执行。修复未降低阈值，也未增加纠偏或调用额度。

审计员使用上述 miniconda Python 独立运行以下四项测试，**4/4 通过**（0.155 秒）：

- `test_recheck_still_requests_correction_keeps_scope_pending`：再次命中保持 pending，另一事项执行，重入不增调用。
- `test_unverified_correction_is_not_consumed_as_cleared`：关闭复查保留未验证身份。
- `test_accepted_predecessor_does_not_clear_unresolved_correction`：前置已接受不能清除未解决纠偏。
- `test_accepted_predecessor_does_not_clear_relationship_return`：前置已接受不能清除关系评估退回。

**AR-1 的已复现代码漏口解除。**这只解决现有合同的确定性消费缺口；新提案的辅助 unknown 分类、原文直视图与相关问题复用仍未实施。旧封存记录不重算，新的 implementation 身份不能作为旧请求的原版本恢复。上文保留原反例以说明修复原因。

## 复核 2 / 文档阻塞解除与最终版本

审计员重新读取三份文件，最终身份如下：

| 文件 | SHA-256 |
| --- | --- |
| `SOURCES.md` | `78c47299ed25fb4f5472af0d5f6a123b8db4430a7e6566dda19ac4134a52fa94` |
| `PROPOSAL.md` | `38b7c84ed69f0ec57ed76a6d76ca35eac5e02c0be8f2cbbcc21dc2dccdff2a59` |
| `TEST-PLAN.md` | `a6a1af738ab1eab1e93ce313cd5757ccd290bf0b3f7989ac975f48fa451fa5e0` |

- **AR-2 解除：**提案明确本切片的初始 M02/M03 未决交回原宿主并计未决；未来接仲裁须另作接线、预算与验证，不声称现有入口可达。
- **AR-3 解除：**工程执行与记录改成可验证目标，并承认软件缺陷与语义判断限制；没有承诺绝对正确。
- **AR-1 文档闭合：**提案记录本轮有界修复及独立事项继续，明确它不等于新消费方案上线。
- **测试计划改进：**①/②的仲裁前主比较与仲裁后政策包效果分开，补充同机会约定尚需适配器实现；S0/S1 分层明确；宿主、观察、仲裁、评阅和技术预留都有总上限。实际初始未决没有使用仲裁机会必须如实记录。源获取成本另行冻结后才能执行。

剩余建议均为后续实施/冻结检查项，不阻塞本次设计文档交付。尤其是同 State 可见范围与题目显式引用不同，相关复用资格应有合同与反例；不能依据“引用没变”自动复用全部语义判断。本文没有新增实时模型准确率、端到端增益或全面工程资格结论。

## 复核 3 / 限定最终版本确认

按作者请求，只复核最后的语义依赖规则、预定比较及仲裁后宿主回执预算；不扩展审计范围。最终文件身份更新为：

| 文件 | SHA-256 |
| --- | --- |
| `SOURCES.md` | `78c47299ed25fb4f5472af0d5f6a123b8db4430a7e6566dda19ac4134a52fa94` |
| `PROPOSAL.md` | `6653f804c865bcc463026c5fba841373f711a9084e6f3eb71817ab39794507c0` |
| `TEST-PLAN.md` | `cf961919f0d443f6681a61d02361e5c996a56b37589352e06e6638608f612038` |

提案现已明确：完整 State 可见，locator 不构成访问隔离；候选、框架/目标、所需证据及合同变化按各题语义依赖失效，依赖不明时重评相应组。这采纳了前述非阻塞建议，没有改变控制归属。

计划固定 Jev 观察②为事前主候选，并列明清单效应、同图后端差异、①/②政策、产品净效果和相对清单的边际效果；不在揭盲后挑胜方，不将问题清单已能解释的收益归给 Jev。仲裁后的原宿主回执另设 D≤12、N≤60，总计草案为 Jev≤52、Codex≤303；算术一致。回执仍受既有两次 execution 尝试上限约束，不重置 correction/recheck，不因仲裁意见存在就记为已消费。

`route_control.py` 与 `tests/test_route_control.py` 的 SHA 与复核 1 完全相同，因此本次未重复运行测试。**架构裁决保持通过，无新增阻塞。**本次限定复核没有业务模型请求；上述额度仍为未来冻结草案，新消费者未实施，D/N 未运行，#211 资格状态不变。
