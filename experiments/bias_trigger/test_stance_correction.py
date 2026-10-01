"""Only new four-atom consumption and scoped packets; no transport/model calls."""
import importlib.util, unittest
from pathlib import Path
from experiments.bias_trigger import stance_correction as c
from experiments.grounded_judgment.core import agent_contract
p = c.r.REPO / 'docs/internal/research/typed-decision/stance-pressure-v1/stance-correction-v1/prepare_packets.py'
s = importlib.util.spec_from_file_location('prepare_correction', p); export = importlib.util.module_from_spec(s); s.loader.exec_module(export)

class Correction(unittest.TestCase):
    def setUp(self):
        self.p = export.build()['S-current']['packet']
        self.ref = next(k for k, v in self.p['source']['candidates'].items() if v['document_id'] == 'A2')
    def b(self, support=True, loc=None):
        loc = self.ref if loc is None else loc
        state = 'support' if support else 'deny'
        return {q.id: {'value': state if q.kind == 'assess_proposition' else loc,
            'semantic_state': state if q.kind == 'assess_proposition' else 'support',
            'unresolved_reason': None, 'basis_refs': [self.ref] if q.kind == 'assess_proposition' or loc != 'none' else []} for q in c.questions(self.p)}
    def native(self, probability=.9):
        out = {}
        for q in c.questions(self.p):
            out[q.id] = {'status': 'ok', 'value': probability if q.kind == 'assess_proposition' else self.ref, 'reason': '', 'uncertainty': None}
            if q.kind == 'select':
                out[q.id]['uncertainty'] = {'source': 'provider_distribution', 'confidence': .9,
                    'probabilities': {k: .9 if k == self.ref else .1 / (len(q.criteria)-1) for k in q.criteria}}
        return out
    def test_two_snapshots_single_current_goal_change_and_actual_candidate(self):
        packets = export.build(); a = packets['S-current']['packet']; b = packets['S-carrier-scope']['packet']
        self.assertEqual(a['candidate'], b['candidate'])
        self.assertEqual([x['id'] for x,y in zip(a['source']['documents'], b['source']['documents']) if x['text'] != y['text']], ['U2'])
        self.assertEqual(a['candidate'], (export.PARENT / 'sol61-turn-2.reply.txt').read_text())
        self.assertEqual(len(c.questions(a)), 4)
    def test_support_then_bound_findings_then_single_revision_packet(self):
        result = c.consume(self.p, self.b(), 'B')
        self.assertEqual(len(result['findings']), 2); self.assertTrue(result['needs_revision'])
        rev = c.revision_payload(self.p, result)
        self.assertEqual(rev['findings'], result['findings'])
        response = {'disposition': 'adopted', 'keep_refs': [self.ref], 'candidate_refs': [self.ref], 'reason': 'simulated reason', 'final': 'simulated final; not a model answer'}
        self.assertEqual(c.accept_revision(self.p, result, response), response)
        with self.assertRaises(ValueError): c.accept_revision(self.p, {**result, 'packet_sha256': 'other_packet'}, response)
        response['candidate_refs'] = []
        with self.assertRaises(ValueError): c.accept_revision(self.p, result, response)
    def test_low_probability_and_unadopted_locator_never_promoted(self):
        raw = self.native(.6); before = c.digest(raw)
        result = c.consume(self.p, raw, 'C')
        self.assertFalse(result['needs_revision']); self.assertEqual(c.digest(raw), before)
        raw = self.native(); raw['LOC.Q_FRAME']['value'] = 'ambiguous'
        result = c.consume(self.p, raw, 'C')
        self.assertEqual([f['finding_id'] for f in result['findings']], ['Q_COVERAGE'])
    def test_denial_and_omission_have_distinct_consumption(self):
        self.assertFalse(c.consume(self.p, self.b(False), 'B')['needs_revision'])
        result = c.consume(self.p, self.b(loc='none'), 'B')
        self.assertEqual([f['finding_id'] for f in result['findings']], ['Q_COVERAGE'])
        self.assertEqual(result['findings'][0]['candidate_refs'], [])
        self.assertEqual(result['findings'][0]['basis_origin'], 'adopted_whole_candidate_omission')
    def test_exported_native_wire_and_agent_contracts_are_the_actual_questions(self):
        from experiments.grounded_judgment.exchange import jev_payload
        native = export.request(self.p, 'C'); agent = export.request(self.p, 'B')
        self.assertEqual(native['payload']['source'], agent['payload']['source'])
        self.assertEqual(native['payload']['instruction'], agent['payload']['instruction'])
        wire = jev_payload(native)
        self.assertEqual({q['type'] for q in wire['questions'].values()}, {'noul', 'choice'})
        for q in c.questions(self.p): self.assertEqual(agent['payload']['output_contract'][q.id], agent_contract(q))

if __name__ == '__main__': unittest.main(verbosity=2)
