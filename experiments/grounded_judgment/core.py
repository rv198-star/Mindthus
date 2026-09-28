"""Source locators, frozen question semantics, arm adapters and shared composition."""
import hashlib
import re
from dataclasses import asdict
from experiments.typed_decision.contracts import (DecisionSpec, DecisionResult,
    ContractError, canonical, digest, require, number)
from . import BASELINE

ROUNDS = (('G','O','C'), ('P','E'), ('ES','ER','R','T','TB','S','I_T','I_R'))
OPTIONS = {
 'ES': {'given':'给定案例条件','direct':'可直接核对的原始材料','reported':'来源转述',
        'claim':'未经验证的现实主张','missing':'缺失','unlocated':'不能定位'},
 'ER': {'supports':'支持P','refutes':'反证P','unrelated':'无关','insufficient':'不能判定'},
 'R': {'sufficient':'给定条件下充分支持，包括同义、机制解释和其他有效推导',
       'overreach':'部分支持，但C扩大范围','contradicts':'P与C矛盾','unrelated':'无关',
       'insufficient':'证据或条件不足，无法判断'},
 'TB': {'match':'明确匹配','different_G_C':'G/C这对原文明确表达不同目标，不能仅凭低T选择',
        'insufficient':'信息不足','unlocated':'无法定位'},
}
TEXT = {
 'G':'当前仍有效的用户目标或成功条件主要由哪一窗口表达？不得换成助手希望的目标。',
 'O':'当前主请求要求判断的对象或命题由哪一窗口表达？不自动选最大对象。',
 'C':'全文当前主请求中，哪一明确结论最值得核对依据？允许没有。不引用同轮G/O。',
 'P':'哪一原文前提被用来支持已选C？不替作者补强。',
 'E':'围绕已选C，哪一窗口提供最直接相关的候选支撑或反证材料？不引用同轮P，不预判支持P。',
 'ES':'已选E的来源身份是什么？来源身份不等于语义支持。',
 'ER':'在给定条件下，E与已选P的语义关系是什么？',
 'R':'给定范围和条件下P到C是什么关系？比较对象、量词、条件、时点；简单解释可以充分。',
 'T':'按已选G的成功条件评价O时，C回答了该目标，而不是另换目标。',
 'TB':'G/O/C对目标匹配提供什么依据？different_G_C须在已引用G/C中有明确冲突；无法指出则未决。',
 'S':'在明确给定条件与范围内，P足以支持C完整强度，不需另加未证前提。不是外部事实认证。',
 'I_T':'假设C确实替换了G的目标，不纠正目标错位对回答影响多大？',
 'I_R':'假设P不足以支持C且需限定或重查，不处理这条推导对回答影响多大？',
}
ORIGINS = {'given','direct','reported','claim','missing','user','assistant'}


def index(documents):
    """Exact Unicode offsets; all sentences + adjacent pairs, without semantic nomination."""
    require(isinstance(documents,list) and documents, 'documents_required')
    ids=set(); candidates={}
    for d in documents:
        require(set(d)=={'id','revision','text','role','order','origin','available'}, 'document_shape')
        require(isinstance(d['id'],str) and d['id'] and d['id'] not in ids, 'document_id')
        require(isinstance(d['text'],str) and isinstance(d['revision'],str), 'document_text')
        require(d['origin'] in ORIGINS and type(d['available']) is bool, 'document_origin')
        require(type(d['order']) is int and isinstance(d['role'],str), 'document_metadata')
        ids.add(d['id']); text=d['text']; spans=[]
        for m in re.finditer(r'[^\n。！？!?；;]+[。！？!?；;]?|\n',text):
            if m.group().strip(): spans.append((m.start(),m.end()))
        for i,(a,b) in enumerate(spans):
            windows=[(a,b)]
            if i+1<len(spans): windows.append((a,spans[i+1][1]))
            for start,end in windows:
                key=f'w{len(candidates):03d}'
                candidates[key]={'document_id':d['id'],'revision':d['revision'],
                    'sha256':hashlib.sha256(text.encode()).hexdigest(),'start':start,'end':end,
                    'exact_text':text[start:end], 'context':text[spans[max(0,i-1)][0]:spans[min(len(spans)-1,i+2)][1]]}
    return {'documents':documents,'candidates':candidates,
            'coverage':'covered' if len(candidates)+2<=255 else 'coverage_miss',
            'input_sha256':digest(documents)}


def validate_ref(src, ref):
    require(isinstance(ref,dict), 'reference_shape')
    d=next((d for d in src['documents'] if d['id']==ref.get('document_id')),None)
    require(d is not None,'reference_document')
    a,b=ref.get('start'),ref.get('end')
    require(type(a) is int and type(b) is int and 0<=a<b<=len(d['text']),'reference_range')
    require(ref.get('revision')==d['revision'] and ref.get('sha256')==hashlib.sha256(d['text'].encode()).hexdigest()
            and ref.get('exact_text')==d['text'][a:b],'reference_mismatch')
    require(any(ref==v for v in src['candidates'].values()),'reference_not_candidate')
    return d


def ref_id(atoms, key):
    a=atoms.get(key,{})
    return a.get('value') if a.get('semantic_state')=='support' else None


def specs(src, round_no, atoms=None):
    atoms=atoms or {}; result=[]
    require(round_no in (1,2,3),'round')
    if src['coverage']!='covered':return []
    if round_no>1 and ref_id(atoms,'C') not in src['candidates']:return []
    for q in ROUNDS[round_no-1]:
        if q in ('R','S','I_R') and ref_id(atoms,'P') not in src['candidates']:continue
        if q in ('T','TB','I_T') and not all(ref_id(atoms,k) in src['candidates'] for k in ('G','O','C')):continue
        if q in ('ES','ER') and ref_id(atoms,'E') not in src['candidates']:continue
        if q=='ER' and ref_id(atoms,'P') not in src['candidates']:continue
        if q in ('G','O','C','P','E'):
            criteria={k:v['exact_text'] for k,v in src['candidates'].items()}
            criteria.update(none='没有对应位置',ambiguous='不能确定位置');kind='select'
        elif q in ('T','S'):
            criteria={'true':'原文支持此命题','false':'原文不支持此命题；缺证不等于相反事实已证实'};kind='assess_proposition'
        elif q.startswith('I_'):
            criteria=['无实质影响','措辞或限定','改变建议或主要结论'];kind='rate'
        else:criteria=OPTIONS[q];kind='select'
        s=DecisionSpec(q,TEXT[q],criteria,('source','bindings'),kind=kind,version=BASELINE)
        s.validate();result.append(s)
    return result


# Shared by request contracts and consumers. These describe the accepted design,
# not additional questions or semantic nomination.
AGENT_FIELDS = ('value','semantic_state','unresolved_reason','basis_refs')
PROPOSITION_STATES = ('support','deny','unresolved')
CONSUMPTION_RULES = {
    'sufficient+support':'retain the inference within its stated conditions',
    'overreach+deny':'limit C; preserve the supported part of P',
    'contradicts+deny':'recheck P/C without declaring either fact verified',
    'insufficient_or_conflicting':'unresolved, not a confirmed content error',
    'target':'reanchor only if T=deny AND TB=different_G_C with bound G/C evidence',
    'evidence':'consume only adopted values; source origin is not semantic support',
    'impact':'I_T/I_R are conditional impacts, consumed only for their established finding',
    'unknown':'method/relationship uncertainty does not block unrelated supported work',
    'check':'independent LOC and OK over full draft; join after return; incompatible basis never revises',
    'limits':'one relation, two findings, one check, at most one revision',
}


def agent_contract(spec):
    proposition=spec.kind=='assess_proposition'
    return {'fields':list(AGENT_FIELDS), 'kind':spec.kind,
        'value_enum':list(PROPOSITION_STATES) if proposition else
                     list(spec.criteria) if spec.kind=='select' else [0,1,2],
        'semantic_states':list(PROPOSITION_STATES) if proposition else ['support','unresolved','unlocated'],
        'mapping': 'true proposition -> support; false/not-supported -> deny; abstention -> unresolved. Never return true/false or confidence.' if proposition else
                   'Selected enum/level -> support; abstention -> unresolved; unavailable locator -> unlocated.',
        'null_value':not proposition,
        'reason':'Nonempty for unresolved/unlocated; null when a decision is adopted. none with source basis means source_absence; ambiguous means no reliable locator.',
        'basis':'Unique candidate IDs from source (draft_index for checks). Located Choice includes its chosen ID. none outside checks requires source evidence; valid IDs do not certify semantics.',
        'check_basis':'LOC cites its selected draft ID. OK independently cites the relevant draft ID(s). For whole-draft omission LOC=none, OK=deny, both basis_refs=[]; do not depend on the other same-batch answer.',
        'probability':None}


def accepted_none(atom):
    return (atom.get('value')=='none' and atom.get('semantic_state')=='unresolved'
            and atom.get('unresolved_reason')=='source_absence' and bool(atom.get('basis_refs')))


def adopted_value(atom):
    if atom.get('semantic_state')=='support' or atom.get('provenance')=='deterministic_absence':
        return atom.get('value')
    return None


def blank(q, reason, state='unresolved'):
    return dict(question_id=q, refs=[],value=None,semantic_state=state,
                unresolved_reason=reason,basis_refs=[],provenance=None,raw_result_ref=None,probability=None)


def adapt(src, spec, raw, arm, atoms):
    """B categorical != C provider probabilities. Invalid items remain visible."""
    a=blank(spec.id,'contract_error','invalid');a['raw_result_ref']=digest(raw)
    a['provenance']='agent_categorical' if arm=='B' else 'provider_distribution'
    try:
        require(isinstance(raw,dict),'raw_shape')
        if arm=='C':
            r=DecisionResult.from_dict(raw,spec)
            if r.status!='ok':
                a.update(semantic_state='unresolved',unresolved_reason=r.status);return a
            val=r.value
            if spec.kind=='assess_proposition':
                state='support' if val>=.8 else 'deny' if val<=.2 else 'unresolved'
                a['probability']=val
            elif spec.kind=='select':
                require(r.uncertainty is not None,'distribution_required')
                prob=r.uncertainty['probabilities'][val];a['probability']=prob
                state='support' if prob>=.8 else 'unresolved'
            else:state='support'
            a['provider_uncertainty']=r.uncertainty
            basis=[ref_id(atoms,k) for k in ('G','O','C') if ref_id(atoms,k) in src['candidates']]
            if spec.id in ('R','S','I_R'):basis=[ref_id(atoms,k) for k in ('P','C') if ref_id(atoms,k) in src['candidates']]
            if spec.id in ('ER','ES'):basis=[ref_id(atoms,k) for k in ('E','P') if ref_id(atoms,k) in src['candidates']]
            reason='low_confidence' if state=='unresolved' else None
        else:
            contract=agent_contract(spec)
            require(arm=='B' and set(raw)==set(contract['fields']),'agent_shape')
            val=raw['value'];state=raw['semantic_state'];reason=raw['unresolved_reason'];basis=raw['basis_refs']
            require(state in contract['semantic_states'],'agent_state')
            require(isinstance(basis,list) and len(basis)==len(set(basis)),'agent_basis')
            if spec.kind=='select': require(val in spec.criteria or (val is None and state!='support'),'choice')
            elif spec.kind=='rate': require(type(val) is int and val in (0,1,2) or (val is None and state=='unresolved'),'score')
            else:require(val in contract['value_enum'] and val==state,'proposition')
            if spec.kind!='assess_proposition': require(state!='deny','categorical_not_deny')
            if state in ('unresolved','unlocated'):require(isinstance(reason,str) and reason,'abstention_reason')
        require(all(k in src['candidates'] for k in basis),'basis_unknown')
        for k in basis:validate_ref(src,src['candidates'][k])
        if spec.id in ('G','O','C','P','E'):
            if val in src['candidates']:
                validate_ref(src,src['candidates'][val]);a['refs']=[val];basis=[val]
            elif state=='support':
                if val=='none':
                    # Jev has no native citation field: retain the inspected full-source
                    # scope explicitly, never label this as a model-selected quote.
                    if arm=='C':
                        basis=list(src['candidates']);a['basis_origin']='runtime_full_source_scope'
                    state='unresolved';reason='source_absence' if basis else 'missing_basis'
                else:state='unlocated';reason='ambiguous'
        elif arm=='B' and not basis and not spec.id.startswith(('LOC.','OK.')):
            state='unresolved';reason='missing_basis'
        if spec.id.startswith('LOC.') and state=='support' and val in src['candidates']:
            if arm=='B':require(val in basis,'locator_basis_mismatch')
            else:basis=[val];a['basis_origin']='model_locator_selection'
            a['refs']=[val]
        if state=='support' and val in ('insufficient','unlocated'):
            state='unresolved';reason='insufficient_basis' if val=='insufficient' else 'unlocated'
        if spec.id=='TB' and val=='different_G_C' and state=='support':
            require(all(ref_id(atoms,k) in basis for k in ('G','C')),'conflict_basis_missing')
        if spec.id=='ES' and state=='support':
            e=ref_id(atoms,'E');require(e in src['candidates'],'evidence_missing')
            doc=validate_ref(src,src['candidates'][e])
            expected=doc['origin'] if doc['origin'] not in ('user','assistant') else 'claim'
            require(val==expected and (val!='direct' or doc['available']),'source_conflict')
        a.update(value=val,semantic_state=state,unresolved_reason=reason,basis_refs=basis)
    except (ContractError,KeyError,TypeError,ValueError):
        a.update(value=None,semantic_state='invalid',unresolved_reason='contract_error')
    return a


def compose(src, atoms):
    """No model or inferred source semantics: approved table only."""
    def v(q):return atoms.get(q,{}).get('value')
    def st(q):return atoms.get(q,{}).get('semantic_state')
    refs={k:ref_id(atoms,k) for k in ('G','O','C','P','E')}
    def valid(*keys):return all(refs[k] in src['candidates'] for k in keys)
    def quote(k):return src['candidates'][refs[k]]['exact_text'] if valid(k) else None
    pdoc=validate_ref(src,src['candidates'][refs['P']]) if valid('P') else None
    bound='conditional_on_given' if pdoc and pdoc['origin']=='given' else 'premise_unverified'
    findings=[];goal='unresolved';relation='unresolved'
    def finding(key,action,qs):
        return dict(finding_id=key,goal_ref=refs['G'],object_ref=refs['O'],premise_ref=refs['P'],
            claim_ref=refs['C'],evidence_ref=refs['E'],evidence_origin=adopted_value(atoms.get('ES',{})),evidence_relation=adopted_value(atoms.get('ER',{})),
            relation=adopted_value(atoms.get('R',{})),keep_exact_text=quote('P'),limit_target_exact_text=quote('C'),action=action,
            uncertainty=bound,source_question_ids=qs,
            requirement={'reanchor':'按所引G/O重新回答；不自动反转C真假。',
                         'limit':'保留P在给定范围成立的部分；不得仅凭P断言完整C，说明缺少的关系证据。',
                         'recheck':'并列P/C冲突；证据不足时不自动判任何一方为真。'}[action])
    if valid('G','O','C'):
        if st('T')=='deny' and st('TB')=='support' and v('TB')=='different_G_C':
            if {refs['G'],refs['C']}<=set(atoms['TB']['basis_refs']):
                goal='reanchor';findings.append(finding('target','reanchor',['G','O','C','T','TB']))
        elif st('T')=='support' and st('TB')=='support' and v('TB')=='match':goal='retain'
    if valid('P','C'):
        if st('R')=='support':
            if v('R')=='sufficient' and st('S')=='support':relation='retain'
            elif v('R') in ('overreach','contradicts') and st('S')=='deny':
                relation='limit' if v('R')=='overreach' else 'recheck'
                findings.append(finding('inference',relation,['P','C','R','S']))
            elif v('R')=='unrelated':relation='unsupported_relation'
    # No keep/delete commands exist; contradictory atomic observations never create a finding.
    scores={key:atoms.get(q,{}) for key,q in [('target','I_T'),('inference','I_R')]}
    if all(scores[f['finding_id']].get('semantic_state')=='support' for f in findings):
        findings.sort(key=lambda f: -scores[f['finding_id']]['value'])
    return {'goal':goal,'relation':relation,'findings':findings,'premise_status':bound,
            'evidence_conflict':st('ER')=='support' and v('ER')=='refutes',
            'limitations':{q:a['unresolved_reason'] for q,a in atoms.items()
                          if a['semantic_state'] in ('unresolved','unlocated','invalid')},
            'external_fact_verified':False}


def score_atom(atom, norm):
    """Independent supplied norm, never a new model judge. All samples remain denominator."""
    incomplete={'low_confidence','coverage_miss','contract_error','missing_basis','missing_result',
                'ambiguous','unlocated','abstain','provider_error','missing_context','dependency_missing'}
    completed=(atom['semantic_state']!='invalid' and atom['unresolved_reason'] not in incomplete
               and bool(atom.get('basis_refs')))
    # Exact independently frozen field match, including normative uncertainty and source basis.
    ok=completed and all(atom.get(k)==norm[k] for k in ('value','semantic_state','unresolved_reason','basis_refs'))
    return {'denominator':1,'success':int(ok),'completed':completed}


def score_samples(samples):
    """Caller supplies every registered sample and independent normative entries.

    No filtering of abstentions/missing outputs and no synthetic answer correctness score.
    """
    require(len({x['id'] for x in samples})==len(samples),'duplicate_sample')
    rows=[]
    for sample in samples:
        results=[]
        for q,norm in sample['norms'].items():
            atom=sample['atoms'].get(q,blank(q,'missing_result'))
            results.append(score_atom(atom,norm))
        rows.append({'id':sample['id'],'success':int(bool(results) and all(x['success'] for x in results)),
                     'atoms':results})
    pairs={}
    for sample,row in zip(samples,rows):
        if sample.get('pair') is not None:pairs.setdefault(sample['pair'],[]).append(row['success'])
    return {'denominator':len(samples),'success':sum(r['success'] for r in rows),
            'rows':rows,'pair_denominator':len(pairs),
            'pair_success':sum(len(v)==2 and all(v) for v in pairs.values())}
