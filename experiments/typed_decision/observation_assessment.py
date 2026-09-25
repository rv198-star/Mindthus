"""Source-direct S1 observations with scoped unknown consumption.

This opt-in successor reads the original task and an existing candidate directly.
It does not require a frame/claim/edge proposal, choose a method, certify facts, or
grant execution authority.  Each fixed check declares how an unresolved result may
affect the current action before any model answer is observed.
"""
from __future__ import annotations

from pathlib import Path

from . import assessment, c01
from .contracts import ContractError, DecisionResult, DecisionSpec, digest, require
from .session import RecoveryRequired, safe_failure_reason

VERSION = '3'
POLICY = 'mindthus.source-direct-observation.v3'

CHECKS = {
    **assessment.CHECKS,
    'evidence_decision_fit': {
        'sources': ('entry', 'frame', 'situated'),
        'fit': 'grounded_and_responsive',
        'hits': ('unsupported_candidate_claim', 'material_source_omission',
                 'conditional_decision_omitted'),
        'unknown_policy': 'blocks_action',
        'question': (
            'Evaluate the evidentiary adequacy of the CURRENT assessment_target for the '
            'actual original_task and decision_context. Identify its task-changing conclusion, '
            'then compare that conclusion with supplied evidence, explicit unknowns, user role, '
            'time, goal and requested decision. The candidate is not evidence. Choose exactly '
            'one relation. grounded_and_responsive means the conclusion answers the actual task, '
            'keeps all material supplied distinctions, and conditions the answer on any unknown '
            'that would change the decision. unsupported_candidate_claim means the conclusion '
            'depends on a material fact or capability introduced only by the candidate. '
            'material_source_omission means supplied evidence or a supplied distinction that '
            'could change the conclusion is ignored or neutralized. conditional_decision_omitted '
            'means the supplied material establishes the choice boundary but the candidate '
            'presents an unconditional answer or evades that boundary. insufficient_context is '
            'only for a real missing material fact that prevents evaluating the conclusion; do '
            'not use it because an organizer omitted a field when the fact remains in '
            'original_task. not_applicable is only for a target without a task-facing conclusion. '
            'Apply canonical rules; do not prefer a longer or more complex explanation.'),
        'criteria': {
            'grounded_and_responsive': 'The conclusion answers the actual task and preserves every supplied distinction or condition material to it.',
            'unsupported_candidate_claim': 'A task-changing claim or capability is introduced by the candidate without support in the supplied material.',
            'material_source_omission': 'A supplied fact or distinction that could change the conclusion is omitted or neutralized.',
            'conditional_decision_omitted': 'The material supplies a decision boundary, but the candidate evades it or states an unconditional result.',
            'insufficient_context': 'A genuinely absent material fact prevents evaluating the candidate conclusion.',
            'not_applicable': 'There is no task-facing candidate conclusion to evaluate.',
        },
        'remedy': (
            'Answer the actual object, role, time and goal. Remove unsupported candidate-only '
            'claims, restore supplied result-changing evidence, and state the concrete condition '
            'for any decision that cannot yet be unconditional.'),
    },
}

# Existing checks retain their semantics.  Their unresolved effect is explicit here,
# rather than inferred after seeing a result.  A semantic hit still requires disposition.
UNKNOWN_POLICY = {
    'explanatory_scope': 'advisory',
    'premise_treatment': 'advisory',
    'scope_preservation': 'blocks_action',
    'evidence_decision_fit': 'blocks_action',
}


def validate_envelope(data: dict) -> None:
    require(isinstance(data, dict) and isinstance(data.get('activation'), dict),
            'source_direct_v3_input_shape')
    requested = data['activation'].get('checks')
    require(isinstance(requested, list) and 0 < len(requested) <= len(CHECKS)
            and len(set(requested)) == len(requested)
            and all(isinstance(key, str) and key in CHECKS for key in requested),
            'source_direct_v3_invalid_checks')
    # Reuse every v2 envelope invariant while validating v3's one additional,
    # fixed-contract check locally.  No looser task/permission/target shape is admitted.
    legacy = assessment.clone(data)
    legacy['activation']['checks'] = [key for key in requested if key in assessment.CHECKS]
    assessment.validate_envelope(legacy)
    activation = data['activation']
    # The minimum slice is S1 only and requires an actual candidate.  S0 method
    # routing remains owned by route-control and is tested separately.
    require(activation['event'] == 'before-answer', 'source_direct_v3_requires_S1')
    require(data['target'] is not None and data['target']['kind'] != 'user_frame',
            'source_direct_v3_requires_candidate')


def _is_unknown(answer: DecisionResult) -> bool:
    return answer.status != 'ok' or answer.value == 'insufficient_context'


def compile_observation(data: dict, repo: Path, *, stage: str = 'S1') -> dict:
    """Compile the exact questions and projected State used by a live admission."""
    validate_envelope(data)
    require(stage in ('S1', 'S2'), 'source_direct_v3_invalid_stage')
    data = assessment.clone(data)
    rules, refs = assessment.source_contracts(repo)
    activation = data['activation']
    target = data['target']
    problem = c01.input_problem(data['task'])
    active = activation['required'] or (activation['frame_risk'] and activation['execution_impact'])
    reason = problem or ('not_activated' if not active else None)
    selected = [key for key in CHECKS if key in activation['checks']] if reason is None else []
    view = {'original_task': data['task'], 'decision_context': data['decision_context'],
            'assessment_target': target, 'canonical_rules': rules}
    specs = [DecisionSpec(key, CHECKS[key]['question'], CHECKS[key]['criteria'], tuple(view),
                          version=VERSION, policy_ref=POLICY) for key in selected]
    return {'data': data, 'refs': refs, 'target': target, 'problem': problem,
            'reason': reason, 'selected': selected, 'view': view, 'specs': specs}


def assess(session, data: dict, repo: Path, *, stage: str = 'S1') -> dict:
    """Evaluate one source-direct batch; unknowns block only their declared scope."""
    compiled = compile_observation(data, repo, stage=stage)
    data = compiled['data']
    refs = compiled['refs']
    target = compiled['target']
    problem = compiled['problem']
    reason = compiled['reason']
    selected = compiled['selected']
    view = compiled['view']
    specs = compiled['specs']
    activation = data['activation']
    answers = {}
    if specs:
        try:
            answers = session.evaluate(specs, view)
        except RecoveryRequired:
            raise
        except ContractError as exc:
            answers = {s.id: DecisionResult('provider_error', reason=safe_failure_reason(exc))
                       for s in specs}

    rows, hits, blocking_unknown, advisory_unknown = [], [], [], []
    for key, check in CHECKS.items():
        answer = answers.get(key)
        hit_values = (tuple(check['hits']) if 'hits' in check
                      else (check['hit'],))
        policy = UNKNOWN_POLICY[key]
        if answer and answer.status == 'ok' and answer.value in hit_values:
            hits.append(key)
        if answer and _is_unknown(answer):
            (blocking_unknown if policy == 'blocks_action' else advisory_unknown).append(key)
        rows.append({
            'check_id': key,
            'question_version': VERSION,
            'effect': {'hit': 'requires_disposition', 'unknown': policy},
            'target_ref': target['source_ref'], 'target_version': target['version'],
            'target_kind': target['kind'], 'object_scope': assessment.clone(data['decision_context']),
            'state_sha256': digest(data), 'phase': stage,
            'dependencies': {'candidate_version': target['version'],
                             'decision_context': digest(data['decision_context']),
                             'source_material': digest(data['task']),
                             'contract': POLICY},
            'sources': {name: refs[name] for name in check['sources']},
            'origin': session.evidence_kind if answer else 'not_evaluated',
            'status': answer.status if answer else 'not_evaluated',
            'value': answer.value if answer else None,
            'uncertainty': assessment.clone(answer.uncertainty) if answer else None,
            'reason': answer.reason if answer else reason or 'not_requested',
            'consumed': bool(answer and not (answer.status == 'ok'
                                             and answer.value == 'not_applicable')),
        })

    if problem:
        action = 'return_original_owner'
    elif data['task'].get('risk') != 'low':
        action = 'return_original_owner'
    elif hits:
        # A known, bounded defect remains actionable even if a sibling observation
        # failed.  Blocking unknowns remain explicit and must be cleared on recheck.
        action = 'request_correction'
    elif blocking_unknown:
        action = ('acquire_information' if all(answers[key].status in ('ok', 'missing_context')
                                                for key in blocking_unknown)
                  else 'return_original_owner')
    elif activation['required'] or data['task'].get('known_obligations'):
        action = 'return_original_owner'
    else:
        action = 'continue_original'

    result = {
        'action': action, 'matrix': rows, 'hits': hits,
        'blocking_unresolved': blocking_unknown, 'advisory_unresolved': advisory_unknown,
        'reason': problem or reason or ('risk_outside_automatic_correction'
                    if data['task'].get('risk') != 'low'
                    else 'scoped_correction_required' if hits
                    else 'blocking_observation_unresolved' if blocking_unknown
                    else 'required_audit_retained' if activation['required']
                    else 'known_obligation_retained' if data['task'].get('known_obligations')
                    else 'source_direct_observations_consumed'),
        'required_audit_retained': activation['required'],
        'obligations': assessment.clone(data['task'].get('known_obligations', [])),
        'qualification': False, 'target': target, 'policy_ref': POLICY,
    }
    graph = {'id': 'mindthus.source-direct-observation', 'version': VERSION,
             'source_bindings': refs, 'selected_checks': selected,
             'unknown_policy': {key: UNKNOWN_POLICY[key] for key in selected},
             'policy_ref': POLICY, 'stage': stage}
    return session.finish(graph, data, result)


def correction_request(report: dict, data: dict, repo: Path) -> dict:
    """Produce one bounded host directive from declared, source-direct hits."""
    require(report['result']['action'] == 'request_correction',
            'source_direct_v3_no_correction')
    require(report['identity']['graph']['version'] == VERSION
            and report['result']['policy_ref'] == POLICY,
            'source_direct_v3_contract_changed')
    require(report['identity']['input_sha256'] == digest(data),
            'source_direct_v3_input_changed')
    rules, refs = assessment.source_contracts(repo)
    require(refs == report['identity']['graph']['source_bindings'],
            'source_direct_v3_sources_changed')
    order = ('scope_preservation', 'premise_treatment', 'explanatory_scope',
             'evidence_decision_fit')
    body = {
        'original_task': assessment.clone(data['task']),
        'decision_context': assessment.clone(data['decision_context']),
        'current_target': assessment.clone(report['result']['target']),
        'instructions': [CHECKS[key]['remedy'] for key in order
                         if key in report['result']['hits']],
        'blocking_unresolved': assessment.clone(report['result']['blocking_unresolved']),
        'advisory_unresolved': assessment.clone(report['result']['advisory_unresolved']),
        'canonical_rules': rules,
        'boundary': ('Revise only the current target once. Preserve original facts, user goals, '
                     'permissions and supported local truths. Do not treat an unresolved advisory '
                     'observation as false or passed. A blocking unresolved relation must remain '
                     'explicit for recheck; do not invent evidence to clear it.'),
        'parent_assessment_ref': report['source_ref'],
    }
    return {'request_id': digest(body), **body}
