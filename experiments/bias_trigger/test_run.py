"""Affected wiring only; no provider, authentication or CLI is invoked."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from . import run as r
from experiments.grounded_judgment.dispatch import classify, check_schema, host_schema
from experiments.typed_decision.contracts import digest
from experiments.typed_decision.session import RecoveryRequired
from experiments.jev_direct.serial import SerialRequests

def state():
    return {'candidate':None,'snapshot_sha256':None,'loaded':{},'readable_paths':['method'],
            'calls':{'A':0,'B':0,'C':0},'arms':{a:{'status':'unrun','final':None} for a in 'ABC'},'measurements':[]}

def cli(reply,terminal='turn.completed'):
    return {'kind':'cli','events':[{'type':'thread.started','thread_id':'fixture-thread'},
        {'type':'turn.started','turn_id':'fixture-turn'}, {'type':terminal,'turn_id':'fixture-turn'}],
        'returncode':0,'reply_text':json.dumps(reply)}

class Wiring(unittest.TestCase):
    def setUp(self):
        self.item={'case_id':'case-01','input':'目标是处理合格任务。人工更准，所以不用自动流程。'}
        self.s=state()
    def baseline(self):
        req=r.request(self.item,self.s,'A','draft',True)
        r.consume(self.item,self.s,req,'returned',{'kind':'answer','text':'保留人工更准，按合格门槛比较整体效率。','read_paths':[],'objection':''},{})
        return req
    def test_baseline_has_no_detection_or_norms(self):
        req=r.request(self.item,self.s,'A','draft',True)
        self.assertNotIn('questions',req['payload']);self.assertEqual(req['payload']['loaded_materials'],{})
        self.assertNotIn('norm',json.dumps(req));self.assertEqual(req['requested_configuration']['model'],'gpt-6.1-sol')
    def test_read_then_same_candidate_for_both_detectors(self):
        req=r.request(self.item,self.s,'A','draft',True)
        r.consume(self.item,self.s,req,'returned',{'kind':'read','text':'','read_paths':['method'],'objection':''},{'method':'original text'})
        self.baseline();b=r.request(self.item,self.s,'B','detect',True);c=r.request(self.item,self.s,'C','detect',True)
        for key in ('source','candidate','loaded_materials'):self.assertEqual(b['payload'][key],c['payload'][key])
        self.assertEqual(b,json.loads(json.dumps(b)))
        self.assertEqual(c,json.loads(json.dumps(c)))
        self.assertEqual(len(c['payload']['questions']),2)
        self.assertEqual(r.jev_payload(c)['questions']['Q_TARGET']['type'],'noul')
    def test_candidate_change_is_blocked(self):
        self.baseline();self.s['candidate']='changed'
        with self.assertRaises(ValueError):r.request(self.item,self.s,'C','detect',True)
    def test_b_legal_actual_schema_response_maps_before_handling(self):
        self.baseline();req=r.request(self.item,self.s,'B','detect',True)
        ref=next(iter(req['payload']['source']['candidates']))
        response={k:{'value':'support','semantic_state':'support','unresolved_reason':None,'basis_refs':[ref]} for k in r.CHECKS}
        check_schema(response,host_schema(req));status,raw,_,_=classify(req,cli(response))
        r.consume(self.item,self.s,req,status,raw,{})
        self.assertEqual(self.s['arms']['B']['status'],'handling_required')
        handling=r.request(self.item,self.s,'B','handling',True)
        self.assertEqual(handling['phase'],'revision');self.assertEqual(len(handling['payload']['supported_checks']),2)
    def test_c_ambiguous_is_incomplete_not_trigger(self):
        self.baseline();req=r.request(self.item,self.s,'C','detect',True)
        status,raw,_,_=classify(req,{'kind':'http_json','raw':{'model':'jev-1.13.0','answers':{k:{'type':'noul','noul':.5} for k in r.CHECKS}}})
        r.consume(self.item,self.s,req,status,raw,{})
        self.assertEqual(self.s['arms']['C']['coverage'],'incomplete');self.assertEqual(self.s['arms']['C']['supported_checks'],[])
    def test_handling_refs_and_rejected_detection_keep_answer(self):
        self.baseline();src=r.snapshot(self.item,self.s)['source']
        task=next(k for k,v in src['candidates'].items() if v['document_id']=='task')
        candidate=next(k for k,v in src['candidates'].items() if v['document_id']=='candidate')
        packet={'goal_refs':[task],'keep_refs':[task],'candidate_refs':[candidate],'disposition':'rejected','reason':'候选已保留边界','final':self.s['candidate']}
        self.assertEqual(r.parse_handling(json.dumps(packet),src)['final'],self.s['candidate'])
        packet['candidate_refs']=[task]
        with self.assertRaises(ValueError):r.parse_handling(json.dumps(packet),src)
    def test_unknown_terminal_and_local_exit_are_not_completion(self):
        self.baseline();req=r.request(self.item,self.s,'B','detect',True)
        raw={'kind':'cli','events':[{'type':'thread.started','thread_id':'fixture-thread'}],'returncode':1,'reply_text':None}
        self.assertEqual(classify(req,raw)[0],'unknown')
        r.consume(self.item,self.s,req,'unknown',None,{})
        self.assertEqual(self.s['calls']['B'],1);self.assertEqual(self.s['arms']['B']['status'],'unknown')
    def test_serial_simulated_clock_and_unknown_never_resend(self):
        with tempfile.TemporaryDirectory() as tmp:
            now=[100.];sleeps=[]
            def sleep(x):sleeps.append(x);now[0]+=x
            serial=SerialRequests(Path(tmp)/'serial',clock=lambda:now[0],monotonic=lambda:now[0],sleep=sleep)
            serial.call('first',lambda:None);serial.call('second',lambda:None)
            self.assertEqual(sum(sleeps),60)
            def unknown():raise RecoveryRequired('unknown')
            with self.assertRaises(RecoveryRequired):serial.call('third',unknown)
            with self.assertRaises(RecoveryRequired):serial.call('fourth',lambda:None)
            self.assertFalse((Path(tmp)/'serial/000002/completion.json').exists())
    def test_mutable_checkpoints_and_adapter_timeouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'state.json';r.persist(p,{'calls':0});r.persist(p,{'calls':1})
            self.assertEqual(json.loads(p.read_text()),{'calls':1})
        import inspect
        source=inspect.getsource(r.prepare)
        self.assertIn("'host_timeout':360,'jev_timeout':60",source)

if __name__=='__main__':unittest.main()
