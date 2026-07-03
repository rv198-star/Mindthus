# TVG-Profile 案例三：`cinematic-colossal-realism`

## 这页讲什么

这是我们为 TVG-Profile 准备的四层完整案例。我们不是把外部 cinematic prompt skill 原样搬进来，
而是把原 SKILL 里真正有效的行为习惯拆开，重组为 TVG 能理解、能复查、能长期维护的高级包。

对应资源：

- `skills/tvg/resources/value-profiles/cinematic-colossal-realism/profile.md`
- `skills/tvg/resources/value-profiles/cinematic-colossal-realism/resources/`
- `skills/tvg/resources/value-profiles/cinematic-colossal-realism/scripts/`
- `skills/tvg/resources/value-profiles/cinematic-colossal-realism/examples/`

## 我们为什么做这个案例

我们做这个案例，是因为外部 cinematic skill 的强，并不只是提示词写得长，而是它带着一整套行为习惯在工作：
它会保留人类尺度锚点、会把庞然物拆成局部威胁碎片、会要求环境反馈、会避免媒体污染词、会在高压场景下做减法，
而不是任由画面越堆越满。

如果我们直接复制原 SKILL，问题也很明显。得到的是一份行为结果，不是可迁移的结构；一旦场景变化、模型变化、
目标变化，维护会越来越难。所以这个案例真正想做的，是把“它为什么有效”从 wording 里剥离出来。

## 我们怎么把它拆成四层

| 层 | 这次怎么落 | 作用 |
| --- | --- | --- |
| `value_semantics` | 定义 human-scale anchor、three-layer scale、decisive pressure frame、physical feedback、negative-constraint hygiene 等好标准 | 先说明什么叫“更有压迫感但不脏乱” |
| `realization_surface` | 把价值落到 witness position、scale ladder、partial visibility、camera and light、generated-image audit 上 | 让 reviewer 能指出问题具体出在哪个 surface |
| `gain_policy` | 写明哪些增益动作最常有用，例如先做 decisive frame、director shot spine、director subtraction pass、controlled fracture coherence、shot economy mode | 避免高压场景里一味做加法 |
| `runtime_support` | 用 subject taxonomy、prompt skeleton、negative constraints、lint 和 examples 提供确定性支撑 | 帮忙补字段、查污染、记录证据，但不替 TVG 决定 exit |

这也是我们最想借这个案例讲清楚的地方。它和普通 prompt profile 的差别，不只是“写得更细”，而是把判断、
显现面、增益路径、支撑物拆成了不同层级。

## 为什么我们选这条路线，而不是直接复制原 SKILL

因为这条路线把原 SKILL 降成了行为样本，而不是 source truth。

这件事看起来像减法，实际上是让 Profile 更稳的关键。只要承认外部 SKILL 只是一个高质量行为样本，
我们就会自然做三件正确的事：

- 不复制它的 concrete wording。
- 不把一次好图当成一般性证明。
- 不把脚本结果误当成美学 verdict。

这样得到的包，反而更适合长期维护，因为我们讨论的是“哪些行为值得留下”，而不是“哪段神 prompt 最神”。

## 这个案例里，我们最看重的是必要的减法

这个案例不是单纯加更多镜头语言，而是明确把很多常见假增益压下去。比如我们会主动压这些东西：

- 亮电光、魔法高光、平行 micro-actions 不能抢走 first read。
- 前景碎片、建筑边缘、树枝、武器不能把画面切成无关条带。
- 破碎感必须服务主事件，不能只是 decorative destruction。
- 高压档不等于把每个区域都写满，反而要保护 one major event。

这也是为什么我们后来会引出 `director subtraction pass`、`controlled fracture coherence` 和 `shot economy mode` 这几类 surface。
它们本质上都在回答同一个问题：怎样只加导演感，不回脏乱差。

## 为什么 `runtime_support` 不是“半个新 SKILL”

因为我们给它的角色，本来就只是确定性支撑，不是审美裁决。

它们可以做的事，是帮你分类 subject、搭 prompt skeleton、检查 human-scale anchor 有没有丢、negative constraints 有没有污染、field template 有没有漂。

它们不能做的事，是替你说“这张图已经电影感足够了”“这个 profile 已经成熟了”“这轮可以 freeze 了”。这些判断仍然属于 TVG loop 里的 agentic audit。

这条边界看起来保守，实际上很重要。因为一旦脚本开始输出语义 verdict，整个 Profile 很容易从“支撑 TVG”滑成“绕开 TVG”。

## 为什么我们把它当作 TVG-Profile 高级用法示例

它同时满足三个条件。

第一，它有清楚的迁移对象。外部 SKILL 足够强，能提供真实行为样本。

第二，它有清楚的边界。这个项目从一开始就不是要复制原 SKILL，也不是要证明“新包全面赢过原 SKILL”，而是要把行为拆成 Mindthus 里可复用的结构。

第三，它有完整的证据纪律。单轮 profile power、loop-assisted production、Images2 对比、pressure 2-5 场景适配，这些都被当成观察证据，而不是胜负口号。

## 证据上限

这个案例的证据上限我们也刻意写得很清楚。就算某次 Images2 对比里，`cinematic-colossal-realism` 在某个压力档表现很好，也只能支持：

- 这套四层包对某类 colossal cinematic prompt 有可用约束力。
- 某些 runtime support 和减法 surface 确实能改善部分失败模式。

它不能直接支持：

- 这套 Profile 已经成为所有电影感提示词的默认答案。
- 脚本足以替代人工审图。
- 某次对比输赢就证明原 SKILL 或新方案的长期优劣已经定了。

## 导航

- 返回 [TVG 详细介绍页](../tvg.md)
- 查看 [轻量 Profile 案例](plain-sharp-skill-intro.md)
- 查看 [风格型影视 Profile 案例](film-style-profiles.md)
