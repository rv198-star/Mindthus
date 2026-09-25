"""Opt-in committed routing. Canonical questions decide; code loads and dispatches.

The retained-candidate/raw-span interface is deliberately bounded. It is not an
open-ended planner or proof of semantic method execution. All calls share Episode.
"""
from __future__ import annotations
from dataclasses import asdict
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json

from . import relationship_assessment as rel, relationship_runtime as rt
from .contracts import DecisionSpec, canonical, digest, number, provider_configuration, require
from .session import Limits, RecoveryRequired, Session, implementation_digest, read_record
from .current_host import AwaitingCurrentAgent, is_current_host

MODE = 'route-control.v0.2.1'
BASE = 'docs/internal/research/typed-decision/'
DESIGN = BASE + 'route-control-v0.2/'
QUESTIONS = BASE + 'mainline-composition-v0.1/questions.json'
METHODS = BASE + 'mainline-composition-v0.1/method-bindings.json'
PROFILE = {**rt.PROFILE, 'judgments_per_turn': 4, 'corrections_total': 1,
           'arbitrations_total': 1, 'request_seconds': 180,
           'executions_total': 0, 'execution_seconds': 0}
STEP_KINDS = {**rt.KINDS, 'route': 'judgment', 'relation': 'judgment',
              'arbitration': 'arbitration', 'execution': 'execution'}
HOST_SLOTS = {'correction': 'corrector', 'organize': 'organizer',
              'arbitration': 'arbitrator', 'execution': 'executor'}


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_policy(repo):
    p = json.loads((repo / DESIGN / 'profile.json').read_bytes())
    a = json.loads((repo / DESIGN / 'implementation-addendum.json').read_bytes())
    require(_sha(repo / DESIGN / 'profile.json') == a['extends']['sha256'], 'route_policy_changed')
    for key in ('extends_questions', 'method_bindings'):
        require(_sha(repo / p[key]['path']) == p[key]['sha256'], 'route_contract_changed')
    qs = {q['id']: q for q in json.loads((repo / QUESTIONS).read_bytes())['questions']}
    bindings = json.loads((repo / METHODS).read_bytes())
    paths = [DESIGN + 'profile.json', DESIGN + 'implementation-addendum.json', QUESTIONS, METHODS]
    paths += [m['source_path'] for m in bindings['methods']]
    sources = {name: _sha(repo / name) for name in paths}
    for m in bindings['methods']:
        require(sources[m['source_path']] == m['source_sha256'], 'canonical_method_changed')
    related, _ = rel.load_contract(repo)
    return {'sources': sources, 'policy': p, 'addendum': a,
            'relationship_contract_sha256': digest(related)}, qs, bindings


def check_ref(ref, docs, *, source_only=False):
    rel.shape(ref, rel.REF_FIELDS, 'route_reference')
    require(ref['document_id'] in docs, 'route_reference_absent')
    doc = docs[ref['document_id']]
    require(rel.quote(doc, ref['start'], ref['end']) == ref, 'route_reference_changed')
    require(not source_only or doc['kind'] in ('user', 'source'), 'route_source_role')
    return doc['text'][ref['start']:ref['end']]


def _resolution(x, packet, docs):
    if x is None:
        return None
    rel.shape(x, {'value', 'owner_ref', 'revision', 'refs'}, 'existing_resolution')
    require(x['owner_ref'] == packet['authority']['owner_ref'] and x['revision'] == packet['revision'],
            'resolution_owner_or_version')
    require(isinstance(x['refs'], list) and bool(x['refs']), 'resolution_source_missing')
    for ref in x['refs']:
        check_ref(ref, docs, source_only=True)
    return x['value']


def validate_input(packet, bindings):
    keys = {'schema', 'episode_id', 'turn_id', 'revision', 'documents', 'authority',
            'issues', 'dependencies', 'relationship', 'task_budget'}
    require(isinstance(packet, dict) and keys <= set(packet) <= keys | {'relationship_issue'}, 'invalid_route_input')
    require(packet['schema'] == 'mindthus.route-control-input.v1', 'route_schema')
    require(all(rel.text(packet[k]) for k in ('episode_id', 'turn_id', 'revision')), 'route_identity')
    require(len(canonical(packet)) <= 98304, 'route_input_overflow')
    docs = {}
    require(isinstance(packet['documents'], list) and 0 < len(packet['documents']) <= 20, 'route_documents')
    for d in packet['documents']:
        rel.shape(d, {'id', 'revision', 'kind', 'text'}, 'route_document')
        require(rel.identifier(d['id']) and d['id'] not in docs and rel.text(d['text'])
                and rel.text(d['revision']) and d['kind'] in ('user', 'source', 'assistant', 'candidate'),
                'route_document_identity')
        docs[d['id']] = d
    auth = packet['authority']
    rel.shape(auth, {'owner_ref', 'risk', 'mode', 'known_obligations'}, 'route_authority')
    require(rel.text(auth['owner_ref']) and auth['risk'] in ('low', 'high', 'unknown')
            and auth['mode'] in ('read_only', 'advisory', 'none'), 'route_authority_value')
    require(isinstance(auth['known_obligations'], list)
            and all(rel.text(x) for x in auth['known_obligations']), 'route_obligations')
    budget = packet['task_budget']
    rel.shape(budget, {'max_calls', 'max_seconds'}, 'task_budget')
    require(type(budget['max_calls']) is int and 0 <= budget['max_calls'] <= 8
            and number(budget['max_seconds'], 0, 360), 'route_task_budget')
    require(isinstance(packet['issues'], list) and 0 < len(packet['issues']) <= 3, 'route_issue_capacity')
    methods = {m['method'] for m in bindings['methods']}
    ids, all_methods = set(), set()
    for issue in packet['issues']:
        keys = {'id', 'request_ref', 'candidates', 'handling', 'assessability', 'attention'}
        require(isinstance(issue, dict) and keys <= set(issue) <= keys | {'coverage'}, 'invalid_route_issue')
        require(rel.identifier(issue['id']) and issue['id'] not in ids, 'route_issue_identity')
        ids.add(issue['id']); check_ref(issue['request_ref'], docs, source_only=True)
        cs = issue['candidates']
        require(isinstance(cs, list) and len(cs) <= 3 and len(cs) == len(set(cs))
                and set(cs) <= methods, 'route_candidates')
        all_methods.update(cs)
        coverage = issue.get('coverage', {})
        require(isinstance(coverage, dict) and set(coverage) <= set(cs), 'invalid_existing_coverage')
        for resolution in coverage.values():
            require(_resolution(resolution, packet, docs) is True, 'coverage_not_established')
        require(type(issue['attention']) is bool, 'route_attention_flag')
        h = _resolution(issue['handling'], packet, docs)
        require(h is None or h in ('direct_execute', 'judge', 'acquire_fact', 'background'), 'route_handling')
        require(_resolution(issue['assessability'], packet, docs) in (None, True, False), 'route_assessability')
    if all_methods & {'sela', 'mpg'}:
        all_methods.update(('sela', 'mpg'))
    require(len(all_methods) <= 4, 'route_full_method_capacity')
    deps = packet['dependencies']
    require(isinstance(deps, list) and len(deps) <= 6, 'route_dependency_capacity')
    seen = set()
    for edge in deps:
        rel.shape(edge, {'id', 'producer', 'consumer', 'artifact', 'condition', 'refs'}, 'route_dependency')
        require(rel.identifier(edge['id']) and edge['id'] not in seen
                and edge['producer'] in ids and edge['consumer'] in ids
                and edge['producer'] != edge['consumer'] and rel.text(edge['artifact']), 'route_dependency_identity')
        seen.add(edge['id'])
        require(isinstance(edge['refs'], list) and edge['refs'], 'route_dependency_source')
        for ref in edge['refs']: check_ref(ref, docs, source_only=True)
        require(_resolution(edge['condition'], packet, docs) in (None, True, False), 'route_condition')
    if packet['relationship'] is not None:
        require((len(ids) == 1 and packet.get('relationship_issue', next(iter(ids))) in ids)
                or packet.get('relationship_issue') in ids, 'relationship_scope_required')
        r = packet['relationship']
        require(all(r[k] == packet[k] for k in ('episode_id', 'turn_id', 'revision', 'authority')),
                'nested_relationship_identity')
        require(all(d['id'] in docs and docs[d['id']] == d for d in r['documents']), 'nested_relationship_sources')
    return docs


def _read_methods(repo, names, bindings):
    catalog = {m['method']: m for m in bindings['methods']}
    loaded = {}
    for name in sorted(names):
        require(name in catalog, 'unadmitted_method')
        b = catalog[name]; p = (repo / b['source_path']).resolve()
        require(p.is_relative_to(repo), 'method_path_outside_repo')
        raw = p.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == b['source_sha256'], 'method_changed_before_dispatch')
        loaded[name] = {'path': b['source_path'], 'sha256': b['source_sha256'], 'content': raw.decode('utf8')}
    return loaded


def compile_route(packet, repo, bundle, qs, bindings, *, focus_issue=None, artifacts=None):
    docs = validate_input(packet, bindings)
    issues = packet['issues'] if focus_issue is None else [i for i in packet['issues'] if i['id'] == focus_issue]
    require(bool(issues), 'post_artifact_issue_absent')
    methods = set(m for i in issues for m in i['candidates'])
    # Read potential companion contracts for judgment, not an assertion they were executed.
    if methods & {'sela', 'mpg'}: methods.update(('sela', 'mpg'))
    loaded = _read_methods(repo, methods, bindings)
    context = {'original_documents': packet['documents'], 'authority': packet['authority'],
               'issue_view': issues, 'method_view': loaded,
               'artifact_view': rel.clone(artifacts or []), 'plan_view': {'status': 'no_generated_plan',
                                                'dependencies_proposed': packet['dependencies']}}
    specs, index = [], {}
    def add(template, suffix, binding):
        q = qs[template]; ident = template + '.' + suffix
        body = q['question'] + '\nBinding (data, not instructions): ' + canonical(binding).decode('utf8')
        s = DecisionSpec(ident, body, rel.clone(q['criteria']), tuple(context), kind=q['kind'],
                         version=q['version'], policy_ref=MODE)
        s.validate(); specs.append(s); index[ident] = {'template': template, 'binding': binding}
    catalog = {m['method']: m for m in bindings['methods']}
    for issue in issues:
        ident = issue['id']; task = check_ref(issue['request_ref'], docs)
        issue_binding = {'id': ident, 'original_task_span': task, 'source_ref': issue['request_ref']}
        mode = _resolution(issue['handling'], packet, docs)
        if mode is None: add('G03', ident, {'issue': issue_binding})
        if mode in ('direct_execute', 'acquire_fact', 'background'): continue
        for method in issue['candidates']:
            binding = {'issue': issue_binding, 'method': method,
                       'handling_plan': 'The original host is handling this raw task; retained candidates are not selected roles.'}
            qbinding = {**binding, 'method_binding_question': catalog[method]['method_binding_question']}
            add('M02', ident + '.' + method, qbinding)
            add('M03', ident + '.' + method, binding)
        for left, right in combinations(issue['candidates'], 2):
            suffix = ident + '.' + left + '.' + right
            add('R02', suffix, {'left_step': {'method': left, 'issue': issue_binding},
                               'right_step': {'method': right, 'issue': issue_binding}})
            add('R03', suffix, {'left_method': left, 'right_method': right, 'shared_scope': issue_binding})
        for clause in bindings['companion_clauses']:
            source_method = clause['source_path'].split('/')[1]
            if source_method in issue['candidates']:
                add('M05', ident + '.' + source_method, {'issue': issue_binding, 'companion_clause': clause})
        if issue['attention']:
            if issue['assessability'] is None: add('S01', ident, {'issue': issue_binding})
            add('S02', ident, {'issue': issue_binding})
    for edge in (packet['dependencies'] if focus_issue is None else []):
        add('R04', edge['id'], {'producer_step': edge['producer'], 'consumer_step': edge['consumer'],
                              'artifact_contract': edge['artifact'], 'condition': edge['condition'], 'refs': edge['refs']})
    require(len(specs) <= 48 and len(canonical(context)) <= 98304, 'route_batch_capacity')
    identity = {'packet_sha256': digest(packet), 'contract_sha256': digest(bundle)}
    if focus_issue is not None:
        identity.update(focus_issue=focus_issue, accepted_artifacts_sha256=digest(artifacts or []))
    return SimpleNamespace(specs=tuple(specs), context=context, index=index, loaded=loaded, identity=identity)


def _evaluate(ep, directory, compiled, *, name='route', mode=MODE):
    step = directory / 'steps' / name
    timeout = ep.profile['single_call_seconds']
    if compiled.specs and not list((step / 'calls').glob('*/outcome.json')):
        timeout = ep.admit('judgment')
    wrapped = rt._Provider(ep); call = wrapped.evaluate
    wrapped.evaluate = lambda specs, state, seconds: call(specs, state, min(timeout, seconds))
    limits = Limits(max_calls=1, max_seconds=45, max_request_bytes=98304)
    scope = 'route-' + digest(compiled.identity)
    live = None
    if ep.live_admission is not None and compiled.specs:
        from .relationship_live import session_admission
        live = session_admission(ep, compiled, scope, asdict(limits))
        rt.save(step / 'live-admission.json', live)
    # No live Session is required for an explicitly direct zero-inference task.
    if not compiled.specs: return {}
    with Session(step, wrapped, scope=scope, limits=limits, live_admission=live) as session:
        result = session.evaluate(list(compiled.specs), compiled.context)
        session.finish({'id': 'mindthus.route-control', 'version': mode}, compiled.context,
                       {k: asdict(v) for k, v in result.items()})
    return {k: asdict(v) for k, v in result.items()}


def _value(observations, ident):
    row = observations.get(ident, {})
    return row.get('value') if row.get('status') == 'ok' else None


def consume(packet, compiled, observations, bundle, bindings):
    docs = {d['id']: d for d in packet['documents']}
    rows, unresolved, reads = [], [], set()
    for issue in packet['issues']:
        iid = issue['id']; roles = {}; reasons = []; covered = []
        h = _resolution(issue['handling'], packet, docs) or _value(observations, 'G03.' + iid)
        row = {'issue_id': iid, 'mode': 'delegated_unresolved', 'primary': None,
               'supports': [], 'constraints': [], 'attention': {'status': 'unknown'}, 'reason': None}
        if h in ('direct_execute', 'background'): row['mode'] = 'direct'
        elif h == 'acquire_fact': row['mode'] = 'acquire'
        elif h == 'judge':
            for m in issue['candidates']:
                p = _value(observations, 'M02.' + iid + '.' + m)
                role = _value(observations, 'M03.' + iid + '.' + m)
                if p is None or role is None or role == 'unclear': reasons.append('method_observation_unresolved:' + m)
                elif p >= .8:
                    if role in ('primary_candidate', 'support', 'constraint', 'support_and_constraint'): roles[m] = role
                    elif role == 'covered':
                        if m in issue.get('coverage', {}): covered.append(m)
                        else: reasons.append('coverage_needs_existing_output:' + m)
                elif p > .2 or role in ('primary_candidate', 'support', 'constraint', 'support_and_constraint'):
                    reasons.append('applicability_role_unresolved:' + m)
            primaries = [m for m, role in roles.items() if role == 'primary_candidate']
            if len(primaries) > 1:
                winners = []
                for candidate in primaries:
                    wins_all = True
                    for other in primaries:
                        if other == candidate: continue
                        pair = next((l, r) for l, r in combinations(issue['candidates'], 2) if {l, r} == {candidate, other})
                        suffix = iid + '.' + '.'.join(pair)
                        winner = _value(observations, 'R03.' + suffix)
                        wanted = 'left' if candidate == pair[0] else 'right'
                        wins_all &= _value(observations, 'R02.' + suffix) == 'same_scope' and winner == wanted
                    if wins_all: winners.append(candidate)
                primaries = winners if len(winners) == 1 else []
            if len(primaries) == 1 and not reasons:
                row.update(mode='committed', primary=primaries[0],
                           supports=[m for m, r in roles.items() if r in ('support', 'support_and_constraint')],
                           constraints=[m for m, r in roles.items() if r in ('constraint', 'support_and_constraint')])
            elif not primaries and covered and not roles and not reasons:
                row['mode'] = 'direct'
                row['reused_methods'] = covered
            else:
                reasons.append('no_established_primary' if not primaries else 'unresolved_required_candidate')
            for m in issue['candidates']:
                if m in ('sela', 'mpg') and (m in roles or m in covered):
                    v = _value(observations, 'M05.' + iid + '.' + m)
                    if v is not None and v >= .8:
                        reads.add('mpg' if m == 'sela' else 'sela')
                    elif v is None or v > .2:
                        reasons.append('companion_condition_unresolved:' + m)
                        row.update(mode='delegated_unresolved', primary=None, supports=[], constraints=[])
        else: reasons.append('handling_unresolved')
        assessable = _resolution(issue['assessability'], packet, docs)
        p = _value(observations, 'S01.' + iid)
        score = observations.get('S02.' + iid)
        if (assessable is True or (assessable is None and p is not None and p >= .8)) and score:
            distribution = (score.get('uncertainty') or {}).get('probabilities')
            if score['status'] == 'ok' and isinstance(distribution, dict) and set(distribution) == {'0', '1', '2', '3'}:
                row['attention'] = {'status': 'guidance_only', 'value': score['value'], 'distribution': distribution}
        if row['mode'] == 'committed': reads.update([row['primary'], *row['supports'], *row['constraints']])
        if row['mode'] == 'delegated_unresolved':
            row['reason'] = ';'.join(reasons)
            unresolved.append({'issue_id': iid, 'owner': 'original_host', 'reason': row['reason']})
        rows.append(row)
    edges = []
    for edge in packet['dependencies']:
        kind = _value(observations, 'R04.' + edge['id'])
        condition = _resolution(edge['condition'], packet, docs)
        if kind == 'none' or (kind == 'conditional' and condition is False): continue
        edges.append({**edge, 'relation': kind or 'unclear', 'condition_value': condition})
    manifest = {'policy_version': MODE, 'input_hash': digest(packet), 'contract_hashes': bundle['sources'],
                'per_issue': rows, 'mandatory_reads': sorted(reads), 'artifact_edges': edges,
                'reuse': [{'issue_id': i['id'], 'method': m, 'resolution': i['coverage'][m]}
                          for i in packet['issues'] for m in i.get('coverage', {})
                          if m in next(r for r in rows if r['issue_id'] == i['id']).get('reused_methods', [])],
                'unresolved': unresolved, 'source_observations': observations,
                'condition_sources': {i['id']: {'handling': i['handling'], 'assessability': i['assessability']}
                                      for i in packet['issues']},
                'claim_ceiling': 'routing instruction, not evidence, permission or semantic task acceptance'}
    return refresh({'route_id': digest([packet['episode_id'], packet['turn_id'], digest(packet)]), 'revision': 1, **manifest})


def refresh(route):
    modes = [r['mode'] for r in route['per_issue']]
    ready = any(m in ('direct', 'committed') for m in modes)
    pending = any(m in ('acquire', 'delegated_unresolved') for m in modes)
    route['mode'] = ('partial' if ready and pending else 'committed' if 'committed' in modes
                     else 'direct' if ready else 'acquire' if set(modes) == {'acquire'} else 'delegated_unresolved')
    route['unresolved'] = [{'issue_id': r['issue_id'], 'owner': 'original_host', 'reason': r['reason'] or r['mode']}
                           for r in route['per_issue'] if r['mode'] in ('acquire', 'delegated_unresolved')]
    return route


def validate_objection(objection, route, iid, packet):
    rel.shape(objection, {'route_id', 'revision', 'affected_issue_or_step', 'kind', 'original_refs',
                         'claimed_conflict', 'requested_change'}, 'route_objection')
    require(objection['route_id'] == route['route_id'] and objection['revision'] == route['revision']
            and objection['affected_issue_or_step'] == iid, 'objection_scope_or_revision')
    require(objection['kind'] in ('source_or_scope', 'method_boundary', 'new_fact', 'dependency', 'permission'),
            'objection_kind')
    require(rel.text(objection['claimed_conflict']) and rel.text(objection['requested_change'])
            and isinstance(objection['original_refs'], list) and objection['original_refs'], 'objection_evidence_required')
    docs = {d['id']: d for d in packet['documents']}
    for ref in objection['original_refs']: check_ref(ref, docs, source_only=True)


def validate_execution(reply, request, packet):
    rel.shape(reply, {'route_id', 'revision', 'issue_id', 'performed_methods', 'text', 'objection', 'usage'}, 'route_execution')
    require(reply['route_id'] == request['route_id'] and reply['revision'] == request['revision']
            and reply['issue_id'] == request['issue']['issue_id'], 'execution_route_revision_mismatch')
    rt._usage(reply['usage'])
    if reply['objection'] is not None:
        require(reply['performed_methods'] == [], 'objection_is_not_execution')
        validate_objection(reply['objection'], request, reply['issue_id'], packet)
    else:
        require(isinstance(reply['performed_methods'], list)
                and sorted(reply['performed_methods']) == sorted(request['execute_methods']), 'silent_route_override')
        require(rel.text(reply['text']), 'empty_method_artifact')


def _change(route, iid, outcome, packet):
    rel.shape(outcome, {'route_id', 'revision', 'issue_id', 'decision', 'replacement', 'original_refs', 'reason', 'usage'},
              'route_arbitration')
    require(outcome['route_id'] == route['route_id'] and outcome['revision'] == route['revision']
            and outcome['issue_id'] == iid, 'arbitration_scope_or_version')
    require(outcome['decision'] in ('uphold', 'amend', 'acquire', 'unresolved') and rel.text(outcome['reason']),
            'arbitration_decision')
    require(isinstance(outcome['original_refs'], list) and outcome['original_refs'], 'arbitration_basis_required')
    for ref in outcome['original_refs']:
        check_ref(ref, {d['id']: d for d in packet['documents']}, source_only=True)
    rt._usage(outcome['usage'])
    revised = rel.clone(route); row = next(r for r in revised['per_issue'] if r['issue_id'] == iid)
    if outcome['decision'] == 'amend':
        replacement = outcome['replacement']
        rel.shape(replacement, {'primary', 'supports', 'constraints'}, 'route_replacement')
        allowed = set(next(i['candidates'] for i in packet['issues'] if i['id'] == iid))
        require(replacement['primary'] in allowed, 'replacement_primary_outside_candidates')
        for name in ('supports', 'constraints'):
            require(isinstance(replacement[name], list) and len(replacement[name]) == len(set(replacement[name]))
                    and set(replacement[name]) <= allowed and replacement['primary'] not in replacement[name],
                    'replacement_roles')
        row.update(mode='committed', reason=None, **replacement)
    elif outcome['decision'] in ('acquire', 'unresolved'):
        row.update(mode='acquire' if outcome['decision'] == 'acquire' else 'delegated_unresolved',
                   primary=None, supports=[], constraints=[], reason=outcome['reason'])
    else: require(outcome['replacement'] is None, 'uphold_cannot_amend')
    revised['revision'] += 1
    revised['parent_commitment_sha256'] = digest(route)
    revised['amendment'] = outcome
    return refresh(revised)



def _after_artifacts(ep, directory, packet, route, iid, needed, outputs, bundle, qs, bindings):
    """Re-evaluate only a waiting consumer against actually accepted predecessor outputs.

    These are host artifacts accepted for a named use, not newly verified external facts.
    The existing Episode/Session reserves and replays this additional batch.
    """
    artifacts = []
    for edge in needed:
        output = outputs[edge['producer']]
        acceptance = output['accepted_uses'][edge['id']]
        require(acceptance['accepted'] is True and acceptance['artifact_sha256'] == output['artifact_sha256']
                and acceptance['dependency_id'] == edge['id'], 'post_artifact_acceptance_required')
        artifacts.append({'producer_issue': edge['producer'], 'consumer_issue': iid,
                          'artifact_contract': edge['artifact'], 'dependency_id': edge['id'],
                          'text': output['text'], 'artifact_sha256': output['artifact_sha256'],
                          'acceptance': acceptance,
                          'provenance': 'original_host_output_accepted_for_this_use_not_independent_fact'})
    compiled = compile_route(packet, ep.repo, bundle, qs, bindings, focus_issue=iid, artifacts=artifacts)
    name = 'route__after__' + iid + '__' + digest(compiled.identity)[:16]
    observations = _evaluate(ep, directory, compiled, name=name)
    # Consumption is restricted to this issue. Original source documents and boundaries stay identical.
    local_packet = {**packet, 'issues': [i for i in packet['issues'] if i['id'] == iid], 'dependencies': []}
    local_route = consume(local_packet, compiled, observations, bundle, bindings)
    changed = rel.clone(route)
    old = next(r for r in route['per_issue'] if r['issue_id'] == iid)
    new = local_route['per_issue'][0]
    changed['per_issue'] = [new if r['issue_id'] == iid else r for r in changed['per_issue']]
    changed['mandatory_reads'] = sorted(set(changed['mandatory_reads']) | set(local_route['mandatory_reads']))
    changed['source_observations'].update(observations)
    changed['revision'] += 1
    changed['parent_commitment_sha256'] = digest(route)
    changed.setdefault('post_artifact_evaluations', []).append({
        'issue_id': iid, 'step': name, 'prior_scope': old,
        'accepted_artifacts_sha256': digest(artifacts), 'observations': observations})
    refresh(changed)
    rt.save(directory / ('commitment-' + str(changed['revision']) + '.json'), changed)
    return changed


def _admission(admission, root, packet, provider, bundle, hooks):
    require(isinstance(admission, dict) and admission.get('schema') == 'mindthus.route-control-live.v1',
            'route_live_admission_required')
    require(admission['root'] == str(root) and admission['mode'] == MODE
            and admission['implementation'] == implementation_digest()
            and admission['source_bindings'] == bundle['sources']
            and admission['provider'] == provider_configuration(provider), 'route_live_identity')
    require(digest(packet) in admission['packet_hashes'] and rel.text(admission['authorization_ref']), 'route_input_not_admitted')
    caps = admission['ceilings']
    for key, maximum in {'judgments': 4, 'corrections': 1, 'organize': 1, 'arbitrations': 1, 'requests': 7,
                         'executions': packet['task_budget']['max_calls']}.items():
        require(type(caps[key]) is int and 0 <= caps[key] <= maximum, 'route_live_budget')
    require(number(caps['reserve_per_jev_usd'], .000001, .25), 'route_live_reserve')
    for name, hook in hooks.items():
        require(admission[name] == (hook.configuration if hook else None), 'route_live_host_configuration')
        if hook:
            require(hook.configuration.get('model') != 'deepseek-v4.1-flash'
                    or hook.configuration.get('reasoning_effort') == 'max', 'deepseek_max_required')


def run(root, provider, data, repo, *, executor=None, arbitrator=None, corrector=None,
        recheck=True, live_admission=None, artifact_acceptor=None):
    repo, root = Path(repo).resolve(), Path(root).resolve(); packet = rel.clone(data)
    require(not root.is_relative_to(repo), 'state_root_inside_repository')
    bundle, qs, bindings = load_policy(repo); validate_input(packet, bindings)
    require(type(recheck) is bool, 'recheck_flag_required')
    live = live_admission is not None
    require(getattr(provider, 'is_live', None) is live, 'route_live_not_admitted')
    owner = packet['authority']['owner_ref']
    hooks = {'executor': executor, 'arbitrator': arbitrator, 'corrector': corrector, 'organizer': None}
    for name, hook in hooks.items():
        if hook:
            expected = owner + ':route-arbitrator' if name == 'arbitrator' else owner
            require(hook.identity == expected and (is_current_host(hook) or
                    getattr(hook, 'is_live', None) is live), 'route_host_identity')
    if arbitrator: require(arbitrator is not executor, 'executor_cannot_self_approve')
    if artifact_acceptor is not None:
        require(artifact_acceptor.identity == owner, 'artifact_acceptance_owner')
    if live: _admission(live_admission, root, packet, provider, bundle, hooks)
    profile = {**PROFILE, 'executions_total': packet['task_budget']['max_calls'],
               'execution_seconds': packet['task_budget']['max_seconds']}
    with rt.Episode(root, repo, provider, packet, bundle, live_admission, mode=MODE,
                    profile=profile, kinds=STEP_KINDS, host_slots=HOST_SLOTS) as ep:
        directory = root / 'turns' / ep.turn_key / 'inputs' / digest(packet)
        require(all(x['directory'] == str(directory) for x in ep.tally()['pending_host']),
                'pending_current_host_input_must_be_resumed')
        binding = {'packet': packet, 'episode_manifest_sha256': digest(ep.manifest), 'recheck': recheck,
                   'hooks': {k: {'identity': h.identity, 'configuration': getattr(h, 'configuration', None)} if h else None
                             for k, h in hooks.items()},
                   'artifact_acceptor': getattr(artifact_acceptor, 'configuration', None)}
        rt.save(root / 'turns' / ep.turn_key / 'versions' / (digest(packet['revision']) + '.json'), binding)
        rt.save(directory / 'manifest.json', binding)
        summary = directory / 'summary.json'
        if summary.exists(): return {**read_record(summary), 'source_ref': str(summary)}
        route = None; outputs = {}; pending = {}; relation_result = None; relation_issue = None
        relationship_pending = None
        def finish(reason=None, terminal=True):
            state = ep.tally()
            out = {'schema': 'mindthus.route-control-result.v1', 'mode': MODE, 'route': route,
                   'outputs': outputs, 'pending': pending, 'reason': reason, 'relationship': relation_result,
                   'original_input': packet, 'counts': state['counts'], 'usage': state['usage'],
                   'plugin_request_seconds': state['seconds'], 'method_request_seconds': state.get('execution_seconds', 0),
                   'evidence_kind': ep.evidence_kind, 'control_surface': 'programmatic_load_dispatch_receipt',
                   'native_plugin_activation': 'not_claimed', 'semantic_method_fidelity': 'not_verified_by_receipt',
                   'task_complete': False, 'qualification': False,
                   'host_transport': 'current_agent' if is_current_host(executor) else 'callback',
                   'pending_host_requests': state['pending_host'], 'reserved_counts': state['reserved_counts']}
            if terminal: rt.save(summary, out)
            return {**out, 'source_ref': str(summary if terminal else directory / 'manifest.json')}
        try:
            if packet['authority']['risk'] != 'low' or packet['authority']['mode'] == 'none':
                return finish('outside_low_risk_opt_in')
            if ep.tally()['failures']: return finish('terminal_prior_failure')
            if packet['relationship'] is not None:
                relation_issue = packet.get('relationship_issue', packet['issues'][0]['id'])
                rpacket = packet['relationship']; c, _ = rel.load_contract(repo)
                rt._raw_validate(rpacket, c)
                require(rpacket['proposal'] is not None, 'route_relationship_requires_existing_proposal')
                initial = rt._judge(ep, directory, rpacket, 'relation__initial')
                relation_result = {'initial': initial, 'revised': None, 'recheck': None}
                if initial['result']['action'] == 'request_correction':
                    if corrector is None: return finish('awaiting_corrector', terminal=False)
                    request = rt.correction_request(rpacket, initial)
                    out = rt._host(ep, directory, 'correction', request, corrector,
                                   lambda reply: rt.revision_packet(request, reply, repo))
                    if out['status'] != 'complete': return finish('correction_failed')
                    revised = rt.revision_packet(request, out['reply'], repo)
                    relation_result['revised'] = revised
                    if recheck:
                        relation_result['recheck'] = rt._judge(ep, directory, revised, 'relation__recheck')
                # The corrected candidate is not promoted to new evidence. Raw routing sources remain intact.
            compiled = compile_route(packet, repo, bundle, qs, bindings)
            rt.save(directory / 'judgment-contract-loads.json', compiled.loaded)
            observations = _evaluate(ep, directory, compiled)
            route = consume(packet, compiled, observations, bundle, bindings)
            if relation_result:
                latest = relation_result.get('recheck') or relation_result['initial']
                action = latest['result']['action']
                if action != 'continue_original':
                    relationship_pending = ('relationship_correction_unverified'
                        if relation_result['revised'] is not None and relation_result['recheck'] is None
                        else 'relationship_correction_unresolved' if action == 'request_correction'
                        else 'relationship_scope_unresolved')
                    affected = next(x for x in route['per_issue'] if x['issue_id'] == relation_issue)
                    affected.update(mode='delegated_unresolved', primary=None, supports=[], constraints=[],
                                    reason=relationship_pending)
                    refresh(route)
            route['engine_identity'] = ep.manifest['provider']
            rt.save(directory / 'commitment-1.json', route)
            dispatch_order = [i['id'] for i in packet['issues']]
            accepted = {}; waiting = set(dispatch_order); advanced = set()
            while waiting:
                progressed = False
                for iid in dispatch_order:
                    if iid not in waiting: continue
                    row = next(r for r in route['per_issue'] if r['issue_id'] == iid)
                    # Accepted predecessor artifacts resolve their dependency only;
                    # they cannot discharge a separate candidate-correction finding.
                    if iid == relation_issue and relationship_pending:
                        pending[iid] = relationship_pending
                        waiting.remove(iid); progressed = True; continue
                    needed = [e for e in route['artifact_edges'] if e['consumer'] == iid]
                    if any(e['relation'] == 'unclear' or (e['relation'] == 'conditional' and e['condition_value'] is not True)
                           for e in needed):
                        pending[iid] = 'dependency_unresolved'; waiting.remove(iid); progressed = True; continue
                    if needed and row['mode'] in ('committed', 'delegated_unresolved'):
                        if any(e['producer'] not in accepted or not accepted[e['producer']].get(e['id']) for e in needed):
                            continue
                        if row['mode'] == 'delegated_unresolved' and iid not in advanced:
                            route = _after_artifacts(ep, directory, packet, route, iid, needed, outputs, bundle, qs, bindings)
                            advanced.add(iid)
                            row = next(r for r in route['per_issue'] if r['issue_id'] == iid)
                    if row['mode'] not in ('committed', 'direct'):
                        pending[iid] = row['reason'] or row['mode']; waiting.remove(iid); progressed = True; continue
                    if any(e['producer'] not in accepted or not accepted[e['producer']].get(e['id']) for e in needed): continue
                    if executor is None:
                        pending[iid] = 'executor_not_supplied'; waiting.remove(iid); progressed = True; continue
                    for attempt in range(2):
                        row = next(r for r in route['per_issue'] if r['issue_id'] == iid)
                        methods = sorted({row['primary'], *row['supports'], *row['constraints']} - {None})
                        names = set(methods) | set(route['mandatory_reads'])
                        loaded = _read_methods(repo, names, bindings)
                        request = {'mode': MODE, 'policy': MODE, 'route_id': route['route_id'], 'revision': route['revision'],
                                   'issue': row, 'execute_methods': methods, 'loaded_methods': loaded,
                                   'original_input': packet, 'prior_outputs': outputs,
                                   'relationship': relation_result if iid == relation_issue else None,
                                   'authority': packet['authority'],
                                   'instruction': 'Execute this committed scope. Do not freely reroute. Return a source-backed scoped objection when needed; preserve uncertainty and original facts.'}
                        request['request_id'] = digest(request)
                        step = 'execution__' + iid + '__' + str(route['revision'])
                        rt.save(directory / 'dispatch' / (step + '.json'),
                                {'request_id': request['request_id'], 'route_sha256': digest(route), 'loads': loaded})
                        out = rt._host(ep, directory, step, request, executor,
                                       lambda reply: validate_execution(reply, request, packet), operation='execute', expected_owner=owner)
                        if out['status'] != 'complete': pending[iid] = 'execution_failed_or_noncompliant'; break
                        reply = out['reply']
                        if reply['objection'] is None:
                            outputs[iid] = {'route_id': route['route_id'], 'revision': route['revision'], 'text': reply['text'],
                                            'methods': methods, 'artifact_sha256': digest(reply['text']), 'accepted_uses': {}}
                            accepted[iid] = {}
                            for edge in route['artifact_edges']:
                                if edge['producer'] == iid and artifact_acceptor:
                                    ap = directory / 'accepted' / (edge['id'] + '.json')
                                    receipt = read_record(ap) if ap.exists() else artifact_acceptor.accept(edge, outputs[iid], packet)
                                    require(isinstance(receipt, dict) and receipt.get('owner_ref') == owner
                                            and receipt.get('artifact_sha256') == outputs[iid]['artifact_sha256']
                                            and receipt.get('dependency_id') == edge['id'] and type(receipt.get('accepted')) is bool,
                                            'artifact_acceptance_receipt')
                                    rt.save(ap, receipt); accepted[iid][edge['id']] = receipt['accepted']
                                    outputs[iid]['accepted_uses'][edge['id']] = receipt
                            break
                        if arbitrator is None or attempt:
                            pending[iid] = 'objection_requires_original_owner'; break
                        ar = {'mode': MODE, 'policy': MODE, 'route_id': route['route_id'], 'revision': route['revision'],
                              'issue_id': iid, 'objection': reply['objection'], 'route': route,
                              'original_input': packet, 'method_contracts': compiled.loaded,
                              'instruction': 'Independently check the named objection only. Retain unrelated scopes and permissions.'}
                        if out.get('host_context_ref'):
                            ar['executor_context_ref'] = out['host_context_ref']
                        ar['request_id'] = digest(ar)
                        adjudicated = rt._host(ep, directory, 'arbitration', ar, arbitrator,
                                               lambda result: _change(route, iid, result, packet),
                                               operation='arbitrate', expected_owner=owner + ':route-arbitrator')
                        if adjudicated['status'] != 'complete': pending[iid] = 'arbitration_failed'; break
                        route = _change(route, iid, adjudicated['reply'], packet)
                        rt.save(directory / ('commitment-' + str(route['revision']) + '.json'), route)
                        if next(r for r in route['per_issue'] if r['issue_id'] == iid)['mode'] not in ('committed', 'direct'):
                            pending[iid] = 'objection_scope_delegated'; break
                    waiting.remove(iid); progressed = True
                if not progressed:
                    pending.update({i: 'dependency_waiting_or_cycle' for i in waiting}); break
            return finish()
        except AwaitingCurrentAgent as exc:
            result = finish('awaiting_current_agent', terminal=False)
            return {**result, 'status': 'awaiting_current_agent', 'host_request': exc.handoff_path}
        except rt.EpisodeStop as exc:
            return finish(str(exc))
