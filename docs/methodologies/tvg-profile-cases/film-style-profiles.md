# TVG-Profile 案例二：风格型影视 Profile

## 这页讲什么

这一组案例是我们用来展示另一条高级路线的：不用脚本，也能先把“导演感”这种很容易飘成形容词的目标，
拆成可审查、可讨论、可迁移的 Profile。

这里合并介绍两个资源：

- `shaw-brothers-wuxia-fantasy`
- `king-hu-wuxia-cinema`

它们都属于影视画面型 Profile，但抓的不是同一种“电影感”。

## 我们为什么把这两个案例放一起

因为我们想借它们一起说明一个关键点：Profile 真正要定义的，不是一个华丽标签，而是一种可检查的价值语义。

| Profile | 真正在抓什么 | 主要减法 |
| --- | --- | --- |
| `shaw-brothers-wuxia-fantasy` | 棚拍时代的人工感、剧场感、宽银幕构图、硬光色块、实物神怪存在 | 减掉现代仙侠 gloss、CG 奇观、自然主义灾难片语法、无功能的特写堆积 |
| `king-hu-wuxia-cinema` | 空间智力、延迟动作、观看者知识状态、节奏停顿、关系镜头 | 减掉邵氏棚拍逻辑污染、现代武侠 trailer inflation、只剩漂亮动作 pose 的假导演感 |

我们把两者并排放出来，就是想让你更直观看见：所谓风格，不是“再多几个 cinematic adjective”，而是你到底要求画面在哪些单位上交代得更清楚。

## 这组案例里，我们重点在演示什么

我们最看重的，不是这两个案例“像不像某个导演”，而是它们把“风格”从印象词，变成了下游可检查的 surface。

在 `shaw-brothers-wuxia-fantasy` 里，style 被翻译成了棚景、布光、色块、剧场式 blocking、practical creature 逻辑和 storyboard panel function。它不是笼统地说“更有老港片感觉”，而是要求你能指出这张图里的舞台人工感到底落在哪。

在 `king-hu-wuxia-cinema` 里，style 被翻译成了 routes、thresholds、line-of-sight、watcher knowledge-state、delay、abrupt release 和 relation shots。它强调的不是“古意”或者“禅意”这些大词，而是观众在每个 panel 里到底知道了什么、没看到什么、为什么这一拍要晚一点才爆。

## 为什么我们把它们算作高级用法

虽然没有脚本，这两个 Profile 其实已经非常“硬”了，因为它们同时做了三件事。

第一，它们有明确的 `value_semantics`。什么算对，什么算错，不是模糊审美。

第二，它们有足够细的 `realization_surface`。价值落在 shot / panel / screen relation / knowledge-state 这些单位上，所以下游 reviewer 真能指出问题出在哪。

第三，它们有很强的 `gain_policy`。它不只是鼓励“多给镜头”，而是规定什么时候该拆、什么时候该并、什么时候要做减法，避免 coverage inflation。

这也是为什么我们会把它们放进高级用法里。它们明明是风格案例，却并不空泛，因为它们用的是减法式约束，而不只是加法式修饰。

## 为什么这一层我们还不急着上脚本

这类案例的主要失败，并不在字段缺失，而在语义跑偏。脚本可以帮你查一些表面问题，但它很难替你判断：

- 这是不是现代仙侠 gloss，而不是邵氏式 theatricality。
- 这是不是漂亮动作 pose，而不是 King Hu 式的空间与知识状态。
- 这次加镜头，到底是更有导演感，还是只是 shot count 变多了。

所以在这一步，我们更看重的不是先写 runtime_support，而是先把前三层写硬。否则脚本只会把一套语义没定住的偏好，伪装成稳定流程。

## 如果你要拿这组案例做迁移

如果你想做别的风格型 Profile，我们最希望你迁走的，不是具体导演词，而是这三条纪律：

1. 风格必须落在可检查单位上，不能只停留在抽象标签。
2. 必须同时写加法和减法。只说“要更多什么”不够，还要说“必须压掉什么”。
3. 必须把污染源写出来。错误样例、生成图、旧 prompt、相邻导演风格，哪些只能当测试对象，不能反过来当 profile source，要写明白。

## 导航

- 返回 [TVG 详细介绍页](../tvg.md)
- 查看 [轻量 Profile 案例](plain-sharp-skill-intro.md)
- 查看 [四层高级案例](cinematic-visual-direction.md)
