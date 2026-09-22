"""Offline blind-packet controls; never invoke a model or read credentials."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('c01_blind_packet', HERE / 'review_packet.py')
PACKET = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKET)


class BlindPacketChecks(unittest.TestCase):
    def setUp(self):
        self.candidates = json.loads((HERE / 'holdout-candidates.json').read_text(encoding='utf-8'))

    def test_author_fields_never_enter_public_rows(self):
        for row in self.candidates['cases']:
            row['family'] = 'PRIVATE_FAMILY_MARKER'
            row['expected'] = {'owner': 'PRIVATE_EXPECTED_MARKER'}
            row['task_criteria'] = ['PRIVATE_CRITERIA_MARKER']
            row['catastrophic'] = ['PRIVATE_CATASTROPHIC_MARKER']
        public, _ = PACKET.blind_cases(self.candidates)
        self.assertTrue(all(set(row) == {'id', 'context'} for row in public))
        text = json.dumps(public)
        for marker in ('PRIVATE_FAMILY', 'PRIVATE_EXPECTED', 'PRIVATE_CRITERIA', 'PRIVATE_CATASTROPHIC'):
            self.assertNotIn(marker, text)

    def test_original_context_is_preserved_including_explicit_method(self):
        public, mapping = PACKET.blind_cases(self.candidates)
        originals = {row['id']: row for row in self.candidates['cases']}
        for row in public:
            self.assertEqual(row['context'], originals[mapping[row['id']]]['context'])
        h12 = next(row for row in public if mapping[row['id']] == 'H12')
        self.assertEqual(h12['context']['explicit_method'], 'wae')

    def test_output_is_detached(self):
        original = copy.deepcopy(self.candidates)
        public, _ = PACKET.blind_cases(self.candidates)
        public[0]['context']['constraints'].append('new output only')
        self.assertEqual(self.candidates, original)

    def test_repeat_packet_and_order_are_deterministic(self):
        self.assertEqual(PACKET.blind_cases(self.candidates), PACKET.blind_cases(self.candidates))
        public, mapping = PACKET.blind_cases(self.candidates)
        self.assertEqual(len(set(mapping.values())), 18)
        self.assertTrue(all(row['id'].startswith('R') for row in public))

    def test_duplicate_ids_rejected(self):
        self.candidates['cases'].append(copy.deepcopy(self.candidates['cases'][0]))
        with self.assertRaises(ValueError):
            PACKET.blind_cases(self.candidates)

    def test_empty_and_missing_context_rejected(self):
        for cases in ([], [{'id': 'H01'}]):
            with self.subTest(cases=cases), self.assertRaises(ValueError):
                PACKET.blind_cases({'cases': cases})

    def test_manifest_and_payload_stay_separate_and_hash_bound(self):
        payload, manifest = PACKET.prepare()
        self.assertEqual(set(payload), {'cases', 'canonical_contracts'})
        self.assertEqual(set(payload['canonical_contracts']), set(PACKET.METHODS))
        self.assertEqual(manifest['payload_sha256'], PACKET.sha(payload))
        self.assertEqual(manifest['status'], 'prepared_not_sent')
        self.assertEqual(manifest['model_calls'], 0)
        self.assertFalse(manifest['holdout_qualified'])
        self.assertNotIn('private_case_id_map', payload)


if __name__ == '__main__':
    unittest.main(verbosity=2)
