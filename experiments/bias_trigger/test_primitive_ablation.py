"""Only new clean-wire and fixed-packet wiring, no credentials or API calls."""
import copy
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from . import run as r, primitive_ablation as a


class CleanWire(unittest.TestCase):
    def test_forward_medium_matches_all_host_groups_without_changing_jev(self):
        host=copy.deepcopy(a.d.DEFAULT_HOST);adapter=a.CleanAdapters()
        config={'host_configuration':host,'limits':{'logical':64,'host':56,'jev':8}}
        item={'case_id':'fixed','input':'原始用户业务文本。'}
        clean=a.initial();prompt=a.initial({k:v['text'] for k,v in a.packet().items()})
        q=r.request(item,clean,'A','draft',True,host)
        direct=adapter.outbound(q,config)
        b=adapter.outbound(r.request(item,prompt,'A','draft',True,host),config)
        body=copy.deepcopy(b['body']);body['messages'][0]=direct['body']['messages'][0]
        self.assertEqual(body,direct['body']);self.assertEqual(body['reasoning_effort'],'medium')
        r.consume(item,clean,q,'returned',{'kind':'answer','text':'首答','read_paths':[],'objection':''},{})
        c=adapter.outbound(r.request(item,clean,'C','detect',True,host),config)
        self.assertEqual(c['body']['model'],'jev-1.13.0')
        self.assertNotIn('reasoning_effort',c['body'])
        clean['arms']['C']['atoms']={'Q_TARGET':{'semantic_state':'support'}}
        handling=adapter.outbound(r.request(item,clean,'C','handling',True,host),config)
        self.assertEqual(handling['body']['reasoning_effort'],'medium')

    def request(self,primitive=False):
        s=a.initial({k:v['text'] for k,v in a.packet().items()} if primitive else None)
        return r.request({'case_id':'fixed','input':'原始用户业务文本。'},s,'A','draft',True,a.HOST)
    def test_direct_is_exact_original_without_catalog_or_index(self):
        req=self.request();wire=a.CleanAdapters(a.HOST).outbound(req,{'host_configuration':a.HOST,'limits':{'logical':64,'host':56,'jev':8}})
        self.assertEqual(wire['body']['messages'][1],{'role':'user','content':'原始用户业务文本。'})
        self.assertNotIn('readable_paths',json.dumps(wire['body']))
        self.assertNotIn('skills/',json.dumps(wire['body']))
        self.assertEqual(wire['body']['reasoning_effort'],'max')
    def test_only_prompt_packet_differs(self):
        config={'host_configuration':a.HOST,'limits':{'logical':64,'host':56,'jev':8}}
        adapter=a.CleanAdapters(a.HOST);direct=adapter.outbound(self.request(),config);prompt=adapter.outbound(self.request(True),config)
        common=copy.deepcopy(prompt['body']);common['messages'][0]=direct['body']['messages'][0]
        self.assertEqual(common,direct['body'])
        self.assertNotIn('momo',prompt['body']['messages'][0]['content'])
        self.assertNotIn('27-inch',prompt['body']['messages'][0]['content'])
        self.assertNotIn('norms',json.dumps(prompt['body']))
    def test_changed_packet_rejected_and_actual_contract_accepts(self):
        req=self.request(True);config={'host_configuration':a.HOST,'limits':{'logical':64,'host':56,'jev':8}};adapter=a.CleanAdapters(a.HOST)
        wire=adapter.outbound(req,config)
        raw={'kind':'cpa_http_json','endpoint':a.HOST['endpoint'],'request_sha256':r.digest(wire['body']),
             'raw':{'model':a.HOST['model'],'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'kind':'answer','text':'首份回答','read_paths':[],'objection':''})}}]}}
        self.assertEqual(adapter.classify(req,raw)[0],'returned')
        req['payload']['loaded_materials']['extra']='预期答案'
        with self.assertRaises(ValueError):adapter.outbound(req,config)
    def test_c_checks_actual_a_not_prompted_b(self):
        item={'case_id':'fixed','input':'原始任务。'};s=a.initial()
        q=r.request(item,s,'A','draft',True,a.HOST)
        r.consume(item,s,q,'returned',{'kind':'answer','text':'实际直出首答。','read_paths':[],'objection':''},{})
        c=r.request(item,s,'C','detect',True,a.HOST)
        wire=a.CleanAdapters(a.HOST).outbound(c,{'host_configuration':a.HOST,'limits':{'logical':64,'host':56,'jev':8}})
        self.assertEqual(c['payload']['candidate'],'实际直出首答。')
        self.assertEqual(len(c['payload']['questions']),2)
        self.assertEqual(wire['body']['model'],'jev-1.13.0')
        self.assertEqual(a.LIMITS,{'logical':32,'host':24,'jev':8})
    def test_new_three_groups_share_serial_and_inherit_debits(self):
        class Simulated(a.CleanAdapters):
            simulation=True
            def invoke(self,req,wire,*unused):
                now[0]+=1
                if req['role']=='jev':
                    return {'kind':'http_json','raw':{'model':'jev-1.13.0','answers':{k:{'type':'noul','noul':.1} for k in r.CHECKS}}}
                reply={'kind':'answer','text':'模拟元语首答。' if req['payload']['loaded_materials'] else '模拟直出首答。','read_paths':[],'objection':''}
                return {'kind':'cpa_http_json','endpoint':a.HOST['endpoint'],'request_sha256':r.digest(wire['body']),
                        'raw':{'model':a.HOST['model'],'choices':[{'finish_reason':'stop','message':{'content':json.dumps(reply)}}]}}
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp)/'parent';root=parent/'phase';(root/'calls').mkdir(parents=True)
            for n in range(9):(parent/'calls'/f'{n:06d}').mkdir(parents=True)
            config={'simulation':True,'source_sha256':{},'parent_preserved':{},'primitive_packet_sha256':r.digest(a.packet()),
                    'host_configuration':a.HOST,'limits':{'logical':64,'host':56,'jev':8},'external_budget_debits':{'logical':11,'host':11,'jev':0},
                    'cases_sha256':r.digest(r.rt.read(r.DOC/'cases.business.json'))}
            r.rt.write(root/'batch.json',config);r.rt.write(root/'materials.json',{})
            now=[100.];sleeps=[]
            def sleep(x):sleeps.append(x);now[0]+=x
            driver=a.Driver.__new__(a.Driver)
            r.Driver.__init__(driver,root,Simulated(a.HOST),clock=lambda:now[0],monotonic=lambda:now[0],sleep=sleep)
            driver.serial=r.SerialRequests(parent/'serial',clock=lambda:now[0],monotonic=lambda:now[0],sleep=sleep)
            driver.stop_path=root/'STOP.json';driver.serial.call('prior-batch-ended',lambda:None)
            clean=a.initial();prim=a.initial({k:v['text'] for k,v in a.packet().items()})
            with patch.object(a,'ROOT',root),patch.object(a.d,'ROOT',parent):
                item={'case_id':'case-01-clean','input':'原题。'}
                driver.step(item,clean,'A','detect')
                driver.step({**item,'case_id':'case-01-prompt'},prim,'A','detect')
                driver.step(item,clean,'C','detect')
                self.assertEqual(clean['arms']['C']['final'],clean['candidate'])
                self.assertNotEqual(prim['candidate'],clean['candidate'])
                with self.assertRaisesRegex(ValueError,'one_answer_or_one_check_handling'):driver.step(item,clean,'A','detect')
            self.assertEqual(sum(sleeps),180)
            self.assertEqual(len(list((root/'calls').iterdir()))+config['external_budget_debits']['logical'],14)


if __name__=='__main__':unittest.main()
