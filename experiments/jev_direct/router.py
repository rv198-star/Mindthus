"""Two-level direct routing: original input -> Jev -> source-bound method dispatch.

No LLM organizer, catalog shortlist, hidden semantic retry, or answer-veto from an
uncertain method. Compact cards are a declared offline projection, not full text.
"""
from dataclasses import asdict
from itertools import combinations
from pathlib import Path
import hashlib
import json

from experiments.typed_decision.contracts import (DecisionSpec, ContractError, canonical,
    digest, require, provider_configuration, project_context)
from experiments.typed_decision.relationship_runtime import _locked, save
from experiments.typed_decision.session import Session, Limits, read_record, implementation_digest
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json
from .full_context import ROUTABLE

PACK_PATH=Path(__file__).with_name('routing_cards.json')
VERSION='direct-two-level.v1'


def file_hash(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_pack(repo):
    repo=Path(repo).resolve();pack=json.loads((repo/'experiments/jev_direct/routing_cards.json').read_text())
    require(pack['schema']=='mindthus.direct-routing-cards.v1','direct_pack_version')
    require(set(pack['cards'])==set(ROUTABLE)|{'using-mindthus','case-prep'},'direct_catalog_coverage')
    for relative,expected in pack['source_sha256'].items():
        p=repo/relative
        require(not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(repo),'direct_source_path')
        require(file_hash(p)==expected,'direct_source_changed')
    require({p for c in pack['cards'].values() for p in c['sources']}|{c['path'] for c in pack['primitives'].values()}==set(pack['source_sha256']), 'direct_source_manifest_coverage')
    return pack


def validate_input(raw):
    require(set(raw)=={'documents','conversation','authority'},'direct_original_fields')
    docs=raw['documents'];turns=raw['conversation']
    require(isinstance(docs,list) and docs and isinstance(turns,list) and turns,'direct_original_required')
    ids=set()
    for d in docs:
        require(set(d)=={'id','kind','revision','text'} and isinstance(d['id'],str) and
                isinstance(d['text'],str) and isinstance(d['revision'],str),'direct_document_shape')
        require(d['id'] not in ids and d['kind'] in ('user','assistant','source'),'direct_document_identity');ids.add(d['id'])
    by={d['id']:d for d in docs}
    require([t['order'] for t in turns]==sorted({t['order'] for t in turns}),'direct_original_order')
    for t in turns:
        require(t['document_id'] in by and by[t['document_id']]['kind']==t['role'],'direct_original_turn_binding')
    require(turns[-1]['role']=='user','direct_latest_user')
    require(raw['authority'].get('risk')=='low' and raw['authority'].get('mode')=='read_only','direct_read_only_pilot')


def initial_state(raw,pack):
    validate_input(raw)
    return {'original_input':json.loads(canonical(raw)),
            'routing_cards':json.loads(canonical(pack['cards'])),
            'cognitive_contracts':json.loads(canonical(pack['primitives'])),
            'interpretation':pack['evidence_boundary'],
            'routing_task':'Evaluate the actual current user task, using its original context. Do not solve it or treat reference examples as task facts. All methods are visible; none has been nominated by another model.',
            'additional_originals':{}}


def questions(state,pack):
    required=tuple(state)
    specs=[]
    def add(i,q,criteria,kind='select'):
        specs.append(DecisionSpec(i,q,criteria,required,kind=kind,version=VERSION,policy_ref=VERSION))
    binary={'true':'The specific proposition is supported by the supplied task and routing contracts.',
            'false':'The proposition is not supported, or its required conditions are absent.'}
    add('MODE','What handling fits the actual requested task? A method being relevant is different from being necessary. Missing background evidence need not prevent a bounded answer.',{
        'direct':'Clear ordinary task: answer or perform its deterministic read-only transformation without a named judgment method.',
        'judgment':'A real hard-judgment point benefits from one or more described methods.',
        'acquire':'A fact necessary for the requested conclusion is missing: give the supported part and identify the necessary missing input.',
        'explicit_helper':'The actual request explicitly invokes a non-routing helper such as case export; route to its authorized host, not an invented execution.',
        'unclear':'The method/handling remains unclear; still give a source-bounded response without claiming a committed method.'})
    add('EFFORT','What degree of method intervention is justified by the current task, considering avoidable loss and overhead?',[
        'Direct response; no named method needed.', 'One lightweight method pass or limited clarification.',
        'Bounded multiple perspectives or a small staged combination.', 'Deep, high-consequence reasoning subject to authority and evidence.'],'rate')
    scope={'whole':'The whole current user task, including still-live explicitly requested parts.'}
    for t in state['original_input']['conversation']:
        if t['role']=='user':scope[t['document_id']]='The requested scope in original user document '+t['document_id']+' as interpreted in the current task, not a superseded instruction.'
    roles={'none':'No execution-changing contribution; topical relevance alone is insufficient.',
           'primary':'Controls the main judgment for a current requested scope.',
           'support':'Provides a needed supporting judgment without taking the main conclusion.',
           'constraint':'Constrains evidence, authority, risk or execution while another method owns the main judgment.',
           'stage':'Needed for a distinct requested stage or separate subtask; not necessarily ready before a prerequisite result.',
           'unclear':'Potential contribution cannot yet be assigned reliably.'}
    for m in ROUTABLE:
        add('FIT.'+m,f'Is {m} substantively applicable to any live part of this task under its positive and exclusion conditions? Future explicitly requested stages may qualify conditionally.',binary,'assess_proposition')
        add('ROLE.'+m,f'What role should {m} have in this task? Use its own boundaries and neighboring methods; do not force a single winner for genuinely separate stages.',roles)
        add('SCOPE.'+m,f'Which original request scope would a real contribution by {m} serve? This answer is consumed only if that method is selected.',scope)
        add('READ.'+m,f'Is there a specific unresolved routing distinction for {m} that reading its original SKILL and methodology, beyond the detailed card, is likely to resolve? Mere relevance or future execution is not a reason to reread.',binary,'assess_proposition')
    add('COMPANION.mpg.sela','If MPG is needed, does its mainline rely on a system-efficiency or trend claim that requires the canonical SELA companion check before path strategy?',binary,'assess_proposition')
    add('COMPANION.sela.mpg','If SELA is needed, is a concrete carrier, exposure, path volatility or continue/exit commitment present, requiring the canonical MPG companion check before the final action judgment?',binary,'assess_proposition')
    for name,c in pack['primitives'].items():add('PRIMITIVE.'+name,c['question'],binary,'assess_proposition')
    add('THESIS','Which cognitive perspective should control the first visible thesis for the main requested judgment? Other relevant perspectives remain as support or constraints.',
        {'none':'No special cognitive perspective is needed.',**{k:v['instruction'] for k,v in pack['primitives'].items()}})
    for a,b in combinations(ROUTABLE,2):
        add('REL.'+a+'.'+b,f'For this task, what is the relationship between {a} (A) and {b} (B)? Speculatively assess the pair, but choose none when either makes no useful contribution. A before B requires a real output dependency, not thematic similarity.',{
            'none':'At least one method is unnecessary for the current task.',
            'independent':'Both contribute to distinct scopes without a prerequisite or support dependency.',
            'a_supports_b':'A supplies supporting judgment; B owns the controlling action or conclusion.',
            'b_supports_a':'B supplies supporting judgment; A owns the controlling action or conclusion.',
            'a_before_b':'B must use an established output of A before completing its requested stage.',
            'b_before_a':'A must use an established output of B before completing its requested stage.',
            'unclear':'Both may contribute, but their interaction is unresolved.'})
    for s in specs:s.validate()
    return specs


def value(answers,k,default=None):
    r=answers.get(k,{})
    return r.get('value',default) if r.get('status')=='ok' else default


def probability(answers,k):
    r=answers.get(k,{})
    if r.get('status')!='ok':return None
    probs=(r.get('uncertainty') or {}).get('probabilities')
    return probs.get(r.get('value')) if isinstance(probs,dict) else None


def requested_details(answers,pack):
    # Fixed budget ordering is visible. Deferred requests never silently count as read.
    wanted=[m for m in ROUTABLE if isinstance(value(answers,'READ.'+m),(int,float))
            and value(answers,'READ.'+m)>=pack['policy']['read_threshold']]
    wanted.sort(key=lambda m:(-value(answers,'READ.'+m),m))
    cap=pack['policy']['max_detail_topics']
    return wanted[:cap],wanted[cap:]


def expanded_state(state,names,pack,repo):
    changed=json.loads(canonical(state))
    for m in names:
        require(m in ROUTABLE,'direct_detail_target')
        for p in pack['cards'][m]['sources']:
            require(file_hash(Path(repo)/p)==pack['source_sha256'][p],'direct_detail_changed')
            changed['additional_originals'][p]=(Path(repo)/p).read_bytes().decode('utf8')
    require(len(canonical(changed))<=pack['policy']['max_state_bytes'],'direct_detail_capacity')
    return changed


def consume(answers,pack):
    mode=value(answers,'MODE','unclear');selected={};uncertain=[]
    for m in ROUTABLE:
        role=value(answers,'ROLE.'+m,'unclear');p=probability(answers,'ROLE.'+m)
        if role not in ('none','unclear') and p is not None and p>=pack['policy']['role_min_probability']:
            selected[m]={'role':role,'scope':value(answers,'SCOPE.'+m,'whole'),'fit':value(answers,'FIT.'+m)}
        elif role!='none':uncertain.append(m)
    # Modes are dispositions, never permission to invent facts or suppress all output.
    # Global handling is a hint; independently executable scoped work survives acquire/unclear.
    companion_checks={};companion_refs=set();unconfirmed=[]
    for owner,companion in (('mpg','sela'),('sela','mpg')):
        if owner not in selected:continue
        observed=value(answers,'COMPANION.'+owner+'.'+companion)
        companion_refs.add(companion)
        needed=isinstance(observed,(int,float)) and observed>=pack['policy']['optional_primitive_threshold']
        companion_checks[owner]={'companion':companion,'observed_need':observed,'required_scope':selected[owner]['scope'],
            'state':'required' if needed else 'needs_execution_scope_check',
            'division':'SELA calibrates direction; MPG owns the concrete carrier/path action. Separate scopes may retain distinct theses.',
            'rule':'This observation never waives the full SKILL obligation. Check its actual condition during method execution; use the preloaded companion if required, or state a source-based route objection.'}
        if needed:
            selected.setdefault(companion,{'role':'support' if companion=='sela' else 'primary',
                'scope':selected[owner]['scope'],'fit':value(answers,'FIT.'+companion),'source':'canonical_companion_observation'})
        covering=(companion in selected and (selected[companion]['scope']=='whole' or selected[companion]['scope']==selected[owner]['scope']))
        if not covering:
            unconfirmed.append(owner)
            companion_checks[owner]['state']='needs_scoped_execution_check'
        elif not needed:companion_checks[owner]['state']='included_in_same_scope'
    relationships=[];edges=[]
    for a,b in combinations(sorted(selected),2):
        # Template keys follow ROUTABLE order, not alphabetic order.
        x,y=sorted((a,b),key=ROUTABLE.index);r=value(answers,'REL.'+x+'.'+y,'unclear')
        relationships.append({'a':x,'b':y,'relation':r})
        if r in ('a_before_b','a_supports_b'):edges.append((x,y))
        if r in ('b_before_a','b_supports_a'):edges.append((y,x))
    if 'sela' in selected and 'mpg' in selected and any(c['state']=='required' for c in companion_checks.values()):
        edges.append(('sela','mpg'))
    remaining=set(selected);order=[]
    while remaining:
        ready=sorted(m for m in remaining if not any(t==m and f in remaining for f,t in edges))
        if not ready:break
        order+=ready;remaining-=set(ready)
    # Resource loading may be deterministic while execution order remains unresolved.
    execution_order=None if remaining else list(order)
    order+=sorted(remaining)
    active=[k for k in pack['primitives'] if isinstance(value(answers,'PRIMITIVE.'+k),(int,float))
            and value(answers,'PRIMITIVE.'+k)>=pack['policy']['optional_primitive_threshold']]
    thesis=value(answers,'THESIS','none')
    return {'mode':mode,'methods':selected,'load_order':order,'relations':relationships,
            'ordering_unresolved':bool(remaining),'execution_order':execution_order,
            'load_order_meaning':'Resource loading order only; execution_order is null when dependency observations conflict. Resolve the source-bound canonical prerequisite before acting, or disclose a bounded route objection.',
            'unresolved_methods':uncertain,
            'companion_checks':companion_checks,'companion_reference_methods':sorted(companion_refs-set(selected)),
            'unconfirmed_companion_scopes':unconfirmed,'handling_is_scope_hint':True,
            'cognitive_obligations':{k:pack['primitives'][k]['instruction'] for k in active},
            'thesis_perspective':thesis if thesis in active else None,
            'effort':value(answers,'EFFORT'),'effort_scale':['direct','light single pass','bounded multiple perspectives','deep bounded analysis'],'route_status':'selected' if selected else 'no_named_method',
            'answer_allowed':True,'permission_granted':False,
            'uncertainty_instruction':'Preserve supported work and identify missing facts or routing uncertainty locally. A named-method ambiguity is not a ban on responding. Genuine permissions and evidence limits remain binding.'}


def evaluate_layer(root,state,pack,provider,freeze_identity):
    specs=questions(state,pack);view=project_context(specs,state)
    limits=Limits(max_calls=1,max_seconds=60,max_request_bytes=pack['policy']['max_request_bytes'])
    scope=VERSION+'-'+digest([str(root),state])
    admission=None
    if provider.is_live:
        admission={'scope':scope,'implementation':implementation_digest(),
            'provider_configuration':provider_configuration(provider),'limits':asdict(limits),
            'request_allowlist':[digest({'questions':[s.to_dict() for s in specs],'context_sha256':digest(view)})],
            'max_cost_usd':0.05,'reserve_per_call_usd':0.05,
            'authorization_ref':'Owner approved two-level direct routing and matched trial; fixed PLAN.md',
            'freeze_sha256':freeze_identity}
    save(root/'request.json',{'state':state,'questions':[s.to_dict() for s in specs], 'admission':admission})
    with Session(root/'journal',provider,scope=scope,limits=limits,live_admission=admission) as session:
        result=session.evaluate(specs,state)
    return {k:asdict(v) for k,v in result.items()}


def route(root,raw,repo,freeze_identity,provider=None):
    root=Path(root);repo=Path(repo);pack=load_pack(repo)
    provider=provider or TypeSafeJevProvider(model='jev-1.13.0',choice_rounding=True,transport=deadline_post_json)
    with _locked(root/'.route-lock'):
        state=initial_state(raw,pack)
        require(len(canonical(state))<=pack['policy']['max_state_bytes'],'direct_initial_capacity')
        binding={'version':VERSION,'pack_sha256':digest(pack),'raw_sha256':digest(raw),
                 'router_sha256':file_hash(__file__),'freeze':freeze_identity,
                 'provider':provider_configuration(provider)}
        save(root/'binding.json',binding)
        if (root/'result.json').exists():
            result=read_record(root/'result.json');seal=read_record(root/'evidence-seal.json')
            observed={str(p.relative_to(root)):file_hash(p) for p in sorted(root.rglob('*.json')) if p.name not in ('result.json','evidence-seal.json')}
            require(seal=={'result_sha256':digest(result),'files':observed},'direct_route_evidence_changed')
            return result
        first=evaluate_layer(root/'level-1',state,pack,provider,freeze_identity)
        requested,deferred=requested_details(first,pack);rounds=1;answers=first;detail_error=None
        if requested:
            try:second=expanded_state(state,requested,pack,repo)
            except ContractError as exc:detail_error=str(exc)
            else:
                answers=evaluate_layer(root/'level-2',second,pack,provider,freeze_identity);rounds=2
        decision=consume(answers,pack)
        decision.update(rounds=rounds,requested_details=requested,deferred_details=deferred,
                        detail_error=detail_error,pre_route_llm_calls=0,
                        full_catalog_each_round=True,initial_state_bytes=len(canonical(state)),
                        questions_per_round=len(questions(state,pack)),bindings=binding)
        if deferred or detail_error:decision['detail_budget_incomplete']=True
        save(root/'result.json',decision)
        files={str(p.relative_to(root)):file_hash(p) for p in sorted(root.rglob('*.json')) if p.name not in ('result.json','evidence-seal.json')}
        save(root/'evidence-seal.json',{'result_sha256':digest(decision),'files':files})
        return decision


def execution_materials(decision,pack,repo):
    result={}
    for name in list(dict.fromkeys(decision['load_order']+decision.get('companion_reference_methods',[]))):
        require(name in ROUTABLE,'direct_method_target')
        for path in pack['cards'][name]['sources']:
            require(file_hash(Path(repo)/path)==pack['source_sha256'][path],'direct_execution_source_changed')
            result[path]={'content':(Path(repo)/path).read_text(),'sha256':pack['source_sha256'][path]}
    return result
