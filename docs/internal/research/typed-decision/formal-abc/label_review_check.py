"""Offline controls for single-call label-review admission and recovery."""
import importlib.util
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('label_review', HERE / 'label_review.py')
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)


def valid_row():
    return {'id':'R01','entry_mode':'direct_execution','unresolved_obligation':'clear',
            'owner':None,'checked_owner':None,'applicable':None,'route':'direct_execute',
            'ambiguity':False,'rationale':'任务明确，可直接执行。'}


class ReviewChecks(unittest.TestCase):
    def test_request_has_no_author_columns_or_private_map(self):
        body, frozen = REVIEW.prepared()
        payload = json.loads(body['messages'][1]['content'])
        self.assertTrue(all(set(row) == {'id','context'} for row in payload['cases']))
        self.assertNotIn('private_case_id_map', payload)
        self.assertEqual(frozen['max_calls'], 1)
        self.assertEqual(frozen['retries'], 0)
        self.assertLessEqual(len(REVIEW.review_packet.canonical(body)), REVIEW.MAX_BYTES)

    def test_valid_review(self):
        rows = REVIEW.validate_judgments(json.dumps({'judgments':[valid_row()]}), ['R01'])
        self.assertEqual(rows[0]['route'], 'direct_execute')

    def test_checked_owner_is_not_final_owner(self):
        row = valid_row()
        row.update(route='llm_fallback', owner=None, checked_owner='wae', applicable='no')
        REVIEW.validate_judgments(json.dumps({'judgments':[row]}), ['R01'])
        row['owner'] = 'wae'
        with self.assertRaises(ValueError):
            REVIEW.validate_judgments(json.dumps({'judgments':[row]}), ['R01'])

    def test_inconsistent_intervention_is_rejected(self):
        row = valid_row(); row.update(route='intervene', owner='sra')
        with self.assertRaises(ValueError):
            REVIEW.validate_judgments(json.dumps({'judgments':[row]}), ['R01'])

    def test_missing_duplicate_or_wrong_ids_rejected(self):
        for rows in [[], [valid_row(),valid_row()], [dict(valid_row(),id='R02')]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                REVIEW.validate_judgments(json.dumps({'judgments':rows}), ['R01'])

    def test_unknown_fields_rejected(self):
        with self.assertRaises(ValueError):
            REVIEW.validate_judgments(json.dumps({'judgments':[dict(valid_row(),extra=True)]}), ['R01'])

    def fixture(self, directory):
        body = {'model':REVIEW.MODEL}
        frozen = {'request_sha256':REVIEW.review_packet.sha(body), 'case_ids':['R01']}
        (directory/'label-review-freeze.json').write_text(json.dumps(frozen))
        return body, frozen

    def test_complete_reentry_calls_transport_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); body, frozen = self.fixture(directory)
            calls=[]
            def transport(*_):
                calls.append(1)
                return {'model':REVIEW.MODEL,'choices':[{'finish_reason':'stop','message':{
                    'content':json.dumps({'judgments':[valid_row()]})}}]}
            with patch.object(REVIEW,'HERE',directory), patch.object(REVIEW,'prepared',return_value=(body,frozen)):
                key=secrets.token_hex(24)
                first=REVIEW.run(directory/'trial',key,transport=transport)
                second=REVIEW.run(directory/'trial',key,transport=lambda *_:self.fail('repeated'))
                self.assertEqual(first,second)
                self.assertEqual(first['status'],'complete')
                self.assertEqual(len(calls),1)

    def test_unknown_intent_never_resubmitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp); body,frozen=self.fixture(directory)
            (directory/'trial').mkdir()
            with patch.object(REVIEW,'HERE',directory), patch.object(REVIEW,'prepared',return_value=(body,frozen)):
                with self.assertRaises(ValueError):
                    REVIEW.run(directory/'trial',secrets.token_hex(24),transport=lambda *_:self.fail('network'))

    def test_invalid_json_preserved_and_no_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);body,frozen=self.fixture(directory);calls=[]
            def transport(*_):
                calls.append(1)
                return {'model':REVIEW.MODEL,'choices':[{'finish_reason':'stop', 'message':{'content':'{bad json'}}]}
            with patch.object(REVIEW,'HERE',directory),patch.object(REVIEW,'prepared',return_value=(body,frozen)):
                row=REVIEW.run(directory/'trial',secrets.token_hex(24),transport=transport)
                self.assertEqual(row['status'],'failed');self.assertEqual(row['raw_content'],'{bad json')
                self.assertEqual(len(calls),1)

    def test_credential_reflection_never_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);body,frozen=self.fixture(directory);key=secrets.token_hex(24)
            def transport(*_):
                return {'model':REVIEW.MODEL,'choices':[{'finish_reason':'stop','message':{'content':key}}]}
            with patch.object(REVIEW,'HERE',directory),patch.object(REVIEW,'prepared',return_value=(body,frozen)):
                row=REVIEW.run(directory/'trial',key,transport=transport)
                self.assertEqual(row['status'],'failed');self.assertIsNone(row['raw_content'])
                self.assertTrue(all(key.encode() not in p.read_bytes() for p in (directory/'trial').rglob('*.json')))


if __name__ == '__main__':
    unittest.main()
