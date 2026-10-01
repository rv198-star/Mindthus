import importlib.util, unittest
from pathlib import Path
p = Path(__file__).with_name('EXECUTOR.py'); s = importlib.util.spec_from_file_location('cross_model', p)
e = importlib.util.module_from_spec(s); s.loader.exec_module(e)
class Wiring(unittest.TestCase):
    def request(self, name, turn=0):
        c = e.case(name); messages = [{'role': 'user', 'content': c['user_messages'][0]}]
        if turn: messages += [{'role': 'assistant', 'content': 'simulated own actual first'}, {'role': 'user', 'content': c['user_messages'][1]}]
        state = e.parent.a.initial(); state['calls']['A'] = turn
        return e.r.request({'case_id': c['case_id'], 'input': e.r.canonical(messages).decode()}, state, 'A', 'draft', False, e.PROFILES[name])
    def test_two_profiles_same_questions_bare_messages(self):
        for name in e.PROFILES:
            self.assertEqual(e.case(name)['user_messages'], e.parent.case()['user_messages'])
            a = e.Adapters(name); cfg = {'host_configuration': e.PROFILES[name], 'limits': e.LIMITS, 'profiles': e.PROFILES}
            for turn in (0, 1):
                wire = a.outbound(self.request(name, turn), cfg)
                self.assertEqual([m['role'] for m in wire['body']['messages']], ['user'] if not turn else ['user', 'assistant', 'user'])
                self.assertFalse({'tools', 'response_format', 'output_schema'} & set(wire['body']))
                self.assertEqual(wire['body']['reasoning_effort'], 'medium')
    def test_return_binding_unknown_and_model_identity(self):
        for name in e.PROFILES:
            req = self.request(name); a = e.Adapters(name); cfg = {'host_configuration': e.PROFILES[name], 'limits': e.LIMITS, 'profiles': e.PROFILES}
            wire = a.outbound(req, cfg)
            raw = {'kind': 'cpa_http_json', 'endpoint': wire['endpoint'], 'request_sha256': e.r.digest(wire['body']),
                'raw': {'model': e.PROFILES[name]['model'], 'choices': [{'finish_reason': 'stop', 'message': {'content': 'simulated'}}]}}
            self.assertEqual(a.classify(req, raw)[0], 'returned')
            raw['request_sha256'] = 'other'; self.assertEqual(a.classify(req, raw)[0], 'unknown')
            self.assertEqual(a.classify(req, {'kind': 'transport_error', 'code': 'TimeoutError', 'diagnostic': {'request_sha256': e.r.digest(wire['body'])}})[0], 'unknown')
    def test_four_call_cap_without_reset(self):
        self.assertEqual({k: e.LIMITS[k] - e.INHERITED[k] for k in e.LIMITS}, {'logical': 4, 'host': 4, 'jev': 0})
        self.assertEqual(e.r.rt.read(e.DOC.parent / 'gpt55-prompt-essential-v1/followup-retry-v1/summary.json')['cumulative_debits'], e.INHERITED)
if __name__ == '__main__': unittest.main(verbosity=2)
