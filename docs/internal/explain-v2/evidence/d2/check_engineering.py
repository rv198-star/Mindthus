#!/usr/bin/env python3
"""Fixed-source parity checks. This is not a V1/V2 model or comprehension benchmark."""
from pathlib import Path
import hashlib
from html.parser import HTMLParser
import json
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'skills/explain/scripts'))
from explain_compiler import compile_source, parse_source, patch_source, recover_source

class Visible(HTMLParser):
    def __init__(self):
        super().__init__(); self.hidden=0; self.parts=[]; self.nodes=[]; self.edges=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','textarea'): self.hidden+=1
        a=dict(attrs)
        if 'data-node-id' in a: self.nodes.append(a['data-node-id'])
        if 'data-edge-id' in a: self.edges.append((a['data-edge-id'],a['data-from'],a['data-to']))
    def handle_endtag(self,tag):
        if tag in ('script','style','textarea'): self.hidden-=1
    def handle_data(self,data):
        if not self.hidden: self.parts.append(data)

def main():
    output=Path(sys.argv[1]); reg=json.loads((HERE/'registration.json').read_text())
    assert not output.exists(), 'Refusing to overwrite a recorded result.'
    assert hashlib.sha256((HERE/'cases.json').read_bytes()).hexdigest()==reg['cases_sha256']
    for name,expected in reg['runtime_files'].items():
        assert hashlib.sha256((ROOT/'skills/explain'/name).read_bytes()).hexdigest()==expected,name
    cases=json.loads((HERE/'cases.json').read_text())['cases']
    rows=[]
    for case in cases:
        reference={}
        for engine in ('node','python'):
            for surface in ('fragment','document'):
                for repeat in range(3):
                    started=time.perf_counter()
                    result=compile_source(case['draft'],engine=engine,output_format=surface)
                    wall=(time.perf_counter()-started)*1000
                    parsed=Visible(); parsed.feed(result['html']); text=''.join(parsed.parts)
                    assert all(x in text for x in case['required_visible']),(case['id'],text)
                    assert len(parsed.nodes)==case['nodes'] and len(parsed.edges)==case['edges']
                    signature=(parsed.parts,parsed.nodes,parsed.edges)
                    if surface in reference: assert signature==reference[surface]
                    else: reference[surface]=signature
                    if surface=='document': assert recover_source(result['html'])==case['draft']
                    rows.append({'case':case['id'],'engine':engine,'surface':surface,'repeat':repeat+1,
                                 'pass':True,'source_bytes':len(case['draft'].encode()),'html_bytes':len(result['html'].encode()),
                                 'same_process_compile_wall_ms':round(wall,3),'source_sha256':result['source_sha256']})
        original=parse_source(case['draft'])
        changed=patch_source(case['draft'],'result','已更正的展示文本；其余内容保留。\n')
        updated=parse_source(changed)
        for old,new in zip(original['sections'],updated['sections']):
            if old['id']!='result':
                assert case['draft'][old['start']:old['end']]==changed[new['start']:new['end']]
    payload={'schema':'explain.d2.engineering-result.v1','candidate_commit':reg['candidate_commit'],
             'registration_sha256':hashlib.sha256((HERE/'registration.json').read_bytes()).hexdigest(),
             'cases_sha256':reg['cases_sha256'],'checks':rows,'engineering_checks_passed':len(rows),
             'source_patch_cases_passed':3,'model_generations':0,'model_token_usage':None,'model_cost':None,
             'independent_comprehension': 'not_run','chat_inline_visibility':'not_verified',
             'overall_d2':'incomplete','d3_authorized_by_this_result':False,
             'measurement_scope':'Same-process deterministic compile wall time only; no model generation, input context, tool return, or human comprehension measurement.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in payload.items() if k!='checks'},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
