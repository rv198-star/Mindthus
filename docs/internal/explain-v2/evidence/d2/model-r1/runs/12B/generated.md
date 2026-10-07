---
title: 请求验证与返回流程
subtitle: 开发期假设／语义样例
layout: doc
lang: zh-CN
---

## 结论与限定 {#result}
```callout info
格式决定流程分支，不证明内容真实
本页仅展示开发期假设流程／语义样例。
格式有效时进入处理器并返回结果；格式无效时返回错误，用户修正后再提交。
格式通过不证明内容真实，处理器不获得额外执行授权。
```

## 提交、返回与再提交 {#flow}
```flow LR
user[用户] -> validator[验证器]: 提交请求
validator -> processor[处理器]: 格式有效
processor -> result[结果]
result -> user: 返回结果
validator -> error[错误]: 格式无效
error -> user: 返回错误
user -> correction[用户修正请求]: 收到错误后修正
correction -> validator: 再提交
```

路径说明：用户提交请求后，格式有效则经处理器返回结果；格式无效则返回错误，用户修正后重新提交到验证器。

## 图中对象 {#details collapsed}
| 对象 | 在本语义样例中的作用 |
| --- | --- |
| 验证器 | 按格式是否有效决定分支 |
| 处理器 | 接收格式有效的请求，再返回结果 |
| 用户 | 提交请求；收到错误后修正并再提交 |