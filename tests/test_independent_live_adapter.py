"""No model calls: verify full-path isolation and exact artifact retention."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from experiments.typed_decision.contracts import ContractError, digest

P=Path(__file__).resolve().parents[1]/'docs/internal/research/typed-decision/route-control-v0.2/design-reassessment-v1/independent-v1/run.py'
S=importlib.util.spec_from_file_location('independent_adapter_test',P)
r=importlib.util.module_from_spec(S);S.loader.exec_module(r)

class IndependentAdapterTests(unittest.TestCase):
    def test_all_arms_start_full_path_without_shared_candidate(self):
        with patch.object(r.b,'run',return_value={'test':True}) as run:
            for condition in r.CONDITIONS:r.run(Path('/isolated'), 'E', condition)
        self.assertEqual(run.call_count,3)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs,{'full':True})
        self.assertNotIn('questions_only',r.CONDITIONS)

    def test_retention_resolves_exact_existing_text_and_hash(self):
        q={'schema':'mindthus.route-v03-native-request.v1','request_id':'id','candidate':'Real answer.',
           'artifact_actions':['retain','replace'],'condition_packet':{'loaded_methods':{},'original_input':{'documents':[]}}}
        raw={'artifact_action':'retain','text':'','performed_methods':[],'decision_status':'decided','dispute_reason':'','source_ids':[]}
        reply=r.normalize(raw,q,dict(r.b.rt.UNKNOWN_USAGE))
        self.assertEqual(reply['text'],'Real answer.');self.assertEqual(reply['version'],digest('Real answer.'))
        raw['text']='Keep original.'
        with self.assertRaisesRegex(ContractError,'retain_requires_empty'):r.normalize(raw,q,dict(r.b.rt.UNKNOWN_USAGE))

    def test_organizer_schema_does_not_supply_author_chosen_methods(self):
        q={'schema':'mindthus.route-v03-organize-request.v1','method_summaries':{'edsp':'x','wae':'y'}}
        schema=r.schema(q)
        self.assertEqual(schema['properties']['issues']['items']['properties']['candidates']['items']['enum'],['edsp','wae'])

class TransportRecoveryTests(unittest.TestCase):
    def test_invalid_ids_map_without_changing_judgments(self):
        import tempfile
        spec=importlib.util.spec_from_file_location('transport_test',P.with_name('transport_recovery.py'))
        adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
        raw={'issues':[{'id':'中文事项','candidates':['edsp'],'goal':'Original goal','scope':'Original scope'}]}
        with tempfile.TemporaryDirectory() as tmp:
            adapter.ROOT=Path(tmp);adapter.r.ACTIVE_LABEL='full-F-jev_advisory'
            with patch.object(adapter,'original_normalize',side_effect=lambda raw,q,u:raw):
                out=adapter.normalize(raw,{'schema':'mindthus.route-v03-organize-request.v1','request_id':'id'}, {})
            self.assertEqual(out['issues'][0],{**raw['issues'][0],'id':'I1'})
            self.assertEqual(raw['issues'][0]['id'],'中文事项')
            self.assertTrue((Path(tmp)/'adapters/full-F-jev_advisory-identifier-map.json').exists())

if __name__=='__main__':unittest.main()
