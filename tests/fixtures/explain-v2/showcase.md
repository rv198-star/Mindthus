---
title: Explain HTML V2 · 组件展示
subtitle: 以下内容是展示样例，不是项目进度或生产测量。
layout: sheet
theme: paper
lang: zh-CN
---
## 结论与限制 {#conclusion}
```callout info
页面由短稿编译生成
模型只描述内容与关系，程序负责版面和图形。
这是组件展示；不代表完整 V2 已验收或已发布。
```

## 状态比较 {#comparison}
| 表达方式 | 负责内容 | 负责排版 | 适用场景 |
| --- | --- | --- | --- |
| 普通 Explain | 当前 Agent | 聊天表面 | 简短说明 |
| Node 渲染 | 同一份源稿 | 自动图布局 | 分支、合流与回路 |
| Python 回退 | 同一份源稿 | 确定性基础布局 | 没有 Node 的环境 |

## 流程与关系 {#pipeline span=2}
```flow LR
输入 -> 编译器: 解释稿
编译器 -> Node: 可用时优先
编译器 -> Python: 环境不满足
Node -> 同源页面
Python -> 同源页面
同源页面 -> 读者: 理解与查阅
```
关系来自这份展示稿；箭头不表示新增的业务授权。

## 进度、区间与未知 {#progress span=2}
```progress
示例完成率 | 62 | % | 假设数据，仅演示百分比表示
测试工作占剩余量 | 35..55 | % | 假设区间；实色为下界，斜纹为不确定段
剩余测试工作 | 6..9 | 小时 | 假设估计，保留原单位，不换算总完成率
验收时间 | ? | 小时 | 尚未估计；未知不是零
```

## 阅读交互与引用 {#evidence collapsed}
这里展示原生折叠；无 JavaScript 也可打开。
保留**条件、风险、未知和引用**。例如：[编译器工单](https://github.com/rv198-star/Mindthus/issues/227)。

逐字示例：`{"status":"blocked","count":0}`。
