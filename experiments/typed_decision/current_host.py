"""Credential-free, resumable host handoff in the existing episode journal.

No model client is constructed here. The owning Agent reads the bound request and
returns a typed result. This is an application receipt boundary, not proof of the
Agent's internal reasoning, identity attestation, or an OS security boundary.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import relationship_assessment as rel
from .contracts import canonical, digest, number, require
from .session import RecoveryRequired, read_record, write_once, implementation_digest

TRANSPORT = 'current-agent-handoff.v1'
ROLES = ('execution', 'correction', 'arbitration')


class AwaitingCurrentAgent(RecoveryRequired):
    def __init__(self, handoff_path: Path):
        super().__init__('awaiting_current_agent')
        self.handoff_path = str(handoff_path)


class CurrentAgentHost:
    """A host interface independent of whether the judgment provider is live."""
    is_live = False  # There is no outbound LLM request, credential, or vendor here.

    def __init__(self, owner_ref: str, *, role: str = 'execution'):
        require(rel.text(owner_ref) and role in ROLES, 'current_host_configuration')
        self.role = role
        self.identity = owner_ref + ':route-arbitrator' if role == 'arbitration' else owner_ref
        self.configuration = {'adapter': TRANSPORT, 'transport': TRANSPORT,
                              'owner': self.identity, 'kind': role,
                              'model': None, 'external_llm_required': False}


def is_current_host(hook) -> bool:
    return isinstance(hook, CurrentAgentHost)


def pending_request(intent: dict, step: Path) -> bool:
    """Only a known local handoff is resumable without a supplier outcome."""
    if intent.get('transport') != TRANSPORT:
        return False
    require(intent.get('host_configuration', {}).get('transport') == TRANSPORT,
            'invalid_current_host_intent')
    request = read_record(step / 'request.json')
    require(digest(request) == intent['request_sha256']
            and request['request_id'] == intent['request_id'], 'current_host_request_changed')
    require(number(intent.get('allowance_seconds'), 0.000001, 45), 'current_host_allowance')
    return True


def _reply_shape(role: str, request: dict) -> dict:
    unknown = {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}
    if role == 'execution':
        return {'route_id': request['route_id'], 'revision': request['revision'],
                'issue_id': request['issue']['issue_id'], 'performed_methods': [],
                'text': '', 'objection': None, 'usage': unknown}
    if role == 'arbitration':
        return {'route_id': request['route_id'], 'revision': request['revision'],
                'issue_id': request['issue_id'], 'decision': 'unresolved',
                'replacement': None, 'original_refs': [], 'reason': '', 'usage': unknown}
    return {'text': '', 'version': '', 'receipt_ref': '', 'usage': unknown, 'proposal': None}


def _validate_reply(role: str, reply: dict, request: dict, repo: Path) -> None:
    # Exact same validators as direct callbacks. Never silently fill method claims.
    from . import route_control as rc, relationship_runtime as rt
    if role == 'execution':
        rc.validate_execution(reply, request, request['original_input'])
    elif role == 'arbitration':
        rc._change(request['route'], request['issue_id'], reply, request['original_input'])
    else:
        rt.revision_packet(request, reply, repo)


def validate_submission(submission: dict, handoff: dict, repo: Path) -> None:
    rel.shape(submission, {'schema', 'request_id', 'request_sha256', 'owner_ref',
                          'host_context_ref', 'elapsed_seconds', 'reply'}, 'current_host_submission')
    require(submission['schema'] == 'mindthus.current-host-response.v1'
            and submission['request_id'] == handoff['request_id']
            and submission['request_sha256'] == handoff['request_sha256']
            and submission['owner_ref'] == handoff['owner_ref'], 'current_host_binding_mismatch')
    require(rel.text(submission['host_context_ref']), 'current_host_context_required')
    elapsed = submission['elapsed_seconds']
    require(elapsed is None or number(elapsed, 0, handoff['allowance_seconds']),
            'current_host_elapsed_exceeds_allowance')
    if handoff['role'] == 'arbitration':
        prior = handoff['request'].get('executor_context_ref')
        require(prior is not None and submission['host_context_ref'] != prior,
                'independent_arbitration_context_required')
    require(len(canonical(submission['reply'])) <= handoff['output_bytes'], 'host_output_overflow')
    _validate_reply(handoff['role'], submission['reply'], handoff['request'], repo)


def host_call(ep, directory, kind, request, hook, validator, expected_owner):
    """Reserve once; export a request; consume only the matching validated reply."""
    from . import relationship_runtime as rt
    require(is_current_host(hook) and hook.identity == expected_owner, 'current_host_identity')
    budget_kind = ep.kinds[kind.split('__', 1)[0]]
    require(hook.role == budget_kind, 'current_host_role_mismatch')
    step = directory / 'steps' / kind
    ip, op = step / 'intent.json', step / 'outcome.json'
    intent = {'mode': ep.mode, 'policy': request.get('policy', rel.POLICY),
              'transport': TRANSPORT, 'request_id': request['request_id'],
              'request_sha256': digest(request), 'owner_ref': expected_owner,
              'profile_sha256': digest(ep.profile), 'output_bytes': ep.profile['host_output_bytes'],
              'host_configuration': hook.configuration}
    rt.save(step / 'request.json', request)
    if ep.live_admission is not None:
        require(ep.live_admission[ep.host_slots[budget_kind]] == hook.configuration,
                'current_host_admission_configuration')
    if ip.exists():
        existing = read_record(ip)
        intent['allowance_seconds'] = existing.get('allowance_seconds')
        require(existing == intent and pending_request(existing, step), 'current_host_intent_changed')
    else:
        intent['allowance_seconds'] = ep.admit(budget_kind)
        rt.save(ip, intent)
    hp = step / 'handoff.json'
    handoff = {'schema': 'mindthus.current-host-request.v1', 'role': hook.role,
               'request_id': request['request_id'], 'request_sha256': digest(request),
               'owner_ref': expected_owner, 'allowance_seconds': intent['allowance_seconds'],
               'output_bytes': intent['output_bytes'], 'request': request,
               'reply_shape': _reply_shape(hook.role, request),
               'instruction': 'Use the current Agent, not an additional model API. Follow the committed '
                              'scope and loaded contracts. A completion must describe the actual work; '
                              'otherwise return a source-bound objection. Preserve original facts, '
                              'permissions and pending obligations. Do not submit hidden chain-of-thought.',
               'arbitration': 'Requires a genuinely separate host context; identifiers record '
                              'the host declaration, not a proof of isolation.',
               'unknown_cost': 'Keep unknown token/cost/elapsed telemetry null. If elapsed is unknown, '
                               'the reservation ceiling is charged conservatively, not reported as measured time.'}
    rt.save(hp, handoff)
    if op.exists():
        outcome = read_record(op)
        validator(outcome['reply'])
        return outcome
    rp = step / 'host-response.json'
    if not rp.exists():
        raise AwaitingCurrentAgent(hp)
    response = read_record(rp)
    submission = response['submission']
    validate_submission(submission, handoff, ep.repo)
    validator(submission['reply'])
    elapsed = submission['elapsed_seconds']
    out = {'status': 'complete', 'reply': submission['reply'], 'error': None,
           'usage': submission['reply']['usage'], 'mode': ep.mode, 'policy': intent['policy'],
           'evidence_kind': ep.evidence_kind, 'host_evidence_kind': 'current_agent_submission',
           'host_configuration': hook.configuration, 'host_context_ref': submission['host_context_ref'],
           'submission_sha256': digest(submission), 'external_llm_requests': 0,
           'elapsed_seconds': intent['allowance_seconds'] if elapsed is None else elapsed,
           'elapsed_basis': 'reserved_ceiling_actual_unknown' if elapsed is None else 'host_reported',
           'reported_elapsed_seconds': elapsed}
    return rt.save(op, out)


def submit_response(root: Path, repo: Path, submission: dict) -> str:
    """Stage a validated response under the SAME lock; bad replies do not consume it.

    Original request identity is mandatory. Completed or accepted replies are
    immutable. This accepts a host receipt; it never approves factual correctness.
    """
    from . import relationship_runtime as rt
    root, repo = Path(root).resolve(), Path(repo).resolve()
    require(not root.is_relative_to(repo), 'state_root_inside_repository')
    require(isinstance(submission, dict) and len(canonical(submission)) <= 65536,
            'current_host_submission_size')
    with rt._locked(root / '.entry-lock'):
        manifest = read_record(root / 'manifest.json')
        require(manifest['mode'] == 'route-control.v0.2.1', 'current_host_mode')
        require(manifest['implementation'] == implementation_digest(), 'current_host_implementation_changed')
        matches = []
        for hp in root.glob('turns/*/inputs/*/steps/*/handoff.json'):
            item = read_record(hp)
            if item['request_id'] == submission.get('request_id'):
                matches.append((hp, item))
        require(len(matches) == 1, 'current_host_request_not_unique_or_absent')
        hp, handoff = matches[0]
        require(pending_request(read_record(hp.with_name('intent.json')), hp.parent),
                'current_host_intent_required')
        validate_submission(submission, handoff, repo)
        rp = hp.with_name('host-response.json')
        if rp.exists():
            require(read_record(rp)['submission'] == submission, 'current_host_response_immutable')
        else:
            write_once(rp, {'submission': submission, 'received_at': datetime.now(timezone.utc).isoformat()})
        return str(rp)
