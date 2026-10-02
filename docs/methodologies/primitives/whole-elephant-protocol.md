# Whole Elephant / 全象流程

## Core

局部真相不能自动拥有整体定义权。围绕实际判断对象和用户目标，确认哪个因素
真正控制结果；如果局部已经充分或用户明确只问局部，就保留它。
全局不是更抽象、更大的对象，也不是强行唱反调。

## Mainline

说明对象是什么、结果由什么控制、当前局部观点覆盖到哪里：

- 足够覆盖目标：retain / grant_as_definition。
- 局部正确但接管整体会改变错误行动：限定范围或 reject_as_definition，讲清主次与后果。
- 用户明确选择合法取舍：保留该目标，不拿另一目标替他决定。
- 证据不足或对象未定：保留未知，指出最小补证据动作。

只有能改变策略、证据要求、风险、下一步或停止条件的纠偏才展开。
让读者看见重要判断，不需要先展示六字段、固定首句或内部标签。

## Guardrail

这保护局部/整体混淆，不覆盖用户价值、权限或事实取证。
不得把接口机制、指标、测试全绿等自动升为完整价值；也不得因它们是局部就
贬低已经充分的局部解释。强压力要求更谨慎的证据，不转移定义权。
“也很重要”未解决主次时需补判断，但“不只是”、让步句或句序本身不证明失败。
scripts must not decide semantic truth。

## Boundary

没有定义/结果控制混淆就不用；缺事实先取证；风险/承载或结构问题交给具体方法。
正确的条件性结论、规范性不确定性与用户合法取舍不应被强制改成否定。

## Runtime support

调试、handoff、独立审阅或结构化重放时才生成审计载荷：
`canonical_object / result_controller / misdirection_if_local_wins` 是语义定位；
现有 v0.1 compact 载荷仍包括 `local_frame_wins / whole_object_wins / better_direction_for_target`。
展开载荷沿用既有 hierarchy、reconstruction、formal_answer_plan、strategy 的 schema。
这属于显式 audit 合同，不是每份业务答案必须输出的流程。

`python3 scripts/primitives/validate_whole_elephant.py audit.json --json` 验证字段、
枚举及内部信息泄漏；词面/标签相似性仅产生 `semantic_hints`，不能裁决真伪。
`shape_only` 不代表内容正确，`semantic_verdict=not_validated`；没运行就不能冒称通过。
调用 using-mindthus fidelity 校验时沿用其触发标记和验证/未运行证据要求。

历史开发案例与完整旧文保留在固定基线 Git；公开案例不能作为每题预期答案。
参见 [共享原语](../shared-primitives.md)、[Frame Fitness](frame-fitness-check.md)、
[使用入口](../../../skills/using-mindthus/SKILL.md)。
