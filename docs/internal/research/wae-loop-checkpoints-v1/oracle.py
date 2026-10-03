"""Scenario acceptance, hidden from model prompts; no LLM grading or keyword PASS.
Expected user-visible results are enumerated separately from reference algorithms.
The confined executor is a research restriction, not a hostile-code sandbox claim.
"""
from __future__ import annotations
import copy
import json
import subprocess
import sys

RECORDS={
 'A':{'revisions':[{'rev':1,'text':'approved A'},{'rev':2,'text':'private A'}],'current':2,'approved':1},
 'B':{'revisions':[{'rev':5,'text':'approved B'}],'current':5,'approved':5},
 'C':{'revisions':[{'rev':8,'text':'unpublished C'}],'current':8,'approved':None}}

def output(status='empty',record=None,rev=None,text=None,approved=False,can_edit=False,error=None):
    return dict(status=status,record=record,rev=rev,text=text,approved=approved,can_edit=can_edit,error=error)

def select(k='A',role='editor',tab='working'):
    return dict(kind='select',record=k,role=role,tab=tab)

def receive(k='A',epoch=1,rev=2,text='private A'):
    return dict(kind='receive',record=k,epoch=epoch,rev=rev,text=text)

def suite(policy,public=False):
    traces=[]
    def add(name,events,expectations,epochs,final_records=None,obligation='G1-G5'):
        traces.append(dict(name=name,events=events,expected=expectations,epochs=epochs,
          final_records=copy.deepcopy(RECORDS if final_records is None else final_records),obligation=obligation))
    add('initial',[],[output()],[0],obligation='API/no selection')
    add('save-before-selection',[dict(kind='save',ok=True,new_rev=99,text='unused'),receive(),select()],
        [output(),output(error='forbidden'),output(error='forbidden'),output('loading','A')],
        [0,0,0,1],obligation='G4/G5 no selection still retains forbidden error until select')
    # Values below are fixtures, not calculated by the reference implementation.
    selected={('A','working'):(2,'private A',False),('A','published'):(1,'approved A',True),
              ('B','working'):(5,'approved B',True),('B','published'):(5,'approved B',True),
              ('C','working'):(8,'unpublished C',False),('C','published'):(None,None,False)}
    for k in RECORDS:
        for role in ('editor','reader'):
            for tab in ('working','published'):
                r,txt,ap=selected[(k,tab if role=='editor' else 'published')]
                wait=output('loading' if r is not None else 'empty',k)
                edit=role=='editor' and r is not None and r==RECORDS[k]['current'] and (tab=='working' or policy=='EDIT_CURRENT')
                ready=output('ready',k,r,txt,ap,edit) if r is not None else wait
                add(f'select-{k}-{role}-{tab}',[select(k,role,tab),receive(k,1,r or 99,txt or 'unknown')],
                    [output(),wait,ready],[0,1,1],obligation='G1/G3, P1 version and policy')
    base=[select(),receive()]; loaded=output('ready','A',2,'private A',False,True)
    for label,bad in [('foreign',receive('B',1,5,'approved B')),('old-epoch',receive(epoch=0)),
      ('new-epoch',receive(epoch=2)),('wrong-version',receive(rev=1,text='approved A')),
      ('corrupt-text',receive(text='tampered')),('duplicate',receive())]:
        add('valid-then-'+label,base+[bad],[output(),output('loading','A'),loaded,loaded],[0,1,1,1],obligation='G2 accepted current result survives irrelevant arrival')
    for label,bad in [('epoch',receive(epoch=0)),('text',receive(text='tampered')),('key',receive('B',1,5,'approved B')),('foreign-with-matching-other-fields',receive('B',1,2,'private A'))]:
        add('pending-'+label,[select(),bad],[output(),output('loading','A'),output('loading','A')],[0,1,1],obligation='G1/G2 pending cannot expose unusable content')
    # ABA intent: revisit same record and same version; record/version equality alone is insufficient.
    ev=[select(),receive(),select('B','reader','published'),receive('B',2,5,'approved B'),select(),receive(epoch=1),receive(epoch=3),receive(epoch=1)]
    add('ABA',ev,[output(),output('loading','A'),loaded,output('loading','B'),output('ready','B',5,'approved B',True),output('loading','A'),output('loading','A'),loaded,loaded],
        [0,1,1,2,2,3,3,3,3],obligation='G1/G2 new intent incl same key/version')
    ev=[select(),receive(),select('A','reader','working'),receive(),receive(epoch=2,rev=1,text='approved A'),receive()]
    add('role-switch',ev,[output(),output('loading','A'),loaded,output('loading','A'),output('loading','A'),output('ready','A',1,'approved A',True),output('ready','A',1,'approved A',True)],
        [0,1,1,2,2,2,2],obligation='P1 privacy across role change')
    failed=dict(kind='save',ok=False,new_rev=3,text='new A')
    add('failed-save',base+[failed],[output(),output('loading','A'),loaded,output('ready','A',2,'private A',False,True,'save_failed')],[0,1,1,1],obligation='G4 failed-save preservation')
    changed=copy.deepcopy(RECORDS); changed['A']['revisions'].append(dict(rev=3,text='new A')); changed['A']['current']=3
    successful=dict(kind='save',ok=True,new_rev=3,text='new A')
    ev=base+[successful,receive(),receive(epoch=2,rev=3,text='new A'),select('A','reader','published'),receive(epoch=3,rev=1,text='approved A')]
    add('new-draft-retains-approval',ev,[output(),output('loading','A'),loaded,output('loading','A'),output('loading','A'),output('ready','A',3,'new A',False,True),output('loading','A'),output('ready','A',1,'approved A',True)],
        [0,1,1,2,2,2,3,3],changed,'G4 save/history + G1/G3 fresh revision')
    add('save-while-loading',[select(),successful],[output(),output('loading','A'),output('loading','A',error='forbidden')],[0,1,1],obligation='G4/G5 no permission while pending')
    add('reader-save',[select('A','reader','published'),receive(rev=1,text='approved A'),successful],
        [output(),output('loading','A'),output('ready','A',1,'approved A',True),output('ready','A',1,'approved A',True,False,'forbidden')],[0,1,1,1],obligation='P1/G4 reader cannot save')
    # Two distinct authorized P2 policies, each checked globally, never per-row cherry-picking.
    may=policy=='EDIT_CURRENT'; bready=output('ready','B',5,'approved B',True,may)
    newb=copy.deepcopy(RECORDS)
    if may: newb['B']['revisions'].append(dict(rev=6,text='new B')); newb['B']['current']=6
    bev=[select('B','editor','published'),receive('B',1,5,'approved B'),dict(kind='save',ok=True,new_rev=6,text='new B')]
    last=output('loading','B') if may else output('ready','B',5,'approved B',True,False,'forbidden')
    add('published-edit-choice',bev,[output(),output('loading','B'),bready,last],[0,1,1,2 if may else 1],newb,'P1 owner choice/G4')
    add('error-cleared-on-select',base+[failed,select('B','reader','published')],
      [output(),output('loading','A'),loaded,output('ready','A',2,'private A',False,True,'save_failed'),output('loading','B')],[0,1,1,1,2],obligation='G5 error clearing')
    if public:
        names={'select-A-editor-working','select-A-reader-published','failed-save'}
        return [t for t in traces if t['name'] in names]
    return traces

REFERENCE = '''def copy_state(s):
    records = {k: {'revisions':[dict(x) for x in v['revisions']], 'current':v['current'], 'approved':v['approved']} for k,v in s['records'].items()}
    return {'records':records, 'epoch':s['epoch'], 'selection':dict(s['selection']) if s['selection'] else None, 'packet':dict(s['packet']) if s['packet'] else None, 'error':s['error']}
def make_state(records):
    return copy_state({'records':records,'epoch':0,'selection':None,'packet':None,'error':None})
def screen(state, published_policy, surface='detail'):
    sel=state['selection']
    result={'status':'empty','record':None,'rev':None,'text':None,'approved':False,'can_edit':False,'error':state['error']}
    if sel is None: return result
    key=sel['record']; result['record']=key; rec=state['records'][key]
    target=rec['current'] if sel['role']=='editor' and sel['tab']=='working' else rec['approved']
    if target is None: return result
    result['status']='loading'
    text=next(r['text'] for r in rec['revisions'] if r['rev']==target)
    p=state['packet']
    if p is None or p['record']!=key or p['epoch']!=state['epoch'] or p['rev']!=target or p['text']!=text: return result
    editable=sel['role']=='editor' and target==rec['current'] and (sel['tab']=='working' or published_policy=='EDIT_CURRENT')
    result.update(status='ready',rev=target,text=text,approved=target==rec['approved'],can_edit=editable)
    return result
def step(state, event, published_policy):
    out=copy_state(state); kind=event['kind']
    if kind=='select':
        out['selection']={k:event[k] for k in ('record','role','tab')}
        out['epoch']+=1; out['packet']=None; out['error']=None
    elif kind=='receive':
        prior=out['packet']; out['packet']={k:event[k] for k in ('record','epoch','rev','text')}
        if screen(out,published_policy)['status']!='ready': out['packet']=prior
    elif kind=='save':
        if not screen(state,published_policy)['can_edit']: out['error']='forbidden'
        elif not event['ok']: out['error']='save_failed'
        else:
            rec=out['records'][out['selection']['record']]
            rec['revisions'].append({'rev':event['new_rev'],'text':event['text']})
            rec['current']=event['new_rev']; out['epoch']+=1; out['packet']=None; out['error']=None
    return out
'''
# A second representation uses a value list for the transport cache. Different
# authorized edit policies additionally produce distinct real behavior.
REFERENCE_2=REFERENCE.replace("'packet':dict(s['packet']) if s['packet'] else None", "'packet':list(s['packet']) if s['packet'] else None").replace("p=state['packet']", "p=dict(zip(('record','epoch','rev','text'),state['packet'])) if state['packet'] else None").replace("out['packet']={k:event[k] for k in ('record','epoch','rev','text')}", "out['packet']=[event[k] for k in ('record','epoch','rev','text')]")

WORKER=r'''
import ast,json,resource,sys
resource.setrlimit(resource.RLIMIT_CPU,(3,3)); resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024)); resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
p=json.load(sys.stdin); code=ast.parse(p['code'])
for n in ast.walk(code):
    if isinstance(n,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.AsyncFunctionDef,ast.With,ast.AsyncWith)): raise ValueError('unsupported statement')
    if isinstance(n,ast.Attribute) and n.attr.startswith('_'): raise ValueError('private attribute')
    if isinstance(n,ast.Name) and n.id.startswith('__'): raise ValueError('private name')
safe={n:__builtins__.__dict__[n] for n in ('dict','list','tuple','set','str','int','float','bool','len','next','iter','range','enumerate','zip','all','any','min','max','sorted','sum','isinstance','ValueError','KeyError','TypeError','Exception')}
scope={'__builtins__':safe}; exec(compile(code,'<candidate>','exec'),scope)
def dump(x): return json.dumps(x,sort_keys=True,ensure_ascii=False)
rows=[]
for t in p['traces']:
    records=json.loads(dump(p['records'])); before=dump(records)
    try:
        s=scope['make_state'](records); pure=dump(records)==before
        for i in range(len(t['events'])+1):
            if i:
                event=json.loads(dump(t['events'][i-1])); sb=dump(s); eb=dump(event)
                old=s; s=scope['step'](s,event,p['policy']); pure=pure and dump(old)==sb and dump(event)==eb
            for surface in ('list','detail','export'):
                sb=dump(s); got=scope['screen'](s,p['policy'],surface); pure=pure and dump(s)==sb
                ok=dump(got)==dump(t['expected'][i]) and s['epoch']==t['epochs'][i] and pure
                rows.append({'name':t['name'],'point':i,'surface':surface,'pass':ok,'got':got,'expected':t['expected'][i],'epoch':s['epoch'],'expected_epoch':t['epochs'][i],'input_preserved':pure,'obligation':t['obligation']})
        ok=dump(s['records'])==dump(t['final_records'])
        rows.append({'name':t['name'],'point':'records','pass':ok,'obligation':'G4 records/history'})
    except Exception as e: rows.append({'name':t['name'],'pass':False,'error':type(e).__name__})
print(json.dumps(rows,ensure_ascii=False))
'''

def check(code,policy,public=False):
    if policy not in ('READ_ONLY','EDIT_CURRENT'): return {'status':'missing_owner_policy','passed':0,'total':0}
    code=code.strip()
    if code.startswith('```') and code.endswith('```'): code='\n'.join(code.splitlines()[1:-1])
    payload={'code':code,'policy':policy,'records':RECORDS,'traces':suite(policy,public)}
    try:
        p=subprocess.run([sys.executable,'-I','-S','-c',WORKER],input=json.dumps(payload),text=True,capture_output=True,timeout=6,cwd='/tmp',env={'PATH':'/usr/bin:/bin'})
        if p.returncode: return {'status':'execution_error','passed':0,'total':0,'error':p.stderr[-900:]}
        rows=json.loads(p.stdout)
        return {'status':'pass' if all(r['pass'] for r in rows) else 'fail','passed':sum(r['pass'] for r in rows),'total':len(rows),
          'trace_count':len(payload['traces']),'failures':[r for r in rows if not r['pass']]}
    except subprocess.TimeoutExpired: return {'status':'timeout','passed':0,'total':0}
