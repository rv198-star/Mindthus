# Release Defaults / 发布默认规则

## Stable 发行

2026-10-03 Owner 明确：Stable发布不再要求同步ROI Beta。
本轮 Owner 进一步确认：**ROI Beta 已停止维护及后续发布**。以后仅维护 Stable；
历史 Beta 标签、资产、源码和资格记录保留。

Stable 默认提供：

- source tag `vX.Y.Z`；
- plugins、skills 两份白名单归档；
- 覆盖实际归档的 `SHA256SUMS`。

`v1.11.0`、`v1.12.0`、`v1.13.0` 按当时规则仅发布 Stable。
`v1.14.0` 延续两资产发行，并明确 ROI Beta 维护结束。

## Verification

发布前核对精确 PR head、main 合并提交和 CI；正式 tag 指向已验证的合并提交。
发布完成验证 tag/source、实际归档下载和最终 SHA256SUMS，保留发布验证记录。
README、CHANGELOG 与发布说明须覆盖自上次 Stable 以来的实际发行范围和资产。

产品包版本和 TPlan runtime generation 分别记录。旧 Mission 保留原固定 writer，
新运行时身份、能力及脚本指纹必须一致，不通过覆写 provenance 迁移历史任务。
