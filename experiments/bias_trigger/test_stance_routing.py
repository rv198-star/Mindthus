"""Only the new one-question wire, consumption and bounded handling wiring."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from . import stance_routing as s
r=s.r
HOST={'model':'gpt-6.1-sol','reasoning_effort':'medium','max_completion_tokens':8192,
      'transport_profile':'cpa_https_json','endpoint':'https://sub2api.72live.com/v1/chat/completions'}


def cfg():
    return {'host_configuration':HOST,'limits':s.LIMITS,'external_budget_debits':s.INHERITED,
            'phase_limits':{'logical':5,'host':3,'jev':2}}


def categorical(value='whole_check'):
    return {s.QID:{'value':value,'semantic_state':'support','unresolved_reason':None,'basis_refs':['U2']}}


def typed(value='whole_check', probability=1.):
    other=(1.-probability)/2
    return {s.QID:{'status':'ok','value':value,'reason':'','uncertainty':{
      'source':'provider_distribution','confidence':probability,
      'probabilities':{k:probability if k==value else other for k in s.OPTIONS}}}}


class Clock:
    def __init__(self):self.value=100.;self.waits=[]
    def now(self):return self.value
    def sleep(self,n):self.waits.append(n);self.value+=n


class Fake(s.Adapters):
    simulation=True
    def __init__(self, unknown=False):super().__init__(HOST);self.count=0;self.unknown=unknown
    def invoke(self,req,wire,directory,config):
        self.count+=1
        if self.unknown:return {'kind':'transport_error','code':'read_timeout','diagnostic':None}
        if req['role']=='jev':
            value='retain' if '暂不讨论Skills的完整定义' in req['payload']['source']['documents'][2]['text'] else 'whole_check'
            return {'kind':'http_json','endpoint':wire['endpoint'],'request_sha256':r.digest(wire['body']),
              'raw':{'model':'jev-1.13.0','answers':{s.QID:{'type':'choice','choice':value,'confidence':1.,
                    'probabilities':{k:float(k==value) for k in s.OPTIONS}}}}}
        if req['phase']=='atoms':response=categorical()
        else:
            response={'kind':'answer','read_paths':[],'objection':'', 'text':json.dumps({
                'disposition':'revised','reason':'SIMULATED transport fixture, no semantic judgment.',
                'final':'SIMULATED final; not a real model answer.',
                'basis':[{'document_id':'U2','quote':req['payload']['source']['documents'][2]['text']}]},ensure_ascii=False)}
        return {'kind':'cpa_http_json','endpoint':wire['endpoint'],'request_sha256':r.digest(wire['body']),
                'raw':{'model':HOST['model'],'choices':[{'finish_reason':'stop','message':{'content':json.dumps(response,ensure_ascii=False)}}]}}


class Wiring(unittest.TestCase):
    def test_exported_contract_legal_b_reply_and_s0_only(self):
        p=s.packets()['S-current'];item={'case_id':'S-current','packet':p};state=s.initial(p)
        b=s.request(item,state,'B','detect',True,HOST);c=s.request(item,state,'C','detect',True,HOST)
        self.assertEqual(b['payload']['questions'],c['payload']['questions'])
        self.assertEqual(set(b['payload']['output_contract'][s.QID]['value_enum']),set(s.OPTIONS)|{None})
        contract=b['payload']['output_contract'][s.QID]
        reply={s.QID:dict(zip(contract['fields'],['whole_check','support',None,['U2']]))}
        self.assertEqual(s.route(p,reply,'B')['adopted_value'],'whole_check')
        wire=s.Adapters(HOST).outbound(c,cfg())
        self.assertEqual(list(wire['body']['questions']),[s.QID])
        self.assertNotIn('questions',wire['body']['state'])
        self.assertNotIn('candidate',wire['body']['state'])
        self.assertEqual([d['id'] for d in wire['body']['state']['source']['documents']],['U1','A1','U2'])
        self.assertNotIn('candidates',wire['body']['state']['source'])

    def test_unadopted_raw_choice_is_not_whole_check(self):
        p=s.packets()['S-current'];result=s.route(p,typed(probability=.6),'C')
        self.assertEqual(result['raw_value'],'whole_check');self.assertIsNone(result['adopted_value'])
        self.assertEqual(result['branch'],'owner_scope_check');self.assertIsNone(result['model_basis_refs'])
        self.assertEqual(result['unresolved_reason'],'low_confidence')
        invalid=typed();invalid[s.QID]['uncertainty']['probabilities']['whole_check']=.99
        self.assertIsNone(s.route(p,invalid,'C')['adopted_value'])

    def test_exact_preservation_and_citation_contract(self):
        p=s.packets()['S-current']
        x={'disposition':'kept','reason':'already sufficient','final':p['candidate'],
           'basis':[{'document_id':'A2','quote':p['candidate'][:10]}]}
        response={'kind':'answer','read_paths':[],'text':json.dumps(x)}
        self.assertEqual(s.accept_handling(p,response)['final'],p['candidate'])
        x['final']+=' changed';response['text']=json.dumps(x)
        with self.assertRaises(ValueError):s.accept_handling(p,response)
        x['disposition']='revised';x['basis'][0]['quote']='NONEXISTENT quote';response['text']=json.dumps(x)
        with self.assertRaises(ValueError):s.accept_handling(p,response)

    def driver(self,root,adapter):
        rows=s.packets();r.rt.write(root/'snapshots.json',rows)
        config={**cfg(),'simulation':True,'source_sha256':{},'cases_source_path':str(root/'snapshots.json'),
                'cases_sha256':r.digest(rows)}
        (root/'calls').mkdir();(root/'states').mkdir();r.rt.write(root/'batch.json',config);r.rt.write(root/'materials.json',{})
        clock=Clock();driver=s.Driver(root,adapter,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
        driver.stop_path=root/'STOP.json'
        return driver,rows,clock

    def test_full_five_call_mock_trace_and_global_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fake=Fake();driver,rows,clock=self.driver(root,fake)
            states={k:s.initial(p) for k,p in rows.items()};trace=[]
            for name,arm,phase in [('S-current','C','detect'),('S-carrier-scope','C','detect'),
                                   ('S-current','C','handling'),('S-current','B','detect'),('S-current','B','handling')]:
                item={'case_id':name,'packet':rows[name]};state=states[name]
                terminal=driver.step(item,state,arm,phase)
                self.assertEqual(terminal['status'],'returned')
                trace.append({'case':name,'arm':arm,'phase':phase,'terminal':terminal,
                              'state':json.loads(r.canonical(state))})
            self.assertEqual(fake.count,5);self.assertEqual(clock.waits,[60.]*4)
            self.assertEqual(states['S-current']['arms']['C']['status'],'delivered')
            self.assertEqual(states['S-carrier-scope']['arms']['C']['result']['branch'],'retain')
            for arm in ('B','C'):
                with self.assertRaises(ValueError):driver.step({'case_id':'S-current','packet':rows['S-current']},states['S-current'],arm,'handling')
            if os.environ.get('STANCE_ROUTING_MOCK_TRACE'):
                path=Path(os.environ['STANCE_ROUTING_MOCK_TRACE']);path.parent.mkdir(parents=True,exist_ok=True)
                r.rt.write(path,{'simulation':True,'model_calls':0,'trace':trace})

    def test_unknown_stops_and_cannot_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fake=Fake(True);driver,rows,_=self.driver(root,fake)
            item={'case_id':'S-current','packet':rows['S-current']};state=s.initial(item['packet'])
            self.assertEqual(driver.step(item,state,'C','detect')['status'],'unknown')
            self.assertIsNone(state['arms']['C']['result']);self.assertTrue(driver.stop_path.exists())
            self.assertFalse((root/'serial/000000/completion.json').exists())
            with self.assertRaises(ValueError):driver.step(item,state,'C','detect')
            self.assertEqual(fake.count,1)

    def test_other_request_receipt_cannot_import(self):
        p=s.packets()['S-current'];req=s.request({'case_id':'S-current','packet':p},s.initial(p),'C','detect',True,HOST)
        adapter=Fake();wire=adapter.outbound(req,cfg());raw=adapter.invoke(req,wire,None,cfg())
        raw['request_sha256']='wrong request'
        self.assertEqual(adapter.classify(req,raw)[0],'unknown')


if __name__=='__main__':unittest.main(verbosity=2)
