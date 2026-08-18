#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"marker missing in {path.relative_to(ROOT)}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# The high-frequency entrypoint was already at its 900-word budget. Preserve it byte-for-byte
# and let the existing conditional pressure resource carry the bugfix semantics.
entry_rel = "skills/using-mindthus/SKILL.md"
entry = subprocess.check_output(["git", "show", f"HEAD:{entry_rel}"], cwd=ROOT)
(ROOT / entry_rel).write_bytes(entry)

# The Cognitive Primitive Index has a stable owner/rule mapping contract. Keep the public
# Perspective Pressure row unchanged; the new semantics live in its existing detail resource.
shared = ROOT / "docs/methodologies/shared-primitives.md"
replace_once(
    shared,
    "| Perspective Pressure | `SELA` / `EDSP` | 单一视角过度自洽时，让真正可能获胜的竞争框架出现，再找会改变判断或行动的关键条件；不要停在对称平衡。 |",
    "| Perspective Pressure | `SELA` / `EDSP` | 单一视角过度自洽时，用角色压力或激励检查挑战判断。 |",
)

# Stable package diagnostic version follows the plugin/package patch version. This is separate
# from TPlan's Mission runtime generation, which intentionally stays at 1.5.4.
path = ROOT / "scripts/log-mindthus-runtime.py"
text = path.read_text(encoding="utf-8")
if 'VERSION = "1.7.0"' not in text:
    raise AssertionError("log-mindthus-runtime Stable VERSION marker missing")
path.write_text(text.replace('VERSION = "1.7.0"', 'VERSION = "1.7.1"', 1), encoding="utf-8")

# Product contract should prove progressive disclosure, not duplicate detail in SKILL.md or
# mutate the stable primitive-index mapping.
path = ROOT / "tests/test_bidirectional_steelman_contract.py"
text = path.read_text(encoding="utf-8")
for line in (
    '        self.assertIn("material competing frame remains", using)\n',
    '        self.assertIn("Visible Translation / 可见表达翻译", using)\n',
    '        self.assertIn("ordinary language", using)\n',
):
    if line not in text:
        raise AssertionError(f"expected temporary entry assertion missing: {line.strip()}")
    text = text.replace(line, "", 1)
needle = '        self.assertIn("Pressure Surface Check / 施压面检查", using)\n'
if needle not in text:
    raise AssertionError("Pressure Surface assertion missing")
text = text.replace(
    needle,
    needle
    + '        self.assertIn("pressure is not a route", using)\n'
    + '        self.assertIn("assign its owner", using)\n'
    + '        self.assertIn("expression-pressure-and-gates.md", using)\n',
    1,
)
old_shared_assert = '        self.assertIn("会改变判断或行动的关键条件", shared)\n'
if old_shared_assert not in text:
    raise AssertionError("temporary shared-index assertion missing")
text = text.replace(
    old_shared_assert,
    '        self.assertIn("competitive-frame convergence", shared)\n',
    1,
)
path.write_text(text, encoding="utf-8")

# README: v1.7.1 is the current Stable patch. The supplemental ROI Beta remains the frozen
# v1.7.0 experimental asset and must not be silently relabeled as 1.7.1.
readme = ROOT / "README.md"
text = readme.read_text(encoding="utf-8")
old_intro = '''当前已发布 Stable 是 `v1.7.0`。本版升级 WAE：在第一层 control assignment 之后，
当 delegation 仍可能隐藏会改变结果的语义选择时，可条件性进入 `Ownership Closure`；新增
`Semantic Ownership Leakage` 诊断、`Mechanical Boundary` 停止条件，以及 Evidence 发现
semantic remainder 后重新打开边界的规则。普通 WAE 不增加额外 ceremony，TPlan runtime
边界保持不变。
'''
new_intro = '''当前已发布 Stable 是 `v1.7.1`。这是 1.x Stable 的小型判断质量 bugfix：当真实竞争
框架仍未收敛时，在现有 Pressure Surface 内构造真正可能获胜的竞争解释，再找会改变判断或
行动的关键条件；用户可见答案把内部抽象翻译成具体选择、损失、证据或行动。它不新增方法、
route、judgment owner、mandatory question 或 debate。本版继承 `v1.7.0` 的 WAE Ownership
Closure；TPlan runtime generation 仍保持 `1.5.4`。
'''
if old_intro not in text:
    raise AssertionError("README Stable intro marker missing")
text = text.replace(old_intro, new_intro, 1)
text = text.replace("mindthus-plugins-1.7.0.tar.gz", "mindthus-plugins-1.7.1.tar.gz")
text = text.replace("mindthus-skills-1.7.0.tar.gz", "mindthus-skills-1.7.1.tar.gz")
text = text.replace(
    "releases/download/v1.7.0/mindthus-plugins-1.7.1.tar.gz",
    "releases/download/v1.7.1/mindthus-plugins-1.7.1.tar.gz",
)
text = text.replace(
    "releases/download/v1.7.0/mindthus-skills-1.7.1.tar.gz",
    "releases/download/v1.7.1/mindthus-skills-1.7.1.tar.gz",
)
text = text.replace("也不是 v1.7.0 Stable 的替代品", "也不是 v1.7.1 Stable 的替代品")
readme.write_text(text, encoding="utf-8")

# The v1.7.0 release contract remains historical; only assertions about the CURRENT release
# move to 1.7.1. Historical v1.7.0 notes and ROI Beta assertions stay unchanged.
path = ROOT / "tests/test_release_boundary_contract.py"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "def test_v1_7_0_release_with_supplemental_roi_beta(self):",
    "def test_current_v1_7_1_release_preserves_v1_7_0_roi_beta_history(self):",
    1,
)
for old, new in (
    ('self.assertIn("当前仓库版本：`v1.7.0`", readme)', 'self.assertIn("当前仓库版本：`v1.7.1`", readme)'),
    ('self.assertIn("当前已发布 Stable 是 `v1.7.0`", readme)', 'self.assertIn("当前已发布 Stable 是 `v1.7.1`", readme)'),
    ('self.assertIn("mindthus-plugins-1.7.0.tar.gz", readme)', 'self.assertIn("mindthus-plugins-1.7.1.tar.gz", readme)'),
    ('self.assertIn("mindthus-skills-1.7.0.tar.gz", readme)', 'self.assertIn("mindthus-skills-1.7.1.tar.gz", readme)'),
    ('self.assertIn(\'VERSION = "1.7.0"\', builder)', 'self.assertIn(\'VERSION = "1.7.1"\', builder)'),
    ('self.assertIn(\'VERSION = "1.7.0"\', runtime_logger)', 'self.assertIn(\'VERSION = "1.7.1"\', runtime_logger)'),
):
    if old not in text:
        raise AssertionError(f"release-boundary current assertion missing: {old}")
    text = text.replace(old, new, 1)
needle = '        self.assertIn("## v1.7.0", changelog)\n'
if needle not in text:
    raise AssertionError("historical v1.7.0 changelog assertion missing")
text = text.replace(
    needle,
    '        self.assertIn("## v1.7.1", changelog)\n' + needle,
    1,
)
path.write_text(text, encoding="utf-8")

# This legacy usage-log test checks that the feature remains in the CURRENT package. Update
# only its moving current-version assertions; its v1.0.1 historical surface stays intact.
path = ROOT / "tests/test_v1_0_1_usage_log.py"
text = path.read_text(encoding="utf-8")
old = '            "当前仓库版本：`v1.7.0`",\n'
if old not in text:
    raise AssertionError("usage-log current README version assertion missing")
text = text.replace(old, '            "当前仓库版本：`v1.7.1`",\n', 1)
old = '            self.assertEqual(plugin["version"], "1.7.0")\n'
if old not in text:
    raise AssertionError("usage-log current plugin version assertion missing")
text = text.replace(old, '            self.assertEqual(plugin["version"], "1.7.1")\n', 1)
path.write_text(text, encoding="utf-8")

print("normalized v1.7.1 progressive-disclosure and release boundaries")
