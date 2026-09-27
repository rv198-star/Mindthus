"""Offline checks of actual parser fixtures and existing bound A1 evidence.

No CLI, provider, model, credential or network operation is performed here.
The separate config-read-only-check.py records actual CLI parsing only.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent/'a1-native-format-repair-2026-09-27/evidence'


def load(name):
    return json.loads((HERE/name).read_text())


def record(path):
    return json.loads(path.read_text())['payload']


def check(label, condition):
    assert condition, label
    print('PASS:', label)


baseline = load('baseline.json')
blocked = load('builtin-override.json')
candidate = load('candidate-official-alias.json')
profile = load('candidate-profile.json')
source = load('official-source-evidence.json')
counts = load('counts-supplement.json')['payload']
check('actual baseline config/read completed without a model turn',
      baseline['returncode'] == 0 and baseline['methods_sent'] == ['initialize','initialized','config/read'])
check('actual built-in openai overrides rejected during parsing',
      blocked['returncode'] == 1 and 'Built-in providers cannot be overridden' in blocked['stderr']
      and blocked['methods_sent'] == ['initialize'])
check('official alias candidate parsed; ordinary retries and websockets disabled in parsed config',
      candidate['returncode'] == 0 and candidate['methods_sent'] == ['initialize','initialized','config/read']
      and candidate['parsed_config']['model_providers']['mindthus_official_http'] == {
          'name':'OpenAI','wire_api':'responses','request_max_retries':0,
          'stream_max_retries':0,'supports_websockets':False,'requires_openai_auth':True}
      and candidate['parsed_config']['unbounded_connection_retries'] is False)
check('candidate remains inactive for both arms, with no reset or matched-latency claim',
      profile['status'] == 'parser_verified_not_activated' and profile['applies_to'] == ['native','direct']
      and not profile['active_runtime_successor_created'] and not profile['budgets_reset']
      and not profile['new_latency_matched_to_old_119_seconds'])
check('user config fingerprint unchanged; same recorded executable as the real A1 call',
      source['config_sha256_before'] == source['config_sha256_after']
      and source['binary_sha256'] == record(PREVIOUS/'freeze.json')['binary_sha256'])
for relative, expected in counts['evidence_sha256'].items():
    check('unchanged historical evidence '+relative,
          hashlib.sha256((PREVIOUS/relative).read_bytes()).hexdigest() == expected)
terminal = record(PREVIOUS/'technical-retry-success-observation.json')
stderr = (PREVIOUS/'runs/A1/native/host/1/cli.stderr.txt').read_text()
retries = [line for line in stderr.splitlines() if 'retrying sampling request' in line]
stdout = [json.loads(line) for line in (PREVIOUS/'runs/A1/native/host/1/cli.stdout.jsonl').read_text().splitlines()]
check('five internal retry logs bind to the original successful turn; four UI notices are distinct',
      len(retries) == counts['counts']['cli_sampling_retry_log_records'] == 5
      and all('turn_id='+terminal['turn_id'] in line for line in retries)
      and sum(e.get('type') == 'error' and e.get('message','').startswith('Reconnecting...') for e in stdout) == 4
      and counts['thread_id'] == terminal['thread_id'] and counts['turn_id'] == terminal['turn_id'])
check('underlying attempt/overlap counts stay unknown, not inferred as six',
      all(counts['counts'][key] is None for key in (
          'actual_underlying_generation_request_attempts','actual_http_sampling_request_attempts','actual_remote_overlap')))
check('outer retry scope is explicit; no new business dispatch or budget reset',
      counts['automatic_retry_scope']['meaning'] == 'outer driver only'
      and counts['counts']['outer_driver_automatic_retries_this_invocation'] == 0
      and counts['budget']['consumed_host_cli_attempts'] == 2
      and counts['budget']['remaining_by_original_4_cap'] == 2
      and counts['current_turn_business_model_requests'] == 0
      and not counts['can_continue_A1_direct'] and counts['A1_direct_status'] == 'not_sent')
print('Checks cover fixture parsing and record integrity, not a live transport acceptance claim.')
