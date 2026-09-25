"""Record current Codex's reviewed acceptance of HD/C I1 for the named P1 use."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))
from experiments.typed_decision.contracts import canonical, digest, require
from experiments.typed_decision.session import read_record

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-formal-abc-v1/HD')
EPISODE = ROOT / 'episodes' / 'C'


def main() -> None:
    matches = list(EPISODE.glob('turns/*/inputs/*/steps/execution__I1__1/host-response.json'))
    require(len(matches) == 1, 'HD_C_I1_response_not_unique')
    response = read_record(matches[0])['submission']
    require(response['host_context_ref'] == 'formal-abc-v1:HD:C:I1'
            and response['owner_ref'] == 'current-codex:formal-abc-v1', 'wrong_host_response')
    reply = response['reply']
    require(reply['objection'] is None and reply['performed_methods'] == ['edsp'], 'not_accepted_I1')
    text = reply['text']
    # These checks support, but do not substitute for, the current Codex's semantic review.
    require(all(term in text for term in ('纸图', '网页', 'App', '第三站', '断网')),
            'required_comparable_candidate_not_found')
    receipt = {'owner_ref': response['owner_ref'], 'dependency_id': 'P1',
               'artifact_sha256': digest(text), 'accepted': True,
               'reason': ('Current Codex reviewed I1: paper map, existing web page, their '
                          'combination, and full App are compared against the same visit, '
                          'offline and scarce-resource criteria; suitable as I2 candidate input, '
                          'not an independently verified fact.'),
               'source_host_response': str(matches[0]),
               'source_host_response_sha256': hashlib.sha256(matches[0].read_bytes()).hexdigest()}
    path = EPISODE / 'host-acceptance' / 'P1.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(json.loads(path.read_bytes()) == receipt, 'acceptance_changed')
    else:
        with path.open('xb') as out:
            out.write(canonical(receipt) + b'\n')
    print(json.dumps({'accepted': True, 'artifact_sha256': receipt['artifact_sha256'],
                      'receipt': str(path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
