# Changelog

## Unreleased

暂无。

## v0.5

发布日期：2026-05-18

### 新增

- 新增项目级方法分层纪律，要求方法写作显式区分 `core`、`mainline`、
  `guardrail`、`boundary`、`example` 与 `runtime support`，避免主思想被
  从属补漏和细节优化冲淡。
- 新增 `SELA` 时机检查，用临时保留、锁死未来、行动窗口三问，防止长期系统
  效率判断被误写成立刻切换动作。
- 新增方法分层契约测试，校验项目级规范存在、所有 `SKILL.md` 入口按分层顺序
  组织，并阻止未归入分层体系的额外 H2 段落。
- 新增 `SELA` 契约测试，校验时机检查保持轻量，不升级成独立原则或人文价值观。

### 调整

- 重构所有 `SKILL.md` 入口，使主路径、从属补漏、边界和运行支撑材料分层清晰。
- 将 `using-mindthus` 的前置校准保留为主路径，将 Anti-Spiral 保留为从属补漏。
- 将 `tplan` 的启动策略和运行循环保留为主路径，将 Alignment Gate、
  Anti-Spiral Gate、Linear Continuation Gate 等放入从属补漏层。
- 将 `WAE`、`TVG`、`3L5S`、`EDSP` 的脚本、模板、常见误用和停止条件从主路径中
  分离出来，降低入口阅读负担。

### 校验

- `python3 -m unittest tests.test_packaging_docs -v`
- `python3 -m unittest tests.test_method_layering_contract -v`
- `python3 -m unittest discover -s tests -v`
- `python3 -m unittest discover -s tests/tplan -v`
- `git diff --check`

## v0.4

发布日期：2026-05-09

### 新增

- 新增 `tplan` Linear Continuation Gate，用于高影响决策。
- 新增 `path_assessment`，包含 `marginal_roi`、`path_role` 与 `evidence_delta`，
  要求同路径继续执行暴露 Mission-relative reasoning surface。
- 新增 Premise Calibration，并写入 `using-mindthus` 与 `AGENTS.md`，作为选择
  Mindthus skill 前去除二手概念的前置动作。
- 新增 Mindthus router pressure tests，覆盖 ROI 标签、first-principles 名称陷阱、
  workflow/agent 伪二分、趋势口号和 polished artifact 陷阱。
- 新增 Anti-Spiral Self-Audit 方法资源，并在 `AGENTS.md` 与 `using-mindthus`
  中提供激活入口。
- 新增 `tplan` `anti_spiral_audit` runtime gate 文档，覆盖重复局部修补、加层、
  负反馈和弱 evidence-delta continuation。
- 新增 WAE 指引，将局部修补螺旋视为 workflow/agent/evidence 控制边界失败模式。
- 新增 Anti-Spiral A/B pressure tests，分别评分 agent 是否触发机制以及是否退出螺旋。

### 调整

- 高影响 `tplan` hook output 在 Mission-aligned、切换 active task、改变 Mission status、
  subtraction、escalation 或 Mission closure 时要求 `path_assessment`。
- `tplan` 文档明确：elapsed time 不是 continuation 的根判断标准；marginal Mission ROI、
  path dominance 和 expected evidence delta 才是相关判断面。

### 校验

- `python3 -m unittest discover tests/tplan -v`
- `python3 -m unittest tests.test_packaging_docs tests.test_mindthus_router_contract -v`
