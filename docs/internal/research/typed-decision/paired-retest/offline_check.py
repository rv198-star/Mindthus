"""Meaningful offline checks for scoring, egress and fail-closed comparison execution."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('paired_run',Path(__file__).with_name('run.py'))
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ComparisonChecks(unittest.TestCase):
    def test_correct_fallback_is_not_technical_success(self):
        case={'accepted':[{'entry_mode':'mindthus_intervention','route':'llm_fallback','owner':None}]}
        report={'result':{'entry_mode':'direct_execution','route':'llm_fallback','owner':None,'status':'abstain'}}
        valid=m.scoring(case,report,[])
        self.assertTrue(valid['final_match'])
        self.assertFalse(valid['joint_match'])
        invalid=m.scoring(case,report,[{'results':{'entry_mode':{'status':'provider_error'}}}])
        self.assertFalse(invalid['final_match'])

    def test_cannot_mix_fields_from_different_alternatives(self):
        case={'accepted':[{'entry_mode':'direct_execution','route':'direct_execute','owner':None},
                          {'entry_mode':'mindthus_intervention','route':'intervene','owner':'sra'}]}
        report={'result':{'entry_mode':'direct_execution','route':'direct_execute','owner':'sra','status':'ok'}}
        self.assertFalse(m.scoring(case,report,[])['final_match'])

    def simulate(self, drift=False):
        calls=[]
        def fake(url,headers,body,timeout):
            state=body.get('state')
            if state is None:
                payload=json.loads(body['messages'][1]['content'])
                state,questions=payload['state'],payload['questions']
                self.assertEqual(body['provider']['only'],['Anthropic'])
                self.assertFalse(body['provider']['allow_fallbacks'])
            else: questions=body['questions']
            self.assertNotIn('accepted',state)
            self.assertNotIn('rationale',state)
            self.assertNotIn('score',state)
            calls.append(body['model'])
            values={'entry_mode':'direct_execution','unresolved_obligation':'clear'}
            if 'messages' in body:
                return {'model':body['model'],'provider':'Other' if drift and len(calls)>2 else 'Anthropic',
                        'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'answers':{
                            k:{'status':'ok','value':values[k]} for k in questions}})}}],
                        'usage':{'prompt_tokens':100,'completion_tokens':20,'cost':.0006}}
            return {'model':body['model'],'answers':{k:{'type':'choice','choice':values[k],
                    'confidence':1,'probabilities':{option:int(option==values[k]) for option in q['criteria']}}
                    for k,q in questions.items()},'usage':{'input_tokens':100,'output_tokens':20}}
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'OPENROUTER_API_KEY':'offline-test',
                'TYPESAFE_API_KEY':'offline-test'}), patch.object(m,'post_json',fake),contextlib.redirect_stdout(io.StringIO()):
            root=Path(d)/'trial'
            m.run(root)
            summary=m.read_record(root/'summary.json')
            with self.assertRaises(Exception): m.run(root)
            self.assertEqual(len(calls),summary['total_calls'])
            return summary

    def test_full_mock_run_keeps_wrong_answers_and_d0_separate(self):
        summary=self.simulate()
        self.assertTrue(summary['complete'])
        self.assertEqual(len(summary['rows']),64)
        self.assertEqual(summary['total_calls'],60)
        self.assertEqual(summary['analysis']['all_semantic']['planned_pairs'],30)
        self.assertEqual(summary['analysis']['sensitivity']['planned_pairs'],22)
        self.assertEqual(summary['analysis']['all_semantic']['B']['observed'],30)

    def test_serving_drift_stops_across_case_sessions(self):
        summary=self.simulate(drift=True)
        self.assertFalse(summary['complete'])
        self.assertEqual(summary['stop_reason'],'technical_failure')
        self.assertEqual(summary['total_calls'],4)
        self.assertFalse(summary['rows'][-1]['final_match'])


if __name__=='__main__': unittest.main()
