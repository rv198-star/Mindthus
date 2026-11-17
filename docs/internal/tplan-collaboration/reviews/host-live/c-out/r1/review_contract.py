"""Independent full-contract checks, scoped to frozen r1 and C's output directory."""
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import sys
from collections import Counter

ROOT = Path('/private/tmp/mindthus246-live-host-qtgzbf0z/frozen/r1')
MANIFEST = Path('/private/tmp/mindthus246-live-host-qtgzbf0z/audit/r1-artifact.json')
CONTRACT = Path('/private/tmp/mindthus246-live-host-qtgzbf0z/input/CONTRACT.md')
OUT = Path('/private/tmp/mindthus246-live-host-qtgzbf0z/c-out/r1')
EXPECTED_DIGEST = 'sha256:03bc9a0581d509c7f233d27946d643a291c3d5fef6f6243aea519596b90a91cb'
FIELDS = ('id', 'label', 'enabled', 'weight')
m = json.loads(MANIFEST.read_text())
files = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(m['artifact']['files'])}
aggregate = 'sha256:' + hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
actual_files = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file())
assert files == m['artifact']['files']
assert actual_files == sorted(files)
assert aggregate == m['artifact']['digest'] == EXPECTED_DIGEST
assert (m['delegation'], m['round'], m['contract_version'], m['required_scope']) == ('D1', 1, 'host-normalizer-v1', ['contract://host-normalizer-v1/all'])
spec = importlib.util.spec_from_file_location('c_review_target_r1', ROOT / 'normalize_record.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
normalize = module.normalize_record

class IntChild(int):
    pass
class StrChild(str):
    pass
class DictChild(dict):
    pass

base = {'id': 'record-1', 'label': 'Sample', 'enabled': True, 'weight': 7}
cases = []
def add(group, name, value, valid):
    cases.append((group, name, value, valid))
for enabled in (False, True):
    for weight in range(101):
        add('valid-domain', f'enabled={enabled},weight={weight}', dict(base, enabled=enabled, weight=weight), True)
for i, order in enumerate(itertools.permutations(FIELDS)):
    add('valid-order', f'permutation-{i}', {key: base[key] for key in order}, True)
for text in (' x ', '\tuser\n', '\u2003中\u2003', '0', '\x00', StrChild(' child ')):
    for field in ('id', 'label'):
        add('valid-strings', f'{field}={text!r}', dict(base, **{field: text}), True)
add('valid-dict-subclass', 'dict-subclass', DictChild(base), True)
for value in (None, False, True, 0, 1, 1.5, '', 'record', [], [base], (), set(), b'bytes'):
    add('invalid-container', repr(value), value, False)
for size in range(4):
    for keys in itertools.combinations(FIELDS, size):
        add('invalid-missing', repr(keys), {key: base[key] for key in keys}, False)
for extra in (None, 0, '', 'extra'):
    add('invalid-extra', repr(extra), dict(base, **{'extra': extra}), False)
invalid_strings = ('', ' ', '\t\n\r', '\u2003\u3000', None, False, True, 0, 1, 0.5, b'x', ['x'], {'x': 1}, ('x',))
for field in ('id', 'label'):
    for value in invalid_strings:
        add('invalid-' + field, repr(value), dict(base, **{field: value}), False)
for value in (None, 0, 1, -1, 2, 0.0, 1.0, '', 'false', 'true', [], [1], {}, {'x': 1}, (), (1,)):
    add('invalid-enabled', repr(value), dict(base, enabled=value), False)
for value in (None, False, True, -100, -1, 101, 1000, 0.0, 1.0, 100.0, float('inf'), float('-inf'), float('nan'), '', '0', '7', [], [7], {}, {'x': 1}, (7,), IntChild(7)):
    add('invalid-weight', repr(value) + ':' + type(value).__name__, dict(base, weight=value), False)

active = False
io_events = []
def audit(event, args):
    if active and (event == 'open' or event.startswith(('socket.', 'subprocess.', 'os.system', 'os.spawn', 'os.exec', 'ctypes.'))):
        io_events.append(event)
        raise RuntimeError('forbidden I/O audit event: ' + event)
sys.addaudithook(audit)
results = []
for group, name, value, valid in cases:
    before = copy.deepcopy(value)
    original_items = list(value.items()) if isinstance(value, dict) else None
    captured_out, captured_err = io.StringIO(), io.StringIO()
    result, error = None, None
    with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
        try:
            active = True
            result = normalize(value)
        except Exception as exc:
            error = exc
        finally:
            active = False
    # No NaN equality assumption: unchanged item identities and order also cover nested invalid values.
    if original_items is not None:
        now = list(value.items())
        unchanged = len(now) == len(original_items) and all(k1 == k2 and v1 is v2 for (k1, v1), (k2, v2) in zip(now, original_items))
    else:
        unchanged = value == before
    violations = []
    if not unchanged:
        violations.append('input mutated')
    if captured_out.getvalue() or captured_err.getvalue():
        violations.append('stdout/stderr I/O')
    if valid:
        if error is not None:
            violations.append('valid input rejected: ' + type(error).__name__ + ': ' + str(error))
        elif not isinstance(result, dict):
            violations.append('output is not dict')
        else:
            if result is value:
                violations.append('output is not fresh')
            if list(result) != list(FIELDS):
                violations.append('wrong output key order')
            if any(result[k] is not value[k] for k in FIELDS):
                violations.append('original values not preserved')
    elif error is None:
        violations.append('invalid input accepted: ' + repr(result))
    elif not isinstance(error, ValueError):
        violations.append('wrong exception: ' + type(error).__name__)
    results.append({'group': group, 'name': name, 'input': repr(value), 'expected': 'accept-preserve-fresh-ordered' if valid else 'ValueError', 'actual': type(error).__name__ + ': ' + str(error) if error else repr(result), 'pass': not violations, 'violations': violations})

source = (ROOT / 'normalize_record.py').read_text()
tree = ast.parse(source)
imports = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
call_targets = sorted({ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)})
assert not imports
assert not io_events
assert {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files} == files
summary = {}
for group in sorted({r['group'] for r in results}):
    rows = [r for r in results if r['group'] == group]
    summary[group] = {'total': len(rows), 'pass': sum(r['pass'] for r in rows), 'fail': sum(not r['pass'] for r in rows)}
report = {
 'status': 'FAIL' if any(not r['pass'] for r in results) else 'PASS',
 'delegation': 'D1', 'round': 1, 'contract_version': 'host-normalizer-v1',
 'required_scope': ['contract://host-normalizer-v1/all'], 'artifact_root': str(ROOT),
 'artifact_digest': aggregate, 'file_digests': files,
 'contract_sha256': hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
 'manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
 'integrity': 'PASS: exact file set, every file digest, compact sorted JSON aggregate, unchanged after checks',
 'static_dependency_check': {'imports': imports, 'call_targets': call_targets},
 'runtime_io_events': io_events,
 'total': len(results), 'passed': sum(r['pass'] for r in results), 'failed': sum(not r['pass'] for r in results),
 'groups': summary, 'cases': results,
}
(OUT / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k:v for k,v in report.items() if k != 'cases'}, ensure_ascii=False, indent=2))
for group in summary:
    failed = next((r for r in results if r['group'] == group and not r['pass']), None)
    if failed:
        print('REPRO', json.dumps(failed, ensure_ascii=False))
sys.exit(1 if report['failed'] else 0)
