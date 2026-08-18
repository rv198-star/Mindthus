# Release Defaults / 发布默认规则

## Stable + ROI Beta

Mindthus Stable release 默认同步发布同版本 ROI Beta supplemental experimental asset。
该默认规则适用于 Stable 的 patch、minor 和 major 发版。

- Stable `vX.Y.Z` -> source tag `vX.Y.Z` + Stable plugins/skills assets；
- 默认同时 -> ROI Beta source tag `vX.Y.Z-roi-beta` + `mindthus-beta-X.Y.Z-roi-beta.tar.gz`；
- Stable 与 ROI Beta 可以共享同一个 GitHub Release；`SHA256SUMS` 覆盖该 Release 的三份归档；
- ROI Beta 保持独立 package / marketplace / cache / skill namespace，不替代 Stable，不自动迁移；
- ROI overlay 只能包含已经资格验证的 runtime delta；新 Stable 能力默认属于 shared-product-core，
  Beta 通过精确 shared-core ref 继承，不能在 overlay 中复制实现。

### Exception rule

只有当某个版本在**发布前**明确记录“本版不发布 ROI Beta”及原因时，才允许省略对应 Beta。
没有明确例外，就按默认规则发布。发布说明、CHANGELOG 和 README 必须与实际 assets 一致。

### Verification

发布完成必须验证 Stable tag/source、ROI Beta source tag、所有归档下载可用、最终
`SHA256SUMS` 校验通过，并保留 release verification 记录。
