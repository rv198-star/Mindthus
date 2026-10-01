"""Only successor wire/receipt/budget wiring; no model requests."""
import importlib.util, unittest
from pathlib import Path
p = Path(__file__).with_name('EXECUTOR.py'); s = importlib.util.spec_from_file_location('followup_retry', p)
e = importlib.util.module_from_spec(s); s.loader.exec_module(e)

class Wiring(unittest.TestCase):
    def request(self):
        wire, summary = e.verified_parent()
        item = {'case_id': e.parent.case()['case_id'], 'input': e.r.canonical(wire['body']['messages']).decode()}
        return e.r.request(item, summary['state'], 'A', 'draft', False, e.HOST)
    def test_same_wire_no_regeneration_or_new_evaluation_prompt(self):
        req = self.request(); cfg = {'host_configuration': e.HOST, 'limits': e.LIMITS}
        wire = e.Adapters().outbound(req, cfg)
        self.assertEqual(e.r.digest(wire), e.OLD_WIRE)
        self.assertEqual(req['sequence'], 2)
        wire['body']['messages'][1]['content'] = 'changed'
        self.assertEqual(e.r.digest(e.verified_parent()[0]), e.OLD_WIRE)
        req['sequence'] = 1
        with self.assertRaises(ValueError): e.Adapters().outbound(req, cfg)
    def test_inherited_receipt_classifier_still_binds_and_keeps_unknown(self):
        req = self.request(); a = e.Adapters(); wire = e.verified_parent()[0]
        raw = {'kind': 'cpa_http_json', 'endpoint': wire['endpoint'], 'request_sha256': e.r.digest(wire['body']),
            'raw': {'model': 'gpt-5.5', 'choices': [{'finish_reason': 'stop', 'message': {'content': 'simulated'}}]}}
        self.assertEqual(a.classify(req, raw)[0], 'returned')
        raw['request_sha256'] = 'other'
        self.assertEqual(a.classify(req, raw)[0], 'unknown')
        self.assertEqual(a.classify(req, {'kind': 'transport_error', 'code': 'TimeoutError',
            'diagnostic': {'request_sha256': e.r.digest(wire['body'])}})[0], 'unknown')
    def test_only_one_additional_debit_and_original_failed_terminal_unchanged(self):
        self.assertEqual({k: e.LIMITS[k] - e.INHERITED[k] for k in e.LIMITS}, {'logical': 1, 'host': 1, 'jev': 0})
        self.assertEqual(e.verified_parent()[1]['state']['calls']['A'], 2)
        self.assertEqual(e.r.rt.read(e.parent.ROOT / 'calls/000001/terminal.json')['status'], 'failed')
        with self.assertRaises(ValueError): e.Adapters().check_configuration({'host_configuration': e.HOST, 'limits': e.parent.LIMITS})

if __name__ == '__main__': unittest.main(verbosity=2)
