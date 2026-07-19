# Public Methodology and Runtime Surfaces

Mindthus 把“读者需要理解的方法”与“agent 必须执行的运行合同”分开维护。这样既不牺牲
runtime 安全，也不会让公共方法文档变成一段可被任意 reader-agent 误执行的隐藏脚本。

## Surface Contract

The classification vocabulary is: `public methodology`, `skill runtime instruction`,
`validator contract`, and `example`.

| Affected surface | Classification | Public surface keeps | Runtime surface owns |
| --- | --- | --- | --- |
| `docs/methodologies/sela.md` Twin-Lens Handshake | public methodology | SELA 校准方向、MPG 决定路径动作，以及两者的边界 | direct-load companion 读取、默认输出形状和 debug 可见性 |
| `docs/methodologies/mpg.md` Twin-Lens Handshake | public methodology | 趋势主线需先校准，长期方向与当前载体必须分开 | direct-load companion 读取、默认输出形状和内部标签处理 |
| `docs/methodologies/primitives/whole-elephant-protocol.md` core and audit package | public methodology | 整体对象、结果主控、局部真相边界和 validator 能力上限 | 审计 schema、命令执行、失败阻断、fallback、路径解析和 trace 可见性 |
| `docs/methodologies/wae.md` Domain Gate and Control Gate | public methodology and boundary | WAE 只处理 agentic system 的 controller mismatch | 没有额外 runtime gate；具体 skill 路由仍由 `skills/wae/SKILL.md` 承担 |
| Method cases and sample theses | example | 帮助读者理解规则，不自动升级为规则 | runtime contract 不从单个例句反推新义务 |

## Ownership Rules

- `docs/methodologies/` 解释 core、mainline、guardrail 和 boundary，可以描述合格输出应当
  达到的语义效果，但不要求任意 reader-agent 加载 skill、执行命令或隐藏命令输出。
- `skills/*/SKILL.md` 与 `skills/*/resources/` 承担 skill discovery、companion loading、
  validator、fallback、trace 和输出形状合同。
- `scripts/` 只验证可机械判断的 shape、状态和一致性，不能宣布语义真相。
- `tests/` 分别保护公共语义和 runtime 合同；公共文档测试不得依赖 command-shaped 精确短语。

如果 runtime 义务变化，先更新 skill/resource 和对应 contract test；只有方法含义或边界真的
变化时，才更新公共方法文档。
