---
title: 请求验证与返回流程
subtitle: 开发期假设／语义样例
layout: doc
lang: zh-CN
---

## 结论与边界 {#result}

```callout info
格式决定流程分支，不证明内容真实
本页仅展示开发期假设流程／语义样例，不代表生产进度。格式有效时进入处理器并返回结果；格式无效时返回错误，用户修正后再提交。格式通过不证明内容真实，处理器不获得额外执行授权。
```

## 提交、返回与再提交 {#route}

```flow LR
user[用户] -> validator[验证器]: 提交请求
validator -> processor[处理器]: 格式有效
processor -> user: 返回结果
validator -> error[错误]: 格式无效
error -> user: 返回错误
user -> correction[用户修正请求]: 收到错误后修正
correction -> validator: 再提交
```

路径说明：用户提交请求后，验证器按格式是否有效分流；有效请求经处理器返回结果，无效请求返回错误，用户修正后再提交到验证器。

## 图示补充 {#notes collapsed}

“错误”和“用户修正请求”分别表示错误返回与修正步骤。再次提交后，仍由验证器判断格式是否有效。