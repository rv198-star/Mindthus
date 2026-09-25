"""One anonymous text-quality review of all frozen formal A/B/C outputs."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))
PARENT = HERE.parent / 'abc-current-codex-v1' / 'run.py'
spec = importlib.util.spec_from_file_location('formal_review_cli', PARENT)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

from experiments.typed_decision.contracts import canonical, digest, require
from experiments.typed_decision.session import read_record

SOURCE = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-formal-abc-v1')
ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-formal-abc-review-v1')
ORDER = {'HB': {'p': 'A', 'q': 'C', 'r': 'B'},
         'HC': {'p': 'C', 'q': 'B', 'r': 'A'},
         'HD': {'p': 'B', 'q': 'A', 'r': 'C'}}
LABEL = {('HB', 'A'): 'HB-A-native', ('HB', 'B'): 'HB-B-host-I1', ('HB', 'C'): 'HB-C-delegated-host',
         ('HC', 'A'): 'HC-A-native', ('HC', 'B'): 'HC-B-host-I1', ('HC', 'C'): 'HC-C-delegated-host',
         ('HD', 'A'): 'HD-A-native', ('HD', 'B'): 'HD-B-delegated-host', ('HD', 'C'): 'HD-C-delegated-host'}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_bundle() -> dict:
    cases, hashes = {}, {}
    for cid, order in ORDER.items():
        case_file = HERE / 'inputs' / cid / 'cases.json'
        case = json.loads(case_file.read_bytes())['cases'][0]
        hashes[str(case_file.relative_to(REPO))] = sha(case_file)
        answers = {}
        for slot, arm in order.items():
            path = SOURCE / cid / 'codex-calls' / LABEL[(cid, arm)] / 'last-message.txt'
            raw = path.read_text()
            hashes[str(path)] = sha(path)
            answer = json.loads(raw)['text'] if arm == 'B' and cid != 'HD' else raw
            answers[slot] = answer
        cases[cid] = {'task_documents': [{k: row[k] for k in ('kind', 'text')}
                                         for row in case['packet']['documents']],
                      'required': case['acceptance']['required'],
                      'severe_errors': case['acceptance']['severe'],
                      'answers': answers}
    return {'cases': cases, 'source_hashes': hashes}


def schema() -> dict:
    judgement = {'type': 'object', 'additionalProperties': False,
                 'properties': {'usable': {'type': 'boolean'}, 'severe_error': {'type': 'boolean'},
                                'reason': {'type': 'string'}},
                 'required': ['usable', 'severe_error', 'reason']}
    row = {'type': 'object', 'additionalProperties': False,
           'properties': {'p': judgement, 'q': judgement, 'r': judgement,
                          'preferred': {'type': 'string',
                                        'enum': ['p', 'q', 'r', 'tie', 'none']},
                          'preference_reason': {'type': 'string'}},
           'required': ['p', 'q', 'r', 'preferred', 'preference_reason']}
    return {'type': 'object', 'additionalProperties': False,
            'properties': {'HB': row, 'HC': row, 'HD': row},
            'required': ['HB', 'HC', 'HD']}


def prompt(bundle: dict) -> str:
    return ('你是独立文本质量评阅者。逐题阅读原任务、给定事实、预先声明的 required 与 severe_errors，'
            '然后分别评价 p/q/r 三份匿名答复。usable 要求覆盖核心 required 且能实际指导任务；'
            '若触发 severe_errors 则 severe_error=true 且 usable=false。'
            '不得因为长短或方法名称直接给优胜；可以平手。只按事实与文本评阅，不搜索或调用工具。'
            '只返回符合 schema 的 JSON。\n\n'
            + canonical(bundle['cases']).decode() + '\n')


def setup() -> None:
    cli.ROOT = ROOT
    cli.FREEZE = ROOT / 'freeze.json'
    home = cli.home('B')
    home.mkdir(parents=True, exist_ok=True)
    config = home / 'config.toml'
    expected = f'model = "{cli.MODEL}"\n'
    if config.exists():
        require(config.read_text() == expected, 'review_model_changed')
    else:
        config.write_text(expected)
    auth = home / 'auth.json'
    source = Path('/Users/william/.codex/auth.json')
    if not auth.exists():
        auth.symlink_to(source)
    require(auth.resolve() == source.resolve(), 'review_auth_changed')
    skills = home / 'skills'
    if skills.exists():
        require({p.name for p in skills.iterdir()} <= {'.system'}, 'review_skill_leak')


def freeze() -> dict:
    setup()
    bundle = input_bundle()
    ROOT.mkdir(parents=True, exist_ok=True)
    input_path, schema_path, prompt_path = (ROOT / 'review-input.json', ROOT / 'review-schema.json',
                                            ROOT / 'review-prompt.txt')
    payload = {k: v for k, v in bundle.items() if k != 'source_hashes'}
    if input_path.exists():
        require(json.loads(input_path.read_bytes()) == payload, 'review_input_changed')
    else:
        input_path.write_bytes(canonical(payload) + b'\n')
    sch = schema()
    if schema_path.exists():
        require(json.loads(schema_path.read_bytes()) == sch, 'review_schema_changed')
    else:
        schema_path.write_bytes(canonical(sch) + b'\n')
    p = prompt(bundle)
    if prompt_path.exists():
        require(prompt_path.read_text() == p, 'review_prompt_changed')
    else:
        prompt_path.write_text(p)
    return {'schema': 'mindthus.formal-abc-blind-review-freeze.v1',
            'source_commit': __import__('subprocess').check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
            'runner_sha256': sha(Path(__file__)), 'parent_runner_sha256': sha(PARENT),
            'answers_and_cases_sha256': bundle['source_hashes'],
            'input_sha256': sha(input_path), 'schema_sha256': sha(schema_path),
            'prompt_sha256': sha(prompt_path), 'model': cli.MODEL,
            'maximum_calls': 1, 'automatic_retries': 0, 'labels_sha256': digest(ORDER),
            'claim_ceiling': 'AI reviewer of AI-synthetic holdout texts; not ground truth'}


if __name__ == '__main__':
    require(len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run'), 'action')
    f = freeze()
    if sys.argv[1] == 'freeze':
        cli.save(cli.FREEZE, f)
        print(json.dumps({'freeze': digest(f), 'calls': 0}))
    else:
        old = read_record(cli.FREEZE)
        f['source_commit'] = old['source_commit']
        require(old == f, 'review_freeze_changed')
        answer, call = cli.codex_call('formal-abc-blind-quality',
                                      (ROOT / 'review-prompt.txt').read_text(),
                                      arm='B', timeout=120,
                                      schema=ROOT / 'review-schema.json')
        print(json.dumps({'status': call['status'], 'answer': bool(answer),
                          'usage': call['usage'], 'elapsed_seconds': call['elapsed_seconds']}))
