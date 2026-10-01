"""Only new driver hooks: native wire, bound consumption, cooldown and unknown stop."""
import tempfile, unittest
from pathlib import Path
from . import stance_detection as d
r=d.r

class Clock:
    def __init__(self):self.n=100.;self.wait=[]
    def now(self):return self.n
    def sleep(self,n):self.wait.append(n);self.n+=n

class Fake(d.Adapters):
    simulation=True
    def __init__(self,unknown=False):self.invocations=0;self.unknown=unknown
    def invoke(self,req,wire,directory,cfg):
        self.invocations+=1
        if self.unknown:return {'kind':'transport_error','code':'deadline_exceeded','diagnostic':None}
        positive='暂不讨论Skills的完整定义' not in req['payload']['source']['documents'][2]['text']
        ref=next(k for k,v in req['payload']['source']['candidates'].items() if v['document_id']=='A2')
        answers={}
        for key,q in wire['body']['questions'].items():
            if q['type']=='noul':answers[key]={'type':'noul','noul':.9 if positive else .1}
            else:
                selected=ref if positive else 'none'
                answers[key]={'type':'choice','choice':selected,'confidence':1.,
                    'probabilities':{k:float(k==selected) for k in q['criteria']}}
        return {'kind':'http_json','raw':{'model':'jev-1.13.0','answers':answers},
            'endpoint':wire['endpoint'],'request_sha256':r.digest(wire['body'])}

class Wiring(unittest.TestCase):
    def driver(self,root,adapter):
        rows=d.packets.build();r.rt.write(root/'snapshots.json',rows)
        cfg={'simulation':True,'source_sha256':{},'limits':d.LIMITS,'external_budget_debits':d.INHERITED,
            'phase_limits':{'logical':2,'host':0,'jev':2},'host_configuration':{},
            'cases_source_path':str(root/'snapshots.json'),'cases_sha256':r.digest(rows)}
        (root/'calls').mkdir();(root/'states').mkdir();r.rt.write(root/'batch.json',cfg);r.rt.write(root/'materials.json',{})
        clock=Clock();driver=d.Driver(root,adapter,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
        return driver,rows,clock
    def test_exact_native_wires_consumption_gap_and_no_extra_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);adapter=Fake();driver,rows,clock=self.driver(root,adapter)
            for name in d.ORDER:
                p=rows[name]['packet'];state=d.initial(p);item={'case_id':name,'packet':p}
                req=d.request(item,state,'C','detect',True,{})
                with self.assertRaises(ValueError):d.request(item,state,'B','detect',True,{})
                self.assertEqual(r.digest(r.jev_payload(req)),r.digest(r.jev_payload(d.packets.request(p,'C'))))
                terminal=driver.step(item,state,'C','detect')
                self.assertEqual(terminal['status'],'returned')
                self.assertEqual(state['arms']['C']['result']['needs_revision'],name=='S-current')
                self.assertFalse(state['arms']['C']['correction_executed'])
            self.assertEqual(adapter.invocations,2);self.assertEqual(clock.wait,[60.])
            self.assertEqual(len(driver.serial.validate()[0]),2)
            with self.assertRaises(ValueError):driver.step(item,d.initial(p),'C','detect')
            self.assertEqual(adapter.invocations,2)
    def test_unknown_preserved_without_completion_or_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);adapter=Fake(True);driver,rows,_=self.driver(root,adapter)
            p=rows['S-current']['packet'];state=d.initial(p);item={'case_id':'S-current','packet':p}
            terminal=driver.step(item,state,'C','detect')
            self.assertEqual(terminal['status'],'unknown');self.assertIsNone(state['arms']['C']['result'])
            self.assertTrue((root/'STOP.json').exists());self.assertFalse((root/'serial/000000/completion.json').exists())
            with self.assertRaises(ValueError):driver.step(item,d.initial(p),'C','detect')
            self.assertEqual(adapter.invocations,1)

if __name__=='__main__':unittest.main(verbosity=2)
