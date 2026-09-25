"""Opt-in source-direct routing in the existing Episode and CurrentAgentHost.

The old route remains available for historical replay. This successor uses its
bounded route compiler, method loader, dependency acceptance and episode journal.
"""
from __future__ import annotations

from pathlib import Path
import subprocess

from . import relationship_assessment as rel, relationship_runtime as rt
from . import route_control as rc, source_direct_v03 as sd
from .contracts import canonical, digest, provider_configuration, require
from .current_host import AwaitingCurrentAgent, CurrentAgentHost, is_current_host
from .session import implementation_digest, read_record

MODE = sd.MODE
PROFILE = {**rc.PROFILE, 'judgments_total': 4, 'judgments_per_turn': 4,
           'corrections_total': 1, 'corrections_per_turn': 1, 'structural_organize': 1,
           'arbitrations_total': 1, 'total_requests': 7,
           'single_call_seconds': 240, 'request_seconds': 960}
STEP_KINDS = {**rc.STEP_KINDS, 'candidate': 'judgment'}
HOST_SLOTS = rc.HOST_SLOTS


def _bundle(repo):
    bundle, qs, bindings = rc.load_policy(repo)
    contract, source_sha256 = sd.load_contract(repo)
    bundle = rel.clone(bundle)
    bundle['sources'][sd.CONTRACT_PATH] = source_sha256
    bundle['v03_contract_sha256'] = digest(contract)
    return bundle, qs, bindings, contract


def prepare_admission(root, provider, packet, repo, hooks, *, authorization_ref, experiment_condition=None, candidate_snapshot=None):
    """Build an identity-bound future live freeze; this makes no provider call."""
    root, repo = Path(root).resolve(), Path(repo).resolve()
    require(repo == Path(__file__).resolve().parents[2] and not root.is_relative_to(repo),
            'v03_checkout_or_state_root')
    require(rel.text(authorization_ref), 'v03_live_authorization_required')
    _validate_provider(provider, experiment_condition)
    bundle, _, bindings, _ = _bundle(repo)
    sd.validate_packet(packet, bindings)
    if candidate_snapshot is not None:
        from .comparison_v03 import validate_snapshot
        validate_snapshot(candidate_snapshot, packet, repo)
    owner = packet['authority']['owner_ref']
    require(set(hooks) == {'executor', 'arbitrator', 'corrector', 'organizer'},
            'v03_host_slots')
    for name, hook in hooks.items():
        _host_identity(hook, owner + (':route-arbitrator' if name == 'arbitrator'
                                      else ':organizer' if name == 'organizer' else ''), True)
        require(hook is None or isinstance(hook, CurrentAgentHost),
                'v03_current_host_only')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo,
                                     text=True, stderr=subprocess.PIPE).strip()
    judgments = 2 if candidate_snapshot is not None else 4 if packet['dependencies'] else 3
    organize = 1 if not packet['issues'] else 0
    return {'schema': 'mindthus.route-control-live.v1', 'authorization_ref': authorization_ref,
            'experiment_condition': experiment_condition, 'candidate_snapshot_sha256': digest(candidate_snapshot),
            'observer_original_context_ref': (provider.host_context_ref
                if experiment_condition == 'codex_observation_committed' else None),
            'source_commit': commit, 'implementation': implementation_digest(),
            'timing_profile': {k: PROFILE[k] for k in ('single_call_seconds','request_seconds')},
            'source_bindings': bundle['sources'], 'mode': MODE,
            'root': str(root), 'packet_hashes': [digest(packet)],
            'provider': provider_configuration(provider),
            **{name: (hook.configuration if hook else None) for name, hook in hooks.items()},
            'ceilings': {'requests': judgments + organize + 2, 'judgments': judgments, 'corrections': 1,
                         'organize': organize,
                         'arbitrations': 1, 'executions': packet['task_budget']['max_calls'],
                         'reserve_per_jev_usd': .02}}


def _validate_provider(provider, experiment_condition=None):
    from .comparison_v03 import CurrentAgentObserver
    serving = provider_configuration(provider)['serving']
    if experiment_condition == 'codex_observation_committed':
        require(isinstance(provider, CurrentAgentObserver), 'v03_explicit_control_backend')
    else:
        require(experiment_condition is None and getattr(provider, 'is_live', None) is True
                and serving['provider'] == 'typesafe' and serving['transport'] == 'systemone-v1'
                and serving['requested_model'] == 'jev-1.13.0', 'v03_official_jev_required')


def _host_identity(hook, expected, live):
    require(hook is None or (hook.identity == expected and
            (is_current_host(hook) or getattr(hook, 'is_live', None) is live)),
            'v03_host_identity')


def _organize_request(packet, bindings):
    body = {'schema': 'mindthus.route-v03-organize-request.v1', 'mode': MODE, 'policy': MODE,
            'original_input': packet,
            'method_summaries': {m['method']: m['method_binding_question']
                                 for m in bindings['methods']},
            'instruction': 'Extract at most three source-bound issues and no more than three '
                           'method candidates per issue. Host guesses are inference, not facts. '
                           'Do not invent a full frame/claim graph or decide the final answer.'}
    return {**body, 'request_id': digest(body)}


def validate_organized(reply, request, bindings):
    rel.shape(reply, {'schema', 'request_id', 'issues', 'host_inferences', 'usage'},
              'v03_organizer_reply')
    require(reply['schema'] == 'mindthus.route-v03-organize-reply.v1'
            and reply['request_id'] == request['request_id'], 'v03_organizer_binding')
    rt._usage(reply['usage'])
    amended = {**request['original_input'], 'issues': reply['issues'],
               'host_inferences': reply['host_inferences']}
    sd.validate_packet(amended, bindings, organized=True)
    return amended


def _admit(admission, root, packet, provider, bundle, hooks):
    require(isinstance(admission, dict) and
            admission.get('schema') == 'mindthus.route-control-live.v1' and
            admission.get('mode') == MODE and admission.get('root') == str(root) and
            admission.get('implementation') == implementation_digest() and
            admission.get('source_bindings') == bundle['sources'] and
            admission.get('provider') == provider_configuration(provider), 'v03_live_identity')
    require(admission.get('timing_profile') ==
            {k: PROFILE[k] for k in ('single_call_seconds','request_seconds')}, 'v03_live_timing_changed')
    require(digest(packet) in admission.get('packet_hashes', []) and
            rel.text(admission.get('authorization_ref')), 'v03_input_not_admitted')
    caps = admission['ceilings']
    for key, maximum in {'judgments': 4, 'corrections': 1, 'organize': 1,
                         'arbitrations': 1, 'requests': 7,
                         'executions': packet['task_budget']['max_calls']}.items():
        require(type(caps.get(key)) is int and 0 <= caps[key] <= maximum, 'v03_live_budget')
    require(0 < caps.get('reserve_per_jev_usd', 0) <= .25, 'v03_live_reserve')
    for name, hook in hooks.items():
        require(admission.get(name) == (hook.configuration if hook else None),
                'v03_live_host_configuration')


def _execution_reply(reply, request, packet, bindings):
    if 'dependency_acceptance' in reply:
        accepted = reply['dependency_acceptance']
        require(isinstance(accepted, dict) and set(accepted) <= set(request['dependency_uses']),
                'v03_dependency_acceptance_scope')
        for item in accepted.values():
            rel.shape(item, {'accepted', 'artifact_sha256', 'reason'}, 'v03_dependency_receipt')
            require(type(item['accepted']) is bool and item['artifact_sha256'] == digest(reply['text'])
                    and rel.text(item['reason']) and reply['objection'] is None, 'v03_dependency_receipt_binding')
    reply = {k: v for k, v in reply.items() if k != 'dependency_acceptance'}
    if packet['consumption_policy'] == 'committed':
        rc.validate_execution(reply, request, sd.route_input(packet))
        return
    rel.shape(reply, {'route_id', 'revision', 'issue_id', 'performed_methods',
                      'text', 'objection', 'usage'}, 'v03_advisory_execution')
    require(reply['route_id'] == request['route_id'] and
            reply['revision'] == request['revision'] and
            reply['issue_id'] == request['issue']['issue_id'], 'v03_advisory_execution_binding')
    rt._usage(reply['usage'])
    allowed = {m['method'] for m in bindings['methods']}
    require(isinstance(reply['performed_methods'], list) and
            len(reply['performed_methods']) == len(set(reply['performed_methods'])) and
            set(reply['performed_methods']) <= allowed, 'v03_advisory_method_claim')
    require(rel.text(reply['text']) and reply['objection'] is None,
            'v03_advisory_result_required')


def _post_artifacts(ep, directory, packet, route, iid, needed, outputs, bundle, qs, bindings, contract):
    old = next(r for r in route['per_issue'] if r['issue_id'] == iid)
    # An accepted artifact cannot supply a missing retained candidate or an unassigned task.
    if 'unassigned_scope' in route['coverage'] or route['coverage']['issues'][iid].get('value') != 'covered':
        return route
    artifacts = []
    for edge in needed:
        out = outputs[edge['producer']]
        receipt = out['accepted_uses'][edge['id']]
        require(receipt['accepted'] and receipt['artifact_sha256'] == out['artifact_sha256'],
                'post_artifact_acceptance_required')
        artifacts.append({'producer_issue': edge['producer'], 'consumer_issue': iid,
                          'artifact_contract': edge['artifact'], 'dependency_id': edge['id'],
                          'text': out['text'], 'artifact_sha256': out['artifact_sha256'],
                          'acceptance': receipt,
                          'provenance': 'original_host_output_accepted_for_this_use_not_independent_fact'})
    compiled = sd.compile_s0(packet, ep.repo, bundle, qs, bindings, contract,
                             focus_issue=iid, artifacts=artifacts)
    name = 'route__after__' + iid + '__' + digest(compiled.identity)[:16]
    answers = rc._evaluate(ep, directory, compiled, name=name, mode=MODE)
    local = {**packet, 'issues': [i for i in packet['issues'] if i['id'] == iid], 'dependencies': []}
    local_answers = {**answers, 'COVERAGE.global': route['coverage']['global']}
    updated = sd.consume_s0(local, compiled, local_answers, bundle, bindings)
    changed = rel.clone(route)
    changed['per_issue'] = [updated['per_issue'][0] if r['issue_id'] == iid else r for r in route['per_issue']]
    changed['coverage']['issues'][iid] = updated['coverage']['issues'][iid]
    changed['mandatory_reads'] = sorted(set(route['mandatory_reads']) | set(updated['mandatory_reads']))
    changed['source_observations'].update(answers)
    changed['revision'] += 1
    changed['parent_commitment_sha256'] = digest(route)
    changed.setdefault('post_artifact_evaluations', []).append({'issue_id': iid, 'step': name,
        'prior_scope': old, 'accepted_artifacts_sha256': digest(artifacts), 'observations': answers})
    rc.refresh(changed)
    rt.save(directory / ('commitment-' + str(changed['revision']) + '.json'), changed)
    return changed


def _invalidate_dependents(route, outputs, changed, pending):
    affected = set(changed)
    dependents = set()
    while True:
        more = {e['consumer'] for e in route['artifact_edges'] if e['producer'] in affected}
        dependents |= more
        if more <= affected:
            break
        affected |= more
    # A simultaneous text revision is not a receipt for consuming the NEW
    # predecessor version. Both changed and unchanged descendants need that proof.
    for iid in dependents:
        pending[iid] = 'accepted_predecessor_version_changed'
        if iid in outputs:
            outputs[iid]['valid_for_current_dependencies'] = False
    for iid in affected:
        if iid in outputs and outputs[iid].get('accepted_uses'):
            outputs[iid]['invalidated_accepted_uses'] = outputs[iid]['accepted_uses']
            outputs[iid]['accepted_uses'] = {}


def _dispatch(ep, directory, packet, route, bundle, qs, bindings, compiled,
              executor, arbitrator, artifact_acceptor, contract):
    """Dispatch current-host work; use the old targeted dependent-successor repair."""
    outputs, pending, accepted = {}, {}, {}
    order = [issue['id'] for issue in packet['issues']]
    waiting, advanced = set(order), set()
    owner = packet['authority']['owner_ref']
    while waiting:
        progressed = False
        for iid in order:
            if iid not in waiting:
                continue
            row = next(r for r in route['per_issue'] if r['issue_id'] == iid)
            needed = [e for e in route['artifact_edges'] if e['consumer'] == iid]
            # Known source-bound prerequisites apply to both consumption modes.
            if any(e['relation'] == 'unclear' or
                   (e['relation'] == 'conditional' and e['condition_value'] is not True)
                   for e in needed):
                pending[iid] = 'dependency_unresolved'
                waiting.remove(iid); progressed = True; continue
            if needed and row['mode'] in ('committed', 'delegated_unresolved'):
                if any(e['producer'] not in accepted or not accepted[e['producer']].get(e['id'])
                       for e in needed):
                    continue
                if row['mode'] == 'delegated_unresolved' and iid not in advanced:
                    route = _post_artifacts(ep, directory, packet, route, iid,
                                            needed, outputs, bundle, qs, bindings, contract)
                    advanced.add(iid)
                    row = next(r for r in route['per_issue'] if r['issue_id'] == iid)
            mode = packet['consumption_policy']
            original_issue = next(x for x in packet['issues'] if x['id'] == iid)
            known_handling = rc._resolution(original_issue['handling'], sd.route_input(packet),
                                            {d['id']: d for d in packet['documents']})
            if known_handling == 'acquire_fact':
                pending[iid] = 'owner_established_fact_required'
                waiting.remove(iid); progressed = True; continue
            if mode == 'committed' and row['mode'] not in ('committed', 'direct'):
                pending[iid] = row['reason'] or row['mode']
                waiting.remove(iid); progressed = True; continue
            if any(e['producer'] not in accepted or not accepted[e['producer']].get(e['id'])
                   for e in needed):
                continue
            if executor is None:
                pending[iid] = 'executor_not_supplied'
                waiting.remove(iid); progressed = True; continue
            for attempt in range(2 if mode == 'committed' else 1):
                row = next(r for r in route['per_issue'] if r['issue_id'] == iid)
                methods = sorted({row['primary'], *row['supports'], *row['constraints']} - {None})
                names = {m['method'] for m in bindings['methods']}
                loaded = rc._read_methods(ep.repo, names, bindings)
                request = {'schema': 'mindthus.route-v03-execution-request.v1',
                           'mode': MODE, 'policy': mode, 'route_id': route['route_id'],
                           'revision': route['revision'], 'issue': row,
                           'execute_methods': methods if mode == 'committed' else [],
                           'suggested_methods': methods, 'loaded_methods': loaded,
                           'route_observations': route['source_observations'], 'coverage': route['coverage'],
                           'dependency_uses': {e['id']: e for e in route['artifact_edges'] if e['producer'] == iid},
                           'original_input': packet, 'prior_outputs': outputs,
                           'authority': packet['authority'],
                           'instruction': ('Execute the committed method scope; give a source-bound '
                                           'objection if it is materially wrong.' if mode == 'committed' else
                                           'Use the route as advice. Choose a sufficient canonical or direct '
                                           'path and disclose performed methods. Preserve authority and known dependencies.')}
                request['request_id'] = digest(request)
                step = 'execution__' + iid + '__' + str(route['revision'])
                rt.save(directory / 'dispatch' / (step + '.json'),
                        {'request_id': request['request_id'], 'route_sha256': digest(route),
                         'loads': loaded})
                out = rt._host(ep, directory, step, request, executor,
                               lambda reply: _execution_reply(reply, request, packet, bindings),
                               operation='execute', expected_owner=owner)
                if out['status'] != 'complete':
                    pending[iid] = 'execution_failed_or_noncompliant'; break
                reply = out['reply']
                if reply['objection'] is None:
                    outputs[iid] = {'route_id': route['route_id'], 'revision': route['revision'],
                                    'text': reply['text'], 'methods': reply['performed_methods'],
                                    'artifact_sha256': digest(reply['text']), 'accepted_uses': {},
                                    'input_artifacts': {e['id']: outputs[e['producer']]['artifact_sha256'] for e in needed},
                                    'valid_for_current_dependencies': True}
                    accepted[iid] = {}
                    for edge in route['artifact_edges']:
                        if edge['producer'] == iid and (artifact_acceptor or edge['id'] in reply.get('dependency_acceptance', {})):
                            ap = directory / 'accepted' / (edge['id'] + '.json')
                            receipt = (read_record(ap) if ap.exists() else
                                       artifact_acceptor.accept(edge, outputs[iid], packet) if artifact_acceptor else
                                       {**reply['dependency_acceptance'][edge['id']], 'owner_ref': owner,
                                        'dependency_id': edge['id'], 'host_context_ref': out.get('host_context_ref'),
                                        'source': 'bound_current_host_execution_receipt'})
                            require(isinstance(receipt, dict) and receipt.get('owner_ref') == owner and
                                    receipt.get('artifact_sha256') == outputs[iid]['artifact_sha256'] and
                                    receipt.get('dependency_id') == edge['id'] and
                                    type(receipt.get('accepted')) is bool,
                                    'v03_artifact_acceptance_receipt')
                            rt.save(ap, receipt)
                            accepted[iid][edge['id']] = receipt['accepted']
                            outputs[iid]['accepted_uses'][edge['id']] = receipt
                    break
                if arbitrator is None or attempt:
                    pending[iid] = 'objection_requires_original_owner'; break
                ar = {'mode': MODE, 'policy': mode, 'route_id': route['route_id'],
                      'revision': route['revision'], 'issue_id': iid,
                      'objection': reply['objection'], 'route': route,
                      'original_input': sd.route_input(packet),
                      'method_contracts': compiled.loaded,
                      'instruction': 'Independently judge the named route objection only.'}
                if out.get('host_context_ref'):
                    ar['executor_context_ref'] = out['host_context_ref']
                ar['request_id'] = digest(ar)
                adjudicated = rt._host(ep, directory, 'arbitration', ar, arbitrator,
                                       lambda result: rc._change(route, iid, result, sd.route_input(packet)),
                                       operation='arbitrate', expected_owner=owner + ':route-arbitrator')
                if adjudicated['status'] != 'complete':
                    pending[iid] = 'arbitration_failed'; break
                route = rc._change(route, iid, adjudicated['reply'], sd.route_input(packet))
                rt.save(directory / ('commitment-' + str(route['revision']) + '.json'), route)
                if next(r for r in route['per_issue'] if r['issue_id'] == iid)['mode'] not in ('committed', 'direct'):
                    pending[iid] = 'objection_scope_delegated'; break
            waiting.remove(iid); progressed = True
        if not progressed:
            pending.update({iid: 'dependency_waiting_or_cycle' for iid in waiting})
            break
    return route, outputs, pending


def run(root, provider, data, repo, *, executor=None, arbitrator=None,
        corrector=None, organizer=None, recheck=True, live_admission=None,
        artifact_acceptor=None, candidate_snapshot=None):
    repo, root, packet = Path(repo).resolve(), Path(root).resolve(), rel.clone(data)
    submitted_packet = rel.clone(packet)
    if candidate_snapshot is not None:
        from .comparison_v03 import validate_snapshot
        validate_snapshot(candidate_snapshot, packet, repo)
    require(not root.is_relative_to(repo), 'state_root_inside_repository')
    bundle, qs, bindings, contract = _bundle(repo)
    sd.validate_packet(packet, bindings)
    require(recheck is True, 'v03_recheck_required_for_correction')
    live = live_admission is not None
    require(getattr(provider, 'is_live', None) is live, 'v03_live_not_admitted')
    if live:
        _validate_provider(provider, live_admission.get('experiment_condition'))
    owner = packet['authority']['owner_ref']
    hooks = {'executor': executor, 'arbitrator': arbitrator,
             'corrector': corrector, 'organizer': organizer}
    for name, hook in hooks.items():
        _host_identity(hook, owner + (':route-arbitrator' if name == 'arbitrator'
                                      else ':organizer' if name == 'organizer' else ''), live)
        require(hook is None or isinstance(hook, CurrentAgentHost), 'v03_current_host_only')
    require(arbitrator is None or arbitrator is not executor,
            'v03_executor_cannot_self_arbitrate')
    if artifact_acceptor is not None:
        require(artifact_acceptor.identity == owner, 'v03_artifact_owner')
    if live:
        _admit(live_admission, root, packet, provider, bundle, hooks)
        require(live_admission.get('candidate_snapshot_sha256') == digest(candidate_snapshot), 'v03_snapshot_not_admitted')
        if live_admission.get('experiment_condition') == 'codex_observation_committed':
            require(live_admission.get('observer_original_context_ref') == provider.host_context_ref,
                    'v03_observer_original_context_changed')
    profile = {**PROFILE, 'executions_total': packet['task_budget']['max_calls'],
               'execution_seconds': packet['task_budget']['max_seconds']}
    with rt.Episode(root, repo, provider, packet, bundle, live_admission,
                    mode=MODE, profile=profile, kinds=STEP_KINDS,
                    host_slots=HOST_SLOTS) as ep:
        rt.save(root / 'intervention.json', {'intervention': packet['intervention'],
                'consumption_policy': packet['consumption_policy']})
        directory = root / 'turns' / ep.turn_key / 'inputs' / digest(packet)
        require(all(p['directory'] == str(directory) for p in ep.tally()['pending_host']),
                'v03_pending_host_must_resume')
        binding = {'original_input': packet, 'episode_manifest_sha256': digest(ep.manifest),
                   'hooks': {name: (hook.configuration if hook else None)
                             for name, hook in hooks.items()},
                   'artifact_acceptor': getattr(artifact_acceptor, 'configuration', None),
                   'recheck': recheck, 'candidate_snapshot': candidate_snapshot}
        rt.save(directory / 'manifest.json', binding)
        summary = directory / 'summary.json'
        if summary.exists():
            return {**read_record(summary), 'source_ref': str(summary)}
        route, outputs, pending, s0, s1 = None, {}, {}, None, None
        correction, arbitration, rechecked, acceptance = None, None, None, None
        finding_states, issue_states = {}, {}
        def finish(reason=None, *, terminal=True):
            state = ep.tally()
            for issue in packet['issues']:
                iid = issue['id']
                if iid not in issue_states:
                    issue_states[iid] = {'state': 'technical_failure' if state['failures'] else
                        'unresolved' if iid in pending or iid in outputs else 'unrun',
                        'reason': pending.get(iid, reason)}
            result = {'schema': 'mindthus.route-control-result.v03', 'mode': MODE,
                      'consumption_policy': packet['consumption_policy'],
                      'original_input': submitted_packet,
                      'effective_input_sha256': digest(packet),
                      'route': route, 'outputs': outputs,
                      'pending': pending, 's0': s0, 's1': s1, 'correction': correction,
                      'arbitration': arbitration, 'recheck': rechecked,
                      'acceptance': acceptance, 'reason': reason,
                      'finding_states': finding_states, 'issue_states': issue_states,
                      'consumption_complete': bool(acceptance) and not pending and
                          all(x['accepted'] for x in acceptance['accepted'].values()),
                      'counts': state['counts'], 'usage': state['usage'],
                      'plugin_request_seconds': state['seconds'],
                      'method_request_seconds': state.get('execution_seconds', 0),
                      'pending_host_requests': state['pending_host'],
                      'reserved_counts': state['reserved_counts'],
                      'evidence_kind': ep.evidence_kind, 'task_complete': False,
                      'qualification': False, 'semantic_method_fidelity': 'not_verified_by_receipt'}
            if terminal:
                rt.save(summary, result)
            return {**result, 'source_ref': str(summary if terminal else directory / 'manifest.json')}
        try:
            if packet['authority']['risk'] != 'low' or packet['authority']['mode'] == 'none':
                return finish('outside_low_risk_opt_in')
            if ep.tally()['failures']:
                return finish('terminal_prior_failure')
            if not packet['issues']:
                if organizer is None:
                    return finish('awaiting_organizer', terminal=False)
                request = _organize_request(packet, bindings)
                out = rt._host(ep, directory, 'organize', request, organizer,
                               lambda reply: validate_organized(reply, request, bindings),
                               operation='organize', expected_owner=owner + ':organizer')
                if out['status'] != 'complete':
                    return finish('organizer_failed')
                packet = validate_organized(out['reply'], request, bindings)
                rt.save(directory / 'organized-input.json', packet)
            if candidate_snapshot is not None:
                route = rel.clone(candidate_snapshot['route'])
                outputs = rel.clone(candidate_snapshot['outputs'])
            else:
                compiled = sd.compile_s0(packet, repo, bundle, qs, bindings, contract)
                rt.save(directory / 'judgment-contract-loads.json', compiled.loaded)
                observations = rc._evaluate(ep, directory, compiled, name='route', mode=MODE)
                s0 = {'observations': observations, 'compiled_identity': compiled.identity}
                route = sd.consume_s0(packet, compiled, observations, bundle, bindings)
                route['engine_identity'] = ep.manifest['provider']
                rt.save(directory / 'commitment-1.json', route)
                route, outputs, pending = _dispatch(ep, directory, packet, route, bundle, qs, bindings,
                                                    compiled, executor, arbitrator, artifact_acceptor, contract)
            if outputs:
                candidate_batch = sd.compile_s1(packet, route, outputs, repo, contract)
                initial = rc._evaluate(ep, directory, candidate_batch, name='candidate', mode=MODE)
                s1 = sd.consume_s1(packet, candidate_batch, initial, contract)
                rt.save(directory / 'candidate-observation.json', s1)
            else:
                return finish('no_current_candidate')
            disposition = {iid: 'resolved' for iid in outputs}
            current_report = s1
            request = None
            if s1['findings']:
                finding_states.update({f['finding_id']: {'state': 'pending', 'issue_id': f['issue_id'],
                    'target_version': f['target_version']} for f in s1['findings']})
                if corrector is None:
                    pending.update({f['issue_id']: 'observation_delivery_not_supplied' for f in s1['findings']})
                    return finish('awaiting_corrector', terminal=False)
                advisory = packet['consumption_policy'] == 'advisory'
                request = (sd.advice_request if advisory else sd.correction_request)(packet, route, outputs, s1)
                validator = sd.validate_advice if advisory else sd.validate_correction
                out = rt._host(ep, directory, 'correction', request, corrector,
                               lambda reply: validator(reply, request), operation='correct', expected_owner=owner)
                if out['status'] != 'complete':
                    return finish('correction_failed')
                correction = out['reply']
                for iid, changed in correction['revisions'].items():
                    outputs[iid] = {**outputs[iid], 'text': changed['text'],
                                    'artifact_sha256': digest(changed['text']),
                                    'candidate_version': changed['version'],
                                    'parent_artifact_sha256': outputs[iid]['artifact_sha256']}
                revised = set(correction['revisions'])
                _invalidate_dependents(route, outputs, revised, pending)
                if revised:
                    followup = sd.compile_s1(packet, route, {i: outputs[i] for i in revised}, repo, contract)
                    result = rc._evaluate(ep, directory, followup, name='candidate__recheck', mode=MODE)
                    rechecked = sd.consume_s1(packet, followup, result, contract)
                    rt.save(directory / 'candidate-recheck.json', rechecked)
                    current_report = {**rechecked,
                        'findings': [f for f in s1['findings'] if f['issue_id'] not in revised] + rechecked['findings'],
                        'matrix': [f for f in s1['matrix'] if f['issue_id'] not in revised] + rechecked['matrix']}
                if not advisory:
                    # Freeze the pre-arbitration endpoint before any extra judgment.
                    rt.save(directory / 'before-arbitration.json',
                            {'outputs': outputs, 'observations': current_report, 'pending': pending})
                    ar = sd.arbitration_request(packet, route, request, correction,
                                                out.get('host_context_ref'), outputs, current_report)
                    if ar['objections'] and arbitrator is not None:
                        step = directory / 'steps' / 'arbitration'
                        existing = read_record(step / 'request.json') if (step / 'request.json').exists() else None
                        # A completed identical request is replayable even when its slot has been used.
                        if existing == ar or (existing is None and ep.tally()['counts']['arbitration'] == 0):
                            judged = rt._host(ep, directory, 'arbitration', ar, arbitrator,
                                lambda reply: sd.validate_arbitration(reply, ar),
                                operation='arbitrate', expected_owner=owner + ':route-arbitrator')
                            if judged['status'] != 'complete':
                                return finish('arbitration_failed')
                            arbitration = judged['reply']
                    decisions = {d['finding_id']: d for d in (arbitration or {}).get('decisions', [])}
                    active = {(f['issue_id'], f['check_id']): f for f in current_report['findings']}
                    old = {f['finding_id']: f for f in s1['findings']}
                    dismissed = set()
                    for item in correction['dispositions']:
                        f = old[item['finding_id']]; key = (f['issue_id'], f['check_id'])
                        state = 'unresolved'
                        if item['decision'] != 'unresolved' and key not in active:
                            state = 'resolved_by_revision'
                        elif item['decision'] == 'objected':
                            decision = decisions.get(item['finding_id'], {})
                            if decision.get('decision') == 'dismiss':
                                state = 'resolved_by_objection'; dismissed.add(key)
                        finding_states[item['finding_id']] = {'state': state,
                            'issue_id': f['issue_id'], 'target_version': outputs[f['issue_id']]['artifact_sha256']}
                        if state == 'unresolved':
                            pending[f['issue_id']] = 'finding_unresolved'
                    for key, f in active.items():
                        if key not in dismissed:
                            pending[f['issue_id']] = 'candidate_correction_unverified_or_unresolved'
                else:
                    for f in s1['findings']:
                        finding_states[f['finding_id']] = {'state': 'advice_consumed',
                            'issue_id': f['issue_id'], 'target_version': outputs[f['issue_id']]['artifact_sha256']}
            for iid in pending:
                if iid in disposition:
                    disposition[iid] = 'unresolved'
            evidence = {'initial': s1, 'recheck': rechecked, 'arbitration': arbitration,
                        'finding_states': finding_states, 'pending': pending,
                        'dependency_versions': {i: o.get('input_artifacts', {}) for i, o in outputs.items()}}
            if executor is not None and outputs:
                ar = sd.acceptance_request(packet, route, outputs, disposition, evidence)
                try:
                    out = rt._host(ep, directory, 'execution__accept', ar, executor,
                                   lambda reply: sd.validate_acceptance(reply, ar),
                                   operation='accept', expected_owner=owner)
                except rt.EpisodeStop as exc:
                    pending.update({iid: 'acceptance_budget_exhausted' for iid in outputs})
                    return finish(str(exc))
                if out['status'] != 'complete':
                    pending.update({iid: 'acceptance_failed' for iid in outputs})
                    return finish('acceptance_failed')
                acceptance = out['reply']
                for iid, receipt in acceptance['accepted'].items():
                    if not receipt['accepted']:
                        pending.setdefault(iid, 'owner_declined_acceptance')
            elif outputs:
                pending.update({iid: 'acceptance_owner_not_supplied' for iid in outputs})
            for issue in packet['issues']:
                iid = issue['id']
                if iid in pending:
                    issue_states[iid] = {'state': 'unresolved', 'reason': pending[iid]}
                elif iid not in outputs:
                    issue_states[iid] = {'state': 'unrun'}
                else:
                    own = [f['state'] for f in finding_states.values() if f['issue_id'] == iid]
                    state = ('resolved_by_objection' if 'resolved_by_objection' in own else
                             'resolved_by_revision' if 'resolved_by_revision' in own else 'accepted')
                    issue_states[iid] = {'state': state, 'artifact_sha256': outputs[iid]['artifact_sha256']}
            return finish()
        except AwaitingCurrentAgent as exc:
            result = finish('awaiting_current_agent', terminal=False)
            return {**result, 'status': 'awaiting_current_agent',
                    'host_request': exc.handoff_path}
        except rt.EpisodeStop as exc:
            if s1 is not None:
                pending.update({f['issue_id']: 'episode_budget_exhausted_after_observation'
                                for f in s1['findings']})
            return finish(str(exc))
