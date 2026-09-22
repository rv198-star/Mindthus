"""Opt-in P1/P2/P3 assessment; semantic results are not an audit or authorization.

Reuses DecisionSpec and the supplied Session (including live admission when present).
Canonical rules stay in their existing documents. This module neither calls a host
LLM nor changes C01 graph4, user goals, method definitions or Mission state.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import c01
from .contracts import ContractError, DecisionResult, DecisionSpec, canonical, digest, require
from .session import RecoveryRequired, safe_failure_reason

VERSION = '2'
POLICY = 'mindthus.entry-assessment.v2'
SOURCES = {
    'entry': 'skills/using-mindthus/SKILL.md',
    'frame': 'docs/methodologies/primitives/frame-fitness-check.md',
    'whole': 'docs/methodologies/primitives/whole-elephant-protocol.md',
    'situated': 'docs/methodologies/primitives/decision-context-calibration.md',
}
CHECKS = {
    'explanatory_scope': {
        'sources': ('frame', 'whole'), 'fit': 'scope_fit', 'hit': 'local_overreach',
        'question': ('Evaluate the local-fact-to-whole-conclusion relation in assessment_target. '
                     'First identify a locally supported observation, mechanism or result in '
                     'original_task evidence. Then check whether the target grants that local '
                     'truth sufficient authority over a broader conclusion about the SAME object, '
                     'omitting a factor material to the user goal. Both the supported local truth '
                     'and the unjustified scope transfer are required for local_overreach. A local '
                     'measure that actually answers the specified local question is scope_fit. '
                     'An unproved causal claim alone, a candidate inventing a fact, or a switch '
                     'to a broader unrelated task is not this relation: use not_applicable. '
                     'Use insufficient_context only when an apparent local-to-whole relation '
                     'cannot be evaluated from the supplied material. The target is not new '
                     'evidence. Apply canonical_rules.frame/whole and preserve decision_context.'),
        'criteria': {
            'scope_fit': 'A supported local observation is used only within its justified object/goal boundary.',
            'local_overreach': 'A supported local truth is made sufficient for a broader same-object conclusion despite a material missing relation.',
            'insufficient_context': 'An apparent local-to-whole transfer exists, but its support or consequential boundary cannot be established.',
            'not_applicable': 'No supported-local-truth to broader-same-object transfer is present; a different defect may still exist.',
        },
        'remedy': ('Keep the user\'s actual object and goal. Reconstruct what controls its target '
                   'result, retain the local truth within its proper boundary, and revise the main '
                   'thesis and its practical consequence. Do not invent a superior global explanation.'),
    },
    'premise_treatment': {
        'sources': ('entry', 'frame'), 'fit': 'treatment_fit', 'hit': 'unsupported_as_fact',
        'question': ('Evaluate USER-PREMISE ADOPTION, not all possible factual errors. Identify '
                     'a factual assertion or suspicion actually supplied by the user in original_task, '
                     'and compare how assessment_target treats that SAME proposition with its '
                     'independent support. unsupported_as_fact requires both user provenance and '
                     'unsupported adoption as settled fact. For an S0 user_frame, inspect the user\'s '
                     'own assertion; for an S1/S2 candidate, inspect its adoption of the user premise. '
                     'A user merely asking whether a conclusion follows is not asserting that '
                     'conclusion. A new overclaim invented only by the candidate is outside this '
                     'narrow check: use not_applicable and retain the original evidence duties. '
                     'Explicit hypotheses preserved as hypotheses, preferences and valid scope '
                     'constraints are treatment_fit. Use insufficient_context when a relevant '
                     'user-premise/support relation exists but cannot be decided. Never use the '
                     'candidate as evidence. Apply canonical_rules.entry/frame.'),
        'criteria': {
            'treatment_fit': 'A user-supplied proposition is supported, qualified, or kept as an explicit hypothesis; valid preferences/scope remain constraints.',
            'unsupported_as_fact': 'The target asserts an unsupported USER-SUPPLIED factual assertion or suspicion as settled fact.',
            'insufficient_context': 'A relevant user-supplied proposition is present but its support or adoption cannot be evaluated.',
            'not_applicable': 'No user-origin factual-premise adoption occurs; candidate-only invention/overclaim is not certified or cleared by this check.',
        },
        'remedy': ('Identify the specific unsupported user-supplied premise and its source. '
                   'Qualify that same proposition as a hypothesis, narrow the claim or request '
                   'the necessary evidence. Preserve valid user preferences and constraints; '
                   'do not attribute a candidate-only invention to the user or infer motives.'),
    },
    'scope_preservation': {
        'sources': ('situated', 'whole'), 'fit': 'within_scope', 'hit': 'scope_overridden',
        'question': ('Compare the existing assessment_target candidate with original_task and '
                     'decision_context under canonical_rules.situated/whole. Does its handling '
                     'unnecessarily replace or expand the valid user object, role, time, goal or '
                     'scope? Correcting an unsupported factual premise is not itself a scope '
                     'violation. Higher abstraction, a broader system or a longer answer is not '
                     'automatically better. Do not judge an answer which does not exist.'),
        'criteria': {
            'within_scope': 'Handling preserves the valid user object, goal and scope.',
            'scope_overridden': 'The candidate replaces or expands valid scope without a task-grounded need.',
            'insufficient_context': 'Valid scope or the candidate\'s relation to it is not established.',
            'not_applicable': 'No candidate handling is present for this comparison.',
        },
        'remedy': ('Restore the user\'s valid object, role, time, goal and limits before changing '
                   'the explanation. Do not move the answer to an umbrella system or erase a '
                   'legitimate local task in the name of a broader perspective.'),
    },
}


def text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def clone(value):
    return json.loads(canonical(value))


def source_contracts(repo: Path) -> tuple[dict, dict]:
    rules = {key: (repo / path).read_text(encoding='utf8') for key, path in SOURCES.items()}
    refs = {key: {'path': SOURCES[key], 'sha256': hashlib.sha256(value.encode()).hexdigest()}
            for key, value in rules.items()}
    return rules, refs


def validate_envelope(data: dict) -> None:
    require(isinstance(data, dict) and set(data) ==
            {'state_version', 'task', 'decision_context', 'target', 'activation'}, 'assessment input shape')
    require(text(data['state_version']), 'state version required')
    require(isinstance(data['task'], dict), 'original task required')
    decision = data['decision_context']
    require(isinstance(decision, dict) and set(decision) == {'object', 'goal', 'scope', 'source_ref'}
            and all(text(v) for v in decision.values()), 'decision context/source required')
    activation = data['activation']
    require(isinstance(activation, dict) and set(activation) ==
            {'event', 'source_ref', 'reason', 'frame_risk', 'execution_impact', 'required', 'checks'},
            'activation contract shape')
    require(activation['event'] in ('before-route', 'before-answer'), 'unsupported activation event')
    require(text(activation['source_ref']) and text(activation['reason']), 'activation source/reason required')
    require(all(type(activation[k]) is bool for k in ('frame_risk', 'execution_impact', 'required')),
            'activation flags must be explicit booleans')
    require(isinstance(activation['checks'], list) and len(activation['checks']) <= 3
            and all(isinstance(k, str) and k in CHECKS for k in activation['checks'])
            and len(set(activation['checks'])) == len(activation['checks']), 'invalid active checks')
    target = data['target']
    if target is not None:
        require(isinstance(target, dict) and set(target) == {'id', 'kind', 'version', 'source_ref', 'text'}
                and all(text(v) for v in target.values()), 'target identity/content required')
        require(target['kind'] in ('user_frame', 'candidate_frame', 'candidate_thesis',
                                   'candidate_plan', 'candidate_answer'), 'unsupported target kind')
        if target['kind'] == 'user_frame':
            require(activation['event'] == 'before-route', 'user frame belongs to S0')
            require(target['text'] in data['task'].get('request', ''), 'user frame must quote original request')
    require(len(canonical(data)) <= 16384, 'assessment input exceeds 16 KiB')


def assess(session, data: dict, repo: Path, *, stage: str | None = None) -> dict:
    """One batch on one State; skipped dimensions are not successful judgments."""
    validate_envelope(data)
    data = clone(data)
    rules, refs = source_contracts(repo)
    target = data['target']
    activation = data['activation']
    if target is None and activation['event'] == 'before-route':
        target = {'id': 'original-request', 'kind': 'user_frame', 'version': data['state_version'],
                  'source_ref': data['task'].get('provenance', {}).get('source_ref', 'unknown'),
                  'text': data['task'].get('request', '')}
    phase = ('S0' if activation['event'] == 'before-route' else 'S1') if target is None else (
        'S0' if target['kind'] == 'user_frame' else 'S1')
    if stage is not None:
        require(stage == 'S2' and target is not None and target['kind'] != 'user_frame', 'invalid recheck stage')
        phase = stage
    problem = c01.input_problem(data['task'])
    active = activation['required'] or (activation['frame_risk'] and activation['execution_impact'])
    reason = (problem or ('not_activated' if not active else None)
              or ('candidate_absent' if target is None else None))
    selected = [key for key in CHECKS if key in activation['checks']
                and not (key == 'scope_preservation' and phase == 'S0')] if reason is None else []
    view = {'original_task': data['task'], 'decision_context': data['decision_context'],
            'assessment_target': target, 'canonical_rules': rules}
    specs = [DecisionSpec(key, CHECKS[key]['question'], CHECKS[key]['criteria'], tuple(view),
                          version=VERSION, policy_ref=POLICY) for key in selected]
    answers = {}
    if specs:
        try:
            answers = session.evaluate(specs, view)
        except RecoveryRequired:
            raise  # An unknown external attempt is not a negative or a retry opportunity.
        except ContractError as exc:
            answers = {s.id: DecisionResult('provider_error', reason=safe_failure_reason(exc)) for s in specs}
    rows = []
    for key, check in CHECKS.items():
        answer = answers.get(key)
        row = {'check_id': key, 'question_version': VERSION, 'target_ref': target['source_ref'] if target else None,
               'target_version': target['version'] if target else None,
               'target_kind': target['kind'] if target else None,
               'object_scope': clone(data['decision_context']), 'state_sha256': digest(data),
               'phase': phase, 'sources': {r: refs[r] for r in check['sources']},
               'origin': session.evidence_kind if answer else 'not_evaluated',
               'status': answer.status if answer else 'not_evaluated',
               'value': answer.value if answer else None,
               'uncertainty': clone(answer.uncertainty) if answer else None,
               'reason': answer.reason if answer else reason or (
                   'no_candidate_handling_in_S0' if key == 'scope_preservation' and phase == 'S0'
                   else 'not_requested'),
               'consumed': bool(answer and not (answer.status == 'ok' and answer.value == 'not_applicable'))}
        rows.append(row)
    hits = [key for key, answer in answers.items()
            if answer.status == 'ok' and answer.value == CHECKS[key]['hit']]
    unknown = [key for key, answer in answers.items()
               if answer.status != 'ok' or answer.value == 'insufficient_context']
    if problem:
        action = 'return_original_owner'
    elif unknown:
        action = ('acquire_information' if all(answers[k].status in ('ok', 'missing_context') for k in unknown)
                  else 'return_original_owner')
    elif data['task'].get('risk') != 'low':
        action = 'return_original_owner'
    elif hits:
        action = 'request_correction'
    elif activation['required'] or data['task'].get('known_obligations'):
        action = 'return_original_owner'  # This detector never discharges a canonical required audit.
    else:
        action = 'continue_original'
    result = {'action': action, 'matrix': rows, 'hits': hits, 'unresolved': unknown,
              'reason': problem or reason or ('risk_outside_automatic_correction' if data['task'].get('risk') != 'low'
                    else 'unresolved_evaluation' if unknown
                    else 'required_audit_retained' if activation['required']
                    else 'known_obligation_retained' if data['task'].get('known_obligations')
                    else 'scoped_checks_consumed'),
              'required_audit_retained': activation['required'],
              'obligations': clone(data['task'].get('known_obligations', [])),
              'frame_status': 'not_assessed', 'qualification': False,
              'target': target, 'policy_ref': POLICY}
    graph = {'id': 'mindthus.entry-assessment', 'version': VERSION, 'source_bindings': refs,
             'selected_checks': selected, 'policy_ref': POLICY, 'stage': phase}
    return session.finish(graph, data, result)


def correction_request(report: dict, data: dict, repo: Path) -> dict:
    """A task-facing directive, not raw diagnostic enums or invented evidence."""
    require(report['result']['action'] == 'request_correction', 'no correction requested')
    require(report['identity']['graph']['version'] == VERSION
            and report['result']['policy_ref'] == POLICY,
            'assessment contract changed; preserve the original report')
    require(report['identity']['input_sha256'] == digest(data),
            'correction input differs from assessed State')
    rules, refs = source_contracts(repo)
    require(refs == report['identity']['graph']['source_bindings'], 'canonical sources changed')
    # Restore the valid object first, then premise treatment and the main explanation.
    order = ('scope_preservation', 'premise_treatment', 'explanatory_scope')
    body = {'original_task': clone(data['task']), 'decision_context': clone(data['decision_context']),
            'current_target': clone(report['result']['target']),
            'instructions': [CHECKS[k]['remedy'] for k in order if k in report['result']['hits']],
            'canonical_rules': rules,
            'boundary': ('Revise only this target once. Preserve original facts, user goals, explicit '
                         'method constraints and permissions. Your revision is an unverified host '
                         'proposal, not new evidence or an audit PASS. Do not execute tools or modify '
                         'Mission state. Identify unresolved evidence rather than inventing it.'),
            'parent_assessment_ref': report['source_ref']}
    return {'request_id': digest(body), **body}
