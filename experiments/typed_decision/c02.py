"""One bounded TVG text module; local decisions never own the TVG exit."""
from __future__ import annotations

from .contracts import ContractError, DecisionSpec, digest, require
from .session import RecoveryRequired, read_record, write_once

GRAPH = {'id': 'mindthus.c02', 'version': '2', 'dependencies': {
    'L0': [], 'D0': ['L0'], 'utility': ['D0'], 'support': ['D0'],
    'action': ['D0'], 'consume': ['utility', 'support', 'action'],
    'rewrite': ['consume'], 'recheck_utility': ['rewrite'],
    'recheck_fidelity': ['rewrite'], 'exit_owner': ['recheck_utility', 'recheck_fidelity']}}
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
    """Version 2: same-State speculative planning, changed-artifact fidelity check."""
    require(isinstance(contract, dict) and set(contract) == {
        'version', 'design_source_ref', 'utility', 'support', 'action', 'fidelity'},
        'invalid C02 design shape')
    require(contract['version'] == '2' and isinstance(contract['design_source_ref'], str)
            and bool(contract['design_source_ref'].strip()), 'unsupported C02 design identity')
    choices = {
        'utility': {'adequate', 'deficit', 'outside_scope', 'conflict', 'unclear'},
        'support': {'sufficient', 'missing', 'conflict', 'unclear'},
        'action': ACTIONS, 'fidelity': {'faithful', 'violation', 'unclear'}}
    validated = {}
    for name, expected in choices.items():
        item = contract[name]
        require(isinstance(item, dict) and set(item) == {'question', 'criteria'}
                and isinstance(item['criteria'], dict) and set(item['criteria']) == expected,
                'C02 policy/answer mismatch')
        spec = DecisionSpec(('recheck_' if recheck else '') + name, item['question'],
            item['criteria'], READS, version=contract['version'],
            policy_ref='c02-one-local-rewrite-v2', fallback_ref='original-tvg-exit-owner')
        spec.validate()
        validated[name] = spec
    return [validated[name] for name in (
        ('utility', 'fidelity') if recheck else ('utility', 'support', 'action'))]


def plan(session, data, contract):
    """Independent questions share State; code consumes only consistent answers."""
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
        judgments = {k: v.value for k, v in answers.items() if v.status == 'ok'}
        if any(a.status != 'ok' for a in answers.values()):
            return finish('original_exit_owner', 'local_judgment_unavailable', judgments=judgments)
        if judgments['utility'] in ('outside_scope', 'conflict', 'unclear'):
            return finish('original_exit_owner', 'scope_or_target_unresolved', judgments=judgments)
        if judgments['support'] == 'missing':
            return finish('acquire_information', 'evidence_missing', judgments=judgments)
        if judgments['support'] != 'sufficient':
            return finish('original_exit_owner', 'source_basis_unresolved', judgments=judgments)
        action = judgments['action']
        if action == 'abstain':
            return finish('original_exit_owner', 'no_supported_action', action, judgments)
        if judgments['utility'] == 'adequate':
            reason = 'no_local_rewrite' if action == 'leave_unchanged' else 'inconsistent_local_judgments'
            return finish('original_exit_owner', reason, action, judgments)
        if action == 'leave_unchanged':
            return finish('original_exit_owner', 'inconsistent_local_judgments', action, judgments)
        return finish('rewrite_candidate', 'bounded_gap_repair_selected', action, judgments)
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
    # The changed artifact affects usefulness and fidelity. Source sufficiency is
    # not an artifact-fidelity question and is not re-scored on unchanged sources.
    statuses_ok = all(answer.status == 'ok' for answer in answers.values())
    reason = ('artifact_review_unavailable' if not statuses_ok else
              'artifact_fidelity_violation' if answers['recheck_fidelity'].value == 'violation' else
              'artifact_review_unresolved' if answers['recheck_fidelity'].value == 'unclear' else
              'artifact_target_not_met' if answers['recheck_utility'].value != 'adequate' else
              'one_rewrite_and_recheck_complete')
    return session.finish({**GRAPH, 'design_sha256': digest(contract),
                           'parent_run_id': report['run_id']}, updated, {
        'route': 'original_exit_owner', 'reason': reason,
        'judgments': {k: {'status': v.status, 'value': v.value} for k, v in answers.items()},
        'artifact_sha256': parent['artifact_sha256'], 'exit_owner': 'original-tvg-agent',
        'exit_state': None})
