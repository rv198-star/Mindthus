"""Only the bound pre-worker guard and equal-wire reuse; no live transport."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from . import stance_routing_host_repair as h
from .test_stance_routing import HOST, cfg, Fake
s=h.s
r=h.r


class BoundRepair(unittest.TestCase):
    def fixture(self, root):
        p=s.packets()['S-current'];item={'case_id':'S-current','packet':p};state=s.initial(p)
        state['calls']['C']=1;state['arms']['C'].update(status='handling_required',result={'branch':'whole_check','adopted_value':'whole_check','status':'adopted','unresolved_reason':None})
        req=s.request(item,state,'C','handling',False,HOST);wire=s.Adapters(HOST).outbound(req,cfg())
        config={**cfg(),'host_timeout':180,'source_sha256':{'experiments/typed_decision/relationship_live.py':r.digest(Path(h.transport.__file__).read_text())}}
        binding={'call_key':'stance-routing-v2:S-current-C:1','request_sha256':req['request_sha256'],
                 'wire_sha256':r.digest(wire),'batch_sha256':r.digest(config)}
        raw={'binding':binding,'transport':{'kind':'transport_error','code':'ContractError','diagnostic':None}}
        t={'binding':binding,'status':'unknown','error':'ContractError','raw_sha256':r.digest(raw['transport'])}
        folder=root/'calls/000002';folder.mkdir(parents=True)
        for name,body in [('request',req),('wire',wire),('terminal',t),('raw',raw)]:r.rt.write(folder/(name+'.json'),body)
        r.rt.write(root/'local-call-key-repair.json',{'effective_config':config})
        r.rt.write(root/'STOP.json',{'call_key':binding['call_key'],'terminal_sha256':r.digest(t)})
        return req,wire,t,config,item,state

    def test_fixed_invalid_deadline_never_launches_worker_and_preserves_old_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            before={p:p.read_bytes() for p in root.rglob('*.json')}
            with patch.object(s,'ROOT',root),patch.object(h.transport.multiprocessing,'get_context',side_effect=AssertionError('network forbidden')) as launch:
                h.verify();self.assertEqual(launch.call_count,0)
            self.assertEqual(before,{p:p.read_bytes() for p in root.rglob('*.json')})

    def test_unbound_error_or_actual_transport_timeout_cannot_reconcile(self):
        for change in ('other_call','timeout'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);_,_,t,_,_,_=self.fixture(root)
                if change=='other_call':t['binding']['call_key']='other-C:1'
                else:t['error']='deadline_exceeded'
                r.persist(root/'calls/000002/terminal.json',t)
                with patch.object(s,'ROOT',root),patch.object(h.transport.multiprocessing,'get_context') as launch:
                    with self.assertRaises(ValueError):h.verify()
                    self.assertEqual(launch.call_count,0)

    def test_compensation_preserves_wire_and_single_budget_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_,wire,_,_,item,state=self.fixture(root)
            state['calls']['C']=2;state['arms']['C']['status']='unknown'
            driver=object.__new__(h.Driver);driver.config=cfg()
            with patch.object(s,'ROOT',root):req=driver.request_factory(item,state,'C','handling',False,HOST)
            self.assertEqual(req['sequence'],2)
            self.assertEqual(s.Adapters(HOST).outbound(req,cfg()),wire)
            self.assertEqual(driver.path_limits,{'A':4,'B':2,'C':3})
            state['calls']['C']=3
            with patch.object(s,'ROOT',root):
                with self.assertRaises(ValueError):driver.request_factory(item,state,'C','handling',False,HOST)

    def test_equal_wire_reuses_real_bound_answer_without_b_call_or_fake_terminal(self):
        for branch in ('whole_check','clarify'):
            with self.subTest(branch=branch),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);doc=root/'doc';doc.mkdir();req,wire,_,_,item,state=self.fixture(root)
                source=root/'calls/000003';source.mkdir()
                answer={'disposition':'revised','reason':'SIMULATED evidence fixture.','final':'SIMULATED final.',
                        'basis':[{'document_id':'U2','quote':item['packet']['source']['documents'][2]['text']}]}
                response={'kind':'answer','read_paths':[],'objection':'','text':json.dumps(answer)}
                binding={'call_key':'stance-routing-v2:S-current-C:2','request_sha256':req['request_sha256'],
                         'wire_sha256':r.digest(wire),'simulation':True}
                raw={'binding':binding,'transport':{'simulation':True,'fixture':response}}
                t={'status':'returned','binding':binding,'raw_sha256':r.digest(raw['transport']),'response':response}
                for name,body in [('terminal',t),('raw',raw),('wire',wire)]:r.rt.write(source/(name+'.json'),body)
                state['calls']['B']=1;state['arms']['B'].update(status='handling_required',result={'branch':branch,'adopted_value':branch,'status':'adopted','unresolved_reason':None})
                before=copy.deepcopy(state);driver=SimpleNamespace(config=cfg(),adapter=Fake())
                with patch.object(s,'ROOT',root),patch.object(s,'DOC',doc):reused=h.reuse_if_equal(driver,item,state)
                self.assertEqual(reused,branch=='whole_check')
                self.assertEqual(state['calls']['B'],1)
                self.assertFalse((root/'calls/000004').exists())
                if reused:
                    self.assertEqual(state['arms']['B']['final'],'SIMULATED final.')
                    self.assertFalse(state['arms']['B']['reuse']['independent_B_generation'])
                    self.assertTrue(state['arms']['B']['reuse']['B_request_not_sent'])
                else:self.assertEqual(state,before)

    def test_simulated_shared_handler_cannot_enter_real_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_,wire,_,_,item,state=self.fixture(root)
            source=root/'calls/000003';source.mkdir()
            binding={'call_key':'stance-routing-v2:S-current-C:2','simulation':True,'wire_sha256':r.digest(wire)}
            raw={'binding':binding,'transport':{'simulation':True}}
            t={'status':'returned','binding':binding,'raw_sha256':r.digest(raw['transport'])}
            r.rt.write(source/'terminal.json',t);r.rt.write(source/'raw.json',raw)
            state['arms']['B'].update(status='handling_required')
            driver=SimpleNamespace(config=cfg(),adapter=s.Adapters(HOST))
            before=copy.deepcopy(state)
            with patch.object(s,'ROOT',root):
                with self.assertRaises(ValueError):h.reuse_if_equal(driver,item,state)
            self.assertEqual(state,before)


if __name__=='__main__':unittest.main(verbosity=2)
