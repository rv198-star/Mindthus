"""Offline wire-level transport double; never starts a CLI or reads credentials."""
import json
from pathlib import Path
from . import runtime as rt
from .development import cases, simulated
from .dispatch import Dispatcher, prepare


class Clock:
    def __init__(self):self.value=0.
    def now(self):return self.value
    def sleep(self,seconds):self.value+=seconds


class SimulatedAdapters:
    simulation=True
    def __init__(self,clock,case):self.clock=clock;self.case=case;self.invocations=[]
    def invoke(self,req,outbound,directory,config):
        self.invocations.append({'phase':req['phase'],'role':req['role'],'at':self.clock.now()})
        self.clock.sleep(2)
        run=directory.parents[1]/'runs'/(self.case['id']+'-'+req['arm']);s=rt.state(run)
        response=simulated(req,s,self.case)
        if req['phase']=='draft' and not s['read_count']:
            response={'kind':'read','text':'','read_paths':['fixture-method'],'objection':''}
        if req['role']=='jev':
            # Actual official answer shape, converted back by the production Jev codec.
            answers={}
            for key,value in response.items():
                kind=outbound['body']['questions'][key]['type']
                row={'type':kind,kind:value['value']}
                if kind!='noul':row.update(confidence=value['uncertainty']['confidence'],probabilities=value['uncertainty']['probabilities'])
                if kind=='score':row['legend']={str(i):t for i,t in enumerate(outbound['body']['questions'][key]['criteria'])}
                answers[key]=row
            return {'kind':'http_json','raw':{'model':'jev-1.13.0','answers':answers,
                    'usage':{'input_tokens':100,'output_tokens':10}}}
        if req['phase']=='atoms':
            for q in req['payload']['questions']:
                response.setdefault(q['id'],{'value':None,'semantic_state':'unresolved','unresolved_reason':'dependency_missing','basis_refs':[]})
        events=[{'type':'thread.started','thread_id':'mock-'+str(req['sequence'])},
                {'type':'turn.started','turn_id':'turn-'+str(req['sequence'])},
                {'type':'turn.completed','turn_id':'turn-'+str(req['sequence']),
                 'usage':{'input_tokens':100,'output_tokens':10}}]
        return {'kind':'cli','events':events,'stdout':'\n'.join(json.dumps(e) for e in events),
                'stderr':'','returncode':0,'reply':response}


def export(out):
    out=Path(out);case=cases()[1];clock=Clock()
    packet={'documents':case['documents'],'materials':{'fixture-method':'Synthetic material for read wiring only.'}}
    prepare(out,{case['id']:packet})
    adapter=SimulatedAdapters(clock,case);driver=Dispatcher(out,adapter,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
    results={}
    for arm in ('C','B','A'):
        name=case['id']+'-'+arm
        while True:
            s=driver.step(name)
            if s['stopped'] or s['phase']=='done':break
        results[arm]={k:s[k] for k in ('phase','stopped','call_count','read_count','draft','final','check_count','revision_count','measurements')}
    summary={'simulation':True,'public_development':True,'holdout':False,'real_model_calls':0,
      'simulated_clock_seconds':clock.now(),'calls':adapter.invocations,'arms':results,
      'unknown_actual_http_counts':True,'cost':None}
    rt.write(out/'summary.json',summary);return summary
