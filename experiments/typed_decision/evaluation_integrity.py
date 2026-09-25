"""Source-window and reviewer contracts for the one-cycle entry evaluation.

Pure preparation/validation: no inference, no selection of favorable cases, and no
runtime success inferred from a schema. Earlier partial snapshots remain partial.
"""
from copy import deepcopy
from pathlib import Path
from .session import read_record

from . import relationship_assessment as rel, route_control as rc, source_direct_v03 as sd
from .contracts import digest, require

PHASES = ('initial', 'after_user_correction', 'new_branch_turn')
TARGET_DIMENSIONS = {
    'E': {
        'scope_preservation': 'Stay within the actual Skill under discussion; do not borrow the entire Agent system.',
        'mechanism_and_object': 'Distinguish transmission mechanism from claimed whole-object responsibilities. '
            'Accept a genuinely sufficient simple explanation; do not assume more machinery exists.',
        'decisive_relation': 'Identify which supported relation actually changes the conclusion. '
            'A generic however/caveat is not sufficient when the task needs a determination; '
            'missing implementation evidence permits a justified conditional conclusion.',
    },
    'F': {
        'situated_goal': 'Let the actual user/OP goal determine what counts as solving the current problem. '
            'Do not silently replace acceptable usability with physical equivalence to 5K.',
        'unwarranted_time_scope': 'Do not restrict usability value to after purchase unless that restriction '
            'follows from the actual source. A cheaper option considered before purchase can also satisfy a usage goal.',
        'constraint_and_verdict': 'Retain physical/performance limits without treating their existence as proof '
            'that a practical problem cannot be solved. Conversely, a user claim alone does not verify all effects.',
    },
}


def prepare_prefix(source, cutoff_order, *, auxiliary_availability, phase, missing_original=()):
    """Include exactly the available prefix, never later user corrections.

    Availability of non-conversation documents must be explicitly declared; a
    reviewer rubric or a later assistant answer is not an auxiliary source.
    """
    require(phase in PHASES and type(cutoff_order) is int, 'evaluation_phase')
    expected = sd.ROUTE_FIELDS | {'conversation', 'host_inferences', 'consumption_policy', 'intervention'}
    require(set(source) == expected, 'evaluation_source_fields')
    conversation = source['conversation']
    require(any(m['order'] == cutoff_order and m['role'] == 'user' for m in conversation),
            'evaluation_cutoff_requires_user')
    retained = [deepcopy(m) for m in conversation if m['order'] <= cutoff_order]
    require(retained and retained[-1]['order'] == cutoff_order, 'evaluation_prefix_order')
    if phase == 'initial':
        require(sum(m['role'] == 'user' for m in retained) == 1 and
                not any(m['role'] == 'assistant' for m in retained), 'evaluation_initial_contains_history')
    docs = {d['id']: d for d in source['documents']}
    require(isinstance(auxiliary_availability, dict), 'evaluation_auxiliary_availability')
    included = {m['document_id'] for m in retained}
    for did, available in auxiliary_availability.items():
        require(did in docs and docs[did]['kind'] == 'source' and type(available) is int,
                'evaluation_auxiliary_source')
        if available <= cutoff_order:
            included.add(did)
    packet = deepcopy(source)
    packet.update(conversation=retained, documents=[deepcopy(d) for d in source['documents'] if d['id'] in included],
                  issues=[], dependencies=[], relationship=None)
    packet['host_inferences'] = {'provenance': 'host_inference',
                                'owner_ref': packet['authority']['owner_ref'], 'issue_views': {}}
    packet['intervention'] = {'turn_id': packet['turn_id'], 'history_sha256': sd.history_identity(packet)}
    metadata = {'phase': phase, 'cutoff_order': cutoff_order,
                'source_sha256': digest(source), 'visible_source_sha256': sd.history_identity(packet),
                'missing_original': list(missing_original),
                'original_failure_reproduction_eligible': False,
                'source_window_complete': not missing_original and phase == 'initial',
                'claim': 'partial_snapshot' if missing_original else 'prefix_only_not_yet_a_reproduction'}
    return {'packet': packet, 'metadata': metadata}


def append_branch_turn(prefix, *, assistant, next_user, context_ref):
    """Append the branch's actual accepted text then the next original user turn.

    The driver supplies an immutable execution receipt. This creates a new
    trajectory and never pretends the new answer is a missing historical answer.
    """
    require(set(assistant) == {'text', 'artifact_sha256', 'author_ref', 'context_ref', 'receipt_ref', 'acceptance_ref'},
            'evaluation_branch_artifact')
    require(rel.text(assistant['text']) and digest(assistant['text']) == assistant['artifact_sha256']
            and assistant['context_ref'] == context_ref and rel.text(context_ref)
            and rel.text(assistant['author_ref']) and rel.text(assistant['receipt_ref']),
            'evaluation_branch_identity')
    receipt_path = Path(assistant['receipt_ref'])
    receipt = read_record(receipt_path)
    request = read_record(receipt_path.with_name('request.json'))
    intent = read_record(receipt_path.with_name('intent.json'))
    observed_input = (request.get('condition_packet') or {}).get('original_input') or request.get('original_input')
    require(receipt.get('status') == 'complete' and receipt.get('host_context_ref') == context_ref
            and receipt.get('reply', {}).get('text') == assistant['text']
            and intent.get('request_sha256') == digest(request)
            and intent.get('request_id') == request.get('request_id')
            and observed_input is not None
            and sd.history_identity(observed_input) == sd.history_identity(prefix['packet']),
            'evaluation_branch_receipt_mismatch')
    accept_path = Path(assistant['acceptance_ref'])
    acceptance = read_record(accept_path)
    accept_request = read_record(accept_path.with_name('request.json'))
    accept_intent = read_record(accept_path.with_name('intent.json'))
    require(acceptance.get('status') == 'complete' and acceptance.get('host_context_ref') == context_ref
            and accept_intent.get('request_sha256') == digest(accept_request)
            and accept_intent.get('request_id') == accept_request.get('request_id'),
            'evaluation_final_acceptance_identity')
    sd.validate_acceptance(acceptance['reply'], accept_request)
    bound = [iid for iid, item in acceptance['reply']['accepted'].items()
             if item['accepted'] and item['artifact_sha256'] == assistant['artifact_sha256']
             and accept_request['candidate_texts'].get(iid) == assistant['text']]
    require(bool(bound) and sd.history_identity(accept_request['original_input']) ==
            sd.history_identity(prefix['packet']), 'evaluation_final_artifact_not_accepted')
    require(set(next_user) == {'document', 'source_ref'} and next_user['document']['kind'] == 'user' 
            and rel.text(next_user['source_ref']), 'evaluation_next_user')
    packet = deepcopy(prefix['packet'])
    ids = {d['id'] for d in packet['documents']}
    aid = 'branch_assistant_' + assistant['artifact_sha256'][:12]
    uid = next_user['document']['id']
    require(aid not in ids and uid not in ids and aid != uid, 'evaluation_duplicate_turn')
    order = packet['conversation'][-1]['order'] + 1
    packet['documents'] += [{'id': aid, 'revision': '1', 'kind': 'assistant', 'text': assistant['text']},
                            deepcopy(next_user['document'])]
    packet['conversation'] += [
        {'document_id': aid, 'role': 'assistant', 'order': order,
         'author_ref': assistant['author_ref'], 'source_ref': assistant['receipt_ref']},
        {'document_id': uid, 'role': 'user', 'order': order + 1,
         'author_ref': 'original-user', 'source_ref': next_user['source_ref']},
    ]
    packet['turn_id'] = str(order + 1)
    packet['intervention'] = {'turn_id': packet['turn_id'], 'history_sha256': sd.history_identity(packet)}
    metadata = {**prefix['metadata'], 'phase': 'new_branch_turn',
                'claim': 'new_realized_trajectory_not_original_failure_replay',
                'original_failure_reproduction_eligible': False,
                'visible_source_sha256': sd.history_identity(packet),
                'prior_artifact_sha256': assistant['artifact_sha256'], 'context_ref': context_ref}
    return {'packet': packet, 'metadata': metadata}


def reviewer_packet(case, scenario, artifacts, *, rubric_version='target-behavior.v1'):
    """Gold and target dimensions enter only this separate reviewer packet.

    Each anonymous artifact carries its actual method material; evaluator omissions
    cannot silently turn real context citations into fabricated-source accusations.
    """
    require(scenario in TARGET_DIMENSIONS and artifacts, 'evaluation_review_scenario')
    rows = {}
    for aid, value in artifacts.items():
        require(rel.text(aid) and set(value) == {'text', 'artifact_sha256', 'actual_method_materials', 'producing_request_ref'},
                'evaluation_anonymous_artifact')
        require(isinstance(value['text'], str) and digest(value['text']) == value['artifact_sha256']
                and isinstance(value['actual_method_materials'], dict), 'evaluation_artifact_binding')
        request_path = Path(value['producing_request_ref'])
        producing = read_record(request_path)
        producing_intent = read_record(request_path.with_name('intent.json'))
        producing_outcome = read_record(request_path.with_name('outcome.json'))
        require(producing_intent.get('request_sha256') == digest(producing)
                and producing_intent.get('request_id') == producing.get('request_id')
                and producing_outcome.get('status') == 'complete'
                and producing_outcome.get('reply', {}).get('text') == value['text'],
                'evaluation_producing_request_binding')
        available = producing.get('loaded_methods')
        if available is None:
            available = producing.get('condition_packet', {}).get('loaded_methods', {})
        require(value['actual_method_materials'] == available, 'evaluation_actual_load_mismatch')
        for material in value['actual_method_materials'].values():
            import hashlib
            require({'path', 'sha256', 'content'} <= set(material) and
                    hashlib.sha256(material['content'].encode()).hexdigest() == material['sha256'],
                    'evaluation_method_material_binding')
        rows[aid] = deepcopy(value)
    return {'schema': 'mindthus.target-behavior-review.v1', 'rubric_version': rubric_version,
            'original_documents': deepcopy(case['packet']['documents']),
            'conversation': deepcopy(case['packet']['conversation']), 'source_limits': deepcopy(case['metadata']),
            'artifacts': rows, 'target_dimensions': deepcopy(TARGET_DIMENSIONS[scenario]),
            'instruction': 'Evaluate each actual text independently. Separate overall usability from each '
                'named target behavior; do not infer a pass from internal completion or other artifacts. '
                'Give pass/fail/not_assessable for every dimension with specific source and answer spans. '
                'A failure needs an actual decision consequence, not an omitted ceremonial sentence. '
                'Missing historical evidence cannot receive a retrospective pass. '
                'Equivalent valid routes may tie. Do not require disagreement with the user.'}


def validate_review(reply, request):
    require(isinstance(reply, dict) and set(reply) == {'artifacts'} and
            set(reply['artifacts']) == set(request['artifacts']), 'evaluation_review_coverage')
    docs = {d['id']: d for d in request['original_documents']}
    for aid, judgment in reply['artifacts'].items():
        require(set(judgment) == {'overall_usable', 'dimensions'}, 'evaluation_judgment_shape')
        require(judgment['overall_usable'] in ('yes', 'no', 'not_assessable'), 'evaluation_usable')
        require(set(judgment['dimensions']) == set(request['target_dimensions']), 'evaluation_target_coverage')
        text = request['artifacts'][aid]['text']
        for value in judgment['dimensions'].values():
            require(set(value) == {'verdict', 'reason', 'source_refs', 'answer_spans', 'decision_consequence'},
                    'evaluation_dimension_shape')
            require(value['verdict'] in ('pass', 'fail', 'not_assessable') and rel.text(value['reason'])
                    and isinstance(value['source_refs'], list) and isinstance(value['answer_spans'], list),
                    'evaluation_dimension_value')
            for ref in value['source_refs']:
                rc.check_ref(ref, docs)
            for span in value['answer_spans']:
                require(set(span) == {'start', 'end', 'sha256'} and type(span['start']) is int
                        and type(span['end']) is int and 0 <= span['start'] < span['end'] <= len(text)
                        and digest(text[span['start']:span['end']]) == span['sha256'], 'evaluation_answer_span')
            if value['verdict'] != 'not_assessable':
                require(value['source_refs'] and (value['answer_spans'] or not text), 'evaluation_verdict_needs_evidence')
            if value['verdict'] == 'fail':
                require(rel.text(value['decision_consequence']), 'evaluation_failure_consequence')
    return True
