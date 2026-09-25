"""Five bounded experimental conditions over the v0.3 contracts.

This module prepares/consumes current-Agent handoffs. It launches no model itself.
The optional observer callback is explicitly supplied by the experiment owner;
production admission remains official Jev only. Gold stays outside host packets.
"""
from pathlib import Path

from . import route_control_v03 as runtime, source_direct_v03 as sd, relationship_runtime as rt
from . import route_control as rc, relationship_assessment as rel
from .contracts import (BatchResult, DecisionResult, EngineIdentity, ServingIdentity,
                        ResolvedRuntime, digest, require)
from .current_host import AwaitingCurrentAgent, CurrentAgentHost
from .session import read_record

CONDITIONS = ('pure_codex', 'questions_only', 'codex_observation_committed',
              'jev_advisory', 'jev_committed')


class CurrentAgentObserver:
    """Explicit control backend; callback runs in a separate current-Codex context.

    Context/config fields are host declarations, not backend attestation.
    Session persists request/outcome and never retries an uncertain external intent.
    """
    is_live = True
    capabilities = frozenset({'select', 'assess_proposition', 'rate'})

    def __init__(self, observe, *, model, host_context_ref, configuration):
        require(callable(observe) and rel.text(model) and rel.text(host_context_ref)
                and isinstance(configuration, dict) and bool(configuration), 'comparison_observer_configuration')
        self.observe, self.model, self.host_context_ref = observe, model, host_context_ref
        self.configuration = {**configuration, 'model': model, 'host_context_ref': host_context_ref}
        self.configuration_sha256 = digest(self.configuration)
        self.engine_identity = EngineIdentity('structured_chat', 'current_agent_control', model)
        self.serving_identity = ServingIdentity('current_agent', 'isolated-observer.v1', model,
            'local://current-agent/' + digest(self.configuration), '1')
        self.receipt = None

    def clear_receipt(self):
        self.receipt = None

    def response_receipt(self):
        return self.receipt

    def validate_runtime(self, runtime):
        runtime.validate()
        require(runtime.model == self.model and runtime.provider == 'current-agent-declared',
                'comparison_observer_runtime_changed')

    def evaluate(self, specs, context, timeout):
        require(digest(self.configuration) == self.configuration_sha256, 'comparison_observer_configuration_changed')
        request = {'questions': [s.to_dict() for s in specs], 'state': context,
                   'configuration': rel.clone(self.configuration),
                   'instruction': 'In an independent context, answer the typed questions from the supplied '
                                  'sources only. Report unknown rather than inventing facts. Probability '
                                  'and rate values are uncalibrated estimates; do not invent native distributions.'}
        request['request_id'] = digest(request)
        reply = self.observe(request, timeout)
        # Reuse the existing safe decoded-response capture; a malformed answer must
        # retain inspectable raw evidence and any valid billed usage.
        from .providers import _JevReceipt
        capture = _JevReceipt()
        capture.capture_receipt(request, reply)
        self.receipt = {**capture.response_receipt(),
                        'schema': 'mindthus.current-agent-observation-receipt.v1',
                        'model_service_attestation': 'not_observed'}
        require(isinstance(reply, dict) and set(reply) == {'request_id','context_ref','configuration','answers','usage'},
                'comparison_observer_reply')
        require(reply['request_id'] == request['request_id'] and rel.text(reply['context_ref'])
                and reply['context_ref'] != self.host_context_ref
                and reply['configuration'] == self.configuration, 'comparison_observer_identity')
        rt._usage(reply['usage'])
        self.receipt['validated_usage'] = rel.clone(reply['usage'])
        require(set(reply['answers']) == {s.id for s in specs}, 'comparison_observer_answers')
        results = {}
        for spec in specs:
            item = reply['answers'][spec.id]
            try:
                rel.shape(item, {'status','value'}, 'comparison_observer_answer')
                result = DecisionResult(item['status'], item['value'], None, 'ordinary_llm_uncalibrated')
                result.validate(spec)
            except (ValueError, KeyError, TypeError):
                # Invalid single answers cannot erase legitimate judgments in the same batch.
                result = DecisionResult('provider_error', reason='answer_contract:current_agent_control')
            results[spec.id] = result
        self.receipt.update(request_id=request['request_id'], context_ref=reply['context_ref'],
                            configuration=rel.clone(self.configuration))
        return BatchResult(results, ResolvedRuntime(self.model, 'current-agent-declared'), reply['usage'])


def prepare_condition(packet, condition, repo):
    require(condition in CONDITIONS, 'comparison_condition')
    bundle, questions, bindings, contract = runtime._bundle(Path(repo))
    sd.validate_packet(packet, bindings)
    originals = {k: rel.clone(packet[k]) for k in ('documents','conversation','authority','intervention')}
    materials = rc._read_methods(Path(repo), {m['method'] for m in bindings['methods']}, bindings)
    body = {'schema': 'mindthus.comparison-condition.v1', 'condition': condition,
            'original_input': originals, 'loaded_methods': materials,
            'source_identity': digest(originals), 'method_identity': digest(materials),
            'contract_identity': digest(contract), 'source_bindings': bundle['sources'],
            'host_work_limits': {'execution': packet['task_budget']['max_calls'],
                                 'correction': 1, 'arbitration': 1}}
    if condition == 'questions_only':
        body['question_contract'] = {name: {k: value[k] for k in ('question','criteria')}
                                    for name,value in contract['candidate_checks'].items()}
        body['routing_questions'] = {name: {k: questions[name][k] for k in ('question','criteria','kind')}
            for name in ('G03','M02','M03','M05','R02','R03','R04','S01','S02')}
        body['routing_questions'].update({name: {k:value[k] for k in ('question','criteria')}
            for name,value in {**{'coverage_'+k:v for k,v in contract['coverage'].items()},
                               'method_scope':contract['method_scope'],
                               'companion_scope':contract['companion_scope']}.items()})
        body['checklist_instruction'] = ('Use these unfilled templates where applicable to your own task '
            'representation and candidate. No issue projection or expected answer is supplied.')
    return body


def validate_native_reply(reply, request):
    rel.shape(reply, {'schema','request_id','text','version','performed_methods','decision_status','dispute','usage'},
              'comparison_native_reply')
    require(reply['schema'] == 'mindthus.route-v03-native-reply.v1' and
            reply['request_id'] == request['request_id'] and rel.text(reply['text']) and
            reply['version'] == digest(reply['text']), 'comparison_native_binding')
    require(reply['decision_status'] in ('decided','unresolved','disputed') and
            isinstance(reply['performed_methods'], list) and
            set(reply['performed_methods']) <= set(request['condition_packet']['loaded_methods']),
            'comparison_native_decision')
    dispute = reply['dispute']
    require((dispute is not None) == (reply['decision_status'] == 'disputed'), 'comparison_dispute_status')
    if dispute is not None:
        rel.shape(dispute, {'reason','original_refs'}, 'comparison_dispute')
        require(rel.text(dispute['reason']) and bool(dispute['original_refs']), 'comparison_dispute_basis')
        docs = {d['id']:d for d in request['condition_packet']['original_input']['documents']}
        for ref in dispute['original_refs']: rc.check_ref(ref,docs)
    rt._usage(reply['usage'])


class _NoObserver:
    is_live = False
    capabilities = frozenset({'select'})
    engine_identity = EngineIdentity('host_only', 'no_observer', 'not_applicable')
    serving_identity = ServingIdentity('current_agent', 'host-only.v1', 'not_applicable', 'local://host-only')
    def evaluate(self, *_):
        raise AssertionError('native conditions do not invoke a decision provider')


def run_native(root, packet, repo, *, condition, executor, corrector, arbitrator=None, candidate_snapshot=None):
    """Natural first answer, one review, and receipt through the SAME host/Episode.

    Questions-only differs by an unfilled checklist; neither sees host-inferred
    issue frames, gold, another branch's answer, or an observer's filled answers.
    """
    require(condition in ('pure_codex','questions_only'), 'comparison_native_condition')
    repo, root = Path(repo).resolve(), Path(root).resolve()
    require(not root.is_relative_to(repo), 'state_root_inside_repository')
    owner = packet['authority']['owner_ref']
    require(isinstance(executor, CurrentAgentHost) and executor.identity == owner and
            isinstance(corrector, CurrentAgentHost) and corrector.identity == owner, 'comparison_native_host')
    prepared = prepare_condition(packet, condition, repo)
    bundle = runtime._bundle(repo)[0]
    profile = {**runtime.PROFILE, 'judgments_total': 0,
               'executions_total': packet['task_budget']['max_calls'],
               'execution_seconds': packet['task_budget']['max_seconds']}
    ep = rt.Episode(root, repo, _NoObserver(), packet, bundle, mode=sd.MODE,
                    profile=profile, kinds=runtime.STEP_KINDS, host_slots=runtime.HOST_SLOTS)
    ep.evidence_kind = 'current_agent_only'
    require(packet['authority']['risk'] == 'low' and packet['authority']['mode'] != 'none', 'comparison_low_risk_only')
    with ep:
        rt.save(root/'condition.json', {**prepared, 'candidate_snapshot': candidate_snapshot})
        rt.save(root/'intervention.json', packet['intervention'])
        directory = root/'turns'/ep.turn_key/'inputs'/digest(packet)
        rt.save(directory/'manifest.json', {'condition': prepared, 'input_hash': digest(packet)})
        summary = directory/'summary.json'
        if summary.exists(): return read_record(summary)
        initial, revised, acceptance, arbitration = None, None, None, None
        def result(reason=None):
            tally = ep.tally()
            return {'condition': condition, 'initial': initial, 'reviewed': revised, 'acceptance': acceptance,
                    'arbitration': arbitration, 'counts': tally['counts'], 'usage': tally['usage'], 'reason': reason,
                    'host_evidence_kind': 'current_agent_submission', 'judgment_evidence_kind': 'not_used',
                    'semantic_correctness': 'not_scored', 'qualification': False,
                    'consumption_complete': bool(acceptance and acceptance['accepted']['task']['accepted'])}
        try:
            steps = [('execution__native', executor, 'execute'), ('correction', corrector, 'correct')]
            if candidate_snapshot is not None:
                validate_snapshot(candidate_snapshot,packet,repo)
                require(len(candidate_snapshot['outputs']) == 1, 'common_candidate_single_task')
                candidate = next(iter(candidate_snapshot['outputs'].values()))
                initial = {'text':candidate['text'], 'version':candidate['artifact_sha256'],
                           'provenance':candidate_snapshot['provenance']}
                steps = steps[1:]
            for step, host, role in steps:
                body = {'schema':'mindthus.route-v03-native-request.v1', 'mode':sd.MODE,
                        'policy':condition, 'condition_packet':prepared,
                        'candidate': initial['text'] if initial else None,
                        'instruction': 'Produce your natural route decision and task answer.' if initial is None else
                                       'Review your answer once against the original task. Keep it or revise. '
                                       'Preserve unresolved facts and authority. This is the only revision opportunity.'}
                body['request_id'] = digest(body)
                out = rt._host(ep,directory,step,body,host,lambda r:validate_native_reply(r,body),
                               operation=role, expected_owner=owner)
                if out['status'] != 'complete':
                    value=result('native_host_failed');rt.save(summary,value);return value
                if initial is None: initial=out['reply']
                else: revised=out['reply']
            route={'route_id':digest(prepared),'revision':1,'contract_hashes':bundle['sources']}
            outputs={'task': {'text':revised['text'],'artifact_sha256':revised['version']}}
            resolved = revised['decision_status']=='decided'
            rt.save(directory/'before-arbitration.json', {'initial':initial,'review':revised})
            if revised['dispute'] is not None and arbitrator is not None:
                finding = {'finding_id':digest(revised['dispute']), 'issue_id':'task','check_id':'host_dispute',
                    'target_version':revised['version'], 'meaning':revised['dispute']['reason'],
                    'source_refs':revised['dispute']['original_refs'], 'value':'host_dispute',
                    'status':'host_reported', 'affected_action':'task'}
                report = {'findings':[finding],'matrix':[]}
                disputed = sd.correction_request(packet,route,outputs,report)
                reply = {'dispositions':[{'finding_id':finding['finding_id'],'decision':'objected',
                                         **revised['dispute']}]}
                request = sd.arbitration_request(packet,route,disputed,reply,out['host_context_ref'],outputs,report)
                judged=rt._host(ep,directory,'arbitration',request,arbitrator,
                    lambda r:sd.validate_arbitration(r,request),operation='arbitrate',expected_owner=owner+':route-arbitrator')
                if judged['status']=='complete':
                    arbitration=judged['reply'];resolved=all(d['decision']=='dismiss' for d in arbitration['decisions'])
            request=sd.acceptance_request(packet,route,outputs,
                {'task':'resolved' if resolved else 'unresolved'},
                {'initial':initial,'review':revised,'arbitration':arbitration,'observer':'not_used'})
            out=rt._host(ep,directory,'execution__accept',request,executor,
                         lambda r:sd.validate_acceptance(r,request),operation='accept',expected_owner=owner)
            if out['status']=='complete': acceptance=out['reply']
            value=result(None if acceptance and acceptance['accepted']['task']['accepted'] else 'unresolved_or_unaccepted')
            rt.save(summary,value);return value
        except AwaitingCurrentAgent as exc:
            return {**result('awaiting_current_agent'),'status':'awaiting_current_agent','host_request':exc.handoff_path}
        except rt.EpisodeStop as exc:
            value=result(str(exc));rt.save(summary,value);return value


def run_condition(root, provider, packet, repo, *, condition, executor, corrector,
                  arbitrator=None, organizer=None, live_admission=None, artifact_acceptor=None, candidate_snapshot=None):
    require(condition in CONDITIONS, 'comparison_condition')
    if condition in ('pure_codex','questions_only'):
        require(provider is None and live_admission is None, 'native_has_no_observer')
        return run_native(root,packet,repo,condition=condition,executor=executor,corrector=corrector,
                          arbitrator=arbitrator,candidate_snapshot=candidate_snapshot)
    expected='advisory' if condition=='jev_advisory' else 'committed'
    require(packet['consumption_policy']==expected, 'comparison_policy_frozen')
    if condition=='codex_observation_committed':
        require(isinstance(provider,CurrentAgentObserver), 'comparison_codex_observer_required')
    else:
        require(not isinstance(provider,CurrentAgentObserver), 'comparison_backend_mismatch')
    return runtime.run(root,provider,packet,repo,executor=executor,corrector=corrector,
                       arbitrator=arbitrator,organizer=organizer,live_admission=live_admission,
                       artifact_acceptor=artifact_acceptor,candidate_snapshot=candidate_snapshot)


def common_candidate(packet, candidates, repo, *, provenance):
    require(isinstance(provenance, dict) and set(provenance) == {'author_ref','context_ref','source_ref'}
            and all(rel.text(x) for x in provenance.values()), 'common_candidate_provenance')
    bundle, _, bindings, _ = runtime._bundle(Path(repo))
    sd.validate_packet(packet,bindings)
    require(set(candidates) == {i['id'] for i in packet['issues']} and
            all(rel.text(text) for text in candidates.values()), 'common_candidate_issues')
    outputs={iid:{'text':text,'artifact_sha256':digest(text),'revision':1,
                  'accepted_uses':{},'methods':[],'input_artifacts':{}} for iid,text in candidates.items()}
    route={'route_id':digest([packet['documents'],candidates]),'revision':1,
           'contract_hashes':bundle['sources'], 'artifact_edges':[],
           'status':'common_candidate_diagnostic_no_route_commitment'}
    return {'route':route,'outputs':outputs,'provenance':provenance,
            'history_sha256':sd.history_identity(packet)}


def validate_snapshot(snapshot, packet, repo):
    expected=common_candidate(packet,{iid:o['text'] for iid,o in snapshot['outputs'].items()},
                              repo,provenance=snapshot['provenance'])
    require(snapshot==expected,'common_candidate_snapshot_changed')


def prepare_campaign(families, repo, *, host_configuration):
    """Pure preparation: returns separate host and reviewer packages, no requests.

    Twelve source families are required for N; synthetic/exposed families keep a
    development label and cannot be renamed into independent-source qualification.
    """
    require(isinstance(host_configuration,dict) and
            set(host_configuration)=={'model','reasoning_effort','tools_sha256','output_limit'},
            'comparison_host_configuration')
    require(len(families)==12 and len({f['family_id'] for f in families})==12,'comparison_family_count')
    require(sorted(f['scenario'] for f in families[:4])==['E','E','F','F'] and
            sorted(f['scenario'] for f in families[4:])==['A','B','C','D','E','E','F','F'],
            'comparison_stage_order')
    hosts, reviewers, seen=set(), [], set()
    host_packets=[]
    for index,family in enumerate(families):
        rel.shape(family,{'family_id','scenario','source_kind','origin_ref','packet','acceptance'},'comparison_family')
        require(family['source_kind'] in ('external_unexposed','historical_exposed','synthetic') and
                rel.text(family['origin_ref']) and isinstance(family['acceptance'],dict) and family['acceptance'],
                'comparison_source_identity')
        identity=sd.history_identity(family['packet'])
        require(identity not in seen and family['origin_ref'] not in hosts,'comparison_duplicate_source')
        seen.add(identity);hosts.add(family['origin_ref'])
        # Prebalanced rotation is frozen before any result; every condition stays in the denominator.
        order=CONDITIONS[index%5:]+CONDITIONS[:index%5]
        branch_packets=[]
        for condition in order:
            value=prepare_condition(family['packet'],condition,repo)
            branch_packets.append(value)
        host_packets.append({'family_id':family['family_id'],'scenario':family['scenario'],
                             'source_kind':family['source_kind'],'origin_ref':family['origin_ref'],
                             'conditions':branch_packets})
        reviewers.append({'family_id':family['family_id'],'acceptance':family['acceptance']})
    body={'host_configuration':host_configuration,'families':host_packets,
          'source_qualification':'independent_sources' if all(f['source_kind']=='external_unexposed' for f in families)
                                 else 'development_only',
          'max_jev_requests':92,'source_results':{f['family_id']:'unrun' for f in families}}
    return {'manifest':body,'manifest_sha256':digest(body),'reviewer_only':reviewers}
