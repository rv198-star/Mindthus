# Release Defaults / 发布默认规则

## Stable 为默认发行

2026-10-03 Owner明确取消每次Stable必须同步发布ROI Beta的要求。
此后Stable发布不再要求同步ROI Beta；默认提供：

- source tag `vX.Y.Z`；
- Stable plugins/skills两份白名单归档；
- 覆盖实际发布归档的 `SHA256SUMS`。

ROI Beta仅在明确需要时单独安排，不因Stable发布自动产生构建、资格验证或发布任务。
本版v1.11.0不发布ROI Beta。既有Beta tag、资产、源码与历史资格记录保留，
不删除、不自动迁移，也不将本次Jev或Stable优化结论外推为Beta无价值。

若未来另行发布Beta，仍保持独立package/marketplace/cache/skill namespace，
通过精确shared-core ref继承Stable；overlay不复制共享实现，发布时核验相应来源与资产。

## Verification

发布完成必须验证Stable tag/source、实际提供的归档下载可用、最终SHA256SUMS校验通过，
并保留release verification记录。README、CHANGELOG和发布说明必须与实际assets一致。

此前版本的Stable/Beta同步记录是历史事实；这次规则调整向前生效，不改写旧记录。
