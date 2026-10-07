---
title: 请求验证与修正再提交
subtitle: 开发期假设／语义样例
layout: doc
lang: zh-CN
---

## 结论与限定 {#result}
```callout info
格式有效进入处理器；格式无效返回错误，用户修正后再提交
本流程是开发期假设／语义样例。
格式通过不证明内容真实，处理器不获得额外执行授权。
```

## 提交与返回路径 {#route}
```flow LR
user[用户] -> validator[验证器]: 提交请求
validator -> processor[处理器]: 格式有效
processor -> result[结果]: 返回结果
result -> user: 结果返回用户
validator -> error[错误]: 格式无效
error -> user: 错误返回用户
user -> correction[用户修正]: 收到错误后修正
correction -> validator: 再提交请求
```

路径说明：用户提交请求后，格式有效则进入处理器并返回结果；格式无效则返回错误，用户修正后再提交到验证器。

## 流程称谓 {#details collapsed}
“有效”和“无效”均指请求格式。图中的结果返回与错误返回，是开发期假设流程中的两条返回路径。