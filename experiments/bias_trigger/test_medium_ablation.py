"""Only medium successor wiring/budget/unknown, no credential or provider I/O."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from . import medium_ablation as m, run as r, primitive_ablation as a


class MediumSuccessor(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.parent=Path(self.tmp.name)/'parent';self.root=self.parent/'medium'
        (self.root/'calls').mkdir(parents=True)
        self.now=[100.];self.waits=[];self.invocations=[]
        config={'simulation':True,'host_configuration':m.HOST,'limits':m.LIMITS,'phase_limits':m.PHASE_LIMITS,
                'external_budget_debits':m.INHERITED,'parent_preserved':{},'source_sha256':{},
                'cases_sha256':r.digest(r.rt.read(r.DOC/'cases.business.json')),
                'primitive_packet_sha256':r.digest(a.packet())}
        r.rt.write(self.root/'batch.json',config);r.rt.write(self.root/'materials.json',{})
        self.addCleanup(patch.stopall);patch.object(m.d,'ROOT',self.parent).start()
        def sleep(x):self.waits.append(x);self.now[0]+=x
        self.clock_options={'clock':lambda:self.now[0],'monotonic':lambda:self.now[0],'sleep':sleep}

    def driver(self,unknown=False):
        owner=self
        class Simulated(m.MediumAdapters):
            simulation=True
            def invoke(self,req,wire,*unused):
                owner.invocations.append((req,wire));owner.now[0]+=1
                if unknown:return {'kind':'transport_error','code':'transport_failure','diagnostic':None}
                if req['role']=='jev':
                    return {'kind':'http_json','raw':{'model':'jev-1.13.0','answers':{k:{'type':'noul','noul':.95 if k=='Q_TARGET' else .1} for k in r.CHECKS}}}
                text='模拟首答'
                if req['phase']=='revision':
                    ids=req['payload']['source']['candidates']
                    goal=next(k for k,v in ids.items() if v['document_id']=='task')
                    candidate=next(k for k,v in ids.items() if v['document_id']=='candidate')
                    text=json.dumps({'goal_refs':[goal],'keep_refs':[goal],'candidate_refs':[candidate],
                                     'disposition':'rejected','reason':'模拟检查后保留','final':'模拟最终回答'})
                reply={'kind':'answer','text':text,'read_paths':[],'objection':''}
                return {'kind':'cpa_http_json','endpoint':m.HOST['endpoint'],'request_sha256':r.digest(wire['body']),
                        'raw':{'model':m.HOST['model'],'choices':[{'finish_reason':'stop','message':{'content':json.dumps(reply)}}]}}
        driver=m.MediumDriver.__new__(m.MediumDriver)
        r.Driver.__init__(driver,self.root,Simulated(m.HOST),**self.clock_options)
        driver.serial=r.SerialRequests(self.parent/'serial',**self.clock_options)
        driver.stop_path=self.root/'STOP.json';return driver

    def test_medium_AB_C_handling_share_sender_and_keep_35_debits(self):
        driver=self.driver();driver.serial.call('prior-max-ended',lambda:None)
        item={'case_id':'case-01-medium-clean','input':'原题'};clean=a.initial()
        driver.step(item,clean,'A','detect')
        driver.step({**item,'case_id':'case-01-medium-prompt'},a.initial({k:v['text'] for k,v in a.packet().items()}),'A','detect')
        driver.step(item,clean,'C','detect');self.assertEqual(clean['arms']['C']['status'],'handling_required')
        driver.step(item,clean,'C','handling');self.assertEqual(clean['arms']['C']['final'],'模拟最终回答')
        self.assertEqual(sum(self.waits),240);self.assertEqual(len(self.invocations)+m.INHERITED['logical'],39)
        self.assertEqual([wire['body']['reasoning_effort'] for req,wire in self.invocations if req['role']=='host'],['medium']*3)
        with self.assertRaisesRegex(ValueError,'one_answer_or_one_check_handling'):driver.step(item,clean,'A','detect')
        self.assertEqual(len(self.invocations),4)

    def test_new_unknown_stops_without_retry_or_old_risk_exception(self):
        driver=self.driver(unknown=True);item={'case_id':'case-01-medium-clean','input':'原题'};state=a.initial()
        terminal=driver.step(item,state,'A','detect');self.assertEqual(terminal['status'],'unknown')
        self.assertTrue(driver.stop_path.exists())
        with self.assertRaises(ValueError):driver.step({'case_id':'case-02-medium-clean','input':'另一题'},a.initial(),'A','detect')
        self.assertEqual(len(self.invocations),1)
        self.assertFalse((self.parent/'serial/000000/completion.json').exists())

    def test_exhausted_new_jev_allowance_does_not_use_old_or_host_balance(self):
        driver=self.driver()
        for i in range(8):
            directory=self.root/'calls'/f'{i:06d}';directory.mkdir()
            r.rt.write(directory/'request.json',{'role':'jev'})
        with self.assertRaisesRegex(ValueError,'medium_phase_budget'):
            driver.step({'case_id':'case-01-medium-clean','input':'原题'},a.initial(),'C','detect')
        self.assertEqual(self.invocations,[]);self.assertEqual(m.LIMITS,{'logical':67,'host':51,'jev':16})


if __name__=='__main__':unittest.main()
