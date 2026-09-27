"""Public development fixtures. Every reply here is synthetic, never a Jev result."""
from dataclasses import asdict
from pathlib import Path
from experiments.typed_decision.contracts import digest
from .core import index, specs, OPTIONS, ROUNDS
from .runtime import init, request, accept, state, write, check_specs


def cases():
    def doc(i,text,origin='given',role='source',order=0):
        return dict(id=i,revision='1',text=text,origin=origin,role=role,order=order,available=True)
    common=[doc('S2','请判断这个Skill是否可以完整地视为模块化提示词。','user','user',1),
            doc('S3','这个Skill可以完整地视为模块化提示词。','claim','user',2)]
    fcommon=[doc('F2','给定条件：软件不能增加这台屏幕的物理像素密度。',order=1),
             doc('F3','仅据F2，就能断定软件不能满足F1所述目标。','claim','user',2),
             doc('F4','这是开发用假设情境；原图不可用，不声称核验过现实体验。','reported','source',3)]
    return [
      {'id':'skills-simple','documents':[doc('S1','这个Skill的组成是按时注入的文字。')]+common,'relation':'sufficient','s':'support'},
      {'id':'skills-validator','documents':[doc('S1','这个Skill的组成是按时注入的文字与独立执行的结果校验程序。')]+common,'relation':'overreach','s':'deny'},
      {'id':'4k-size','documents':[doc('F1','我的目标是用软件让这台4K屏幕的界面大小适合我。','user','user')]+fcommon,'relation':'insufficient','s':'unresolved'},
      {'id':'4k-density','documents':[doc('F1','我的目标是用软件让这台4K屏幕的物理像素密度达到同尺寸5K屏幕水平。','user','user')]+fcommon,'relation':'sufficient','s':'support'},
    ]


def values(case,src):
    def w(doc):return next(k for k,v in src['candidates'].items() if v['document_id']==doc)
    skills=case['id'].startswith('skills')
    return {'G':w('S2' if skills else 'F1'),'O':w('S2' if skills else 'F1'),
      'C':w('S3' if skills else 'F3'),'P':w('S1' if skills else 'F2'),'E':'none',
      'ES':'missing','ER':'insufficient','R':case['relation'],'T':'support','TB':'match',
      'S':case['s'],'I_T':2,'I_R':1}


def model_value(spec,val,basis,arm):
    if arm=='B':
        state=val if spec.kind=='assess_proposition' else 'support'
        return {'value':val,'semantic_state':state,'unresolved_reason':'insufficient_basis' if state=='unresolved' else None,'basis_refs':basis}
    if spec.kind=='assess_proposition':
        return {'status':'ok','value':{'support':.95,'deny':.05,'unresolved':.5}[val], 'uncertainty':None,'reason':''}
    choices=list(spec.criteria) if spec.kind=='select' else ['0','1','2']
    probs={k:float(k==str(val)) for k in choices}
    return {'status':'ok','value':val,'reason':'','uncertainty':{'source':'provider_distribution','confidence':1.,'probabilities':probs}}


def simulated(req,s,case):
    phase=req['phase'];arm=s['arm'];v=values(case,s['source'])
    if phase=='atoms' or phase.startswith('round'):
        out={};atoms={}
        groups=(1,2,3) if phase=='atoms' else (int(phase[-1]),)
        # B emits 13 categorical atoms; dependency validation is the production adapter's job.
        if phase=='atoms':
            from .core import adapt
            for n in groups:
                for q in specs(s['source'],n,atoms):
                    basis=[v[k] for k in ('G','C','P') if v[k] in s['source']['candidates']]
                    out[q.id]=model_value(q,v[q.id],list(dict.fromkeys(basis)),arm)
                    atoms[q.id]=adapt(s['source'],q,out[q.id],arm,atoms)
            return out
        for rawq in req['payload']['questions']:
            from experiments.typed_decision.contracts import DecisionSpec
            q=DecisionSpec(**rawq);out[q.id]=model_value(q,v[q.id],[],arm)
        return out
    if phase=='draft':
        return {'kind':'answer','text':'【模拟首稿】这是一份供离线接线验证的答案，不是模型能力证据。',
                'read_paths':[],'objection':''}
    if phase=='check':
        if arm=='A':return {'needs_revision':False,'basis_text':''}
        src=req['payload']['draft_index'];loc=next(iter(src['candidates']));out={}
        for q in check_specs(s):
            out[q.id]=model_value(q,loc if q.id.startswith('LOC.') else 'deny',[loc],arm)
        return out
    return {'kind':'answer','text':'【模拟修订】保留原文给定前提，限定结论；仅测试一次修订的接线。','read_paths':[],'objection':''}


def export(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    outputs=[]
    for case in cases():
        for arm in ('A','B','C'):
            r=root/(case['id']+'-'+arm)
            init(r,case['documents'],arm)
            while (req:=request(r)) is not None:
                s=state(r)
                accept(r,{'request_sha256':req['request_sha256'],'simulation':True,'status':'returned',
                          'response':simulated(req,s,case),'measurement':{}})
            s=state(r);assert not s['stopped']
            outputs.append({'case':case['id'],'arm':arm,'phase':s['phase'],'calls':s['call_count'],
                            'composition':s['composition'],'draft':s['draft'],'final':s['final'],
                            'checks':s['check_count'],'revisions':s['revision_count']})
    write(root/'summary.json',{'kind':'synthetic_public_development_only','baseline':s['baseline'],
                             'real_model_calls':0,'holdout':False,'runs':outputs})
    return outputs
