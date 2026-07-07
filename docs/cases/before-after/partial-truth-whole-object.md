# Partial Truth / Whole-Object Correction

## User Input

Skills 不就是高级 prompt 吗？所以 Mindthus 本质上只是写了一堆提示词。

## Baseline-Style Output

可以这么理解。Skills 的核心确实是把提示词和说明文档组织起来，让模型在需要时读取，所以 Mindthus 本质上也是一组经过整理的 prompts。

## +Mindthus-Style Output

“Skills 里有 prompt”是局部真相，但不能定义整个对象。Mindthus 的完整对象包括路由入口、方法边界、测试契约、validator、fixture、发布包和运行时证据。prompt 是接口载体，不是全部价值承载者。把它定义成“高级 prompt”会误导优化方向：你会只改措辞，而忽略脚本门禁、测试覆盖、fixture 质量和真实任务验收。

## What Changed

The judgment changed from accepting a locally true mechanism as essence into reconstructing the whole object and assigning definition authority.
