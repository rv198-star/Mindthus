"""First executable entry-assessment slice: check -> one host correction -> recheck.

The public assess(Session, ...) seam accepts any already-admitted DecisionProvider.
This end-to-end driver/CLI is deliberately offline until a separate paid campaign
admits checks, host corrections and routing together. It never accesses credentials.
The original C01 graph4 remains the optional routing backend, not a rewritten router.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from . import assessment, c01, handoff
from .contracts import BatchResult, canonical, digest, number, provider_configuration, require
from .providers import FixtureProvider, ProviderError
from .session import Limits, RecoveryRequired, Session, implementation_digest, read_record, write_once
from .trace import from_c01, validate_with_existing

VERSION = '1'
CHECK_LIMITS = Limits(max_calls=2, max_seconds=60, max_request_bytes=98304)
ROUTE_LIMITS = Limits(max_calls=3, max_seconds=30, max_request_bytes=98304)
BUDGET = {'assessment_calls': 2, 'corrections': 1, 'routing_calls': 3,
          'total_calls': 6, 'total_seconds': 90, 'correction_seconds': 30,
          'correction_output_bytes': 16384, 'paid_calls_authorized': 0}
USAGE_UNKNOWN = {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}


def _save_or_match(path: Path, payload: dict) -> None:
    if path.exists():
        require(read_record(path) == payload, 'immutable entry record changed')
    else:
        write_once(path, payload)


def _elapsed(root: Path) -> float:
    total = 0.0
    for folder in ('assessment', 'routing'):
        for p in (root / folder / 'calls').glob('*/outcome.json'):
            elapsed = read_record(p)['elapsed_seconds']
            require(number(elapsed, 0, 86400), 'invalid recorded elapsed time')
            total += elapsed
    p = root / 'correction' / 'outcome.json'
    if p.exists():
        elapsed = read_record(p)['elapsed_seconds']
        require(number(elapsed, 0, 86400), 'invalid recorded correction elapsed time')
        total += elapsed
    return total


def _remaining(root: Path, started: float) -> float:
    remaining = BUDGET['total_seconds'] - max(_elapsed(root), time.monotonic() - started)
    require(remaining > 0, 'entry shared time budget exhausted')
    return remaining


class _BudgetedProvider:
    """Same provider identity; all child calls share the episode's remaining time."""
    def __init__(self, provider, root, started):
        self.wrapped, self.root, self.started = provider, root, started

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def evaluate(self, specs, context, timeout):
        allowed = min(timeout, _remaining(self.root, self.started))
        begin = time.monotonic()
        batch = self.wrapped.evaluate(specs, context, allowed)
        if time.monotonic() - begin > allowed:
            raise ProviderError('deadline_exceeded')
        require(isinstance(batch, BatchResult), 'invalid provider batch')
        batch.validate(specs)
        if batch.resolved_runtime is not None:
            self.wrapped.validate_runtime(batch.resolved_runtime)
            path = self.root / 'resolved-runtime.json'
            runtime = batch.resolved_runtime.to_dict()
            if path.exists():
                require(read_record(path) == runtime, 'resolved runtime drift within trial')
            else:
                write_once(path, runtime)
        return batch


def _correct(root: Path, request: dict, owner_ref: str, corrector, timeout: float) -> dict:
    """Execute an explicit host hook once; incomplete external attempts never resend.

The hook must honor timeout. Late-return detection is not a process-kill guarantee.
A production host must enforce its own HTTP/subprocess timeout and paid admission.
"""
    intent = {'request_id': request['request_id'], 'owner_ref': owner_ref,
              'request_sha256': digest(request), 'max_calls': 1,
              'output_bytes': BUDGET['correction_output_bytes']}
    ip, op = root / 'intent.json', root / 'outcome.json'
    if op.exists():
        require(ip.exists() and read_record(ip) == intent, 'correction request/owner changed')
        return read_record(op)
    if ip.exists():
        raise RecoveryRequired('unknown host correction; reconcile original receipt before continuation')
    require(corrector is not None and not corrector.is_live, 'offline correction hook required')
    require(corrector.identity == owner_ref, 'correction hook identity differs')
    write_once(ip, intent)
    begin = time.monotonic()
    try:
        reply = corrector.correct(assessment.clone(request), timeout)
        require(isinstance(reply, dict) and set(reply) == {'text', 'version', 'receipt_ref', 'usage'},
                'correction reply shape')
        require(all(assessment.text(reply[k]) for k in ('text', 'version', 'receipt_ref')),
                'correction artifact and receipt required')
        require(reply['version'] != request['current_target']['version'], 'revision version unchanged')
        require(reply['text'] != request['current_target']['text'], 'revision text unchanged')
        require(len(canonical(reply)) <= BUDGET['correction_output_bytes'], 'correction output exceeds budget')
        require(isinstance(reply['usage'], dict) and set(reply['usage']) == set(USAGE_UNKNOWN)
                and all(v is None or (number(v, 0, 1e15) and (k == 'cost_usd' or type(v) is int))
                        for k, v in reply['usage'].items()), 'invalid correction usage')
        require(time.monotonic() - begin <= timeout, 'correction deadline exceeded')
        outcome = {'status': 'complete', 'reply': assessment.clone(reply), 'error': None}
    except Exception as exc:
        # Keep technical outcomes terminal, never make a replacement key or retry.
        outcome = {'status': 'failed', 'reply': None, 'error': type(exc).__name__}
    outcome.update(elapsed_seconds=time.monotonic() - begin, evidence_kind='offline_fixture')
    write_once(op, outcome)
    return outcome


def _final(root: Path, manifest: dict, initial: dict, final: dict, status: str,
           revised: dict | None, route_report: dict | None = None, bundle: dict | None = None) -> dict:
    correction_path = root / 'correction' / 'outcome.json'
    correction = read_record(correction_path) if correction_path.exists() else None
    paths = list((root / 'assessment' / 'calls').glob('*/intent.json'))
    route_paths = list((root / 'routing' / 'calls').glob('*/intent.json'))
    result = {
        'schema': 'mindthus.entry-result.v1', 'manifest_sha256': digest(manifest), 'status': status,
        'initial_assessment_ref': initial['source_ref'], 'final_assessment_ref': final['source_ref'],
        'matrix': final['result']['matrix'], 'action': final['result']['action'],
        'original_task': manifest['input']['task'], 'revised_target': revised,
        'correction_receipt_ref': (correction['reply']['receipt_ref']
                                   if correction and correction['status'] == 'complete' else None),
        'routing': route_report, 'handoff': bundle,
        'counts': {'assessment_calls': len(paths), 'corrections': int(correction_path.exists()),
                   'routing_calls': len(route_paths), 'total': len(paths) + len(route_paths)
                   + int(correction_path.exists())},
        'cost': {'coverage': 'partial', 'actual_cost_usd': None,
                 'correction_usage': correction['reply']['usage'] if correction and correction['reply'] else None,
                 'design_and_maintenance': 'unknown'},
        'qualification': False, 'native_skill_load': 'not_observed',
        'canonical_audit': 'not_certified_by_checks', 'task_acceptance': 'not_evaluated',
    }
    require(result['counts']['total'] <= BUDGET['total_calls'], 'entry total call budget exceeded')
    path = root / ('awaiting-correction.json' if status == 'awaiting_correction' else 'summary.json')
    _save_or_match(path, result)
    return {**result, 'source_ref': str(path)}


def run(root: Path, provider, data: dict, repo: Path, *, corrector=None,
        correction_owner_ref='original-agent:v1', route=False, mode='assessment-v2',
        organizer=None, recheck=True, live_admission=None) -> dict:
    """Run an opt-in assessment episode; route only after its scoped gate permits it.

S0 inspects an actual user frame. S1 requires an existing candidate. A corrected
frame/answer stays a proposal alongside, never in place of, the original request.
"""
    require(mode in ('assessment-v2', 'relationship-frame.v1'), 'unknown_entry_mode')
    if mode == 'relationship-frame.v1':
        from . import relationship_runtime
        require(route is False, 'relationship_mode_does_not_stack_C01_routing')
        require(correction_owner_ref in ('original-agent:v1', data.get('authority', {}).get('owner_ref')),
                'relationship_owner_mismatch')
        return relationship_runtime.run(root, provider, data, repo, corrector=corrector,
                                        organizer=organizer, recheck=recheck, live_admission=live_admission)
    require(organizer is None and recheck is True and live_admission is None, 'relationship_options_on_legacy_mode')
    require(not provider.is_live, 'entry_live_campaign_not_preregistered')
    require(corrector is None or not corrector.is_live, 'host_live_campaign_not_preregistered')
    require(assessment.text(correction_owner_ref) and type(route) is bool, 'entry options malformed')
    assessment.validate_envelope(data)
    data = assessment.clone(data)
    repo, root = Path(repo).resolve(), Path(root).resolve()
    require(not root.is_relative_to(repo), 'state root must stay outside repository')
    _, refs = assessment.source_contracts(repo)
    manifest = {'version': VERSION, 'input': data, 'provider': provider_configuration(provider),
                'implementation': implementation_digest(), 'source_bindings': refs,
                'budget': BUDGET, 'correction_owner_ref': correction_owner_ref, 'route': route,
                'route_sources': {name: digest((repo / 'skills' / name / 'SKILL.md').read_text(encoding='utf8'))
                                  for name in sorted(c01.METHODS)} if route else {},
                'scope': 'entry-' + digest(data)[:24]}
    import fcntl
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.entry-lock').open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RecoveryRequired('another process owns this entry') from None
        _save_or_match(root / 'manifest.json', manifest)
        started = time.monotonic()
        provider = _BudgetedProvider(provider, root, started)
        revised = None
        with Session(root / 'assessment', provider, scope=manifest['scope'], limits=CHECK_LIMITS) as session:
            initial = final = assessment.assess(session, data, repo)
            _save_or_match(root / 'initial.json', {'source_ref': initial['source_ref'],
                                                  'run_id': initial['run_id']})
            action = initial['result']['action']
            if initial['result']['reason'] == 'candidate_absent':
                return _final(root, manifest, initial, final, 'candidate_absent', None)
            if action == 'request_correction':
                request = assessment.correction_request(initial, data, repo)
                _save_or_match(root / 'correction-request.json', request)
                cp = root / 'correction'
                if corrector is None and not (cp / 'outcome.json').exists():
                    if (cp / 'intent.json').exists():
                        raise RecoveryRequired('unknown correction must not be resubmitted')
                    return _final(root, manifest, initial, final, 'awaiting_correction', None)
                remaining = _remaining(root, started)
                outcome = _correct(cp, request, correction_owner_ref, corrector,
                                   min(BUDGET['correction_seconds'], remaining))
                if outcome['status'] != 'complete':
                    return _final(root, manifest, initial, final, 'correction_failed', None)
                reply = outcome['reply']
                revised = {**initial['result']['target'], 'version': reply['version'],
                           'text': reply['text'], 'source_ref': reply['receipt_ref']}
                if revised['kind'] == 'user_frame':
                    revised['kind'] = 'candidate_frame'
                next_state = assessment.clone(data)
                next_state.update(state_version=digest([data['state_version'], request['request_id'], revised]),
                                  target=revised)
                # All active checks read the same revised target, so all are affected.
                # P3 becomes applicable when an S0 user frame gains a host candidate.
                _save_or_match(root / 'revision.json', {
                    'parent_state_sha256': digest(data), 'parent_assessment_ref': initial['source_ref'],
                    'correction_request_id': request['request_id'], 'input': next_state})
                _remaining(root, started)
                final = assessment.assess(session, next_state, repo, stage='S2')
                _save_or_match(root / 'recheck.json', {'source_ref': final['source_ref'], 'run_id': final['run_id']})
                action = final['result']['action']
                if action != 'continue_original':
                    return _final(root, manifest, initial, final, 'returned_to_owner_after_one_recheck', revised)
            elif action != 'continue_original':
                return _final(root, manifest, initial, final, action, None)
        if not route:
            return _final(root, manifest, initial, final,
                          'corrected_rechecked' if revised else ('assessment_skipped' if initial['result']['reason'] == 'not_activated'
                                                               else 'assessment_complete'), revised)
        if data['activation']['event'] == 'before-answer' and data['target'] is None:
            return _final(root, manifest, initial, final, 'candidate_absent', revised)
        route_input = assessment.clone(data['task'])
        target = revised or data['target']
        if target is not None and target['kind'] != 'user_frame':
            route_input['evidence'].append({'source_ref': target['source_ref'],
                'summary': 'Host candidate, not established fact; original task/constraints remain authoritative: '
                           + target['text']})
        # Do not automatically dismiss a canonical audit just because a detector is clear.
        if revised and initial['result']['hits']:
            route_input['known_obligations'].append('entry_correction_requires_original_owner_audit')
        _remaining(root, started)
        with Session(root / 'routing', provider, scope=manifest['scope'] + ':route', limits=ROUTE_LIMITS) as session:
            routing = c01.run(session, route_input, repo)
        # Bind the same physical runtime across both journals, not just within each child.
        locks = [p for p in (root / 'assessment' / 'resolved-runtime.json',
                             root / 'routing' / 'resolved-runtime.json') if p.exists()]
        if len(locks) == 2:
            require(read_record(locks[0]) == read_record(locks[1]), 'entry runtime drift across stages')
        routing_stable = {k: routing[k] for k in ('run_id', 'identity', 'result', 'call_keys', 'source_ref')}
        if routing['result']['status'] in ('provider_error', 'unsupported'):
            return _final(root, manifest, initial, final, 'routing_failed', revised, routing_stable)
        bundle = handoff.prepare(root / 'routing', routing['run_id'], route_input, repo)
        _save_or_match(root / 'handoff.json', bundle)
        trace = from_c01(routing)
        trace['provenance']['source_ref'] = str(root / 'summary.json')
        validate_with_existing(trace, repo)
        if not (root / 'judgment-trace.json').exists():
            write_once(root / 'judgment-trace.json', trace)
        return _final(root, manifest, initial, final, 'routed_proposal', revised, routing_stable, bundle)


class ScriptedCorrection:
    """Offline host-response fixture. No claim that a real LLM produced this revision."""
    is_live = False

    def __init__(self, reply: dict, identity='original-agent:v1'):
        self.reply, self.identity = assessment.clone(reply), identity
        self.calls = 0

    def correct(self, request: dict, timeout: float) -> dict:
        self.calls += 1
        return assessment.clone(self.reply)


class EntryFixtureProvider(FixtureProvider):
    """Offline exact-target answer script; engine identity binds the entire script."""
    def __init__(self, answers: dict):
        super().__init__(answers)

    def evaluate(self, specs, context, timeout):
        saved = self.answers
        target = context.get('assessment_target')
        if 'proposal_view' in context:
            candidate = context['proposal_view']['candidate']
            version = candidate['ref']['revision'] if candidate else 'S0'
            self.answers = saved.get('by_target_version', {}).get(version, saved.get('initial', {}))
        elif target is not None:
            self.answers = saved.get('by_target_version', {}).get(target['version'], saved.get('initial', {}))
        else:
            self.answers = saved.get('routing', {})
        try:
            return super().evaluate(specs, context, timeout)
        finally:
            self.answers = saved


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=Path(__file__).parent / 'fixtures/entry-correction.json')
    parser.add_argument('--state-root', type=Path, required=True)
    parser.add_argument('--route', action='store_true', help='Continue via existing C01; no native skill execution')
    parser.add_argument('--mode', choices=['assessment-v2', 'relationship-frame.v1'], default='assessment-v2')
    parser.add_argument('--no-recheck', action='store_true', help='Relationship mode only: return revision without S2')
    parser.add_argument('--live-input', type=Path, help='D3: exact admitted input packet JSON')
    parser.add_argument('--live-admission', type=Path, help='D3: frozen per-episode admission JSON')
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    try:
        if args.live_input is not None or args.live_admission is not None:
            require(args.live_input is not None and args.live_admission is not None
                    and args.mode == 'relationship-frame.v1', 'explicit_live_input_admission_required')
            from .relationship_live import CPAHost, deadline_post_json
            from .providers import TypeSafeJevProvider
            packet = json.loads(args.live_input.read_bytes())
            admission = json.loads(args.live_admission.read_bytes())
            owner = packet['authority']['owner_ref']
            provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True, transport=deadline_post_json)
            result = run(args.state_root, provider, packet, repo, mode=args.mode, route=args.route,
                         corrector=CPAHost(owner, repo),
                         organizer=CPAHost(owner, repo, organizer=True) if admission['organizer'] else None,
                         recheck=not args.no_recheck, live_admission=admission)
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
            return 0
        fixture = json.loads(args.fixture.read_text(encoding='utf8'))
        owner = (fixture['input']['authority']['owner_ref'] if args.mode == 'relationship-frame.v1'
                 else 'original-agent:v1')
        hook = ScriptedCorrection(fixture['correction'], identity=owner) if fixture.get('correction') else None
        result = run(args.state_root, EntryFixtureProvider(fixture['answers']), fixture['input'], repo,
                     corrector=hook, route=args.route, mode=args.mode, recheck=not args.no_recheck)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, KeyError, OSError, RecoveryRequired) as exc:
        print(json.dumps({'status': 'blocked', 'error_type': type(exc).__name__}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
