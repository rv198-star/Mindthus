"""Frozen construction of nine new A-F task snapshots, without expected answers."""
from __future__ import annotations

import json
from pathlib import Path

from experiments.typed_decision import relationship_assessment as rel

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'holdout-candidate-source-v1' / 'evidence-20260925' / 'records' / 'codex-calls' / 'task-candidates' / 'last-message.txt'
OWNER = 'current-codex:paired-local-v3'


def doc(ident: str, kind: str, text: str) -> dict:
    return {'id': ident, 'revision': '1', 'kind': kind, 'text': text}


def resolution(value: str, refs: list[dict]) -> dict:
    return {'value': value, 'owner_ref': OWNER, 'revision': '1', 'refs': refs}


def issue(ident: str, source: dict, methods: list[str], mode: str,
          attention: bool) -> dict:
    ref = rel.quote(source)
    return {'id': ident, 'request_ref': ref, 'candidates': methods,
            'handling': resolution(mode, [ref]), 'assessability': None,
            'attention': attention}


def relationship(case_id: str, docs: list[dict], kind: str,
                 actor: str, obj: str, time: str, goal: str, scope: str,
                 claim_text: str) -> dict:
    user, source, candidate = docs
    ur, sr, cr = rel.quote(user), rel.quote(source), rel.quote(candidate)
    fields = {key: {'text': value, 'origin': 'explicit', 'refs': [ur]}
              for key, value in zip(rel.FRAME_FIELDS,
                                    (actor, obj, time, goal, scope))}
    return {'schema': 'relationship-input.v1',
            'episode_id': 'paired-local-v3-' + case_id,
            'turn_id': '1', 'revision': '1', 'stage': 'S1',
            'documents': docs,
            'proposal': {'frames': [{'id': 'F0', 'kind': kind, **fields}],
                         'candidate': {'ref': cr, 'thesis_refs': [cr],
                                       'controller_refs': [cr],
                                       'discriminator_refs': [cr]},
                         'scope_correction_refs': [ur] if case_id == 'E1' else [],
                         'claims': [{'id': 'K0', 'text': claim_text,
                                     'origin': 'source_observation', 'refs': [sr]}],
                         'edges': [], 'user_premise': None, 'competitions': []},
            'authority': {'owner_ref': OWNER, 'risk': 'low', 'mode': 'read_only',
                          'known_obligations': []},
            'activation': {'enabled': True, 'source_refs': [ur],
                           'reason': '新本地开发批次：检查已写定的候选是否需要具名纠偏'}}


RELATION_CASES = {
    'E1': ('definition', '博物馆导览页编辑', '音频导览观察的说明', '发布前',
           '保留有根据的范围并修订无证据推论', '只用所给三周记录',
           '没有收集喜好评价或未使用导览者的时长',
           '使用导览的人在展厅停留更久，因此他们都更喜欢这次展览。'),
    'E2': ('definition', '手作店店员', '固定订单备注整理指令', '当前用途',
           '判断是否需要更多轮和角色', '只处理一行交接条目',
           '七周抽查均可整理且工具不联系顾客或改订单',
           '即使只要固定格式，也必须增设多轮判断和多个角色，否则无法可靠整理订单。'),
    'F1': ('decision', '鲜切店店主', '已启用周转箱的交接补救', '本周',
           '在不换箱型下消除记录混乱', '本季不能更换箱型',
           '可调整登记、贴临时标识并盘点',
           '直接换一批带编号的新箱子，本周就能解决交接混乱。'),
    'F2': ('decision', '果蔬配送站', '两种周转容器的购前选择', '采购决定前',
           '比较利弊并补齐条件', '尚未确认损耗、回收周期和仓储上限',
           '未确认线路损耗、回收周期、仓储上限，也未签采购约定',
           '无论损耗、回收周期和仓储条件怎样，都应立即采购带编号可折叠筐。'),
}


def packets() -> dict[str, dict]:
    source = {x['id']: x for x in json.loads(SOURCE.read_text())['cases']}
    out = {}
    for case_id, row in source.items():
        if case_id == 'D1':
            user = row['user_request']
            cut = user.index('再建议')
            u1 = doc('U1', 'user', user[:cut].strip('，。 '))
            u2 = doc('U2', 'user', user[cut:].strip('，。 '))
            s = doc('S', 'source', row['given_facts'])
            docs = [u1, u2, s]
            issues = [issue('I1', u1, ['edsp'], 'judge', True),
                      issue('I2', u2, ['sra'], 'judge', True)]
            deps = [{'id': 'P1', 'producer': 'I1', 'consumer': 'I2',
                     'artifact': '已澄清的可行做法及试行条件', 'condition': None,
                     'refs': [rel.quote(u1), rel.quote(u2)]}]
            relation_packet = None
        elif case_id in RELATION_CASES:
            kind, actor, obj, time, goal, scope, claim, candidate = RELATION_CASES[case_id]
            docs = [doc('U', 'user', row['user_request']),
                    doc('S', 'source', row['given_facts']),
                    doc('C', 'candidate', candidate)]
            issues = [issue('I1', docs[0], [], 'direct_execute', False)]
            deps = []
            relation_packet = relationship(case_id, docs, kind, actor, obj,
                                            time, goal, scope, claim)
        else:
            docs = [doc('U', 'user', row['user_request']),
                    doc('S', 'source', row['given_facts'])]
            methods = {'A1': [], 'A2': [], 'B1': ['wae'],
                       'C1': ['sela', 'mpg']}[case_id]
            mode = 'judge' if methods else 'direct_execute'
            issues = [issue('I1', docs[0], methods, mode, bool(methods))]
            deps = []
            relation_packet = None
        out[case_id] = {'schema': 'mindthus.route-control-input.v1',
                        'episode_id': 'paired-local-v3-' + case_id,
                        'turn_id': '1', 'revision': '1', 'documents': docs,
                        'authority': {'owner_ref': OWNER, 'risk': 'low',
                                      'mode': 'read_only', 'known_obligations': []},
                        'issues': issues, 'dependencies': deps,
                        'relationship': relation_packet,
                        'task_budget': {'max_calls': 2 if case_id == 'D1' else 1,
                                        'max_seconds': 90 if case_id == 'D1' else 45}}
    return out
