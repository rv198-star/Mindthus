"""Only the new named000098 wiring; no real transport, core review or probes."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from . import stance_routing_dsf_resume as m
from experiments.typed_decision.relationship_runtime import save
r=m.r;c=m.c;s=m.s


class NamedResume(unittest.TestCase):
    def setUp(self):
        self.p=c.packet('SIMULATED own A1','SIMULATED own A2',[])
        self.item={'case_id':'dsf41-current','packet':self.p}
        self.cfg={'host_configuration':c.PROFILES['dsf41'],'limits':c.LIMITS}
        self.old=c.request(self.item,s.initial(self.p),'B','detect',True,c.PROFILES['dsf41'])
        self.wire=c.Adapters(c.PROFILES['dsf41']).outbound(self.old,self.cfg)
        self.driver=object.__new__(m.Driver);self.driver.config=self.cfg

    def test_one_named_compensation_reuses_entire_wire_and_preserves_state(self):
        state=s.initial(self.p);state['calls']['B']=1;state['arms']['B']['status']='unknown';before=copy.deepcopy(state)
        with patch.object(m,'old_bound',return_value=(self.old,self.wire,{})):
            req=self.driver.request_factory(self.item,state,'B','detect',True,c.PROFILES['dsf41'])
        self.assertEqual(req['sequence'],1)
        self.assertEqual(req['technical_retry_of'],{'call_key':m.KEY,'request_sha256':m.REQUEST})
        self.assertEqual(c.Adapters(c.PROFILES['dsf41']).outbound(req,self.cfg),self.wire)
        self.assertNotEqual(req['request_sha256'],self.old['request_sha256'])
        self.assertEqual(state,before)
        state['calls']['B']=2
        with self.assertRaises(ValueError):self.driver.request_factory(self.item,state,'B','detect',True,c.PROFILES['dsf41'])
        with self.assertRaises(ValueError):self.driver.request_factory({'case_id':'sol56-current','packet':self.p},before,'B','detect',True,c.PROFILES['dsf41'])

    def test_post_retry_handling_keeps_contract_and_does_not_reset_debits(self):
        state=s.initial(self.p);state['calls']['B']=2
        state['arms']['B'].update(status='handling_required',result={'branch':'whole_check','adopted_value':'whole_check','status':'adopted','unresolved_reason':None})
        before=copy.deepcopy(state)
        req=self.driver.request_factory(self.item,state,'B','handling',True,c.PROFILES['dsf41'])
        self.assertEqual(req['sequence'],2);self.assertEqual(state,before)
        normal=copy.deepcopy(state);normal['calls']['B']=1
        expected=c.request(self.item,normal,'B','handling',True,c.PROFILES['dsf41'])
        self.assertEqual(c.Adapters(c.PROFILES['dsf41']).outbound(req,self.cfg),c.Adapters(c.PROFILES['dsf41']).outbound(expected,self.cfg))
        state['calls']['B']=3
        with self.assertRaises(ValueError):self.driver.request_factory(self.item,state,'B','handling',True,c.PROFILES['dsf41'])

    def test_serial_accepts_only_named_bound_disposition_and_creates_no_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            serial=m.NamedSerial(Path(tmp)/'serial');directory=serial.root/'000098';intent={'label':m.KEY}
            x={'SIMULATED':'authority fixture, no actual risk authorization'}
            end={'status':'risk_accepted_remote_unknown','intent_sha256':r.digest(intent),'successor_sha256':r.digest(x),'is_completion':False,'local_disposition_at_epoch':123.}
            save(directory/'accepted-unknown.json',end)
            save(serial.anchors/'000098/accepted-unknown.json',{'sha256':r.digest(end)})
            with patch.object(m,'verified',return_value=x):
                self.assertEqual(serial._accepted_unknown(directory,intent),end)
                with self.assertRaises(ValueError):serial._accepted_unknown(directory,{'label':'other request'})
            with patch.object(s.old.prior.NamedSerial,'_accepted_unknown',side_effect=r.RecoveryRequired('other unknown remains blocked')):
                with self.assertRaises(r.RecoveryRequired):serial._accepted_unknown(serial.root/'000099',{'label':'other request'})
            self.assertFalse((directory/'completion.json').exists())


if __name__=='__main__':unittest.main(verbosity=2)
