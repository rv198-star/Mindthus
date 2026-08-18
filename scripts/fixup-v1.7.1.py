#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

# The high-frequency entrypoint was already at its 900-word budget. Preserve it byte-for-byte
# and let the existing conditional pressure resource carry the bugfix semantics.
entry_rel = "skills/using-mindthus/SKILL.md"
entry = subprocess.check_output(["git", "show", f"HEAD:{entry_rel}"], cwd=ROOT)
(ROOT / entry_rel).write_bytes(entry)

# Stable package diagnostic version follows the plugin/package patch version. This is separate
# from TPlan's Mission runtime generation, which intentionally stays at 1.5.4.
path = ROOT / "scripts/log-mindthus-runtime.py"
text = path.read_text(encoding="utf-8")
if 'VERSION = "1.7.0"' not in text:
    raise AssertionError("log-mindthus-runtime Stable VERSION marker missing")
path.write_text(text.replace('VERSION = "1.7.0"', 'VERSION = "1.7.1"', 1), encoding="utf-8")

# Product contract should prove progressive disclosure, not duplicate the detail in SKILL.md.
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
path.write_text(text, encoding="utf-8")

print("normalized v1.7.1 progressive-disclosure boundary")
