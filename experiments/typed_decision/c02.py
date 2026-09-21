"""One bounded TVG text module; local decisions never own the TVG exit."""
from __future__ import annotations

from .contracts import ContractError, DecisionSpec, digest, require
from .session import RecoveryRequired, read_record, write_once

GRAPH = {'id': 'mindthus.c02', 'version': '1', 'dependencies': {
    'L0': [], 'D0': ['L0'], 'J1': ['D0'], 'J2': ['D0'],
    'M1': ['J1', 'J2'], 'J3': ['M1'], 'L1': ['J3'],
    'J4': ['L1'], 'J5': ['L1'], 'exit_owner': ['J4', 'J5']}}
READS = ('artifact', 'target', 'evidence', 'veto_constraints', 'tvg_contract')
ACTIONS = frozenset({'make_actionable', 'explain_tradeoff', 'compact_preserve',
                     'leave_unchanged', 'abstain'})
REWRITES = ACTIONS - {'leave_unchanged', 'abstain'}


def rewrite_directory(root, run_id):
    require(isinstance(run_id, str) and len(run_id) == 64 and set(run_id) <= set('0123456789abcdef'),
            'invalid parent run id')
    return root / 'rewrites' / run_id


def input_problem(data):
    if not isinstance(data, dict):
        return 'input_not_object'
    for name in ('artifact', 'tvg_contract', 'source_ref'):
        if not isinstance(data.get(name), str) or not data[name].strip():
            return 'missing_' + name
    target = data.get('target')
    if not isinstance(target, dict) or not all(isinstance(target.get(k), str) and target[k].strip()
            for k in ('source_ref', 'purpose', 'standard')):
        return 'missing_independent_target'
    if target['source_ref'] == data['source_ref']:
        return 'target_is_artifact'
    if not isinstance(data.get('evidence'), list) or not all(isinstance(x, dict)
            and all(isinstance(x.get(k), str) and x[k].strip() for k in ('source_ref', 'text'))
            for x in data['evidence']):
        return 'invalid_evidence'
    if not isinstance(data.get('veto_constraints'), list) or not data['veto_constraints'] or not all(
            isinstance(x, str) and x.strip() for x in data['veto_constraints']):
        return 'missing_veto_constraints'
    if data.get('freshness') != 'current':
        return 'stale_context'
    if data.get('permission') != {'mode': 'advisory', 'scope': 'one_synthetic_text_module'}:
        return 'outside_experimental_authority'
    return None


def specs(contract, *, recheck=False):
    """LLM-designed, frozen questions are inputs; no automatic designer service."""
    require(set(contract) == {'version', 'design_source_ref', 'utility', 'support', 'action'},
            'invalid C02 design shape')
    require(isinstance(contract['version'], str) and bool(contract['version'])
            and isinstance(contract['design_source_ref'], str) and bool(contract['design_source_ref']),
            'missing design identity')
    result = []
    for name in ('utility', 'support'):
        item = contract[name]
        require(isinstance(item, dict) and set(item) == {'question', 'criteria'}, 'invalid C02 question')
        expected = {'adequate', 'deficit', 'outside_scope', 'conflict', 'unclear'} if name == 'utility' else {
            'sufficient', 'missing', 'conflict', 'unclear'}
        require(set(item['criteria']) == expected, 'C02 policy/answer mismatch')
        s = DecisionSpec(('recheck_' if recheck else '') + name, item['question'], item['criteria'],
                         READS, version=contract['version'], policy_ref='c02-one-local-rewrite-v1',
                         fallback_ref='original-tvg-exit-owner')
        s.validate()
        result.append(s)
    action = contract['action']
    require(isinstance(action, dict) and set(action) == {'question', 'criteria'}
            and set(action['criteria']) == ACTIONS, 'invalid C02 action candidates')
    DecisionSpec('action', action['question'], action['criteria'], READS + ('weaknesses',),
                 version=contract['version']).validate()
    return result


def plan(session, data, contract):
    """J1/J2 share State; their results are real input dependencies of J3."""
    questions = specs(contract)
    graph = {**GRAPH, 'design_sha256': digest(contract)}

    def finish(route, reason, action=None, judgments=None):
        return session.finish(graph, data, {'route': route, 'reason': reason, 'action': action,
            'judgments': judgments or {}, 'consumption': 'not_executed',
            'exit_owner': 'original-tvg-agent', 'exit_state': None})

    problem = input_problem(data)
    if problem:
        return finish('original_exit_owner', problem)
    view = {key: data[key] for key in READS}
    try:
        answers = session.evaluate(questions, view)
        if any(a.status != 'ok' for a in answers.values()):
            return finish('original_exit_owner', 'local_judgment_unavailable')
        judgments = {k: v.value for k, v in answers.items()}
        if judgments['utility'] in ('outside_scope', 'conflict', 'unclear'):
            return finish('original_exit_owner', 'scope_or_target_unresolved', judgments=judgments)
        if judgments['support'] != 'sufficient':
            return finish('acquire_information', 'evidence_not_established', judgments=judgments)
        choice = contract['action']
        action_spec = DecisionSpec('action', choice['question'], choice['criteria'], READS + ('weaknesses',),
            version=contract['version'], policy_ref='c02-one-local-rewrite-v1',
            fallback_ref='original-tvg-exit-owner')
        chosen = session.evaluate([action_spec], {**view, 'weaknesses': judgments})['action']
        if chosen.status != 'ok' or chosen.value == 'abstain':
            return finish('original_exit_owner', 'no_supported_action', judgments=judgments)
        if chosen.value == 'leave_unchanged':
            return finish('original_exit_owner', 'no_local_rewrite', chosen.value, judgments)
        return finish('rewrite_candidate', 'bounded_action_selected', chosen.value, judgments)
    except (ContractError, RecoveryRequired):
        return finish('original_exit_owner', 'contract_budget_or_recovery_failure')


def begin_rewrite(session, report, data, contract, generator_identity):
    """Create one generation intent before a host performs its authorized L1 call.

    This records a handoff; it does not launch or repeat a model call. An existing
    unmatched intent requires the host to reconcile, never regenerate blindly.
    """
    require(input_problem(data) is None, 'invalid rewrite context')
    require(report['identity']['input_sha256'] == digest(data)
            and report['identity']['graph'] == {**GRAPH, 'design_sha256': digest(contract)}
            and report['identity']['scope'] == session.scope
            and report['identity']['implementation'] == session.impl, 'rewrite lineage mismatch')
    require(report['result']['route'] == 'rewrite_candidate'
            and report['result']['action'] in REWRITES, 'no rewrite handoff')
    directory = rewrite_directory(session.root, report['run_id'])
    persisted = read_record(session.root / 'runs' / (report['run_id'] + '.json'))
    require(persisted['result'] == report['result'], 'rewrite report differs from journal')
    require(isinstance(generator_identity, str) and bool(generator_identity), 'missing generator identity')
    path = directory / 'intent.json'
    payload = {'parent_run_id': report['run_id'], 'parent_artifact_sha256': digest(data['artifact']),
               'context_sha256': digest(data), 'contract_sha256': digest(contract),
               'action': report['result']['action'], 'generator_identity': generator_identity,
               'max_rewrites': 1, 'exit_authority': False}
    if path.exists():
        require(read_record(path) == payload, 'rewrite intent changed')
        if not (path.parent / 'outcome.json').exists():
            raise RecoveryRequired('unresolved generation; reconcile original result')
        return read_record(path.parent / 'outcome.json')
    write_once(path, payload)
    return payload


def record_rewrite(session, run_id, artifact, *, generation_evidence, usage):
    """Import a host's actual single output; no synthetic generation evidence."""
    directory = rewrite_directory(session.root, run_id)
    intent = read_record(directory / 'intent.json')
    require(isinstance(artifact, str) and bool(artifact.strip()) and len(artifact.encode()) <= 16384,
            'invalid bounded rewrite')
    require(isinstance(generation_evidence, str) and bool(generation_evidence), 'missing generation evidence')
    require(isinstance(usage, dict) and set(usage) == {'input_tokens', 'output_tokens', 'cost_usd'},
            'missing generation cost coverage')
    from .contracts import number
    require(all(v is None or number(v, 0, 1e15) for v in usage.values()), 'invalid generation usage')
    payload = {**intent, 'artifact': artifact, 'artifact_sha256': digest(artifact),
               'generation_evidence': generation_evidence, 'usage': usage}
    path = directory / 'outcome.json'
    if path.exists():
        require(read_record(path) == payload, 'second rewrite is outside budget')
    else:
        write_once(path, payload)
    return payload


def recheck(session, report, data, contract, *, rewrite_root=None):
    """New artifact State, one check batch, then the original agent owns exit."""
    questions = specs(contract, recheck=True)
    parent = read_record(rewrite_directory(rewrite_root or session.root, report['run_id']) / 'outcome.json')
    require(parent['context_sha256'] == digest(data) and parent['contract_sha256'] == digest(contract),
            'recheck parent changed')
    updated = {**data, 'artifact': parent['artifact'], 'source_ref': 'rewrite:' + parent['artifact_sha256']}
    view = {key: updated[key] for key in READS}
    answers = session.evaluate(questions, view)
    # All judgments in this small graph read the artifact, so both are affected.
    # Original local judgments remain journaled; no unrelated source is re-evaluated.
    return session.finish({**GRAPH, 'design_sha256': digest(contract),
                           'parent_run_id': report['run_id']}, updated, {
        'route': 'original_exit_owner', 'reason': 'one_rewrite_and_recheck_complete',
        'judgments': {k: {'status': v.status, 'value': v.value} for k, v in answers.items()},
        'artifact_sha256': parent['artifact_sha256'], 'exit_owner': 'original-tvg-agent',
        'exit_state': None})
