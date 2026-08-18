#!/usr/bin/env python3
from pathlib import Path
import subprocess


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


# README: current Stable + matching ROI Beta, with the default release rule explicit.
p = Path("README.md")
text = read(str(p))
anchor = "优先安装插件包；插件不可用或需要 portable skills 时，再安装 skills 包。\n"
rule = (
    "优先安装插件包；插件不可用或需要 portable skills 时，再安装 skills 包。\n\n"
    "**发布默认规则**：Stable release 默认同步提供同版本 ROI Beta supplemental asset；"
    "只有该版本在发布前明确声明例外时才不发布 ROI Beta。\n"
)
assert text.count(anchor) == 1
text = text.replace(anchor, rule, 1)
old = """`v1.7.0` Release 同时提供 Stable plugins、Stable skills 与补充发布的 ROI Beta
experimental asset。ROI Beta 从冻结的 `v1.7.0` Stable core 重新组装，因此继承 WAE
Ownership Closure，以及 Judgment Trace、Case Export、case-prep、Test Lifecycle 与现有
TPlan 能力；运行时差异仍只允许经资格验证的 ROI.2 薄入口、一条 3L5S Anti-Spiral 合同和
Beta identity / namespace / diagnostic 坐标。TPlan runtime generation 仍保持 `1.5.4`。
"""
new = """`v1.7.1` Release 同时提供 Stable plugins、Stable skills 与补充发布的 ROI Beta
experimental asset。ROI Beta 从冻结的 `v1.7.1` Stable core 重新组装，因此继承本版
Competitive-frame convergence / Visible Translation 修复、WAE Ownership Closure、Judgment
Trace、Case Export、case-prep、Test Lifecycle 与现有 TPlan 能力；运行时差异仍只允许经资格
验证的 ROI.2 薄入口、一条 3L5S Anti-Spiral 合同和 Beta identity / namespace / diagnostic
坐标。TPlan runtime generation 仍保持 `1.5.4`。
"""
assert old in text
text = text.replace(old, new, 1)
text = text.replace(
    "`mindthus-beta-1.7.0-roi-beta.tar.gz`；它使用独立的 Codex plugin / marketplace 包与",
    "`mindthus-beta-1.7.1-roi-beta.tar.gz`；它使用独立的 Codex plugin / marketplace 包与",
    1,
)
old = """只在高能力 Codex / GPT-Sol 上复查低开销唤起实验时使用。这个
`v1.7.0-roi-beta` 包从冻结的 `v1.7.0` Stable core 重新组装，继承 WAE Ownership
Closure、Judgment Trace、Case Export、case-prep、Test Lifecycle 与现有 TPlan 能力；它只
替换经资格验证的 `using-mindthus` 薄入口和一条 3L5S Anti-Spiral 句子。Stable 与 ROI Beta
使用不同的 package、marketplace、cache 与 skill namespace，可以独立安装或移除：
"""
new = """只在高能力 Codex / GPT-Sol 上复查低开销唤起实验时使用。这个
`v1.7.1-roi-beta` 包从冻结的 `v1.7.1` Stable core 重新组装，继承本版 competing-frame /
visible-translation 修复、WAE Ownership Closure、Judgment Trace、Case Export、case-prep、
Test Lifecycle 与现有 TPlan 能力；它只替换经资格验证的 `using-mindthus` 薄入口和一条
3L5S Anti-Spiral 句子。Stable 与 ROI Beta 使用不同的 package、marketplace、cache 与
skill namespace，可以独立安装或移除：
"""
assert old in text
text = text.replace(old, new, 1)
text = text.replace("mindthus-beta-1.7.0-roi-beta.tar.gz", "mindthus-beta-1.7.1-roi-beta.tar.gz")
text = text.replace(
    "releases/download/v1.7.0/mindthus-beta-1.7.1-roi-beta.tar.gz",
    "releases/download/v1.7.1/mindthus-beta-1.7.1-roi-beta.tar.gz",
)
write(str(p), text)

# Stable release note now describes the default supplemental asset.
p = Path("docs/releases/v1.7.1.md")
text = read(str(p))
old = """发布资产：

- `mindthus-plugins-1.7.1.tar.gz`
- `mindthus-skills-1.7.1.tar.gz`
- `SHA256SUMS`

本 patch 只发布 Stable 资产；ROI Beta 如需同步将在独立补充发布中处理。"""
new = """发布资产：

- `mindthus-plugins-1.7.1.tar.gz`
- `mindthus-skills-1.7.1.tar.gz`
- `mindthus-beta-1.7.1-roi-beta.tar.gz`
- `SHA256SUMS`

本 patch 按 Stable release 默认规则同步提供 ROI Beta supplemental experimental asset；
其 shared core 固定为本版 Stable，ROI.2 overlay 继续保持独立 identity / namespace。
详细边界见 [v1.7.1 ROI Beta 发布说明](v1.7.1-roi-beta.md)。"""
assert old in text
write(str(p), text.replace(old, new, 1))

# Copy the exact Beta source release note into main docs.
beta_note = subprocess.check_output(
    ["git", "show", "origin/release/v1.7.1-roi-beta:docs/releases/v1.7.1-roi-beta.md"],
    text=True,
)
write("docs/releases/v1.7.1-roi-beta.md", beta_note)

# Changelog: correct the asset list and record the supplemental Beta explicitly.
p = Path("CHANGELOG.md")
text = read(str(p))
old = """### 验证与发布资产

- compileall、Test Lifecycle、完整 unittest、Stable plugins/skills build 均通过后发布。
- GitHub Release 提供 `mindthus-plugins-1.7.1.tar.gz`、`mindthus-skills-1.7.1.tar.gz` 和
  `SHA256SUMS`。
- 本 patch 不包含新的 ROI Beta 资产。
"""
new = """### 补充发布包：1.7.1 ROI Beta（GPT/Sol）

- Stable release 默认同步提供同版本 ROI Beta，除非该版本发布前显式声明例外；v1.7.1 未声明例外。
- ROI Beta 从冻结的 `v1.7.1` Stable core 重新组装，因此继承 competing-frame convergence、
  Visible Translation Boundary、WAE Ownership Closure 与其余 shared-product-core 能力。
- runtime delta 继续限制为资格验证过的 ROI.2 `using-mindthus` 薄入口、单句 3L5S
  Anti-Spiral correction、Beta identity / namespace 与 runtime diagnostic 坐标。
- 源码 tag：`v1.7.1-roi-beta`；资产：`mindthus-beta-1.7.1-roi-beta.tar.gz`；不自动迁移，
  不自动发布 marketplace。

### 验证与发布资产

- compileall、Test Lifecycle、完整 unittest、Stable plugins/skills build 均通过后发布。
- GitHub Release 提供 `mindthus-plugins-1.7.1.tar.gz`、`mindthus-skills-1.7.1.tar.gz`、
  `mindthus-beta-1.7.1-roi-beta.tar.gz` 和覆盖三份归档的 `SHA256SUMS`。
"""
assert old in text
write(str(p), text.replace(old, new, 1))

policy = """# Release Defaults / 发布默认规则

## Stable + ROI Beta

Mindthus Stable release 默认同步发布同版本 ROI Beta supplemental experimental asset。

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
"""
write("docs/internal/release-defaults.md", policy)

# Guard the default release rule in the current release contract.
p = Path("tests/test_release_boundary_contract.py")
text = read(str(p))
text = text.replace(
    'self.assertIn("mindthus-beta-1.7.0-roi-beta.tar.gz", readme)',
    'self.assertIn("mindthus-beta-1.7.1-roi-beta.tar.gz", readme)',
    1,
)
marker = "    def test_v1_4_6_release_surface_is_preserved(self):\n"
test = '''    def test_release_defaults_publish_roi_beta_unless_explicitly_exempted(self):
        policy = (REPO / "docs" / "internal" / "release-defaults.md").read_text(encoding="utf-8")
        release = (REPO / "docs" / "releases" / "v1.7.1.md").read_text(encoding="utf-8")
        beta = (REPO / "docs" / "releases" / "v1.7.1-roi-beta.md").read_text(encoding="utf-8")
        changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        for phrase in (
            "Stable release 默认同步发布同版本 ROI Beta",
            "只有当某个版本在**发布前**明确记录",
            "没有明确例外，就按默认规则发布",
        ):
            self.assertIn(phrase, policy)
        self.assertIn("mindthus-beta-1.7.1-roi-beta.tar.gz", release)
        self.assertIn("v1.7.1-roi-beta", beta)
        self.assertIn("补充发布包：1.7.1 ROI Beta", changelog)
        self.assertIn("覆盖三份归档的 `SHA256SUMS`", changelog)

'''
assert marker in text
text = text.replace(marker, test + marker, 1)
write(str(p), text)

print("synced v1.7.1 ROI Beta release docs and default policy")
