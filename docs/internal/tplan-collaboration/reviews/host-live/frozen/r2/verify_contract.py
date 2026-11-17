"""Read-only self-review; prints JSON for the D2/I2/R2 artifact."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import test_normalize_record as checks


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
prior = json.loads((ROOT / "c-out/r1/results.json").read_text())
rebuilt = [
    (group, name, repr(value), "accept-preserve-fresh-ordered" if valid else "ValueError")
    for group, name, value, valid in checks.CASES[:checks.BASE_CASE_COUNT]
]
recorded = [(case["group"], case["name"], case["input"], case["expected"]) for case in prior["cases"]]
assert rebuilt == recorded
contract_sha = hashlib.sha256((ROOT / "input/CONTRACT.md").read_bytes()).hexdigest()
assert contract_sha == prior["contract_sha256"]
log = (HERE / "test-results.txt").read_text()
match = re.search(r"^Ran (\d+) tests in [^\n]+", log, re.M)
assert match and int(match[1]) == len(checks.CASES) + 1
assert re.search(r"^OK$", log, re.M)
for path in sorted(HERE.glob("*.py")):
    compile(path.read_text(), str(path), "exec")
tree = ast.parse((HERE / "normalize_record.py").read_text())
imports = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
calls = sorted({ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)})
assert not imports
assert set(calls) <= {"ValueError", "isinstance", "set", "type", "str.strip"}
report = {
    "delegation": "D2", "intent": "I2", "round": 2,
    "contract_version": "host-normalizer-v1", "contract_sha256": contract_sha,
    "status": "B_SELF_CHECK_PASS", "independent_C_review": "pending",
    "unittest_summary": match[0], "tests_run": int(match[1]), "failed": 0, "skipped": 0,
    "behavior_cases": len(checks.CASES), "rebuilt_C_cases": len(rebuilt),
    "extra_behavior_cases": len(checks.CASES) - len(rebuilt), "static_purity_checks": 1,
    "prior_C_passed": prior["passed"], "prior_C_failed": prior["failed"],
    "original_C_matrix_exact_match": True,
    "groups": dict(sorted(Counter(case[0] for case in checks.CASES).items())),
    "static_imports": imports, "static_call_targets": calls,
    "syntax_compile": "PASS for all three Python files, with no bytecode output",
    "runtime_purity": "Every behavior test asserts no audited file/network/process I/O and empty stdout/stderr",
    "preservation": "Every behavior test checks original dict keys, order and value identities; valid output is a fresh ordered built-in dict",
    "repair_mapping": {
        "F1": "Exact bool validation accepts False without a truthiness gate",
        "F2": "Exact int and inclusive range validation accepts 0 and 100",
        "F3": "Exact four-key set rejects extras, missing keys and same-length key replacement",
        "F4": "String validation uses strip only for emptiness and retains original objects",
        "F5": "type(enabled) is bool rejects numbers, strings and containers",
        "F6": "type(weight) is int and 0 <= weight <= 100 rejects bool, int subclasses and other types"
    },
    "known_residual_issues": []
}
print(json.dumps(report, ensure_ascii=False, indent=2))
