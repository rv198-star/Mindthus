"""Offline controls for the live-validation driver. No network or credentials."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('entry_live_run', HERE / 'run.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

from experiments.typed_decision.providers import TypeSafeJevProvider


HITS = {
    'validation:V01-candidate': 'explanatory_scope',
    'validation:V02-candidate': 'premise_treatment',
    'validation:V03-candidate': 'scope_preservation',
}


def fake_jev(url, headers, body, timeout):
    target = body['state']['assessment_target']
    expected = HITS.get(target['source_ref'])
    answers = {}
    for qid, question in body['questions'].items():
        keys = list(question['criteria'])
        fit = m.assessment.CHECKS[qid]['fit']
        hit = m.assessment.CHECKS[qid]['hit']
        value = hit if expected == qid else fit
        probs = {key: 0.03 for key in keys}
        probs[value] = 0.91
        answers[qid] = {
            'type': 'choice',
            'choice': value,
            'confidence': 0.91,
            'probabilities': probs,
        }
    return {
        'model': 'jev-1.13.0',
        'answers': answers,
        'usage': {'input_tokens': 100, 'output_tokens': 10, 'cost': 0.0001},
    }


def fake_host(url, headers, body, timeout):
    return {
        'model': m.HOST_MODEL,
        'usage': {'prompt_tokens': 120, 'completion_tokens': 40, 'cost': 0.001},
        'choices': [{
            'finish_reason': 'stop',
            'message': {
                'content': '保留已知局部事实，但不把它升级成整体结论；按原任务范围处理，并明确仍缺的证据。',
            },
        }],
    }


def provider_factory(*, model='jev-1.13.0', choice_rounding=False, **kwargs):
    return TypeSafeJevProvider(
        model=model,
        choice_rounding=choice_rounding,
        transport=fake_jev,
    )


def main():
    frozen = m.prepare()
    assert frozen['case_ids'] == [
        'V01_local_overreach',
        'V02_unsupported_premise',
        'V03_scope_override',
        'N01_local_controller_valid',
        'N02_explicit_local_scope',
        'N03_explicit_hypothesis',
    ]
    assert len(frozen['detector']['initial_batches']) == 6
    assert all(row['question_ids'] == list(m.assessment.CHECKS)
               for row in frozen['detector']['initial_batches'].values())
    assert all(row['request_bytes'] <= m.CHECK_LIMITS.max_request_bytes
               for row in frozen['detector']['initial_batches'].values())

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        freeze_path = root / 'freeze.json'
        freeze_path.write_bytes(m.canonical(frozen) + b'\n')
        campaign_root = root / 'campaign'
        old_ts = os.environ.pop('TYPESAFE_API_KEY', None)
        old_host = os.environ.pop('MINDTHUS_HOST_API_KEY', None)
        try:
            with patch.object(m, 'FREEZE', freeze_path), \
                 patch.object(m, 'TypeSafeJevProvider', provider_factory), \
                 patch.object(m, 'post_json', fake_host):
                result = m.run_campaign(campaign_root, 'offline-typesafe', 'offline-host')
        finally:
            if old_ts is not None:
                os.environ['TYPESAFE_API_KEY'] = old_ts
            if old_host is not None:
                os.environ['MINDTHUS_HOST_API_KEY'] = old_host

        assert result['positive_detection'] == {'correct': 3, 'total': 3}
        assert result['negative_false_positive'] == {'cases': 0, 'total': 3}
        assert result['corrections_triggered'] == 3
        assert result['corrections_completed'] == 3
        assert result['rechecks_completed'] == 3
        assert result['jev_usage']['calls'] == 9
        assert result['host_usage']['calls'] == 3
        assert all(
            row['correction_status'] == 'not_triggered'
            for row in result['case_results'] if row['expected_hit'] is None
        )
        assert all(
            row['recheck_hits'] == []
            for row in result['case_results'] if row['expected_hit'] is not None
        )

        # Unknown host intent is never resubmitted.
        sample = campaign_root / 'V01_local_overreach' / 'correction'
        outcome = sample / 'outcome.json'
        saved = outcome.read_bytes()
        outcome.unlink()
        try:
            try:
                m._host_correct(
                    campaign_root / 'V01_local_overreach',
                    m.read_record(campaign_root / 'V01_local_overreach' / 'correction-request.json'),
                    'offline-host',
                )
                raise AssertionError('expected RecoveryRequired')
            except m.RecoveryRequired:
                pass
        finally:
            outcome.write_bytes(saved)

        print(json.dumps({
            'status': 'PASS',
            'network_calls': 0,
            'positive_detection': result['positive_detection'],
            'negative_false_positive': result['negative_false_positive'],
            'corrections': result['corrections_completed'],
            'rechecks': result['rechecks_completed'],
            'jev_calls': result['jev_usage']['calls'],
            'host_calls': result['host_usage']['calls'],
        }, ensure_ascii=False))


if __name__ == '__main__':
    main()
