"""New two-turn binding and scoped confirmation only; no network/credentials."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from . import stance_pressure as s, run as r


class ScreenWiring(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.parent=Path(tmp.name);self.root=self.parent/'screen'
        (self.root/'calls').mkdir(parents=True);(self.root/'states').mkdir()
        self.now=[100.];self.waits=[];self.sent=[]
        self.config={'simulation':True,'host_configuration':s.d.DEFAULT_HOST,'limits':s.LIMITS,
                     'phase_limits':s.PHASE_LIMITS,'external_budget_debits':s.INHERITED,
                     'source_sha256':{},'parent_preserved':{},
                     'cases_source_path':str((s.DOC/'cases.business.json').relative_to(r.REPO)),
                     'cases_sha256':r.digest(r.rt.read(s.DOC/'cases.business.json')),
                     'norms_sha256':r.digest(r.rt.read(s.DOC/'norms.evaluation-only.json'))}
        r.rt.write(self.root/'batch.json',self.config);r.rt.write(self.root/'materials.json',{})
        self.addCleanup(patch.stopall);patch.object(s.d,'ROOT',self.parent).start();patch.object(s,'ROOT',self.root).start()

    def driver(self,unknown=False):
        owner=self
        class Simulated(s.Adapters):
            simulation=True
            def invoke(self,req,wire,*args):
                owner.sent.append(wire);owner.now[0]+=1
                if unknown:return {'kind':'transport_error','code':'transport_failure','diagnostic':None}
                reply={'kind':'answer','text':'真实传输替身返回的句子','read_paths':[],'objection':''}
                content=json.dumps(reply,ensure_ascii=False,indent=2)
                return {'kind':'cpa_http_json','endpoint':self.endpoint,'request_sha256':r.digest(wire['body']),
                        'raw':{'model':self.host['model'],'choices':[{'finish_reason':'stop','message':{'content':content}}]}}
        def sleep(x):self.waits.append(x);self.now[0]+=x
        return s.Driver(self.root,Simulated(),clock=lambda:self.now[0],monotonic=lambda:self.now[0],sleep=sleep)

    def test_actual_first_return_is_exact_second_turn_history_with_shared_cooldown(self):
        driver=self.driver();driver.serial.call('prior-ended',lambda:None)
        state=s.initial('S02-skeptic','screen');driver.turn(state);driver.turn(state)
        first,second=[w['body']['messages'] for w in self.sent]
        self.assertEqual([x['role'] for x in second],['system','user','assistant','user'])
        self.assertEqual(first[0],second[0]);self.assertEqual(first[1],second[1])
        raw=r.rt.read(self.root/'calls/000000/raw.json')['transport']['raw']['choices'][0]['message']['content']
        self.assertEqual(second[2]['content'],raw)
        self.assertEqual(second[3]['content'],s.cases()['S02-skeptic']['user_messages'][1])
        self.assertNotIn('Q_FRAME',json.dumps(second));self.assertNotIn('norms',json.dumps(second))
        self.assertEqual(len(state['turn_records']),2);self.assertEqual(sum(self.waits),120)
        self.assertEqual(state['calls']['A']+s.INHERITED['host'],45)
        with self.assertRaisesRegex(ValueError,'episode_not_resubmittable'):driver.turn(state)
        self.assertEqual(len(self.sent),2)

    def test_unknown_stops_without_retry_or_new_exception(self):
        driver=self.driver(True);state=s.initial('S02-skeptic','screen')
        self.assertEqual(driver.turn(state)['status'],'unknown');self.assertTrue(driver.stop_path.exists())
        with self.assertRaises(ValueError):driver.turn(s.initial('S03-advocate','screen'))
        self.assertEqual(len(self.sent),1);self.assertFalse((self.parent/'serial/000000/completion.json').exists())

    def test_changed_actual_assistant_and_reserve_dispatch_are_rejected(self):
        driver=self.driver();state=s.initial('S02-skeptic','screen');driver.turn(state)
        state['turn_records'][0]['assistant_raw_sha256']='not-the-return'
        with self.assertRaisesRegex(ValueError,'actual_assistant_changed'):driver.turn(state)
        with self.assertRaisesRegex(ValueError,'reserve_not_authorized'):driver.turn(s.initial('D01-pro-software','screen'))
        self.assertEqual(len(self.sent),1)

    def test_confirmation_requires_exact_bound_error_and_first_strong_case(self):
        driver=self.driver()
        for cid in s.PRIMARY:
            state=s.initial(cid,'screen');driver.turn(state);driver.turn(state)
        state=r.rt.read(self.root/'states/S02-skeptic-screen.json')
        review={'batch_sha256':r.digest(self.config),'norms_sha256':self.config['norms_sha256'],
                'confirmation_case_id':'S02-skeptic','important_failures':[{'case_id':'S02-skeptic','turn':1,
                'terminal_sha256':state['turn_records'][0]['terminal_sha256'],'quote':'真实传输替身','explanation':'模拟范围内的固定检查说明'}]}
        r.rt.write(self.root/'screen-review.json',review)
        confirm=s.confirm_state();self.assertEqual(confirm['case_id'],'S02-skeptic')
        review['important_failures'][0]['quote']='没有出现在真实返回的句子'
        r.persist(self.root/'screen-review.json',review)
        with self.assertRaisesRegex(ValueError,'failure_evidence_binding'):s.confirm_state()


if __name__=='__main__':unittest.main()
