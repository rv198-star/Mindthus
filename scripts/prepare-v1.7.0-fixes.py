#!/usr/bin/env python3
from pathlib import Path


def replace_all(path: str, before: str, after: str, expected: int) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(before)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} occurrences of {before!r}, got {count}")
    target.write_text(text.replace(before, after), encoding="utf-8")


# These are current-release assertions, not historical v1.6.0 guards.
replace_all("tests/test_packaging_docs.py", "1.6.0", "1.7.0", 6)
replace_all("tests/test_v1_0_1_usage_log.py", "1.6.0", "1.7.0", 2)

notes = Path("docs/releases/v1.7.0.md")
text = notes.read_text(encoding="utf-8")
before = "closure 判断；普通 implementation defect 不会自动移动 ownership。"
after = "closure 判断；普通 implementation defect 只是 execution repair，不会自动移动 ownership。"
if text.count(before) != 1:
    raise SystemExit("v1.7.0 release note execution-repair sentence changed")
notes.write_text(text.replace(before, after), encoding="utf-8")
