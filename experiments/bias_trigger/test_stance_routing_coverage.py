"""Only new model/parameter/baseline wiring, independent outputs and shared cap."""
import json
from pathlib import Path
import tempfile
import unittest
from . import stance_routing_coverage as c
from .test_stance_routing import Clock, categorical
r=c.r;s=c.s


def config(rows):
    return {'simulation':True,'host_configuration':c.PROFILES['gpt54'],'profiles':c.PROFILES,
        'limits':c.LIMITS,'external_budget_debits':c.INHERITED,'phase_limits':c.PHASE,'host_timeout':90,
        'source_sha256':{},'cases_sha256':r.digest(rows)}


class Fake(c.Adapters):
    simulation=True
    def __init__(self,host,clock,unknown=False):super().__init__(host);self.clock=clock;self.count=0;self.unknown=unknown
    def invoke(self,req,wire,directory,cfg):
        self.count+=1;self.clock.value+=1
        if self.unknown:return {'kind':'transport_error','code':'read_timeout','diagnostic':{'request_sha256':r.digest(wire['body']),'generation_send_status':'unknown'}}
        if req['role']=='jev':
            value='retain' if req['payload']['source']['documents'][2]['text']==c.CONTROL_U2 else 'whole_check'
            return {'kind':'http_json','endpoint':wire['endpoint'],'request_sha256':r.digest(wire['body']),
             'raw':{'model':'jev-1.13.0','answers':{s.QID:{'type':'choice','choice':value,'confidence':1.,'probabilities':{k:float(k==value) for k in s.OPTIONS}}}}}
        if req['arm']=='A':content='SIMULATED bare answer '+str(req['sequence'])
        elif req['phase']=='atoms':content=json.dumps(categorical())
        else:
            answer={'disposition':'revised','reason':'SIMULATED separate transport fixture.',
                    'final':'SIMULATED '+req['arm']+' final.','basis':[{'document_id':'U2','quote':c.MESSAGES[1]}]}
            content=json.dumps({'kind':'answer','read_paths':[],'objection':'','text':json.dumps(answer)})
        return {'kind':'cpa_http_json','endpoint':wire['endpoint'],'request_sha256':r.digest(wire['body']),
                'raw':{'model':self.host['model'],'choices':[{'finish_reason':'stop','message':{'content':content}}]}}


class Coverage(unittest.TestCase):
    def test_all_profile_wires_keep_same_question_and_correct_supplier_parameters(self):
        p=c.packet('SIMULATED A1','SIMULATED A2',[]);item={'case_id':'example','packet':p}
        for name,host in c.PROFILES.items():
            adapter=c.Adapters(host);state=s.initial(p);cfg={**config(c.manifest()),'host_configuration':host}
            b=c.request(item,state,'B','detect',True,host);jev=c.request(item,state,'C','detect',True,host)
            self.assertEqual(b['payload']['questions'],jev['payload']['questions'])
            self.assertNotIn('candidate',jev['payload'])
            wire=adapter.outbound(b,cfg)
            self.assertEqual(wire['body']['reasoning_effort'],'medium')
            self.assertEqual(wire['body']['model'],host['model'])
            if name=='dsf41':
                self.assertIn('max_tokens',wire['body']);self.assertNotIn('max_completion_tokens',wire['body'])
                self.assertEqual(wire['body']['thinking'],{'type':'enabled'})
            else:self.assertEqual(wire['body']['max_completion_tokens'],8192)
            state['calls']['B']=state['calls']['C']=1
            for arm in 'BC':state['arms'][arm].update(status='handling_required',result=s.route(p,categorical(),'B'))
            bw=adapter.outbound(c.request(item,state,'B','handling',True,host),cfg)
            cw=adapter.outbound(c.request(item,state,'C','handling',True,host),cfg)
            self.assertEqual(bw,cw)
            self.assertNotIn('norms',str(bw))

    def test_reused_baselines_bind_real_model_specific_history_without_rerun(self):
        for name,paths in c.REUSED.items():
            values=[c.actual_reply(s.DOC.parent/p,c.PROFILES[name]) for p in paths]
            p=c.packet(values[0][0],values[1][0],[v[1] for v in values])
            self.assertEqual(p['source']['documents'][1]['text'],values[0][0])
            self.assertEqual(p['candidate'],values[1][0])
            control=c.packet(values[0][0],values[1][0],p['parent_receipts'],True)
            self.assertEqual(p['source']['documents'][:2],control['source']['documents'][:2])
            self.assertNotEqual(p['source']['documents'][2]['text'],control['source']['documents'][2]['text'])

    def setup_driver(self,root,unknown=False):
        rows=c.manifest();r.rt.write(root/'cases.json',rows);cfg={**config(rows),'cases_source_path':str(root/'cases.json')}
        (root/'calls').mkdir();(root/'states').mkdir();r.rt.write(root/'batch.json',cfg);r.rt.write(root/'materials.json',{})
        clock=Clock();adapter=Fake(c.PROFILES['gpt54'],clock,unknown);driver=c.Driver(root,adapter,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
        return driver,clock

    def test_22_call_mock_path_has_independent_handling_and_one_global_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);driver,clock=self.setup_driver(root);count=0
            state={'candidate':None,'snapshot_sha256':None,'calls':{'A':0,'B':0,'C':0},'arms':{'A':{'status':'pending'}},'measurements':[]}
            messages=[{'role':'user','content':c.MESSAGES[0]}]
            for turn in range(2):
                self.assertEqual(driver.step({'case_id':'gpt54-bare','messages':messages},state,'A','draft')['status'],'returned')
                count+=1
                if not turn:messages+=[{'role':'assistant','content':state['candidate']},{'role':'user','content':c.MESSAGES[1]}]
            for name,host in c.PROFILES.items():
                driver.adapter=Fake(host,clock);driver.config={**driver.parent_config,'host_configuration':host}
                p=c.packet('SIMULATED A1','SIMULATED A2',[]);item={'case_id':name+'-current','packet':p};state=s.initial(p)
                for arm in 'BC':self.assertEqual(driver.step(item,state,arm,'detect')['status'],'returned');count+=1
                cp=c.packet('SIMULATED A1','SIMULATED A2',[],True);control={'case_id':name+'-carrier','packet':cp,'control':True};cs=s.initial(cp)
                self.assertEqual(driver.step(control,cs,'C','detect')['status'],'returned');count+=1
                self.assertEqual(cs['arms']['C']['result']['branch'],'retain')
                for arm in 'BC':self.assertEqual(driver.step(item,state,arm,'handling')['status'],'returned');count+=1
                self.assertNotEqual(state['arms']['B']['final'],state['arms']['C']['final'])
                self.assertEqual(state['calls'],{'A':0,'B':2,'C':2})
            self.assertEqual(count,22);self.assertEqual(clock.waits,[60.]*21)
            p=c.packet('SIMULATED A1','SIMULATED A2',[])
            with self.assertRaises(ValueError):driver.step({'case_id':'overflow','packet':p},s.initial(p),'B','detect')
            self.assertEqual(len(list((root/'calls').iterdir())),22)

    def test_new_unknown_does_not_reuse_old_disposition_or_send_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);driver,_=self.setup_driver(root,True)
            p=c.packet('SIMULATED A1','SIMULATED A2',[]);item={'case_id':'one','packet':p};state=s.initial(p)
            self.assertEqual(driver.step(item,state,'C','detect')['status'],'unknown')
            with self.assertRaises(ValueError):driver.step(item,state,'B','detect')
            self.assertEqual(driver.adapter.count,1)
            self.assertFalse((root/'serial/000000/completion.json').exists())

    def test_bound_http_format_failure_is_not_timeout_or_safety_retry_authority(self):
        host=c.PROFILES['gpt55'];adapter=c.Adapters(host);p=c.packet('SIMULATED A1','SIMULATED A2',[])
        req=c.request({'case_id':'one','packet':p},s.initial(p),'B','detect',True,host)
        wire=adapter.outbound(req,{'host_configuration':host})
        for status,expected in ((400,'failed'),(401,'safety_refusal')):
            raw={'kind':'transport_error','code':'http_'+str(status),'diagnostic':{'request_sha256':r.digest(wire['body']),
                 'http_response_received':True,'http_status':status,'http_error_response':{'body_status':'json_error_object','type':'invalid_request_error'}}}
            self.assertEqual(adapter.classify(req,raw)[0],expected)
            raw['diagnostic']['request_sha256']='other request'
            self.assertEqual(adapter.classify(req,raw)[0],'unknown')


if __name__=='__main__':unittest.main(verbosity=2)
