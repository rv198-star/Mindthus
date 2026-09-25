"""Source objections are consumed without silently discarding their limits."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tarfile
import unittest
from tests import test_route_control_v03 as f
from experiments.typed_decision import route_control_v03 as runtime, relationship_assessment as rel
from experiments.typed_decision.contracts import ContractError

class AdvisorySourceObjectionTests(unittest.TestCase):
    setUp=f.V03Tests.setUp
    run_entry=f.V03Tests.run_entry
    submit=f.V03Tests.submit
    drive=f.V03Tests.drive

    def objection(self,reply,q,status=None,kind='source_or_scope'):
        reply.pop('dependency_acceptance',None)
        reply.update(performed_methods=[],text='The transcript supports a conditional answer; the original image remains unavailable.',
            objection=dict(route_id=q['route_id'],revision=q['revision'],affected_issue_or_step=q['issue']['issue_id'],
                kind=kind,original_refs=[rel.quote(self.data['documents'][0])],
                claimed_conflict='Original image is not available.',requested_change='Keep image details unverified.'))
        if status is not None:reply['advisory_status']=status

    def test_legacy_source_objection_is_valid_but_not_implicitly_accepted(self):
        self.data=f.packet('advisory')
        result=self.drive(lambda r,q:self.objection(r,q) if q['schema'].endswith('execution-request.v1') else None)
        self.assertFalse(result['consumption_complete'])
        self.assertEqual(result['pending']['I1'],'advisory_host_unresolved')
        self.assertEqual(result['outputs']['I1']['advisory_objection']['disposition'],'unresolved')
        self.assertFalse(result['acceptance']['accepted']['I1']['accepted'])
        self.assertEqual(result['counts']['arbitration'],0)

    def test_explicit_bounded_answer_reaches_original_owner_with_limits(self):
        self.data=f.packet('advisory')
        result=self.drive(lambda r,q:self.objection(r,q,'bounded_answer') if q['schema'].endswith('execution-request.v1') else None)
        self.assertTrue(result['consumption_complete'])
        request=next(q for q in self.requests if q['schema'].endswith('accept-request.v1'))
        self.assertEqual(request['evidence']['advisory_objections']['I1']['disposition'],'bounded_answer')
        self.assertEqual(result['acceptance']['accepted']['I1']['artifact_sha256'],result['outputs']['I1']['artifact_sha256'])
        self.assertEqual(result,self.run_entry())
        self.assertEqual(self.provider.batch_count,2)

    def test_necessary_unknown_does_not_block_independent_answer(self):
        self.data=f.packet('advisory',count=2)
        def mutate(r,q):
            if q['schema'].endswith('execution-request.v1') and q['issue']['issue_id']=='I1':self.objection(r,q,'unresolved')
        result=self.drive(mutate)
        self.assertEqual(result['pending'],{'I1':'advisory_host_unresolved'})
        self.assertTrue(result['acceptance']['accepted']['I2']['accepted'])
        self.assertFalse(result['acceptance']['accepted']['I1']['accepted'])

    def test_bad_reference_and_hard_objection_cannot_be_accepted(self):
        self.data=f.packet('advisory');pending=self.run_entry()
        with self.assertRaisesRegex(ContractError,'hard_objection'):
            self.submit(pending,lambda r,q:self.objection(r,q,'bounded_answer','permission'))
        def invalid(r,q):
            self.objection(r,q,'bounded_answer');r['objection']['original_refs'][0]['sha256']='0'*64
        with self.assertRaises(ContractError):self.submit(pending,invalid)

    def test_empty_bounded_answer_rejected(self):
        self.data=f.packet('advisory')
        def invalid(r,q):self.objection(r,q,'bounded_answer');r['text']=''
        with self.assertRaisesRegex(ContractError,'result_required'):self.submit(self.run_entry(),invalid)

    def test_committed_contract_not_weakened(self):
        with self.assertRaises(ContractError):
            self.submit(self.run_entry(),lambda r,q:self.objection(r,q,'bounded_answer'))

    def test_original_4k_rejected_reply_now_valid_without_editing_raw_return(self):
        base=f.REPO/'docs/internal/research/typed-decision/route-control-v0.2/design-reassessment-v1'
        spec=importlib.util.spec_from_file_location('old_live_normalizer',base/'live-v03-d1/run.py')
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        with tarfile.open(base/'independent-sol56-v1/evidence.tar.gz') as archive:
            names=archive.getnames()
            hn=next(n for n in names if 'full-F-jev_advisory/' in n and n.endswith('steps/execution__I1__1/handoff.json'))
            q=json.load(archive.extractfile(hn))['payload']['request']
            raw=json.load(archive.extractfile('codex-calls/full-F-jev_advisory-execution__I1__1/answer.json'))
        reply=adapter.normalize(raw,q,dict(f.rt.UNKNOWN_USAGE))
        runtime._execution_reply(reply,q,q['original_input'],runtime._bundle(f.REPO)[2])
        self.assertEqual(reply['text'],raw['text'])
        self.assertEqual(reply['objection']['claimed_conflict'],raw['objection_reason'])
        self.assertNotIn('advisory_status',reply)

if __name__=='__main__':unittest.main()
