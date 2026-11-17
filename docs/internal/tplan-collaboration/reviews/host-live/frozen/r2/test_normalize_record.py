"""B's full-contract regression, derived from the contract and C's findings.

The first 337 cases rebuild the reviewed R1 input matrix. Additional cases cover
numeric subclasses, Unicode whitespace, non-dict mappings and exact key sets.
Every case checks silence, audited I/O, input retention and the expected outcome.
"""
import ast
from collections import UserDict
import contextlib
import io
import itertools
from pathlib import Path
import sys
from types import MappingProxyType
import unittest

from normalize_record import normalize_record


class IntChild(int):
    pass


class StrChild(str):
    pass


class DictChild(dict):
    pass


FIELDS = ("id", "label", "enabled", "weight")
BASE = {"id": "record-1", "label": "Sample", "enabled": True, "weight": 7}
CASES = []


def add(group, name, value, valid):
    CASES.append((group, name, value, valid))


for enabled in (False, True):
    for weight in range(101):
        add("valid-domain", f"enabled={enabled},weight={weight}", dict(BASE, enabled=enabled, weight=weight), True)
for index, order in enumerate(itertools.permutations(FIELDS)):
    add("valid-order", f"permutation-{index}", {key: BASE[key] for key in order}, True)
for text in (" x ", "\tuser\n", "\u2003中\u2003", "0", "\x00", StrChild(" child ")):
    for field in ("id", "label"):
        add("valid-strings", f"{field}={text!r}", dict(BASE, **{field: text}), True)
add("valid-dict-subclass", "dict-subclass", DictChild(BASE), True)
for value in (None, False, True, 0, 1, 1.5, "", "record", [], [BASE], (), set(), b"bytes"):
    add("invalid-container", repr(value), value, False)
for size in range(4):
    for keys in itertools.combinations(FIELDS, size):
        add("invalid-missing", repr(keys), {key: BASE[key] for key in keys}, False)
for extra in (None, 0, "", "extra"):
    add("invalid-extra", repr(extra), dict(BASE, extra=extra), False)
for field in ("id", "label"):
    for value in ("", " ", "\t\n\r", "\u2003\u3000", None, False, True, 0, 1, 0.5, b"x", ["x"], {"x": 1}, ("x",)):
        add("invalid-" + field, repr(value), dict(BASE, **{field: value}), False)
for value in (None, 0, 1, -1, 2, 0.0, 1.0, "", "false", "true", [], [1], {}, {"x": 1}, (), (1,)):
    add("invalid-enabled", repr(value), dict(BASE, enabled=value), False)
for value in (None, False, True, -100, -1, 101, 1000, 0.0, 1.0, 100.0, float("inf"), float("-inf"), float("nan"), "", "0", "7", [], [7], {}, {"x": 1}, (7,), IntChild(7)):
    add("invalid-weight", repr(value) + ":" + type(value).__name__, dict(BASE, weight=value), False)
BASE_CASE_COUNT = len(CASES)
assert BASE_CASE_COUNT == 337

for field in ("id", "label"):
    for text in ("\u00a0", "\u0085", "\v\f", StrChild(" \t ")):
        add("extra-blank-strings", field + ":" + repr(text), dict(BASE, **{field: text}), False)
    for text in ("\u200b", "\u00a0名字\u00a0", StrChild("  preserved  ")):
        add("extra-valid-strings", field + ":" + repr(text), dict(BASE, **{field: text}), True)
for value in (IntChild(0), IntChild(100), complex(7, 0), bytearray(b"7"), frozenset({7}), range(7), object(), 10**100, -(10**100)):
    add("extra-invalid-weight", type(value).__name__ + ":" + repr(value), dict(BASE, weight=value), False)
for value in (IntChild(1), float("nan"), complex(1, 0), bytearray(b"1"), object()):
    add("extra-invalid-enabled", type(value).__name__, dict(BASE, enabled=value), False)
for value in (UserDict(BASE), MappingProxyType(BASE), iter(BASE)):
    add("extra-nondict-mappings", type(value).__name__, value, False)
for key in (None, 0, ("extra",), b"extra"):
    add("extra-nonstring-keys", repr(key), {**BASE, key: None}, False)
for field in FIELDS:
    replacement = {key: value for key, value in BASE.items() if key != field}
    replacement["wrong"] = BASE[field]
    add("extra-replaced-key", field, replacement, False)
for enabled in (False, True):
    for weight in (0, 100):
        add("extra-dict-subclass-boundaries", f"{enabled}/{weight}", DictChild(BASE, enabled=enabled, weight=weight), True)

_ACTIVE = False
_IO_EVENTS = []


def _audit(event, args):
    if _ACTIVE and (event == "open" or event.startswith(("socket.", "subprocess.", "os.system", "os.spawn", "os.exec", "ctypes."))):
        _IO_EVENTS.append(event)
        raise RuntimeError("I/O attempted during normalize_record: " + event)


sys.addaudithook(_audit)


class ContractTests(unittest.TestCase):
    def check_case(self, case):
        global _ACTIVE
        group, name, value, valid = case
        before = list(value.items()) if isinstance(value, dict) else None
        before_repr = repr(value)
        stdout, stderr = io.StringIO(), io.StringIO()
        io_before = len(_IO_EVENTS)
        result, error = None, None
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                _ACTIVE = True
                result = normalize_record(value)
            except Exception as exc:
                error = exc
            finally:
                _ACTIVE = False
        self.assertEqual(len(_IO_EVENTS), io_before, (group, name, _IO_EVENTS))
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(repr(value), before_repr, "input content changed")
        if before is not None:
            after = list(value.items())
            self.assertEqual([key for key, _ in after], [key for key, _ in before])
            self.assertEqual(len(after), len(before))
            for (_, old), (_, new) in zip(before, after):
                self.assertIs(new, old)
        if valid:
            self.assertIsNone(error, (group, name, error))
            self.assertIs(type(result), dict)
            self.assertIsNot(result, value)
            self.assertEqual(list(result), list(FIELDS))
            for field in FIELDS:
                self.assertIs(result[field], value[field])
        else:
            self.assertIs(type(error), ValueError, (group, name, error, result))

    def test_static_purity(self):
        tree = ast.parse(Path(__file__).with_name("normalize_record.py").read_text())
        self.assertEqual([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))], [])
        calls = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        self.assertLessEqual(calls, {"ValueError", "isinstance", "set", "type", "str.strip"})


def make_test(case):
    def test(self):
        self.check_case(case)
    test.__doc__ = case[0] + ": " + case[1]
    return test


for index, case in enumerate(CASES):
    setattr(ContractTests, f"test_case_{index:03d}_{case[0].replace('-', '_')}", make_test(case))


if __name__ == "__main__":
    unittest.main()
