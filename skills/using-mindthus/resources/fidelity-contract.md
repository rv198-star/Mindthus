# using-mindthus fidelity / 显式审计合同

## Purpose

用于用户要求审计、debug、handoff 或重放时的结构化证据，不是普通业务回答的固定步骤。
主路径见 SKILL.md。验证器是 Shape & Evidence Risk Report，scripts must not decide semantic truth。

## Contract

显式生成 v0.1 载荷时仍满足现有模板：applicability、判断动作、action_posture、
plain_language_conclusion、证据与未决。缺输入可以 acquire_information；不适用可以退出。
`partial_truth_capture_triggered` 为显式布尔值；触发时提供 v0.1 `whole_elephant_audit`
与 `whole_elephant_validation`。Compact Semantic Triad 定位对象、结果控制和误导后果；
载荷保留六个 compact 字段，以兼容已经保存的 audit，不要求普通答案逐项展开。

展开 audit 的枚举沿用 grant_as_definition / reject_as_definition /
qualify_as_component / blocked_by_missing_evidence。grant 合法时局部可拥有定义权，
不可预设否定；不足的依据保留未知。

## Evidence

- 运行结构校验：登记准确 command、output_evidence、script_verdict=shape_only。
- 未运行：script_verdict=not_run_fallback，登记 fallback_reason 与 self_check_evidence；
  这不是脚本通过或内容验收。
- 字段、枚举及真实内部 stdout 泄漏可被 block；词面、句序和自由文本近似只给
  candidate-only-review-hint。semantic_verdict 始终 not_validated。
- 人工/Agent 仍独立判断局部是否越界、主要价值是否充分、证据和权限是否满足。
  干净措辞或填满表格不证明答案正确。

## Runtime support

`templates/fidelity-output.json`；`scripts/validate_using_mindthus_output.py`；
`python3 scripts/primitives/validate_whole_elephant.py audit.json --json`。
历史 Skills/4K 参考答案保留在原 Git 与开发归档；不进入新业务提示，不当通用模板。
