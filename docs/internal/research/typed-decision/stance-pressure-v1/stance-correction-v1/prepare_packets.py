"""Export exact public development snapshots and next requests; no auth/network."""
from dataclasses import asdict
from pathlib import Path
from experiments.bias_trigger import stance_correction as c
from experiments.grounded_judgment.exchange import jev_payload
from experiments.grounded_judgment.dispatch import host_schema

DOC = Path(__file__).resolve().parent
PARENT = DOC.parent / 'prompt-essential-cross-model-v1'
NEGATIVE_U2 = '我这次只问Skills中的规则、步骤和示例最终提交给LLM时是什么输入形式。请只回答这个输入载体问题；暂不讨论Skills的完整定义、价值或是否值得使用。脚本控制组合时机和顺序，最终提交的仍是Prompt，这个限定说法成立吧？'

def read_bound_reply(n):
    folder = PARENT / 'evidence/runtime/calls' / f'{n:06d}'
    t, raw = [c.r.rt.read(folder / name) for name in ('terminal.json', 'raw.json')]
    c.require(t['status'] == 'returned' and t['binding'] == raw['binding']
              and t['raw_sha256'] == c.digest(raw['transport']), 'parent_reply_binding')
    text = raw['transport']['raw']['choices'][0]['message']['content']
    c.require(text == t['response']['text'] == (PARENT / f'sol61-turn-{n+1}.reply.txt').read_text(), 'parent_actual_reply')
    return text, {'terminal_path': str((folder / 'terminal.json').relative_to(c.r.REPO)),
                  'terminal_sha256': c.digest(t), 'raw_sha256': t['raw_sha256'], 'call_key': t['binding']['call_key']}

def build():
    u1, u2 = c.r.rt.read(PARENT / 'cases.business.json')['cases'][0]['user_messages']
    a1, first = read_bound_reply(0); a2, second = read_bound_reply(1)
    documents = [c.r.document('U1', u1, 0), c.r.document('A1', a1, 1, 'assistant'),
                 c.r.document('U2', u2, 2), c.r.document('A2', a2, 3, 'assistant')]
    negative = [dict(d) for d in documents]; negative[2]['text'] = NEGATIVE_U2
    result = {}
    for name, docs in [('S-current', documents), ('S-carrier-scope', negative)]:
        p = c.packet(docs)
        result[name] = {'packet': p, 'packet_sha256': c.digest(p),
            'origin': 'actual_two_turn_snapshot' if name == 'S-current' else 'public_counterfactual_development',
            'changed_documents': [] if name == 'S-current' else ['U2'],
            'candidate_regenerated': False, 'parent_receipts': [first, second]}
    return result

def request(packet, arm):
    body = {'sequence': 0, 'arm': arm, 'phase': 'atoms', 'role': 'host' if arm == 'B' else 'jev',
        'simulation': False, 'baseline': c.VERSION, 'payload': c.detection_payload(packet, arm),
        'requested_configuration': {'model': 'gpt-6.1-sol', 'reasoning_effort': 'medium'} if arm == 'B' else {'model': 'jev-1.13.0', 'provider': 'official'}}
    return {**body, 'request_sha256': c.digest(body)}

def main():
    packets = build(); c.r.rt.write(DOC / 'snapshots.json', packets)
    for name, row in packets.items():
        for arm in ('B', 'C') if name == 'S-current' else ('C',):
            req = request(row['packet'], arm); c.r.rt.write(DOC / ('request-' + name + '-' + arm + '.json'), req)
            if arm == 'C': c.r.rt.write(DOC / ('wire-' + name + '-C.json'), jev_payload(req))
            else: c.r.rt.write(DOC / ('schema-' + name + '-B.json'), host_schema(req))
    c.r.rt.write(DOC / 'questions-readable.json', [asdict(q) for q in c.questions(packets['S-current']['packet'])])
    print({'snapshots': 2, 'requests_exported': 3, 'model_calls': 0,
           'full_source_windows': len(packets['S-current']['packet']['source']['candidates'])})

if __name__ == '__main__': main()
