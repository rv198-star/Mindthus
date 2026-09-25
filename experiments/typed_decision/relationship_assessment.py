"""D1: bounded relationship contracts, provenance validation and offline consumption.

No host correction, live admission, episode ledger, or automatic skill activation.
Semantic expectations belong to separate development fixtures, never model State.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .contracts import DecisionResult, DecisionSpec, canonical, digest, require

VERSION = '1.2'
POLICY = 'mindthus.relationship-frame.v1.2'
CONTRACT = ('docs/internal/research/typed-decision/entry-assessment/'
            'original-scenarios-design/relationship-contracts-v0.3.3.json')
ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,31}$')
FRAME_FIELDS = ('actor', 'object', 'time', 'goal', 'scope')
REF_FIELDS = {'document_id', 'revision', 'start', 'end', 'sha256'}


def clone(value: Any) -> Any:
    return json.loads(canonical(value))


def shape(value: Any, keys: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == keys, 'invalid_' + label)


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def identifier(value: Any) -> bool:
    return isinstance(value, str) and ID.fullmatch(value) is not None


def quote(document: dict, start: int = 0, end: int | None = None) -> dict:
    """Quote offsets are Unicode codepoints; hashes cover exact UTF-8 slice bytes."""
    end = len(document['text']) if end is None else end
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(document['text']),
            'invalid_quote_span')
    return {'document_id': document['id'], 'revision': document['revision'],
            'start': start, 'end': end,
            'sha256': hashlib.sha256(document['text'][start:end].encode('utf8')).hexdigest()}


def load_contract(repo: Path) -> tuple[dict, dict]:
    repo = Path(repo).resolve()
    contract = json.loads((repo / CONTRACT).read_bytes())
    require(contract.get('schema') == 'mindthus.relationship-contract.v1'
            and contract.get('policy') == POLICY and contract.get('version') == VERSION,
            'relationship_contract_version_changed')
    rules = {}
    for path, binding in contract['sources'].items():
        file = (repo / path).resolve()
        require(file.is_relative_to(repo), 'source_outside_repository')
        raw = file.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == binding['sha256'], 'canonical_source_changed')
        lines = raw.decode('utf8').splitlines(keepends=True)
        pieces = []
        for start, end in binding['ranges']:
            require(1 <= start <= end <= len(lines), 'source_line_range_invalid')
            pieces.append(''.join(lines[start-1:end]))
        rules[path] = {'source_sha256': binding['sha256'], 'excerpts': pieces}
    return contract, rules


def _validate(packet: dict, limits: dict) -> dict[str, dict]:
    shape(packet, {'schema', 'episode_id', 'turn_id', 'revision', 'stage', 'documents',
                   'proposal', 'authority', 'activation'}, 'packet')
    require(packet['schema'] == 'relationship-input.v1', 'packet_version')
    require(all(text(packet[x]) for x in ('episode_id', 'turn_id', 'revision')), 'input_identity')
    require(packet['stage'] in ('S0', 'S1', 'S2'), 'invalid_stage')
    require(len(canonical(packet)) <= limits['input_bytes'], 'coverage_overflow:input_bytes')
    documents = packet['documents']
    require(isinstance(documents, list) and 0 < len(documents) <= limits['documents'],
            'coverage_overflow:documents')
    docs = {}
    for doc in documents:
        shape(doc, {'id', 'revision', 'kind', 'text'}, 'document')
        require(identifier(doc['id']) and doc['id'] not in docs, 'document_identity')
        require(text(doc['revision']) and text(doc['text']), 'empty_document')
        require(doc['kind'] in ('user', 'assistant', 'source', 'candidate'), 'document_kind')
        docs[doc['id']] = doc

    def refs(values, *, kinds=None, required=False, inside=None):
        require(isinstance(values, list) and len(values) <= limits['quotes_per_slot']
                and (bool(values) or not required), 'invalid_reference_list')
        for ref in values:
            shape(ref, REF_FIELDS, 'reference')
            require(identifier(ref['document_id']) and ref['document_id'] in docs, 'unknown_document')
            doc = docs[ref['document_id']]
            require(kinds is None or doc['kind'] in kinds, 'reference_origin_mismatch')
            require(type(ref['start']) is int and type(ref['end']) is int,
                    'reference_offsets_must_be_integers')
            require(quote(doc, ref['start'], ref['end']) == ref, 'reference_digest_or_revision')
            if inside:
                require(ref['document_id'] == inside['document_id']
                        and inside['start'] <= ref['start'] < ref['end'] <= inside['end'],
                        'candidate_location_outside_target')

    p = packet['proposal']
    shape(p, {'frames', 'candidate', 'scope_correction_refs', 'claims', 'edges',
              'user_premise', 'competitions'}, 'proposal')
    require(isinstance(p['frames'], list) and 1 <= len(p['frames']) <= limits['frames'],
            'coverage_overflow:frames')
    frame_ids = set()
    for frame in p['frames']:
        shape(frame, {'id', 'kind', *FRAME_FIELDS}, 'frame')
        require(identifier(frame['id']) and frame['id'] not in frame_ids, 'frame_identity')
        frame_ids.add(frame['id'])
        require(frame['kind'] in ('definition', 'decision', 'explanation'), 'frame_kind')
        for field in FRAME_FIELDS:
            item = frame[field]
            shape(item, {'text', 'origin', 'refs'}, 'frame_field')
            require(item['origin'] in ('explicit', 'inferred', 'unstated'), 'frame_field_origin')
            if item['origin'] == 'unstated':
                require(item['text'] == '' and item['refs'] == [], 'unstated_has_claim')
            else:
                require(text(item['text']), 'empty_frame_field')
                refs(item['refs'], kinds={'user', 'source'} if item['origin'] == 'explicit' else None, required=True)
    candidate = p['candidate']
    if candidate is not None:
        shape(candidate, {'ref', 'thesis_refs', 'controller_refs', 'discriminator_refs'}, 'candidate')
        require(packet['stage'] != 'S0', 'candidate_in_S0')
        refs([candidate['ref']], kinds={'candidate'}, required=True)
        for key in ('thesis_refs', 'controller_refs', 'discriminator_refs'):
            refs(candidate[key], kinds={'candidate'}, inside=candidate['ref'])
    else:
        require(packet['stage'] == 'S0', 'candidate_required_for_S1_S2')
    refs(p['scope_correction_refs'], kinds={'user'})
    for name in ('claims', 'edges', 'competitions'):
        require(isinstance(p[name], list) and len(p[name]) <= limits[name], 'coverage_overflow:' + name)
    claim_ids = set()
    for claim in p['claims']:
        shape(claim, {'id', 'text', 'origin', 'refs'}, 'claim')
        require(identifier(claim['id']) and claim['id'] not in claim_ids, 'claim_identity')
        claim_ids.add(claim['id'])
        require(text(claim['text']), 'claim_text')
        require(claim['origin'] in ('source_observation', 'user_hypothesis', 'host_interpretation'),
                'claim_origin')
        kind = {'source_observation': {'source'}, 'user_hypothesis': {'user'}}.get(claim['origin'])
        refs(claim['refs'], kinds=kind, required=True)
    edge_ids = set()
    for edge in p['edges']:
        shape(edge, {'id', 'frame_id', 'premise_refs', 'conclusion_refs'}, 'edge')
        require(identifier(edge['id']) and edge['id'] not in edge_ids, 'edge_identity')
        edge_ids.add(edge['id'])
        require(edge['frame_id'] in frame_ids, 'edge_frame')
        refs(edge['premise_refs'], required=True)
        refs(edge['conclusion_refs'], required=True)
    if p['user_premise'] is not None:
        shape(p['user_premise'], {'premise_refs', 'target_refs'}, 'user_premise')
        refs(p['user_premise']['premise_refs'], kinds={'user'}, required=True)
        refs(p['user_premise']['target_refs'], required=True)
    competition_frames = set()
    for item in p['competitions']:
        shape(item, {'frame_id', 'left_refs', 'right_refs'}, 'competition')
        require(item['frame_id'] in frame_ids and item['frame_id'] not in competition_frames,
                'competition_frame')
        competition_frames.add(item['frame_id'])
        refs(item['left_refs'], required=True)
        refs(item['right_refs'], required=True)
    auth = packet['authority']
    shape(auth, {'owner_ref', 'risk', 'mode', 'known_obligations'}, 'authority')
    require(text(auth['owner_ref']) and auth['risk'] in ('low', 'high', 'unknown'), 'authority_owner_risk')
    require(auth['mode'] in ('advisory', 'read_only', 'none'), 'authority_mode')
    require(isinstance(auth['known_obligations'], list)
            and all(text(v) for v in auth['known_obligations']), 'known_obligations')
    activation = packet['activation']
    shape(activation, {'enabled', 'source_refs', 'reason'}, 'activation')
    require(type(activation['enabled']) is bool and text(activation['reason']), 'activation_fields')
    refs(activation['source_refs'], required=activation['enabled'])
    return docs


@dataclass(frozen=True)
class Compiled:
    packet: dict
    identity: dict
    context: dict
    specs: tuple[DecisionSpec, ...]
    bindings: tuple[dict, ...]
    skip_reason: str | None


def compile_packet(packet: dict, repo: Path) -> Compiled:
    contract, rules = load_contract(repo)
    limits = contract['budgets']
    _validate(packet, limits)
    packet = clone(packet)
    proposal = packet['proposal']
    candidate = proposal['candidate']
    skip = ('not_activated' if not packet['activation']['enabled'] else
            'authority_outside_scope' if packet['authority']['risk'] != 'low'
            or packet['authority']['mode'] == 'none' else None)
    context = {'original_documents': packet['documents'], 'proposal_view': proposal,
               'authority': packet['authority'], 'canonical_rules': rules}
    specs, bindings = [], []

    def add(family: str, *, frame=None, claim=None, edge=None, subject=None):
        parts = [family] + [x for x in (frame, claim, edge) if x is not None]
        qid = '.'.join(parts)
        binding = {'id': qid, 'family': family, 'frame_id': frame, 'claim_id': claim,
                   'edge_id': edge, 'subject': subject or {}}
        template = contract['templates'][family]
        question = template['question'] + '\nBinding (host proposal, not fact): ' + canonical(binding).decode('utf8')
        spec = DecisionSpec(qid, question, clone(template['criteria']), tuple(context),
                            version=VERSION, policy_ref=POLICY)
        spec.validate()
        specs.append(spec)
        bindings.append(binding)

    if skip is None:
        add('q0')
        choices = {f"frame.{f['id']}": '; '.join(k + ': ' + (f[k]['text'] or '[unstated]')
                                                for k in FRAME_FIELDS) for f in proposal['frames']}
        choices.update(none='No supplied frame covers the original request.',
                       ambiguous='Material does not distinguish a unique frame.',
                       multiple_requests='User genuinely asks multiple different questions.')
        q1 = DecisionSpec('q1', 'Select the actual task frame from original text and legitimate scope. '
                          'Scope correction does not prove the rest of the user conclusion. '
                          'Use readable frame definitions, not scenario keywords.',
                          choices, tuple(context), version=VERSION, policy_ref=POLICY)
        q1.validate()
        specs.append(q1)
        bindings.append({'id':'q1','family':'q1','frame_id':None,'claim_id':None,'edge_id':None,'subject':{}})
        if candidate and proposal['scope_correction_refs']:
            add('scope_acceptance', subject={'scope_refs':proposal['scope_correction_refs'],
                                             'candidate_ref':candidate['ref']})
        if candidate:
            for f in proposal['frames']:
                add('alignment', frame=f['id'])
        for e in proposal['edges']:
            add('local_transfer', frame=e['frame_id'], edge=e['id'], subject=e)
        if proposal['user_premise']:
            add('user_adoption', subject=proposal['user_premise'])
        for c in proposal['claims']:
            add('support', claim=c['id'])
        for f in proposal['frames']:
            for c in proposal['claims']:
                add('role', frame=f['id'], claim=c['id'])
        if candidate and len(proposal['claims']) == 2:
            for f in proposal['frames']:
                add('joint', frame=f['id'], subject={'claim_ids':[c['id'] for c in proposal['claims']],
                    'preconditions':contract['templates']['joint']['consume_preconditions']})
        for f in proposal['frames']:
            add('readiness', frame=f['id'])
            if candidate:
                add('delivery', frame=f['id'])
                if f['kind'] == 'definition':
                    add('definition', frame=f['id'])
        for pair in proposal['competitions']:
            add('competition', frame=pair['frame_id'], subject=pair)
    require(len(specs) <= limits['questions_per_batch'], 'coverage_overflow:questions')
    projection = {'state':context,'questions':[s.to_dict() for s in specs]}
    require(len(canonical(projection)) <= limits['projected_request_bytes'], 'coverage_overflow:projection')
    identity = {'policy':POLICY,'version':VERSION,'packet_sha256':digest(packet),
                'contract_sha256':digest(contract),'sources':clone(contract['sources']),
                'projection_sha256':digest(projection),'bindings_sha256':digest(bindings),
                'projected_request_bytes':len(canonical(projection))}
    return Compiled(packet, identity, context, tuple(specs), tuple(bindings), skip)


REMEDIES = {
    'restore_scope': 'Restore the valid object/situation from the original request without accepting unrelated conclusions.',
    'qualify_local_transfer': 'Keep the supported local truth and evaluate its actual authority over the same-object conclusion.',
    'qualify_user_premise': 'Keep the user proposition as a hypothesis unless independent supplied evidence establishes it.',
    'rebuild_same_object': 'Explain the same object through supported target-job/result-control relations. A simple mechanism may suffice; do not invent a richer opponent.',
    'retract_unsupported_alternative': 'Withdraw unsupported opposing claims; preserve supported material and the user scope.',
    'deliver_verdict': 'State a supported situated judgment rather than only listing viewpoints; retain its limits.',
    'state_conditions': 'State the concrete unresolved user tradeoff and its corresponding conditional choices.',
    'explain_joint_relation': 'Explain the supported joint or conditional relation among factors; do not vote or force one factor to dominate.',
    'compare_supported_accounts': 'Compare strongest supported accounts within the same object on a result-changing difference.'
}


def consume(compiled: Compiled, response: dict, repo: Path) -> dict:
    """Pure consumption of bound typed results, never truth certification or execution."""
    require(isinstance(compiled, Compiled), 'compiled_type')
    fresh = compile_packet(compiled.packet, repo)
    require(compiled == fresh, 'compiled_input_or_contract_changed')
    shape(response, {'identity', 'results'}, 'response')
    require(response['identity'] == compiled.identity, 'response_identity_changed')
    require(isinstance(response['results'], dict)
            and set(response['results']) == {s.id for s in compiled.specs}, 'answer_ids_changed')
    results = {s.id: DecisionResult.from_dict(response['results'][s.id], s) for s in compiled.specs}
    rows = [{**clone(b), **clone(response['results'][b['id']]), 'consumed': False,
             'unconsumed_reason': 'prerequisite_not_met'} for b in compiled.bindings]
    by_id = {r['id']:r for r in rows}
    packet, p = compiled.packet, compiled.packet['proposal']
    auth, candidate = packet['authority'], p['candidate']

    def val(key):
        answer = results.get(key)
        return answer.value if answer and answer.status == 'ok' else None

    def ret(reason, failed=()):
        return {'action':'return_original_owner','reason':reason,'identity':clone(compiled.identity),
                'original_packet_ref':compiled.identity['packet_sha256'], 'failed_check_refs':list(failed),
                'known_obligations':clone(auth['known_obligations']),'matrix':rows,
                'task_complete':False,'qualification':False}

    if compiled.skip_reason:
        return ret(compiled.skip_reason)
    by_id['q0']['consumed'], by_id['q0']['unconsumed_reason'] = True, None
    if val('q0') != 'usable':
        return ret('mapping_not_usable', ['q0'])
    by_id['q1']['consumed'], by_id['q1']['unconsumed_reason'] = True, None
    selected = next((f for f in p['frames'] if val('q1') == 'frame.' + f['id']), None)
    if selected is None:
        return ret('frame_not_unique', ['q1'])
    fid = selected['id']
    for row in rows:
        if row['id'] in ('q0', 'q1'):
            continue
        if row['frame_id'] not in (None, fid):
            row['unconsumed_reason'] = 'unconsumed_speculative:unselected_frame'
            continue
        if row['family'] == 'role' and val('support.' + row['claim_id']) != 'source_supported':
            row['unconsumed_reason'] = 'unconsumed_speculative:source_not_supported'
            continue
        if row['family'] == 'joint' and not all(
                val('support.' + c['id']) == 'source_supported'
                and val('role.' + fid + '.' + c['id']) == 'decision_driver' for c in p['claims']):
            row['unconsumed_reason'] = 'unconsumed_speculative:two_supported_drivers_absent'
            continue
        row['consumed'], row['unconsumed_reason'] = True, None
    unknown = [r['id'] for r in rows if r['consumed'] and
               (r['status'] != 'ok' or r['value'] in ('uncertain', 'unresolved'))]
    if unknown:
        return ret('unresolved_evaluation', unknown)
    contradictions = [r['id'] for r in rows if r['consumed'] and
                      r['value'] in ('source_contradicted', 'conflicting_verdicts')]
    if contradictions:
        return ret('source_or_verdict_contradiction', contradictions)
    if val('readiness.' + fid) == 'need_named_fact' or val('delivery.' + fid) == 'named_evidence_gap':
        return ret('named_fact_requires_original_owner', ['readiness.' + fid])
    if candidate and val('definition.' + fid) == 'grounded_object_account':
        need = ['thesis_refs','controller_refs']
        if val('competition.' + fid) == 'material_comparison':
            need.append('discriminator_refs')
        if any(not candidate[k] for k in need):
            return ret('reference_gap', ['definition.' + fid])
    for row in rows:
        if row['consumed'] and row['family'] == 'joint' and row['value'] == 'not_applicable':
            return ret('joint_precondition_disagreement', [row['id']])
        if row['consumed'] and row['family'] == 'competition' and row['value'] == 'missing_candidate':
            return ret('missing_competing_material', [row['id']])
    repairs = []
    mapping = {
        'scope_acceptance': {'not_preserved':'restore_scope'},
        'alignment': {x:'restore_scope' for x in ('object_substituted','situation_substituted','multiple_substitutions')},
        'local_transfer': {'local_overreach':'qualify_local_transfer'},
        'user_adoption': {'unsupported_user_adoption':'qualify_user_premise'},
        'definition': {'carrier_only_unjustified':'rebuild_same_object','account_missing':'rebuild_same_object',
                       'unsupported_alternative':'retract_unsupported_alternative'},
        'joint': {'joint_account_missing':'explain_joint_relation'},
        'competition': {'weak_counterframe':'compare_supported_accounts'},
        'delivery': {'other_question':'restore_scope'},
    }
    for row in rows:
        if not row['consumed']:
            continue
        remedy = mapping.get(row['family'], {}).get(row['value'])
        if row['family'] == 'delivery':
            if row['value'] == 'list_only' and val('readiness.' + fid) == 'decide_now':
                remedy = 'deliver_verdict'
            if (row['value'] == 'verdict_with_basis' and val('readiness.' + fid) == 'conditional_decision'
                    and selected['kind'] == 'decision'):
                remedy = 'state_conditions'
        if remedy:
            repairs.append({'kind':remedy,'check_ref':row['id'],'instruction':REMEDIES[remedy],
                            'subject':clone(row['subject']), 'frame_id':row['frame_id'],
                            'target_ref':clone(candidate['ref']) if candidate else None})
    if repairs and candidate is None:
        return ret('frame_signal_without_candidate', [r['check_ref'] for r in repairs])
    scope_acceptance = True if val('scope_acceptance') == 'preserved' else (
                       False if val('scope_acceptance') == 'not_preserved' else None)
    if not repairs:
        if auth['known_obligations']:
            return ret('known_obligation_retained')
        return {'action':'continue_original','identity':clone(compiled.identity),'matrix':rows,
                'scope_acceptance':scope_acceptance,'known_obligations':[],
                'task_complete':False,'qualification':False}
    preserve = []
    if val('scope_acceptance') in ('preserved','not_preserved'):
        preserve += [{'kind':'user_constraint','ref':clone(ref)} for ref in p['scope_correction_refs']]
    for claim in p['claims']:
        kind = claim['origin']
        if kind == 'source_observation':
            if val('support.' + claim['id']) != 'source_supported':
                continue
            kind = 'source_supported_in_supplied_material'
        preserve += [{'kind':kind,'ref':clone(ref)} for ref in claim['refs']]
    plan = {'schema':'mindthus.relationship-correction-plan.v1','identity':clone(compiled.identity),
            'owner_ref':auth['owner_ref'],'permissions':{'risk':auth['risk'],'mode':auth['mode']},
            'preserve_refs':preserve,'repair_relations':repairs,'answer_under':clone(selected),
            'needs':['user_tradeoff'] if val('readiness.' + fid) == 'conditional_decision' else [],
            'known_obligations':clone(auth['known_obligations']),'task_complete':False,'qualification':False}
    return {'action':'request_correction','identity':clone(compiled.identity),'plan':plan,'matrix':rows,
            'scope_acceptance':scope_acceptance,'known_obligations':clone(auth['known_obligations']),
            'task_complete':False,'qualification':False}


def assess_offline(session, packet: dict, repo: Path) -> dict:
    """Use the existing journal seam for fixtures only; no live gate is removed."""
    require(getattr(session.provider, 'is_live', None) is False
            and session.evidence_kind == 'offline_fixture'
            and session.live_admission is None, 'relationship_live_not_admitted')
    compiled = compile_packet(packet, repo)
    answers = session.evaluate(list(compiled.specs), compiled.context) if compiled.specs else {}
    response = {'identity':compiled.identity,'results':{k:asdict(v) for k,v in answers.items()}}
    result = consume(compiled, response, repo)
    graph = {'id':'mindthus.relationship-frame','version':VERSION,
             'contract_sha256':compiled.identity['contract_sha256'],
             'source_bindings':compiled.identity['sources']}
    return session.finish(graph, packet, result)
