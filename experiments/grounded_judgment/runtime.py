"""File exchange runner: creates requests and consumes replies; never sends a model request.

All external calls must be made by an independently authorized executor. A pending exchange
cannot be replaced/retried here. Simulation exercises exactly the same transition functions.
"""
from dataclasses import asdict
import copy
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from experiments.typed_decision.contracts import DecisionSpec, canonical, digest, require
from experiments.typed_decision.cli_defaults import host_configuration
from . import BASELINE
from .core import index, specs, adapt, blank, compose, ROUNDS, OPTIONS, TEXT, agent_contract, accepted_none, CONSUMPTION_RULES


def write(path,value):
    with open(path,'xb') as f:f.write(canonical(value)+b'\n')


def read(path):return json.loads(Path(path).read_text())


@contextmanager
def lock(root):
    with open(Path(root)/'.lock','a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def append(root,kind,payload):
    files=sorted((root/'events').glob('*.json'))
    prev=read(files[-1])['sha256'] if files else None
    body={'ordinal':len(files),'previous':prev,'kind':kind,'payload':payload}
    write(root/'events'/f'{len(files):04d}.json',{'body':body,'sha256':digest(body)})


def verify(root):
    prev=None
    for n,p in enumerate(sorted((root/'events').glob('*.json'))):
        e=read(p);b=e['body']
        require(b['ordinal']==n and b['previous']==prev and digest(b)==e['sha256'],'event_integrity')
        prev=e['sha256']
    return prev


def state(root):
    verify(root)
    records=[read(p)['body'] for p in sorted((root/'events').glob('*.json'))]
    require(records[-1]['kind']=='state','incomplete_event_transaction')
    return copy.deepcopy(records[-1]['payload'])


def init(root,documents,arm,*,simulation=True,materials=None,initial_paths=None,host_config=None):
    root=Path(root);require(arm in ('A','B','C'),'arm')
    root.mkdir(parents=True,exist_ok=False);(root/'events').mkdir()
    source=index(documents);materials=materials or {};initial_paths=initial_paths or []
    if not simulation:
        require('skills/using-mindthus/SKILL.md' in initial_paths and 'method_catalog' in initial_paths,'real_entry_required')
    require(all(p in materials for p in initial_paths),'initial_materials')
    s={'arm':arm,'simulation':simulation,'source':source,'materials':materials,
       'host_configuration':copy.deepcopy(host_config if host_config is not None else host_configuration()),
       'loaded':{p:materials[p] for p in initial_paths},'initial_paths':initial_paths,
       'phase':'draft' if arm=='A' else 'atoms' if arm=='B' else 'round1',
       'atoms':{},'composition':None,'draft':None,'final':None,'pending':None,'call_count':0,
       'host_logical_calls':0,'check_count':0,'revision_count':0,'read_count':0,'measurements':[],
       'started_epoch':time.time(),'stopped':None,'baseline':BASELINE}
    append(root,'init',{'source_sha256':source['input_sha256'],'arm':arm,'simulation':simulation,
                        'materials_sha256':digest(materials),'baseline':BASELINE})
    if arm!='A' and source['coverage']!='covered':
        s['atoms']={q:blank(q,'coverage_miss') for group in ROUNDS for q in group}
        finish_atoms(root,s)
    append(root,'state',s)
    return root


def all_specs_for_agent(src):
    """Same semantics and options, but references are bound by the Agent within its one call."""
    result=[]
    for ids in ROUNDS:
        for q in ids:
            criteria=OPTIONS.get(q)
            if q in ('G','O','C','P','E'):
                criteria={k:v['exact_text'] for k,v in src['candidates'].items()}
                criteria.update(none='没有对应位置',ambiguous='不能确定位置')
            if q in ('T','S'):criteria={'true':'原文支持此命题','false':'原文不支持此命题；缺证不等于相反事实已证实'}
            if q.startswith('I_'):criteria=['无实质影响','措辞或限定','改变建议或主要结论']
            kind='assess_proposition' if q in ('T','S') else 'rate' if q.startswith('I_') else 'select'
            spec=DecisionSpec(q,TEXT[q],criteria,('source','bindings'),kind=kind)
            result.append({**asdict(spec),'output_contract':agent_contract(spec)})
    return result


def finish_atoms(root,s):
    for group in ROUNDS:
        for q in group:
            if q not in s['atoms']:
                s['atoms'][q]=blank(q,'dependency_missing')
    if accepted_none(s['atoms']['E']):
        for q,val in [('ES','missing'),('ER','insufficient')]:
            a=blank(q,'evidence_missing');a.update(value=val,provenance='deterministic_absence')
            s['atoms'][q]=a
    append(root,'adapted',s['atoms'])
    s['composition']=compose(s['source'],s['atoms'])
    append(root,'combined',s['composition']);s['phase']='draft'


def check_specs(s):
    if s['arm']=='A':return []
    src=index([{'id':'draft','revision':'1','text':s['draft'],'role':'assistant','order':0,
                'origin':'assistant','available':True}])
    if src['coverage']!='covered':return []
    out=[]
    for f in s['composition']['findings']:
        key=f['finding_id']
        binding='检查finding_id='+key+'：'+canonical(f).decode()+'。独立读取完整首稿，不依赖同批其他答案。'
        choices={k:v['exact_text'] for k,v in src['candidates'].items()};choices['none']='没有相关句'
        out.append(DecisionSpec('LOC.'+key,binding+' 哪一首稿句对应此发现？',choices,('source','draft','findings','draft_index','consumption_rules')))
        out.append(DecisionSpec('OK.'+key,binding+' 首稿是否落实此发现的keep/action且未升级证据上限？',
                               {'true':'已落实','false':'未落实'},('source','draft','findings','draft_index','consumption_rules'),kind='assess_proposition'))
    return out


def request(root):
    root=Path(root)
    with lock(root):
        s=state(root)
        if s['stopped']:return None
        if s['pending']:return s['pending']
        while s['phase'].startswith('round'):
            n=int(s['phase'][-1]);qs=specs(s['source'],n,s['atoms'])
            if qs:break
            append(root,'skipped',{'phase':s['phase'],'reason':'dependency_missing'})
            if n==3:finish_atoms(root,s)
            else:s['phase']='round'+str(n+1)
        if s['phase']=='done' or s['stopped']:return None
        phase=s['phase'];payload={'source':s['source'],'bindings':s['atoms']}
        if phase.startswith('round'):
            payload['questions']=[asdict(q) for q in qs]
        elif phase=='atoms':
            payload.update(questions=all_specs_for_agent(s['source']),dependency_order=ROUNDS,
              output_contract={'per_question':'Use each question.output_contract; no draft, confidence or extra keys.'},
              instruction='仅输出原子结果，按三轮依赖顺序内部绑定，未适用题保留未决。不得输出首稿或自行生成发现。')
        elif phase in ('draft','revision'):
            payload={'source':s['source'],'findings':s['composition'], 'loaded_materials':s['loaded'],
                     'readable_paths':sorted(s['materials']),
                     'instruction':'回答原始当前请求；保留正确内容和证据边界。可先请求必要材料。不要展示路由标签。',
                     'output_contract':{'kind':'answer|read','text':'string','read_paths':'list[str]','objection':'string'}}
            if s['arm']=='A':
                payload.pop('findings');payload['instruction']='正常使用给定原入口，必要时读取材料，然后回答原始请求。'
            if phase=='revision':payload.update(first_draft=s['draft'],check=s['check'],instruction='只做这一次定点修订，允许保留已有正确答案；不得编造事实。')
        elif phase=='check':
            payload={'source':s['source'],'draft':s['draft'],'findings':s['composition']}
            if s['arm']=='A':
                payload.pop('findings');payload['instruction']='对原任务进行一次自检，返回needs_revision及首稿原文依据，不自行重写。'
            else:
                cs=check_specs(s)
                if not cs:
                    append(root,'check_skipped',{'reason':'draft_coverage_miss'})
                    s['phase']='done';s['final']=s['draft'];append(root,'state',s);return None
                payload['questions']=[asdict(q) for q in cs]
                payload['draft_index']=index([{'id':'draft','revision':'1','text':s['draft'],'role':'assistant',
                                              'order':0,'origin':'assistant','available':True}])
        if s['arm'] in ('B','C'):
            payload['consumption_rules']=CONSUMPTION_RULES
            if phase=='check':
                payload['question_bindings']={q['id']:q['id'].split('.',1)[1] for q in payload['questions']}
                if s['arm']=='B':
                    payload['output_contract']={q.id:agent_contract(q) for q in cs}
        role='jev' if s['arm']=='C' and (phase.startswith('round') or phase=='check') else 'host'
        body={'sequence':s['call_count'],'arm':s['arm'],'phase':phase,'role':role,
              'simulation':s['simulation'],'baseline':BASELINE,'payload':payload,
              'requested_configuration':{'model':'jev-1.13.0','provider':'official'} if role=='jev' else
              s.get('host_configuration',{'model':'gpt-6-sol','reasoning_effort':'xhigh','transport_profile':'mindthus_official_http'})}
        req=json.loads(canonical({**body,'request_sha256':digest(body)}))
        s['pending']=req;append(root,'request',req);append(root,'state',s)
        return req


def accept(root,envelope):
    root=Path(root)
    with lock(root):
        s=state(root);require(not s['stopped'],'run_stopped');req=s['pending'];require(req is not None,'no_pending_request')
        require(envelope.get('request_sha256')==req['request_sha256'],'wrong_request')
        require(envelope.get('simulation') is s['simulation'],'mode_mismatch')
        # Dispatch-owned runs import only the matching persisted transport receipt.
        # Legacy standalone file exchange retains its original contract.
        if (root/'dispatch-owner.json').exists():
            from .dispatch import validate_import
            validate_import(root,req,envelope)
        status=envelope.get('status');require(status in ('returned','failed','unknown','safety_refusal'),'terminal_status')
        # Persist exact raw exchange before adapting. Never infers terminal from exit status.
        append(root,'response',envelope)
        s['call_count']+=1
        if req['role']=='host':s['host_logical_calls']+=1
        measurement=envelope.get('measurement',{})
        require(isinstance(measurement,dict),'measurement')
        s['measurements'].append({'phase':req['phase'],'role':req['role'],
            'simulation':s['simulation'],'logical_calls':1,'cli_starts':measurement.get('cli_starts'),
            'observed_recoveries':measurement.get('observed_recoveries'),
            'underlying_requests':measurement.get('underlying_requests'),
            'active_wait_seconds':measurement.get('active_wait_seconds'),
            'session_seconds':measurement.get('session_seconds'),
            'loading_seconds':measurement.get('loading_seconds'),
            'usage':measurement.get('usage'),'cost':measurement.get('cost'),
            'transport_evidence':measurement.get('transport_evidence')})
        if status!='returned':
            s['stopped']=status;append(root,'state',s);return s
        raw=envelope.get('response');phase=s['phase']
        try:
            require(isinstance(raw,dict),'response_shape')
            if phase=='atoms' or phase.startswith('round'):
                allowed=set(q for group in ROUNDS for q in group) if phase=='atoms' else set(q.id for q in specs(s['source'],int(phase[-1]),s['atoms']))
                require(set(raw)<=allowed,'unexpected_atom_or_draft')
                groups=(1,2,3) if phase=='atoms' else (int(phase[-1]),)
                for n in groups:
                    for q in specs(s['source'],n,s['atoms']):
                        s['atoms'][q.id]=adapt(s['source'],q,raw[q.id],s['arm'],s['atoms']) if q.id in raw else blank(q.id,'missing_result')
                append(root,'round_adapted',{'phase':phase,'atoms':s['atoms']})
                if phase in ('atoms','round3'):finish_atoms(root,s)
                else:s['phase']='round'+str(int(phase[-1])+1)
            elif phase in ('draft','revision'):
                require(set(raw)=={'kind','text','read_paths','objection'},'host_reply_shape')
                require(isinstance(raw['text'],str) and isinstance(raw['objection'],str),'host_text')
                paths=raw['read_paths'];require(isinstance(paths,list) and all(isinstance(p,str) for p in paths),'read_paths')
                require(len(paths)==len(set(paths)) and all(p in s['materials'] and p not in s['loaded'] for p in paths),'read_paths_invalid')
                if raw['kind']=='read':
                    require(paths and not raw['text'] and phase=='draft','read_only_before_first_draft')
                    require(s['read_count']<3,'read_budget')
                    s['read_count']+=1;s['loaded'].update({p:s['materials'][p] for p in paths})
                    append(root,'loaded',{'paths':paths,'material_sha256':digest(s['loaded'])})
                else:
                    require(raw['kind']=='answer' and not paths and raw['text'].strip(),'answer_required')
                    if phase=='draft':
                        s['draft']=raw['text'];append(root,'first_draft',raw)
                        s['phase']='check' if s['arm'] in ('A','B') or s['composition']['findings'] else 'done'
                        # B/C no finding means no extra check under the same contract.
                        if s['arm']=='B' and not s['composition']['findings']:s['phase']='done'
                    else:
                        require(s['revision_count']==0,'revision_budget')
                        s['revision_count']=1;append(root,'revision',raw);s['phase']='done'
                    s['final']=raw['text']
            elif phase=='check':
                require(s['check_count']==0,'check_budget');s['check_count']=1
                if s['arm']=='A':
                    require(set(raw)=={'needs_revision','basis_text'} and type(raw['needs_revision']) is bool,'self_check_shape')
                    require(isinstance(raw['basis_text'],str) and (not raw['needs_revision'] or raw['basis_text'] and raw['basis_text'] in s['draft']),'self_check_basis')
                    revise=raw['needs_revision'];check=raw
                else:
                    src=req['payload']['draft_index'];check={};revise=False
                    cs=check_specs(s);require(set(raw)<=set(q.id for q in cs),'check_ids')
                    for q in cs:
                        # OK evaluates full draft independently. It gets no same-batch LOC.
                        check[q.id]=adapt(src,q,raw[q.id],s['arm'],{}) if q.id in raw else blank(q.id,'missing_result')
                    for f in s['composition']['findings']:
                        loc=check['LOC.'+f['finding_id']];ok=check['OK.'+f['finding_id']]
                        valid_loc=loc['semantic_state']=='support' and loc['value'] in src['candidates']
                        # none+deny: absent required content, a bounded omission can be repaired.
                        absent=loc['semantic_state']=='support' and loc['value']=='none'
                        if s['arm']=='C' and loc['semantic_state']=='support':
                            # Post-return linkage, not a fabricated native Jev citation.
                            ok['basis_refs']=[loc['value']] if valid_loc else []
                            ok['basis_origin']='runtime_post_return_LOC_link'
                        compatible=(valid_loc and loc['value'] in ok['basis_refs']) or (
                            absent and not loc['basis_refs'] and not ok['basis_refs'])
                        if not compatible or (ok['semantic_state']=='support' and absent):
                            ok.update(semantic_state='unresolved',unresolved_reason='check_conflict')
                        elif ok['semantic_state']=='deny':revise=True
                s['check']=check;append(root,'check',check);s['phase']='revision' if revise else 'done'
            s['pending']=None
        except (ValueError,KeyError,TypeError) as e:
            s['stopped']='format_failure';append(root,'format_failure',{'type':type(e).__name__,'message':str(e)[:160]})
        if s['phase']=='done':
            s['finished_epoch']=time.time();s['wall_seconds']=s['finished_epoch']-s['started_epoch']
        append(root,'state',s)
        return s
