# Explain Compact Style R1 · 视觉重构记录

日期：2026-10-08。**实现与回归检查完成；主观风格待 Owner 确认。**

Owner 已认可上一版功能，本轮要求“紧凑小一号”，减少大标题、宽松圆角卡片的通用风格。基线为 `0b138451558d55b63b6894086b27ffa36bb59673`，在原 `feat/explain-html-v2` 分支继续，不重开功能设计、不合并或发布。

## 视觉方向

采用紧凑编辑式简报：暖白底、石墨文字、低饱和苔绿强调，警告/错误保留语义色；`blueprint` 保留偏冷的配色。桌面页头把工具区放在标题右侧；章节用细线、编号与对齐分组，不再每节套一个大圆角卡片，也不在图形外再加渐变框。

| 项目 | 重构前 | 紧凑版 |
| --- | --- | --- |
| 桌面主标题 | 37px | 24px |
| 章节标题 | 19px | 15px |
| 正文 | 15px | 14px |
| 表格正文 | 13px | 保持13px，收紧行间距 |
| 图内标签与坐标 | 已有值 | 保持原字号与图布局 |
| 章节外框 | 11px圆角卡片 | 细线分区、无圆角套框 |
| 页头 | 标题和工具分成多行 | 小标题与工具横向并列 |
| 整宽指标 | 逐项纵排 | 按原顺序双栏，窄屏还原单栏 |

没有使用整体 zoom/scale 缩放，也没有为缩短页面而删除内容、合并状态、隐藏限定或擅自折叠正文。

## 同稿实测

11份原稿：原组件展示、上一轮同源业务报告及9份既有 B 短稿。两版分别以 Node/Python 渲染，得到22组前后对照。**移除 CSS 并归一化编译器版本显示后，每组 HTML 完全相同**；源稿摘要逐一相等。

同一1440px Chromium视窗，默认展开状态、Node路径；以下为解释根容器高度，不是受视窗最低高度影响的整张截图高度：

| 样例 | 前/后高度 | 减少 |
| --- | --- | --- |
| 同源业务报告 | 1871 → 1424px | 23.9% |
| 进度简报31B | 1011 → 751px | 25.7% |
| 流程11B | 1025 → 738px | 28.0% |
| 组件展示 | 2111 → 1567px | 25.8% |

这是固定稿件的版面测量，不是对所有报告的效率或用户理解率结论。字体渲染随操作系统可能不同。

## 验证

- 22/22 同源输出除 CSS/版本外完全一致，源稿可恢复；解析器、HTML renderer、Node/Python布局与JS文件相对基线未改动。
- 88/88 浏览器配对检查（实际176次页面检查）：11稿 × 两引擎 × 1440/390px × JS开关；初始可见文字相等，无新增整页溢出、SVG文字越界或默认图形裁切；键盘折叠、视图切换、展开、深色和图形尺寸切换通过。
- 7/7 附加检查：paper/blueprint × 明/暗四组合的文字配色与打印，以及320/720/1024px窄屏检查；所测文字配色最小对比度4.81:1。此为这些配色组合的检查，不是完整无障碍认证。
- Python3.12 focused tests：107项，106通过、1个既有依赖skip、0失败；调用回执 `session-9ff08c306c61b01204507387`，16.732秒。
- 对照查看器：4稿 × 新版/上版/并排截图，共12/12检查，无外部请求和脚本错误。
- 新模型生成：0；原18次模型生成和评审材料保持不变。

证据：[baseline.json](baseline.json)、[checks.json](checks.json)、[browser-results.json](browser-results.json)、[preview-check.json](preview-check.json)。

## 产物与复核

OCI持久缓存：`/srv/agentdock/.cache/mindthus-explain-compact-r1`。`before/`、`after/`含两种引擎真实HTML，`sources/`含原稿，`qa-r1/`含原始截图与浏览器结果，`preview.html`为离线自包含对照查看器。查看器仅用于本轮开发验收，不进入Skill运行时。

已有快照可用以下脚本复核；输出使用新的目录，保留原证据：

```bash
EXPLAIN_PLAYWRIGHT_MODULE=/path/to/playwright \
EXPLAIN_CHROMIUM=/path/to/chromium \
node check_style.mjs /path/to/comparison-cache /path/to/new-check-output
```

首次构建查看器：`python3 build_preview.py /path/to/comparison-cache`。脚本从实际HTML与截图组装，不通过模型重写内容；已有文件拒绝覆盖。

## 范围

功能认可来自 Owner 本轮反馈；新风格的审美认可仍由 Owner 确认。本轮没有重复独立模型评审，没有更改 TPlan、增加新组件或恢复旧 Jev 工作。浏览器/链接预览不冒充 ChatGPT 宿主 inline app-block 的真实交互回执。
