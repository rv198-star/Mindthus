"""Offline design checks only. Does not implement the router or invoke a model.

Validates DecisionSpec compatibility, source bindings, branch inventory, family
coverage and the forward dependency specification. Semantic examples stay unrun.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))
from experiments.typed_decision.contracts import DecisionSpec, canonical


def load(name):
    return json.loads((HERE / name).read_text(encoding='utf8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def topological(graph):
    nodes = {n['id'] for n in graph['nodes']}
    require(len(nodes) == len(graph['nodes']), 'duplicate graph node')
    incoming = {n: set() for n in nodes}
    for edge in graph['edges']:
        require(edge['from'] in nodes and edge['to'] in nodes and edge['condition'], 'invalid edge')
        incoming[edge['to']].add(edge['from'])
    order = []
    while incoming:
        ready = sorted(k for k, v in incoming.items() if not v)
        require(ready, 'cyclic graph')
        for k in ready:
            order.append(k)
            del incoming[k]
        for v in incoming.values():
            v.difference_update(ready)
    return order


def validate_questions(payload, acceptance, sources):
    questions = payload['questions']
    ids = {q['id'] for q in questions}
    cases = {c['id'] for c in acceptance['cases']}
    require(len(questions) == len(ids) == 19, 'question inventory')
    require({q['wire_type'] for q in questions} == {'choice', 'noul', 'score'}, 'all three types required')
    required = {'id', 'title', 'group', 'kind', 'wire_type', 'version', 'parameters',
                'question', 'criteria', 'required_context', 'activation', 'consume_prerequisites',
                'consume', 'non_ok', 'source_refs', 'acceptance_refs'}
    specs = []
    for q in questions:
        require(set(q) == required, 'question shape:' + q['id'])
        require(q['parameters'] and len(set(q['parameters'])) == len(q['parameters']), 'binding parameters')
        require(q['activation'] and q['non_ok'] and q['source_refs'], 'missing purpose/source')
        require(all(p in sources['sources'] for p in q['source_refs']), 'unknown source')
        require(q['acceptance_refs'] and set(q['acceptance_refs']) <= cases, 'missing question acceptance')
        mapping = {'select': 'choice', 'rate': 'score', 'assess_proposition': 'noul'}
        require(mapping[q['kind']] == q['wire_type'], 'wire type mismatch')
        if q['kind'] == 'select':
            require(set(q['criteria']) == set(q['consume']), 'choice branch missing:' + q['id'])
        if q['kind'] == 'assess_proposition':
            require(set(q['consume']) == {'positive', 'negative', 'unresolved'}, 'Noul bands missing')
        if q['kind'] == 'rate':
            require(set(q['consume']) == {'assessable', 'not_assessable', 'conflict_with_authority_or_dependency'},
                    'Score consumption missing')
        require(all(isinstance(v, str) and v for v in q['consume'].values()), 'empty consumption')
        binding = {p: 'Offline shape binding; not a task observation: ' + p for p in q['parameters']}
        spec = DecisionSpec(q['id'] + '.shape', q['question'] + '\nBinding: ' + canonical(binding).decode(),
                            q['criteria'], tuple(q['required_context']), kind=q['kind'],
                            version=q['version'], policy_ref=payload['policy_ref'])
        spec.validate()
        specs.append(spec)
    for c in acceptance['cases']:
        require(c['question_refs'] and set(c['question_refs']) <= ids, 'unknown case question')
        require(c['execution_status'] == 'not_run', 'design specimens presented as measured')
        require(c['task'] and c['given_material'] and c['contrast'] and c['required_properties']
                and c['forbidden_outcomes'], 'incomplete acceptance control')
    require(len(cases) == len(acceptance['cases']) == 24, 'case inventory')
    return specs


def render_catalog(payload):
    rows = ['# 主线问题逐题合同 v0.1', '',
            '由 questions.json 生成；本文件是设计候选，不是已部署问题或模型成绩。', '',
            '每一题实例化时附加可读对象、当前范围及来源 Binding；ID 不承担题义。方法 M02 还附加 method-bindings.json 的八种正式来源解释。', '']
    for q in payload['questions']:
        rows += ['## ' + q['id'] + ' · ' + q['title'] + ' · ' + q['wire_type'], '', q['question'], '',
                 '**参数：** ' + ' / '.join(q['parameters']), '', '**激活：** ' + q['activation'], '',
                 '**消费前提：** ' + ('；'.join(q['consume_prerequisites']) or '机械身份/权限前检后，按激活条件。'), '',
                 '| 答案/等级 | 含义 |', '|---|---|']
        criteria = q['criteria'].items() if isinstance(q['criteria'], dict) else enumerate(q['criteria'])
        rows += ['| ' + str(k) + ' | ' + v.replace('|', '/') + ' |' for k, v in criteria]
        rows += ['', '| 消费条件 | 实际后果 |', '|---|---|']
        rows += ['| ' + k + ' | ' + v.replace('|', '/') + ' |' for k, v in q['consume'].items()]
        rows += ['', '**失败/未知：** ' + q['non_ok'], '',
                 '**验收条目：** ' + ', '.join(q['acceptance_refs']), '',
                 '**正式来源：** ' + '；'.join('`' + x + '`' for x in q['source_refs']), '']
    return '\n'.join(rows).rstrip() + '\n'


def render_mermaid(graph):
    lines = ['flowchart TB']
    for n in graph['nodes']:
        label = n['label'] + ('<br/>' + ' '.join(n['question_refs']) if n['question_refs'] else '')
        lines.append('  ' + n['id'] + '["' + label + '"]')
    for e in graph['edges']:
        lines.append('  ' + e['from'] + ' -->|' + e['condition'] + '| ' + e['to'])
    return '\n'.join(lines) + '\n'


def run(generate=False):
    payload, acceptance, sources = load('questions.json'), load('acceptance.json'), load('source-index.json')
    policy, graph, iteration, methods = load('policy.json'), load('dag.json'), load('iteration-policy.json'), load('method-bindings.json')
    for path, expected in sources['sources'].items():
        file = (REPO / path).resolve()
        require(file.is_relative_to(REPO), 'source path outside repo')
        require(hashlib.sha256(file.read_bytes()).hexdigest() == expected, 'source changed:' + path)
    specs = validate_questions(payload, acceptance, sources)
    method_ids = {m['method'] for m in methods['methods']}
    require(method_ids == {'3l5s','edsp','sela','mpg','sra','wae','tvg','tplan'}, 'eight method coverage')
    q02 = next(q for q in payload['questions'] if q['id'] == 'M02')
    for m in methods['methods']:
        require(m['source_sha256'] == sources['sources'][m['source_path']], 'method source changed')
        require(m['positive_example'] and m['negative_example'] and m['method_binding_question'], 'method examples')
        spec = DecisionSpec('M02.' + m['method'], q02['question'] + '\n' + m['method_binding_question'],
                            q02['criteria'], tuple(q02['required_context']), kind=q02['kind'],
                            version='0.1', policy_ref=payload['policy_ref'])
        spec.validate()
        specs.append(spec)
    order = topological(graph)
    qids = {q['id'] for q in payload['questions']}
    require({q for n in graph['nodes'] for q in n['question_refs']} == qids, 'DAG question coverage')
    require(all(q in qids for n in graph['nodes'] for q in n['question_refs']), 'unknown DAG question')
    require(policy['limits']['plugin_requests_total'] == sum(policy['limits'][k] for k in
        ['fast_requests_per_episode','organizers','arbitrations','named_revisions']), 'request units conflict')
    require(policy['limits']['paid_calls_authorized_this_design'] == 0, 'unexpected paid admission')
    require(iteration['cycle_limits']['semantic_candidates'] == 3, 'iteration ceiling')
    require(iteration['partition_rules']['LOCKED'] and iteration['reuse_rules']['unknown_intent'], 'evaluation isolation')
    require(policy['choice_policy']['automatic_adoption'] is False, 'unqualified automatic adoption')
    # Negative mutations prove checker boundaries, not behavior of an unimplemented router.
    rejected = []
    def expect_rejection(name, fn):
        try:
            fn()
        except (ValueError, KeyError, TypeError):
            rejected.append(name)
            return
        raise AssertionError('mutation not rejected: ' + name)
    broken = deepcopy(payload); broken['questions'][0]['consume'].pop('faithful')
    expect_rejection('choice_branch_removed', lambda: validate_questions(broken, acceptance, sources))
    broken2 = deepcopy(payload); broken2['questions'][0]['acceptance_refs'] = ['A99']
    expect_rejection('unknown_acceptance', lambda: validate_questions(broken2, acceptance, sources))
    broken3 = deepcopy(payload); broken3['questions'][0]['source_refs'] = ['invented']
    expect_rejection('invented_canonical_source', lambda: validate_questions(broken3, acceptance, sources))
    broken4 = deepcopy(payload); broken4['questions'][-1]['wire_type'] = 'score'
    expect_rejection('wrong_wire_type', lambda: validate_questions(broken4, acceptance, sources))
    broken5 = deepcopy(payload); next(q for q in broken5['questions'] if q['id']=='S02')['criteria'] = ['only_one_level']
    expect_rejection('invalid_score_levels', lambda: validate_questions(broken5, acceptance, sources))
    broken6 = deepcopy(payload); next(q for q in broken6['questions'] if q['id']=='M02')['criteria'] = {'maybe':'undefined'}
    expect_rejection('invalid_noul_semantics', lambda: validate_questions(broken6, acceptance, sources))
    broken7 = deepcopy(graph); broken7['edges'].append({'from':'answer','to':'input','condition':'retry_forever'})
    expect_rejection('infinite_back_edge', lambda: topological(broken7))
    broken8 = deepcopy(acceptance); broken8['cases'][0]['execution_status'] = 'pass'
    expect_rejection('unrun_fixture_claimed_pass', lambda: validate_questions(payload, broken8, sources))
    catalog, diagram = render_catalog(payload), render_mermaid(graph)
    generated = {'question-catalog.md': catalog, 'dag.mmd': diagram}
    for name, text in generated.items():
        if generate:
            (HERE/name).write_text(text, encoding='utf8')
        else:
            require((HERE/name).read_text(encoding='utf8') == text, 'generated view drift:' + name)
    return {'status':'PASS_DESIGN_STRUCTURE_ONLY', 'runtime_implemented':False,
            'semantic_accuracy_tested':False, 'independent_audit_performed':False,
            'new_model_calls':0, 'question_templates':len(payload['questions']),
            'type_counts':{t:sum(q['wire_type']==t for q in payload['questions']) for t in ['choice','noul','score']},
            'DecisionSpec_compilations':len(specs), 'method_bindings':len(method_ids),
            'source_files_verified':len(sources['sources']), 'acceptance_specimens':len(acceptance['cases']),
            'acceptance_specimens_executed':0, 'dag_nodes':len(graph['nodes']),
            'dag_edges':len(graph['edges']), 'topological_order':order,
            'mutation_controls_rejected':rejected, 'default_paths_unchanged':True,
            'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(HERE.iterdir())
                               if p.is_file() and p.name != 'verification.json'}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', action='store_true', help='Generate catalog and Mermaid source from JSON.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run(args.generate)
    if args.output:
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('artifact_sha256','topological_order')},ensure_ascii=False))
