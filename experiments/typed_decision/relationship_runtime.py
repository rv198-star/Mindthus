"""D2/D3 persistence for the existing entry's explicit relationship mode.

D1 owns semantics; Session owns judgment receipts. This module owns the episode
lock, aggregate allowances and host receipts. Live requires frozen D3 admission.
"""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import asdict
from pathlib import Path
import fcntl
import subprocess
import time

from . import relationship_assessment as relation
from .contracts import BatchResult, ContractError, canonical, digest, number, provider_configuration, require
from .providers import ProviderError
from .session import Limits, RecoveryRequired, Session, implementation_digest, read_record, write_once

MODE = 'relationship-frame.v1'
VERSION = '1'
PROFILE = {'judgments_total': 4, 'judgments_per_turn': 2,
           'corrections_total': 2, 'corrections_per_turn': 1,
           'structural_organize': 1, 'total_requests': 7,
           'request_seconds': 120, 'single_call_seconds': 45,
           'paid_calls_authorized': 0, 'host_output_bytes': 32768}
KINDS = {'initial': 'judgment', 'recheck': 'judgment',
         'correction': 'correction', 'organize': 'organize'}
UNKNOWN_USAGE = {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}


class EpisodeStop(Exception):
    """Return current input to the original owner without a new invocation."""


def save(path: Path, payload: dict) -> dict:
    if path.exists():
        require(read_record(path) == payload, 'immutable_relationship_record_changed')
    else:
        write_once(path, payload)
    return payload


def _registry(repo: Path) -> Path:
    common = subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=repo,
                                     text=True, stderr=subprocess.PIPE).strip()
    project = str((repo / common).resolve())
    return Path.home() / '.local/state/mindthus/relationship-episodes' / digest(project)


@contextmanager
def _locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RecoveryRequired('relationship_episode_already_running') from None
        yield


class Episode:
    def __init__(self, root: Path, repo: Path, provider, packet: dict, contract: dict, live_admission=None):
        self.root, self.repo, self.provider = root, repo, provider
        self.live_admission = relation.clone(live_admission) if live_admission is not None else None
        self.evidence_kind = "live_model" if self.live_admission is not None else "offline_fixture"
        self.turn_key = digest(packet['turn_id'])
        self.manifest = {'schema': 'mindthus.relationship-episode.v1', 'mode': MODE,
                         'episode_id': packet['episode_id'], 'profile': relation.clone(PROFILE),
                         'implementation': implementation_digest(),
                         'provider': provider_configuration(provider),
                         'owner_ref': packet['authority']['owner_ref'],
                         'contract_sha256': digest(contract), 'sources': contract['sources']}
        if self.live_admission is not None:
            self.manifest["live_admission"] = self.live_admission
        self.stack = ExitStack()

    def __enter__(self):
        registry = _registry(self.repo)
        key = digest(self.manifest['episode_id'])
        try:
            self.stack.enter_context(_locked(registry / (key + '.lock')))
            binding = {'root': str(self.root), 'episode_id': self.manifest['episode_id'], 'mode': MODE}
            binding_path = registry / (key + '.json')
            if binding_path.exists():
                require(read_record(binding_path) == binding, 'episode_root_changed')
                require((self.root / 'manifest.json').exists(), 'registered_episode_ledger_missing')
            self.stack.enter_context(_locked(self.root / '.entry-lock'))
            mp = self.root / 'manifest.json'
            if not mp.exists():
                require(not any(p.name != '.entry-lock' for p in self.root.iterdir()),
                        'nonempty_unbound_episode_root')
            save(mp, self.manifest)
            save(binding_path, binding)
            self.started = time.monotonic()
            self.start_seconds = self.tally()['seconds']
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *args):
        self.stack.close()

    def bind_runtime(self, runtime):
        self.provider.validate_runtime(runtime)
        save(self.root / 'resolved-runtime.json', runtime.to_dict())

    def tally(self) -> dict:
        counts = {'judgment': 0, 'correction': 0, 'organize': 0, 'total': 0}
        turn_counts = {k: 0 for k in counts}
        rows, failures = [], []
        intents = sorted(self.root.glob('turns/*/inputs/*/steps/*/calls/*/intent.json'))
        intents += sorted(self.root.glob('turns/*/inputs/*/steps/*/intent.json'))
        # Orphan results would make budget accounting untrustworthy.
        for outcome in self.root.glob('turns/*/inputs/*/steps/**/outcome.json'):
            require(outcome.with_name('intent.json').exists(), 'outcome_without_intent')
        for ip in intents:
            parts = ip.relative_to(self.root).parts
            kind = KINDS[parts[5]]
            read_record(ip)
            op = ip.with_name('outcome.json')
            if not op.exists():
                raise RecoveryRequired('unresolved_relationship_call:' + str(ip.relative_to(self.root)))
            out = read_record(op)
            require(out.get('evidence_kind') == self.evidence_kind, 'unexpected_evidence_kind')
            elapsed = out.get('elapsed_seconds')
            require(number(elapsed, 0, 86400), 'invalid_recorded_request_seconds')
            counts[kind] += 1
            counts['total'] += 1
            if parts[1] == self.turn_key:
                turn_counts[kind] += 1
                turn_counts['total'] += 1
            usage = out['usage'] if kind == 'judgment' else out.get('usage', UNKNOWN_USAGE)
            _usage(usage)
            rows.append({'kind': kind, 'seconds': elapsed, 'usage': usage})
            if self.live_admission is not None:
                cap = self.live_admission['ceilings']
                if kind == 'judgment' and usage['cost_usd'] is not None and usage['cost_usd'] > cap['reserve_per_jev_usd']:
                    failures.append(str(op.relative_to(self.root)))
                if kind != 'judgment':
                    slot = 'organizer' if kind == 'organize' else 'corrector'
                    require(out.get('host_configuration') == self.live_admission[slot], 'recorded_host_drift')
            if kind == 'judgment':
                if any(r['status'] == 'provider_error' for r in out['results'].values()):
                    failures.append(str(op.relative_to(self.root)))
                if out.get('resolved_runtime') is not None:
                    shared = self.root / 'resolved-runtime.json'
                    require(shared.exists() and read_record(shared) == out['resolved_runtime'],
                            'cross_turn_resolved_runtime_changed')
            elif out['status'] != 'complete':
                failures.append(str(op.relative_to(self.root)))
        return {'counts': counts, 'turn_counts': turn_counts,
                'seconds': sum(r['seconds'] for r in rows), 'failures': failures,
                'usage': {k: sum(r['usage'][k] for r in rows)
                          if rows and all(r['usage'][k] is not None for r in rows) else None
                          for k in UNKNOWN_USAGE}}

    def remaining(self) -> float:
        used = max(self.tally()['seconds'], self.start_seconds + time.monotonic() - self.started)
        return PROFILE['request_seconds'] - used

    def admit(self, kind: str) -> float:
        state = self.tally()
        if state['failures']:
            raise EpisodeStop('terminal_technical_failure')
        counts, turn = state['counts'], state['turn_counts']
        if self.live_admission is not None:
            cap = self.live_admission['ceilings']
            slot = {'judgment': 'judgments', 'correction': 'corrections', 'organize': 'organize'}[kind]
            if counts['total'] >= cap['requests'] or counts[kind] >= cap[slot]:
                raise EpisodeStop('live_admission_budget_exhausted')
        ceilings = {'judgment': 'judgments_total', 'correction': 'corrections_total',
                    'organize': 'structural_organize'}
        if counts['total'] >= PROFILE['total_requests'] or counts[kind] >= PROFILE[ceilings[kind]]:
            raise EpisodeStop('episode_' + kind + '_budget_exhausted')
        turn_ceiling = {'judgment': 'judgments_per_turn', 'correction': 'corrections_per_turn'}
        if kind in turn_ceiling and turn[kind] >= PROFILE[turn_ceiling[kind]]:
            raise EpisodeStop('turn_' + kind + '_budget_exhausted')
        remaining = self.remaining()
        if remaining <= 0:
            raise EpisodeStop('request_time_budget_exhausted')
        return min(PROFILE['single_call_seconds'], remaining)


class _Provider:
    def __init__(self, episode: Episode):
        self.episode, self.wrapped = episode, episode.provider

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def evaluate(self, specs, context, timeout):
        begin = time.monotonic()
        batch = self.wrapped.evaluate(specs, context, timeout)
        require(isinstance(batch, BatchResult), 'invalid_relationship_batch')
        batch.validate(specs)
        if batch.resolved_runtime is not None:
            self.episode.bind_runtime(batch.resolved_runtime)
        if time.monotonic() - begin > timeout:
            raise ProviderError('deadline_exceeded')
        return batch


def _usage(value):
    relation.shape(value, set(UNKNOWN_USAGE), 'usage')
    require(all(v is None or (number(v, 0, 1e15) and (k == 'cost_usd' or type(v) is int))
                for k, v in value.items()), 'invalid_host_usage')


def _raw_validate(packet: dict, contract: dict):
    """Validate incomplete organizer input without inventing a model-visible frame."""
    relation.shape(packet, {'schema', 'episode_id', 'turn_id', 'revision', 'stage', 'documents',
                            'proposal', 'authority', 'activation'}, 'raw_packet')
    require(packet['schema'] == 'relationship-input.v1' and packet['stage'] in ('S0', 'S1'),
            'entry_requires_original_S0_or_S1')
    require(all(relation.text(packet[k]) for k in ('episode_id', 'turn_id', 'revision')), 'raw_identity')
    require(len(canonical(packet)) <= contract['budgets']['input_bytes'], 'coverage_overflow:input_bytes')
    docs = packet['documents']
    require(isinstance(docs, list) and 0 < len(docs) <= contract['budgets']['documents'],
            'coverage_overflow:documents')
    ids = set()
    for doc in docs:
        relation.shape(doc, {'id', 'revision', 'kind', 'text'}, 'document')
        require(relation.identifier(doc['id']) and doc['id'] not in ids, 'document_identity')
        ids.add(doc['id'])
        require(relation.text(doc['revision']) and relation.text(doc['text']) and
                doc['kind'] in ('user', 'assistant', 'source', 'candidate'), 'raw_document')
    auth = packet['authority']
    relation.shape(auth, {'owner_ref', 'risk', 'mode', 'known_obligations'}, 'authority')
    require(relation.text(auth['owner_ref']) and auth['risk'] in ('low', 'high', 'unknown')
            and auth['mode'] in ('advisory', 'read_only', 'none'), 'raw_authority')
    require(isinstance(auth['known_obligations'], list) and
            all(relation.text(x) for x in auth['known_obligations']), 'raw_obligations')
    a = packet['activation']
    relation.shape(a, {'enabled', 'source_refs', 'reason'}, 'activation')
    require(type(a['enabled']) is bool and relation.text(a['reason']), 'raw_activation')
    require(isinstance(a['source_refs'], list) and len(a['source_refs']) <= 2
            and (a['source_refs'] or not a['enabled']), 'raw_activation_refs')
    by_id = {d['id']: d for d in docs}
    for ref in a['source_refs']:
        relation.shape(ref, relation.REF_FIELDS, 'activation_ref')
        require(ref['document_id'] in by_id and
                relation.quote(by_id[ref['document_id']], ref['start'], ref['end']) == ref,
                'raw_activation_quote')


def _judge(ep: Episode, directory: Path, packet: dict, name: str) -> dict:
    compiled = relation.compile_packet(packet, ep.repo)
    step = directory / 'steps' / name
    rp = step / 'report.json'
    if rp.exists():
        report = read_record(rp)
        require(report['result']['identity'] == compiled.identity, 'cached_assessment_input_changed')
        return report
    existing = list((step / 'calls').glob('*/outcome.json'))
    if compiled.specs and not existing:
        timeout = ep.admit('judgment')
    else:
        timeout = PROFILE['single_call_seconds']
    # Session policy is fixed, while the transport receives the current aggregate time limit.
    wrapped = _Provider(ep)
    original_evaluate = wrapped.evaluate
    wrapped.evaluate = lambda specs, context, seconds: original_evaluate(specs, context, min(seconds, timeout))
    scope = 'relationship-' + digest([packet, name])
    limits = Limits(max_calls=1, max_seconds=45, max_request_bytes=49152)
    live = None
    if ep.live_admission is not None:
        from .relationship_live import session_admission
        live = session_admission(ep, compiled, scope, asdict(limits))
        save(step / 'live-admission.json', live)
    with Session(step, wrapped, scope=scope, limits=limits, live_admission=live) as session:
        if live is None:
            report = relation.assess_offline(session, packet, ep.repo)
        else:
            answers = session.evaluate(list(compiled.specs), compiled.context) if compiled.specs else {}
            result = relation.consume(compiled, {'identity': compiled.identity,
                'results': {k: asdict(v) for k, v in answers.items()}}, ep.repo)
            graph = {'id': 'mindthus.relationship-frame', 'version': relation.VERSION,
                     'contract_sha256': compiled.identity['contract_sha256'],
                     'source_bindings': compiled.identity['sources']}
            report = session.finish(graph, packet, result)
    stable = {k: report[k] for k in ('identity', 'run_id', 'result', 'call_keys', 'source_ref', 'trial_usage')}
    return save(rp, stable)


def correction_request(packet: dict, report: dict) -> dict:
    plan = report['result']['plan']
    target = packet['proposal']['candidate']['ref']
    doc = next(d for d in packet['documents'] if d['id'] == target['document_id'])
    seed = digest([packet, plan])
    body = {'schema': 'mindthus.relationship-host-request.v1', 'mode': MODE, 'policy': relation.POLICY,
            'original_input': relation.clone(packet), 'plan': relation.clone(plan),
            'current_target': {'text': doc['text'][target['start']:target['end']], 'version': doc['revision']},
            'revision_document_id': 'R' + seed[:24], 'owner_ref': packet['authority']['owner_ref'],
            'boundary': 'Revise this candidate once; preserve source text, scope, permissions and obligations. '
                        'Return updated proposal references; execute no tools and claim no task acceptance.'}
    return {'request_id': digest(body), **body}


def _same_except_target_refs(old, new, old_id, new_doc):
    if isinstance(old, dict) and set(old) == relation.REF_FIELDS and old['document_id'] == old_id:
        relation.shape(new, relation.REF_FIELDS, 'rebound_reference')
        require(new['document_id'] == new_doc['id'] and
                relation.quote(new_doc, new['start'], new['end']) == new, 'stale_candidate_reference')
    elif isinstance(old, dict):
        require(isinstance(new, dict) and set(old) == set(new), 'proposal_membership_changed')
        for k in old:
            _same_except_target_refs(old[k], new[k], old_id, new_doc)
    elif isinstance(old, list):
        require(isinstance(new, list) and len(old) == len(new), 'proposal_relationships_removed')
        for x, y in zip(old, new):
            _same_except_target_refs(x, y, old_id, new_doc)
    else:
        require(old == new, 'original_proposal_semantics_changed')


def revision_packet(request: dict, reply: dict, repo: Path) -> dict:
    relation.shape(reply, {'text', 'version', 'receipt_ref', 'usage', 'proposal'}, 'correction_reply')
    require(all(relation.text(reply[k]) for k in ('text', 'version', 'receipt_ref')), 'empty_correction')
    _usage(reply['usage'])
    require(reply['version'] != request['current_target']['version'] and
            reply['text'] != request['current_target']['text'], 'unchanged_correction')
    packet = relation.clone(request['original_input'])
    old_id = packet['proposal']['candidate']['ref']['document_id']
    doc = {'id': request['revision_document_id'], 'revision': reply['version'],
           'kind': 'candidate', 'text': reply['text']}
    require(doc['id'] not in {d['id'] for d in packet['documents']}, 'revision_document_collision')
    p = reply['proposal']
    require(isinstance(p, dict) and set(p) == set(packet['proposal']), 'revision_proposal_shape')
    for k in packet['proposal']:
        if k != 'candidate':
            _same_except_target_refs(packet['proposal'][k], p[k], old_id, doc)
    require(isinstance(p['candidate'], dict) and p['candidate'].get('ref') == relation.quote(doc),
            'revised_candidate_must_reference_new_document')
    packet['documents'].append(doc)
    packet.update(proposal=relation.clone(p), stage='S2', revision=digest([packet['revision'], request['request_id'], reply]))
    relation.compile_packet(packet, repo)
    return packet


def _host(ep: Episode, directory: Path, kind: str, request: dict, hook, validator) -> dict:
    step = directory / 'steps' / kind
    ip, op = step / 'intent.json', step / 'outcome.json'
    expected_owner = ep.manifest['owner_ref'] + (':organizer' if kind == 'organize' else '')
    intent = {'mode': MODE, 'policy': relation.POLICY, 'request_id': request['request_id'],
              'request_sha256': digest(request), 'owner_ref': expected_owner,
              'profile_sha256': digest(PROFILE), 'output_bytes': PROFILE['host_output_bytes']}
    if ep.live_admission is not None:
        slot = 'organizer' if kind == 'organize' else 'corrector'
        intent['host_configuration'] = ep.live_admission[slot]
        if hook is not None:
            require(hook.configuration == ep.live_admission[slot], 'host_configuration_changed')
            body = hook.wire_body(request)
            from .relationship_live import no_secrets
            no_secrets(body)
            intent['wire_request_sha256'] = digest(body)
            save(step / 'wire-request.json', body)
        elif ip.exists():
            intent['wire_request_sha256'] = read_record(ip)['wire_request_sha256']
    save(step / 'request.json', request)
    if op.exists():
        require(ip.exists() and read_record(ip) == intent, 'host_request_identity_changed')
        outcome = read_record(op)
        if outcome['status'] == 'complete':
            validator(outcome['reply'])
        return outcome
    if ip.exists():
        raise RecoveryRequired('unresolved_host_' + kind)
    require(hook is not None and getattr(hook, 'is_live', None) is (ep.live_admission is not None)
            and hook.identity == expected_owner, 'offline_host_identity_required')
    timeout = ep.admit(kind)
    save(ip, intent)
    begin = time.monotonic()
    out = {'status': 'failed', 'reply': None, 'error': None, 'usage': relation.clone(UNKNOWN_USAGE),
           'mode': MODE, 'policy': relation.POLICY, 'evidence_kind': ep.evidence_kind}
    try:
        if ep.live_admission is not None:
            hook.last_receipt = None
        fn = hook.organize if kind == 'organize' else hook.correct
        reply = fn(relation.clone(request), timeout)
        require(len(canonical(reply)) <= PROFILE['host_output_bytes'], 'host_output_overflow')
        validator(reply)
        require(time.monotonic() - begin <= timeout, 'host_deadline_exceeded')
        out.update(status='complete', reply=relation.clone(reply), usage=relation.clone(reply['usage']))
    except Exception as exc:
        out['error'] = type(exc).__name__  # Never store arbitrary hook/remote text.
    if ep.live_admission is not None:
        out['host_configuration'] = ep.live_admission[slot]
        receipt = getattr(hook, 'last_receipt', None)
        if receipt is not None:
            from .relationship_live import no_secrets
            no_secrets(receipt)
            out['transport_receipt'] = relation.clone(receipt)
            out['usage'] = relation.clone(receipt['usage'])
    out['elapsed_seconds'] = time.monotonic() - begin
    return save(op, out)


def run(root: Path, provider, data: dict, repo: Path, *, corrector=None, organizer=None, recheck=True, live_admission=None) -> dict:
    """Same entry mode; live is possible only through the explicit D3 admission."""
    live = live_admission is not None
    require(getattr(provider, 'is_live', None) is live, 'relationship_live_not_admitted')
    require(type(recheck) is bool, 'recheck_flag_required')
    require(all(h is None or getattr(h, 'is_live', None) is live for h in (corrector, organizer)),
            'relationship_host_live_not_admitted')
    root, repo = Path(root).resolve(), Path(repo).resolve()
    require(not root.is_relative_to(repo), 'state_root_inside_repository')
    contract, _ = relation.load_contract(repo)
    require(all(contract['budgets'][k] == v for k, v in PROFILE.items() if k != 'host_output_bytes'),
            'relationship_profile_contract_changed')
    packet = relation.clone(data)
    if live:
        from .relationship_live import validate_admission
        validate_admission(live_admission, root, repo, provider, packet, contract, PROFILE,
                           corrector, organizer, recheck)
    try:
        _raw_validate(packet, contract)
    except ContractError as exc:
        if not str(exc).startswith('coverage_overflow:'):
            raise
        return {'schema': 'mindthus.relationship-entry-result.v1', 'mode': MODE,
                'status': 'returned_to_owner', 'reason': str(exc), 'original_input': packet,
                'action': 'return_original_owner', 'source_ref': None, 'new_calls': 0,
                'task_complete': False, 'qualification': False, 'evidence_kind': 'live_model' if live else 'offline_fixture'}
    owner = packet['authority']['owner_ref']
    for hook, identity in ((corrector, owner), (organizer, owner + ':organizer')):
        require(hook is None or hook.identity == identity, 'relationship_hook_owner_changed')
    with Episode(root, repo, provider, packet, contract, live_admission=live_admission) as ep:
        turn_root = root / 'turns' / ep.turn_key
        key = digest(packet)
        directory = turn_root / 'inputs' / key
        binding = {'input_sha256': key, 'input': packet, 'recheck': recheck,
                   'episode_manifest_sha256': digest(ep.manifest)}
        save(turn_root / 'versions' / (digest(packet['revision']) + '.json'), binding)
        save(directory / 'manifest.json', binding)
        summary = directory / 'summary.json'
        if summary.exists():
            return {**read_record(summary), 'source_ref': str(summary)}
        initial = final = revised = prepared = None

        def finish(status, reason=None, *, pending=False):
            state = ep.tally()
            r = final['result'] if final else None
            out = {'schema': 'mindthus.relationship-entry-result.v1', 'mode': MODE,
                   'manifest_sha256': digest(binding), 'status': status, 'reason': reason,
                   'original_input': packet, 'prepared_input': prepared, 'revised_input': revised,
                   'initial_assessment_ref': initial['source_ref'] if initial else None,
                   'final_assessment_ref': final['source_ref'] if final else None,
                   'action': r['action'] if r else 'return_original_owner',
                   'matrix': r['matrix'] if r else [], 'scope_acceptance': r.get('scope_acceptance') if r else None,
                   'known_obligations': relation.clone(packet['authority']['known_obligations']),
                   'episode_counts': state['counts'], 'turn_counts': state['turn_counts'],
                   'recorded_request_seconds': state['seconds'], 'usage': state['usage'],
                   'host_followup_cost': 'unknown', 'evidence_kind': ep.evidence_kind,
                   'task_complete': False, 'qualification': False, 'native_skill_load': 'not_observed'}
            if status not in ('assessment_complete', 'corrected_rechecked'):
                out['action'] = 'return_original_owner'
            if pending:
                return {**out, 'source_ref': str(directory / 'manifest.json')}
            save(summary, out)
            return {**out, 'source_ref': str(summary)}

        try:
            if not packet['activation']['enabled'] or packet['authority']['risk'] != 'low' or packet['authority']['mode'] == 'none':
                return finish('returned_to_owner', 'inactive_or_authority_outside_scope')
            if ep.tally()['failures']:
                return finish('returned_to_owner', 'terminal_technical_failure')
            prepared = relation.clone(packet)
            if prepared['proposal'] is None:
                if organizer is None and not (directory / 'steps/organize/outcome.json').exists():
                    return finish('awaiting_structure', pending=True)
                body = {'mode': MODE, 'policy': relation.POLICY, 'original_input': packet,
                        'owner_ref': owner + ':organizer', 'task': 'Organize raw references only; no new evidence or verdict.'}
                request = {'request_id': digest(body), **body}

                def validate_organized(reply):
                    relation.shape(reply, {'proposal', 'receipt_ref', 'usage'}, 'organizer_reply')
                    require(relation.text(reply['receipt_ref']), 'organizer_receipt_missing')
                    _usage(reply['usage'])
                    relation.compile_packet({**packet, 'proposal': reply['proposal']}, repo)
                out = _host(ep, directory, 'organize', request, organizer, validate_organized)
                if out['status'] != 'complete':
                    return finish('returned_to_owner', 'organizer_failed')
                prepared['proposal'] = relation.clone(out['reply']['proposal'])
                save(directory / 'prepared.json', prepared)
            initial = final = _judge(ep, directory, prepared, 'initial')
            if initial['result']['action'] != 'request_correction':
                return finish('assessment_complete' if initial['result']['action'] == 'continue_original'
                              else 'returned_to_owner', initial['result'].get('reason'))
            request = correction_request(prepared, initial)
            if corrector is None and not (directory / 'steps/correction/outcome.json').exists():
                return finish('awaiting_corrector', pending=True)
            out = _host(ep, directory, 'correction', request, corrector,
                        lambda reply: revision_packet(request, reply, repo))
            if out['status'] != 'complete':
                return finish('returned_to_owner', 'correction_failed')
            revised = revision_packet(request, out['reply'], repo)
            save(directory / 'revision.json', {'parent_input_sha256': digest(prepared),
                 'request_id': request['request_id'], 'receipt_ref': out['reply']['receipt_ref'], 'input': revised})
            if not recheck:
                return finish('corrected_unverified', 'optional_recheck_not_requested')
            final = _judge(ep, directory, revised, 'recheck')
            return finish('corrected_rechecked' if final['result']['action'] == 'continue_original'
                          else 'returned_to_owner_after_recheck', final['result'].get('reason'))
        except EpisodeStop as exc:
            return finish('returned_to_owner', str(exc))
        except ContractError as exc:
            # Input-size/shape failures after binding return the raw task, without fabricating judgments.
            if str(exc).startswith(('coverage_overflow:', 'invalid_', 'candidate_')):
                return finish('returned_to_owner', str(exc).split(':')[0])
            raise
