"""Scoped compensation interface only; no model or transport calls."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from experiments.grounded_judgment import complete_missing as m,runtime as rt
from experiments.grounded_judgment.resume_000007 import guard
from experiments.typed_decision.contracts import digest


class MissingThree(unittest.TestCase):
    def test_unknown_draft_requires_exact_old_input_and_identity(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);old={'request_sha256':m.RETRIES['record-source-1-B:2']['request_sha256'],
                'payload':{'source':'original','bindings':'original','output_contract':'same'}}
            rt.write(root/'calls/000047/request.json',old)
            req={'phase':'draft','payload':dict(old['payload'])};x={'retries':m.RETRIES}
            out=m.retry_binding(root,x,'record-source-1-B:2',req)
            self.assertEqual(out['compensates_local_call'],'000047');self.assertFalse(out['sending_contract_changed'])
            req['payload']['source']='changed'
            with self.assertRaisesRegex(ValueError,'input_changed'):m.retry_binding(root,x,'record-source-1-B:2',req)
            self.assertEqual(m.retry_binding(root,x,'record-source-1-B:3',req),{})

    def test_format_compensation_allows_only_sending_contract_clarification(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);x={'retries':m.RETRIES}
            for key in ('display-goal-2-C:4','mechanism-object-2-A:2'):
                old={'request_sha256':m.RETRIES[key]['request_sha256'],
                     'payload':{'source':'original','loaded_materials':['old'],'output_contract':'old'}}
                rt.write(root/'calls'/m.RETRIES[key]['local_call']/'request.json',old)
                req={'phase':'draft','payload':{**old['payload'],'output_contract':'clarified'}}
                self.assertTrue(m.retry_binding(root,x,key,req)['sending_contract_changed'])
                req['payload']['loaded_materials']=[]
                with self.assertRaisesRegex(ValueError,'input_changed'):m.retry_binding(root,x,key,req)

    def test_new_unknown_and_changed_delivered_answer_block_continuation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);config={'synthetic':True};state={'final':'unchanged','phase':'done'}
            rt.write(root/'batch.json',config)
            for name in m.parent49.STOPS:rt.write(root/name,{})
            for slot in ('000047','000049'):rt.write(root/'calls'/slot/'terminal.json',{'status':'unknown'})
            x={'batch_sha256':digest(config),'allowed_paths':m.PATHS,'retries':m.RETRIES,'retry_limit_per_path':1,
               'preserved':{},'prior_delivered':{'original-A':digest(state)}}
            rt.write(root/m.NAME,x)
            with patch.object(m,'BATCH',digest(config)),patch.object(rt,'state',return_value=state):
                self.assertEqual(guard(root),x)
                rt.write(root/'STOP-000076.json',{'reason':'unknown'})
                with self.assertRaisesRegex(ValueError,'new_stop'):guard(root)
                (root/'STOP-000076.json').unlink();state['final']='changed'
                with self.assertRaisesRegex(ValueError,'delivered_changed'):guard(root)


if __name__=='__main__':unittest.main()
